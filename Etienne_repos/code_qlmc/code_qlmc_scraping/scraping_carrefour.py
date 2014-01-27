#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import cookielib
import re
import string
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
  
  # # Build urllib2 opener
  # cookie_jar = cookielib.LWPCookieJar()
  # opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
  # opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')]
  # urllib2.install_opener(opener)
  
  # Brand (carrefour) page
  brand_url = r'http://www.carrefour.fr/nos-magasins/liste-carrefour'
  response = urllib2.urlopen(brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  block_other_types = soup.find('ul', {'id' : 'brand-store-name'})
  list_typle_blocks = block_other_types.findAll('a', {'href' : re.compile(r'/nos-magasins/.*')})
  list_types = [(type_block.string, type_block['href']) for type_block in list_typle_blocks]
  # First type is current: (u'Carrefour', u'/nos-magasins/liste-carrefour')
  
  list_store_general_info = []
  for type_name , type_url_extension in list_types:
    response_type = urllib2.urlopen(r'http://www.carrefour.fr' + type_url_extension)
    data_type = response_type.read()
    soup_type = BeautifulSoup(data_type)
    block_stores = soup_type.find('ul', {'id' : 'brand-store-names'})
    list_store_blocks = block_stores.findAll('a', {'href' : re.compile(r'/magasin/.*')})
    list_store_temp = [(store_block.string, store_block['href'], type_name) for store_block in list_store_blocks]
    list_store_general_info += list_store_temp
  
  # enc_json(list_store_general_info, path_data + folder_source_qlmc_chains + r'/list_carrefour_general_info')
  
  # Visit store pages and extract infos pratiques
  # 2358 pages to visit hence split the job (slightly varies...)
  
  # list_store_full_info = []
  list_store_full_info = dec_json(path_data + folder_source_qlmc_chains + r'/list_carrefour_full_info')
  
  for (store_name, store_url_extension, store_type) in list_store_general_info:
    if store_url_extension not in [store['url'] for store in list_store_full_info]:
      store_url = r'http://www.carrefour.fr' + store_url_extension
      response_store = urllib2.urlopen(store_url)
      data_store = response_store.read()
      soup_store = BeautifulSoup(data_store)
      
      # block_store_address = soup_store.find('div', {'class' : 'address'})
      # store_address = []
      # if block_store_address:
        # store_address = [elt.strip() for elt in block_store_address.findAll(text = True)]
      
      # # TODO: visit pages '/services'... otherwise incomplete
      # block_store_services = soup_store.find('div', {'id' : 'store-services-block'})
      # store_services = None
      
      block_store_hours = soup_store.find('div', {'id' : 'store-opening-block'})
      list_store_opening = []
      if block_store_hours:
        list_store_days = [elt.findAll(text = True) for elt in \
                            block_store_hours.findAll('span', {'class' : \
                            ['opening-schedule-label', 'day-pass-opening-schedule-label']})]
        list_store_hours = [elt.findAll(text = True)  for elt in \
                            block_store_hours.findAll('span', {'class' : 'opening-schedule-value'})]
        list_store_opening = zip(list_store_days, list_store_hours)
      
      latitude, longitude, city, address, zip_code, telephone = None, None, None, None, None, None
      latitude = soup_store.find('input', {'name' : 'latitude'})['value']
      longitude = soup_store.find('input', {'name' : 'longitude'})['value']
      city = soup_store.find('input', {'name' : 'city'})['value']
      address = soup_store.find('input', {'name' : 'adress'})['value']
      zip_code = soup_store.find('input', {'name' : 'zipcode'})['value']
      telephone = soup_store.find('input', {'name' : 'contact_phone'})['value']
      
      store_info = {'name' : store_name,
                    'type' : store_type,
                    'url' : store_url_extension,
                    'gps' : [latitude, longitude],
                    'address' : address,
                    'city' : city,
                    'zip' : zip_code,
                    'phone' : telephone,
                    'hours' : list_store_opening}
      
      list_store_full_info.append(store_info)
  # enc_json(list_store_full_info, path_data + folder_source_qlmc_chains + r'/list_carrefour_full_info')