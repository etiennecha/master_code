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

# SELECTION PRICE / DAY
ls_cols_price = ['price_at', 'price_bt', 'Markup']
ls_cols_comp = ['nb_c_1km', 'nb_c_3km', 'nb_c_5km', 'dist_c']
ls_cols_rigidity = ['pct_chge', 'avg_pos_chge', 'avg_neg_chge']

df_info.rename(columns = {'group' : 'group_0',
                          'group_type' : 'group_type_0'},
               inplace = True)

#str_date, str_be = '2011-09-04', '0'
str_date, str_be = '2014-12-04', 'last'

df_info['price_at'] = df_prices_ttc.ix[str_date]
df_info['price_bt'] = df_prices_ht.ix[str_date]

df_info['brand'] = df_info['brand_{:s}'.format(str_be)]
df_info['group'] = df_info['group_{:s}'.format(str_be)]
df_info['group_type'] = df_info['group_type_{:s}'.format(str_be)]

df_sub = df_info[~df_info['price_at'].isnull()].copy()
df_sub['nb_brand'] = df_sub[['price_at', 'brand']].groupby('brand')\
                                                  .transform(len)['price_at']
df_sub = df_sub[df_sub['nb_brand'] >= 50]

# #######################
# STATS DES: CHAIN PRICES
# #######################

ls_pctiles = [0.10, 0.25, 0.75, 0.90]
df_desc = df_sub[['price_at', 'group_type', 'brand']]\
                .groupby(['group_type', 'brand'])\
                .describe(percentiles = ls_pctiles).unstack()['price_at']
df_desc.reset_index(drop = False, inplace = True)
df_desc['Q75/Q25'] = df_desc['75%'] / df_desc['25%']
df_desc['Q90/Q10'] = df_desc['90%'] / df_desc['10%']
#df_desc.drop(['min', '10%', '25%', '50%', '75%', '90%', 'max'],
#             axis = 1,
#             inplace = True)
df_desc['count'] = df_desc['count'].astype(int)

#ls_drop_brands = ['INDEPENDANT',
#                  'COLRUYT',
#                  'NETTO']
#df_desc = df_desc[~df_desc['brand'].isin(ls_drop_brands)]

print()
print(u'Price distribution by chain:')
print(df_desc.to_string(float_format = '{:,.2f}'.format))

# ############
# REGRESSIONS
# ############

# SOME DUMMIES
ls_ls_areas = [['idf', ['77', '78', '91', '95']],
               ['pariss', ['92', '93', '94']],
               ['paris', ['75']],
               ['paca', ['13']]]
for area_title, ls_area_dpts in ls_ls_areas:
  df_sub[area_title] = 0
  df_sub.loc[df_sub['dpt'].isin(ls_area_dpts),
             area_title] = 1

# CHAINS : NO CONTROLS
print()

res_chains = smf.ols('price_at ~ brand', data = df_sub).fit()
print(res_chains.summary())

res_type = smf.ols('price_at ~ group_type', data = df_sub).fit()
print(res_type.summary())

res_chains_sup = smf.ols('price_at ~ brand',
                         data = df_sub[df_sub['group_type'] == 'SUP']).fit()
print(res_chains_sup.summary())

res_chains_nsup = smf.ols('price_at ~ brand',
                          data = df_sub[df_sub['group_type'] != 'SUP']).fit()
print(res_chains_nsup.summary())

res_type = smf.ols('price_at ~ group_type', data = df_sub).fit()
print(res_type.summary())

# CHAINS: WITH CONTROLS

# adapt dist for idf / paca (avoid large nb of competitors)
df_sub.loc[((df_sub['idf'] == 1) | (df_sub['paca'] == 1)),
           'nb_c_3km'] = df_sub['nb_c_2km']

df_sub['monop'] = 0
df_sub.loc[df_sub['dist_c'] >= 5, 'monop'] = 1

res_chains_c = smf.ols('price_at ~ idf + pariss + paris + brand' +\
                       ' + nb_c_3km + dist_c_sup',
                        data = df_sub).fit()
print(res_chains_c.summary())

res_chains_c_alt = smf.ols('price_at ~ brand' +\
                           ' + nb_c_3km + dist_c_sup',
                            data = df_sub[(df_sub['idf'] == 0) &\
                                          (df_sub['paca'] == 0)]).fit()
print(res_chains_c_alt.summary())
