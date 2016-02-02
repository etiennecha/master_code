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

# DF STATION STATS
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

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

# FILTER DATA
# exclude stations with insufficient (quality) price data
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'corse')].index)))
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


# DF RANK REVERSALS
df_rr = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                 'df_rank_reversals_all.csv'),
                    parse_dates = ['date'],
                    encoding = 'utf-8')
df_rr.set_index('date', inplace = True)
df_rr = df_rr.T
df_rr.index = [tuple(x.split('-')) for x in df_rr.index]

# DF QUOTATIONS (WHOLESALE GAS PRICES)

df_quotations = pd.read_csv(os.path.join(path_dir_built_other_csv,
                                   'df_quotations.csv'),
                                 encoding = 'utf-8',
                                 parse_dates = ['date'])
df_quotations.set_index('date', inplace = True)

# DF MACRO TRENDS

ls_sup_ids = df_info[df_info['group_type'] == 'SUP'].index
ls_other_ids = df_info[df_info['group_type'] != 'SUP'].index
df_quotations['UFIP Brent R5 EL'] = df_quotations['UFIP Brent R5 EB'] / 158.987
df_macro = pd.DataFrame(df_prices_ht.mean(1).values,
                        columns = [u'Retail avg excl. taxes'],
                        index = df_prices_ht.index)
df_macro['Brent'] = df_quotations['UFIP Brent R5 EL']
df_macro[u'Retail avg excl. taxes - Supermarkets'] = df_prices_ht[ls_sup_ids].mean(1)
df_macro[u'Retail avg excl. taxes - Others'] = df_prices_ht[ls_other_ids].mean(1)
df_macro = df_macro[[u'Brent',
                     u'Retail avg excl. taxes',
                     u'Retail avg excl. taxes - Supermarkets',
                     u'Retail avg excl. taxes - Others']]
df_macro['Brent'] = df_macro['Brent'].fillna(method = 'bfill')

# #######################
# TEMPORAL RANK REVERSALS
# #######################

# RESTRICT CATEGORY (EXCLUDE MC)
df_pairs_all = df_pairs.copy()
df_pairs = df_pairs[df_pairs['cat'] == 'no_mc'].copy()
df_pairs['tup_ids'] = df_pairs.apply(lambda row: (row['id_1'], row['id_2']),
                                   axis = 1)

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
  
  # Keep filtered pairs
  df_rr = df_rr.ix[df_pair_comp['tup_ids'].values]
  df_rr_nd = df_rr.ix[df_pair_comp_nd['tup_ids'].values]
  df_rr_nd_sup = df_rr.ix[df_pair_sup_nd['tup_ids'].values]
  df_rr_nd_nsup = df_rr.ix[df_pair_nsup_nd['tup_ids'].values]
  
  zero = np.float64(1e-10)
  ls_df_rrs_su = []
  for df_rrs_temp in [df_rr, df_rr_nd, df_rr_nd_sup, df_rr_nd_nsup]:
    se_nb_valid = df_rrs_temp.apply(lambda x: (~pd.isnull(x)).sum())
    # se_nb_valid = se_nb_valid.astype(float)
    se_nb_valid[se_nb_valid == 0] = np.nan
    se_nb_rr    = df_rrs_temp.apply(lambda x: (np.abs(x) > zero).sum())
    # se_nb_rr = se_nb_rr.astype(float)
    se_nb_rr[se_nb_rr == 0] = np.nan
    se_avg_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero]).mean())
    se_std_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero]).std())
    se_med_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero]).median())
    df_rrs_su_temp = pd.DataFrame({'se_nb_valid' : se_nb_valid,
                                   'se_nb_rr'    : se_nb_rr,
                                   'se_avg_rr'   : se_avg_rr,
                                   'se_std_rr'   : se_std_rr,
                                   'se_med_rr'   : se_med_rr})
    df_rrs_su_temp['pct_rr'] = df_rrs_su_temp['se_nb_rr'] / df_rrs_su_temp['se_nb_valid']
    ls_df_rrs_su.append(df_rrs_su_temp) 
  
  print()
  print(u'Overview pct rank reversals - No differentiation')
  print(ls_df_rrs_su[1].describe())
  
  plt.rcParams['figure.figsize'] = 16, 6
  
  ls_loop_rr_temp = [['All pairs', ls_df_rrs_su[0]],
                     ['Low differentiation', ls_df_rrs_su[1]],
                     ['Both supermarkets', ls_df_rrs_su[2]],
                     ['Not supermarkets', ls_df_rrs_su[3]]]
  
  fig = plt.figure()
  ax1 = fig.add_subplot(111)
  ls_l = []
  for (label, df_temp), ls, alpha in zip(ls_loop_rr_temp,
                                         ['-', '-', ':', '-.'],
                                         [0.4, 1, 1, 1]):
    ls_l.append(ax1.plot(df_temp.index,
                         df_temp['pct_rr'].values,
                         c = 'k', ls = ls, alpha = alpha,
                         label = label))
  lns = ls_l[0] + ls_l[1] + ls_l[2] + ls_l[3]
  labs = [l.get_label() for l in lns]
  ax1.set_ylim(0, 0.5)
  ax1.legend(lns, labs, loc=0, labelspacing = 0.3)
  ax1.grid()
  # Show ticks only on left and bottom axis, out of graph
  ax1.yaxis.set_ticks_position('left')
  ax1.xaxis.set_ticks_position('bottom')
  ax1.get_yaxis().set_tick_params(which='both', direction='out')
  ax1.get_xaxis().set_tick_params(which='both', direction='out')
  plt.xlabel('')
  plt.ylabel(u'% reversed pairs')
  plt.tight_layout()
  plt.savefig(os.path.join(path_dir_built_dis_graphs,
                           dir_graphs,
                           'macro_rank_reversals_le_{:.0f}c.png'.format(diff_bound*100)),
              bbox_inches='tight')
  plt.close()
