#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
import pprint

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_dispersion')

path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

# #################
# LOAD ALL INFO DFS
# #################

df_chars = pd.read_csv(os.path.join(path_dir_built_csv,
                                    'df_chars.csv'),
                       encoding = 'utf-8',
                       dtype = {'id_station' : str,
                                'adr_zip' : str,
                                'adr_dpt' : str})
# could read whole as str and then destr a few columns
df_chars.set_index('id_station', inplace = True)

df_geocoding = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_geocoding.csv'),
                           encoding = 'utf-8',
                           dtype = {'id_station' : str})
df_geocoding.set_index('id_station', inplace = True)

df_ci = pd.read_csv(os.path.join(path_dir_built_csv,
                                 'df_ci.csv'),
                           encoding = 'utf-8',
                           dtype = str)
df_ci.set_index('id_station', inplace = True)

df_brand_activity = pd.read_csv(os.path.join(path_dir_built_csv,
                                             'df_brand_activity.csv'),
                           encoding = 'utf-8',
                           dtype = {'id_station' : str,
                                    'dilettante' : int})
df_brand_activity.set_index('id_station', inplace = True)

# #######
# MERGE
# #######

df_station_info = pd.merge(df_chars,
                           df_brand_activity,
                           left_index = True,
                           right_index = True,
                           how = 'outer')

for df_temp in [df_ci, df_geocoding]:
  df_station_info = pd.merge(df_station_info,
                             df_temp,
                             left_index = True, 
                             right_index = True,
                             how = 'outer')

# ######
# OUTPUT
# ######

# CSV
df_station_info.to_csv(os.path.join(path_dir_built_csv,
                                    'df_station_info.csv'),
                       index_label = 'id_station',
                       float_format= '%.3f',
                       encoding = 'utf-8')

# XLS (?)
