#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
import os, sys
import pandas as pd
import matplotlib.pyplot as plt

path_dir_opendata = os.path.join(path_data,
                                 'data_gasoline',
                                 'data_source',
                                 'data_opendata')

path_dir_csv = os.path.join(path_dir_opendata, 'csv_files')

path_dir_match_insee = os.path.join(path_data, u'data_insee', u'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_data, u'data_insee', u'data_extracts')
path_dir_insee_dpts_regions = os.path.join(path_data, u'data_insee', u'dpts_regions')

# LOAD DATA

df_info_open = pd.read_csv(os.path.join(path_dir_csv,
                                        'df_info_all.csv'),
                           dtype = {'id_station' : str,
                                    'zip_code' : str},
                           encoding = 'UTF-8')

print u'Original nb of rows', len(df_info_open)

# FIX DATA AND ZIP_CODE

# Ad hoc fix (original zip_code '35***')
df_info_open.loc[df_info_open['id_station'] == '35200004', 'zip_code'] = '35200'
# Ad hoc fix (original zip_code '00000' and city 'XX')
df_info_open.loc[df_info_open['id_station'] == '59279001', 'zip_code'] = '59279'
df_info_open.loc[df_info_open['id_station'] == '59279001', 'city'] = 'Loon-Plage'

# One without id (pbmatic line...) and three without info except lat, lng
print u'\nNb excluded rows', len(df_info_open[(pd.isnull(df_info_open['id_station'])) |\
                                             (pd.isnull(df_info_open['zip_code'])) |\
                                             (df_info_open['city'] == 'test') |\
                                             (df_info_open['city'] == 'TEST')])

# Could try to fix if there are prices available (also look in my data?)
df_info_open = df_info_open[(~pd.isnull(df_info_open['id_station'])) &\
                            (~pd.isnull(df_info_open['zip_code'])) &\
                            (df_info_open['city'] != 'test') &\
                            (df_info_open['city'] != 'TEST')]

# Check whether zip_code is well formed
ls_pbms = []
for row_i, row in df_info_open.iterrows():
  if not re.match(u'^[0-9]{5}$', row['zip_code']):
    ls_pbms.append(row['zip_code'])
print u'\nNb pbms with zip:', len(ls_pbms)

## Other pbms detected during matching
#len(df_info_open[(pd.isnull(df_info_open['city'])) |\
#                 (df_info_open['city'] == 'XX') |\
#                 (df_info_open['zip_code'] == '00000')])

# FIx city names
df_info_open['city'] = df_info_open['city'].apply(\
                         lambda x: x.replace(u'&#xC3;&#x89;', u'E'))

# LOAD CLASS MatchingINSEE

path_df_corr = os.path.join(path_dir_match_insee, 'df_corr_gas.csv')
matching_insee = MatchingINSEE(path_df_corr)

# MATCHING

ls_match_res = []
for row_i, row in df_info_open.iterrows():
  match_res = matching_insee.match_city(row['city'], row['zip_code'][:-3], row['zip_code'])
  ls_match_res.append(match_res)

# Check results
dict_len = {}
for i, row in enumerate(ls_match_res):
  if row[0]:
    dict_len.setdefault(len(row[0]), []).append(i)
  else:
    dict_len.setdefault(0, []).append(i)

print u'\nINSEE matching results:'
for k,v in dict_len.items():
	print k, len(v)

print df_info_open[['id_station', 'street', 'zip_code', 'city']].iloc[dict_len[0]].to_string()
