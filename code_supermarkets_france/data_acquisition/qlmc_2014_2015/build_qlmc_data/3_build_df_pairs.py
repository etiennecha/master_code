#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import os, sys
import re
import pandas as pd

path_built_csv = os.path.join(path_data, 'data_supermarkets', 'data_built',
                              'data_qlmc_2014_2015', 'data_csv')

path_lsa_csv = os.path.join(path_data, 'data_supermarkets', 'data_built',
                            'data_lsa', 'data_csv')

# ################
# LOAD STORE DATA
##################

df_stores = pd.read_csv(os.path.join(path_built_csv, 'df_stores_final_201503.csv'),
                        dtype = {'id_lsa' : str},
                        encoding='utf-8')

df_lsa = pd.read_csv(os.path.join(path_lsa_csv, 'df_lsa.csv'),
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

# MERGE
df_stores = pd.merge(df_lsa[['id_lsa',
                             'latitude',
                             'longitude',
                             'enseigne_alt',
                             'groupe']],
                     df_stores,
                     left_on = 'id_lsa',
                     right_on = 'id_lsa',
                     how = 'right')
# drop stores non identified i.e. w/ no id_lsa
df_stores = df_stores[~df_stores['id_lsa'].isnull()]

# #####################
# GET CLOSE STORE PAIRS
# #####################

print('Getting list of qlmc close pairs:')
ls_close_pairs  = []
for row_i, row in df_stores.iterrows():
  ident, lat, lng = row[['id_lsa', 'latitude', 'longitude']].values
  # want list of unique pairs
  df_temp = df_stores.ix[row_i:][1:].copy() # [1:] to avoid itself
  df_temp['lat_temp'] = lat
  df_temp['lng_temp'] = lng
  df_temp['dist'] = compute_distance_ar(df_temp['latitude'],
                                        df_temp['longitude'],
                                        df_temp['lat_temp'],
                                        df_temp['lng_temp'])
  ls_close = df_temp[df_temp['dist'] <= 25][['id_lsa', 'dist']].values.tolist()
  ls_close_pairs += [[ident, ident_close, dist]\
                         for (ident_close, dist) in ls_close]

df_close_pairs = pd.DataFrame(ls_close_pairs,
                              columns = ['id_lsa_0', 'id_lsa_1', 'dist'])

dict_close_pairs = {}
for ident, ident_close, dist in ls_close_pairs:
  dict_close_pairs.setdefault(ident, []).append([ident_close, dist])
  dict_close_pairs.setdefault(ident_close, []).append([ident, dist])

# ################################
# ADD Store AND Store_Chain IN DF
# ################################

# todo: take enseigne_alt / groupe at the right period
# suffix works only with redundant columns

df_stores = df_stores[['store_id', 'store_chain', 'store_municipality',
                       'id_lsa', 'enseigne_alt', 'groupe']]
df_stores.columns = ['{:s}_0'.format(x) for x in df_stores.columns]

df_close_pairs = pd.merge(df_close_pairs,
                          df_stores,
                          on = ['id_lsa_0'],
                          how = 'left')

df_stores.columns = [x.replace('0', '1') for x in df_stores.columns]

df_close_pairs = pd.merge(df_close_pairs,
                          df_stores,
                          on = ['id_lsa_1'],
                          how = 'left')

# #############################################
# GET COMP STORE PAIRS & SAME CHAIN STORE PAIRS
# #############################################

df_comp_pairs = df_close_pairs[df_close_pairs['groupe_0'] != df_close_pairs['groupe_1']]
df_same_pairs = df_close_pairs[df_close_pairs['groupe_0'] == df_close_pairs['groupe_1']]

# #############
# OUTPUT
# #############

# May wish to add surface

df_close_pairs.to_csv(os.path.join(path_built_csv, 'df_pairs_201503.csv'),
                      encoding = 'utf-8',
                      index = False)

#enc_json(ls_close_pairs, os.path.join(path_dir_built_json, 'ls_close_pairs.json'))
#enc_json(dict_close_pairs, os.path.join(path_dir_built_json, 'dict_close_pairs.json'))
