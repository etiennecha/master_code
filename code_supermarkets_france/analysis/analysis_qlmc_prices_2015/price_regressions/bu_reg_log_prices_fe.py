#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import timeit
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import scipy
from sklearn.feature_extraction import DictVectorizer

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)

# #############
# LOAD DATA
# #############

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

df_prices['ln_price'] = np.log(df_prices['price'])

# Add store chars / environement
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        encoding = 'utf-8')

# ###############################
# RESTRICTIONS ON PRODUCTS/STORES
# ###############################

## RESTRICTION ON PRODS BY NB OBS AND ON STORES BY NB OBS BY STORE
#
## keep only if products observed w/in at least 1000 stores
#df_prices['nb_prod_obs'] =\
#  df_prices.groupby('product')['product'].transform(len).astype(int)
#df_prices = df_prices[df_prices['nb_prod_obs'] >= 1000]
#
## keep only stores w/ at least 400 products
#df_prices['nb_store_obs'] =\
# df_prices.groupby('store_id')['store_id'].transform(len).astype(int)
#df_prices = df_prices[df_prices['nb_store_obs'] >= 400]
#
## count product obs again
#df_prices['nb_prod_obs'] =\
#  df_prices.groupby('product')['product'].transform(len).astype(int)
#
#print df_prices[['nb_prod_obs', 'nb_store_obs']].describe()

# RESTRICTION: 10 LECLERC AND 10 PRODUCTS

#df_prices = df_prices[df_prices['store_chain'] == 'LECLERC']
df_prices = df_prices[df_prices['store_chain'].isin(['LECLERC', 'AUCHAN'])]

se_nb_store_obs = df_prices.groupby('store_id')['store_id'].agg(len)
se_nb_store_obs.sort(ascending = False, inplace = True)
#df_prices = df_prices[df_prices['product'].isin(list(se_nb_store_obs[0:200].index))]
ls_keep_stores = list(se_nb_store_obs[se_nb_store_obs.index.str.contains('leclerc')][0:10].index) +\
                  list(se_nb_store_obs[se_nb_store_obs.index.str.contains('auchan')][0:10].index) 
df_prices = df_prices[df_prices['store_id'].isin(ls_keep_stores)]

se_nb_prod_obs = df_prices.groupby('product')['product'].agg(len)
se_nb_prod_obs.sort(ascending = False, inplace = True)
df_prices = df_prices[df_prices['product'].isin(list(se_nb_prod_obs[0:10].index))]

# sort on alphabetical order to have same ref group with smf.ols (could fail)
df_prices.sort(['store_id', 'product'], ascending = True, inplace = True)

#df_prices = df_prices[df_prices['store_chain'] == 'LECLERC']

# ##############################
# REGRESSION WITH DICTVECTORIZER
# ##############################

# result consistent with smf.ols
# caution with ref categories
# caution with order of returned coefficients (to match with param names...)

ls_X_dicts = [dict(list(row.iteritems()) + [('intercept', 'intercept')])\
                 for row_ind, row in df_prices[['store_id', 'product']].iterrows()]

# choose ref store and product
# erase store_id and product in observation dict for these (intercept remains)
#ref_store_id = ls_X_dicts[0]['store_id'] # u'centre-e-leclerc-les-angles'
ref_store_id = u'centre-e-leclerc-trie-chateau' # u'centre-e-leclerc-andrezieux-boutheon' 
ref_product = ls_X_dicts[0]['product']
for X_dict in ls_X_dicts:
  if X_dict['store_id'] == ref_store_id:
    X_dict.pop('store_id', None)
  if X_dict['product'] == ref_product:
    X_dict.pop('product', None)

price_col = 'ln_price'
sparse_mat_prod_store = DictVectorizer(sparse=True).fit_transform(ls_X_dicts)
res_01 = scipy.sparse.linalg.lsqr(sparse_mat_prod_store,
                                  df_prices[price_col].values,
                                  iter_lim = 100,
                                  calc_var = True)
nb_fd_01 = len(df_prices) - len(res_01[0])
ar_std_01 = np.sqrt(res_01[3]**2/nb_fd_01 * res_01[9])
ls_stores = sorted(df_prices['store_id'].copy().drop_duplicates().values)
ls_products = sorted(df_prices['product'].copy().drop_duplicates().values)

# Compute rsquare
y_hat = sparse_mat_prod_store * res_01[0]
df_prices['yhat'] = y_hat
df_prices['residual'] = df_prices[price_col] - df_prices['yhat'] 
rsquare = 1 - ((df_prices[price_col] - df_prices['yhat'])**2).sum() /\
                ((df_prices[price_col] - df_prices[price_col].mean())**2).sum()

ls_stores.remove(ref_store_id)
ls_products.remove(ref_product)

# Caution: so happens that products are returned before stores (dict keys..?)
ls_rows_01 = zip(['intercept'] + ls_products + ls_stores, res_01[0], ar_std_01)
df_res_01 = pd.DataFrame(ls_rows_01, columns = ['Name', 'Coeff', 'Std'])
df_res_01['t_stat'] = df_res_01['Coeff'] / df_res_01['Std']
df_stores_fe = df_res_01[len(ls_products) + 1:].copy()


## CHECK
#print u'\nMean price of reference product:',\
#      df_prices[df_prices['product'] == ref_product]['price'].mean()
#
#print u'\nCoeffs for 5 first products:'
#print df_res_01.iloc[0:5].to_string()
#
#print u'\nMean prices for 5 first products'
#print df_prices[df_prices['product'].isin(df_res_01['Name'][0:5].values)]\
#        [['product', 'price']].groupby('product').mean()

# ANALYSE STORE FEs

df_stores.set_index('store_id', inplace = True)
df_stores_fe.set_index('Name', inplace = True)
df_stores = pd.merge(df_stores,
                     df_stores_fe,
                     left_index = True,
                     right_index = True,
                     how = 'left')

## center Coeff data
#df_stores['Coeff'] = df_stores['Coeff'] - df_stores['Coeff'].mean()

# check syntax update in pandas 0.17
try:
  df_chains_su = df_stores.groupby('store_chain')['Coeff']\
                          .agg('describe').reset_index()\
                          .pivot(index='store_chain',
                                 values='Coeff',
                                 columns='level_1')
except:
  df_chains_su = df_stores.groupby('store_chain')['Coeff']\
                          .agg('describe').reset_index()\
                          .pivot(index='store_chain',
                                 values=0,
                                 columns='level_1')
df_chains_su = df_chains_su[df_chains_su['count'] >= 10]
lsddesc = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
#print(df_chains_su[lsddesc].to_string())

pd.set_option('float_format', '{:,.4f}'.format)
print()
print(df_stores_fe[0:20].to_string())

# ##############################
# REGRESSION WITH SMF.OLS
# ##############################

#print()
#print(smf.ols('ln_price ~ C(store_id) + C(product)', data = df_prices).fit().summary())

print(smf.ols("ln_price ~ C(store_id, Treatment('{:s}'))".format(ref_store_id) +\
                       u" + C(product)", data = df_prices).fit().summary())

# ##############################
# REGRESSION WITH to_sparse()
# ##############################

# requires recent enough versions of patsy / statsmodels

df_qlmc = df_prices.copy()

df_0 = df_qlmc[['product']].copy()
df_0['product'] = u'C(product) ' + df_0['product']
df_0.index.name = 'row'
df_0.rename(columns = {'product': 'col'}, inplace = True)

df_1 = df_qlmc[['store_id']].copy()
df_1['store_id'] = u'C(store_id) ' + df_1['store_id']
df_1.index.name = 'row'
df_1.rename(columns = {'store_id': 'col'}, inplace = True)

# create df to convert to sparse (need index: 0 to n obs)
df_i = pd.DataFrame('intercept', columns = ['col'], index = df_qlmc.index)
df_i.index.name = 'row'
df_2 = pd.concat([df_i, df_0, df_1], axis = 0)

# omit one category for each categorical variable (reference)
# a priori can simply drop row if there is an intercept (mat row created)
df_2['val'] = 1

##ref_store_id =  # df_qlmc.iloc[0]['store_id'] # u'centre-e-leclerc-les-angles'
#ref_store_id = 'centre-e-leclerc-trie-chateau' 
#ref_product = df_qlmc.iloc[0]['product']

ref_product = u'FITNESS C\xc9R\xc9ALES FITNESS CHOCOLAT NESTL\xc9 375G'

#ls_refs = [u'C(product) ' + ref_product]
ls_refs = [u'C(store_id) ' + ref_store_id]
#ls_refs = [u'C(product) ' + ref_product,
#           u'C(store_id) ' + ref_store_id]
for ref in ls_refs:
  df_2 = df_2[~(df_2['col'] == ref)]
df_2.set_index('col', append = True, inplace = True)

# build sparse matrix
s = pd.Series(df_2['val'].values)
s.index = df_2.index
ss = s.to_sparse()
A, rows, columns = ss.to_coo(row_levels=['row'],
                             column_levels = ['col'],
                             sort_labels = True)
price_col = 'ln_price'
y = df_qlmc[price_col].values
param_names = columns

res = scipy.sparse.linalg.lsqr(A,
                               y,
                               iter_lim = 200,
                               calc_var = True)
param_values = res[0]
nb_freedom_degrees = len(df_qlmc) - len(res[0])
param_se = np.sqrt(res[3]**2/nb_freedom_degrees * res[9])

df_reg = pd.DataFrame(zip(param_names,
                          param_values,
                          param_se), columns = ['name', 'coeff', 'bse'])
df_reg['tstat'] = df_reg['coeff'] / df_reg['bse']

print()
print(df_reg[df_reg['name'].str.contains(u'C\(store_id\)')][0:60].to_string())

yhat_alt = A * res[0]
df_qlmc['yhat_alt'] = yhat_alt
