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
  
  # Brand (Leclerc) page
  brand_url = r'http://www.e-leclerc.com/magasin'
  response = urllib2.urlopen(brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  block_stores = soup.find('div', {'class' : 'liste_magasins'})
  list_store_blocks = block_stores.findAll('li') 
  list_store_general_info = []
  for store_block in list_store_blocks:
    store_name = store_block.find('h4', {'class' : 'nom_magasin'}).string
    store_city_cp = store_block.find('span', {'class' : 'ville_cp_magasin'}).findAll(text=True)
    store_url = store_block.find('a', {'class' : 'button btnRentrer'})['href']
    list_store_general_info.append([store_name, store_city_cp, store_url])
  
  # enc_json(list_store_general_info, path_data + folder_source_qlmc_chains + r'/list_leclerc_general_info')
  
  # Visit store pages and extract infospratiques
  list_store_full_info = []
  for (store_name, store_city_cp, url_extension) in list_store_general_info:
    store_url = brand_url.replace('/magasin', '') + url_extension + r'/infospratiques'
    response_store = urllib2.urlopen(store_url)
    data_store = response_store.read()
    soup_store = BeautifulSoup(data_store)
    
    store_address = soup_store.find('div', {'class' : 'adresse'})
    store_gps = soup_store.find('div', {'class' : 'gps'})
    
    store_hours = None
    store_hours = soup_store.find('div', {'class' : 'Fright horaires'})
    if store_hours:
      store_hours = [elt.strip() for elt in store_hours.findAll(text = True) if elt.strip()]
    
    latitude, longitude, city, address, zip_code, telephone = None, None, None, None, None, None
    latitude = soup_store.find('input', {'name' : 'latitudeGPS'})['value']
    longitude = soup_store.find('input', {'name' : 'longitudeGPS'})['value']
    city = soup_store.find('input', {'name' : 'ville'})['value']
    address = soup_store.find('input', {'name' : 'adresse'})['value']
    zip_code = soup_store.find('input', {'name' : 'codePostal'})['value']
    telephone = soup_store.find('input', {'name' : 'telephone'})['value']
    
    store_info = {'name' : store_name,
                  'url' : url_extension,
                  'gps' : [latitude, longitude],
                  'address' : address,
                  'city' : city,
                  'zip' : zip_code,
                  'phone' : telephone,
                  'hours' : store_hours}
    
    list_store_full_info.append(store_info)
  
  # enc_json(list_store_full_info, path_data + folder_source_qlmc_chains + r'/list_leclerc_full_info')