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
  
  brand_url = r'http://www.netto.fr/nos-magasins'
  response = urllib2.urlopen(brand_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  list_store_general_info = []
  ls_div_bloc_stores = soup.findAll('div', {'class' : 'shops'})
  for div_bloc_stores in ls_div_bloc_stores:
    ls_bloc_spans = div_bloc_stores.findAll('span', {'class' : 'shop'})
    for bloc_span in ls_bloc_spans:
      bloc_href = bloc_span.find('a', {'href' : True})
      list_store_general_info.append([bloc_href['href'],
                                      bloc_href.findAll(text=True)])
  
  list_store_full_info = []
  for store_url_ext, ls_store_city in list_store_general_info:
    try:
      store_url = u'http://www.netto.fr%s' %store_url_ext
      response = urllib2.urlopen(store_url)
      data = response.read()
      soup = BeautifulSoup(data)
      street = soup.find(u'div', {u'class' : re.compile(u'field\sfield-name-field-adresse.*')})
      zip_code = soup.find(u'div', {u'class' : re.compile(u'field\sfield-name-field-zipcode.*')})
      city = soup.find(u'div', {u'class' : re.compile(u'field\sfield-name-field-city.*')})
      hours = soup.find(u'div', {u'class' : re.compile(u'field\sfield-name-field-hours.*')})
      phone = soup.find(u'div', {u'class' : re.compile(u'field\sfield-name-field-phone.*')})
      ls_results = []
      for x in street, zip_code, city, hours, phone:
        if x:
          ls_results.append(x.findAll(text=True))
        else:
           ls_results.append([])
      list_store_full_info.append(ls_results)
    except:
      print store_url, 'not collected'

  #                                 [x.replace(u'\n', u'').replace(u'\t', u'') for x in ls_address\
  #                                    if x.replace(u'\n', u'').replace(u'\t', u'')],

  #enc_json(list_store_general_info,
  #         path_data + folder_source_qlmc_chains + r'/list_netto_info')
  #enc_json(list_store_full_info,
  #         path_data + folder_source_qlmc_chains + r'/list_netto_full_info')
