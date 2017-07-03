#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import os, sys
import re
import json
import pandas as pd

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_qlmc_scraped = os.path.join(path_data, 'data_supermarkets', 'data_source',
                                 'data_qlmc_2014_2015', 'data_scraped_201503')

path_built_csv = os.path.join(path_data, 'data_supermarkets', 'data_built',
                              'data_qlmc_2014_2015', 'data_csv')

dict_reg_leclerc = dec_json(os.path.join(path_qlmc_scraped, 'dict_reg_leclerc_stores.json'))
dict_leclerc_comp = dec_json(os.path.join(path_qlmc_scraped, 'dict_leclerc_comp.json'))

# dict_leclerc_comp should contain all stores including leclerc
ls_rows_stores = []
for leclerc_id, ls_stores in dict_leclerc_comp.items():
  for store in ls_stores:
    ls_rows_stores.append([store['slug'],
                           store['city'],
                           store['title'],
                           store['signCode'],
                           store['latitude'],
                           store['longitude']])

df_stores = pd.DataFrame(ls_rows_stores,
                         columns = ['store_id',
                                    'store_municipality',
                                    'store_name',
                                    'store_chain',
                                    'store_lat',
                                    'store_lng'])

## write explicit chain
dict_chains = {'LEC' : 'LECLERC',
               'ITM' : 'INTERMARCHE',
               'USM' : 'SUPER U',
               'CAR' : 'CARREFOUR',
               'CRM' : 'CARREFOUR MARKET', # or MARKET
               'AUC' : 'AUCHAN',
               'GEA' : 'GEANT CASINO',
               'CAS' : 'CASINO',
               'SCA' : 'CASINO',
               'HSM' : 'HYPER U',
               'UHM' : 'HYPER U',
               'COR' : 'CORA',
               'SIM' : 'SIMPLY MARKET',
               'MAT' : 'SUPERMARCHE MATCH',
               'HCA' : 'HYPER CASINO',
               'UEX' : 'U EXPRESS',
               'ATA' : 'ATAC',
               'MIG' : 'MIGROS',
               'G20' : 'G 20',
               'REC' : 'RECORD',
               'HAU' : "LES HALLES D'AUCHAN"}
df_stores['store_chain'] = df_stores['store_chain'].apply(lambda x: dict_chains[x])

# unique stores listed
df_stores.drop_duplicates('store_id', inplace = True)

df_stores.to_csv(os.path.join(path_built_csv, 'df_stores_201503.csv'),
                 encoding = 'utf-8',
                 float_format='%.4f',
                 index = False)
