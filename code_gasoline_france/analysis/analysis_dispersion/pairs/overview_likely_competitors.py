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

# DF COMP
df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_comp.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str})
df_comp.set_index('id_station', inplace = True)

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

# RESTRICT CATEGORY

df_pairs_all = df_pairs.copy()
df_pairs = df_pairs[df_pairs['cat'] == 'no_mc'].copy()

# ################################
# BUILD CLOSEST SAME / COMPETITORS
# ################################


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

#df_pairs['abs_mean_spread'] = df_pairs['mean_spread'].abs()
df_pairs['freq_rr'] = df_pairs['nb_spread'] / df_pairs['nb_rr']
df_pairs['freq_rr'] = df_pairs['freq_rr'].replace([np.inf, -np.inf], np.nan)

df_pairs.sort('distance', ascending = True, inplace = True)

ls_ids = list(set(df_pairs['id_1'].tolist() + df_pairs['id_2'].tolist()))
ls_fields_other = ['id',
                  'brand_last',
                  'group_type_last']
ls_fields_stats = ['distance',
                   'abs_mean_spread',
                   'pct_same',
                   'pct_rr',
                   'mc_spread',
                   'freq_mc_spread']

nb_comp_max = 2
ls_rows = []
for id_station in ls_ids:
  df_station = df_pairs[(df_pairs['id_1'] == id_station) |\
                        (df_pairs['id_2'] == id_station)].copy()
  # closest same group station
  df_closest_same = df_station[df_station['group_last_1'] ==\
                               df_station['group_last_2']].copy()
  # need to have proper dim Null res_same
  res_same = [None for field in ls_fields_other] +\
             [np.nan for field in ls_fields_stats]
  if len(df_closest_same) > 0:
    row_other = df_closest_same.iloc[0]
    # find if other has suffix 1 or 2
    ls_ids = row_other[['id_1', 'id_2']].values.tolist()
    id_station_ind = ls_ids.index(id_station)
    other_ind = 1
    if id_station_ind == 0:
      other_ind = 2
    res_same = row_other[['{:s}_{:d}'.format(field, other_ind)\
                            for field in ls_fields_other]].values.tolist() +\
               row_other[ls_fields_stats].values.tolist()
  row = [id_station,
         df_info.ix[id_station]['brand_last'],
         df_info.ix[id_station]['group_type_last']] +\
        res_same
  # closest competitor station (could impose limit on abs_mean_spread)
  df_closest_comp = df_station[df_station['group_last_1'] !=\
                               df_station['group_last_2']].copy()
  df_closest_comp = df_closest_comp[df_closest_comp['abs_mean_spread'] <= 0.01]
  for row_other_i, row_other in df_closest_comp[:nb_comp_max].iterrows():
    ls_ids = row_other[['id_1', 'id_2']].values.tolist()
    id_station_ind = ls_ids.index(id_station)
    other_ind = 1
    if id_station_ind == 0:
      other_ind = 2
    res_comp = row_other[['{:s}_{:d}'.format(field, other_ind)\
                            for field in ls_fields_other]].values.tolist() +\
               row_other[ls_fields_stats].values.tolist()
    row += res_comp
  ls_rows.append(row)

ls_fields = ls_fields_other + ls_fields_stats
ls_same_cols = ['{:s}_same'.format(field) for field in ls_fields]
ls_ls_comp_cols = [['{:s}_{:d}'.format(field, ind)\
                     for field in ls_fields]\
                   for ind in range(1, nb_comp_max + 1)]
ls_cols  = ['id_station', 'brand_last', 'group_type_last'] +\
           ls_same_cols +\
           [x for ls_x in ls_ls_comp_cols for x in ls_x]
df_env = pd.DataFrame(ls_rows,
                      columns = ls_cols)

# ############
# STATS DES
# ############

# best to have filtered on differentiation when building data

print()
print(u'Check rank reversal of closest vs. second closest competitor:')

print()
print('Supermarkets:')
print(df_env[(~df_env['id_2'].isnull()) & (df_env['group_type_last'] == 'SUP')]\
            [['abs_mean_spread_1', 'abs_mean_spread_2', 'distance_1', 'distance_2',
              'pct_rr_1', 'pct_rr_2', 'pct_same_1', 'pct_same_2']].describe().to_string())

print()
print('Others:')
print(df_env[(~df_env['id_2'].isnull()) & (df_env['group_type_last'] != 'SUP')]\
            [['abs_mean_spread_1', 'abs_mean_spread_2', 'distance_1', 'distance_2',
              'pct_rr_1', 'pct_rr_2', 'pct_same_1', 'pct_same_2']].describe().to_string())

# ############
# REGRESSIONS
# ############

# higher same price share / lower rank reversals

# ADD PCT SAME / RR IN INFO
df_env.set_index('id_station', inplace = True)
ls_ind = range(1, nb_comp_max + 1)
df_info['pct_rr'] = df_env[['pct_rr_{:d}'.format(i) for i in ls_ind]].min(1)
df_info['pct_same'] = df_env[['pct_same_{:d}'.format(i) for i in ls_ind]].max(1)
df_info['abs_mean_spread'] = df_env[['abs_mean_spread_{:d}'.format(i) for i in ls_ind]].min(1)
df_info['distance'] = df_env[['distance_{:d}'.format(i) for i in ls_ind]].min(1)


# SELECTION PRICE / DAY

str_date = '2014-12-04' # '2011-09-04'
df_info['price_at'] = df_prices_ttc.ix[str_date]
df_info['price_bt'] = df_prices_ht.ix[str_date]

str_be = 'last' # '0'
df_info['brand'] = df_info['brand_{:s}'.format(str_be)]
df_info['group'] = df_info['group_{:s}'.format(str_be)]
df_info['group_type'] = df_info['group_type_{:s}'.format(str_be)]

df_sub = df_info[~df_info['price_at'].isnull()].copy()
df_sub['nb_brand'] = df_sub[['price_at', 'brand']].groupby('brand')\
                                                  .transform(len)['price_at']
df_sub = df_sub[df_sub['nb_brand'] >= 30]

# ADD SOME GEO DUMMIES
ls_ls_areas = [['idf', ['77', '78', '91', '95']],
               ['pariss', ['92', '93', '94']],
               ['paris', ['75']],
               ['paca', ['13']]]
for area_title, ls_area_dpts in ls_ls_areas:
  df_sub[area_title] = 0
  df_sub.loc[df_sub['dpt'].isin(ls_area_dpts),
             area_title] = 1

# ADD DISCOUNT CATEGORY
ls_dis = ['TOTAL_ACCESS', 'ESSO_EXPRESS']
df_sub.loc[df_sub['brand_last'].isin(ls_dis),
           'group_type_last'] = 'DIS'

# Regressions including only stations which have a non diff competitor only

for col, col2 in [['pct_rr', 'no_rr'],
                  ['pct_same', 'no_same']]:
  res_chains_a = smf.ols('price_at ~ idf + pariss + paris + brand' +\
                         ' + {:s}:C(group_type_last)'.format(col),
                          data = df_sub).fit()
  print(res_chains_a.summary())

# Regressions with all stations

df_sub['no_comp'] = 0
df_sub.loc[df_sub['distance'].isnull(), 'no_comp'] = 1

df_sub['no_rr'] = 0
df_sub['no_same'] = 0
df_sub.loc[df_sub['pct_rr'] == 0, 'no_rr'] = 1
df_sub.loc[df_sub['pct_same'] == 0, 'no_same'] = 1

df_sub.loc[df_sub['pct_rr'].isnull(), 'pct_rr'] = 0
df_sub.loc[df_sub['pct_same'].isnull(), 'pct_same'] = 0

for col, col2 in [['pct_rr', 'no_rr'],
                  ['pct_same', 'no_same']]:
  res_chains_b = smf.ols('price_at ~ idf + pariss + paris + brand'\
                         ' + no_comp:C(group_type_last)' +\
#                         ' + {:s}:C(group_type_last)'.format(col2) +\
                         ' + {:s}:C(group_type_last)'.format(col),
                         data = df_sub).fit()
  print(res_chains_b.summary())

#df_info['no_comp'] = 0
#df_info.loc[df_info['distance'].isnull(), 'no_comp'] = 1
#
#col, col2 = 'pct_rr', 'rr'
#df_info['comp_no_{:s}'.format(col2)] = 0
#df_info['comp_no_{:s}'.format(col2)] = 0
