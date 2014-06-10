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
  
  # Brand (Franprix) page
  brand_url = r'http://www.franprix.fr/localiser-votre-magasin'
  response = urllib2.urlopen(brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  list_store_general_info = []
  pattern_block = ur'google\.maps\.event\.addListener.*?window\.markersArray\.push\(marker\);'
  list_store_blocks = re.findall(pattern_block, data, re.DOTALL)
  for store_block in list_store_blocks[:-1]:
    latitude = re.search(ur'var lat = "(.*?)"', store_block).group(1)
    longitude = re.search(ur'var lng = "(.*?)"', store_block).group(1)
    store_address = re.search(ur'title: "(.*?)"', store_block).group(1)
    store_url = re.search(ur"\$\.get\('(.*?)'", store_block).group(1)
    
    store_info = {'url' : store_url,
                  'address' : store_address,
                  'gps' : [float(latitude), float(longitude)]}
    
    list_store_general_info.append(store_info)
  
  # enc_json(list_store_general_info, path_data + folder_source_qlmc_chains + r'/list_franprix_general_info')
  
  # enc_json(list_store_full_info, path_data + folder_source_qlmc_chains + r'/list_franprix_full_info')