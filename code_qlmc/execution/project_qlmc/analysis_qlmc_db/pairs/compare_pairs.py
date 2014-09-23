#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path_sub
from add_to_path_sub import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')

path_dir_source_json = os.path.join(path_dir_qlmc, 'data_source', 'data_json_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

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

# master_all_periods = dec_json(os.path.join(path_dir_built_json, 'master_all_periods'))

# Find stores in same location (all based on indexes... fragile for now)
ls_ls_store_insee = dec_json(os.path.join(path_dir_built_json, 'ls_ls_store_insee'))
ls_ls_pairs = []
for ls_store_insee in ls_ls_store_insee:
  ls_pairs = []
  for j, store in enumerate(ls_store_insee):
    for k, store_2 in enumerate(ls_store_insee[j+1:], start = j+1):
      if store and store_2 and store[0] == store_2[0]:
        ls_pairs.append((j,k))
  ls_ls_pairs.append(ls_pairs)

ls_ls_comparisons = []
for per in range(0,10):
  json_file = ls_json_files[per]
  ls_rows = dec_json(os.path.join(path_dir_source_json, json_file))
  ls_rows = [row + get_split_chain_city(row[3], ls_chain_brands) for row in ls_rows]
  ls_rows =  [row + get_split_brand_product(row[2], ls_brand_patches) for row in ls_rows]
  ls_rows = [[per] + row[:5] + row[6:9] for row in ls_rows]
  ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin',
                'Prix', 'Enseigne', 'Ville', 'Marque']
  df_prices = pd.DataFrame(ls_rows, columns = ls_columns)
  
  # ls_ls_tuple_stores = dec_json(os.path.join(path_dir_built_json, 'ls_ls_tuple_stores'))
  ## fragile for now...
  ls_pairs = ls_ls_pairs[per]
  ls_stores = list(set(df_prices['Magasin'].unique()))
  
  ## Inspect pairs (since so fragile for now...)
  #for (j,k) in ls_pairs:
  #  print ls_stores[j], ls_stores[k]
  #store_a, store_b = ls_stores[j], ls_stores[k]
  #test = compare_stores(store_a, store_b, df_prices, per, u'Rayon')
  
  ls_ls_store_fe = dec_json(os.path.join(path_dir_built_json, 'ls_ls_store_fe')) 
  ls_store_fe = ls_ls_store_fe[per]
  dict_store_fe = {k:v for k,v in ls_store_fe}
  
  pd.options.display.float_format = '{:,.2f}'.format
  ls_comparisons = []
  for (j,k) in ls_pairs:
    store_a, store_b = ls_stores[j], ls_stores[k]
    comparison_result = compare_stores(store_a, store_b, df_prices, per, 'Rayon')
    ls_comparisons.append([store_a,
                           store_b,
                           dict_store_fe[store_a],
                           dict_store_fe[store_b],
                           zip(*comparison_result)])
  ls_ls_comparisons.append(ls_comparisons)

# enc_json(ls_ls_comparisons, os.path.join(path_dir_built_json, 'ls_ls_comparisons'))



#print '\n', store_a, store_b
#ls_columns = ['Category', '#PA<PB', '#PA>PB', '#PA=PB']
#df_comparison = pd.DataFrame(zip(*comparison_result), columns = ls_columns)
#df_comparison['%PA<PB'] = df_comparison['#PA<PB'] /\
#                            df_comparison[['#PA<PB', '#PA>PB', '#PA=PB']].sum(1)
#df_comparison['%PA>PB'] = df_comparison['#PA>PB'] /\
#                            df_comparison[['#PA<PB', '#PA>PB', '#PA=PB']].sum(1)
#df_comparison['%PA=PB'] = df_comparison['#PA=PB'] /\
#                            df_comparison[['#PA<PB', '#PA>PB', '#PA=PB']].sum(1)
#print df_comparison.to_string(index=False)
