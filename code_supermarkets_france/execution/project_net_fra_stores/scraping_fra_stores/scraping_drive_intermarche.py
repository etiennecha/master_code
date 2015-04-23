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
  
  # Brand (intermarche) page
  brand_url = r'http://www.intermarche.com/courses_en_ligne'
  response = urllib2.urlopen(brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  list_store_general_info = []
  
  # block_stores = soup.find('div', {'class' : 'referencement pagelet_referencement_largePdvListe'})
  # list_store_blocks = block_stores.findAll('li')
  # for store_block in list_store_blocks:
    # list_zip_city = store_block.find('span', {'class' : 'column line liste_ville'}).findAll(text=True)
    # list_zip_city = [elt.strip() for elt in list_zip_city if elt.strip()]
    # name_address_block = store_block.find('a', {'href' : re.compile('/magasin_accueil')})
    # store_name = name_address_block.string
    # store_welcome_url = name_address_block['href']
    # store_name_address = name_address_block['title']
    # store_address = store_name_address.replace(store_name, '').strip()
    # store_info_url = store_block.find('a', {'href' : re.compile('/magasin_infos_pratiques')})['href']
    # list_store_general_info.append((store_name, store_address, list_zip_city, store_welcome_url, store_info_url))
    
  # enc_json(list_store_general_info, path_data + folder_source_qlmc_chains + r'/list_drive_intermarche_general_info')
  
  # Visit store pages and extract infos pratiques
  
  # list_store_full_info = []
  
  # for (store_name, store_address, list_zip_city, store_welcome_url, store_info_url) in list_store_general_info[0:1]:
    # store_url = r'http://www.intermarche.com/' + store_info_url
    # response_store = urllib2.urlopen(store_url)
    # data_store = response_store.read()
    # soup_store = BeautifulSoup(data_store)
      
    # # block_store_address = soup_store.find('div', {'class' : 'address'})
    # # store_address = []
    # # if block_store_address:
      # # store_address = [elt.strip() for elt in block_store_address.findAll(text = True)]
    
    # # # TODO: visit pages '/services'... otherwise incomplete
    # # block_store_services = soup_store.find('div', {'id' : 'store-services-block'})
    # # store_services = None
    
    # block_store_hours = soup_store.find('div', {'id' : 'store-opening-block'})
    # list_store_opening = []
    # if block_store_hours:
      # list_store_days = [elt.findAll(text = True) for elt in \
                          # block_store_hours.findAll('span', {'class' : \
                          # ['opening-schedule-label', 'day-pass-opening-schedule-label']})]
      # list_store_hours = [elt.findAll(text = True)  for elt in \
                          # block_store_hours.findAll('span', {'class' : 'opening-schedule-value'})]
      # list_store_opening = zip(list_store_days, list_store_hours)
    
    # latitude, longitude, city, address, zip_code, telephone = None, None, None, None, None, None
    # latitude = soup_store.find('input', {'name' : 'latitude'})['value']
    # longitude = soup_store.find('input', {'name' : 'longitude'})['value']
    # city = soup_store.find('input', {'name' : 'city'})['value']
    # address = soup_store.find('input', {'name' : 'adress'})['value']
    # zip_code = soup_store.find('input', {'name' : 'zipcode'})['value']
    # telephone = soup_store.find('input', {'name' : 'contact_phone'})['value']
    
    # store_info = {'name' : store_name,
                  # 'type' : store_type,
                  # 'url' : store_url_extension,
                  # 'gps' : [latitude, longitude],
                  # 'address' : address,
                  # 'city' : city,
                  # 'zip' : zip_code,
                  # 'phone' : telephone,
                  # 'hours' : list_store_opening}
      
      # list_store_full_info.append(store_info)
  # enc_json(list_store_full_info, path_data + folder_source_qlmc_chains + r'/list_drive_intermarche_full_info')