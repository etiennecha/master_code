#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_dir_qlmc = os.path.join(path_data,
                             'data_supermarkets',
                             'data_qlmc_2007-12')

path_dir_source_json = os.path.join(path_dir_qlmc,
                                    'data_source',
                                    'data_json')

path_dir_built_json = os.path.join(path_dir_qlmc,
                                   'data_built',
                                   'data_json')

path_dir_built_csv = os.path.join(path_dir_qlmc,
                                  'data_built',
                                  'data_csv')

ls_json_files = [u'200705_releves_QLMC.json',
                 u'200708_releves_QLMC.json',
                 u'200801_releves_QLMC.json',
                 u'200804_releves_QLMC.json',
                 u'200903_releves_QLMC.json',
                 u'200909_releves_QLMC.json',
                 u'201003_releves_QLMC.json',
                 u'201010_releves_QLMC.json', 
                 u'201101_releves_QLMC.json',
                 u'201104_releves_QLMC.json',
                 u'201110_releves_QLMC.json', # "No brand" starts to be massive
                 u'201201_releves_QLMC.json',
                 u'201206_releves_QLMC.json']

print u'Reading json qlmc price records:'
ls_ls_records = []
for json_file in ls_json_files:
  print json_file
  ls_records = dec_json(os.path.join(path_dir_source_json, json_file))
  ls_ls_records.append(ls_records)

print u'\nBuild df_qlmc'
ls_columns = ['Period', 'Department', 'Family', 'Product', 'Store', 'Price', 'Date']
ls_rows = [[i] + record for i, ls_records in enumerate(ls_ls_records)\
             for record in ls_records]
df_qlmc = pd.DataFrame(ls_rows, columns = ls_columns)

print u'\nOutput df_raw_qlmc'
df_qlmc.to_csv(os.path.join(path_dir_built_csv,
                            'df_raw_qlmc.csv'),
               encoding = 'utf-8',
               float_format='%.3f',
               index = False)

df_stores = df_qlmc[['Period', 'Store']].drop_duplicates()
print u'\nOutput df_raw_stores'
df_stores.to_csv(os.path.join(path_dir_built_csv,
                              'df_raw_stores.csv'),
                 encoding = 'utf-8',
                 index = False)

# Only product name, designed to fix spelling
df_products = df_qlmc[['Product']].drop_duplicates()
print u'\nOutput df_raw_products'
df_products.to_csv(os.path.join(path_dir_built_csv,
                                'df_raw_products.csv'),
                   encoding = 'utf-8',
                   index = False)

# ##########
# DEPRECATED
# ##########
#
## EXTRACT STORES (JSON)
#
#print u'\nExtract stores:'
#ls_ls_stores = []
#for ls_records in ls_ls_records:
#  ls_stores = list(set([record[3] for record in ls_records]))
#  ls_ls_stores.append(ls_stores)
#
##enc_json(ls_ls_stores,
##         os.path.join(path_dir_built_json,
##                      'ls_ls_stores'))
#
#
## EXTRACT PRODUCT NAMES (JSON)
#
#print u'\nExtract product names:'
#ls_ls_products = []
#for ls_records in ls_ls_records:
#  set_products = set()
#  for record in ls_records:
#    set_products.add(tuple(record[0:3]))
#  ls_ls_products.append([list(x) for x in list(set_products)])
#
##enc_json(ls_ls_products,
##         os.path.join(path_dir_built_json,
##                      'ls_ls_products.json'))
