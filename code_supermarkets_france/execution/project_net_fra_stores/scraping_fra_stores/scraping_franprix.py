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
  # pattern_block = ur'google\.maps\.event\.addListener.*?window\.markersArray\.push\(marker\);' # WRONG
  pattern_block = ur'var\slat\s=.*?StoreRef\.init\(\);'
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

  # Visit store pages
  list_store_full_info = []
  for store_info in list_store_general_info:
    store_url = u'http://www.franprix.fr' + store_info['url']
    response = urllib2.urlopen(store_url)
    data = response.read()
    soup = BeautifulSoup(data)
    
    bloc_address = soup.find('div', {'class' : "franprix_address border_bottom"})
    ls_address = []
    if bloc_address:
      ls_address = bloc_address.findAll(text=True)
      ls_address = [x.replace(u'\n', u'').replace(u'&bull;', u'').strip() for x in ls_address\
                      if x.replace(u'\n', u'').replace(u'bull;', u'').strip()]
    
    bloc_schedule = soup.find('div', {'class' : "franprix_schedules border_bottom"})
    ls_schedule = []
    if bloc_schedule:
      bloc_table_schedule = bloc_schedule.find('table', {'class' : 'schedules'})
      if bloc_table_schedule:
        for tr in bloc_table_schedule.findAll('tr'):
          ls_schedule.append([x.replace(u'\n', u'').replace(u'&bull;', u'').strip() for x in tr.findAll(text=True)\
                                if x.replace(u'\n', u'').replace(u'bull;', u'').strip()])

    bloc_services = soup.find('div', {'class' : "franprix_services border_bottom"})
    ls_services = []
    if bloc_services:
      ls_bloc_services = bloc_services.findAll('img', {'src' : True, 'title' : True})
      for bloc_service in ls_bloc_services:
        ls_services.append(bloc_service['title'])
          
    list_store_full_info.append([store_info['url'],
                                 store_info['address'],
                                 store_info['gps'],
                                 ls_address,
                                 ls_schedule,
                                 ls_services])

  #enc_json(list_store_general_info, path_data + folder_source_qlmc_chains + r'/list_franprix_general_info')
  #
  #enc_json(list_store_full_info, path_data + folder_source_qlmc_chains + r'/list_franprix_full_info')
