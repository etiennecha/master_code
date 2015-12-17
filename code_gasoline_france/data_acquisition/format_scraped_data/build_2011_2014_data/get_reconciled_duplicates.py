#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')

path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built, 'data_json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dir_other = os.path.join(path_dir_source, 'data_other')

ls_tup_duplicates = dec_json(os.path.join(path_dir_other,
                                          'ls_id_reconciliations.json'))

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
                               'dpt' : str},
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

ls_di0 = ['name', 'adr_street', 'adr_city', 'ci_ardt_1']
ls_di1 = ls_di0 + ['start', 'end', 'brand_0', 'brand_1', 'brand_2']

ls_disp_noinfo = ['name', 'adr_street', 'adr_city', 'ci_ardt_1',
                  'start', 'end', 'brand_0', 'brand_1', 'brand_2']

print df_info[pd.isnull(df_info['name'])][ls_disp_noinfo].to_string()

# #########################
# LOAD PRICES
# #########################

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc.csv'),
                            parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# BU so results can be checked
df_info_bu = df_info.copy()
df_prices_ttc_bu = df_prices_ttc.copy()
df_prices_ht_bu = df_prices_ht.copy()

# ######################
# DROP AND ADHOC FIXING
# ######################

# todo: add df_gas_* and df_dates?

# drop those with no prices
for id_station in df_info.index[pd.isnull(df_info['start'])]:
	if id_station in df_prices_ttc.columns:
		df_prices_ttc.drop(id_station, 1, inplace = True)
		df_prices_ht.drop(id_station, 1, inplace = True)
df_info = df_info[~pd.isnull(df_info['start'])]

# drop ad hoc
ls_drop_ids = ['95500009', '62128009',
               '76170004', '41000015',
               '45190008',
               '56000007',             # from zagaz matching
               '78000017',             # todo: use these prices to fix 78000018
               '85210005', '85210006', # from zagaz highway matching (?)
               '87160005', '87160006',
               '34400014', '44370007',
               '38080005',
               '99999001', '99999002'] # seem like tests
for id_station in ls_drop_ids:
  if id_station in df_prices_ttc.columns:
    df_prices_ttc.drop(id_station, 1, inplace = True)
    df_prices_ht.drop(id_station, 1, inplace = True)
  df_info = df_info[df_info.index != id_station].copy()

# #################
# DELETE DUPLICATES
# #################

## DETECT DUPLICATES
#first_date, last_date = df_info['start'].min(), df_info['end'].max()
#
#ls_check = []
#for ci_1 in df_info['ci_1'].unique():
#  # could check cross distances within and alert if 0 here
#  df_temp = df_info[(df_info['ci_1'] == ci_1) &
#                    ((df_info['start'] != first_date) |\
#                     (df_info['end'] != last_date))].copy()
#  if len(df_temp) > 1:
#    df_ee = df_temp[(df_temp['start'] == first_date) & (df_temp['end'] != last_date)]
#    df_ls = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] == last_date)]
#    df_sh = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] != last_date)]
#    if (len(df_temp) != len(df_ee)) and (len(df_temp) != len(df_ls)):
#        ls_check.append(ci_1)
#        print '\n', '-'*30
#        print df_temp[ls_di1].to_string()
#
#print '\nDuplicates about to be fixed:'
#for x, y in ls_tup_duplicates:
#  if x in df_info.index and y in df_info.index:
#    print x,y

# DELETE DUPLICATES (W/O LOSING INFO: EX BRAND / EX ADDRESS ?)
for x, y in ls_tup_duplicates:
  if x in df_info.index and y in df_info.index:
    # just to make sure:
    if df_info.ix[y]['start'] > df_info.ix[x]['start']:
      
      # fix prices
      date_switch = df_info.ix[y]['start']
      df_prices_ttc.loc[:date_switch-datetime.timedelta(days=1), y] =\
         df_prices_ttc.loc[:date_switch-datetime.timedelta(days=1), x]
      df_prices_ht.loc[:date_switch-datetime.timedelta(days=1), y] =\
         df_prices_ht.loc[:date_switch-datetime.timedelta(days=1), x]
      
      # fix dates (TODO)

      # drop prices
      df_prices_ttc.drop(x, axis = 1, inplace = True)
      df_prices_ht.drop(x, axis = 1, inplace = True)
      
      # fix start and end data (todo: other fields?)
      ls_start_dates = [df_info.ix[x]['start'], df_info.ix[y]['start']]
      df_info.loc[y, 'start'] = min(ls_start_dates)
      ls_end_dates = [df_info.ix[x]['end'], df_info.ix[y]['end']]
      df_info.loc[y, 'end'] = max(ls_end_dates)
      
      # fix group and group_type (keep old)
      df_info.loc[y, 'group'] = df_info.ix[x]['group']
      df_info.loc[y, 'group_type'] = df_info.ix[x]['group_type']

      # fix brand (assuming weird stuffs may be possible)
      ls_tup_x = [(df_info.ix[x]['brand_%s' %i],
                   df_info.ix[x]['day_%s' %i]) for i in range(3)\
                      if not pd.isnull(df_info.ix[x]['brand_%s' %i])]
      ls_tup_y = [(df_info.ix[y]['brand_%s' %i],
                   df_info.ix[y]['day_%s' %i]) for i in range(3)\
                      if not pd.isnull(df_info.ix[y]['brand_%s' %i])]
      ls_tup_xy = ls_tup_x + ls_tup_y
      # sort on date to be sure
      ls_tup_xy = sorted(ls_tup_xy, key=lambda tup: tup[1])
      # avoid duplicate brand
      ls_tup_xy_final = [ls_tup_xy[0]]
      for tup_brand in ls_tup_xy[1:]:
        if tup_brand[0] != ls_tup_xy_final[-1][0]:
          ls_tup_xy_final.append(tup_brand)
      # add to df (will break if more than 3)
      for i, tup_brand in enumerate(ls_tup_xy_final):
        df_info.loc[y, 'brand_%s' %i] = tup_brand[0]
        df_info.loc[y, 'day_%s' %i] = tup_brand[1]
      
      # drop info
      df_info.drop(x, axis = 0, inplace = True)

# ###########################
# DETECT REMAINING DUPLICATES
# ###########################

first_date, last_date = df_info['start'].min(), df_info['end'].max()

ls_check = []
for ci_1 in df_info['ci_1'].unique():
  # could check cross distances within and alert if 0 here
  df_temp = df_info[(df_info['ci_1'] == ci_1) &
                    ((df_info['start'] != first_date) | (df_info['end'] != last_date))].copy()
  if len(df_temp) > 1:
    df_ee = df_temp[(df_temp['start'] == first_date) & (df_temp['end'] != last_date)]
    df_ls = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] == last_date)]
    df_sh = df_temp[(df_temp['start'] != first_date) & (df_temp['end'] != last_date)]
    if (len(df_temp) != len(df_ee)) and (len(df_temp) != len(df_ls)):
        ls_check.append(ci_1)
        print '\n', '-'*30
        print df_temp[ls_di1].to_string()

## INSPECT AREA
#print df_info_bu[ls_di1][df_info_bu['ci_ardt_1'] == '85223'].to_string()
#print df_info.ix['20220005']['ci_ardt_1']
#print df_info_bu[(~pd.isnull(df_info_bu['adr_street'])) &\
#                 (df_info_bu['adr_street'].str.contains('monolithe',
#                                                        case = False))][ls_di1].to_string()

# ######
# OUTPUT
# ######

df_info.to_csv(os.path.join(path_dir_built_csv,
                                    'df_station_info_final.csv'),
                       index_label = 'id_station',
                       float_format= '%.3f',
                       encoding = 'utf-8')

df_prices_ttc.to_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                     index_label = 'date',
                     float_format= '%.3f',
                     encoding = 'utf-8')

df_prices_ht.to_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                    index_label = 'date',
                    float_format= '%.3f',
                    encoding = 'utf-8')

# Add in long form (long to write)
df_prices_ht_long = df_prices_ht.unstack()
df_prices_ht_long = df_prices_ht_long.reset_index()
df_prices_ht_long.rename(columns = {'level_0' : 'id_station',
                                    0: 'price'},
                         inplace = True)

df_prices_ht_long.to_csv(os.path.join(path_dir_built_csv,
                                      'df_prices_ht_final_long.csv'),
                         index = False,
                         float_format= '%.3f',
                         encoding = 'utf-8')

df_prices_ttc_long = df_prices_ttc.unstack()
df_prices_ttc_long = df_prices_ttc_long.reset_index()
df_prices_ttc_long.rename(columns = {'level_0' : 'id_station',
                                    0: 'price'},
                          inplace = True)

df_prices_ttc_long.to_csv(os.path.join(path_dir_built_csv,
                                      'df_prices_ttc_final_long.csv'),
                         index = False,
                         float_format= '%.3f',
                         encoding = 'utf-8')

## #############
## STATS DES
## #############

print u'\nOverview of brand changes over the period:'
df_brand_chge = pd.pivot_table(df_info[df_info['brand_0'] !=\
                                         df_info['brand_last']],
                               values = 'brand_1',
                               index=['brand_0', 'brand_last'],
                               aggfunc=len)
print df_brand_chge.to_string()

print u'\nOverview of group changes over the period:'
df_group_chge = pd.pivot_table(df_info[df_info['group'] !=\
                                         df_info['group_last']],
                               values = 'brand_0',
                               index=['group', 'group_last'],
                               aggfunc=len)
print df_group_chge.to_string()

print u'\nOverview: CARREFOUR to MOUSQUETAIRES:'
ls_ov_disp = ['name', 'adr_street', 'adr_city', 'brand_0', 'brand_1', 'start', 'end']
print df_info[(df_info['group'] == 'CARREFOUR') &\
              (df_info['group_last'] == 'MOUSQUETAIRES')][ls_ov_disp].to_string()

print u'\nOverview: left TOTAL:'
ls_ov_disp = ['name', 'adr_street', 'adr_city', 'brand_0', 'brand_1', 'start', 'end']
print df_info[(df_info['group'] == 'TOTAL') &\
              (df_info['group_last'] != 'TOTAL')][ls_ov_disp].to_string()

# 10270004 : conversion to Carrefour Market seems credible
# 44117002 : conversion to Leclerc... seems actually closed
# 26140005 : conversion to Leclerc: on highway, credible
