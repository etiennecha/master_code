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

# DF COMP

df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_comp.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_comp.set_index('id_station', inplace = True)

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
df_comp = df_comp.ix[ls_keep_ids]

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

# DF STATION PRICE

str_date = '2011-09-04'
df_station_price = pd.DataFrame(df_prices_ttc.ix[str_date].values,
                                index = df_prices_ttc.columns,
                                columns = ['Price after tax'])
df_station_price['Price before tax'] = df_prices_ht.ix[str_date]
df_station_price['Markup'] = df_station_price['Price before tax'] -\
                               df_cost['UFIP RT Diesel R5 EL'].ix[str_date]

df_station_mprice = pd.DataFrame(df_prices_ttc.mean(0).values,
                                 index = df_prices_ttc.columns,
                                 columns = ['Price after tax'])
df_station_mprice['Price before tax'] = df_prices_ht.mean(0)
df_station_mprice['Markup'] = (df_prices_ht.subtract(df_cost['UFIP RT Diesel R5 EL'],
                                                     axis = 'index')).mean(0)

# ##########
# STATS DES
# ##########

ls_ids_sup = df_info[df_info['group_type_last'] == 'SUP'].index
ls_ids_nsup = df_info[df_info['group_type_last'] != 'SUP'].index
ls_ids_idf = df_info[df_info['reg'] == 'Ile-de-France'].index
ls_ids_nidf = df_info[df_info['reg'] != 'Ile-de-France'].index
ls_ids_fra = df_info.index

ls_loop_groups = [('Supermarkets', ls_ids_sup),
                  ('Non Supermarkets', ls_ids_nsup),
                  ('Paris region', ls_ids_idf),
                  ('Non Paris region', ls_ids_nidf),
                  ('France', ls_ids_fra)]

ls_cols_price = ['Price after tax', 'Price before tax', 'Markup']
ls_cols_comp = ['nb_c_1km', 'nb_c_3km', 'nb_c_5km', 'dist_c']
ls_cols_rigidity = ['pct_chge', 'avg_pos_chge', 'avg_neg_chge']

ls_loop_topics = [('Price', df_station_mprice, ls_cols_price),
                  ('Competition', df_comp, ls_cols_comp),
                  ('Rigidity', df_station_stats, ls_cols_rigidity)]

dict_df_topics = {}
for topic_title, df_topic, ls_cols_topic in ls_loop_topics:
  ls_titles_desc_temp, ls_se_desc_temp = [], []
  for group_title, ls_ids_group in ls_loop_groups:
    se_desc_temp = df_topic.ix[ls_ids_group][ls_cols_topic].mean()
    ls_se_desc_temp.append(se_desc_temp)
    ls_titles_desc_temp.append(group_title)
  df_topic_desc = pd.concat(ls_se_desc_temp,
                            axis = 1,
                            keys = ls_titles_desc_temp)
  dict_df_topics[topic_title] = df_topic_desc

df_desc = pd.concat([dict_df_topics['Price'],
                     dict_df_topics['Competition'],
                     dict_df_topics['Rigidity']])

df_desc.ix['avg_pos_chge'] = df_desc.ix['avg_pos_chge'] * 100
df_desc.ix['avg_neg_chge'] = df_desc.ix['avg_neg_chge'] * 100

df_desc.rename(index = {'nb_c_1km' : 'Nb of rivals within 1 km',
                        'nb_c_3km' : 'Nb of rivals within 3 km',
                        'nb_c_5km' : 'Nb of rivals within 5 km',
                        'dist_c'   : 'Distance to closest rival',
                        'pct_chge' : 'Daily price change probability',
                        'avg_pos_chge' : 'Mean positive price change (cent)',
                        'avg_neg_chge' : 'Mean negative price change (cent)'},
               inplace = True)

df_desc.ix['Nb stations (total)'] =\
  [len(ls_ids_group) for group_title, ls_ids_group in ls_loop_groups]

df_desc.ix['Nb stations (observed)'] =\
  [df_prices_ttc[ls_ids_group].count(1).mean()\
     for group_title, ls_ids_group in ls_loop_groups]

print(df_desc.to_string())

# ##################################
# HISTOGRAM PRICE CHANGE PROBABLITY
# ##################################

myarray = df_station_stats['pct_chge'].values
weights = np.ones_like(myarray)/float(len(myarray)) * 100

fig = plt.figure()
ax = fig.add_subplot(111)
n, bins, rectangles = ax.hist(myarray,
                              weights = weights,
                              bins = np.linspace(0, 1, 21),
                              normed = 0)
ax.set_xlabel('Daily price change probability')
ax.set_ylabel('Percent')
plt.show()

# #########################
# HISTOGRAM PRICE CHANGES
# #########################

df_chges = df_prices_ttc - df_prices_ttc.shift(1)
ar_chges = df_chges.values.flatten()
ar_chges = ar_chges[(~np.isnan(ar_chges)) & (np.abs(ar_chges) > 1e-10)]

ar_chges = ar_chges * 100
weights = np.ones_like(ar_chges)/float(len(ar_chges)) * 100

fig = plt.figure()
ax = fig.add_subplot(111)
n, bins, rectangles = ax.hist(ar_chges,
                              weights = weights,
                              bins = np.linspace(-10, 10, 101),
                              normed = 0)
ax.set_xlabel('Price changes')
ax.set_ylabel('Percent')
ax.set_xlim(-10, 10)
plt.xticks(np.linspace(-10, 10, 21))
plt.show()
