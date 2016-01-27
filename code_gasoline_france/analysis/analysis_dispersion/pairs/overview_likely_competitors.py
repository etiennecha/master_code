#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built, u'data_json')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_built_dis = os.path.join(path_data,
                                  u'data_gasoline',
                                  u'data_built',
                                  u'data_dispersion')
path_dir_built_dis_csv = os.path.join(path_dir_built_dis, u'data_csv')
path_dir_built_dis_json = os.path.join(path_dir_built_dis, u'data_json')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ################
# LOAD DATA
# ################

# DF INFO
df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
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

# DF STATION STATS
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# CLOSE STATIONS
dict_ls_close = dec_json(os.path.join(path_dir_built_json,
                                      'dict_ls_close.json'))

# DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

# FILTER DATA
# exclude stations with insufficient (quality) price data
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'Corse')].index)))
#df_info = df_info.ix[ls_keep_ids]
#df_station_stats = df_station_stats.ix[ls_keep_ids]
#df_prices_ttc = df_prices_ttc[ls_keep_ids]
#df_prices_ht = df_prices_ht[ls_keep_ids]
#df_prices_cl = df_prices_cl[ls_keep_ids]

ls_drop_ids = list(set(df_prices_ttc.columns).difference(set(ls_keep_ids)))
df_prices_ttc[ls_drop_ids] = np.nan
df_prices_ht[ls_drop_ids] = np.nan
# highway stations may not be in df_prices_cl (no pbm here)
ls_drop_ids_nhw =\
  list(set(ls_drop_ids).difference(set(df_info[df_info['highway'] == 1].index)))
df_prices_cl[ls_drop_ids_nhw] = np.nan

# DF PAIRS

ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                    'df_pair_final.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# LOOP TO FIND (id, dist, stat except for two first)
# - closest comp
# - closest non comp
# - highest pct of sim prices
# - highest pct of sim price variations (or same day?)
# - lowest spread
# - highest nb of rank reversals

def extract_id(df_station, id_station):
  id_same = df_station[['id_1', 'id_2']].iloc[0].tolist()
  id_same.remove(id_station)
  return id_same[0]

df_pairs['abs_mean_spread'] = df_pairs['mean_spread'].abs()
df_pairs['freq_rr'] = df_pairs['nb_spread'] / df_pairs['nb_rr']
df_pairs['freq_rr'] = df_pairs['freq_rr'].replace([np.inf, -np.inf], np.nan)

df_pairs.sort('distance', inplace = True)

ls_rows = []
ls_ids = list(set(df_pairs['id_1'].tolist() + df_pairs['id_2'].tolist()))
ls_fields = [('pct_same', False), # sort order: ascending?
             ('abs_mean_spread', True),
             ('pct_rr', False),
             ('freq_rr', True),
             ('freq_mc_spread', False)]

# seems slow... optimize?
for id_station in ls_ids[0:1000]:
  df_station = df_pairs[(df_pairs['id_1'] == id_station) |\
                        (df_pairs['id_2'] == id_station)].copy()
  # closest same group station
  df_closest_same = df_station[df_station['group_last_1'] ==\
                                 df_station['group_last_2']]
  id_same, distance_same = None, np.nan
  if len(df_closest_same) > 0:
    id_same = extract_id(df_closest_same, id_station)
    distance_same = df_closest_same['distance'].iloc[0]
  # closest competitor station
  df_closest_comp = df_station[df_station['group_last_1'] !=\
                                 df_station['group_last_2']].copy()
  id_comp, distance_comp = None, np.nan
  if len(df_closest_comp) > 0:
    id_comp = extract_id(df_closest_comp, id_station)
    distance_comp = df_closest_comp['distance'].iloc[0]
  row = [id_station, id_same, distance_same, id_comp, distance_comp]
  df_temp = df_closest_comp # choose all (df_station) or comp only (df_closest_comp)
  if len(df_temp) > 0:
    for field, sort_order in ls_fields:
      id_field, dist_field, stat_field = None, np.nan, np.nan
      df_temp.sort(field, ascending = sort_order, inplace = True)
      id_field = extract_id(df_temp, id_station)
      dist_field = df_temp['distance'].iloc[0]
      stat_field = df_temp[field].iloc[0]
      row += [id_field, dist_field, stat_field]
  else:
    for field, sort_order in ls_fields:
      row += [None, np.nan, np.nan]
  ls_rows.append(row)

ls_cols = ['id_station',
           'id_friend', 'dist_friend',
           'id_comp', 'dist_comp'] +\
          [x for ls_x in [['id_{:s}'.format(field),
                           'dist_{:s}'.format(field),
                           field] for field, sort_order in ls_fields] for x in ls_x]

df_lcomp = pd.DataFrame(ls_rows, columns = ls_cols)
df_lcomp.set_index('id_station', inplace = True)

print(df_lcomp.describe().to_string())
