#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

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

# ###################
# LOAD DATA
# ###################

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

# temp add (move?)
df_pairs['rr<=5'] = df_pairs[['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5']].sum(1)

# RESTRICT CATEGORY

df_pairs_all = df_pairs.copy()

price_cat = 'all' # 'residuals_no_mc'
print(u'Prices used : {:s}'.format(price_cat))
df_pairs = df_pairs[df_pairs['cat'] == price_cat].copy()

# robustness check with idf: 1 km max
ls_dense_dpts = [75, 92, 93, 94]
df_pairs = df_pairs[~((((df_pairs['dpt_1'].isin(ls_dense_dpts)) |\
                        (df_pairs['dpt_2'].isin(ls_dense_dpts))) &\
                       (df_pairs['distance'] > 1)))]

## robustness check keep closest competitor
#df_pairs.sort(['id_1', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_1', inplace = True, take_last = False)
## could also collect closest for each id_2 and filter further
## - id_1 can have closer competitor as an id_2
## - duplicates in id_2 (that can be solved also but drops too much)
#df_pairs.sort(['id_2', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_2', inplace = True, take_last = False)
## - too many drops: end ids always listed as id_2 disappear... etc.

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

# ##########################
# FILTER DATA (MOVE BEFORE?)
# ##########################

print()
print(u'Nb w/ mean_rr_len > 14:', len(df_pair_comp[df_pair_comp['mean_rr_len'] > 14]))
#df_pairs = df_pairs[(pd.isnull(df_pairs['mean_rr_len'])) | (df_pairs['mean_rr_len'] <= 14)]

# SEPARATE PAIRS WITH A TOTAL ACCESS

df_pair_ta = df_pair_comp[(df_pair_comp['brand_last_1'] == 'TOTAL_ACCESS') |\
                       (df_pair_comp['brand_last_2'] == 'TOTAL_ACCESS')]

df_pair_nta = df_pair_comp[(df_pair_comp['brand_last_1'] != 'TOTAL_ACCESS') &\
                         (df_pair_comp['brand_last_2'] != 'TOTAL_ACCESS')]

# need to separate since change in brand tends to inflate pct_rr artificially
# todo: generalize to rule out significant chges in margin

# Caution: long length rank reversals can be legit (deterministic?)
# Can require a certain nb of rank reversals (how many?)

# STILL SUSPECT (Small number of rank reversals but long...)
ls_disp = ['id_1', 'id_2',
           'brand_last_1', 'brand_last_2',
           'nb_chges_1','nb_chges_2',
           'pct_rr', 'mean_rr_len', 'nb_rr']

print()
print(u'Nb with long length rank reversals only:')
print(len(df_pair_comp[(df_pair_comp['rr>20'] > 0) &\
                       (df_pair_comp['nb_rr'] < 5)]))

print()
print(u'Overview of long length rank reversals only:')
print(df_pair_comp[ls_disp][(df_pair_comp['rr>20'] > 0) &\
                        (df_pair_comp['nb_rr'] < 5)][0:10].to_string())
#df_pair_comp = df_pair_comp[~((df_pair_comp['rr>20'] > 0) &\
#                              (df_pair_comp['nb_rr'] < 5))]

print()
print(u'Nb with high average rank reversal length:')
print(len(df_pair_comp[(df_pair_comp['mean_rr_len'] >= 15)]))

print()
print(u'Overview of high average rank reversal length:')
print(df_pair_comp[ls_disp][(df_pair_comp['mean_rr_len'] >= 15)][0:10].to_string())

## Keep only if no rank reversal or rank reversal not too long?
#df_pair_comp = df_pair_comp[(df_pair_comp['mean_rr_len'].isnull()) |\
#                            (df_pair_comp['mean_rr_len'] <= 15)|
#                            (df_pair_comp['nb_rr'] >= 5)]

# #########################################################
# STATS DES: LIMITS IN RR (TA/LONG RR? AND DIFFERENTIATION)
# #########################################################

# Histogram of average spreads (abs value required)
hist_test = plt.hist(df_pairs['mean_spread'].abs().values,
                     bins = 100,
                     range = (0, 0.3))
plt.show()

# IMPACT OF TOTAL ACCESS
print()
print(u'Overview rank reversals: impact of TA')
ls_loop_ta = [['All', df_pair_comp],
              ['TA', df_pair_ta],
              ['All but TA', df_pair_nta],
              ['No diff neither TA', df_pair_nta[df_pair_nta['abs_mean_spread'] <= diff_bound]],
              ['Diff, no TA', df_pair_nta[df_pair_nta['abs_mean_spread'] > diff_bound]]]
for df_temp_title, df_temp in ls_loop_ta:
  print()
  print(u'Rank reversal: {:s}'.format(df_temp_title))
  print(df_temp[['pct_rr', 'mean_rr_len', 'rr>20', 'rr<=5']].describe())

# IMPACT OF DIFFERENTIATION
print()
print(u'Overview rank reversals: impact of TA')
ls_loop_diff = [['All', df_pair_comp],
                ['No differentation', df_pair_comp_nd],
                ['Differentiation', df_pair_comp_d]]
zero = np.float64(1e-10)
for df_temp_title, df_temp in ls_loop_diff:
  print()
  print(df_temp_title)
  print('Nb pairs', len(df_temp))
  print('Of which no rank rank reversals',\
           len(df_temp['pct_rr'][df_temp['pct_rr'] <= zero]))
  
  # RR & SPREAD VS DISTANCE + PER TYPE OF BRAND
  #hist_test = plt.hist(df_pairs_nodiff['pct_rr'][~pd.isnull(df_pairs_nodiff['pct_rr'])], bins = 50)
  df_temp = df_temp[~df_temp['pct_rr'].isnull()] # check why necessary
  df_all = df_temp[df_temp['distance'] <= 3]
  df_close = df_temp[df_temp['distance'] <= 1]
  df_far = df_temp[(df_temp['distance'] > 1) & (df_temp['distance'] <= 3)]
  
  # Plot ECDF of rank reversals: close vs. far
  ecdf = ECDF(df_all['pct_rr'])
  ecdf_close = ECDF(df_close['pct_rr'])
  ecdf_far = ECDF(df_far['pct_rr'])
  x = np.linspace(min(df_all['pct_rr']), max(df_all['pct_rr']), num=100)
  y = ecdf(x)
  y_close = ecdf_close(x)
  y_far = ecdf_far(x)
  plt.rcParams['figure.figsize'] = 8, 6
  ax = plt.subplot()
  ax.step(x, y_close, label = r'$d_{ij} \leq 1km$')
  ax.step(x, y_far, label = r'$1km < d_{ij} \leq 3km$')
  plt.title(df_temp_title)
  plt.legend()
  plt.tight_layout()
  plt.show()
  
  print('K-S test of equality of rank reversal distributions')
  print(ks_2samp(df_close['pct_rr'], df_far['pct_rr']))
  # one side test not implemented in python ? (not in scipy at least)
  print('Nb of pairs:', len(df_all['pct_rr']))
  print('Nb of pairs w/ short distance:', len(df_close['pct_rr']))
  print('Nb of pairs w/ longer distance:', len(df_far['pct_rr']))

# RELATION DISTANCE VS DIFFERENTIATION
print()
print('Relation differentiation vs. distance')
ls_loop_dd = [['All', df_pair_comp],
              ['Sup', df_pair_sup],
              ['Non sup', df_pair_nsup]]
for df_temp_title, df_temp in ls_loop_dd:
  print()
  print(df_temp_title)
  print(smf.ols('abs_mean_spread ~ distance',
                data = df_temp).fit().summary())

# #################
# GENERAL STATS DES
# #################

# Overview of most common spread frequency (various distances)
ls_df_temp = []
ls_distances = [5, 4, 3, 2, 1, 0.5]
for distance in ls_distances:
  ls_df_temp.append(df_pairs[df_pairs['distance'] <= distance]\
                       ['freq_mc_spread'].describe())

df_d_f_mcs = pd.concat(ls_df_temp, axis = 1, keys = ls_distances)
print()
print(u'Overview of most common spread frequency for various distances:')
print(df_d_f_mcs.to_string())

# Overview of pct same price (various distances)
ls_df_temp = []
ls_distances = [5, 4, 3, 2, 1, 0.5]
for distance in ls_distances:
  ls_df_temp.append(df_pairs[df_pairs['distance'] <= distance]\
                       ['pct_same'].describe())
df_d_pct_sp = pd.concat(ls_df_temp, axis = 1, keys = ls_distances)
print()
print(u'Overview of pct same price for various distances:')
print(df_d_pct_sp.to_string())

# Overview of most common spread frequency (various differentiation)
ls_df_temp = []
ls_mean_spread = [0.1, 0.05, 0.02,  0.01, 0.005, 0.0025]
for mean_spread in ls_mean_spread:
  ls_df_temp.append(df_pairs[(df_pairs['distance'] <= 5) &\
                             (df_pairs['abs_mean_spread'] <= mean_spread)]
                            ['freq_mc_spread'].describe())
df_ms_f_mcs = pd.concat(ls_df_temp, axis = 1, keys = ls_mean_spread)
print()
print(u'Overview of most common spread frequency for various max mean spread:')
print(df_ms_f_mcs.to_string())

# Overview of pct same price (various differentiation)
ls_df_temp = []
ls_mean_spread = [0.1, 0.05, 0.02,  0.01, 0.005, 0.0025]
for mean_spread in ls_mean_spread:
  ls_df_temp.append(df_pairs[(df_pairs['distance'] <= 5) &\
                             (df_pairs['abs_mean_spread'] <= mean_spread)]
                            ['pct_same'].describe())
df_ms_pct_sp = pd.concat(ls_df_temp, axis = 1, keys = ls_mean_spread)
print()
print(u'Overview of pct same price for various max mean spread:')
print(df_ms_pct_sp.to_string())

# RANK REVERSALS (todo: compare vs nb identical prices)
# Overview of pct rr price (various differentiation)
ls_df_temp = []
ls_mean_spread = [0.1, 0.05, 0.01, 0.005, 0.002, 0.001]
for mean_spread in ls_mean_spread:
  ls_df_temp.append(df_pairs[(df_pairs['distance'] <= 3) &\
                             (df_pairs['abs_mean_spread'] <= mean_spread)]
                            ['pct_rr'].describe())
df_ms_pct_rr = pd.concat(ls_df_temp, axis = 1, keys = ls_mean_spread)
print(u'Overview of pct rank reversals for various max mean spread')
print(df_ms_pct_rr.to_string())

# GAIN FROM SEARCH
# Overview of gain from search (various differentiation)
ls_df_temp = []
ls_mean_spread = [0.1, 0.05, 0.01, 0.005, 0.002, 0.001]
for mean_spread in ls_mean_spread:
  ls_df_temp.append(df_pairs[(df_pairs['distance'] <= 3) &\
                             (df_pairs['abs_mean_spread'] <= mean_spread)]
                            ['mean_abs_spread'].describe())
df_ms_gfs = pd.concat(ls_df_temp, axis = 1, keys = ls_mean_spread)
print()
print(u'Overview of gain from search for various max mean spread:')
print(df_ms_gfs.to_string())

# #############################
# ALIGNED PRICES AND LEADERSHIP
# #############################

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
# Pct same vs. mean_spread: make MSE appear? (i.e. close prices but no steady gap...)

print()
print(u'Overview aligned prices i.e. pct_same >= 0.33:')
print(df_pairs[(df_pairs['pct_same'] >= 0.33)][['pct_rr', 'nb_rr']].describe())

# STANDARD SPREAD (ALLOW GENERALIZATION OF LEADERSHIP?)
print()
print('Inspect abs mc_spread == 0.010')
print(df_pairs[(df_pairs['mc_spread'] == 0.010) | (df_pairs['mc_spread'] == -0.010)]
              [['distance', 'abs_mean_spread',
                'pct_rr', 'freq_mc_spread', 'pct_same']].describe())

df_pair_comp['pct_1_lead'] = df_pair_comp['nb_1_lead'].astype(float) /\
  df_pair_comp[['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same']].sum(1)
df_pair_comp['pct_2_lead'] = df_pair_comp['nb_2_lead'].astype(float) /\
  df_pair_comp[['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same']].sum(1)
df_pair_comp['pct_sim_same'] = df_pair_comp['nb_chge_to_same'].astype(float) /\
  df_pair_comp[['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same']].sum(1)
#print(df_pair_comp[df_pair_comp['pct_same'] >= 1/3.0]\
#        [lsd + ['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same',
#                'pct_1_lead', 'pct_2_lead', 'pct_sim_same']][0:10].to_string())

# NO LEADER
nl_ps_lim = 33/100.0
nl_pct_lead_lim = 10/100.0
df_nl = df_pair_comp[(df_pair_comp['pct_same'] >= nl_ps_lim) &\
                     (df_pair_comp['pct_1_lead'] <= 10/100.0) &\
                     (df_pair_comp['pct_2_lead'] <= 10/100.0) ].copy()
se_nl_chains = pd.concat([df_nl['brand_last_1'], df_nl['brand_last_2']]).value_counts()
print()
print(u'Chains: pair with high similar price pct but no leader')
print(se_nl_chains.to_string())

lsdnl = ['distance', 'id_1', 'id_2', 'brand_last_1', 'brand_last_2',
        'pct_same', 'pct_1_lead', 'pct_2_lead', 'pct_sim_same']

print(df_nl[lsdnl][0:20].to_string())

# LEADERSHIP?
# Restrictive def:
# - pct_to_same_max: max lead or simulatenously change to same
# - pct_to_same_min: min lead

ps_lim =      33/100.0
ptsmaxu_lim = 95/100.0
ptsmaxl_lim = 25/100.0
ptsmin_lim =  05/100.0

df_leadership = df_pair_comp[(df_pair_comp['pct_same'] >= ps_lim) &\
                             (df_pair_comp['pct_to_same_maxl'] >= (3 * df_pair_comp['pct_to_same_min'])) &\
                             (df_pair_comp['pct_to_same_maxl'] > 0.10)].copy()

df_leadership['leader_brand'] = df_leadership['brand_last_1']
df_leadership.loc[df_leadership['nb_2_lead'] > df_leadership['nb_1_lead'],
                  'leader_brand'] = df_leadership['brand_last_2']

df_leadership['follower_brand'] = df_leadership['brand_last_1']
df_leadership.loc[df_leadership['nb_2_lead'] < df_leadership['nb_1_lead'],
                  'leader_brand'] = df_leadership['brand_last_2']

lsdl = ['distance', 'id_1', 'id_2', 'brand_last_1', 'brand_last_2',
        'pct_same', 'pct_1_lead', 'pct_2_lead', 'pct_sim_same',
        'leader_brand', 'follower_brand']

print()
print(u'Overview of leadership')
print(df_leadership[lsdl][0:20].to_string())

print()
print('Chain of leaders')
print(df_leadership['leader_brand'].value_counts()[0:10])

print()
print('Chain of followers')
print(df_leadership['follower_brand'].value_counts()[0:10])

# Question: how often is a leader a follower (and vice versa?)

# UNSURE

df_unsure = df_pair_comp[(df_pair_comp['pct_same'] >= ps_lim) &\
                         (df_pair_comp['pct_to_same_maxl'] <= (3 * df_pair_comp['pct_to_same_min'])) &\
                         (df_pair_comp['pct_to_same_maxl'] > 0.10)].copy()
