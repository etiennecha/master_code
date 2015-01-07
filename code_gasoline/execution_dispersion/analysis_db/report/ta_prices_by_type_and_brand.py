#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import datetime
import time
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:,.0f}'.format(x)
format_float_float = lambda x: '{:,.2f}'.format(x)

# LOAD DATA

df_prices = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices.set_index('date', inplace = True)

df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_station_stats.csv'),
                               dtype = {'id_station' : str},
                               encoding = 'utf-8')
df_station_stats.set_index('id_station', inplace = True)

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
                      parse_dates = [u'day_%s' %i for i in range(3)]) # fix
df_info.set_index('id_station', inplace = True)

df_stats_all = pd.merge(df_info, df_station_stats, left_index = True, right_index = True)
# exclude highway
df_stats = df_stats_all[df_stats_all['highway'] != 1].copy()
# exclude not enough price data
df_stats = df_stats[(df_stats['nb_chge'] >= 5) &\
                    (df_stats['pct_chge'] >= 0.03)].copy()

# STATS DESC
df_stats['brand_last'] = df_stats[['brand_0', 'brand_1', 'brand_2']].apply(\
                           lambda row: [x for x in row\
                                          if not pd.isnull(x)][-1], axis = 1)

# Nb of digits by brand (pbm create col last avail brand)
se_2d = df_stats['brand_last'][df_stats['2d'] == 1].value_counts()
se_3d = df_stats['brand_last'][df_stats['2d'] == 0].value_counts()
df_digits_bb = pd.concat([se_2d, se_3d], axis = 1, keys = ['#two', '#three'])
df_digits_bb.fillna(0, inplace = True)
df_digits_bb['#total'] = df_digits_bb.sum(1)
df_digits_bb['%two'] = df_digits_bb['#two'] / df_digits_bb['#total']
df_digits_bb.sort('#total', ascending = False, inplace = True)
df_digits_bb.ix['ALL_STATIONS'] = [df_digits_bb['#two'].sum(),
                                   df_digits_bb['#three'].sum(),
                                   df_digits_bb['#total'].sum(),
                                   df_digits_bb['#two'].sum() / df_digits_bb['#total'].sum()]
dict_formatters = {'#two': format_float_int,
                   '#three': format_float_int,
                   '#total' : format_float_int}
print df_digits_bb[['#total', '#three', '#two', '%two']]\
        [df_digits_bb['#total'] > 10].to_string(formatters = dict_formatters)

# todo: Nb digits by regrouped brand + by type (loop...)

# Check Total w/ 2 digits vs. w/3 (then do regressions etc.)
brand = 'LECLERC'

print u'\nPct chge w/ 2 digits'
print df_stats['pct_chge'][(df_stats['brand_last'] == brand) &\
                           (df_stats['2d'] == 1)].describe()

print u'\nPct chge w/ 3 digits'
print df_stats['pct_chge'][(df_stats['brand_last'] == brand) &\
                           (df_stats['2d'] == 0)].describe()

ls_total_2d = list(df_stats.index[(df_stats['brand_last'] == brand) &\
                                  (df_stats['2d'] == 1)])
ls_total_3d = list(df_stats.index[(df_stats['brand_last'] == brand) &\
                                   (df_stats['2d'] == 0)])

# Price distributions on a given day
day_ind = 600

print u'\nPrices in a given day w/ 2 digits'
print df_prices[ls_total_2d].iloc[day_ind].describe()

print u'\nPrices in a given day w/ 3 digits'
print df_prices[ls_total_3d].iloc[day_ind].describe()

se_2d = df_prices[ls_total_2d].iloc[day_ind]
se_2d = se_2d[~pd.isnull(se_2d)]
se_3d = df_prices[ls_total_3d].iloc[day_ind]
se_3d = se_3d[~pd.isnull(se_3d)]
bins = np.linspace(1.25, 1.75, 30)
hist_2d = plt.hist(se_2d, bins, alpha = 0.5, label = '2d')
hist_3d = plt.hist(se_3d, bins, alpha = 0.5, label = '3d')
plt.legend(loc='upper right')
plt.show()

# Difference in mean over time
se_diff = df_prices[ls_total_2d].mean(1) - df_prices[ls_total_3d].mean(1)
se_diff.plot()
plt.show()
