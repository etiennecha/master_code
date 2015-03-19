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

path_qlmc_scrapped = os.path.join(path_data,
                                  'data_qlmc',
                                  'data_source',
                                  'data_scrapped')

dict_reg_leclerc = dec_json(os.path.join(path_qlmc_scrapped,
                                         'dict_reg_leclerc_stores.json'))

dict_leclerc_comp = {}
for reg_slug, ls_reg_leclerc in dict_reg_leclerc.items():
  for leclerc in ls_reg_leclerc:
    leclerc_id = leclerc['slug']
    #url_leclerc = u'http://www.quiestlemoinscher.com/carte/{:s}'.format(leclerc_id)
    #response_leclerc = urllib2.urlopen(url_leclerc)
    #data_leclerc = response_leclerc.read()
    #soup_leclerc = BeautifulSoup(data_leclerc)
    #bloc_comp = soup_leclerc.find('div', {'id' : 'contentChangeStore'})
    #ls_comp_blocs = bloc_comp.findAll('option', {'value' : True})
    #ls_comp_ids = [x['value'] for x in ls_comp_blocs if x['value']]
    #dict_leclerc_comp[leclerc_id] = ls_comp_ids
    dict_params = {'store' : leclerc_id}
    headers = {'Referer' : 'http://www.quiestlemoinscher.com/carte/{:s}'.format(leclerc_id),
               'X-Requested-With' : 'XMLHttpRequest',
               #'X-Prototype-Version' : '1.6.0.3',
               'Content-type' : 'application/x-www-form-urlencoded; charset=UTF-8'}
    params = urllib.urlencode(dict_params)  
    req  = urllib2.Request('http://www.quiestlemoinscher.com/mapping/data', params, headers)
    response = urllib2.urlopen(req)
    data = response.read()
    dict_data = json.loads(data)
    ls_leclerc_comp = dict_data['signs']
    dict_leclerc_comp[leclerc_id] = ls_leclerc_comp

# Unique comp
ls_comp_ids = [x['slug'] for k,v in dict_leclerc_comp.items() for x in v]
ls_unique_comp_ids = list(set(ls_comp_ids))

# Check if really duplicates? (is slug really a unique identifier?)
ls_duplicates = [x for x, y in collections.Counter(ls_comp_ids).items() if y > 1]
ls_all_comp = [x for k,v in dict_leclerc_comp.items() for x in v]
# Looks ok... need to generalize
for x in ls_all_comp:
  if x['slug'] == ls_duplicates[0]:
    print x

## Store Leclerc competitors
#enc_json(dict_leclerc_comp,
#         os.path.join(path_qlmc_scrapped,
#                      'dict_leclerc_comp.json'))
