#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
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

# MERGE
df_stores = pd.merge(df_lsa,
                     df_stores,
                     left_on = 'Ident',
                     right_on = 'id_lsa',
                     how = 'right')

# DISTANCES
ident, per, lat, lng = df_stores[['Ident', 'P', 'Latitude', 'Longitude']].iloc[0].values

ls_comp = []
for row_i, row in df_stores.iterrows():
  ident, per, lat, lng = row[['Ident', 'P', 'Latitude', 'Longitude']].values
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
  df_temp.sort('dist', inplace = True)
  # print df_temp[df_temp['dist'] <= 25][['Magasin', 'Surf Vente', 'dist', 'INSEE_Code']].to_string()
  ls_comp.append(df_temp[df_temp['dist'] <= 25][['Ident', 'dist']].values.tolist())
