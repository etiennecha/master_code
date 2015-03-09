#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_paper_dispersion')

path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

# #########
# LOAD DATA
# #########

# LOAD PAIRS: includes both competitors and same group pairs
ls_pairs = dec_json(os.path.join(path_dir_built_json,
                                 'ls_close_pairs.json'))

# LOAD DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = True)
df_prices_cl.set_index('date', inplace = True)

# LOAD DF MARGIN CHANGE
df_margin_chge = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_margin_chge.csv'),
                             dtype = {'id_station' : str},
                             encoding = 'utf-8')
df_margin_chge.set_index('id_station', inplace = True)

df_margin_chge = df_margin_chge[df_margin_chge['value'].abs() >= 0.03]

# LOAD DF INFO
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

# LOAD DF STATION STATS
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# LOAD DF PAIR STATS
df_ppd = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_pair_raw_price_dispersion.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_1' : str,
                                        'id_2' : str})

# LOAD DF PAIR DISPERSION
df_pair_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_pair_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_1' : str,
                                        'id_2' : str})

# ################
# PREPARE DF PAIRS
# ################

# MERGE PAIR STATS AND DISPERSION
df_ppd.drop(labels = ['distance', 'nb_spread'], axis = 1, inplace = True)
df_pairs = pd.merge(df_ppd,
                    df_pair_stats,
                    on = ['id_1', 'id_2'],
                    how = 'left')

# ADD STATION INFO
df_info_sub = df_info[['ci_ardt_1', 'dpt', 'reg',
                       'brand_0', 'group', 'group_type',
                       'brand_last', 'group_last', 'group_type_last']].copy()
df_info_sub['id_1'] = df_info_sub.index
df_pairs = pd.merge(df_info_sub,
                    df_pairs,
                    on='id_1',
                    how = 'right')
df_info_sub.rename(columns={'id_1': 'id_2'}, inplace = True)
df_pairs = pd.merge(df_info_sub,
                    df_pairs,
                    on = 'id_2',
                    how = 'right',
                    suffixes=('_2', '_1'))

## Check result of merger
#print df_pairs[['id_1', 'id_2', 'group_1', 'group_2']][0:10].to_string()
#print df_info.ix['10000001']['group']
#print df_info.ix['10000005']['group']

# DROP PAIRS WITH INSUFFICIENT DATA
print u'\nNb observations filtered out for lack of data: {:.0f}'.format(\
      len(df_pairs[~((df_pairs['nb_chges_min'] >= 20) &
                     (df_pairs['nb_spread'] >= 30) &\
                     (df_pairs['nb_ctd_both'] >= 30))]))

df_pairs = df_pairs[(df_pairs['nb_chges_min'] >= 20) &
                    (df_pairs['nb_spread'] >= 30) &\
                    (df_pairs['nb_ctd_both'] >= 30)]

# CREATE SAME CORNER VARIABLE
for dist in [500, 750, 1000]:
  df_pairs['sc_{:d}'.format(dist)] = 0
  df_pairs.loc[df_pairs['distance'] <= dist/1000.0, 'sc_{:d}'.format(dist)] = 1

# ######
# OUPUT
# ######

df_pairs.to_csv(os.path.join(path_dir_built_csv,
                             'df_pairs.csv'),
                encoding = 'utf-8',
                index = False)

## SEPARATE SAME GROUP vs. COMPETITORS
#
#df_pairs_sg = df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
#                       (df_pairs['group_last_1'] == df_pairs['group_last_2'])]
#
#df_pairs_cp = df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
#                       (df_pairs['group_last_1'] != df_pairs['group_last_2'])]
#
#df_pairs_sg.to_csv(os.path.join(path_dir_built_csv,
#                                'df_pairs_sg.csv'),
#                   encoding = 'utf-8',
#                   index = False)
#
#df_pairs_cp.to_csv(os.path.join(path_dir_built_csv,
#                                'df_pairs_cp.csv'),
#                   encoding = 'utf-8',
#                   index = False)
