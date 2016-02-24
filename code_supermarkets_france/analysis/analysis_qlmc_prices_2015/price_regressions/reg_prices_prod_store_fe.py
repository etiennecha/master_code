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

# Add store chars / environement
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        encoding = 'utf-8')

# ###############################
# RESTRICTIONS ON PRODUCTS/STORES
# ###############################

# keep only if products observed w/in at least 1000 stores
df_prices['nb_prod_obs'] =\
  df_prices.groupby('product')['product'].transform(len).astype(int)
df_prices = df_prices[df_prices['nb_prod_obs'] >= 1000]

# keep only stores w/ at least 400 products
df_prices['nb_store_obs'] =\
 df_prices.groupby('store_id')['store_id'].transform(len).astype(int)
df_prices = df_prices[df_prices['nb_store_obs'] >= 400]

# count product obs again
df_prices['nb_prod_obs'] =\
  df_prices.groupby('product')['product'].transform(len).astype(int)

print df_prices[['nb_prod_obs', 'nb_store_obs']].describe()

# ##############
# REGRESSION
# ##############

ref_var = 'store_id' # store_id

df_prices['ln_price'] = np.log(df_prices['price'])

pd_as_dicts = [dict(r.iteritems())\
                 for _, r in df_prices[['store_id', 'product']].iterrows()]
#pd_as_dicts_2 = [dict(dict_temp.items() + [('intercept', 'intercept')])\
#                   for dict_temp in pd_as_dicts]

if ref_var == 'store_id':
  ref = u'centre-e-leclerc-les-angles' # pd_as_dicts[0]['store_id']
  pd_as_dicts_2 = [dict_temp if dict_temp['store_id'] != ref \
                   else {'product': dict_temp['product']} for dict_temp in pd_as_dicts]
else:
  ref = pd_as_dicts[0]['product']
  pd_as_dicts_2 = [dict_temp if dict_temp['product'] != ref \
                   else {'store_id': dict_temp['store_id']} for dict_temp in pd_as_dicts]

price_col = 'price'
sparse_mat_prod_store = DictVectorizer(sparse=True).fit_transform(pd_as_dicts_2)
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

if ref_var == 'store_id':
  ls_stores.remove(ref)
else:
  ls_products.remove(ref)

# Caution: so happens that products are returned before stores (dict keys..?)
ls_rows_01 = zip(ls_products + ls_stores, res_01[0], ar_std_01)
df_res_01 = pd.DataFrame(ls_rows_01, columns = ['Name', 'Coeff', 'Std'])
df_res_01['t_stat'] = df_res_01['Coeff'] / df_res_01['Std']
df_stores_fe = df_res_01[len(ls_products):].copy()

# This reg:
# - No intercept (could add one by modif matrix?)
# - Ref is pd_as_dicts[0]['product']
# - Store FEs are centered around this ref price

# Check 
# Ok if using 'product' as ref and price (not log))
print u'\nMean price of reference product:',\
      df_prices[df_prices['product'] == pd_as_dicts[0]['product']]['price'].mean()

print u'\nCoeffs for 5 first products:'
print df_res_01.iloc[0:5].to_string()

print u'\nMean prices for 5 first products'
print df_prices[df_prices['product'].isin(df_res_01['Name'][0:5].values)]\
        [['product', 'price']].groupby('product').mean()

# ##################
# ANALYSE STORE FEs
# ##################

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
df_chains_su = df_stores.groupby('store_chain')['Coeff']\
                        .agg('describe').reset_index()\
                        .pivot(index='store_chain',
                               values=0,
                               columns='level_1')
df_chains_su = df_chains_su[df_chains_su['count'] >= 10]
lsddesc = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
print df_chains_su[lsddesc].to_string()

# todo: log analysis? no need to center?
