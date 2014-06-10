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
import time

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
  
  # # build urllib2 opener
  # cookie_jar = cookielib.LWPCookieJar()
  # opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
  # opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')]
  # urllib2.install_opener(opener)
  
  # Brand (Super Casino) page
  casino_brand_url = r'http://www.casino.fr/liste-magasin-casino.html'
  response = urllib2.urlopen(casino_brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  list_block_dpts = soup.findAll('a', {'href' : re.compile('/magasins/page.*')})
  list_dpt_urls = [block_dpt['href'] for block_dpt in list_block_dpts]
  
  list_store_general_info = []
  
  # list_dpt_urls[0].index('1') # u'/magasins/page-1/7-magasin-casino-haut-rhin-68.html'
  # test = [elt for elt in list_dpt_urls if elt[list_dpt_urls[0].index('1')] != '1']
  # # Hence: can loop replacing the 15th element and break if no store in page
  
  for dpt_url in list_dpt_urls:
    for i in range(1,8):
      time.sleep(10)
      dpt_url = dpt_url[:15] + '%s' %i + dpt_url[16:]
      print 'Visiting', dpt_url
      dpt_response = urllib2.urlopen(r'http://www.casino.fr' + dpt_url)
      dpt_data = dpt_response.read()
      dpt_soup = BeautifulSoup(dpt_data)
      
      if dpt_soup.findAll('div', {'class' : re.compile('blocResultRechercheMag.*')}):
        pattern_block_google_map = ur'google\.load\("maps", "2\.x"\).*?google\.setOnLoadCallback\(initialize\)'
        block_google_map = re.search(pattern_block_google_map, dpt_data, re.DOTALL)
        if block_google_map:
          pattern_gps = ur'\smarkers\[.*?google\.maps\.LatLng\([0-9]{0,2}\.[0-9]{0,20},[0-9]{0,2}\.[0-9]{0,20}\),'
          list_gps_blocks = re.findall(pattern_gps, block_google_map.group(0))
          if list_gps_blocks:
            dict_gps = {}
            for gps_block in list_gps_blocks:
              marker = re.search(ur'markers\[(.*?)\]', gps_block).group(1)
              gps = re.search(ur'LatLng\(([0-9]{0,2}\.[0-9]{0,20},[0-9]{0,2}\.[0-9]{0,20})\)', gps_block).group(1)
              gps = map(lambda x: float(x), gps.split(','))
              dict_gps[marker] = gps
          else:
            dict_gps = {}
        else:
          dict_gps = {}
        
        list_block_stores = dpt_soup.findAll('div', {'class' : re.compile('blocResultRechercheMag.*')})
        for block_store in list_block_stores:
          store_id = block_store['id']
          store_url = block_store.find('a', {'class': 'info'})['href']
          gps = None
          if block_store.find('a', {'class': 'plan'}):
            store_plan = block_store.find('a', {'class': 'plan'})['onclick']
            store_marker = re.search(ur'focusMagasin\((.*?)\)', store_plan).group(1)
            gps = dict_gps.get(store_marker, None)
          store_name = re.sub(u'^[0-9]{1,2}\. ','',block_store.find('h3').string)
          store_address = block_store.find('p').findAll(text = True)
          list_store_address = [elt.strip() for elt in store_address if elt]
          
          store_general_info = {'id' : store_id,
                                'url' : store_url,
                                'name' : store_name,
                                'address' : store_address,
                                'gps' : gps,
                                'address' : list_store_address}
                                
          list_store_general_info.append(store_general_info)
      else:
        break
  
  # enc_json(list_store_general_info, path_data + folder_source_qlmc_chains + r'/list_super_casino_general_info')
  
  # enc_json(list_store_full_info, path_data + folder_source_qlmc_chains + r'/list_super_casino_full_info')