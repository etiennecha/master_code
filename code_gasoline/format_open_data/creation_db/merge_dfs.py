#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import pandas as pd
import matplotlib.pyplot as plt

path_dir_opendata = os.path.join(path_data,
                                 'data_gasoline',
                                 'data_source',
                                 'data_opendata')

path_dir_csv = os.path.join(path_dir_opendata, 'csv_files')

ls_years = ['20{:02d}'.format(i) for i in range(7, 15)]

# LOAD YEARLY DF INFOS
ls_df_info = []
for year in ls_years:
  df_info = pd.read_csv(os.path.join(path_dir_csv,
                                     u'df_info_%s.csv' %year),
                        dtype = {'id_station' : str,
                                 'zip_code' : str},
                        encoding = 'utf-8')
  df_info.set_index('id_station', inplace = True)
  ls_df_info.append(df_info)

# GET SURVIVAL SUMMARY TABLE
ls_ls_ids = [list(df_info.index) for df_info in ls_df_info]
ls_rows_survivors = []
for i, (year, ls_ids) in enumerate(zip(ls_years, ls_ls_ids)):
  row_survivors = [0 for j in range(i)]
  if i == 0:
    set_ids_last_year = set()
  else:
    set_ids_last_year = set(ls_ls_ids[i-1])
  set_new_ids = set(ls_ids).difference(set_ids_last_year)
  for ls_ids_next_year in ls_ls_ids[i:]:
    set_new_ids.intersection_update(set(ls_ids_next_year))
    row_survivors.append(len(set_new_ids))
  ls_rows_survivors.append(row_survivors)
df_survivors = pd.DataFrame(ls_rows_survivors,
                               columns = ls_years,
                               index = ls_years)

df_survivors['out'] = df_survivors.max(1) - df_survivors['2014']
df_survivors.ix['total'] = df_survivors.sum(0)
print df_survivors.to_string()
print 'Net increase: {:4.0f}'.format(df_survivors.loc['total', '2014'] -\
                                       df_survivors.loc['total', '2007'])

# MERGE ALL DF INFOS
df_info_all = pd.concat(ls_df_info, axis = 0)
df_info_all['id_station'] = df_info_all.index
df_info_all.drop_duplicates('id_station', take_last = True, inplace = True)
df_info_all.drop('id_station', axis = 1, inplace = True)

df_info_all.to_csv(os.path.join(path_dir_csv,
                                'df_info_all.csv'),
                   encoding = 'utf-8',
                   index_label = 'id_station')

# LOAD YEARLY DF PRICES
fuel_type = 'Gazole'
ls_df_prices = []
for year in ls_years:
  df_prices = pd.read_csv(os.path.join(path_dir_csv,
                                       u'%s_%s.csv' %(year, fuel_type)),
                          parse_dates = ['date'],
                          encoding = 'utf-8')
  df_prices.set_index('date', inplace = True)
  df_prices = df_prices / 1000.0
  ls_df_prices.append(df_prices)

df_prices_all = pd.concat(ls_df_prices, axis = 0)

df_prices_all.to_csv(os.path.join(path_dir_csv,
                                  'df_prices_all.csv'),
                     encoding = 'utf-8',
                     float_format = '%.3f',
                     index_label = 'date')

## SHOW PROBLEMS (to be refined and merge with gasoline project)
#df_prices = ls_df_prices[0]
#for ind in df_prices.index[0:10]:
#  print df_prices.ix[ind][df_prices.ix[ind] < 0.5]
