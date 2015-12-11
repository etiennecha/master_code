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

path_dir_built_dis = os.path.join(path_data,
                                  u'data_gasoline',
                                  u'data_built',
                                  u'data_dispersion')
path_dir_built_dis_csv = os.path.join(path_dir_built_dis, u'data_csv')
path_dir_built_dis_json = os.path.join(path_dir_built_dis, u'data_json')
path_dir_built_dis_graphs = os.path.join(path_dir_built_dis, u'data_graphs')

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

zero = np.float64(1e-10)

# ###################
# LOAD DATA
# ###################

# DF PRICES

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

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

# DF PAIRS

ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                     'df_pair_final.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)


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

# ##########
# STATS DES
# ##########

# Histogram of average spreads (abs value required)
hist_test = plt.hist(df_pairs['mean_spread'].abs().values,
                     bins = 100,
                     range = (0, 0.3))
plt.show()

ls_loop = [['All', df_pair_comp],
           ['No differentiation', df_pair_comp_nd],
           ['Differentiation', df_pair_comp_d]]


for ppd_name, df_pairs_temp in ls_loop:
  print()
  print(ppd_name)
  print("Nb pairs", len(df_pairs_temp))
  print("Of which no rank rank reversals",\
           len(df_pairs_temp['pct_rr'][df_pairs_temp['pct_rr'] <= zero]))
  
  # RR & SPREAD VS DISTANCE + PER TYPE OF BRAND
  #hist_test = plt.hist(df_pairs_nodiff['pct_rr']\
  #                       [~pd.isnull(df_pairs_nodiff['pct_rr'])],
  #                     bins = 50)
  df_all = df_pairs_temp[(~pd.isnull(df_pairs_temp['pct_rr'])) &\
                         (df_pairs_temp['distance'] <= 3)]
  df_close = df_pairs_temp[(~pd.isnull(df_pairs_temp['pct_rr'])) &\
                           (df_pairs_temp['distance'] <= 1)]
  df_far = df_pairs_temp[(~pd.isnull(df_pairs_temp['pct_rr'])) &\
                         (df_pairs_temp['distance'] > 1)]
  
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
  plt.title(ppd_name)
  plt.legend()
  plt.tight_layout()
  plt.show()
  
  print('\nK-S test of equality of rank reversal distributions')
  print(ks_2samp(df_close['pct_rr'], df_far['pct_rr']))
  # one side test not implemented in python ? (not in scipy at least)
  
  print('\nNb of pairs', len(df_all['pct_rr']))
  print('Nb of pairs w/ short distance', len(df_close['pct_rr']))
  print('Nb of pairs w/ longer distance', len(df_far['pct_rr']))
  
  #print('Pair types representation among all pairs, close pairs, far pairs')
  #for df_temp, name_df in zip([df_all, df_close, df_far], ['All', 'Close', 'Far']):
  #  print ('\n%s' %name_df, len(df_temp), 'pairs')
  #  for pair_type in np.unique(df_temp['pair_type']):
  #    print("{:20} {:>4.2f}".\
  #            format(pair_type, len(df_temp[df_temp['pair_type'] == pair_type]) /\
  #                     float(len(df_temp))))

# HEATMAP: PCT SAME VS PCT RR
heatmap, xedges, yedges = np.histogram2d(df_pair_comp_nd['pct_same'].values,
                                         df_pair_comp_nd['pct_rr'].values,
                                         bins=30)
extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
plt.imshow(heatmap.T, extent=extent, origin = 'lower', aspect = 'auto')
plt.show()

# HEATMAP: PCT RR VS MEAN SPREAD
heatmap, xedges, yedges = np.histogram2d(df_pair_comp_nd['abs_mean_spread'].values,
                                         df_pair_comp_nd['pct_rr'].values,
                                         bins=30)
extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
plt.imshow(heatmap.T, extent=extent, origin = 'lower', aspect = 'auto')
plt.show()
