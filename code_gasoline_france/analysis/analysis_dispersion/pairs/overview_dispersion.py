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

# ##################
# FILTER DATA
# ##################

# Caution: long length rank reversals can be legit (deterministic?)
# Can require a certain nb of rank reversals (how many?)

# STILL SUSPECT (Small number of rank reversals but long...)
ls_disp = ['id_1', 'id_2',
           'group_last_1', 'group_last_2',
           'nb_chges_1','nb_chges_1',
           'pct_rr', 'mean_rr_len', 'nb_rr']

df_pair_comp['rr<=5'] = df_pair_comp[lsd_rr[0:5]].sum(axis = 1)

print(u'\nNb with long length rank reversals only:')
print(len(df_pair_comp[(df_pair_comp['rr>20'] > 0) &\
                   (df_pair_comp['nb_rr'] < 5)]))

print(u'\nOverview of long length rank reversals only:')
print(df_pair_comp[ls_disp][(df_pair_comp['rr>20'] > 0) &\
                        (df_pair_comp['nb_rr'] < 5)][0:10].to_string())
df_pair_comp = df_pair_comp[~((df_pair_comp['rr>20'] > 0) &\
                              (df_pair_comp['nb_rr'] < 5))]

print(u'\nNb with high average rank reversal length:')
print(len(df_pair_comp[(df_pair_comp['mean_rr_len'] >= 15)]))

print(u'\nOverview of high average rank reversal length:')
print(df_pair_comp[ls_disp][(df_pair_comp['mean_rr_len'] >= 15)][0:10].to_string())

# Keep only if no rank reversal or rank reversal not too long?
df_pair_comp = df_pair_comp[(df_pair_comp['mean_rr_len'].isnull()) |\
                            (df_pair_comp['mean_rr_len'] <= 15)|
                            (df_pair_comp['nb_rr'] >= 5)]

# ##########
# STATS DESC
# ##########

# RELATION MEAN SPREAD vs. DISTANCE

print()
print(u'Reg: Mean spread on distance (all)')
print(smf.ols('abs_mean_spread ~ distance',
              data = df_pair_comp).fit().summary())

print()
print(u'Reg: Mean spread on distance and distance_sq (all)')
df_pair_comp['distance_sq'] = df_pair_comp['distance'] ** 2
print(smf.ols('abs_mean_spread ~ distance + distance_sq',
              data = df_pair_comp).fit().summary())

print()
print(u'Reg: ln abs mean spread on distance (exclude zeros..)')
df_pair_comp['ln_distance'] = np.log(df_pair_comp['distance'])
df_pair_comp['ln_abs_mean_spread'] = np.log(df_pair_comp['mean_spread'])
print(smf.ols('ln_abs_mean_spread ~ ln_distance',
              data = df_pair_comp[(df_pair_comp['distance'] != 0) &\
                                  (df_pair_comp['abs_mean_spread'] != 0)]).fit().summary())

# PAIR COMPARISON

# Overview of most common spread frequency (various distances)
ls_df_temp = []
ls_distances = [5, 4, 3, 2, 1, 0.5]
for distance in ls_distances:
  ls_df_temp.append(df_pair_comp[df_pair_comp['distance'] <= distance]\
                       ['freq_mc_spread'].describe())

df_d_f_mcs = pd.concat(ls_df_temp, axis = 1, keys = ls_distances)
print()
print(u'\nOverview of most common spread freq for various distances:')
print(df_d_f_mcs.to_string())

# Overview of pct same price (various distances)
ls_df_temp = []
ls_distances = [5, 4, 3, 2, 1, 0.5]
for distance in ls_distances:
  ls_df_temp.append(df_pair_comp[df_pair_comp['distance'] <= distance]\
                       ['pct_same'].describe())
df_d_pct_sp = pd.concat(ls_df_temp, axis = 1, keys = ls_distances)
print(u'\nOverview of pct same price for various distances:')
print(df_d_pct_sp.to_string())

# Overview of most common spread frequency (various differentiation)
ls_df_temp = []
ls_mean_spread = [0.1, 0.05, 0.02,  0.01, 0.005, 0.0025]
for mean_spread in ls_mean_spread:
  ls_df_temp.append(df_pair_comp[(df_pair_comp['distance'] <= 5) &\
                             (df_pair_comp['abs_mean_spread'] <= mean_spread)]
                            ['freq_mc_spread'].describe())
df_ms_f_mcs = pd.concat(ls_df_temp, axis = 1, keys = ls_mean_spread)
print(u'\nOverview of most common spread freq for various max abs mean spread:')
print(df_ms_f_mcs.to_string())

# Overview of pct same price (various differentiation)
ls_df_temp = []
ls_mean_spread = [0.1, 0.05, 0.02,  0.01, 0.005, 0.0025]
for mean_spread in ls_mean_spread:
  ls_df_temp.append(df_pair_comp[(df_pair_comp['distance'] <= 5) &\
                             (df_pair_comp['abs_mean_spread'] <= mean_spread)]
                            ['pct_same'].describe())
df_ms_pct_sp = pd.concat(ls_df_temp, axis = 1, keys = ls_mean_spread)
print(u'\nOverview of pct same price for various max mean spread:')
print(df_ms_pct_sp.to_string())

# RANK REVERSALS (todo: compare vs nb identical prices)
# Overview of pct rr price (various differentiation)
ls_df_temp = []
ls_mean_spread = [0.1, 0.05, 0.01, 0.005, 0.002, 0.001]
for mean_spread in ls_mean_spread:
  ls_df_temp.append(df_pair_comp[(df_pair_comp['distance'] <= 3) &\
                             (df_pair_comp['abs_mean_spread'] <= mean_spread)]
                            ['pct_rr'].describe())
df_ms_pct_rr = pd.concat(ls_df_temp, axis = 1, keys = ls_mean_spread)
print(u'\nOverview of pct rank reversals for various max mean spread')
print(df_ms_pct_rr.to_string())

# GAIN FROM SEARCH
# Overview of gain from search (various differentiation)
ls_df_temp = []
ls_mean_spread = [0.1, 0.05, 0.01, 0.005, 0.002, 0.001]
for mean_spread in ls_mean_spread:
  ls_df_temp.append(df_pair_comp[(df_pair_comp['distance'] <= 3) &\
                             (df_pair_comp['abs_mean_spread'] <= mean_spread)]
                            ['mean_abs_spread'].describe())
df_ms_gfs = pd.concat(ls_df_temp, axis = 1, keys = ls_mean_spread)
print(u'\nOverview of gain from search for various max mean spread:')
print(df_ms_gfs.to_string())

# todo: harmonize pct i.e. * 100

# MIXED STRATEGY
# 1/ Continuous support or discrte with low grid density
# Similar price level but scarcely same price and/or no steady spread

print(u'\nNb pairs with low differentiation and no steady spread:')
print(len(df_pair_comp[(df_pair_comp['abs_mean_spread'] <= 0.005) &\
                   (df_pair_comp['freq_mc_spread'] < 10)]))

print(u'\nNb pairs with low differentiation and low pct same price:')
print(len(df_pair_comp[(df_pair_comp['abs_mean_spread'] <= 0.005) &\
                   (df_pair_comp['pct_same'] < 0.1)]))

# 2/ Discrete support with low grid density
# High prevalence of two spread values with opposit signs
print(u'\nNb pairs with two frequent spreads of opposit sign:')
print(len(df_pair_comp[(df_pair_comp['freq_mc_spread'] > 10) &\
                   (df_pair_comp['freq_smc_spread'] > 10) &\
                   ((df_pair_comp['mc_spread'] * df_pair_comp['smc_spread']) < 0)]))

## Not so many without checking it (check inexistence of a reference spread?)
#print len(df_pair_comp[((df_pair_comp['mc_spread'] * df_pair_comp['smc_spread']) < 0)])

# RANK REVERSALS
print(u'\nDescribe rank reversals if pct_rr >= 0.2')
print(df_pair_comp_nd[df_pair_comp_nd['pct_rr'] >= 0.2]\
        [['pct_rr', 'nb_rr', 'mean_rr_len',
          'abs_mean_spread', 'mean_abs_spread', 'pct_same']].describe().to_string())

print(u'\nDescribe rank reversals if pct_rr >= 0.3')
print(df_pair_comp_nd[df_pair_comp_nd['pct_rr'] >= 0.3]\
        [['pct_rr', 'nb_rr', 'mean_rr_len',
          'abs_mean_spread', 'mean_abs_spread', 'pct_same']].describe().to_string())


print(u'\nOverview of pairs with pct_rr >= 0.2 and nb_rr < 8')
print(df_pair_comp_nd[(df_pair_comp_nd['pct_rr'] >= 0.2) &\
                      (df_pair_comp_nd['nb_rr'] < 8)]\
                     [lsd + lsd_rr + ['pct_rr', 'nb_rr']][0:10].to_string())

print(u'\nOverview of pairs with pct_rr >= 0.2 and high mean_rr_len')
print(df_pair_comp_nd[(df_pair_comp_nd['pct_rr'] >= 0.2) &\
                      (df_pair_comp_nd['mean_rr_len'] >=
                         df_pair_comp_nd['mean_rr_len'].quantile(q=0.95))]\
                     [lsd + lsd_rr + ['pct_rr', 'mean_rr_len']][0:10].to_string())

print(u'\nOverview of pairs with low differentiation and high gfs:')
print(df_pair_comp_nd[(df_pair_comp_nd['mean_abs_spread'] >= 0.02) &\
                      (df_pair_comp_nd['abs_mean_spread'] <= 0.002)]\
        [lsd + ['nb_rr', 'mean_rr_len', 'mean_abs_spread', 'abs_mean_spread']].to_string())
### Only one kind of legit (initiated by one station only though):
#df_prices_ttc[['67000002', '67800010']].plot()
#plt.show()

print(u'\nNb both in 4th quartiles in terms of aligned prices and rr:')
print(len(df_pair_comp_nd[(df_pair_comp_nd['pct_same'] >=\
                             df_pair_comp_nd['pct_same'].quantile(q=0.75)) &\
                          (df_pair_comp_nd['pct_rr'] >=\
                             df_pair_comp_nd['pct_rr'].quantile(q=0.75))]))

print(u'\nOverview if in 4th quartiles in terms of aligned prices and rr:')
print(df_pair_comp_nd[(df_pair_comp_nd['pct_same'] >=\
                         df_pair_comp_nd['pct_same'].quantile(q=0.75)) &\
                      (df_pair_comp_nd['pct_rr'] >=\
                         df_pair_comp_nd['pct_rr'].quantile(q=0.75))]\
                     [lsd + lsd_rr + ['pct_rr', 'pct_same']][0:10].to_string())

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
