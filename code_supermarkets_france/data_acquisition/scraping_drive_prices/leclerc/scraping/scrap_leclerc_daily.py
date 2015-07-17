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

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

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
dict_drives = {drive['sNomMagasin'] : drive for drive in ls_drives}

ls_store_subset = [u"Bois d'Arcy",
                   u"Clermont Ferrand",
                   u"Saint-Médard-en-Jalles",
                   u"Lyon 9e",
                   u"Massy Palaiseau",
                   u"Trappes"]

## TO GET ALL
#ls_store_subset = dict_drives.keys()
## take non collected so far
#path_leclerc = os.path.join(path_data,
#                            u'data_drive_supermarkets',
#                            u'data_leclerc')
#today_date = date.today().strftime(u"%Y%m%d")
#ls_stores_collected = dec_json(os.path.join(path_leclerc,
#                                            u'data_source',
#                                            u'data_json_leclerc',
#                                            u'{:s}_ls_leclerc_all'.format(today_date)))
#ls_store_subset = [x for x in ls_store_subset if x not in ls_stores_collected]

dict_store_prices = {}
for store_id in ls_store_subset:
  try:
    # go to store page
    store_url = dict_drives[store_id]['sURLCourses']
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
    
    # Loop on sub dpts
    ls_products = []
    for sub_dpt_title, sub_dpt_url in ls_sub_dpts:
      sub_dpt_response = urllib2.urlopen(sub_dpt_url)
      sub_dpt_data = sub_dpt_response.read()
      #sub_dpt_soup = BeautifulSoup(sub_dpt_data)
      data_products_json = json.loads(re.search(u'({"objContenu":{"lstElements":\[{"objElement":.*?}})\);',
                                                sub_dpt_data).group(1))
      ls_sub_dpt_products = data_products_json['objContenu']['lstElements']
      for dict_product in ls_sub_dpt_products:
        dict_product['sub_dpt'] = sub_dpt_title
      ls_products += ls_sub_dpt_products
    dict_store_prices[store_id] = ls_products
  except Exception, e:
    print u'\nProblem with store {:s}'.format(store_id)
    print e

path_leclerc = os.path.join(path_data,
                            u'data_supermarkets',
                            u'data_drive',
                            u'data_leclerc')

today_date = date.today().strftime(u"%Y%m%d")

enc_json(dict_store_prices,
         os.path.join(path_leclerc,
                      u'data_source',
                      u'data_json_leclerc',
                      u'{:s}_dict_leclerc'.format(today_date)))

print today_date, len(dict_store_prices)

## TO GET ALL
#enc_json(dict_store_prices,
#         os.path.join(path_leclerc,
#                      u'data_source',
#                      u'data_json_leclerc',
#                      u'{:s}_dict_leclerc_all_2'.format(today_date)))
#
#ls_stores_all = dict_store_prices.keys()
#enc_json(ls_stores_all,
#         os.path.join(path_leclerc,
#                      u'data_source',
#                      u'data_json_leclerc',
#                      u'{:s}_ls_leclerc_all_2'.format(today_date)))
