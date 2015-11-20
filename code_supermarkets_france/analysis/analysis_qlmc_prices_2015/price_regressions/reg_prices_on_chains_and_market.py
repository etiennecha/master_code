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

df_comp_h = pd.read_csv(os.path.join(path_built_lsa_csv,
                                     '201407_competition',
                                     'df_store_prospect_comp_H_v_all.csv'),
                        encoding = 'utf-8')

df_comp_s = pd.read_csv(os.path.join(path_built_lsa_csv,
                                     '201407_competition',
                                     'df_store_prospect_comp_S_v_all.csv'), 
                        encoding = 'utf-8')

df_comp = pd.concat([df_comp_h, df_comp_s],
                    axis = 0,
                    ignore_index = True)

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
df_qlmc = df_qlmc[~(df_qlmc['qlmc_chain'] == 'SUPERMARCHE MATCH')]

# keep only if products observed w/in at least 1000 stores (or more: memory..)
df_qlmc['nb_prod_obs'] =\
  df_qlmc.groupby('product')['product'].transform(len).astype(int)
df_qlmc = df_qlmc[df_qlmc['nb_prod_obs'] >= 1200]

# keep only stores w/ at least 400 products
df_qlmc['nb_store_obs'] =\
 df_qlmc.groupby('store_id')['store_id'].transform(len).astype(int)
df_qlmc = df_qlmc[df_qlmc['nb_store_obs'] >= 400]

# count product obs again
df_qlmc['nb_prod_obs'] =\
  df_qlmc.groupby('product')['product'].transform(len).astype(int)

print df_qlmc[['nb_prod_obs', 'nb_store_obs']].describe()

# ############
# REGRESSION
# ############

# check pop variable... 0 for Leclerc in Porto Vecchio
# todo: should cluster standard errors on stores

#str_exo = "C(qlmc_chain) + C(product)"
#X = dmatrix(str_exo, data = df_qlmc, return_type = "matrix")
#y = df_qlmc['price'].values

str_exo = "price ~ C(qlmc_chain) + C(product)"
#str_exo = "price ~ C(qlmc_chain) + surface + C(region) + C(product) + ac_hhi + ac_nb_stores"
y, X = dmatrices(str_exo,
                 data = df_qlmc,
                 return_type = "matrix")

A = csr_matrix(X)

res = scipy.sparse.linalg.lsqr(A,
                               y,
                               iter_lim = 100,
                               calc_var = True)
# X.design_info
param_names = X.design_info.column_names
param_values = res[0]
nb_freedom_degrees = len(df_qlmc) - len(res[0])
param_se = np.sqrt(res[3]**2/nb_freedom_degrees * res[9])

# todo: check if can get same results as with smf.ols
df_reg = pd.DataFrame(zip(param_names,
                          param_values,
                          param_se), columns = ['name', 'coeff', 'bse'])

print u'\nReg result (omitting prod and region FEs):'
print df_reg[(~df_reg['name'].str.contains(u'C\(product\)')) &\
             (~df_reg['name'].str.contains(u'C\(region\)'))].to_string()

# try to create result instance to use statsmodels post estimation functions
# https://github.com/statsmodels/statsmodels/blob/master/statsmodels/stats/sandwich_covariance.py
# http://statsmodels.sourceforge.net/ipdirective/_modules/scikits/statsmodels/regression/linear_model.html
class Results: pass
results = Results()
results.model = Results()
# pinv_wexog: pseudo inverse of n*p matrix... can be a bottleneck
# see if can use res[9] i.e. (A'A)^{-1}
# get rid of Patsy design matrices => numpy arrays
results.model.pinv_wexog = np.linalg.pinv(np.array(X))
results.resid = np.array(y.flatten()) - np.dot(np.array(X), res[0])
results.nobs = len(df_qlmc)
results.df_resid = len(df_qlmc) - len(res[0]) # nb obs - nb parameters
# hc2 requires:
results.model.exog = np.array(X)
results.normalized_cov_params = np.dot(results.model.pinv_wexog,
                                       np.transpose(results.model.pinv_wexog))
print sm.stats.sandwich_covariance.cov_hc0(results)

## #################
## REGRESSIONS (OLD
## #################
#
### representativeness of store sample
##print u'\nCheck retail chain representation:'
##se_ens_alt = df_qlmc[['enseigne_alt', 'store_id']]\
##                    .drop_duplicates()\
##                    .groupby('enseigne_alt').agg(len)['store_id']
##se_repr = se_ens_alt.div(df_comp['enseigne_alt'].value_counts().astype(float),
##                         axis = 'index')
##print se_repr[~pd.isnull(se_repr)]
#
#print u'\nNo control:'
#res_a = smf.ols("price ~ C(qlmc_chain) + C(product)",
#                data = df_qlmc).fit()
#rob_cov_a = sm.stats.sandwich_covariance.cov_hc0(res_a)
#
##print u'\nWith controls:'
##res_b = smf.ols("price ~ C(product) + C(c_departement) + surface + ac_hhi + " +\
##                "C(qlmc_chain, Treatment(reference = 'CENTRE E.LECLERC'))",
##                data = df_qlmc).fit()
