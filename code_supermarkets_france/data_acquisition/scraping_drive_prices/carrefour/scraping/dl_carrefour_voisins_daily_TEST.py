#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import httplib, urllib2
import urllib
import cookielib
from cookielib import Cookie
from BeautifulSoup import BeautifulSoup
import string
import re
from datetime import date
import json

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

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
# structure of the data folder should be the same
folder_source_carrefour_voisins_prices = r'\data_drive_supermarkets\data_carrefour\data_source\data_json_carrefour_voisins'
   
# build urllib2 opener
cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.172 Safari/537.22')]
urllib2.install_opener(opener)

# get list of stores
drive_website_url = r'http://courses.carrefour.fr'
response = urllib2.urlopen(drive_website_url + r'/drive/accueil')
data = response.read()
soup = BeautifulSoup(data)

# go on store page
shop_blocs = soup.findAll('li', {'class' : 'shop'})
shop_voisin = soup.find('li', {'id' : 215, 'class' : 'shop'})
shop_voisin_href = shop_voisin.find('a')['href']

post_args = {'id' : 'drivePickingForm_176',
             'name' : 'drivePickingForm_176'}
req = urllib2.Request(drive_website_url + shop_voisin_href)
req.add_data(urllib.urlencode(post_args))
response_2 = urllib2.urlopen(req)
data_2 = response_2.read()
soup_2 = BeautifulSoup(data_2)

# need to play with cookies to get products
cookie_jar.set_cookie(makeCookie("serviceDrive", "3"))
cookie_jar.set_cookie(makeCookie("storeDrive", "215"))
cookie_jar.set_cookie(makeCookie("browserSupportCheck", "checked"))
# pprint.pprint(cookie_jar.__dict__)

product_links = soup_2.findAll('a', {'class' : 'page', 'href' : re.compile('/drive/tous-les-rayons/*')})
master_departments = []
master_products = []
for product_link in product_links[1:]:
  if product_link.find('img', {'alt':''}):
    # a bit fragile
    department = product_link.text
  else:
    sub_department_link  = product_link['href']
    sub_departement = product_link.text
    try:
      master_departments.append([department, sub_departement, sub_department_link])
      response_3 = urllib2.urlopen(drive_website_url + sub_department_link)
      data_3 = response_3.read()
      soup_3 = BeautifulSoup(data_3)
      product_lis = soup_3.findAll('li', {'class' : 'product'})
      for product_li in product_lis:
        product_title = product_li.find('h3').findAll(text=True)
        block_price = product_li.find('div', {'class' : 'specs priceSpecs'})
        # block_price (precaution)
        ls_block_price = block_price.findAll(text=True)
        # block promo (precaution)
        ls_block_promo = []
        block_promo_price = block_price.find('div', {'class' : 'priceBlock promoBlock'})
        if block_promo_price:
          ls_block_promo = block_promo_price.findAll(text=True)
        # heding promo
        ls_heading = []
        block_heading = block_price.find('h4', {'class' : 'heading'})
        if block_heading:
          ls_heading = block_heading.findAll(text= True)
        # reduction promo
        ls_reduction = []
        block_reduction = block_price.find('div', {'class' : 'spec reduction'})
        if block_reduction:
          ls_redudction = block_reduction.findAll(text=True)
        # regular price
        ls_regular_price = []
        block_regular_price = block_price.find('div', {'class' : 'spec price'})
        if block_regular_price:
          ls_regular_price = block_regular_price.findAll(text=True)
        # format
        ls_format = []
        block_format = block_price.find('span', {'class' : 'unit'})
        if block_format:
          ls_format = block_format.findAll(text=True)
        # unit price
        ls_unit_price = []
        block_unit_price = block_price.find('div', {'class' : 'unitPrice'})
        if block_unit_price:
          ls_unit_price = block_unit_price.findAll(text=True)
        
        dict_products = {'product_title' : product_title,
                         'ls_block_price' : ls_block_price,
                         'ls_block_promo' : ls_block_promo,
                         'ls_heading' : ls_heading,
                         'ls_reduction': ls_reduction,
                         'ls_regular_price' : ls_regular_price,
                         'ls_format' : ls_format,
                         'ls_unit_price' : ls_unit_price,
                         'subdepartment' : sub_departement,
                         'department' : department}
        master_products.append(dict_products)
    except Exception, e:
      print [department, sub_departement, sub_department_link]
      print e

# today_date = date.today().strftime("%y%m%d")
# enc_stock_json(master_products, path_data + folder_source_carrefour_voisins_prices +\
                                # r'\20%s_carrefour_voisins' %today_date)
# print today_date, len(master_products)