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
  
  list_store_general_info = []
  # DIA dpt page
  for dpt in range(1,96):
    brand_url = r'http://www.dia.fr/trouver-un-magasin/magasins-par-departement/?dept=%s' %dpt
    response = urllib2.urlopen(brand_url)
    data = response.read()
    soup = BeautifulSoup(data)

    ls_js_blocs = soup.findAll('script', {'type' : 'text/javascript'})
    for js_bloc in ls_js_blocs:
      if re.search(u'/\\*<!\\[CDATA\\[\\*/\s\\\n\svar\sgeocoder', js_bloc.text):
        str_stores = js_bloc.text
        break
    
    # get list of store blocs
    #ls_store_blocks = re.findall(u"markerContent\s=\s'(.*?)';\\\n\s\s\s\sinfoWindow.setContent\(markerContent\)", str_stores)
    ls_bloc_stores = re.findall(u"marker\[[0-9]{1,4}\]\s=\snew google.maps.Marker\({"+\
                                  u".*?"+\
                                  u"infoWindow.setContent\(markerContent\);\\\n\s\s\s\sinfoWindow.open\(map,\sthis\);\s\s\s\s\\\n}\);",
                                str_stores,
                                re.DOTALL)
    # for each store
    for bloc_store in ls_bloc_stores:
      re_gps = re.search(u'position:\snew google\.maps\.LatLng\(([-0-9.]*),\s([-0-9.]*)\)', bloc_store)
      ls_store_gps = []
      if re_gps:
        ls_store_gps = [re_gps.group(1), re_gps.group(2)]
      re_store_info = re.search(u"markerContent\s=\s'(.*?)';\\\n\s\s\s\sinfoWindow.setContent\(markerContent\)", bloc_store)
      ls_store_name, ls_store_address = [], []
      if re_store_info:
        bloc_store_info = BeautifulSoup(re_store_info.group(1))
        ls_store_name = bloc_store_info.find('a', {'href' : '###LIEN_DETAIL###'}).findAll(text=True)
        ls_store_address = bloc_store_info.find('p', {'class' : 'address'}).findAll(text=True)
      bloc_details = bloc_store_info.find('div', {'class' : 'detail'})
      ls_store_details = []
      if bloc_details:
        ls_store_details = bloc_details.findAll(text=True)
      list_store_general_info.append([ls_store_name,
                                      ls_store_gps,
                                      ls_store_address,
                                      ls_store_details])
                                  
  enc_json(list_store_general_info, path_data + folder_source_qlmc_chains + r'/list_dia_general_info')
  
  # enc_json(list_store_full_info, path_data + folder_source_qlmc_chains + r'/list_dia_full_info')
