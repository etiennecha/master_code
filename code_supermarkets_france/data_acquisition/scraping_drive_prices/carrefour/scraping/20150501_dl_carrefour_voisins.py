#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import httplib, urllib2
import urllib
import cookielib
from cookielib import Cookie
from bs4 import BeautifulSoup
import string
import re
from datetime import date
import json

def enc_json(data, path_data):
  with open(path_data, 'w') as f:
    json.dump(data, f)

def makeCookie(name, value):
  return Cookie(
    version=0,
    name=name,
    value=value,
    port=None,
    port_specified=False,
    domain="courses.carrefour.fr",
    domain_specified=True,
    domain_initial_dot=False,
    path="/",
    path_specified=True,
    secure=False,
    expires=None,
    discard=False,
    comment=None,
    comment_url=None,
    rest=None
   )

def extract_bs_text(soup_bloc, ls_text = True):
  if soup_bloc and ls_text:
    return soup_bloc.findAll(text = True)
  elif not soup_bloc and ls_text:
    return []
  elif soup_bloc and not ls_text:
    return soup_bloc.text
  elif not soup_bloc and not ls_text:
    return None

def parse_product_page(product_soup):
  ls_dict_products = []
  ls_bloc_products = product_soup.findAll('li', {'class' : 'product'})
  for bloc_product in ls_bloc_products:
    ls_product_title = extract_bs_text(bloc_product.find('h3'))
    # bloc img_alt
    bloc_product_main = bloc_product.find('div', {'class' : 'productMain clearfix'})
    bloc_img = bloc_product_main.find('div', {'class' : 'img'})
    img_name = None
    if bloc_img and bloc_img.find('img', {'alt' : True}):
      img_name = bloc_img.find('img', {'alt' : True})['alt']
    # bloc price
    bloc_price = bloc_product.find('div', {'class' : 'specs priceSpecs'})
    ls_price = extract_bs_text(bloc_price) # conservative: captures all
    ls_promo = extract_bs_text(bloc_price.find('div', {'class' : 'priceBlock promoBlock'}))
    ls_promo_heading = extract_bs_text(bloc_price.find('h4', {'class' : 'heading'}))
    ls_reduction = extract_bs_text(bloc_price.find('div', {'class' : 'spec reduction'}))
    ls_format = extract_bs_text(bloc_price.find('span', {'class' : 'unit'}))
    ls_total_price = extract_bs_text(bloc_price.find('div', {'class' : 'spec price'}))
    ls_unit_price = extract_bs_text(bloc_price.find('div', {'class' : 'unitPrice'}))
    dict_product = {'ls_product_title' : ls_product_title,
                    'ls_price' : ls_price,
                    'ls_promo' : ls_promo,
                    'ls_promo_heading' : ls_promo_heading,
                    'ls_reduction': ls_reduction,
                    'ls_format' : ls_format,
                    'ls_total_price' : ls_total_price,
                    'ls_unit_price' : ls_unit_price,
                    'img_name' : img_name}
    ls_dict_products.append(dict_product)
  return ls_dict_products

# build urllib2 opener
cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [(u'User-agent',
                      u'Mozilla/5.0 (Windows NT 6.0)'+\
                      u'AppleWebKit/537.22 (KHTML, like Gecko)'+\
                      u'Chrome/25.0.1364.172 Safari/537.22')]
urllib2.install_opener(opener)

# get list of stores
drive_website_url = u'http://courses.carrefour.fr'
response = urllib2.urlopen(drive_website_url + r'/drive/accueil')
data = response.read()
soup = BeautifulSoup(data)

## go on store page (deprecated)
#shop_blocs = soup.findAll('li', {'class' : 'shop'})
#shop_voisin = soup.find('li', {'id' : 215, 'class' : 'shop'})
#shop_voisin_href = shop_voisin.find('a')['href']
#shop_voisin_href = soup.find('form', {'id' : 'drivePickingForm_290'})['action']

post_args = {'id' : 'drivePickingForm_404',
             'name' : 'drivePickingForm_404'}
req = urllib2.Request(drive_website_url)
req.add_data(urllib.urlencode(post_args))
response_2 = urllib2.urlopen(req)
data_2 = response_2.read()
soup_2 = BeautifulSoup(data_2)

# need to play with cookies to get products
cookie_jar.set_cookie(makeCookie("serviceDrive", "3"))
cookie_jar.set_cookie(makeCookie("storeDrive", "215"))
cookie_jar.set_cookie(makeCookie("browserSupportCheck", "checked"))
# pprint.pprint(cookie_jar.__dict__)

product_links = soup_2.findAll('a', {'class' : 'page',
                                     'href' : re.compile('/drive/tous-les-rayons/*')})
ls_products = []
for product_link in product_links[1:]:
  if product_link.find('img', {'alt':''}):
    # a bit fragile
    department = product_link.text
  else:
    try:
      sub_department_link  = product_link['href']
      sub_department = product_link.text
      response_3 = urllib2.urlopen(drive_website_url + sub_department_link)
      data_3 = response_3.read()
      soup_3 = BeautifulSoup(data_3)
      
      ls_sd_dict_products = parse_product_page(soup_3)
      # scrap other pages if any
      ac_param = sub_department_link.split('/')[-1]
      for cookie in cookie_jar:
        if cookie.name == 'JSESSIONID':
          jsessionid = cookie.value
      ls_page_nbs = extract_bs_text(soup_3.find('ul', {'class' : 'pageNumbers'}))
      if ls_page_nbs and len(ls_page_nbs) > 1:
        for page_nb in ls_page_nbs[1:]:
          headers_page = {u'Host' : 'courses.carrefour.fr',
                          u'Origin' : 'http://courses.carrefour.fr',
                          u'Referer' : drive_website_url + sub_department_link +\
                                       u';jsessionid=' + jsessionid,
                          u'X-Requested-With' : u'XMLHttpRequest',
                          u'X-Prototype-Version' : u'1.6.0.3',
                          u'Content-type' : u'application/x-www-form-urlencoded; charset=UTF-8'}
          data_page = {'t:ac' : ac_param}
          req_page = urllib2.Request(u'http://courses.carrefour.fr/drive'+\
                                     u'/rayon.categoryproductlistcontainer'+\
                                     u'.paging.selectpage/{:s}?t:ac={:s}'.format(page_nb,
                                                                                 ac_param),
                                     data = urllib.urlencode(data_page),
                                     headers = headers_page)
          response_page = urllib2.urlopen(req_page)
          data_page = response_page.read()
          
          json_content = json.loads(data_page)
          data_prods = json_content['zones']['componentZone']
          soup_prods = BeautifulSoup(data_prods)
          ls_sd_dict_products += parse_product_page(soup_prods)
      for dict_product in ls_sd_dict_products:
        dict_product['department'] = department
        dict_product['sub_department'] = sub_department
      ls_products += ls_sd_dict_products
    except Exception, e:
      print [department, sub_department, sub_department_link]
      print e

#path_carrefour = os.path.join(path_data,
#                              u'data_drive_supermarkets',
#                              u'data_carrefour')
#
#today_date = date.today().strftime(u"%Y%m%d")
#
#enc_json(ls_products,
#         os.path.join(path_carrefour,
#                      u'data_source',
#                      u'data_json_carrefour_voisins',
#                      u'{:s}_carrefour_voisins'.format(today_date)))
#
#print today_date, len(ls_products)
