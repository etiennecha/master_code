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
path_dir_built_json = os.path.join(path_dir_built, u'data_json')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_built_zagaz = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_zagaz')
path_dir_built_zagaz_csv = os.path.join(path_dir_built_zagaz, 'data_csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DATA
# ##############

# INFO

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

# COMP

dict_comp_dtype = {'id_ta_{:d}'.format(i) : str for i in range(23)}
dict_comp_dtype['id_station'] = str
df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_comp.csv'),
                      dtype = dict_comp_dtype,
                      encoding = 'utf-8')
df_comp.set_index('id_station', inplace = True)

dict_close = dec_json(os.path.join(path_dir_built_json,
                                   'dict_ls_close.json'))

ls_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                          'ls_robust_stable_markets.json'))

# PRICE STATS DES

df_price_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_station_stats.csv'),
                               dtype = {'id_station' : str},
                               encoding = 'utf-8')
df_price_stats.set_index('id_station', inplace = True)

# MATCHING ZAGAZ

df_matching_zagaz = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                             'df_zagaz_stations_match_1.csv'),
                                dtype = {'zag_id' : str,
                                         'gov_id' : str,
                                         'ci' : str},
                                encoding = 'utf-8')

# ZAGAZ INFO

df_zagaz_info = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                         'df_zagaz_stations.csv'),
                            encoding='utf-8',
                            dtype = {'id_zagaz' : str,
                                     'zip' : str,
                                     'ci_1' : str,
                                     'ci_ardt_1' : str})
df_zagaz_info.set_index('id_zagaz', inplace = True)

# ZAGAZ USER DATA

df_zagaz_users = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                          'df_zagaz_users_201404.csv'),
                             encoding = 'utf-8')

df_zagaz_reports = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                            'df_zagaz_price_reports_201404.csv'),
                               dtype = {'station' : str},
                               encoding = 'utf-8')

# ADD ZAGAZ INFO TO GOV INFO

lsdzm = ['gov_id', 'zag_id',
         'zag_street', 'zag_city',
         'zag_br', 'zag_lat', 'zag_lng']

df_info = pd.merge(df_info,
                   df_matching_zagaz[lsdzm],
                   left_index = True,
                   right_on = 'gov_id',
                   how = 'left')

df_info = df_info[df_info['highway'] != 1]

# ############
# STATS DES
# ############

# todo: comp with zagaz info only
# todo: number of robust stable markets in zagaz
# todo: check if appears in zagaz user data
