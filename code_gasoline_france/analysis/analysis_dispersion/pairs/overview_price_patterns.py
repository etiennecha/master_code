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

# COMPETITORS VS. SAME GROUP

df_pair_same =\
  df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
           (df_pairs['group_last_1'] == df_pairs['group_last_2'])].copy()
df_pair_comp =\
  df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
           (df_pairs['group_last_1'] != df_pairs['group_last_2'])].copy()

# DIFFERENTIATED VS. NON DIFFERENTIATED

diff_bound = 0.01
df_pair_same_nd = df_pair_same[df_pair_same['mean_spread'].abs() <= diff_bound]
df_pair_same_d  = df_pair_same[df_pair_same['mean_spread'].abs() > diff_bound]
df_pair_comp_nd = df_pair_comp[df_pair_comp['mean_spread'].abs() <= diff_bound]
df_pair_comp_d  = df_pair_comp[df_pair_comp['mean_spread'].abs() > diff_bound]

# LISTS FOR DISPLAY

lsd = ['id_1', 'id_2', 'distance', 'group_last_1', 'group_last_2']
lsd_rr = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

lsd_spread = ['id_1', 'id_2', 'distance',
              'mc_spread', 'smc_spread',
              'freq_mc_spread', 'freq_smc_spread',
              'abs_mean_spread', 'mean_abs_spread', 'pct_rr', 'pct_same']

zero = 1e-10
ls_pctiles = [0.05, 0.10, 0.25, 0.5, 0.75, 0.90, 0.95]

# ########################
# OVERVIEW DIFFERENTIATION
# ########################

# Based on spread value and frequency:

# No differentiation:
# - mc_spread == 0 & freq_mc_spread high (high pct_same) : Betrand or Collusion
# - mc_spread st positive and smc_spread std negative
# - could add tmc_spread to capture cases w/ 3 prices

df_null_mc_spread = df_pair_comp[df_pair_comp['mc_spread'].abs() < zero]

print()
print('Overview most common spread 0 ({:d}):'.format(len(df_null_mc_spread)))
print(df_null_mc_spread[lsd_spread].describe(percentiles=ls_pctiles).to_string())

df_opp_spreads = df_pair_comp[((df_pair_comp['mc_spread'] > zero) &\
                               (df_pair_comp['smc_spread'] < -zero)) |
                              ((df_pair_comp['mc_spread'] <- zero) &\
                               (df_pair_comp['smc_spread'] > zero))]

print()
print('Overview opp sign spreads ({:d}):'.format(len(df_opp_spreads)))
print(df_opp_spreads[lsd_spread].describe(percentiles=ls_pctiles).to_string())

df_opp_spreads_alt =\
  df_pair_comp[(((df_pair_comp['mc_spread']*df_pair_comp['smc_spread']) < -zero) &\
                (df_pair_comp['tmc_spread'].abs() < zero)) |\
               (((df_pair_comp['smc_spread']*df_pair_comp['tmc_spread']) <- zero) &\
                (df_pair_comp['mc_spread'].abs() < zero)) |\
               (((df_pair_comp['mc_spread']*df_pair_comp['tmc_spread']) <- zero) &\
                (df_pair_comp['smc_spread'].abs() < zero))]

print()
print('Overview null and opp sign spreads ({:d}):'.format(len(df_opp_spreads_alt)))
print(df_opp_spreads_alt[lsd_spread].describe(percentiles=ls_pctiles).to_string())

#print(df_null_opp_spreads[lsd_spread][0:20].to_string())

# Low differentiation
# - mc_spread or smc_spread == 0 and both high

df_low_diff_spreads= df_pair_comp[(df_pair_comp['mc_spread'].abs() < zero) |\
                                  (df_pair_comp['smc_spread'].abs() < zero)]

#print(df_low_diff_spreads['abs_mean_spread'].describe(percentiles = ls_pctiles))
#print(df_low_diff_spreads[df_low_diff_spreads['abs_mean_spread'] > 0.057]\
#                         [lsd_spread].to_string())
## Pricing of 93000009: pathological (check dup reconciliations?)

# High(er) differentiation
# - can require mc_spread and smc_spread to be of same sign

df_high_diff_spreads = df_pair_comp[((df_pair_comp['mc_spread'] > zero) &\
                                     (df_pair_comp['smc_spread'] > zero)) |
                                    ((df_pair_comp['mc_spread'] < -zero) &\
                                     (df_pair_comp['smc_spread'] < -zero))]

print()
print('Overview same sign spreads ({:d}):'.format(len(df_high_diff_spreads)))
print(df_high_diff_spreads[lsd_spread].describe(percentiles=ls_pctiles).to_string())

# #######################
# OVERVIEW PRICE PATTERNS
# #######################

### Spread stability
#for df_pair_temp in [df_pair_comp, df_pair_comp_d, df_pair_comp_nd]:
#  print(df_pair_temp['freq_mc_spread'].describe())

# Same price: "Betrand" (or collusion..) competition vs distance

print()
print(u'Distribution of pct_same among non differentiated')
print(df_pair_comp_nd['pct_same'].describe())

df_bertrand = df_pair_comp[df_pair_comp['pct_same'] >= 1/2.0]
ls_bertrand_ids = list(set(df_bertrand[['id_1', 'id_2']].values.flatten()))

print()
print(u'Overview: distance separating pairs of "Bertrand" competitors')
print(df_bertrand['distance'].describe())

# Seems that not always the closest at all (due to differentiation?)
print()
print(u'Overview of group type of stations in pairs of "Bertrand" competitors')
print(df_info.ix[ls_bertrand_ids]['group_type'].value_counts())

print()
print(u'Overview of competition of stations in pairs of "Bertrand" competitors')
print(df_comp.ix[ls_bertrand_ids][['dist_c', 'dist_c_sup', 'nb_c_1km', 'nb_c_3km']].describe())

# ALIGNED PRICES AND LEADERSHIP
print(u'\nNb of high pct_same (above 20 pct):')
print(len(df_pair_comp[df_pair_comp['pct_same'] >= 0.3]))

df_pair_comp['pct_1_lead'] = df_pair_comp['nb_1_lead'].astype(float) /\
                           df_pair_comp[['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same']].sum(1)
df_pair_comp['pct_2_lead'] = df_pair_comp['nb_2_lead'].astype(float) /\
                           df_pair_comp[['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same']].sum(1)
df_pair_comp['pct_sim_same'] = df_pair_comp['nb_chge_to_same'].astype(float) /\
                             df_pair_comp[['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same']].sum(1)
df_pair_comp.replace([np.inf, -np.inf], np.nan, inplace = True)

print(u'\nInspect pct_same above 30 pct:')
print(df_pair_comp[df_pair_comp['pct_same'] >= 0.3]\
        [lsd + ['nb_1_lead', 'nb_2_lead', 
                'pct_same', 'nb_chge_to_same',
                'pct_1_lead', 'pct_2_lead', 'pct_sim_same']][0:10].to_string())

print(u'\nPct price convergence (both grouped) when pct_same above 30 pct:')
print(df_pair_comp[df_pair_comp['pct_same'] >= 0.3]['pct_price_cv'].describe())

print(u'\nMax pct price convergence when pct_same above 30 pct:')
print(df_pair_comp[df_pair_comp['pct_same'] >= 0.3]\
        [['pct_price_cv_1', 'pct_price_cv_2']].max(1).describe())

print(u'\nPct price convergence (both_grouped) when pct_rr above 30 pct:')
print(df_pair_comp[df_pair_comp['pct_rr'] >= 0.3]['pct_price_cv'].describe())

print(u'\nMax pct price convergence when pct_rr above 30 pct:')
print(df_pair_comp[df_pair_comp['pct_rr'] >= 0.3]\
        [['pct_price_cv_1', 'pct_price_cv_2']].max(1).describe())

# STANDARD SPREAD
lsd_f_sp = ['mc_spread', 'smc_spread',
            'freq_mc_spread', 'freq_smc_spread',
            'pct_rr']

# if exists: can generalize rank reversal and leadership
print(u'\nInspect given spread with significant frequency:')
print(df_pair_comp[(df_pair_comp['mc_spread'] == 0.010) &\
               (df_pair_comp['freq_mc_spread'] >= 25)]\
              [lsd + lsd_f_sp][0:10].to_string())

# DISTANCE VS. PERCENT SAME PRICES
print(u'\nDistance in 4th quartile of pct_same:')
print(df_pair_comp_nd[df_pair_comp_nd['pct_same'] >=\
                        df_pair_comp_nd['pct_same'].quantile(0.75)]\
                     ['distance'].describe())

print(u'\nDistance in 3 lower quartiles of pct_same:')
print(df_pair_comp_nd[df_pair_comp_nd['pct_same'] <\
                        df_pair_comp_nd['pct_same'].quantile(0.75)]\
                     ['distance'].describe())

#len(df_pair_comp_nd[(df_pair_comp_nd['pct_same'] >= 0.33) &\
#                    (df_pair_comp_nd['pct_rr'] >= 0.33)])
#df_pair_comp_nd[(df_pair_comp_nd['pct_same'] >= 0.33) &\
#                (df_pair_comp_nd['pct_rr'] >= 0.33)][lsd]
