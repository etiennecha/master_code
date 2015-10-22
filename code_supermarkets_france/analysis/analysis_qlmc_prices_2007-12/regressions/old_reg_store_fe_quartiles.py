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
import scipy
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.feature_extraction import DictVectorizer

path_built = os.path.join(path_data,
                         'data_supermarkets',
                         'data_built',
                         'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

pd.set_option('float_format', '{:,.3f}'.format)

# LOAD DF QLMC

print u'Loading df_qlmc'
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      dtype = {'id_lsa' : str,
                               'INSEE_ZIP' : str,
                               'INSEE_Code' : str},
                      encoding = 'utf-8')

# RESTRICT TO ONE PERIOD

for per in range(7,8):
  print 'Period', per
  df_qlmc_per = df_qlmc[df_qlmc['Period'] == per]
  
  # #########################
  # FILTER STORES: ENOUGH OBS
  # #########################

  ls_stores = df_qlmc_per['Store'].unique()
  set_keep_stores = set(ls_stores)
  # Want stores which have at least 10 products in each 4 Families below
  df_store_families = df_qlmc_per[['Store', 'Family']].pivot_table(index = 'Store',
                                                                   columns = 'Family',
                                                                   aggfunc=len,
                                                                   fill_value=0)
  ls_required_Families = [u'Boissons',
                          u'Epicerie salée',
                          u'Epicerie sucrée',
                          u'Produits frais']
  for Family in ls_required_Families:
    df_store_families = df_store_families[df_store_families[Family] >= 10]
  ls_keep_stores = list(df_store_families.index.unique())
  print u'Nb stores kept:', len(ls_keep_stores)
  df_qlmc_per = df_qlmc_per[df_qlmc_per['Store'].isin(ls_keep_stores)]
  
  # OLS WITH STORE AND PRODUCT FE
  pd_as_dicts = [dict(r.iteritems())\
                   for _, r in df_qlmc_per[['Store', 'Product']].iterrows()]
  pd_as_dicts_2 = [dict_temp if dict_temp['Product'] != u"3D'S - Bacon extrud\xe9s - 85g"\
                   else {'Store': dict_temp['Store']} for dict_temp in pd_as_dicts]
  sparse_mat_magasin_produit = DictVectorizer(sparse=True).fit_transform(pd_as_dicts_2)
  res_01 = scipy.sparse.linalg.lsqr(sparse_mat_magasin_produit,
                                    df_qlmc_per['Price'].values,
                                    iter_lim = 100,
                                    calc_var = True)
  nb_fd_01 = len(df_qlmc_per) - len(res_01[0])
  ar_std_01 = np.sqrt(res_01[3]**2/nb_fd_01 * res_01[9])
  ls_stores = sorted(df_qlmc_per['Store'].copy().drop_duplicates().values)
  ls_products = sorted(df_qlmc_per['Product'].copy().drop_duplicates().values)[1:]
  # Caution: so happens that products are returned before stores (dict keys..?)
  ls_rows_01 = zip(ls_products + ls_stores, res_01[0], ar_std_01)
  df_res_01 = pd.DataFrame(ls_rows_01, columns = ['Name', 'Coeff', 'Std'])
  df_res_01['t_stat'] = df_res_01['Coeff'] / df_res_01['Std']
  df_stores_fe = df_res_01[len(ls_products):].copy()

  # OLS WITH STORE FAMILY AND PRODUCT FE
  df_qlmc_per['Store_Family'] = df_qlmc_per['Store']+ '_' + df_qlmc_per['Family']
  df_qlmc_per.sort(['Store_Family', 'Product'], inplace = True)
  pd_as_dicts = [dict(r.iteritems())\
                   for _, r in df_qlmc_per[['Store_Family', 'Product']].iterrows()]
  pd_as_dicts_2 = [dict_temp if dict_temp['Product'] != u"3D'S - Bacon extrud\xe9s - 85g"\
                   else {'Store_Family': dict_temp['Store_Family']} for dict_temp in pd_as_dicts]
  sparse_mat_magasinr_produit = DictVectorizer(sparse=True).fit_transform(pd_as_dicts_2)
  res_02 = scipy.sparse.linalg.lsqr(sparse_mat_magasinr_produit,
                                    df_qlmc_per['Price'].values,
                                    iter_lim = 100,
                                    calc_var = True)
  nb_fd_02 = len(df_qlmc_per) - len(res_02[0])
  ar_std_02 = np.sqrt(res_02[3]**2/nb_fd_02 * res_02[9])
  ls_products = sorted(df_qlmc_per['Product'].copy().drop_duplicates().values)[1:]
  ls_store_families = sorted(df_qlmc_per['Store_Family'].copy().drop_duplicates().values)
  # Caution: seems product FE returned before store_rayon...
  ls_rows = zip(ls_products + ls_store_families, res_02[0])
  df_res_02 = pd.DataFrame(ls_rows, columns = ['Name', 'Coeff'])
 
  df_sf_fe = df_res_02[len(ls_products):].copy()
  # assumes no '_' in store name and product categories
  df_sf_fe['Store'] = df_sf_fe['Name'].apply(lambda x: x.split('_')[0])
  df_sf_fe['Family'] = df_sf_fe['Name'].apply(lambda x: x.split('_')[-1])
  ls_keep_Families = [u'Boissons',
                      u'Epicerie salée',
                      u'Epicerie sucrée',
                      u'Produits frais']
  df_sf_fe = df_sf_fe[df_sf_fe['Family'].isin(ls_keep_Families)
  df_sf_su = df_sf_fe[['Store', 'Family', 'Coff'
  
  df_sf_su = pd.pivot_table(df_sf_fe,
                            index = 'Store',
                            columns = 'Family',
                            values = 'Coeff')
  
  # Add chain + surf etc? (could be from LSA)
  df_stores_per = df_qlmc[['Store', 'Store_Chain']].drop_duplicates()
  df_stores_per.set_index('Store', inplace = True)
  df_sf_su_2 = pd.merge(df_sf_su,
                        df_stores_per,
                        left_index = True,
                        right_index = True,
                        how = 'left')
  df_sf_su_2.set_index('Store_Chain', append = True, inplace = True)
  # Store_Chain: poor quality: need to add LSA
  
  # OLD QUARTILE CREATION: todo: update

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
    df_temp.loc[(df_temp.index <= quartile_nb),
                'Quartile'] = 1
    df_temp.loc[(df_temp.index > quartile_nb) &\
                (df_temp.index <= 2*quartile_nb),
                'Quartile'] = 2
    df_temp.loc[(df_temp.index > 2*quartile_nb) &\
                (df_temp.index <= 3*quartile_nb),
                'Quartile'] = 3
    df_temp.set_index('Name', inplace = True)
    ls_se_quartiles.append(df_temp['Quartile'])
  
  df_quartiles = pd.concat(ls_se_quartiles,axis=1,
                           keys=['boisson', 'episa', 'episu', 'profrais'])
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

# ########################
# CHECK SPARSE VS. SMF OLS
# ########################

print u'\nCompare results from sparse reg. vs. statsmodels ols:'

# NO INTERCEPT: Consistent results
df_test = df_qlmc_per[(df_qlmc_per['Store'] == df_qlmc_per['Store'].iloc[0])].copy()
pd_as_dicts = [dict(r.iteritems()) for _, r in df_test[['Store_Family']].iterrows()]
sparse_mat_magasin_produit = DictVectorizer(sparse=True).fit_transform(pd_as_dicts)
res_00 = scipy.sparse.linalg.lsqr(sparse_mat_magasin_produit,
                                  df_test['Price'].values,
                                  iter_lim = 100,
                                  calc_var = True)
# Compute standard errors (need degrees of freedom + be caution with res_00[3])
nb_freedom_degrees = len(df_test) - len(res_00[0])
ar_std_errors = np.sqrt(res_00[3]**2/nb_freedom_degrees * res_00[9])
print u'No intercept:'
print u'Coeffs:', np.around(res_00[0], 3)
print u'Std:', np.around(ar_std_errors, 3)
print smf.ols('Price ~ 0 + Store_Family', data = df_test).fit().summary()

# WITH INTERCEPT: Consistent results once ref category eliminated
df_test['Intercept'] = 'Intercept'
pd_as_dicts = [dict(r.iteritems())\
                 for _, r in df_test[['Intercept', 'Store_Family']].iterrows()]
# get rid of reference category
pd_as_dicts_2 = [dict_temp if dict_temp['Store_Family'] != 'AUCHAN AUBAGNE_Boissons'\
                   else {'Intercept': 'Intercept'} for dict_temp in pd_as_dicts ]
sparse_mat_magasin_produit = DictVectorizer(sparse=True).fit_transform(pd_as_dicts_2)
res_0b = scipy.sparse.linalg.lsqr(sparse_mat_magasin_produit,
                                  df_test['Price'].values,
                                  iter_lim = 100,
                                  calc_var = True)
nb_freedom_degrees = len(df_test) - len(res_00[0])
ar_std_errors_b = np.sqrt(res_0b[3]**2/nb_freedom_degrees * res_0b[9])
print u'\nWith intercept:'
print u'Coeffs:', np.around(res_0b[0], 3)
print u'Std:', np.around(ar_std_errors_b, 3)
print smf.ols('Price ~ Store_Family', data = df_test).fit().summary()

# todo: check with two FEs (two ref categories?)
