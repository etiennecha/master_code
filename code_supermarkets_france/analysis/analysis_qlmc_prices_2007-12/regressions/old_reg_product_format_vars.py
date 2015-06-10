#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
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

per = 2
json_file = ls_json_files[per]
ls_rows = dec_json(os.path.join(path_dir_source_json, json_file))
ls_rows = [row + get_split_chain_city(row[3], ls_chain_brands) for row in ls_rows]
ls_rows =  [row + get_split_brand_product(row[2], ls_brand_patches) for row in ls_rows]
ls_rows = [[per] + row[:5] + row[6:9] for row in ls_rows]
ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin',
              'Prix', 'Enseigne', 'Ville', 'Marque']
df_prices = pd.DataFrame(ls_rows, columns = ls_columns)

ls_prod_pairs = [[u'Ricard - Ricard pastis 45°, 50cl',
                  u'Ricard - Ricard pastis 45°, 70cl'],
                 [u'Ricard - Ricard pastis 45°, 70cl',
                  u'Ricard - Ricard pastis 45°, , 1L'],
                 [u'Ricard - Ricard pastis 45°, , 1L',
                  u'Ricard - Ricard pastis 45°, 1,5L'],
                 [u'Coca Cola - Coca Cola avec caféine, 1,5L',
                  u'Coca Cola - Coca Cola avec caféine, 2L'],
                 [u'Panzani - Spagheto Sauce pleine saveur bolognaise, 210g',
                  u'Panzani - Spagheto Sauce pleine saveur bolognaise, 425g'],
                 [u'Panzani - Spagheto Sauce pleine saveur bolognaise, 425g',
                  u'Panzani - Spagheto Sauce pleine saveur bolognaise, 600g']]
                 
for prod_1, prod_2 in ls_prod_pairs[1:2]:
  print '\n', prod_1
  print prod_2
  df_prod_1 = df_prices[['Magasin', 'Prix']][df_prices['Produit'] == prod_1]
  df_prod_2 = df_prices[['Magasin', 'Prix']][df_prices['Produit'] == prod_2]
  df_prod_1.set_index('Magasin', inplace = True)
  df_prod_2.set_index('Magasin', inplace = True)
  df_prod_f = df_prod_1.join(df_prod_2, how = 'inner', lsuffix='_1', rsuffix='_2')
  # outer may allow to see manipulation or small stores with less inventory
  df_prod_f['Diff'] = df_prod_f['Prix_2'] - df_prod_f['Prix_1']
  
  df_prod_f = df_prod_f[df_prod_f['Diff'] < df_prod_f['Diff'].mean() + 1*df_prod_f['Diff'].std()]
  df_prod_f = df_prod_f[df_prod_f['Diff'] > df_prod_f['Diff'].mean() - 1*df_prod_f['Diff'].std()]
  
  plt.scatter(df_prod_f['Prix_1'], df_prod_f['Diff'])
  plt.show()
  
  plt.scatter(df_prod_f['Prix_2'], df_prod_f['Diff'])
  plt.show()
   
  # Diff not so easy to interpret, just focus on that for now:
  ax = plt.subplot()
  ax.scatter(df_prod_f['Prix_1'], df_prod_f['Prix_2'])
  ax.set_xlabel('Prix %s' %prod_1)
  ax.set_ylabel('Prix %s' %prod_2)
  plt.show()

  ## caution: get rid of outliers (how to automate?)
  #df_prod_f = df_prod_f[(df_prod_f['Diff'] < 10) & (df_prod_f['Diff'] > 5)]
  print smf.ols('Diff ~ Prix_1', data = df_prod_f).fit().summary()
  print smf.ols('Diff ~ Prix_2', data = df_prod_f).fit().summary()
