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
from functions_generic_qlmc import *
import numpy as np

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

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'qlmc_scraped',
                                     'df_stores.csv'))

df_comp = pd.read_csv(os.path.join(path_csv,
                                   'qlmc_scraped',
                                   'df_competitors.csv'))

# Fix gps problems (move later?)
ls_fix_gps = [['intermarche-super-le-portel', (50.7093, 1.5789)], # too far
              ['casino-l-ile-rousse',         (42.6327, 8.9383)],
              ['centre-e-leclerc-lassigny',   (49.5898, 2.8531)],
              ['carrefour-market-chateau-gontier', (47.8236, -0.7064)],
              ['casino-san-nicolao', (42.3742, 9.5299)], # too close
              ['centre-e-leclerc-san-giuliano', (42.2625, 9.5480)]]

for store_id, (store_lat, store_lng) in ls_fix_gps:
  df_comp.loc[df_comp['store_id'] == store_id, ['store_lat', 'store_lng']] = [store_lat, store_lng]
  df_stores.loc[df_stores['store_id'] == store_id, ['store_lat', 'store_lng']] = [store_lat, store_lng]

# Merge df_comp and df_stores to add info about leclerc competitor to df_comp
df_comp = pd.merge(df_comp,
                   df_stores[['store_id', 'store_lat', 'store_lng',
                              'store_name', 'store_city']],
                   left_on = 'store_leclerc_id',
                   right_on = 'store_id',
                   how = 'left',
                   suffixes = ('', '_lec'))
df_comp.drop('store_leclerc_id', axis = 1, inplace = True) # should be here?

df_comp['dist'] = compute_distance_ar(df_comp['store_lat'].values,
                                      df_comp['store_lng'].values,
                                      df_comp['store_lat_lec'].values,
                                      df_comp['store_lng_lec'].values)

ls_disp_dist = ['store_id', 'store_id_lec', 'store_city_lec',
                'store_lat', 'store_lng', 'store_lat_lec', 'store_lng_lec', 'dist']

## Check high distances to find obvious location mistakes
#print df_comp[df_comp['dist'] > 30][ls_disp_dist].to_string()
#print df_comp[df_comp['dist'] <= 0.1][ls_disp_dist].to_string()

# Overview of pair distance distribution
print df_comp['dist'].describe()

# Overview of leclercs' competitors
df_leclerc_comp = df_comp[['store_name_lec', 'dist']]\
                    .groupby('store_name_lec').agg([len, min, max, np.mean])['dist']

print df_leclerc_comp.describe()

## todo: check for each trigram if name starts with cor. dict entry
#dict_chains = {'ITM' : 'INTERMARCHE SUPER',
#               'USM' : 'SUPER U',
#               'CAR' : 'CARREFOUR',
#               'CRM' : 'CARREFOUR MARKET', # or MARKET
#               'AUC' : 'AUCHAN',
#               'GEA' : 'GEANT CASINO',
#               'COR' : 'CORA',
#               'SCA' : 'CASINO',
#               'HSM' : 'HYPER U',
#               'SIM' : 'SIMPLY MARKET',
#               'MAT' : 'SUPERMARCHE MATCH',
#               'HCA' : 'HYPER CASINO',
#               'UEX' : 'U EXPRESS',
#               'ATA' : 'ATAC',
#               'CAS' : 'CASINO',
#               'UHM' : 'HYPER U',
#               'MIG' : 'MIGROS',
#               'G20' : 'G 20',
#               'REC' : 'RECORD',
#               'HAU' : "LES HALLES D'AUCHAN"}
