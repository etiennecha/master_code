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

#dict_reg_leclerc = dec_json(os.path.join(path_qlmc_scraped,
#                                         'dict_reg_leclerc_stores.json'))
#
#dict_leclerc_comp = dec_json(os.path.join(path_qlmc_scraped,
#                                          'dict_leclerc_comp.json'))

ls_fra_regions = [u'picardie',
                  u'franche-comte',
                  u'languedoc-roussillon',
                  u'rhone-alpes',
                  u'basse-normandie',
                  u'poitou-charentes',
                  u'pays-de-la-loire',
                  u'lorraine',
                  u'midi-pyrenees',
                  u'nord-pas-de-calais',
                  u'centre',
                  u'bretagne',
                  u'bourgogne',
                  u'aquitaine',
                  u'auvergne',
                  u'alsace',
                  u'corse',
                  u'champagne-ardenne',
                  u'haute-normandie',
                  u'ile-de-france',
                  u'provence-alpes-cote-d-azur',
                  u'limousin']

ls_df_regions = []
for region in ls_fra_regions:
  df_region = pd.read_csv(os.path.join(path_csv,
                                       'qlmc_scraped',
                                       'df_region_{:s}.csv'.format(region)))
  ls_df_regions.append(df_region)

df_france = pd.concat(ls_df_regions)
df_france.sort(['store_id', 'family', 'subfamily', 'product'], inplace = True)
df_france.drop_duplicates(['store_id', 'family', 'subfamily', 'product'], inplace = True)

df_france.to_csv(os.path.join(path_csv,
                              'df_france.csv'),
                   encoding = 'utf-8',
                   float_format='%.3f',
                   index = False)

## STATS DES
#
## Top present products
#print df_france['product'].value_counts()[0:20].to_string()
#
## Check coca cola
#df_france[df_france['product'].str.match(u'^COCA')]['product'].value_counts()
