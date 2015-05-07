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
import json
import pprint
# import string
import re
from datetime import date

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
    return [unicode(x) for x in soup_bloc.findAll(text = True)]
  elif not soup_bloc and ls_text:
    return []
  elif soup_bloc and not ls_text:
    return unicode(soup_bloc.text)
  elif not soup_bloc and not ls_text:
    return None

#def parse_product_page(product_soup):
#    dict_product = {'ls_product_title' : ls_product_title,
#                    'ls_price' : ls_price,
#                    'ls_promo' : ls_promo,
#                    'ls_promo_heading' : ls_promo_heading,
#                    'ls_reduction': ls_reduction,
#                    'ls_format' : ls_format,
#                    'ls_total_price' : ls_total_price,
#                    'ls_unit_price' : ls_unit_price,
#                    'img_name' : img_name}
#    ls_dict_products.append(dict_product)
#  return ls_dict_products

# build urllib2 opener
cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [(u'User-agent',
                      u'Mozilla/5.0 (Windows NT 6.0)'+\
                      u'AppleWebKit/537.22 (KHTML, like Gecko)'+\
                      u'Chrome/25.0.1364.172 Safari/537.22')]
urllib2.install_opener(opener)

# go to main page (useless? cookie acquisition?)
drive_website_url = u'http://fd5-www.leclercdrive.fr/default.aspx' # u'http://www.leclercdrive.fr'
response = urllib2.urlopen(drive_website_url)
data = response.read()
# soup = BeautifulSoup(data)

# get list of stores
json_stores_url = u'http://fd5-www.leclercdrive.fr/' +\
                  u'recuperermagasins.ashz?callbackJsonp=' +\
                  u'jQuery18302400790594983846_1430997880716&d=undefined&_=1430997881039'
response_stores = urllib2.urlopen(json_stores_url)
data_stores = response_stores.read()
data_stores_json = json.loads(re.sub('\);',
                                     '',
                                     re.sub('^jQuery[0-9_]*\(',
                                            '',
                                            data_stores)))
ls_stores = data_stores_json['objDonneesReponse']['lstMagasins']
ls_stores = [store for store in ls_stores if store['sNomMagasin'] != u'Assortiment complet']

ls_store_names = [store['sNomMagasin'] for store in ls_stores]
# print len(set(ls_store_names))
# Beginning of list: no drive
ls_drives = [store for store in ls_stores if store[ u'sSiteInternetActif'] == u'O']

# go to store page
#store_headers = {u'Host' : 'courses.carrefour.fr',
#                 u'Origin' : 'http://courses.carrefour.fr',
#                 u'Referer' : 'http://courses.carrefour.fr/drive/accueil',
#                 u'X-Requested-With' : u'XMLHttpRequest',
#                 u'X-Prototype-Version' : u'1.6.0.3',
#                 u'Content-type' : u'application/x-www-form-urlencoded; charset=UTF-8'}
store_url = ls_drives[0]['sURLCourses']
response = urllib2.urlopen(store_url)
store_data = response.read()
store_soup = BeautifulSoup(store_data)

bloc_rayons = store_soup.find('div', {'class' : re.compile('_BandeauRayon$')})
# ls_bloc_rayons = bloc_rayons.findAll('li')
data_rayons_json = json.loads(bloc_rayons['data-infomil-options'])
rayons_url = data_rayons_json['tConfigurationAjax']['RecuperationBandeau']['url']

# get rayons (ok to loop on subdepartments?)

rayons_response = urllib2.urlopen(rayons_url)
rayons_data = rayons_response.read()
rayons_soup = BeautifulSoup(rayons_data)

ls_sub_dpt_blocs = rayons_soup.findAll('a', {'class' : re.compile('_Sub$')})

ls_sub_dpts = [(unicode(sub_dpt_bloc.text), unicode(sub_dpt_bloc['href']))\
                 for sub_dpt_bloc in ls_sub_dpt_blocs]


sub_dpt_url = u'http://fd3-courses.leclercdrive.fr/magasin-090201-Athies-sous-Laon/rayon-284325-Boucherie.aspx'

# Loop on sub dpts
sub_dpt_title, sub_dpt_url = ls_sub_dpts[0]
sub_dpt_response = urllib2.urlopen(sub_dpt_url)
sub_dpt_data = sub_dpt_response.read()
#sub_dpt_soup = BeautifulSoup(sub_dpt_data)
data_products_json = json.loads(re.search(u'({"objContenu":{"lstElements":\[{"objElement":.*?}})\);',
                                          sub_dpt_data).group(1))
ls_products = data_products_json['objContenu']['lstElements']

#store_post = {'t:formdata' : store_tformdata}
#store_req = urllib2.Request(u'http://courses.carrefour.fr' + store_url,
#                            data = urllib.urlencode(store_post),
#                            headers = store_headers)
#store_response = urllib2.urlopen(store_req)
## pprint.pprint(cookie_jar.__dict__)
#
### ALTERNATIVE GO TO STORE PAGE (add cookies manually)
##cookie_jar.set_cookie(makeCookie("serviceDrive", "3"))
##cookie_jar.set_cookie(makeCookie("storeDrive", "215"))
##cookie_jar.set_cookie(makeCookie("browserSupportCheck", "checked"))
## pprint.pprint(cookie_jar.__dict__)
#
## GET DPTS AND SUBDPTS (PAGES TO VISIT)
#store_response_2 = urllib2.urlopen(drive_website_url + '/drive/accueil')
#store_data = store_response_2.read()
#store_soup = BeautifulSoup(store_data)
#
##ls_dsd_href = store_soup.findAll('a', {'class' : 'page',
##                                       'href' : re.compile('/drive/tous-les-rayons/*')})
#
#bloc_dpts = store_soup.find('div', {'class' : 'lowerLevel'})
#ls_dpt_blocs = bloc_dpts.findAll('li', {'class' : True,
#                                        'onmouseout' : True,
#                                        'onmouseover' : True})
#dict_dsds = {}
#for dpt_bloc in ls_dpt_blocs:
#  dpt_title = dpt_bloc.find('a', {'class' : 'page'}).text.strip()
#  # next line to avoid capturing url of dpt
#  dpt_sd_bloc = dpt_bloc.find('div', {'class' : 'nextLevel'})
#  ls_sd_blocs = dpt_sd_bloc.findAll('a', {'class' : 'page',
#                                         'href' : True})
#  ls_sds = [(sd_bloc.text, sd_bloc['href']) for sd_bloc in ls_sd_blocs]
#  dict_dsds[dpt_title] = ls_sds
#
#ls_products = []
## VISIT AND PARSE SUBDPT PAGES
#for dpt, ls_sds in dict_dsds.items():
#  for sub_dpt, sub_dpt_href in ls_sds:
#    # exclude pages displaying specific selections of products
#    if re.match('/drive/tous-les-rayons/', sub_dpt_href):
#      try:
#        response_3 = urllib2.urlopen(drive_website_url + sub_dpt_href)
#        data_3 = response_3.read()
#        soup_3 = BeautifulSoup(data_3)
#        
#        ls_sd_dict_products = parse_product_page(soup_3)
#        # scrap other pages if any
#        ac_param = sub_dpt_href.split('/')[-1]
#        for cookie in cookie_jar:
#          if cookie.name == 'JSESSIONID':
#            jsessionid = cookie.value
#        ls_page_nbs = extract_bs_text(soup_3.find('ul', {'class' : 'pageNumbers'}))
#        if ls_page_nbs and len(ls_page_nbs) > 1:
#          for page_nb in ls_page_nbs[1:]:
#            headers_page = {u'Host' : 'courses.carrefour.fr',
#                            u'Origin' : 'http://courses.carrefour.fr',
#                            u'Referer' : drive_website_url + sub_dpt_href +\
#                                         u';jsessionid=' + jsessionid,
#                            u'X-Requested-With' : u'XMLHttpRequest',
#                            u'X-Prototype-Version' : u'1.6.0.3',
#                            u'Content-type' : u'application/x-www-form-urlencoded; charset=UTF-8'}
#            data_page = {'t:ac' : ac_param}
#            req_page = urllib2.Request(u'http://courses.carrefour.fr/drive'+\
#                                       u'/rayon.categoryproductlistcontainer'+\
#                                       u'.paging.selectpage/{:s}?t:ac={:s}'.format(page_nb,
#                                                                                   ac_param),
#                                       data = urllib.urlencode(data_page),
#                                       headers = headers_page)
#            response_page = urllib2.urlopen(req_page)
#            data_page = response_page.read()
#            
#            json_content = json.loads(data_page)
#            data_prods = json_content['zones']['componentZone']
#            soup_prods = BeautifulSoup(data_prods)
#            ls_sd_dict_products += parse_product_page(soup_prods)
#        for dict_product in ls_sd_dict_products:
#          dict_product['department'] = dpt
#          dict_product['sub_department'] = sub_dpt
#        ls_products += ls_sd_dict_products
#      except Exception, e:
#        print [dpt, sub_dpt, sub_dpt_href]
#        print e
#
## todo: inspect Marché, Le fromage du marché: ls_promo
## seems ls_promo should be empty but returns ls_price (print soup)
#
##path_carrefour = os.path.join(path_data,
##                              u'data_drive_supermarkets',
##                              u'data_carrefour')
##
##today_date = date.today().strftime(u"%Y%m%d")
##
##enc_json(ls_products,
##         os.path.join(path_carrefour,
##                      u'data_source',
##                      u'data_json_carrefour_voisins',
##                      u'{:s}_carrefour_voisins'.format(today_date)))
##
##print today_date, len(ls_products)
