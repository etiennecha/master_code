#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
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
path_dir_built_dis_graphs = os.path.join(path_dir_built_dis, 'data_graphs')

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
                               'dpt' : str},
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
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

# DF COMP
df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_comp.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_comp.set_index('id_station', inplace = True)

# FILTER DATA
# exclude stations with insufficient (quality) price data

df_pbms = df_station_stats[(df_station_stats['pct_chge'] < 0.03) |\
                           (df_station_stats['nb_valid'] < 90)]
print(u'Nb with insufficient/pbmatic price data: {:d}'.format(len(df_pbms)))

df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'Corse')].index)))
df_prices_ht = df_prices_ht[ls_keep_ids]
df_prices_ttc = df_prices_ttc[ls_keep_ids]
df_info = df_info.ix[ls_keep_ids]
df_station_stats = df_station_stats.ix[ls_keep_ids]
df_comp = df_comp.ix[ls_keep_ids]

print(u'Nb of stations after all filters: {:d}'.format(len(df_info)))

# DF PAIRS
ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                    'df_pair_final.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# basic pair filter (insufficient obs, biased rr measure)
df_pairs = df_pairs[(~((df_pairs['nb_spread'] < 90) &\
                       (df_pairs['nb_ctd_both'] < 90))) &
                    (~(df_pairs['nrr_max'] > 60))]



## DF QUOTATIONS (WHOLESALE GAS PRICES)
#df_quotations = pd.read_csv(os.path.join(path_dir_built_other_csv,
#                                   'df_quotations.csv'),
#                                 encoding = 'utf-8',
#                                 parse_dates = ['date'])
#df_quotations.set_index('date', inplace = True)
#
## DF MACRO TRENDS
#ls_sup_ids = df_info[df_info['group_type'] == 'SUP'].index
#ls_other_ids = df_info[df_info['group_type'] != 'SUP'].index
#df_quotations['UFIP Brent R5 EL'] = df_quotations['UFIP Brent R5 EB'] / 158.987
#df_macro = pd.DataFrame(df_prices_ht.mean(1).values,
#                        columns = [u'Retail avg excl. taxes'],
#                        index = df_prices_ht.index)
#df_macro['Brent'] = df_quotations['UFIP Brent R5 EL']
#df_macro[u'Retail avg excl. taxes - Supermarkets'] = df_prices_ht[ls_sup_ids].mean(1)
#df_macro[u'Retail avg excl. taxes - Others'] = df_prices_ht[ls_other_ids].mean(1)
#df_macro = df_macro[[u'Brent',
#                     u'Retail avg excl. taxes',
#                     u'Retail avg excl. taxes - Supermarkets',
#                     u'Retail avg excl. taxes - Others']]
#df_macro['Brent'] = df_macro['Brent'].fillna(method = 'bfill')

# SPREAD IN CENT
for spread_var in ['mean_spread',
                   'mean_abs_spread', 'abs_mean_spread',
                   'std_spread', 'std_abs_spread',
                   'mc_spread', 'smc_spread']:
  df_pairs[spread_var] = df_pairs[spread_var] * 100

for pct_var in ['pct_to_same_maxu', 'pct_to_same_maxl',
                'pct_to_same_min', 'pct_same', 'pct_rr']:
  df_pairs[pct_var] = df_pairs[pct_var] * 100

# REFINE GROUP TYPE
# beginning: ELF + need to use future info
# (todo: add TA with no detected margin chge?)
df_info.loc[((df_info['brand_0'] == 'ELF') |\
             (df_info['brand_last'] == 'ESSO_EXPRESS')),
            'group_type'] = 'DIS'
df_info.loc[(df_info['brand_last'].isin(['ELF',
                                         'ESSO_EXPRESS',
                                         'TOTAL_ACCESS'])),
            'group_type_last'] = 'DIS'
# Further GMS refining
ls_hypers = ['AUCHAN', 'CARREFOUR', 'GEANT', 'LECLERC', 'CORA',
             'INTERMARCHE', 'SYSTEMEU']
df_info.loc[(df_info['brand_0'].isin(ls_hypers)),
            'group_type'] = 'HYP'
df_info.loc[(df_info['brand_last'].isin(ls_hypers)),
            'group_type_last'] = 'HYP'

# DEAL WITH OTHER
str_be = 'last' # '_0'
df_info['brand'] = df_info['brand_{:s}'.format(str_be)]
df_info['group_type'] = df_info['group_type_{:s}'.format(str_be)]

df_info['nb_brand'] = df_info[['brand', 'group_type']].groupby('brand')\
                                      .transform(len)

for group_type in df_info['group_type'].unique():
  df_info.loc[(df_info['nb_brand'] <= 50) &\
             (df_info['group_type'] == group_type),
             'brand'] = 'OTHER_{:s}'.format(group_type)

# temp: overwrite ELF for table (fragile but else overwritten due to nb_brand)
df_info.loc[df_info['brand'] == 'OTHER_DIS', 'brand'] = 'TOTAL_ACCESS'

# temp: set small OIL & IND to INDEPENDANT (group_type too => for agg stat on remainder)
df_info.loc[df_info['brand'] == 'OTHER_OIL', 'group_type'] = 'IND'
df_info.loc[df_info['brand'] == 'OTHER_OIL', 'brand'] = 'INDEPENDANT'
df_info.loc[df_info['brand'] == 'OTHER_IND', 'brand'] = 'INDEPENDANT'

# #############
# PREPARE DATA
# #############

# RESTRICT CATEGORY: PRICES AND MARGIN CHGE
df_pairs_all = df_pairs.copy()
price_cat = 'no_mc' # 'residuals_no_mc'
print(u'Prices used : {:s}'.format(price_cat))
df_pairs = df_pairs[df_pairs['cat'] == price_cat].copy()

# RESTRICTION ON DISTANCE
df_pairs = df_pairs[df_pairs['distance'] <= 3]

# NEED TUP IDS TO INTERACT WITH RR
df_pairs['tup_ids'] = df_pairs.apply(lambda row: (row['id_1'], row['id_2']),
                                   axis = 1)

## robustness check with idf: 1 km max
#ls_dense_dpts = [75, 92, 93, 94]
#df_pairs = df_pairs[~((((df_pairs['dpt_1'].isin(ls_dense_dpts)) |\
#                        (df_pairs['dpt_2'].isin(ls_dense_dpts))) &\
#                       (df_pairs['distance'] > 1)))]

## robustness check keep closest competitor
#df_pairs.sort(['id_1', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_1', inplace = True, take_last = False)
# could also collect closest for each id_2 and filter further
# - id_1 can have closer competitor as an id_2
# - duplicates in id_2 (that can be solved also but drops too much)
#df_pairs.sort(['id_2', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_2', inplace = True, take_last = False)
## - too many drops: end ids always listed as id_2 disappear... etc.

### robustness check: rr>20 == 0
#df_pairs = df_pairs[(df_pairs['rr>20'] == 0)]
#df_pairs = df_pairs[(df_pairs['mean_rr_len'] <= 21)]

# COMPETITORS VS. SAME GROUP
df_pair_same =\
  df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
           (df_pairs['group_last_1'] == df_pairs['group_last_2'])].copy()
df_pair_comp =\
  df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
           (df_pairs['group_last_1'] != df_pairs['group_last_2'])].copy()

# DF RANK REVERSALS
# pbm: takes long to load
df_rr = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                 'df_rank_reversals_all.csv'),
                    parse_dates = ['date'],
                    encoding = 'utf-8')
df_rr.set_index('date', inplace = True)
df_rr = df_rr.T
df_rr.index = [tuple(x.split('-')) for x in df_rr.index]

# DICT OF DFS
# pairs without spread restriction
# (keep pairs with group change in any)
dict_pair_comp = {'any' : df_pair_comp}
for k in df_pair_comp['pair_type'].unique():
  dict_pair_comp[k] = df_pair_comp[df_pair_comp['pair_type'] == k]
# add sup sup&dis cat
dict_pair_comp['sup&dis'] = pd.concat([dict_pair_comp['sup'],
                                       dict_pair_comp['dis'],
                                       dict_pair_comp['sup_dis']])

# LOW SPREAD PAIRS
for diff_bound in [1.0, 2.0]:
  dict_pair_comp_nd = {}
  for df_temp_title, df_temp in dict_pair_comp.items():
    dict_pair_comp_nd[df_temp_title] =\
        df_temp[df_temp['abs_mean_spread'] <= diff_bound]
  
  # #######################
  # TEMPORAL RANK REVERSALS
  # #######################
  
  # Keep filtered pairs
  df_rr = df_rr.ix[dict_pair_comp['any']['tup_ids'].values]
  df_rr_nd = df_rr.ix[dict_pair_comp_nd['any']['tup_ids'].values]
  
  df_rr_sup = df_rr.ix[dict_pair_comp['sup&dis']['tup_ids'].values]
  df_rr_nsup = df_rr.ix[dict_pair_comp['oil&ind']['tup_ids'].values]
  
  df_rr_nd_sup = df_rr.ix[dict_pair_comp_nd['sup&dis']['tup_ids'].values]
  df_rr_nd_nsup = df_rr.ix[dict_pair_comp_nd['oil&ind']['tup_ids'].values]
  
  zero = np.float64(1e-10)
  ls_df_rrs_su = []
  for df_rrs_temp in [df_rr, df_rr_nd, df_rr_nd_sup, df_rr_nd_nsup]:
    se_nb_valid = df_rrs_temp.apply(lambda x: (~pd.isnull(x)).sum())
    # se_nb_valid = se_nb_valid.astype(float)
    se_nb_valid[se_nb_valid == 0] = np.nan
    se_nb_rr    = df_rrs_temp.apply(lambda x: (np.abs(x) > zero).sum())
    # se_nb_rr = se_nb_rr.astype(float)
    se_nb_rr[se_nb_rr == 0] = np.nan
    se_avg_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero]).mean() * 100)
    se_std_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero]).std() * 100)
    se_med_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero]).median() * 100)
    df_rrs_su_temp = pd.DataFrame({'se_nb_valid' : se_nb_valid,
                                   'se_nb_rr'    : se_nb_rr,
                                   'se_avg_rr'   : se_avg_rr,
                                   'se_std_rr'   : se_std_rr,
                                   'se_med_rr'   : se_med_rr})
    df_rrs_su_temp['pct_rr'] = df_rrs_su_temp['se_nb_rr'] / df_rrs_su_temp['se_nb_valid'] * 100
    ls_df_rrs_su.append(df_rrs_su_temp) 
  
  print()
  print(u'Overview pct rank reversals - No differentiation')
  print(ls_df_rrs_su[1].describe())

  plt.rcParams['figure.figsize'] = 16, 6
  
  ls_loop_rr_temp = [['All', ls_df_rrs_su[0]],
                     #['Low differentiation', ls_df_rrs_su[1]],
                     ['Supermarkets & Discounters', ls_df_rrs_su[2]],
                     ['Oil & Independent', ls_df_rrs_su[3]]]
  
  fig = plt.figure()
  ax1 = fig.add_subplot(111)
  ls_l = []
  for (label, df_temp), ls, alpha in zip(ls_loop_rr_temp,
                                         ['-', '-', '--', ':'],
                                         [1, 0.4, 1, 1]):
    ls_l.append(ax1.plot(df_temp.index,
                         df_temp['pct_rr'].values,
                         c = 'k', ls = ls, alpha = alpha,
                         label = label))
  lns = [x[0] for x in ls_l]
  labs = [l.get_label() for l in lns]
  ax1.set_ylim(0, 50.0)
  ax1.legend(lns, labs, loc=0, labelspacing = 0.3)
  ax1.grid()
  # Show ticks only on left and bottom axis, out of graph
  ax1.yaxis.set_ticks_position('left')
  ax1.xaxis.set_ticks_position('bottom')
  ax1.get_yaxis().set_tick_params(which='both', direction='out')
  ax1.get_xaxis().set_tick_params(which='both', direction='out')
  plt.xlabel('')
  plt.ylabel(u'Share of reversed pairs (%)')
  plt.tight_layout()
  plt.savefig(os.path.join(path_dir_built_dis_graphs,
                           dir_graphs,
                           'macro_rank_reversals_le_{:.0f}c.png'.format(diff_bound)),
              bbox_inches='tight')
  plt.close()
