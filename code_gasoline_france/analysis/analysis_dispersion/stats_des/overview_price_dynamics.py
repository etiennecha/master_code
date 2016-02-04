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

df_station_stats = pd.merge(df_station_stats,
                            df_info[['brand_last',
                                     'group_last',
                                     'group_type_last']],
                            left_index = True,
                            right_index = True,
                            how = 'left')

df_station_stats_sup =\
  df_station_stats[df_station_stats['group_type_last'] == 'SUP']
df_station_stats_nsup =\
  df_station_stats[df_station_stats['group_type_last'] != 'SUP']

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

# ######################
# SIMULATE STATION PRICE
# ######################

# assuming one change per week

zero = 1e-10

print()
print(u'Price changes based on simple simulation:')
for day in range(0,5):
  print()
  print('Day:', day)
  df_dyna = pd.DataFrame(df_prices_ht.mean(1),
                         index = df_prices_ht.index,
                         columns = ['Retail diesel before tax (France)'])
  df_dyna['Wholesale diesel (Rotterdam)'] = df_cost['UFIP RT Diesel R5 EL']
  df_dyna['Brent (Rotterdam)'] = df_cost['UFIP Brent R5 EB'] / 158.987295
  
  df_dyna['retail_star'] = (df_dyna['Wholesale diesel (Rotterdam)'] + 0.4419) * 1.196
  
  df_dyna['wd'] = df_dyna.index.weekday # friday is 4
  df_dyna['retail_day'] = np.nan
  df_dyna.loc[df_dyna['wd'] == day, 'retail_day'] = df_dyna['retail_star']
  df_dyna['retail_day'] = df_dyna['retail_day'].fillna(method = 'ffill')
  df_dyna['rd_chge'] =\
    df_dyna['retail_day'] - df_dyna['retail_day'].shift(1)
  
  print(u'Positive chges')
  print(u'Nb: {:d}'.format(len(df_dyna['rd_chge'][df_dyna['rd_chge'] > zero])))
  print(u'Mean: {:.3f}'.format(df_dyna['rd_chge'][df_dyna['rd_chge'] > zero].mean()))
  
  print(u'Negative chges')
  print(u'Nb: {:d}'.format(len(df_dyna['rd_chge'][df_dyna['rd_chge'] < -zero])))
  print(u'Mean: {:.3f}'.format(df_dyna['rd_chge'][df_dyna['rd_chge'] < -zero].mean()))

# consistant with actual stats
print()
print('Actual station price stats:')
for title, df_stats in [['All', df_station_stats],
                        ['Sup', df_station_stats_sup],
                        ['Others', df_station_stats_nsup]]:
  print()
  print(u'-'*20)
  print(title)

  print()
  print(df_stats[['nb_valid', 'nb_chge', 'pct_chge']].describe().to_string())
  
  print()
  print(df_stats[['nb_pos_chge', 'nb_neg_chge',
                  'avg_pos_chge', 'avg_neg_chge',
                  'med_pos_chge', 'med_neg_chge']].describe().to_string())

  print()
  print(df_stats['dow_max'].value_counts(normalize = 1))
  
  print()
  print(u'Dummy 2 digits:')
  print(df_stats['2d'].value_counts(normalize = 1))

  # Todo: total percent of chges on each day of week

# Promo? Cuts etc. seems similar distrib in supermarkets and others
ls_pctiles = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
print()
print(df_station_stats['nb_promo'].describe(percentiles = ls_pctiles).to_string())

# inspect : rather sups... (or different value for nsup)
df_station_stats_nsup[df_station_stats_nsup['nb_promo'] > 40].index[0:10]
df_station_stats_sup[df_station_stats_sup['nb_promo'] > 40].index[0:10]

# Case study: dynamic discrimination? obfuscation?
# Maybe focus on .ix['2013-11':'2014-06'] => period of price stability
id_station = '22190001'  # '10410001'
se_station = df_prices_ttc[id_station].ix['2013-12':'2014-05'].copy()
ax = se_station.plot()
for wd_date in se_station[se_station.index.weekday == 4].index: # 4 is friday
  ax.axvline(wd_date)
plt.show()
# todo: check exact timing of price cut and increase?
# '10410001' saturday is cheapest day?
# '22190001' saturday may be ok but sunday/monday/tu.. not su much?
