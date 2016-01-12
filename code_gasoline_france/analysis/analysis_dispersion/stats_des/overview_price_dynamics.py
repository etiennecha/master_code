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
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_built_other = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_other')
path_dir_built_other_csv = os.path.join(path_dir_built_other, 'data_csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DATA
# ##############

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
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

# DF PRICES

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

# DF STATION STATS

df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# FILTER DATA
# exclude stations with insufficient (quality) price data
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'Corse')].index)))
df_prices_ht = df_prices_ht[ls_keep_ids]
df_prices_ttc = df_prices_ttc[ls_keep_ids]
df_info = df_info.ix[ls_keep_ids]
df_station_stats = df_station_stats.ix[ls_keep_ids]

# DF COST (WHOLESALE GAS PRICES)
df_cost = pd.read_csv(os.path.join(path_dir_built_other_csv,
                                   'df_quotations.csv'),
                                 encoding = 'utf-8',
                                 parse_dates = ['date'])
df_cost.set_index('date', inplace = True)

# ##############
# GRAPH PRICE HT
# ##############

df_dyna = pd.DataFrame(df_prices_ht.mean(1),
                       index = df_prices_ht.index,
                       columns = ['Retail diesel before tax (France)'])
df_dyna['Wholesale diesel (Rotterdam)'] = df_cost['UFIP RT Diesel R5 EL']
df_dyna['Brent (Rotterdam)'] = df_cost['UFIP Brent R5 EB'] / 158.987295
#df_dyna['Brent (Rotterdam)'] = df_cost['Europe Brent FOB EL']

from pylab import *
rcParams['figure.figsize'] = 16, 6

ax = df_dyna.plot()
ax.set_ylabel(r"Price (euros/l)")
ax.set_xlabel('')

plt.tight_layout()
plt.show()

# #################
# GRAPH PRICE CHGES
# #################

df_chges = df_prices_ttc - df_prices_ttc.shift(1)
#df_chges = df_chges.ix['2012-01-01':'2012-12-31']

fig = plt.figure()
se_neg_chges = df_chges[df_chges < - 1e-10].count(1)
se_pos_chges = df_chges[df_chges >   1e-10].count(1)

ax = plt.subplot(111)
ax.bar(se_neg_chges.index, (-se_neg_chges).values, lw=0, color='r')
ax.bar(se_pos_chges.index, se_pos_chges.values, lw=0, color='b')
plt.show()
