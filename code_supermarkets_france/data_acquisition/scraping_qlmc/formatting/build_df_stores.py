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
                                 'data_supermarkets',
                                 'data_source',
                                 'data_qlmc_2015',
                                 'data_scraped_201503')

path_csv = os.path.join(path_data,
                        'data_supermarkets',
                        'data_built',
                        'data_qlmc_2015',
                        'data_csv_201503')

dict_reg_leclerc = dec_json(os.path.join(path_qlmc_scraped,
                                         'dict_reg_leclerc_stores.json'))

dict_leclerc_comp = dec_json(os.path.join(path_qlmc_scraped,
                                          'dict_leclerc_comp.json'))

# dict_leclerc_comp should contain all stores including leclerc
ls_rows_comp = []
for leclerc_id, ls_stores in dict_leclerc_comp.items():
  for store in ls_stores:
    ls_rows_comp.append([store['slug'],
                         store['city'],
                         store['title'],
                         store['signCode'],
                         store['latitude'],
                         store['longitude'],
                         leclerc_id])

df_comp = pd.DataFrame(ls_rows_comp, columns = ['store_id',
                                                'store_city',
                                                'store_name',
                                                'store_chain',
                                                'store_lat',
                                                'store_lng',
                                                'store_leclerc_id'])

# unique stores listed
df_stores = df_comp.copy()
df_stores.drop('store_leclerc_id', axis = 1, inplace = True)
df_stores.drop_duplicates('store_id', inplace = True)

df_stores.to_csv(os.path.join(path_csv,
                              'df_stores.csv'),
                 encoding = 'utf-8',
                 float_format='%.4f',
                 index = False)

# pairs of competitors (not necessarily scraped of course)
df_comp = df_comp[df_comp['store_id'] != df_comp['store_leclerc_id']]

df_comp.to_csv(os.path.join(path_csv,
                            'df_competitors.csv'),
               encoding = 'utf-8',
               float_format='%.4f',
               index = False)
