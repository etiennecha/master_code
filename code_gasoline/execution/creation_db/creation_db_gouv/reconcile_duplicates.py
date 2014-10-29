#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_ls_duplicates = os.path.join(path_dir_source, 'data_other', 'ls_id_reconciliations.json')
ls_duplicate_corrections = dec_json(path_ls_duplicates)

# #########################
# LOAD INFO STATIONS
# #########################

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str})
df_info.set_index('id_station', inplace = True)

ls_di0 = ['name', 'adr_street', 'adr_city', 'ci_1',
          'lat_gov_1', 'lng_gov_1']
ls_di1 = ls_di0 + ['start', 'end', 'brand_0']

# #########################
# LOAD PRICES
# #########################

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# ##############################
# DROP THOSE WITH NO PRICE INFO
# ##############################

for id_station in df_info.index[pd.isnull(df_info['start'])]:
	if id_station in df_prices_ttc.columns:
		df_prices_ttc.drop(id_station, 1, inplace = True)
df_info = df_info[~pd.isnull(df_info['start'])]

# DETECT DUPLICATES
first_date, last_date = df_info['start'].min(), df_info['end'].max()

ls_check = []
for ci_1 in df_info['ci_1'].unique():
  # could check cross distances within and alert if 0 here
  df_temp = df_info[(df_info['ci_1'] == ci_1) &
                    ((df_info['start'] != first_date) | (df_info['end'] != last_date))]
  if len(df_temp) > 1:
    df_ee = df_temp[(df_info['start'] == first_date) & (df_info['end'] != last_date)]
    df_ls = df_temp[(df_info['start'] != first_date) & (df_info['end'] == last_date)]
    df_sh = df_temp[(df_info['start'] != first_date) & (df_info['end'] != last_date)]
    if (len(df_temp) != len(df_ee)) and (len(df_temp) != len(df_ls)):
        ls_check.append(ci_1)
        print '\n', '-'*30
        print df_temp[ls_di1].to_string()

# DETECTED DUPLICATES (NOT PRESENT ANYMORE SO FAR... PROBABLY FORGOT SOME?)
for x, y in ls_duplicate_corrections:
	if x in df_info.index and y in df_info.index:
		print x,y
		break

# todo: DELETE DUPLICATES (W/O LOSING INFO: EX BRAND / EX ADDRESS ?)
# need to recursive
