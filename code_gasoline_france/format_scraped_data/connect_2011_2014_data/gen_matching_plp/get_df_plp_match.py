#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_scraped = os.path.join(path_data,
                                      u'data_gasoline',
                                      u'data_built',
                                      u'data_scraped_2011_2014')

path_dir_built_scraped_csv = os.path.join(path_dir_built_scraped,
                                          u'data_csv')

path_dir_built_plp = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_scraped_2007_2009')

path_dir_built_plp_csv = os.path.join(path_dir_built_plp, 
                                      'data_csv')

# #########################
# LOAD INFO STATIONS
# #########################

df_info = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
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
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
df_info.set_index('id_station', inplace = True)

df_info_plp = pd.read_csv(os.path.join(path_dir_built_plp_csv,
                                       'df_plp_info.csv'),
                          encoding = 'utf-8',
                          dtype = {'id_station' : str,
                                   'adr_zip' : str,
                                   'adr_dpt' : str,
                                   'ci_1' : str,
                                   'ci_ardt_1' :str,
                                   'ci_2' : str,
                                   'ci_ardt_2' : str,
                                   'dpt' : str})
df_info_plp.set_index('id_station', inplace = True)

ls_ctd = [x for x in df_info_plp.index if x in df_info.index]
# todo: take into account known duplicates
# todo: see chges in brands
