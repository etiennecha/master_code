#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import os, sys
import json
import re
import pandas as pd

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built_csv = os.path.join(path_data, 'data_supermarkets', 'data_built',
                              'data_qlmc_2014_2015', 'data_csv')

# #########
# LOAD DATA
# #########

df_prices = pd.read_csv(os.path.join(path_built_csv, 'df_prices_201503.csv'),
                        encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv, 'df_stores_final_201503.csv'),
                        encoding = 'utf-8')

df_qlmc = pd.merge(df_prices,
                   df_stores[['store_id', 'store_name']],
                   on = ['store_id'],
                   how = 'left')

# OUTPUT TO 2014-2015 FOLDER

df_qlmc.to_csv(os.path.join(path_built_csv, 'df_qlmc_201503.csv'),
               encoding = 'utf-8',
               float_format='%.3f',
               index = False)
