#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')

path_dir_built_dis = os.path.join(path_data,
                                  u'data_gasoline',
                                  u'data_built',
                                  u'data_dispersion')
path_dir_built_dis_json = os.path.join(path_dir_built_dis, 'data_json')
path_dir_built_dis_csv = os.path.join(path_dir_built_dis, 'data_csv')
path_dir_built_dis_graphs = os.path.join(path_dir_built_dis, 'data_graphs')

path_dir_built_other = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_other')
path_dir_built_other_csv = os.path.join(path_dir_built_other, 'data_csv')

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

from pylab import *
rcParams['figure.figsize'] = 16, 6

## french date format
#import locale
#locale.setlocale(locale.LC_ALL, 'fra_fra')

dir_graphs = 'bw'
str_ylabel = 'Price (euro/litre)'
alpha_1 = 0.2
alpha_2 = 0.4

# #########
# LOAD DATA
# #########

# DF STATION INFO

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
                               'dpt' : str},
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
df_info.set_index('id_station', inplace = True)
df_info = df_info[df_info['highway'] != 1]

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

# DF PAIRS
ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                    'df_pair_final.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

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

for diff_bound in [0.01, 0.02, 0.05]:
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
  
  # ##########################
  # GRAPH PAIR RANK REVERSALS
  # ##########################
  
  myarray = df_pair_comp_nd['pct_rr'].values
  weights = np.ones_like(myarray)/float(len(myarray)) * 100
  
  fig = plt.figure()
  ax = fig.add_subplot(111)
  # truncate: exclude those above 0.20
  bins = np.linspace(0, 0.5, 21)
  ax.hist(myarray,
          weights = weights,
          alpha=0.5,
          color = 'k',
          bins = bins,
          normed = 0)
  ax.set_xticks(np.linspace(0, 0.5, 6))  
  # Show ticks only on left and bottom axis, out of graph
  ax.yaxis.set_ticks_position('left')
  ax.xaxis.set_ticks_position('bottom')
  ax.get_yaxis().set_tick_params(which='both', direction='out')
  ax.get_xaxis().set_tick_params(which='both', direction='out')
  plt.xlabel(u'Rank reversals')
  plt.ylabel(u'% of obs')
  #plt.legend()
  plt.savefig(os.path.join(path_dir_built_dis_graphs,
                           dir_graphs,
                           'hist_pair_rank_reversal_le_{:.0f}c.png'.format(diff_bound*100)),
              bbox_inches='tight')
  plt.close()
  
  # ##########################
  # GRAPH PAIR SAME
  # ##########################
  
  myarray = df_pair_comp_nd['pct_same'].values
  weights = np.ones_like(myarray)/float(len(myarray)) * 100
  
  fig = plt.figure()
  ax = fig.add_subplot(111)
  # truncate: exclude those above 0.20
  bins = np.linspace(0, 1.0, 21)
  ax.hist(myarray,
          weights = weights,
          alpha=0.5,
          color = 'k',
          bins = bins,
          normed = 0)
  ax.set_xticks(np.linspace(0, 1.0, 11))  
  # Show ticks only on left and bottom axis, out of graph
  ax.yaxis.set_ticks_position('left')
  ax.xaxis.set_ticks_position('bottom')
  ax.get_yaxis().set_tick_params(which='both', direction='out')
  ax.get_xaxis().set_tick_params(which='both', direction='out')
  plt.xlabel(u'Same price')
  plt.ylabel(u'% of obs')
  #plt.legend()
  plt.savefig(os.path.join(path_dir_built_dis_graphs,
                           dir_graphs,
                           'hist_pair_same_price_le_{:.0f}c.png'.format(diff_bound*100)),
              bbox_inches='tight')
  plt.close()
  
  # ###########################################
  # GRAPH PAIR RANK REVERSALS: SUP VS. NON SUPS
  # ###########################################
  
  fig = plt.figure()
  ax = fig.add_subplot(111)
  # truncate: exclude those above 0.20
  bins = np.linspace(0, 0.5, 21)
  myarray = df_pair_sup_nd['pct_rr'].values
  weights = np.ones_like(myarray)/float(len(myarray)) * 100
  n, bins, rectangles = ax.hist(myarray,
                                weights = weights,
                                bins = bins,
                                alpha = alpha_1,
                                label = u'Supermarkets',
                                color = 'k',
                                normed = 0)
  myarray = df_pair_nsup_nd['pct_rr'].values
  weights = np.ones_like(myarray)/float(len(myarray)) * 100
  n, bins, rectangles = ax.hist(myarray,
                                weights = weights,
                                bins = bins,
                                alpha = alpha_2,
                                label = u'Non supermarkets',
                                color = 'k',
                                normed = 0)
  ax.set_xticks(np.linspace(0, 0.5, 11))  
  # Show ticks only on left and bottom axis, out of graph
  ax.yaxis.set_ticks_position('left')
  ax.xaxis.set_ticks_position('bottom')
  ax.get_yaxis().set_tick_params(which='both', direction='out')
  ax.get_xaxis().set_tick_params(which='both', direction='out')
  plt.xlabel(u'Rank reversals')
  plt.ylabel(u'% of obs')
  plt.legend()
  plt.savefig(os.path.join(path_dir_built_dis_graphs,
                           dir_graphs,
                           'hist_pair_rank_reversals_sup_nsup_le_{:.0f}c.png'\
                                .format(diff_bound*100)),
              bbox_inches='tight')
  plt.close()
  
  # ###########################################
  # GRAPH PAIR RANK SAME: SUP VS. NON SUPS
  # ###########################################
  
  fig = plt.figure()
  ax = fig.add_subplot(111)
  # truncate: exclude those above 0.20
  bins = np.linspace(0, 1.0, 21)
  myarray = df_pair_sup_nd['pct_same'].values
  weights = np.ones_like(myarray)/float(len(myarray)) * 100
  n, bins, rectangles = ax.hist(myarray,
                                weights = weights,
                                bins = bins,
                                alpha = alpha_1,
                                label = u'Supermarkets',
                                color = 'k',
                                normed = 0)
  myarray = df_pair_nsup_nd['pct_same'].values
  weights = np.ones_like(myarray)/float(len(myarray)) * 100
  n, bins, rectangles = ax.hist(myarray,
                                weights = weights,
                                bins = bins,
                                alpha = alpha_2,
                                label = u'Non supermarkets',
                                color = 'k',
                                normed = 0)
  ax.set_xticks(np.linspace(0, 1.0, 11))  
  # Show ticks only on left and bottom axis, out of graph
  ax.yaxis.set_ticks_position('left')
  ax.xaxis.set_ticks_position('bottom')
  ax.get_yaxis().set_tick_params(which='both', direction='out')
  ax.get_xaxis().set_tick_params(which='both', direction='out')
  plt.xlabel(u'Same price')
  plt.ylabel(u'% of obs')
  plt.legend()
  plt.savefig(os.path.join(path_dir_built_dis_graphs,
                           dir_graphs,
                           'hist_pair_same_price_sup_nsup_le_{:.0f}c.png'\
                                .format(diff_bound*100)),
              bbox_inches='tight')
  plt.close()
