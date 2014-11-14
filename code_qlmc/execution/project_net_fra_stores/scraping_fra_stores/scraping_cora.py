#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import cookielib
import re
import string
import ast
from datetime import date

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

if __name__=="__main__":
  if os.path.exists(r'W:/Bureau/Etienne_work/Data'):
    path_data = r'W:/Bureau/Etienne_work/Data'
  else:
    path_data = r'C:/Users/etna/Desktop/Etienne_work/Data'
  # structure of the data folder should be the same
  folder_source_qlmc_chains = '/data_qlmc/data_source/data_chain_websites'
  
  # build urllib2 opener
  cookie_jar = cookielib.LWPCookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
  opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')]
  urllib2.install_opener(opener)
  
  # Brand (Auchan) page
  brand_url = r'http://www.cora.fr/lentreprise/nos-magasins.html'
  response = urllib2.urlopen(brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  block_stores = re.search(u'var\scoraImp\s=\s(\[\[.*?\]\])', unicode(soup), re.DOTALL)
  block_stores = block_stores.group(1)
  list_stores = ast.literal_eval(block_stores)
  
  list_store_general_info = []
  for store in list_stores:
    store_info = {'name' : store[0],
                  'street' : store[1].replace('&lt;br', ' ').replace('/&gt;', ' ').decode('utf-8'),
                  'zip_city' : store[2].decode('utf-8'),
                  'gps' : [store[3], store[4]],
                  'short_id' : store[6]}
    list_store_general_info.append(store_info)
  
  # enc_json(list_store_general_info, path_data + folder_source_qlmc_chains + r'/list_cora_general_info')
  
  #TODO: add url and visit store pages (not sure it will be of any use though)
  
  # Visit store pages and extract infospratiques
  
  # list_store_full_info = []
  # for (store_name, store_url) in list_store_general_info:
    # # may need to rebuild opener here (reinitiate cookies)
    # response_store = urllib2.urlopen(store_url)
    # response_store = urllib2.urlopen(store_url.replace('accueil', 'informations-pratiques'))
    # data_store = response_store.read()
    # soup_store = BeautifulSoup(data_store)
    
    # block_opening_address = soup_store.find('div', {'class' : 'welcome'})
    # list_blocks_opening_address = block_opening_address.findAll('p',{'class' : None})
    # list_opening_address = []
    # if list_blocks_opening_address:
      # list_opening_address = [elt.findAll(text = True) for elt in list_blocks_opening_address]

    # block_opening_phone = soup_store.find('div', {'class' : 'aside rounded infos'})
    # list_blocks_opening_phone = block_opening_phone.findAll('p', {'class' : 'details'})
    # list_opening_phone = [elt.findAll(text = True) for elt in list_blocks_opening_phone]
    
    # block_gps = soup_store.find('div', {'class' : 'rounded coordonnees'})
    # list_gps = []
    # if block_gps:
      # list_gps = block_gps.findAll(text = True)
    
    # store_info = {'name' : store_name,
                  # 'url' : store_url,
                  # 'list_opening_address' : list_opening_address,
                  # 'list_opening_phone' : list_opening_phone,
                  # 'gps' : list_gps}
    
    # list_store_full_info.append(store_info)
  
  # enc_json(list_store_full_info, path_data + folder_source_qlmc_chains + r'/list_cora_full_info')