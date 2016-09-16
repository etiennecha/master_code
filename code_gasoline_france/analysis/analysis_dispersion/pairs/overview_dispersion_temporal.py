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
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

# basic station filter (geo scope or insufficient obs.)
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'corse')].index)))
ls_drop_ids = list(set(df_prices_ttc.columns).difference(set(ls_keep_ids)))
df_prices_ttc[ls_drop_ids] = np.nan
df_prices_ht[ls_drop_ids] = np.nan
# highway stations may not be in df_prices_cl (no pbm here)
ls_drop_ids_cl = list(set(df_prices_cl.columns).difference(set(ls_keep_ids)))
df_prices_cl[ls_drop_ids_cl] = np.nan
#df_info = df_info.ix[ls_keep_ids]
#df_station_stats = df_station_stats.ix[ls_keep_ids]

# DF PAIRS
ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                    'df_pair_final.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# basic pair filter (insufficient obs.)
df_pairs = df_pairs[(~((df_pairs['nb_spread'] < 90) &\
                       (df_pairs['nb_ctd_both'] < 90))) &
                    (~(df_pairs['nrr_max'] > 60))]

## filter on distance: 5 km
#df_pairs = df_pairs[df_pairs['distance'] <= 5]

# todo? harmonize pct i.e. * 100

# LISTS FOR DISPLAY
lsd = ['id_1', 'id_2', 'distance', 'group_last_1', 'group_last_2']
lsd_rr = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

# DF RANK REVERSALS
df_rr = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                 'df_rank_reversals_all.csv'),
                    parse_dates = ['date'],
                    encoding = 'utf-8')
df_rr.set_index('date', inplace = True)
df_rr = df_rr.T
df_rr.index = [tuple(x.split('-')) for x in df_rr.index]

# ##################
# FILTER DATA
# ##################

# keep pairs with margin change to allow overview of total access chge impact

# RESTRICT CATEGORY: PRICES AND MARGIN CHGE
df_pairs_all = df_pairs.copy()
# price_cat = 'all' # to have impact of total access with margin chges
price_cat = 'no_mc' # 'residuals_no_mc'
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

# DIFFERENTIATED VS. NON DIFFERENTIATED
diff_bound = 0.01
df_pair_same_nd = df_pair_same[df_pair_same['abs_mean_spread'] <= diff_bound]
df_pair_same_d  = df_pair_same[df_pair_same['abs_mean_spread'] > diff_bound]
df_pair_comp_nd = df_pair_comp[df_pair_comp['abs_mean_spread'] <= diff_bound]
df_pair_comp_d  = df_pair_comp[df_pair_comp['abs_mean_spread'] > diff_bound]

# DICT OF DFS
# pairs without spread restriction
# (keep pairs with group change in any)
dict_pair_comp = {'any' : df_pair_comp}
for k in df_pair_comp['pair_type'].unique():
  dict_pair_comp[k] = df_pair_comp[df_pair_comp['pair_type'] == k]
# low spread pairs
dict_pair_comp_nd = {}
for df_temp_title, df_temp in dict_pair_comp.items():
  dict_pair_comp_nd[df_temp_title] =\
      df_temp[df_temp['abs_mean_spread'] <= diff_bound]

# FOCUS ON COMPETITOR PAIRS
df_ppd = df_pair_comp.copy()
df_ppd['tup_ids'] = df_ppd.apply(lambda row: (row['id_1'], row['id_2']),
                                 axis = 1)

# PAIRS W/ TOTAL ACCESS
df_ppd_ta = df_ppd[(df_ppd['brand_last_1'] == 'TOTAL_ACCESS') |
                   (df_ppd['brand_last_2'] == 'TOTAL_ACCESS')]
df_ppd_nota = df_ppd[(df_ppd['brand_last_1'] != 'TOTAL_ACCESS') &
                     (df_ppd['brand_last_2'] != 'TOTAL_ACCESS')]
# Price spread restriction (not total access)
df_ppd_nota_nd = df_ppd_nota[df_ppd_nota['abs_mean_spread'] <= diff_bound]
df_ppd_nota_d = df_ppd_nota[df_ppd_nota['abs_mean_spread'] >  diff_bound]

## ####################
## DF PAIR PD TEMPORAL
## ####################

# Select pair subsamples
df_rr = df_rr.ix[df_ppd['tup_ids'].values]
df_rr_ta = df_rr.ix[df_ppd_ta['tup_ids'].values]
df_rr_nota = df_rr.ix[df_ppd_nota['tup_ids'].values]
df_rr_nd = df_rr.ix[df_ppd_nota_nd['tup_ids'].values] # ta excluded

zero = np.float64(1e-10)
ls_df_rrs_su = []
for df_rrs_temp in [df_rr, df_rr_ta, df_rr_nota, df_rr_nd]:
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
print(ls_df_rrs_su[-1].describe())

plt.rcParams['figure.figsize'] = 16, 6
ls_df_rrs_su[-1]['pct_rr'].plot()
plt.title('Overview pct rank reversals - No differentiation')
plt.show()

# Merge: to be improved? (more dataframes potentially?)
df_rrs_su_all = pd.merge(ls_df_rrs_su[0], ls_df_rrs_su[1],\
                         right_index = True, left_index = True, suffixes=('', '_ta'))
df_rrs_su_all = pd.merge(df_rrs_su_all, ls_df_rrs_su[2],\
                         right_index = True, left_index = True, suffixes=('', '_nota'))
df_rrs_su_all = pd.merge(df_rrs_su_all, ls_df_rrs_su[3],\
                         right_index = True, left_index = True, suffixes=('', '_nodiff'))

df_rrs_su_all[df_rrs_su_all['pct_rr_nota'] == np.inf] = np.nan
print()
print('Overview pct rank reversals (excluding Total Access)')
print(df_rrs_su_all['pct_rr_nota'].describe())
print('Argmax (day):', df_rrs_su_all['pct_rr_nota'].argmax())

df_rrs_su_all[df_rrs_su_all['pct_rr_nodiff'] == np.inf] = np.nan
print()
print('Overview pct rank reversals (No differentiation (nor TA))')
print(df_rrs_su_all['pct_rr_nodiff'].describe())

plt.rcParams['figure.figsize'] = 16, 6
ax = df_rrs_su_all[['pct_rr', 'pct_rr_ta', 'pct_rr_nota', 'pct_rr_nodiff']].plot()
handles, labels = ax.get_legend_handles_labels()
labels = ['All', 'Total Access', 'All but Total Access', 'No differentiation']
ax.legend(handles, labels)
plt.title('Overview pct rank reversals')
plt.tight_layout()
plt.show()
