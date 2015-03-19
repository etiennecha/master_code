#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import httplib
import urllib, urllib2
from bs4 import BeautifulSoup
import re
import json
import time

def enc_json(data, path_file):
  with open(path_file, 'w') as f:
    json.dump(data, f)

def dec_json(path_file):
  with open(path_file, 'r') as f:
    return json.loads(f.read())

path_qlmc_scrapped = os.path.join(path_data,
                                  'data_qlmc',
                                  'data_source',
                                  'data_scrapped')

start = time.time()

# Region map (todo: loop over region)
url = u'http://www.quiestlemoinscher.com/carte/ile-de-france'
response = urllib2.urlopen(url)
data = response.read()
soup = BeautifulSoup(data)
dict_params = {'region' : 'ile-de-france',
               'regionTitle' : 'Ile-de-France'}
headers = {'Referer' : url,
           'X-Requested-With' : 'XMLHttpRequest',
           #'X-Prototype-Version' : '1.6.0.3',
           'Content-type' : 'application/x-www-form-urlencoded; charset=UTF-8'}
params = urllib.urlencode(dict_params)  
req  = urllib2.Request('http://www.quiestlemoinscher.com/mapping/data', params, headers)
response_2 = urllib2.urlopen(req)
data_2 = response_2.read()
dict_reg_stores = json.loads(data_2)
print dict_reg_stores['signs'][0]

# Get competitors for a given store (todo: loop over stores within region)
store_id = dict_reg_stores['signs'][0]['slug']
url_store = u'http://www.quiestlemoinscher.com/carte/{:s}'.format(store_id)
response_store = urllib2.urlopen(url_store)
data_store = response_store.read()
soup_store = BeautifulSoup(data_store)
bloc_comp = soup_store.find('div', {'id' : 'contentChangeStore'})
ls_comp_blocs = bloc_comp.findAll('option', {'value' : True})
ls_comp_ids = [x['value'] for x in ls_comp_blocs if x['value']]

# Visit competitor's page
comp_id = ls_comp_ids[0]
url_comp = u'http://www.quiestlemoinscher.com/local/{:s}/{:s}'.\
              format(store_id, comp_id)
response_comp = urllib2.urlopen(url_comp)
data_comp = response_comp.read()
soup_comp = BeautifulSoup(data_comp)
# Get link to family/subfamilies of products
bloc_families = soup_comp.find('div', {'id' : 'menuLev2', 'class' : 'onTop'})
ls_family_blocs = bloc_families.findAll('ul', {'id' : True})
dict_families = {}
for family_bloc in ls_family_blocs:
  family_name = family_bloc['id']
  ls_subfamily_blocs = family_bloc.findAll('a', {'href' : True})
  ls_subfamilies = [(x.text, x['href']) for x in ls_subfamily_blocs]
  dict_families[family_name] = ls_subfamilies
# Get comparison result
bloc_comparison = soup_comp.find('div', {'id' : 'battleHomeLocal'})
ls_compa = [bloc_comparison.find('p', {'class' : 'mention'}).text,
            bloc_comparison.find('h2', {'class' : 'sign textblue'}).text,
            bloc_comparison.find('p', {'class' : 'result textblue'}).text,
            bloc_comparison.find('h2', {'class' : 'sign textred'}).text,
            bloc_comparison.find('p', {'class' : 'result textred'}).text]

# Visit competitor's (sub)family pages

#family = dict_families.keys()[0]
#sf, sf_url_extension = dict_families[family][0]

dict_comp =  {}
for family, ls_sub_families in dict_families.items():
  dict_comp[family] = {}
  for sf, sf_url_extension in ls_sub_families:
    print 'Ask for:', sf 
    sf_url = u'http://www.quiestlemoinscher.com{:s}'.format(sf_url_extension)
    sf_response = urllib2.urlopen(sf_url)
    sf_data = sf_response.read()
    print 'Got:', sf
    sf_soup = BeautifulSoup(sf_data)
    ls_prod_blocs = sf_soup.findAll('article', {'class' : 'listProducts'})
    ls_sf_products = []
    for prod_bloc in ls_prod_blocs:
      product_name = prod_bloc.find('div', {'class' : 'txtProducts'}).h3.text
      ls_prod_info = []
      ls_prod_sub_blocs = prod_bloc.findAll('div', {'class' : 'txtCompare'})
      for prod_sub_bloc in ls_prod_sub_blocs:
        releve_date = prod_sub_bloc.find('div', {'class' : 'mentionReleve'}).text
        psb_temp = prod_sub_bloc.find('div', {'class' : re.compile('signPrice*.')})
        releve_store = psb_temp.find('img')['src']
        releve_price = psb_temp.text
        ls_prod_info.append([releve_date, releve_store, releve_price])
      ls_sf_products.append([product_name, ls_prod_info])
    dict_comp[family][sf] = ls_sf_products

print time.time() - start

#file_name = '_VERSUS_'.join([store_id, comp_id]) + '.json'
#enc_json(dict_comp,
#         os.path.join(path_qlmc_scrapped,
#                      file_name))
