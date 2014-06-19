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

# BUILD PERIOD DF

for per in range(7,8):
  print 'Period', per
  json_file = ls_json_files[per]
  ls_rows = dec_json(os.path.join(path_dir_source_json, json_file))
  ls_rows = [row + get_split_chain_city(row[3], ls_chain_brands) for row in ls_rows]
  ls_rows =  [row + get_split_brand_product(row[2], ls_brand_patches) for row in ls_rows]
  ls_rows = [[per] + row[:5] + row[6:9] for row in ls_rows]
  ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin',
                'Prix', 'Enseigne', 'Ville', 'Marque']
  df_prices = pd.DataFrame(ls_rows, columns = ls_columns)
  
  # DROP STORES WITH TOO FEW PRODUCTS
  ls_stores = df_prices['Magasin'].unique()
  set_keep_stores = set(ls_stores)
  for rayon in [u'Boissons', u'Epicerie salée', u'Epicerie sucrée', u'Produits frais']:
    set_keep_stores.intersection_update(\
      set(df_prices['Magasin'][df_prices['Rayon'] == rayon].unique()))
  for store in ls_stores:
    if store not in set_keep_stores:
      df_prices = df_prices[df_prices['Magasin'] != store]
  print 'df_prices filetered: check'
  
  # OLS - SPARCE
  pd_as_dicts = [dict(r.iteritems()) for _, r in df_prices[['Magasin', 'Produit']].iterrows()]
  sparse_mat_magasin_produit = DictVectorizer(sparse=True).fit_transform(pd_as_dicts)
  res_01 = scipy.sparse.linalg.lsqr(sparse_mat_magasin_produit,
                                    df_prices['Prix'].values,
                                    iter_lim = 100)
  
  df_prices['Magasin_Rayon'] = df_prices['Magasin']+ '_' + df_prices['Rayon']
  df_prices.sort(['Magasin_Rayon', 'Produit'], inplace = True)
  pd_as_dicts = [dict(r.iteritems()) for _, r in df_prices[['Magasin_Rayon', 'Produit']].iterrows()]
  sparse_mat_magasinr_produit = DictVectorizer(sparse=True).fit_transform(pd_as_dicts)
  res_02 = scipy.sparse.linalg.lsqr(sparse_mat_magasinr_produit,
                                    df_prices['Prix'].values,
                                    iter_lim = 100)
  
  nb_stores = len(df_prices['Magasin'].unique())
  nb_stores_rayons = len(df_prices['Magasin_Rayon'].unique())
  nb_products = len(df_prices['Produit'].unique())
  
  # build df with fixed effects
  ls_magasin_rayon = list(df_prices['Magasin_Rayon'].unique())
  ls_magasin_rayon.sort() # should be sorted already though
  ls_produit = list(df_prices['Produit'].unique())
  ls_produit.sort() # need to sort absolutely!
  ls_rows = zip(ls_magasin_rayon + ls_produit, res_02[0])
  df_res_02 = pd.DataFrame(ls_rows, columns = ['Name', 'Coeff'])
  
  # todo: automate
  df_boissons_fe = df_res_02[df_res_02['Name'].str.contains(u'Boissons')]
  df_boissons_fe = df_boissons_fe.sort('Coeff')
  df_boissons_fe['Name'] = df_boissons_fe['Name'].apply(lambda x: x.split('_')[0])
  
  df_episa_fe = df_res_02[df_res_02['Name'].str.contains(u'Epicerie salée')]
  df_episa_fe = df_episa_fe.sort('Coeff') # creates a new df
  df_episa_fe['Name'] = df_episa_fe['Name'].apply(lambda x: x.split('_')[0])
  
  df_episu_fe = df_res_02[df_res_02['Name'].str.contains(u'Epicerie sucrée')]
  df_episu_fe = df_episu_fe.sort('Coeff')
  df_episu_fe['Name'] = df_episu_fe['Name'].apply(lambda x: x.split('_')[0])
  
  df_profrais_fe = df_res_02[df_res_02['Name'].str.contains(u'Produits frais')]
  df_profrais_fe = df_profrais_fe.sort('Coeff')
  df_profrais_fe['Name'] = df_profrais_fe['Name'].apply(lambda x: x.split('_')[0])
  
  quartile_nb = int(len(df_episa_fe)/4.0)
  ls_se_quartiles = []
  for df_temp in [df_boissons_fe, df_episa_fe, df_episu_fe, df_profrais_fe]:
    df_temp = df_temp.reset_index(drop=True) # need df sorted and numbered
    df_temp['Quartile'] = 4
    df_temp['Quartile'][(df_temp.index <= quartile_nb)] = 1
    df_temp['Quartile'][(df_temp.index > quartile_nb) &\
                               (df_temp.index <= 2*quartile_nb)] = 2
    df_temp['Quartile'][(df_temp.index > 2*quartile_nb) &\
                               (df_temp.index <= 3*quartile_nb)] = 3
    df_temp.set_index('Name', inplace = True)
    ls_se_quartiles.append(df_temp['Quartile'])
  
  df_quartiles = pd.concat(ls_se_quartiles,axis=1, keys=['boisson', 'episa', 'episu', 'profrais'])
  df_quartiles['all'] = df_quartiles['boisson'].map(str) + df_quartiles['episa'].map(str) +\
                          df_quartiles['episu'].map(str) + df_quartiles['profrais'].map(str)
  
  print '\nData for quantile positions table'
  nb_quartile_stores = float(len(df_quartiles))
  print 'Nb of stores in period', nb_quartile_stores
  for poss in ['1111', '2222', '3333', '4444']:
    nb_temp = len(df_quartiles[df_quartiles['all'] == poss])
    print poss, ': {:2.0f}% ({:4d})'.format(100 * nb_temp / nb_quartile_stores, nb_temp)
  for i in range(1,5):
    for j in range(i+1,5):
      nb_temp = len(df_quartiles[(df_quartiles['all'].str.contains('%s'%i)) &\
                               (df_quartiles['all'].str.contains('%s'%j))])
      print i, j, ': {:2.0f}% ({:4d})'.format(100 * nb_temp / nb_quartile_stores, nb_temp)
  
  df_quartiles['sum'] = df_quartiles[['boisson', 'episa', 'episu', 'profrais']].sum(1)
  df_quartiles.sort('sum', inplace= True)
# print df_quartiles.to_string()

# add: build measure of price dispersion at store level
# expected price vs. price set

## CHECK SPARSE VS. STANDARD OLS
#df_test = df_prices[(df_prices['Magasin'] == 'AUCHAN AUBIERE')]
#pd_as_dicts = [dict(r.iteritems()) for _, r in df_test[['Magasin_Rayon']].iterrows()]
#sparse_mat_magasin_produit = DictVectorizer(sparse=True).fit_transform(pd_as_dicts)
#res_00 = scipy.sparse.linalg.lsqr(sparse_mat_magasin_produit, df_test['Prix'].values,
#                                  iter_lim = 100,
#                                  calc_var = True)
## compute standard errors (need degrees of freedom + be caution with res_00[3])
#ar_std_errors = np.sqrt(res_00[3]**2/1799 * res_00[9])
#print res_00[0]
#print np.around(ar_std_errors, 3)
#print smf.ols('Prix ~ 0 + Magasin_Rayon', data = df_test).fit().summary()
## consistency is ok
#
## check how to replicate intercept with sparse, not ok for now
#df_test['Intercept'] = 'Intercept'
#pd_as_dicts = [dict(r.iteritems()) for _, r in df_test[['Intercept', 'Magasin_Rayon']].iterrows()]
#sparse_mat_magasin_produit = DictVectorizer(sparse=True).fit_transform(pd_as_dicts)
#res_0b = scipy.sparse.linalg.lsqr(sparse_mat_magasin_produit,
#                                  df_test['Prix'].values,
#                                  iter_lim = 100,
#                                  calc_var = True)
#ar_std_errors_b = np.sqrt(res_0b[3]**2/1799 * res_0b[9])
#print res_0b[0]
#print np.around(ar_std_errors_b, 3)
#print smf.ols('Prix ~ Magasin_Rayon', data = df_test).fit().summary()
