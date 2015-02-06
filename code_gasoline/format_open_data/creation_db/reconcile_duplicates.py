#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime

path_dir_opendata = os.path.join(path_data,
                                 'data_gasoline',
                                 'data_source',
                                 'data_opendata')

path_dir_csv = os.path.join(path_dir_opendata, 'csv_files')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dir_other = os.path.join(path_dir_source, 'data_other')

# #############
# LOAD DATA
# #############

# Duplicates found in other projects
ls_tup_duplicates = dec_json(os.path.join(path_dir_other,
                                          'ls_id_reconciliations.json'))

# Load prices
df_prices = pd.read_csv(os.path.join(path_dir_csv,
                                     'df_prices_all.csv'),
                        encoding = 'utf-8',
                        parse_dates = ['date'])
df_prices.set_index('date', inplace = True)

# Load df info
df_info = pd.read_csv(os.path.join(path_dir_csv,
                                   'df_info_all.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str})
df_info.set_index('id_station', inplace = True)

# #####################
# RECONCILE DUPLICATES
# #####################

# Build duplicate mapping
dict_duplicates = {}
for (x, y) in ls_tup_duplicates:
  ind_found = False
  for k, v in dict_duplicates.items():
    # update entry with new id
    if x == v:
      print 'Add new:', k, v, y
      dict_duplicates[k] = y # fix old one
      dict_duplicates[x] = y # add latest
      ind_found = True
      break
    # update entry with old id
    if y == k:
      print 'Update old:', x, y, v
      dict_duplicates[x] = v # add old
      ind_found = True
      break
  if not ind_found:
    dict_duplicates[x] = y
