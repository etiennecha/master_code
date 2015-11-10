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

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2015')

path_built_csv = os.path.join(path_built,
                              'data_csv_201503')

path_built_lsa = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_lsa')

path_built_csv_lsa = os.path.join(path_built_lsa, 'data_csv')
path_built_json_lsa = os.path.join(path_built_lsa, 'data_json')
path_built_comp_csv_lsa = os.path.join(path_built_csv_lsa, '201407_competition')
path_built_comp_json_lsa = os.path.join(path_built_json_lsa, '201407_competition')

# ##############
# LOAD DATA
# ##############

# QLMC DATA

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str})

df_comp = pd.read_csv(os.path.join(path_built_csv,
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

# LSA DATA

df_lsa = pd.read_csv(os.path.join(path_built_csv_lsa,
                                  'df_lsa_active.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'UTF-8')


dict_ls_comp = dec_json(os.path.join(path_built_comp_json_lsa,
                                     'dict_ls_comp_hs.json'))

# #################
# GET LSA DISTANCES
# #################

df_comp['dist'] = compute_distance_ar(df_comp['lec_lat'].values,
                                      df_comp['lec_lng'].values,
                                      df_comp['comp_lat'].values,
                                      df_comp['comp_lng'].values)

ls_disp_dist = ['lec_id', 'comp_id',
                'lec_lat', 'lec_lng',
                'comp_lat', 'comp_lng',
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

# #######################
# ANALYSE LSA COMPETITORS
# #######################

df_lsa.loc[df_lsa['enseigne'] == 'MARKET',
           'enseigne'] = 'CARREFOUR MARKET'

ls_enseignes_compa = ['INTERMARCHE SUPER',
                      'SUPER U',
                      'CARREFOUR',
                      'CARREFOUR MARKET',
                      'AUCHAN',
                      'GEANT CASINO',
                      'CASINO',
                      'CORA',
                      'HYPER U',
                      'SIMPLY MARKET',
                      'HYPER U']

df_stores.set_index('store_id', inplace = True)
df_lsa.set_index('id_lsa', inplace = True)

dict_lec_comp = {}
for row_i, row in df_comp.iterrows():
  lec_lsa_id = df_stores.ix[row['lec_id']]['id_lsa']
  comp_lsa_id = df_stores.ix[row['comp_id']]['id_lsa']
  if not pd.isnull(lec_lsa_id) and not pd.isnull(comp_lsa_id):
    dict_lec_comp.setdefault(lec_lsa_id, []).append((comp_lsa_id, row['dist']))

# Example:
lsd0 = ['enseigne', 'adresse1', 'ville', 'surface']

lec_lsa_id_ex = dict_lec_comp.keys()[0]

print u'\nCompetitors picked by Leclerc:'
print df_lsa.ix[[x[0] for x in dict_lec_comp[lec_lsa_id_ex]]][lsd0].to_string()

print u'\nAll competitors (25 km) LSA:'
print df_lsa.ix[[x[0] for x in dict_ls_comp[lec_lsa_id_ex]]][lsd0].to_string()

# Loop: for each leclerc:
# - look if missing store of 1000m2 or more within radius by leclerc
# - if missing: look if there is already a store of enseigne (/group) brand closer

dict_lec_missing_comp = {}
dict_lec_missing_big_comp = {}
dict_lec_missing_big_comp_2 = {}
for lec_lsa_id, ls_lec_comp in dict_lec_comp.items():
  ls_missing, ls_missing_big, ls_missing_big_2 = [], [], []
  ls_lec_comp = sorted(ls_lec_comp, key = lambda x: x[1])
  qlmc_max_dist = ls_lec_comp[-1][1]
  lec_surface = df_lsa.ix[lec_lsa_id]['surface']
  
  ls_qlmc_comp_lsa_ids = [x[0] for x in ls_lec_comp]
  ls_qlmc_temp = [(x, df_lsa.ix[x]['enseigne'], df_lsa.ix[x]['groupe'], df_lsa.ix[x]['surface'])\
                    for x in ls_qlmc_comp_lsa_ids]
  
  ls_lsa_comp_lsa_ids = [x[0] for x in dict_ls_comp[lec_lsa_id]]
  ls_lsa_comp_lsa_ids_dist = [x[0] for x in dict_ls_comp[lec_lsa_id]\
                               if x[1] <= qlmc_max_dist]
  ls_lsa_temp = [(x, df_lsa.ix[x]['enseigne'], df_lsa.ix[x]['groupe'], df_lsa.ix[x]['surface'])\
                   for x in ls_lsa_comp_lsa_ids_dist]
  
  # keep store if group not yet found and size above some threshold
  ls_missing, ls_enseignes, ls_groupes = [], [], []
  for id_lsa, enseigne, groupe, surface in ls_lsa_temp:
    if id_lsa in ls_qlmc_comp_lsa_ids:
      # could add size criterion by enseigne/groupe
      ls_enseignes.append(enseigne)
      ls_groupes.append(groupe)
    elif (groupe not in ls_groupes) &\
         (surface >= 1500):
      ls_missing.append(id_lsa)
      ls_groupes.append(groupe)
      if surface >= lec_surface:
        ls_missing_big.append(id_lsa)
        if id_lsa not in df_stores['id_lsa'].values:
          ls_missing_big_2.append(id_lsa)
  dict_lec_missing_comp[lec_lsa_id] = ls_missing
  dict_lec_missing_big_comp[lec_lsa_id] = ls_missing_big
  dict_lec_missing_big_comp_2[lec_lsa_id] = ls_missing_big_2

# Could check later if store of same enseigne/groupe further but bigger
ls_check_refined = [lec_lsa_id for lec_lsa_id, ls_missing\
                      in dict_lec_missing_big_comp_2.items()\
                        if ls_missing]

# Example
lec_lsa_id_ex = ls_check_refined[0]

for lec_lsa_id_ex in ls_check_refined[0:20]:
  print u'\n' + '-'*20
  print df_lsa.ix[lec_lsa_id_ex][lsd0 + ['c_postal']].T.to_string()

  print u'\nCompetitors picked by Leclerc:'
  print df_lsa.ix[[x[0] for x in dict_lec_comp[lec_lsa_id_ex]]][lsd0].to_string()
  
  print u'\nLarge(r) competitors missing?'
  print df_lsa.ix[dict_lec_missing_big_comp[lec_lsa_id_ex]][lsd0].to_string()

  print u'\nLarge(r) competitors missing and not in data?'
  print df_lsa.ix[dict_missing_refined[lec_lsa_id_ex]][lsd0].to_string()
