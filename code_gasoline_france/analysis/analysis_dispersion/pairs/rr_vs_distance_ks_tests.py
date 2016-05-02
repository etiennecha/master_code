#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp
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

# FILTER DATA
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

# RESTRICT CATEOGORY
df_pairs_all = df_pairs.copy()
df_pairs = df_pairs[df_pairs['cat'] == 'no_mc'].copy()

# COMP VS SAME GROUP
df_pair_same =\
  df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
           (df_pairs['group_last_1'] == df_pairs['group_last_2'])].copy()
df_pair_comp =\
  df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
           (df_pairs['group_last_1'] != df_pairs['group_last_2'])].copy()

# DIFFERENTIATION
diff_bound = 0.01
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

# ##########
# STATS DES
# ##########

zero = 1e-10

# Todo:
# KS test comparing same corner to market (3 and 5?)
# OLS QR here too?
# Graphs back up (same scenarios than graphs displayed in paper?)
# Check nb obs

# Interesting case: differentiated w/ residuals
df_pairs_temp = df_pair_nsup_nd

ls_loop_dist = [(0, 1, 0.2),
                (1, 3, 0.5),
                (3, 5, 1.0)]
ls_loop_df_dist = [(dist_min,
                    dist_max,
                    alpha,
                    df_pairs_temp[(df_pairs_temp['distance'] >= dist_min) &\
                            (df_pairs_temp['distance'] < dist_max)]) for\
                     dist_min, dist_max, alpha in ls_loop_dist]

# GRAPH: ECDF RANK REVERSALS
df_all = df_pairs_temp[df_pairs_temp['distance'] <= 3]
fig = plt.figure()
ax = fig.add_subplot(111)
x = np.linspace(min(df_all['pct_rr']), max(df_all['pct_rr']), num=100)
for dist_min, dist_max, alpha, df_pairs_dist in ls_loop_df_dist:
  ecdf_dist = ECDF(df_pairs_dist['pct_rr'])
  y_dist = ecdf_dist(x)
  ax.step(x,
          y_dist,
          label = r'{:d}km '.format(dist_min) +\
                  r'$\leq d_{ij} <$' +\
                  r' {:d}km'.format(dist_max),
          color = 'k',
          alpha = alpha)
plt.legend(loc = 4)
plt.show()

# KS test

# For each same corner is <= 0.5 or 1 and further 1 to 3 (check with 5)
# Non differentiated - Raw prices
# Non differentiated - Price residuals
# Differentiated - Price residuals (got to rerun with cat == 'residuals_no_mc')

# Todo: cover supermarket pairs vs. others?

ls_loop_pair_dis = [['No diff', df_pair_comp_nd],
                    ['Diff', df_pair_comp_d],
                    ['Supermarkets', df_pair_sup],
                    ['Others', df_pair_nsup]]

dist_max = 3
for title, df_temp in ls_loop_pair_dis:
  print()
  print(title)
  for dist_sc in (0.5, 1):
    df_sc = df_temp[df_temp['distance'] <= dist_sc]
    df_further = df_temp[df_temp['distance'] >= 1]
    print()
    print('Nb pairs same corner ({:.1f}km): {:d}'.format(dist_sc, len(df_sc)))
    print('Nb pairs further: {:d}'.format(len(df_further)))
    print('KS stats', ks_2samp(df_sc['pct_rr'], df_further['pct_rr']))
