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
import scipy
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.feature_extraction import DictVectorizer

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

ls_ls_store_fe = []
for per in range(len(ls_json_files)):
  json_file = ls_json_files[per]
  ls_rows = dec_json(os.path.join(path_dir_source_json, json_file))
  ls_rows = [row + get_split_chain_city(row[3], ls_chain_brands) for row in ls_rows]
  ls_rows =  [row + get_split_brand_product(row[2], ls_brand_patches) for row in ls_rows]
  ls_rows = [[per] + row[:5] + row[6:9] for row in ls_rows]
  ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin',
                'Prix', 'Enseigne', 'Ville', 'Marque']
  df_prices = pd.DataFrame(ls_rows, columns = ls_columns)
  
  # OLS - SPARCE
  pd_as_dicts = [dict(r.iteritems()) for _, r in df_prices[['Magasin', 'Produit']].iterrows()]
  sparse_mat_magasin_produit = DictVectorizer(sparse=True).fit_transform(pd_as_dicts)
  res_01 = scipy.sparse.linalg.lsqr(sparse_mat_magasin_produit,
                                    df_prices['Prix'].values,
                                    iter_lim = 100)
  
  nb_stores = len(df_prices['Magasin'].unique())
  nb_products = len(df_prices['Produit'].unique())
  
  # build df with fixed effects
  ls_magasin = list(df_prices['Magasin'].unique())
  ls_magasin.sort() # should be sorted already though
  ls_produit = list(df_prices['Produit'].unique())
  ls_produit.sort() # need to sort absolutely!
  ls_rows = zip(ls_magasin + ls_produit, res_01[0])
  df_res_01 = pd.DataFrame(ls_rows, columns = ['Name', 'Coeff'])
  
  df_magasin = df_res_01[:len(ls_magasin)]
  df_magasin = df_magasin.sort('Coeff')
  
  ls_store_fe = df_magasin.to_records(index=False)
  ls_ls_store_fe.append(ls_store_fe)

ls_ls_store_fe = [list(ls_store_fe) for ls_store_fe in ls_ls_store_fe]
for ls_store_fe in ls_ls_store_fe:
  ls_ls_store_fe_final.append([[x[0], float(x[1])] for x in ls_store_fe])
enc_json(ls_ls_store_fe_final, os.path.join(path_dir_built_json, 'ls_ls_store_fe')) 
