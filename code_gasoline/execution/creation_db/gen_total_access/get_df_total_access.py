#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
import pprint

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                           'df_station_info.csv'),
                              encoding = 'utf-8',
                              dtype = {'id_station' : str,
                                       'adr_zip' : str,
                                       'adr_dpt' : str,
                                       'ci_1' : str,
                                       'ci_ardt_1' :str,
                                       'ci_2' : str,
                                       'ci_ardt_2' : str,
                                       'dpt' : str})

# Active gas stations?

# Total Access in brands... but could no more be (check by concatenating)
df_info['TA'] = 0
df_info['TA'][(df_info['brand_0'] == 'TOTAL_ACCESS') |\
              (df_info['brand_1'] == 'TOTAL_ACCESS') |\
              (df_info['brand_2'] == 'TOTAL_ACCESS')] = 1
print u'Nb Total Access (assume no exit of brand nor dupl.):', df_info['TA'].sum()

# Chge to Total Access recorded
df_info['TA_chge'] = 0
df_info['TA_chge'][(df_info['brand_0'] != 'TOTAL_ACCESS') &\
                   (df_info['brand_1'] == 'TOTAL_ACCESS')] = 1
df_info['TA_chge'][(df_info['brand_1'] != 'TOTAL_ACCESS') &\
                   (df_info['brand_2'] == 'TOTAL_ACCESS')] = 1
print u'Chge to Total Access:', df_info['TA_chge'].sum()

# Total Access within area
print df_info[['dpt', 'TA']].groupby('dpt').agg([sum])['TA'].to_string()

# Need ids of TAs within areas to find dates
