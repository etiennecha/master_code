#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *

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

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

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

print(u'Nb of stations in df_info before filtering: {:d}'.format(len(df_info)))
print(u'Nb on highway: {:d}'.format(len(df_info[df_info['highway'] == 1])))
print(u'Nb in Corsica: {:d}'.format(len(df_info[df_info['reg'] == 'Corse'])))

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

# DF STATION STATS

df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

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

# DF COST (WHOLESALE GAS PRICES)
df_cost = pd.read_csv(os.path.join(path_dir_built_other_csv,
                                   'df_quotations.csv'),
                                 encoding = 'utf-8',
                                 parse_dates = ['date'])
df_cost.set_index('date', inplace = True)

# fill backward (except first day...)
df_cost.fillna(axis = 'index',
               method = 'bfill',
               inplace = True)
df_cost.ix['2011-09-04'] = df_cost.ix['2011-09-05']

# ADD COMP
df_info = pd.merge(df_info,
                   df_comp,
                   left_index = True,
                   right_index = True,
                   how = 'left')

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

# ###############
# PRICE BOUNDS
# ###############

df_prices = df_prices_ttc.copy()

## Robustness check: use price only upon change
df_chges = df_prices - df_prices.shift(1)
df_prices = df_prices[df_chges.abs() > 1e-5]

# do with cleaned prices?

ind_ids_high = df_info[(df_info['group_type'].isin(['OIL', 'IND'])) &\
                     (df_info['group_type_last'].isin(['OIL', 'IND']))].index
ind_ids_low = df_info[(df_info['group_type'].isin(['HYP', 'SUP', 'DIS'])) &\
                      (df_info['group_type_last'].isin(['HYP', 'SUP', 'DIS']))].index
ind_ids_low_nd = df_info[(df_info['group_type'].isin(['HYP', 'SUP'])) &\
                         (df_info['group_type_last'].isin(['HYP', 'SUP']))].index


ls_pctiles = [0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95]

df_high_desc = df_prices[ind_ids_high].T.describe(percentiles = ls_pctiles).T
df_low_desc = df_prices[ind_ids_low].T.describe(percentiles = ls_pctiles).T

str_cost = 'UFIP RT Diesel R5 EL'
df_high_desc['cost'] = df_cost[str_cost]
df_low_desc['cost'] = df_cost[str_cost]

df_high_desc = df_high_desc[df_high_desc.index >= '2013-02-01']
df_low_desc = df_low_desc[df_low_desc.index >= '2013-02-01']

ax = df_high_desc.plot(kind = 'scatter', x = 'cost', y = 'mean', color = 'b')
df_low_desc.plot(kind = 'scatter', x = 'cost', y = 'mean', color = 'g', ax = ax)
plt.show()

# max price sensitive to outliers but still (can use 95%... same conclusion)
df_high_desc.plot(kind = 'scatter', x = 'cost', y = 'max', color = 'b')
plt.show()

df_low_desc.plot(kind = 'scatter', x = 'cost', y = 'max', color = 'b')
plt.show()

# one gas station
df_prices['cost'] = df_cost[str_cost]
ax = df_prices.plot(kind = 'scatter', x = 'cost', y = df_prices.columns[0], color = 'b')
plt.show()
