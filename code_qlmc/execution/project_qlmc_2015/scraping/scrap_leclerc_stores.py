#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import httplib
import urllib, urllib2
from bs4 import BeautifulSoup
import re
import json
import collections

def enc_json(data, path_file):
  with open(path_file, 'w') as f:
    json.dump(data, f)

def dec_json(path_file):
  with open(path_file, 'r') as f:
    return json.loads(f.read())

path_qlmc_scraped = os.path.join(path_data,
                                  'data_qlmc',
                                  'data_source',
                                  'data_scraped')

# France map
url = u'http://www.quiestlemoinscher.com'
#response = urllib2.urlopen(url)
#data = response.read()
#soup = BeautifulSoup(data)
dict_params = {'regions' : '1'}
headers = {'Referer' : url,
           'X-Requested-With' : 'XMLHttpRequest',
           #'X-Prototype-Version' : '1.6.0.3',
           'Content-type' : 'application/x-www-form-urlencoded; charset=UTF-8'}
params = urllib.urlencode(dict_params)  
req  = urllib2.Request('http://www.quiestlemoinscher.com/mapping/data', params, headers)
response = urllib2.urlopen(req)
data = response.read()
dict_data = json.loads(data)
ls_fra_reg = [(x['title'], x['slug']) for x in dict_data['data']]

# Get leclerc stores from each region
dict_reg_stores = {}
for reg_title, reg_slug in ls_fra_reg:
  url_reg = u'http://www.quiestlemoinscher.com/carte/{:s}'.format(reg_slug)
  #response_reg = urllib2.urlopen(url_reg)
  #data_reg = response_reg.read()
  #soup_reg = BeautifulSoup(data_reg)
  dict_params = {u'region' : reg_slug.encode('utf-8'),
                 u'regionTitle' : reg_title.encode('utf-8')}
  headers = {'Referer' : url_reg,
             'X-Requested-With' : 'XMLHttpRequest',
             #'X-Prototype-Version' : '1.6.0.3',
             'Content-type' : 'application/x-www-form-urlencoded; charset=UTF-8'}
  params = urllib.urlencode(dict_params)  
  req  = urllib2.Request('http://www.quiestlemoinscher.com/mapping/data', params, headers)
  response_2 = urllib2.urlopen(req)
  data_2 = response_2.read()
  dict_reg_data = json.loads(data_2)
  ls_reg_stores = dict_reg_data['signs']
  dict_reg_stores[reg_slug] = ls_reg_stores

# Check unicity of leclerc ids => no: pbm in Corse
ls_leclerc_ids = [x['slug'] for k, v in dict_reg_stores.items() for x in v]
#ls_unique_leclerc_ids = list(set(ls_leclerc_ids))
ls_duplicates = [x for x, y in collections.Counter(ls_leclerc_ids).items() if y > 1]
for reg_slug, ls_reg_stores in dict_reg_stores.items():
  for store in ls_reg_stores:
    if store['slug'] in ls_duplicates:
      print '\n', reg_slug, store

# Get rid of duplicates in Corse (dup w/ Picardie): could imply other issues?
ls_corse_stores = [x for x in dict_reg_stores['corse']\
                     if x not in dict_reg_stores['picardie']]
dict_reg_stores['corse'] = ls_corse_stores

## Store Leclerc stores
#enc_json(dict_reg_stores,
#         os.path.join(path_qlmc_scraped,
#                      'dict_reg_leclerc_stores.json'))
