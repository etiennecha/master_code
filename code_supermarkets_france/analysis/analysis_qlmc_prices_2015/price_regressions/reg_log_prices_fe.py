#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
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
from patsy import dmatrix, dmatrices
from scipy.sparse import csr_matrix

pd.set_option('float_format', '{:,.3f}'.format)

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

# Rename chains to have similar chains as on qlmc
ls_replace_chains = [['HYPER U', 'SYSTEME U'],
                     ['U EXPRESS', 'SYSTEME U'],
                     ['SUPER U', 'SYSTEME U'],
                     ['HYPER CASINO', 'CASINO'],
                     ["LES HALLES D'AUCHAN", 'AUCHAN']]
for old_chain, new_chain in ls_replace_chains:
  df_prices.loc[df_prices['store_chain'] == old_chain,
                'store_chain'] = new_chain

# Drop (weird) products and fix problematic names:
# should not start with numeric + quote issues?
ls_drop_products = [u'TOTAL ACTIVA 7000 10W40',
                    u'TOTAL ACTIVA 7000 DIESEL 10W40',
                    u'TOTAL ACTIVA 5000 15W40',
                    u'TOTAL ACTIVA 5000 DIESEL 15W40',
                    u'BLEDINA']
#                    u'"MAPED AGRAFEUSE HALF STRIP ""UNIVERSAL"" METAL 24/6 26/6 + 400 AGRAFES"']
df_prices = df_prices[~df_prices['product'].isin(ls_drop_products)]

# Drop " once and for all
df_prices['product'] = df_prices['product'].str.replace('"', '')

# Add prefix if starts with numeric (reversed after regression)
se_prods = df_prices['product'].drop_duplicates()
ls_rename_prods =\
  [x for i in range(9)\
     for x in se_prods[se_prods.str.startswith('{:d}'.format(i))].tolist()]
for prod in ls_rename_prods:
  df_prices.loc[df_prices['product'] == u'{:s}'.format(prod),
                'product'] = u'STR_{:s}'.format(prod)

df_qlmc = df_prices.copy()

# Avoid error msg on condition number
df_qlmc['ln_price'] = np.log(df_qlmc['price'])

# REFINE DATA

# keep only if products observed w/in at least 100 stores (or more: memory..)
df_qlmc['nb_prod_obs'] =\
  df_qlmc.groupby('product')['product'].transform(len).astype(int)
df_qlmc = df_qlmc[df_qlmc['nb_prod_obs'] >= 50]

# keep only stores w/ at least 100 products
df_qlmc['nb_store_obs'] =\
 df_qlmc.groupby('store_id')['store_id'].transform(len).astype(int)
df_qlmc = df_qlmc[df_qlmc['nb_store_obs'] >= 100]

# count product obs again
df_qlmc['nb_prod_obs'] =\
  df_qlmc.groupby('product')['product'].transform(len).astype(int)

print(df_qlmc[['nb_prod_obs', 'nb_store_obs']].describe())

# ############
# REGRESSIONS
# ############

#df_qlmc = df_qlmc[df_qlmc['store_chain'] == 'LECLERC']

## test get_dummies /w sparse option (requires pandas => 0.16.1)
#df_test = pd.get_dummies(df_qlmc,
#                         columns = ['product', 'qlmc_chain'],
#                         prefix = ['product', 'qlmc_chain'],
#                         sparse = True)

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
ref_prod =  df_qlmc['product'].sort_values().iloc[0]

ref_store = u'centre-e-leclerc-limoges'
#ref_store = u'centre-e-leclerc-amilly' # amboise not bad
#ref_store = u'centre-e-leclerc-lanester'
#ref_store = u'centre-e-leclerc-andrezieux-boutheon' # u'centre-e-leclerc-les-angles'
#ref_store = df_qlmc['store_id'].sort_values().iloc[0]

ls_refs = [u'C(store_id) ' + ref_store]
#ls_refs = [u'C(product) ' + ref_prod,
#           u'C(store_id) ' + ref_store]
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
                               iter_lim = 100,
                               calc_var = True)
param_values = res[0]
nb_freedom_degrees = len(df_qlmc) - len(res[0])
param_se = np.sqrt(res[3]**2/nb_freedom_degrees * res[9])

df_reg = pd.DataFrame(zip(param_names,
                          param_values,
                          param_se), columns = ['name', 'coeff', 'bse'])
df_reg['tstat'] = df_reg['coeff'] / df_reg['bse']

#print u'\nReg result (omitting prod and region FEs):'
#print df_reg[(~df_reg['name'].str.contains(u'C\(product\)')) &\
#             (~df_reg['name'].str.contains(u'C\(region\)'))].to_string()

# compute rsquare
y_hat = A * res[0]
rsquare = 1 - ((y - y_hat)**2).sum() /\
                ((y - y.mean())**2).sum()

# goodness of fit (to compare with log)
if price_col == 'ln_price':
  df_qlmc['ln_price_hat'] = y_hat
  df_qlmc['price_hat'] = np.exp(y_hat)
else:
  df_qlmc['price_hat'] = y_hat
#print('SS of residuals for price:',
#      ((df_qlmc['price'] - df_qlmc['price_hat'])**2).sum())

# Check leclerc
df_lec = df_reg[df_reg['name'].str.contains(u'C\(store_id\) centre-e-leclerc')].copy()
df_lec.sort(['coeff'], ascending = True, inplace = True)
print(df_lec[0:150].to_string())

df_lec['price_ind'] = (df_lec['coeff'] + 1) * 100
print(df_lec[~df_lec['coeff'].isnull()]['coeff'].describe())

## ######
## OUTPUT
## ######
#
## Prices
#df_qlmc.to_csv(os.path.join(path_built_csv,
#                            'df_res_{:s}s.csv'.format(price_col)),
#               encoding = 'utf-8',
#               float_format='%.3f',
#               index = False)
#
## Fixed effects
#df_reg.to_csv(os.path.join(path_built_csv,
#                           'df_res_{:s}_fes.csv'.format(price_col)),
#              encoding = 'utf-8',
#              float_format='%.3f',
#              index = False)


## ###############
## BU PATSY SYNTAX
## ###############
#
## check pop variable... 0 for Leclerc in Porto Vecchio
## todo: check w/ clustered std errors on stores?
#
#str_exo = "C(qlmc_chain) + C(product)"
#X = dmatrix(str_exo, data = df_qlmc, return_type = "matrix")
#y = df_qlmc['price'].values
#
##str_exo = "price ~ C(qlmc_chain) + C(product)"
###str_exo = "price ~ C(qlmc_chain) + surface + C(region) + C(product) + ac_hhi + ac_nb_stores"
##y, X = dmatrices(str_exo,
##                 data = df_qlmc,
##                 return_type = "matrix")
#param_names = X.design_info.column_names
#A = csr_matrix(X)

## ###############
## BU: ROBUST STD
## ###############
#
## try to create result instance to use statsmodels post estimation functions
## https://github.com/statsmodels/statsmodels/blob/master/statsmodels/stats/sandwich_covariance.py
## https://github.com/statsmodels/statsmodels/blob/master/statsmodels/regression/linear_model.py
#
## scipy.sparse.linalg.lsqr returns only diag of (X'X)^{-1}... insuff to get cov
## pinv_wexog: pseudo inverse of X (n, p) i.e. (X'X)^{-1}X' which is (p, n) dense
## cannot simply use existing sm code since requires pinv_wexog
## hence avoid it => use (X'X){-1} which is (p, p) dense
## https://gist.github.com/josef-pkt/21ca2394b073440b3e23
#xtx = A.T.dot(A).toarray()
#xtxi = np.linalg.inv(xtx)
#resid = np.array(y.flatten()) - A.dot(res[0]) # need to use A (sparse)
#df_resid = len(df_qlmc) - len(res[0])
#nobs = len(df_qlmc)
#xu = A.T.dot(scipy.sparse.dia_matrix((resid, 0), shape=(nobs, nobs))).T
#assert scipy.sparse.issparse(xu)
#S = xu.T.dot(xu).toarray()
#cov_p = xtxi.dot(S).dot(xtxi)
#bse = np.sqrt(np.diag(cov_p))
#
## check computation of various het_scale
#hc0_het_scale = resid**2
#hc1_het_scale = nobs/(df_resid)*(resid**2)
##hc2_h = np.diag(np.dot(A, np.dot(xtxi, A.T)))
##hc2_het_scale = resid**2/(1-hc2_h)
