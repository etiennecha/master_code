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
hist_test = plt.hist(df_pair_comp['mean_spread'].abs().values,
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

# detected biases not dealt with here

# OVERVIEW OF PAIR STATS DEPENDING ON DISTANCE

print()
print(u'Overview of pair stats depending on distance:')

ls_col_overview = ['mean_abs_spread',
                   'freq_mc_spread',
                   'pct_same',
                   'pct_rr']

ls_distances = [5, 4, 3, 2, 1, 0.5]

df_pair_temp = df_pair_comp

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
