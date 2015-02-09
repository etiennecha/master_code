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

# Can check with df_info that reconciliation is right
# No price available for ids no more active though

# #####################
# FILLING GAPS
# #####################

# try to load scraped data and fill gaps when possible
# need to fix open data prices first though: fill forward
# important question: how many days? (max 30... maybe 15?)

# FIX OPEN DATA PRICES: FILL GAPS

df_prices_fixed = df_prices.fillna(method = 'ffill',
                                   axis = 0,
                                   limit = 30)

# LOAD PRICES SCRAPED

path_dir_dispersion = os.path.join(path_data,
                                   'data_gasoline',
                                   'data_built',
                                   'data_paper_dispersion')

path_dir_dispersion_csv = os.path.join(path_dir_dispersion,
                                       'data_csv')

df_prices_sc = pd.read_csv(os.path.join(path_dir_dispersion_csv,
                                        'df_prices_ttc.csv'),
                           encoding = 'utf-8',
                           parse_dates = ['date'])
df_prices_sc.set_index('date', inplace = True)
# find days missing (improve?)
se_mean_price_sc = df_prices_sc.mean(axis = 1)
ls_missing_days = se_mean_price_sc.index[pd.isnull(se_mean_price_sc)]

# CHECK OPEN DATA PRICES ON THESE DAYS

df_desc = df_prices_fixed.ix[ls_missing_days].T.describe()
df_desc = df_desc.T

# Too low prices

df_desc.sort('min', ascending = True, inplace = True)
print u'\n', df_desc[0:10]

for date_ind in df_desc[df_desc['min'] <= 1].index:
  print u'\n', df_prices_fixed.ix[date_ind][df_prices_fixed.ix[date_ind] <= 1]

# Too high prices

df_desc.sort('max', ascending = False, inplace = True)
print u'\n', df_desc[0:10]

for date_ind in df_desc[df_desc['max'] >= 1.8].index:
  print u'\n', df_prices_fixed.ix[date_ind][df_prices_fixed.ix[date_ind] >= 1.8]

# Very limited fix: only on missing days (to be generalized)
ls_fix_prices = [['19000005', '2012-08-19', 1.55],
                 ['19000005', '2012-08-18', 1.55],
                 ['57000004', '2012-08-21', np.nan],
                 ['33190002', '2012-08-17', np.nan],
                 ['31290003', '2013-01-10', np.nan],
                 ['31290003', '2013-01-09', np.nan],
                 ['31290003', '2013-01-11', np.nan],
                 ['84100007', '2012-07-18', np.nan],
                 ['93270001', '2012-07-09', np.nan]]

for id_station, date_ind, price in ls_fix_prices:
  df_prices_fixed.loc[date_ind, id_station] = price

# FILL SCRAPED DATA WITH OPEN DATA

se_count_valid = df_prices_sc.count(1)

for day_ind in ls_missing_days:
  df_prices_sc.loc[day_ind, :] = df_prices_fixed.loc[day_ind, :]

se_count_valid_fixed = df_prices_sc.count(1)

ax = se_count_valid.plot()
se_count_valid_fixed.plot(ax = ax)
plt.show()
