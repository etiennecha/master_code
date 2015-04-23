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
import pandas as pd

def enc_json(data, path_file):
  with open(path_file, 'w') as f:
    json.dump(data, f)

def dec_json(path_file):
  with open(path_file, 'r') as f:
    return json.loads(f.read())

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_qlmc_scraped = os.path.join(path_data,
                                  'data_qlmc',
                                  'data_source',
                                  'data_scraped')

path_csv = os.path.join(path_data,
                        'data_qlmc',
                        'data_built',
                        'data_csv')

dict_reg_leclerc = dec_json(os.path.join(path_qlmc_scraped,
                                         'dict_reg_leclerc_stores.json'))

dict_leclerc_comp = dec_json(os.path.join(path_qlmc_scraped,
                                          'dict_leclerc_comp.json'))

df_comp = pd.read_csv(os.path.join(path_csv,
                                   'qlmc_scraped',
                                   'df_competitors.csv'))

# Exclude Leclerc from competitors (not compared on website)
for leclerc_id, ls_comp in dict_leclerc_comp.items():
  ls_comp_cl = [comp for comp in ls_comp if comp['signCode'] != u'LEC']
  dict_leclerc_comp[leclerc_id] = ls_comp_cl

# Count all competitor pairs from website
ls_all_pairs = [(leclerc_id, comp['slug']\
                  for leclerc_id, ls_comp in dict_leclerc_comp.items()\
                    for comp in ls_comp]

# Count competitor pairs actually queried
# NB: fragile... loop on dict and order matters
ls_covered_comp = [] # should be stored and updated?
ls_collect_pairs = []
dict_reg_pairs = {}
for region, ls_leclerc in dict_reg_leclerc.items():
  ls_reg_pairs = []
  for leclerc in ls_leclerc:
    ls_comp = dict_leclerc_comp[leclerc['slug']]
    # keep competitors not met in scrapping so far (store itself included in list)
    ls_comp_todo = [comp for comp in ls_comp if\
                      (comp['slug'] not in ls_covered_comp)]
    # if all scraped, take first one to get current Leclerc's prices
    if not ls_comp_todo:
      ls_comp_todo = ls_comp[:1]
    for comp in ls_comp_todo:
      ls_collect_pairs.append((leclerc['slug'], comp['slug']))
      ls_reg_pairs.append((leclerc['slug'], comp['slug']))
      ls_covered_comp.append(comp['slug'])
  dict_reg_pairs[region] = ls_reg_pairs

# List competitor pairs not collected (on purpose)
ls_exclude_pairs = [(leclerc_id, comp_id) for (leclerc_id, comp_id) in ls_all_pairs\
                      if (leclerc_id, comp_id) not in ls_collect_pairs]

print u'\nTotal nb pairs listed on website {:d}'.format(len(ls_all_pairs))
print u'\nNumber of pairs queried {:d}'.format(len(ls_pairs))
