#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json')
#path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

# LOAD QLMC STORES
df_stores = pd.read_csv(os.path.join(path_dir_built_csv,
                             'df_qlmc_stores.csv'),
                        dtype = {'id_lsa': str,
                                 'INSE_ZIP' : str,
                                 'INSEE_Dpt' : str,
                                 'INSEE_Code' : str,
                                 'QLMC_Dpt' : str},
                        encoding = 'UTF-8')

df_stores['Magasin'] = df_stores['Enseigne'] + u' ' + df_stores['Commune']
df_stores.rename(columns = {'Enseigne' : 'Enseigne_qlmc'}, inplace = True)

# LOAD LSA STORES
df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_lsa.csv'),
                     dtype = {'Ident': str,
                              'Code INSEE' : str,
                              'Code INSEE ardt' : str},
                     parse_dates = [u'DATE ouv',
                                    u'DATE ferm',
                                    u'DATE réouv',
                                    u'DATE chg enseigne',
                                    u'DATE chgt surf'],
                     encoding = 'UTF-8')
df_lsa

# MERGE
df_stores = pd.merge(df_lsa,
                     df_stores,
                     left_on = 'Ident',
                     right_on = 'id_lsa',
                     how = 'right')

# GET COMPETITION

# list competitor pairs
print '\nGetting list of qlmc competitor pairs'
ls_comp_pairs  = []
for row_i, row in df_stores.iterrows():
  ident, per, lat, lng = row[['Ident', 'P', 'Latitude', 'Longitude']].values
  if ident:
    # want list of unique competitor pairs here
    df_temp = df_stores.ix[row_i:].copy()
    # keep stores in same period and with different lsa id
    df_temp = df_temp[(df_temp['P'] == per) &\
                      (df_temp['Ident'] != ident)]
    df_temp['lat_temp'] = lat
    df_temp['lng_temp'] = lng
    df_temp['dist'] = compute_distance_ar(df_temp['Latitude'],
                                          df_temp['Longitude'],
                                          df_temp['lat_temp'],
                                          df_temp['lng_temp'])
    # df_temp.sort('dist', inplace = True)
    # print df_temp[df_temp['dist'] <= 25][['Magasin', 'Surf Vente', 'dist', 'INSEE_Code']].to_string()
    ls_comp = df_temp[df_temp['dist'] <= 25][['Ident', 'dist']].values.tolist()
    ls_comp_pairs += [[int(per), ident, ident_comp, dist] for (ident_comp, dist) in ls_comp]

enc_json(ls_comp_pairs, os.path.join(path_dir_built_json,
                                     'ls_qlmc_comp_pairs.json'))

# dict qlmc competitors (at least one obs)
print '\nGetting dict of qlmc competitors'
dict_comp = {}
for row_i, row in df_stores.iterrows():
  ident, per, lat, lng = row[['Ident', 'P', 'Latitude', 'Longitude']].values
  if ident:
    # keep stores in same period and with different lsa id
    df_temp = df_stores[(df_stores['P'] == per) &\
                        (df_stores['Ident'] != ident)].copy()
    df_temp['lat_temp'] = lat
    df_temp['lng_temp'] = lng
    df_temp['dist'] = compute_distance_ar(df_temp['Latitude'],
                                          df_temp['Longitude'],
                                          df_temp['lat_temp'],
                                          df_temp['lng_temp'])
    # df_temp.sort('dist', inplace = True)
    # print df_temp[df_temp['dist'] <= 25][['Magasin', 'Surf Vente', 'dist', 'INSEE_Code']].to_string()
    dict_comp.setdefault(ident, []).append([int(per),
                                            df_temp[df_temp['dist'] <= 25]\
                                              [['Ident', 'dist']].values.tolist()])

enc_json(dict_comp, os.path.join(path_dir_built_json,
                                 'dict_qlmc_comp.json'))

# OVERVIEW COMPETITION

df_pairs = pd.DataFrame(ls_comp_pairs, columns = ['P', 'id_lsa_0', 'id_lsa_1', 'dist'])
se_pair_per_vc = df_pairs['P'].value_counts()
print se_pair_per_vc.to_string()
