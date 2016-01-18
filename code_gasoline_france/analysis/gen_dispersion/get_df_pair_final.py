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

# #########
# LOAD DATA
# #########

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

# DF MARGIN CHGE
df_margin_chge = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_margin_chge.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_margin_chge.set_index('id_station', inplace = True)

# CLOSE PAIRS
ls_close_pairs = dec_json(os.path.join(path_dir_built_json,
                                       'ls_close_pairs.json'))

# COMPETITORS
dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# STABLE MARKETS
ls_dict_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                               'ls_dict_stable_markets.json'))
ls_robust_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                                 'ls_robust_stable_markets.json'))
# 0 is 3km, 1 is 4km, 2 is 5km
ls_stable_markets = [stable_market for nb_sellers, stable_markets\
                       in ls_dict_stable_markets[2].items()\
                          for stable_market in stable_markets]

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
                          parse_dates = True)
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

# DF PAIR DISPERSION
df_pair_dispersion = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                              'df_pair_dispersion.csv'),
                                 encoding = 'utf-8',
                                 dtype = {'id_1' : str,
                                          'id_2' : str})

# DF PAIR STATS
df_pair_stats = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                         'df_pair_stats.csv'),
                            encoding = 'utf-8',
                            dtype = {'id_1' : str,
                                     'id_2' : str})

# Merge scenarios (Dispersion - STATS)
# Residuals : All (unsure? see later)
# Before : Before
# After : After
# No mc : No mc
# All : All

# Then stack and save

# ################
# PREPARE DF PAIRS
# ################

dict_df_pair_dispersion =\
    {cat: df_pair_dispersion[df_pair_dispersion['cat'] == cat].copy()\
            for cat in df_pair_dispersion['cat'].unique()}

dict_df_pair_stats =\
    {cat: df_pair_stats[df_pair_stats['cat'] == cat].copy()\
            for cat in df_pair_stats['cat'].unique()}

ls_loop_merge = [['residuals', 'all'],
                 ['all', 'all'],
                 ['after_mc', 'after_mc'],
                 ['before_mc', 'before_mc'],
                 ['no_mc', 'no_mc']]

dict_df_final = {}
for cat_dispersion, cat_stats in ls_loop_merge:
  df_dispersion = dict_df_pair_dispersion[cat_dispersion].copy()
  df_stats = dict_df_pair_stats[cat_stats].copy()
  # todo: update names when building df
  df_dispersion.drop(labels = ['distance',
                               'nb_spread',
                               'avg_spread',
                               'std_spread',
                               'std_abs_spread'], axis = 1, inplace = True)
  df_stats.drop(labels = ['cat'], axis = 1, inplace = True)
  df_final = pd.merge(df_dispersion,
                      df_stats,
                      on = ['id_1', 'id_2'],
                      how = 'left')
 # add some station info
  df_info_sub = df_info[['ci_ardt_1', 'dpt', 'reg',
                         'brand_0', 'group', 'group_type',
                         'brand_last', 'group_last', 'group_type_last']].copy()
  df_info_sub['id_1'] = df_info_sub.index
  df_final = pd.merge(df_info_sub,
                      df_final,
                      on='id_1',
                      how = 'right')
  df_info_sub.rename(columns={'id_1': 'id_2'}, inplace = True)
  df_final = pd.merge(df_info_sub,
                      df_final,
                      on = 'id_2',
                      how = 'right',
                      suffixes=('_2', '_1'))
  dict_df_final[cat_dispersion] = df_final

# todo: stack dfs
# todo: filter out rows with insufficient data?
# todo: see if add / remove variables?
# todo: see if leave same group vs. comp for later?
# todo: output (move stats des?)

## #################
## STATS DES (MOVE)
## #################
#
#df_pairs = dict_df_final['no_mc'].copy()
#
## DROP PAIRS WITH INSUFFICIENT DATA
#print(u'\nNb observations filtered out for lack of data: {:.0f}'.format(\
#      len(df_pairs[~((df_pairs['nb_spread'] < 90) &\
#                     (df_pairs['nb_ctd_both'] < 90))])))
#
#df_pairs = df_pairs[(df_pairs['nb_spread'] >= 90) &\
#                    (df_pairs['nb_ctd_both'] >= 90)]
#
## CREATE SAME CORNER VARIABLE
#for dist in [500, 750, 1000]:
#  df_pairs['sc_{:d}'.format(dist)] = 0
#  df_pairs.loc[df_pairs['distance'] <= dist/1000.0, 'sc_{:d}'.format(dist)] = 1
#
## ADD ABS MEAN SPREAD (DIFFERENTIATION CRITERION => todo: move)
#df_pairs['abs_mean_spread'] = df_pairs['mean_spread'].abs()
#
## ADD AVERAGE RANK REVERSAL LENGTH
#df_pairs['mean_rr_len'] = (df_pairs['nb_spread'] * df_pairs['pct_rr']) / df_pairs['nb_rr']
#df_pairs['mean_rr_len'] = df_pairs['mean_rr_len'].replace(np.inf, np.nan)
#
## ADD MEASURE OF PRICE CONVERGENCE
#df_pairs['pct_price_cv'] = df_pairs[['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same']].sum(1)/\
#                             df_pairs[['nb_chges_1', 'nb_chges_2']].sum(1)
#df_pairs['pct_price_cv_1'] = df_pairs[['nb_2_lead', 'nb_chge_to_same']].sum(1)/\
#                               df_pairs[['nb_chges_1']].sum(1)
#df_pairs['pct_price_cv_2'] = df_pairs[['nb_1_lead', 'nb_chge_to_same']].sum(1)/\
#                               df_pairs[['nb_chges_2']].sum(1)

## ######
## OUPUT
## ######
#
#df_pairs.to_csv(os.path.join(path_dir_built_dis_csv,
#                             'df_pair_final.csv'),
#                encoding = 'utf-8',
#                index = False)
#
### SEPARATE SAME GROUP vs. COMPETITORS
##
##df_pairs_sg = df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
##                       (df_pairs['group_last_1'] == df_pairs['group_last_2'])]
##
##df_pairs_cp = df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
##                       (df_pairs['group_last_1'] != df_pairs['group_last_2'])]
##
##df_pairs_sg.to_csv(os.path.join(path_dir_built_csv,
##                                'df_pairs_sg.csv'),
##                   encoding = 'utf-8',
##                   index = False)
##
##df_pairs_cp.to_csv(os.path.join(path_dir_built_csv,
##                                'df_pairs_cp.csv'),
##                   encoding = 'utf-8',
##                   index = False)
