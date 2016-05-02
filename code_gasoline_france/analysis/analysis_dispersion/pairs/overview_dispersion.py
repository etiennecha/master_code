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

pd.set_option('float_format', '{:,.3f}'.format)
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

# filter data
# exclude stations with insufficient (quality) price data
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'corse')].index)))
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

df_pairs = df_pairs[~((df_pairs['nb_spread'] < 90) &\
                      (df_pairs['nb_ctd_both'] < 90))]

# RESTRICT CATEGORY

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
## could also collect closest for each id_2 and filter further
## - id_1 can have closer competitor as an id_2
## - duplicates in id_2 (that can be solved also but drops too much)
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

# DIFFERENTIATED VS. NON DIFFERENTIATED

diff_bound = 0.01
print(u'Differentiated if spread above: {:.3f} euros'.format(diff_bound))

df_pair_same_nd = df_pair_same[df_pair_same['mean_spread'].abs() <= diff_bound]
df_pair_same_d  = df_pair_same[df_pair_same['mean_spread'].abs() > diff_bound]
df_pair_comp_nd = df_pair_comp[df_pair_comp['mean_spread'].abs() <= diff_bound]
df_pair_comp_d  = df_pair_comp[df_pair_comp['mean_spread'].abs() > diff_bound]

# COMP SUP VS. NON SUP

# robustness check: drop pair beyon 1 km if 

df_pair_sup = df_pair_comp[(df_pair_comp['group_type_1'] == 'SUP') &\
                           (df_pair_comp['group_type_2'] == 'SUP')]
df_pair_nsup = df_pair_comp[(df_pair_comp['group_type_1'] != 'SUP') &\
                            (df_pair_comp['group_type_2'] != 'SUP')]
df_pair_sup_nd = df_pair_sup[(df_pair_sup['mean_spread'].abs() <= diff_bound)]
df_pair_nsup_nd = df_pair_nsup[(df_pair_nsup['mean_spread'].abs() <= diff_bound)]
df_pair_sup_d = df_pair_sup[(df_pair_sup['mean_spread'].abs() > diff_bound)]
df_pair_nsup_d = df_pair_nsup[(df_pair_nsup['mean_spread'].abs() > diff_bound)]

# LISTS FOR DISPLAY

lsd = ['id_1', 'id_2', 'distance', 'group_last_1', 'group_last_2']
lsd_rr = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

# todo: harmonize pct i.e. * 100

# #################
# GENERAL STATS DES
# #################

# OVERVIEW OF PAIR STATS DEPENDING ON DISTANCE

print()
print(u'Overview of pair stats depending on distance:')

ls_col_overview = ['mean_abs_spread',
                   'freq_mc_spread',
                   'pct_same',
                   'pct_rr']

ls_distances = [5, 4, 3, 2, 1, 0.5]

#df_pair_temp = df_pair_comp
df_pair_temp = df_pair_comp[(df_pair_comp['abs_mean_spread'] <= 0.01)]

dict_df_dist_desc = {}
print()
for col in ls_col_overview:
  ls_se_temp = []
  for distance in ls_distances:
    ls_se_temp.append(df_pair_comp[df_pair_comp['distance'] <= distance]\
                                  [col].describe())
  df_desc_temp = pd.concat(ls_se_temp, axis = 1, keys = ls_distances)
  dict_df_dist_desc[col] = df_desc_temp

  print()
  print(u'Overview of {:s} frequency for various max mean spread:'.format(col))
  print(df_desc_temp.to_string())

# OVERVIEW OF PAIR STATS DEPENDING ON STATIC DIFFERENTIATION

print()
print(u'Overview of pair stats depending on static differentiation:')

ls_col_overview = ['mean_abs_spread',
                   'freq_mc_spread',
                   'pct_same',
                   'pct_rr']

ls_abs_mean_spread = [0.1, 0.05, 0.02,  0.01, 0.005, 0.002]

df_pair_temp = df_pair_comp[(df_pair_comp['distance'] <= 3)]

dict_df_diff_desc = {}
for col in ls_col_overview:
  ls_se_temp = []
  for ams in ls_abs_mean_spread:
    ls_se_temp.append(df_pair_comp[(df_pair_comp['abs_mean_spread'] <= ams)]\
                                  [col].describe())
  df_desc_temp = pd.concat(ls_se_temp, axis = 1, keys = ls_abs_mean_spread)
  dict_df_diff_desc[col] = df_desc_temp
  
  print()
  print(u'Overview of {:s} frequency for various max mean spread:'.format(col))
  print(df_desc_temp.to_string())

# #######################
# STATS DES BY GROUP TYPE
# #######################

# Need to play on two criteria to produce tables of paper
# - diff_bound set to 0.01 and 0.02 (differentiation)
# - df_pairs['cat'] : 'no_mc' (raw _prices) and 'residuals_no_mc' (price residuals)

ls_var_desc = ['distance', 'abs_mean_spread', 'std_spread', 'pct_rr', 'pct_same']

ls_loop_pair_disp = [('All', df_pair_comp),
                     ('Sup', df_pair_sup),
                     ('Non Sup', df_pair_nsup),
                     ('No diff.', df_pair_comp_nd),
                     ('Sup No diff', df_pair_sup_nd),
                     ('Non Sup no diff', df_pair_nsup_nd),
                     ('Diff', df_pair_comp_d),
                     ('Sup diff', df_pair_sup_d),
                     ('Non sup diff', df_pair_nsup_d)]

pd.set_option('float_format', '{:,.1f}'.format)
for dist_lim in [1, 3, 5]:
  print()
  print('Overview of pair dispersion w/ max distance {:d}'.format(dist_lim))
  ls_se_desc, ls_nb_obs = [], []
  for title, df_pair_disp in ls_loop_pair_disp:
    df_pair_disp_sub = df_pair_disp[df_pair_disp['distance'] <= dist_lim]
    ls_se_desc.append(df_pair_disp_sub[ls_var_desc].mean())
    ls_nb_obs.append(len(df_pair_disp_sub))
  df_desc_pair_disp = pd.concat(ls_se_desc,
                                axis = 1,
                                keys = [x[0] for x in ls_loop_pair_disp])
  # switch to cent and percent
  df_desc_pair_disp = df_desc_pair_disp * 100
  df_desc_pair_disp.ix['nb_obs'] = ls_nb_obs
  print(df_desc_pair_disp.ix[['nb_obs'] + ls_var_desc[1:]].T.to_string())

# Nb ids covered for each distance
print()
print('Nb ids covered depending on distance')
for dist_lim in [1, 3, 5]:
  df_temp = df_pair_comp[df_pair_comp['distance'] <= dist_lim]
  ls_ids = set(df_temp['id_1'].values.tolist() +\
                 df_temp['id_2'].values.tolist())
  print('Nb ids for dist {:.1f} km: {:d}'.format(dist_lim, len(ls_ids)))

# ##################################
# PCT SAME PRICE VS. RANK REVERSALS
# ##################################

## HEATMAP: PCT SAME VS PCT RR
#heatmap, xedges, yedges = np.histogram2d(df_pair_comp_nd['pct_same'].values,
#                                         df_pair_comp_nd['pct_rr'].values,
#                                         bins=30)
#extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
#plt.imshow(heatmap.T, extent=extent, origin = 'lower', aspect = 'auto')
#plt.show()
#
## HEATMAP: PCT RR VS MEAN SPREAD (rounding issues)
#heatmap, xedges, yedges = np.histogram2d(df_pair_comp_nd['abs_mean_spread'].values,
#                                         df_pair_comp_nd['pct_rr'].values,
#                                         bins=30)
#extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
#plt.imshow(heatmap.T, extent=extent, origin = 'lower', aspect = 'auto')
#plt.show()

# ALIGNED PRICES
print()
print(u'Nb aligned prices i.e. pct_same >= 0.33',\
      len(df_pairs[(df_pairs['pct_same'] >= 0.33)])) # todo: harmonize pct i.e. * 100

# todo: add distinction supermarkets vs. others
print()
print(u'Overview aligned prices i.e. pct_same >= 0.33:')
print(df_pairs[(df_pairs['pct_same'] >= 0.33)][['pct_rr',
                                                'nb_rr',
                                                'pct_same']].describe())

# STANDARD SPREAD (ALLOW GENERALIZATION OF LEADERSHIP?)
print()
print('Inspect abs mc_spread == 0.010')
print(df_pairs[(df_pairs['mc_spread'] == 0.010) | (df_pairs['mc_spread'] == -0.010)]
              [['distance', 'abs_mean_spread',
                'pct_rr', 'freq_mc_spread', 'pct_same']].describe())
