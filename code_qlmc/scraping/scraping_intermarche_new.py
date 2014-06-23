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
  brand_url = r'https://www.intermarche.com/home/magasins/accueil.html'
  response = urllib2.urlopen(brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  ls_dpt_stores = soup.findAll('ul', {'class' : 'list-pdv'})
  ls_store_urls = []
  for dpt in ls_dpt_stores:
    for x in dpt.findAll('a', {'href' : re.compile('/home/magasins/accueil/.*')}):
      ls_store_urls.append(x['href'])

  # enc_json(ls_store_urls, path_data + folder_source_qlmc_chains + r'/list_intermarche_urls_new')
  
  # load existing and avoid collecting those which are already here
  
  ls_store_full_info = []
  ls_todo_urls = ls_store_urls
  #ls_store_full_info = dec_json(path_data + folder_source_qlmc_chains + r'/list_intermarche_full_info_new')
  #ls_done_urls = [x[0] for x in ls_store_full_info]
  #ls_todo_urls = [x for x in ls_store_urls if x not in ls_done_urls]
  
  for store_url in ls_todo_urls[0:1]: # ls_store_urls:
    store_full_url = r'https://www.intermarche.com' + store_url
    response_store = urllib2.urlopen(store_full_url)
    data_store = response_store.read()
    soup_store = BeautifulSoup(data_store)
    
    block_address = soup_store.find('div', {'class' : 'block_address clearfix'})
    block_img = block_address.find('img', {'src' : True, 'alt' : re.compile('Logo.*')})
    logo, ls_address = None, []
    if block_img:
      logo = block_img['src']
    if block_address.p:
      ls_address = block_address.p.findAll(text = True) # todo: standard cleaning

    block_info = soup_store.find('div', {'class' : 'block_infos clearfix'})
    block_schedule = soup_store.find('div', {'class' : 'schedule'})
    ls_schedule = []
    if block_schedule:
      ls_schedule = block_schedule.findAll(text = True)
     
    ls_services = []
    block_services = soup_store.find('div', {'class' : 'block_items clearfix'})
    if block_services:
      ls_block_services = block_services.findAll('div', {'class' : 'service_item clearfix'})
      for block_service in ls_block_services:
        if block_service.h3:
          ls_services.append(block_service.h3.text)
     
    store_info = [store_url,
                  logo,
                  ls_address,
                  ls_schedule,
                  ls_services]
    ls_store_full_info.append(store_info)

  # enc_json(ls_store_full_info, path_data + folder_source_qlmc_chains + r'/list_intermarche_full_info_new')
