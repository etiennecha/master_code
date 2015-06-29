#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_dir_qlmc = os.path.join(path_data,
                             'data_qlmc')

path_dir_source_json = os.path.join(path_dir_qlmc,
                                    'data_source',
                                    'data_json_qlmc')

path_dir_built_json = os.path.join(path_dir_qlmc,
                                   'data_built',
                                   'data_json')

path_dir_built_csv = os.path.join(path_dir_qlmc,
                                  'data_built',
                                  'data_csv')

ls_json_files = [u'200705_releves_QLMC',
                 u'200708_releves_QLMC',
                 u'200801_releves_QLMC',
                 u'200804_releves_QLMC',
                 u'200903_releves_QLMC',
                 u'200909_releves_QLMC',
                 u'201003_releves_QLMC',
                 u'201010_releves_QLMC', 
                 u'201101_releves_QLMC',
                 u'201104_releves_QLMC',
                 u'201110_releves_QLMC', # "No brand" starts to be massive
                 u'201201_releves_QLMC',
                 u'201206_releves_QLMC']

print u'\nBuild df_qlmc:'
ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin', 'Prix', 'Date']
ls_rows = [[i] + record for i, ls_records in enumerate(ls_ls_records)\
             for record in ls_records]
df_qlmc = pd.DataFrame(ls_rows, columns = ls_columns)

df_qlmc.to_csv(os.path.join(path_dir_built_csv,
                            

## #############
## EXTRACT MAIN
## #############
#
#print u'Reading json qlmc price records:'
#ls_ls_records = []
#for json_file in ls_json_files:
#  print json_file
#  ls_records = dec_json(os.path.join(path_dir_source_json, json_file))
#  ls_ls_records.append(ls_records)
#
## ###############
## EXTRACT STORES
## ###############
#
## Will merge on periods/stores
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
## #####################
## EXTRACT PRODUCT NAMES
## #####################
#
## Will merge on product name
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
