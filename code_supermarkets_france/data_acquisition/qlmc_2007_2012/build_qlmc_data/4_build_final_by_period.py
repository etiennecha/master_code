#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_source = os.path.join(path_data,
                           'data_supermarkets',
                           'data_source',
                           'data_qlmc_2007-12')

path_source_csv = os.path.join(path_source,
                               'data_csv')

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_built_csv_by_period = os.path.join(path_built,
                                        'data_csv_by_period')

# ######
# OUTPUT
# ######

df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                       encoding='utf-8')

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                         encoding='utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores.csv'),
                         encoding='utf-8')

for Period in df_stores['period'].unique():
  df_qlmc_per = df_qlmc[df_qlmc['period'] == Period]
  df_prices_per = df_prices[df_prices['period'] == Period]
  df_stores_per = df_stores[df_stores['period'] == Period]

  df_qlmc_per.to_csv(os.path.join(path_built_csv_by_period,
                                  'df_qlmc_{:d}.csv'.format(Period)),
                     float_format = '%.2f',
                     encoding = 'utf-8',
                     index = False)

  df_prices_per.to_csv(os.path.join(path_built_csv_by_period,
                                    'df_prices_{:d}.csv'.format(Period)),
                        float_format = '%.2f',
                        encoding = 'utf-8',
                        index = False)

  df_stores_per.to_csv(os.path.join(path_built_csv_by_period,
                                    'df_stores_{:d}.csv'.format(Period)),
                        float_format='%.2f',
                        encoding='utf-8',
                        index=False)
