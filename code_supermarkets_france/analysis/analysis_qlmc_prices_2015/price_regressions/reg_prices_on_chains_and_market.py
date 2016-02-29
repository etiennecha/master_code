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

# Add qlmc_chain
ls_ls_enseigne_lsa_to_qlmc = [[['CENTRE E.LECLERC'], 'LECLERC'],
                              [['GEANT CASINO'], 'GEANT'],
                              [['HYPER CASINO'], 'CASINO'],
                              [['INTERMARCHE SUPER',
                                'INTERMARCHE HYPER',
                                'INTERMARCHE CONTACT'], 'INTERMARCHE'],
                              [['HYPER U',
                                'SUPER U',
                                'U EXPRESS'], 'SYSTEME U'],
                              [['MARKET'], 'CARREFOUR MARKET'],
                              [["LES HALLES D'AUCHAN"], 'AUCHAN']]

df_stores['qlmc_chain'] = df_stores['store_chain']
for ls_enseigne_lsa_to_qlmc in ls_ls_enseigne_lsa_to_qlmc:
  df_stores.loc[df_stores['store_chain'].isin(ls_enseigne_lsa_to_qlmc[0]),
              'qlmc_chain'] = ls_enseigne_lsa_to_qlmc[1]

# LOAD STORE COMPETITION (todo: aggregate elsewhere)

ls_lsa_info_cols = [u'surface',
                    u'nb_caisses',
                    u'nb_emplois',
                    u'nb_parking',
                    u'int_ind',
                    u'groupe',
                    u'groupe_alt',
                    u'enseigne_alt',
                    u'type_alt']

ls_lsa_comp_cols = ['ac_nb_stores',
                    'ac_nb_comp',
                    'ac_store_share',
                    'ac_group_share',
                    'ac_hhi',
                    'dist_cl_comp',
                    'dist_cl_groupe',
                    'hhi',
                    'store_share',
                    'group_share',
                    'c_departement',
                    'region']

df_stores = pd.merge(df_stores,
                     df_comp[['id_lsa'] +\
                             ls_lsa_info_cols +\
                             ls_lsa_comp_cols],
                     left_on = 'id_lsa',
                     right_on = 'id_lsa',
                     how = 'left')

# LOAD STORE DEMAND

df_demand_h = pd.read_csv(os.path.join(path_built_lsa_csv,
                                     '201407_competition',
                                     'df_store_prospect_demand_H.csv'),
                        encoding = 'utf-8')

df_demand_s = pd.read_csv(os.path.join(path_built_lsa_csv,
                                       '201407_competition',
                                       'df_store_prospect_comp_S_v_all.csv'), 
                        encoding = 'utf-8')

df_demand = pd.concat([df_demand_h, df_demand_s],
                      axis = 0,
                      ignore_index = True)

df_stores = pd.merge(df_stores,
                     df_demand[['id_lsa', 'pop', 'ac_pop']],
                     left_on = 'id_lsa',
                     right_on = 'id_lsa',
                     how = 'left')

# Merge store chars and prices

print len(df_prices)

# drop redundant columns
df_prices.drop(['store_chain'], axis = 1, inplace = True)
df_qlmc = pd.merge(df_prices,
                   df_stores,
                   how = 'left',
                   on = 'store_id')

print len(df_qlmc)

# Avoid error msg on condition number
df_qlmc['surface'] = df_qlmc['surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_price'] = np.log(df_qlmc['price'])

# ###############################
# RESTRICTIONS ON PRODUCTS/STORES
# ###############################

# drop chain(s) with too few stores
df_qlmc = df_qlmc[~(df_qlmc['qlmc_chain'].isin(['SUPERMARCHE MATCH',
                                                'ATAC',
                                                'MIGROS',
                                                'RECORD',
                                                'G 20']))]

# keep only if products observed w/in at least 1000 stores (or more: memory..)
df_qlmc['nb_prod_obs'] =\
  df_qlmc.groupby('product')['product'].transform(len).astype(int)
df_qlmc = df_qlmc[df_qlmc['nb_prod_obs'] >= 1000]

# keep only stores w/ at least 400 products
df_qlmc['nb_store_obs'] =\
 df_qlmc.groupby('store_id')['store_id'].transform(len).astype(int)
df_qlmc = df_qlmc[df_qlmc['nb_store_obs'] >= 400]

# count product obs again
df_qlmc['nb_prod_obs'] =\
  df_qlmc.groupby('product')['product'].transform(len).astype(int)

print df_qlmc[['nb_prod_obs', 'nb_store_obs']].describe()

# ############
# REGRESSIONS
# ############

## test get_dummies /w sparse option (requires pandas => 0.16.1)
#df_test = pd.get_dummies(df_qlmc,
#                         columns = ['product', 'qlmc_chain'],
#                         prefix = ['product', 'qlmc_chain'],
#                         sparse = True)

# create df to convert to sparse (need index: 0 to n obs)
df_i = pd.DataFrame('intercept', columns = ['col'], index = df_qlmc.index)
df_i.index.name = 'row'

df_0 = df_qlmc[['product']].copy()
df_0['product'] = 'C(product) ' + df_0['product']
df_0.index.name = 'row'
df_0.rename(columns = {'product': 'col'}, inplace = True)

df_1 = df_qlmc[['qlmc_chain']].copy()
df_1['qlmc_chain'] = 'C(qlmc_chain) ' + df_1['qlmc_chain']
df_1.index.name = 'row'
df_1.rename(columns = {'qlmc_chain': 'col'}, inplace = True)

df_2 = pd.concat([df_i, df_0, df_1], axis = 0)

# omit one category for each categorical variable (reference)
# a priori can simply drop row if there is an intercept (mat row created)
df_2['val'] = 1
ref_prod =  df_qlmc['product'].drop_duplicates().sort_values().iloc[0]
ref_chain = 'LECLERC' # df_qlmc['qlmc_chain'].drop_duplicates().sort_values().iloc[0]
ls_refs = ['C(product) ' + ref_prod,
           'C(qlmc_chain) ' + ref_chain]
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
print u'\nReg result (omitting prod and region FEs):'
print df_reg[(~df_reg['name'].str.contains(u'C\(product\)')) &\
             (~df_reg['name'].str.contains(u'C\(region\)'))].to_string()

# try to create result instance to use statsmodels post estimation functions
# https://github.com/statsmodels/statsmodels/blob/master/statsmodels/stats/sandwich_covariance.py
# https://github.com/statsmodels/statsmodels/blob/master/statsmodels/regression/linear_model.py

# scipy.sparse.linalg.lsqr returns only diag of (X'X)^{-1}... insuff to get cov
# pinv_wexog: pseudo inverse of X (n, p) i.e. (X'X)^{-1}X' which is (p, n) dense
# cannot simply use existing sm code since requires pinv_wexog
# hence avoid it => use (X'X){-1} which is (p, p) dense
# https://gist.github.com/josef-pkt/21ca2394b073440b3e23
xtx = A.T.dot(A).toarray()
xtxi = np.linalg.inv(xtx)
resid = np.array(y.flatten()) - A.dot(res[0]) # need to use A (sparse)
df_resid = len(df_qlmc) - len(res[0])
nobs = len(df_qlmc)
xu = A.T.dot(scipy.sparse.dia_matrix((resid, 0), shape=(nobs, nobs))).T
assert scipy.sparse.issparse(xu)
S = xu.T.dot(xu).toarray()
cov_p = xtxi.dot(S).dot(xtxi)
bse = np.sqrt(np.diag(cov_p))

# check computation of various het_scale
hc0_het_scale = resid**2
hc1_het_scale = nobs/(df_resid)*(resid**2)
#hc2_h = np.diag(np.dot(A, np.dot(xtxi, A.T)))
#hc2_het_scale = resid**2/(1-hc2_h)

# compute rsquare
y_hat = A * res[0]
rsquare = 1 - ((y - y_hat)**2).sum() /\
                ((y - y.mean())**2).sum()

# goodness of fit (to compare with log)
if price_col == 'ln_price':
  df_qlmc['price_hat'] = np.exp(y_hat)
else:
  df_qlmc['price_hat'] = y_hat
print('SS of residuals for price:',
      ((df_qlmc['price'] - df_qlmc['price_hat'])**2).sum())

#### #################
#### NON SPARSE REG 
#### #################
###
#### Check regression results with reduced nb stores / products
###
###print u'\nNo control:'
###res_a = smf.ols("price ~ C(qlmc_chain) + C(product)",
###                data = df_qlmc).fit()
###rob_cov_a = sm.stats.sandwich_covariance.cov_hc0(res_a)
###
####print u'\nWith controls:'
####res_b = smf.ols("price ~ C(product) + C(c_departement) + surface + ac_hhi + " +\
####                "C(qlmc_chain, Treatment(reference = 'CENTRE E.LECLERC'))",
####                data = df_qlmc).fit()
