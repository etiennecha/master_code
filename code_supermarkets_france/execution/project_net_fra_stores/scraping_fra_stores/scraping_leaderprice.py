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
  opener.addheaders = [(u'User-agent',
                        u'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11' +\
                          u'(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')]
  urllib2.install_opener(opener)
  
  brand_url = r'http://www.leaderprice.fr/listes-des-magasins-en-france'
  response = urllib2.urlopen(brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  list_store_general_info = []
  ls_bloc_tables = soup.findAll('table', {'class' : 'tab_liste'})
  for bloc_table in ls_bloc_tables:
    ls_td_stores = bloc_table.findAll('td')
    for td_store in ls_td_stores:
      list_store_general_info.append([td_store.find('a', {'href' : True})['href'],
                                      td_store.findAll(text=True)])

  list_store_full_info = []
  for store_url_ext, ls_store_address in list_store_general_info:
    try:
      store_url = u'http://www.leaderprice.fr/%s' %store_url_ext
      response = urllib2.urlopen(store_url)
      data = response.read()
      soup = BeautifulSoup(data)
      
      store_name = soup.title.text

      bloc_store_info = soup.find('div', {'class' : 'fichemagasin'})
      
      ls_address = bloc_store_info.find('div', {'class' : 'adresse'}).findAll(text=True)
      ls_hours = bloc_store_info.find('div', {'class' : 'horaires'}).findAll(text=True)
      bloc_access = bloc_store_info.find('div', {'class' : 'access'})
      ls_gps = []
      if bloc_access:
        bloc_map = bloc_access.find('script', {'type' : 'text/javascript'})
        if bloc_map:
          str_map = bloc_map.text
          re_gps = re.search(u'var\smagPoint\s=\snew\sgoogle\.maps\.LatLng\(([-0-9.]*),\s([-0-9.]*)\)',
                             str_map)
          if re_gps:
            ls_gps = [re_gps.group(1), re_gps.group(2)]
      list_store_full_info.append([store_name,
                                   ls_gps,
                                   [x.replace(u'\n', u'').replace(u'\t', u'') for x in ls_address\
                                      if x.replace(u'\n', u'').replace(u'\t', u'')],
                                   [x.replace(u'\n', u'').replace(u'\t', u'') for x in ls_hours\
                                      if x.replace(u'\n', u'').replace(u'\t', u'')],
                                   store_url_ext,
                                   ls_store_address])
    except:
      print store_url, 'not collected'

  #enc_json(list_store_general_info,
  #         path_data + folder_source_qlmc_chains + r'/list_leaderprice_general_info')
  #enc_json(list_store_full_info,
  #         path_data + folder_source_qlmc_chains + r'/list_leaderprice_full_info')
