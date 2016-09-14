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

pd.set_option('float_format', '{:,.1f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

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

# basic pair filter (insufficient obs, biased rr measure)
df_pairs = df_pairs[(~((df_pairs['nb_spread'] < 90) &\
                       (df_pairs['nb_ctd_both'] < 90))) &
                    (~(df_pairs['nrr_max'] > 60))]

# LISTS FOR DISPLAY
lsd = ['id_1', 'id_2', 'distance', 'group_last_1', 'group_last_2']
lsd_rr = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

# CREATE SAME CORNER VARIABLES
df_pairs['sc_500'] = 0
df_pairs.loc[df_pairs['distance'] <= 0.5, 'sc_500'] = 1
df_pairs['sc_750'] = 0
df_pairs.loc[df_pairs['distance'] <= 0.75, 'sc_750'] = 1
df_pairs['sc_1000'] = 0
df_pairs.loc[df_pairs['distance'] <= 1, 'sc_1000'] = 1

# SPREAD IN CENT (ONLY IF USED)
for spread_var in ['mean_spread',
                   'mean_abs_spread', 'abs_mean_spread',
                   'std_spread', 'std_abs_spread']:
  df_pairs[spread_var] = df_pairs[spread_var] * 100

for pct_var in ['pct_to_same_maxu', 'pct_to_same_maxl',
                'pct_to_same_min', 'pct_same', 'pct_rr']:
  df_pairs[pct_var] = df_pairs[pct_var] * 100

# #############
# PREPARE DATA
# #############

# RESTRICT CATEGORY: PRICES AND MARGIN CHGE
df_pairs_all = df_pairs.copy()
price_cat = 'no_mc' # 'residuals_no_mc'
print(u'Prices used : {:s}'.format(price_cat))
df_pairs = df_pairs[df_pairs['cat'] == price_cat].copy()

## robustness check with idf: 1 km max
#ls_dense_dpts = [75, 92, 93, 94]
#df_pairs = df_pairs[~((((df_pairs['dpt_1'].isin(ls_dense_dpts)) |\
#                        (df_pairs['dpt_2'].isin(ls_dense_dpts))) &\
#                       (df_pairs['distance'] > 1)))]

## robustness check keep closest competitor
#df_pairs.sort(['id_1', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_1', inplace = True, take_last = False)
# could also collect closest for each id_2 and filter further
# - id_1 can have closer competitor as an id_2
# - duplicates in id_2 (that can be solved also but drops too much)
#df_pairs.sort(['id_2', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_2', inplace = True, take_last = False)
## - too many drops: end ids always listed as id_2 disappear... etc.

### robustness check: rr>20 == 0
#df_pairs = df_pairs[(df_pairs['rr>20'] == 0)]
#df_pairs = df_pairs[(df_pairs['mean_rr_len'] <= 21)]

# COMPETITORS VS. SAME GROUP
df_pair_same =\
  df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
           (df_pairs['group_last_1'] == df_pairs['group_last_2'])].copy()
df_pair_comp =\
  df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
           (df_pairs['group_last_1'] != df_pairs['group_last_2'])].copy()

# DICT OF DFS
# pairs without spread restriction
# (keep pairs with group change in any)
dict_pair_comp = {'any' : df_pair_comp}
for k in df_pair_comp['pair_type'].unique():
  dict_pair_comp[k] = df_pair_comp[df_pair_comp['pair_type'] == k]
# add sup sup&dis cat
dict_pair_comp['sup&dis'] = pd.concat([dict_pair_comp['sup'],
                                       dict_pair_comp['dis'],
                                       dict_pair_comp['sup_dis']])
# Low spread pairs (limit on average long term price difference)
diff_bound = 1.0 # euro cents
dict_pair_comp_nd = {}
for df_temp_title, df_temp in dict_pair_comp.items():
  dict_pair_comp_nd[df_temp_title] =\
      df_temp[df_temp['abs_mean_spread'] <= diff_bound]

# ##########
# STATS DESC
# ##########

# Need to play on two criteria to produce tables of paper
# - diff_bound set to 0.01 and 0.02 (differentiation)
# - df_pairs['cat'] : 'no_mc' (raw _prices) and 'residuals_no_mc' (price residuals)

ls_var_desc = ['distance', 'pct_rr', 'pct_same', 'abs_mean_spread', 'std_spread']

ls_loop_pair_disp = [('All', dict_pair_comp['any']),
                     ('Oil&Ind', dict_pair_comp['oil&ind']),
                     ('Sup&Dis', dict_pair_comp['sup&dis']),
                     ('Sup', dict_pair_comp['sup']),
                     ('Dis', dict_pair_comp['dis']),
                     ('Sup vs. Dis', dict_pair_comp['sup_dis']),
                     ('Nd All', dict_pair_comp_nd['any']),
                     ('Nd Oil&Ind', dict_pair_comp_nd['oil&ind']),
                     ('Nd Sup&Dis', dict_pair_comp_nd['sup&dis']),
                     ('Nd Sup', dict_pair_comp_nd['sup']),
                     ('Nd Dis', dict_pair_comp_nd['dis']),
                     ('Nd Sup vs. Dis', dict_pair_comp_nd['sup_dis'])]

for dist_lim in [1, 3, 5]:
  print()
  print(u'-'*50)
  print()
  print('Distance {:2.1f} km'.format(dist_lim))
  print('Overview of pair dispersion w/ max distance {:d}'.format(dist_lim))
  for stat in ['mean', 'std']:
    print()
    print(stat)
    ls_se_desc, ls_nb_obs = [], []
    for title, df_pair_disp in ls_loop_pair_disp:
      df_pair_disp_sub = df_pair_disp[df_pair_disp['distance'] <= dist_lim]
      ls_se_desc.append(df_pair_disp_sub[ls_var_desc].describe().ix[stat])
      ls_nb_obs.append(len(df_pair_disp_sub))
    df_desc_pair_disp = pd.concat(ls_se_desc,
                                  axis = 1,
                                  keys = [x[0] for x in ls_loop_pair_disp])
    df_desc_pair_disp.ix['nb_obs'] = ls_nb_obs
    print(df_desc_pair_disp.ix[['nb_obs'] + ls_var_desc[1:]].T.to_string())
