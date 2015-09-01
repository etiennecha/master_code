#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime

# DATA SOURCES
# ------------
# - my scraped data: include all stations (at the time) and brands
# - plp scraped data: include all stations (at the time) and brands but weekly
# - open data: prices backward (not if station discontinued) and no brands
# Also open data have not been really fixed (id reconciliations + errors in prices)

# OUTPUT DESIRED
# --------------
# Dynamic (index date, cols id_station): price dataframe, brand dataframe (not sure?)
# Static: station brand info with dates of changes
# Static: station location info (name, address, gps... c_insee...)
# Dyna low frequency (?): services, opening hours...

# METHOD
# ------
# - concat open data before + my scraped data when available (id reconciliations?)
# - add missing stations from plp (fill prices using dates?)
# - brand info from plp

# ###########
# LOAD DATA
# ###########

path_dir_built_csv = os.path.join(path_data,
                                  'data_gasoline',
                                  'data_built',
                                  'data_paper_total_access',
                                  'data_csv')

path_dir_source = os.path.join(path_data,
                               'data_gasoline',
                               'data_source')

path_dir_plp_csv = os.path.join(path_dir_source,
                                'data_plp')

path_dir_open_csv = os.path.join(path_dir_source,
                                 'data_opendata',
                                 'csv_files')

# Load open data files
df_open_info = pd.read_csv(os.path.join(path_dir_open_csv,
                                        'df_info_all.csv'),
                             encoding = 'utf-8',
                           dtype = {'id_station' : str})

df_open_prices = pd.read_csv(os.path.join(path_dir_open_csv,
                                          'df_prices_all.csv'),
                             encoding = 'utf-8')

# Load plp files
df_plp_info = pd.read_csv(os.path.join(path_dir_plp_csv,
                                       'df_plp_info.csv'),
                          encoding = 'utf-8',
                          dtype = {'id_station' : str})
df_plp_prices = pd.read_csv(os.path.join(path_dir_plp_csv,
                                         'df_plp_diesel.csv'),
                            encoding = 'utf-8')

# Load my scraped data files
df_my_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_station_info_final.csv'),
                          encoding = 'utf-8',
                          dtype = {'id_station' : str})
df_my_prices = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_prices_ttc_final.csv'),
                             encoding = 'utf-8')

# ###########
# MERGE DATA
# ###########

df_all_diesel = pd.concat([df_open_prices.ix[:'2011-09-04'],
                           df_my_prices.ix['2011-09-04':]],
                          axis = 0)
