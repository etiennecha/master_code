#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
from functions_string import *
from BeautifulSoup import BeautifulSoup
import collections
import copy

# #####################
# LOAD ZAGAZ DATA
# #####################

path_dir_source_zagaz = os.path.join(path_data,
                                     'data_gasoline',
                                     'data_source',
                                     'data_zagaz_scraped')

path_dir_built_zagaz = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_zagaz')

## Dict of stations with latest prices: was used to scrape stations
#dict_zagaz_station_ids = dec_json(os.path.join(path_dir_source_zagaz,
#                                              'data_json',
#                                              '20140124_dict_zagaz_station_ids.json'))

# Station info (not gps) and prices (but does not contain full history?)
dict_zagaz_ext_prices = dec_json(os.path.join(path_dir_source_zagaz,
                                              'data_json',
                                              '20140127_dict_zagaz_ext_prices.json'))

## Lists of users (and url) by dpt: was used to scrape users
#dict_zagaz_user_dpt = dec_json(os.path.join(path_dir_source_zagaz,
#                                             'data_json',
#                                             '20140408_dict_zagaz_dpt_users.json'))

# User provided prices (full history if all users scraped?)
dict_zagaz_user_info = dec_json(os.path.join(path_dir_source_zagaz,
                                             'data_json',
                                             '20140408_dict_zagaz_user_info.json'))

ls_rows_users = []
ls_rows_reports = []
for k, v in dict_zagaz_user_info.items():
  if len(v[0]) == 5:
    ls_rows_users.append([x[1] for x in v[0]] + [v[0][2][2]])
    for report in v[1]:
      ls_rows_reports.append([v[0][0][1]] + report[0:2] + report[2])

# BUILD USER DATAFRAME

df_users = pd.DataFrame(ls_rows_users,
                        columns = ['pseudo',
                                   'points',
                                   'municipality',
                                   'registration',
                                   'latest_activity',
                                   'departement'])

df_users['points'] =\
  df_users['points'].apply(lambda x: re.search('&nbsp;\((.*?)\)\sPts',
                                               x).group(1))
df_users['points'] = df_users['points'].astype(int)

df_users['municipality'] =\
  df_users['municipality'].apply(lambda x: x.rstrip(u'\n\t    \t\t('))

df_users['latest_activity'] =\
  df_users['latest_activity'].apply(lambda x: x.replace(' &agrave;', ''))
# drop hour in latest activity: no need for such precision
df_users['latest_activity'] = df_users['latest_activity'].str.slice(stop = 10)
df_users['latest_activity'] = pd.to_datetime(df_users['latest_activity'], '%d/%m/%Y')

df_users['registration'] = pd.to_datetime(df_users['registration'], '%d/%m/%Y')

df_users.sort('points', ascending = False, inplace = True)

#print df_users[0:20].to_string()

df_users.to_csv(os.path.join(path_dir_built_zagaz,
                             'data_csv',
                             'df_zagaz_users_201404.csv'),
                index = False,
                float_format='%.3f',
                encoding='utf-8')

# BUILD PRICE REPORT DATAFRAME

df_reports = pd.DataFrame(ls_rows_reports,
                          columns = ['user',
                                     'station',
                                     'time',
                                     'c0',
                                     'c1',
                                     'c2',
                                     'c3',
                                     'c4'])

df_reports['time'] =\
  df_reports['time'].apply(lambda x: x.replace(' &agrave;', ''))
df_reports['time'] = pd.to_datetime(df_reports['time'], format = '%d/%m/%Y %Hh%M')

#print df_reports[0:20].to_string()

df_reports.to_csv(os.path.join(path_dir_built_zagaz,
                               'data_csv',
                               'df_zagaz_price_reports_201404.csv'),
                  index = False,
                  float_format='%.3f',
                  encoding='utf-8')

# BUILD PRICE DATAFRAME

# fix some issues
df_reports.loc[df_reports['c0'] == '1,219.000', 'c0'] = '1.219'
df_reports.loc[df_reports['c1'] == '24.000', 'c1'] = np.nan
for gas_type in ['c0', 'c1', 'c2', 'c3', 'c4']:
  #print df_reports[~df_reports[gas_type].isnull()]\
  #        [df_reports[~df_reports[gas_type].isnull()][gas_type].str.contains(',')]
  df_reports[gas_type] = df_reports[gas_type].astype(float)

# c0 => diesel
# c1 => dieselp
# c2 => SP95
# c3 => E10
# c4 => SP98

dict_df_prices = {}
for gas_type in ['c0', 'c1', 'c2', 'c3', 'c4']:
  df_reports_temp = df_reports[~df_reports[gas_type].isnull()].copy()
  df_reports_temp.sort(['station', 'time'], inplace = True)
  df_reports_temp['time'] = df_reports_temp['time'].apply(lambda x: x.date())
  df_reports_temp.drop_duplicates(['station', 'time'],
                                  take_last = True,
                                  inplace = True)
  df_prices = df_reports_temp.pivot(index = 'time',
                                    columns = 'station',
                                    values = gas_type)
  df_prices = df_prices.astype(float)
  # todo: reindex, slice (cut before 2011?) and fill backward (lim?)
  index = pd.date_range(start = df_prices.index[0],
                        end   = df_prices.index[-1], 
                        freq='D')
  df_prices = df_prices.reindex(index)
  df_prices.fillna(method = 'backfill',
                   axis = 0,
                   limit = 14,
                   inplace = True)
  dict_df_prices[gas_type] = df_prices

#import matplotlib.pyplot as plt
#ax = dict_df_prices['c2']['3636'].ix['2011-09': '2014-12'].plot() # middle $$$ : SP95
#dict_df_prices['c3']['3636'].ix['2011-09': '2014-12'].plot(ax = ax) # least $$$: E10
#dict_df_prices['c4']['3636'].ix['2011-09': '2014-12'].plot(ax = ax) # most $$$: SP98
#plt.show()
