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
                                 'data_supermarkets',
                                 'data_source',
                                 'data_qlmc_2015',
                                 'data_scraped_201503')

path_csv = os.path.join(path_data,
                        'data_supermarkets',
                        'data_built',
                        'data_qlmc_2015',
                        'data_csv_201503')

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'df_stores_final.csv'))

df_comp = pd.read_csv(os.path.join(path_csv,
                                   'df_qlmc_competitors.csv'))

# Fix gps problems (move later?)
ls_fix_gps = [['intermarche-super-le-portel',       (50.7093, 1.5789)], # too far
              ['casino-l-ile-rousse',               (42.6327, 8.9383)],
              ['centre-e-leclerc-lassigny',         (49.5898, 2.8531)],
              ['carrefour-market-chateau-gontier',  (47.8236, -0.7064)],
              ['casino-san-nicolao',                (42.3742, 9.5299)], # too close
              ['centre-e-leclerc-san-giuliano',     (42.2625, 9.5480)]]

for store_id, (store_lat, store_lng) in ls_fix_gps:
  df_comp.loc[df_comp['comp_id'] == store_id,
              ['comp_lat', 'comp_lng']] = [store_lat, store_lng]
  df_comp.loc[df_comp['lec_id'] == store_id,
              ['lec_lat', 'lec_lng']] = [store_lat, store_lng]
  df_stores.loc[df_stores['store_id'] == store_id,
                ['store_lat', 'store_lng']] = [store_lat, store_lng]

# Compute distances
df_comp['dist'] = compute_distance_ar(df_comp['lec_lat'].values,
                                      df_comp['lec_lng'].values,
                                      df_comp['comp_lat'].values,
                                      df_comp['comp_lng'].values)

ls_disp_dist = ['lec_id', 'comp_id',
                'lec_lat', 'lec_lng', 'comp_lat', 'comp_lng',
                'dist']

## Check high distances to find obvious location mistakes
#print df_comp[df_comp['dist'] > 30][ls_disp_dist].to_string()
#print df_comp[df_comp['dist'] <= 0.1][ls_disp_dist].to_string()

# Overview of pair distance distribution
print u'\nOverview pair dist (km):'
print df_comp['dist'].describe()

# Overview of leclercs' competitors
print u'\nOverview market dist (km) around leclerc stores:'
df_leclerc_comp = df_comp[['lec_name', 'dist']]\
                    .groupby(['lec_name']).agg([len,
                                                min,
                                                max,
                                                np.mean,
                                                np.median])['dist']
ls_pctiles = [0.1, 0.25, 0.5, 0.75, 0.9]
print df_leclerc_comp.describe(percentiles = ls_pctiles)

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

# Latex display
pd.set_option('float_format', '{:,.1f}'.format)
df_leclerc_comp.reset_index(drop = False, inplace = True)

df_leclerc_comp = pd.merge(df_leclerc_comp,
                           df_stores[['store_name', 'ic']],
                           left_on = 'lec_name',
                           right_on = 'store_name',
                           how = 'left')
df_leclerc_comp['dpt'] = df_leclerc_comp['ic'].str.slice(stop = -3)           

print u'\nDist (km) between Leclerc stores and competitors (France):'
print df_leclerc_comp.describe().to_latex()

print u'\nDist (km) between Leclerc stores and competitors (Ile-de-France):'
print df_leclerc_comp[df_leclerc_comp['dpt'].isin(['75', '77', '78', '91',
                                                   '92', '93', '94', '95'])].describe().to_latex()

dict_rename = {'len' : 'Nb stores',
               'min': 'Closest',
               'max' : 'Furthest',
               'mean': 'Mean',
               'median': 'Median'}
