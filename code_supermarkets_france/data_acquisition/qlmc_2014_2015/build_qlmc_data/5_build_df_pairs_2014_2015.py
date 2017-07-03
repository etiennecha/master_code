#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_built = os.path.join(path_data, 'data_supermarkets', 'data_built', 'data_qlmc_2014_2015')
path_built_csv = os.path.join(path_built, 'data_csv')
path_built_json = os.path.join(path_built, 'data_json')

path_lsa_csv = os.path.join(path_data, 'data_supermarkets', 'data_built',
                            'data_lsa', 'data_csv')

# ################
# LOAD DATA
##################

df_qlmc = pd.read_csv(os.path.join(path_built_csv, 'df_qlmc_2014_2015.csv'),
                      dtype = {'ean' : str,
                               'id_lsa' : str},
                      encoding = 'utf-8')
df_stores = df_qlmc[['id_lsa', 'store_name', 'store_chain']].drop_duplicates()

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
                     encoding = 'utf-8')

# MERGE
df_stores = pd.merge(df_stores,
                     df_lsa[['id_lsa', 'enseigne_alt', 'groupe'
                             'latitude', 'longitude']],
                     left_on = 'id_lsa',
                     right_on = 'id_lsa',
                     how = 'left')

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
  ls_close_pairs += [[ident, ident_close, dist] for (ident_close, dist) in ls_close]

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

df_stores = df_stores[['store_name', 'store_chain',
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
df_same_pairs = df_close_pairs[df_close_pairs['groupe_0'] ==  df_close_pairs['groupe_1']]

# #############
# OUTPUT
# #############

# May wish to add surface

df_close_pairs.to_csv(os.path.join(path_built_201415_csv, 'df_pairs_2014_2015.csv'),
                      encoding = 'utf-8',
                      index = False)

#enc_json(ls_close_pairs, os.path.join(path_dir_built_json, 'ls_close_pairs.json'))
#enc_json(dict_close_pairs, os.path.join(path_dir_built_json, 'dict_close_pairs.json'))
