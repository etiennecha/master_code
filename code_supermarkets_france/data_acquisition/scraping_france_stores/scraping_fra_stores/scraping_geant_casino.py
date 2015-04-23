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
  
  # build urllib2 opener
  cookie_jar = cookielib.LWPCookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
  opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')]
  urllib2.install_opener(opener)
  
  # Brand (Geant Casino) page
  geant_brand_url = r'http://www.geantcasino.fr/pages/magasins/liste-magasins.aspx'
  response = urllib2.urlopen(geant_brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  block_stores = soup.find('div', {'id' : 'deux_colonnes_liste'})
  list_store_blocks = block_stores.findAll('li')
  
  list_store_names = [store_block.find('a').find(text=True).strip() for store_block in list_store_blocks]
  list_store_names = [' '.join(store_name.split()) for store_name in list_store_names]
  
  list_store_urls = [store_block.find('a')['href'].strip() for store_block in list_store_blocks]
  
  list_store_addresses = [store_block.find('p').findAll(text=True) for store_block in list_store_blocks]
  list_store_addresses = [map(lambda s: s.replace(u'\xa0', u' '), store_address) \
                            for store_address in list_store_addresses]
  
  list_store_general_info = [(store_name, store_url, store_address) for store_name, store_url, store_address in \
                              zip(list_store_names, list_store_urls, list_store_addresses)]
  
  # enc_json(list_store_general_info, path_data + folder_source_qlmc_chains + r'/list_geant_casino_general_info')
  
  # Visit store pages and extract infospratiques
  
  list_store_full_info = []
  for (store_name, store_url_extension, store_address) in list_store_general_info:
    response_store = urllib2.urlopen(r'http://www.geantcasino.fr' + store_url_extension)
    data_store = response_store.read()
    soup_store = BeautifulSoup(data_store)
    
    block_contact = soup_store.find('div', {'class' : 'droite'})
    try:
      sub_contact_1 = re.search(u'(.*?)<a href', unicode(block_contact), re.DOTALL).group(1)
      sub_contact_2 = re.search('<br />(.*)<br />', unicode(sub_contact_1), re.DOTALL).group(1)
      sub_contact_3 = [elt.replace('<b>', '').replace('</b>','').strip() for\
                        elt in sub_contact_2.split('<br />') if elt]
      sub_contact_4 = [elt.replace(u'\xa0', u' ') for elt in sub_contact_3]
      list_contact = sub_contact_4
    except:
      list_contact = []
    
    list_hours = []
    if soup_store.findAll('p', {'class' : 'horaires'}):
      list_hours = [elt.findAll(text = True) for elt in soup_store.findAll('p', {'class' : 'horaires'})]
    
    block_services = soup_store.find('ul', {'class' : 'maglisteservices'})
    list_block_services = block_services.findAll('li')
    list_services = []
    if list_block_services:
      list_services = [elt.span.string for elt in list_block_services]
    
    block_gps = soup_store.find('div', {'class' : 'coordonnees'})
    list_gps = []
    if block_gps:
      list_gps = block_gps.findAll(text = True)
    
    latitude, longitude, city, address, zip_code = None, None, None, None, None
    latitude = soup_store.find('input', {'id' : 'hid_lx'})['value']
    longitude = soup_store.find('input', {'id' : 'hid_ly'})['value']
    city = soup_store.find('input', {'id' : 'hid_cit'})['value']
    address = soup_store.find('input', {'id' : 'hid_adr'})['value']
    zip_code = soup_store.find('input', {'id' : 'hid_zip'})['value']
    
    store_info = {'name' : store_name,
                  'url' : store_url_extension,
                  'gps' : [latitude, longitude],
                  'address' : address,
                  'city' : city,
                  'zip' : zip_code,
                  'contact': list_contact,
                  'hours' : list_hours,
                  'services' : list_services}
    
    list_store_full_info.append(store_info)
  
  # enc_json(list_store_full_info, path_data + folder_source_qlmc_chains + r'/list_geant_casino_full_info')