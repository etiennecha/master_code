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

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

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
df_pairs['tup_ids'] = df_pairs.apply(lambda x: (x['id_1'], x['id_2']),
                                     axis = 1)

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

# DF RANK REVERSALS

df_rr = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                 'df_rank_reversals.csv'),
                    parse_dates = ['date'],
                    encoding = 'utf-8')
df_rr.set_index('date', inplace = True)
df_rr = df_rr.T
df_rr.index = [tuple(x.split('-')) for x in df_rr.index]

# ##################
# FILTER DATA
# ##################

# FOCUS ON COMPETITOR PAIRS

df_ppd = df_pair_comp

# DROP PAIRS WITH INSUFFICIENT PRICE DATA

print("Dropped pairs (insuff spread obs):",\
        len(df_ppd[(df_ppd['mean_spread'].isnull()) | (df_ppd['nb_spread'] < 100)]))
df_ppd = df_ppd[(~df_ppd['mean_spread'].isnull()) & (df_ppd['nb_spread'] >= 100)]

# SEPARATE PAIRS W/ TOTAL ACCESS
# todo: more generally: price policy change
# df_prices_ttc[['63000013','63000019']].plot()

df_ppd_ta = df_ppd[(df_ppd['brand_last_1'] == 'TOTAL_ACCESS') |
                   (df_ppd['brand_last_2'] == 'TOTAL_ACCESS')]
df_ppd_nota = df_ppd[(df_ppd['brand_last_1'] != 'TOTAL_ACCESS') &
                     (df_ppd['brand_last_2'] != 'TOTAL_ACCESS')]

# SEPARATE DIFF AND NO DIFF

diff_bound = 0.01
# caution not to restrict df_ppd to df_ppd for now => overview before
df_ppd_nodiff = df_ppd_nota[df_ppd_nota['abs_mean_spread'] <= diff_bound]
df_ppd_diff   = df_ppd_nota[df_ppd_nota['abs_mean_spread'] >  diff_bound]
ls_ppd_names = ['All', 'No differentation', 'Differentiation']

## ####################
## DF PAIR PD TEMPORAL
## ####################

# Keep filtered pairs
df_rr = df_rr.ix[df_ppd['tup_ids'].values]
df_rr_ta = df_rr.ix[df_ppd_ta['tup_ids'].values]
df_rr_nota = df_rr.ix[df_ppd_nota['tup_ids'].values]
df_rr_nd = df_rr.ix[df_ppd_nodiff['tup_ids'].values] # ta excluded

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
