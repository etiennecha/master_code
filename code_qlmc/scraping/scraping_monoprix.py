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
  
  # Brand (Monoprix) page (got to insist... sometimes page doesn't load)
  brand_url = r'http://www.monoprix.fr/TrouverMonMagasin/Nos-Magasins.aspx'
  response = urllib2.urlopen(brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  block_stores = soup.find('table', {'class' : 'data tm1'})
  list_store_blocks = block_stores.findAll('tr', {'class' : 'line'})
  list_store_general_info = []
  for store_block in list_store_blocks:
    store_type = store_block.td.string
    store_name = store_block.find('a').string
    store_url = store_block.find('a')['href']
    temp = store_block.find('a').parent
    list_store_address_temp = temp.findNextSiblings('td')
    list_store_address = [elt.string.encode('raw_unicode_escape').decode('utf-8') if elt.string else u'' \
                            for elt in list_store_address_temp ]
    list_store_general_info.append([store_type, store_name, store_url, list_store_address])
  
  # enc_json(list_store_general_info, path_data + folder_source_qlmc_chains + r'/list_monoprix_general_info')
  
  # Visit store pages and extract infospratiques
  list_store_full_info = []
  for (store_type, store_name, store_url, store_address) in list_store_general_info[0:1]:
    response_store = urllib2.urlopen(store_url)
    data_store = response_store.read()
    soup_store = BeautifulSoup(data_store)
    
    # # TODO: pbm to get gps...
    
    # store_address = soup_store.find('div', {'class' : 'adresse'})
    # store_gps = soup_store.find('div', {'class' : 'gps'})
    
    # store_hours = None
    # store_hours = soup_store.find('div', {'class' : 'Fright horaires'})
    # if store_hours:
      # store_hours = [elt.strip() for elt in store_hours.findAll(text = True) if elt.strip()]
    
    # latitude, longitude, city, address, zip_code, telephone = None, None, None, None, None, None
    # latitude = soup_store.find('input', {'name' : 'latitudeGPS'})['value']
    # longitude = soup_store.find('input', {'name' : 'longitudeGPS'})['value']
    # city = soup_store.find('input', {'name' : 'ville'})['value']
    # address = soup_store.find('input', {'name' : 'adresse'})['value']
    # zip_code = soup_store.find('input', {'name' : 'codePostal'})['value']
    # telephone = soup_store.find('input', {'name' : 'telephone'})['value']
    
    # store_info = {'name' : store_name,
                  # 'url' : url_extension,
                  # 'gps' : [latitude, longitude],
                  # 'address' : address,
                  # 'city' : city,
                  # 'zip' : zip_code,
                  # 'phone' : telephone,
                  # 'hours' : store_hours}
    
    # list_store_full_info.append(store_info)
  
  # enc_json(list_store_full_info, path_data + folder_source_qlmc_chains + r'/list_monoprix_full_info')