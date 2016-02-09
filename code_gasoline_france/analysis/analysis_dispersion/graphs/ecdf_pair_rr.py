#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

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
#rcParams['figure.figsize'] = 16, 6
rcParams['figure.figsize'] = 8, 6

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

for diff_bound in [0.01, 0.02, 0.05]: # , 0.02, 0.05]:
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
  # GRAPH ECDF RANK REVERSALS
  # ##########################
  
  df_pairs_temp = df_pair_comp_nd

  df_all = df_pairs_temp[df_pairs_temp['distance'] <= 5]
  ls_loop_dist = [(0, 1, 0.2),
                  (1, 3, 0.5),
                  (3, 5, 1.0)]
  ls_loop_df_dist = [(dist_min,
                      dist_max,
                      alpha,
                      df_pairs_temp[(df_pairs_temp['distance'] >= dist_min) &\
                              (df_pairs_temp['distance'] < dist_max)]) for\
                       dist_min, dist_max, alpha in ls_loop_dist]
  fig = plt.figure()
  ax = fig.add_subplot(111)
  x = np.linspace(min(df_all['pct_rr']), max(df_all['pct_rr']), num=100)
  # ecdf = ECDF(df_all['pct_rr'])
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
  # Show ticks only on left and bottom axis, out of graph
  ax.yaxis.set_ticks_position('left')
  ax.xaxis.set_ticks_position('bottom')
  ax.get_yaxis().set_tick_params(which='both', direction='out')
  ax.get_xaxis().set_tick_params(which='both', direction='out')
  plt.legend(loc = 4)
  plt.savefig(os.path.join(path_dir_built_dis_graphs,
                           dir_graphs,
                           'ecdf_rank_reversals_le_{:.0f}c.png'.format(diff_bound*100)),
              bbox_inches='tight')
  plt.close()

  # ############################################
  # GRAPH ECDF RANK REVERSALS: SUPS / NON SUPS
  # ############################################
  
  for title_temp, df_pairs_temp in [('sup', df_pair_sup_nd),
                                    ('nsup', df_pair_nsup_nd)]:

    df_all = df_pairs_temp[df_pairs_temp['distance'] <= 5]
    ls_loop_dist = [(0, 1, 0.2),
                    (1, 3, 0.5),
                    (3, 5, 1.0)]
    ls_loop_df_dist = [(dist_min,
                        dist_max,
                        alpha,
                        df_pairs_temp[(df_pairs_temp['distance'] >= dist_min) &\
                                (df_pairs_temp['distance'] < dist_max)]) for\
                         dist_min, dist_max, alpha in ls_loop_dist]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    x = np.linspace(min(df_all['pct_rr']), max(df_all['pct_rr']), num=100)
    # ecdf = ECDF(df_all['pct_rr'])
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
    # Show ticks only on left and bottom axis, out of graph
    ax.yaxis.set_ticks_position('left')
    ax.xaxis.set_ticks_position('bottom')
    ax.get_yaxis().set_tick_params(which='both', direction='out')
    ax.get_xaxis().set_tick_params(which='both', direction='out')
    plt.legend(loc = 4)
    plt.savefig(os.path.join(path_dir_built_dis_graphs,
                             dir_graphs,
                             'ecdf_rank_reversals_{:s}_le_{:.0f}c.png'\
                               .format(title_temp, diff_bound*100)),
                bbox_inches='tight')
    plt.close()
    #plt.tight_layout()
    #plt.show()
