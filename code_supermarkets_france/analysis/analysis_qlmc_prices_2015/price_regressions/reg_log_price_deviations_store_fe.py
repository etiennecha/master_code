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
from sklearn.feature_extraction import DictVectorizer

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

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str},
                        encoding = 'utf-8')

df_lsa = pd.read_csv(os.path.join(path_built_lsa_csv,
                                  'df_lsa.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

# Harmonize chains
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

## log deviation to mean product price
#df_prices['ln_pd'] = np.log(df_prices['price'] /\
#                      df_prices.groupby('product')['price'].transform('mean'))

# log deviation to mean market (dpt for instance) product price
df_stores = pd.merge(df_stores,
                     df_lsa[['id_lsa', 'c_departement']],
                     on = 'id_lsa',
                     how = 'left')
df_prices = pd.merge(df_prices,
                     df_stores[['store_id', 'id_lsa', 'c_departement']],
                     on = 'store_id',
                     how = 'left')
df_prices = df_prices[~df_prices['c_departement'].isnull()]
df_prices['ln_pd'] = np.log(df_prices['price'] /\
                      df_prices.groupby(['product', 'c_departement'])['price'].transform('mean'))
df_prices = df_prices[~df_prices['ln_pd'].isnull()]
ls_suspicious_prods = ['VIVA LAIT TGV 1/2 ÉCRÉMÉ VIVA BP 6X50CL']
df_prices = df_prices[~df_prices['product'].isin(ls_suspicious_prods)]

## ##############
## REGRESSION
## ##############
#
#price_col = 'ln_pd'
#
#df_prices['intercept'] = 'intercept'
#pd_as_dicts = [dict(r.iteritems())\
#                 for _, r in df_prices[['store_id', 'intercept']].iterrows()]
##pd_as_dicts_2 = [dict(dict_temp.items() + [('intercept', 'intercept')])\
##                   for dict_temp in pd_as_dicts]
#ref = u'centre-e-leclerc-les-angles' # ref = pd_as_dicts[0]['store_id']
#pd_as_dicts_2 = [dict_temp if dict_temp['store_id'] != ref \
#                     else {'intercept' : 'intercept'} for dict_temp in pd_as_dicts]
#
#sparse_mat_prod_store = DictVectorizer(sparse=True).fit_transform(pd_as_dicts_2)
#res_01 = scipy.sparse.linalg.lsqr(sparse_mat_prod_store,
#                                  df_prices[price_col].values,
#                                  iter_lim = 100,
#                                  calc_var = True)
#nb_fd_01 = len(df_prices) - len(res_01[0])
#ar_std_01 = np.sqrt(res_01[3]**2/nb_fd_01 * res_01[9])
#ls_stores = sorted(df_prices['store_id'].copy().drop_duplicates().values)
#
## Compute rsquare
#y_hat = sparse_mat_prod_store * res_01[0]
#df_prices['yhat'] = y_hat
#df_prices['residual'] = df_prices[price_col] - df_prices['yhat'] 
#rsquare = 1 - ((df_prices[price_col] - df_prices['yhat'])**2).sum() /\
#                ((df_prices[price_col] - df_prices[price_col].mean())**2).sum()
#ls_stores.remove(ref)
#
#ls_rows_01 = zip(ls_stores, res_01[0], ar_std_01)
#df_res_01 = pd.DataFrame(ls_rows_01, columns = ['Name', 'Coeff', 'Std'])
#df_res_01['t_stat'] = df_res_01['Coeff'] / df_res_01['Std']
#df_stores_fe = df_res_01.copy()
#
## Analyse store FEs
#df_stores.set_index('store_id', inplace = True)
#df_stores_fe.set_index('Name', inplace = True)
#df_stores = pd.merge(df_stores,
#                     df_stores_fe,
#                     left_index = True,
#                     right_index = True,
#                     how = 'left')
## check syntax update in pandas 0.17
#df_chains_su = df_stores.groupby('qlmc_chain')['Coeff']\
#                        .agg('describe').reset_index()\
#                        .pivot(index='qlmc_chain',
#                               values=0,
#                               columns='level_1')
#df_chains_su = df_chains_su[df_chains_su['count'] >= 10]
#lsddesc = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
#print df_chains_su[lsddesc].to_string()

# #########################
# REGRESSION: PATSY DUMMIES
# #########################

price_col = 'ln_pd'

# create df to convert to sparse (use df_prices.index: not 0 to nobs)
df_i = pd.DataFrame('intercept',
                    columns = ['col'],
                    index = df_prices.index)
df_i.index.name = 'row'

df_0 = df_prices[['store_id']].copy()
df_0.index.name = 'row'
df_0.rename(columns = {'store_id': 'col'}, inplace = True)

df_2 = pd.concat([df_i, df_0], axis = 0)

# omit one category for each categorical variable (reference)
# a priori can simply drop row if there is an intercept (mat row created)
df_2['val'] = 1
ref_id = u'centre-e-leclerc-les-angles'
ls_refs = [ref_id]
for ref in ls_refs:
  df_2 = df_2[~(df_2['col'] == ref)]
df_2.set_index('col', append = True, inplace = True)

# add variables which are not dummies: need to append multiindex df
df_3 = pd.DataFrame(df_prices['price'].values,
                    columns = ['val'],
                    index = df_prices.index)
df_3.index.name = 'row'
df_3['col'] = 'price'
df_3.set_index('col', append = True, inplace = True)

# concat dfs
df_2 = pd.concat([df_2, df_3], axis = 0)

# build sparse matrix
s = pd.Series(df_2['val'].values)
s.index = df_2.index
ss = s.to_sparse()
A, rows, columns = ss.to_coo(row_levels=['row'],
                             column_levels = ['col'],
                             sort_labels = True)
y = df_prices[price_col].values
param_names = columns
res = scipy.sparse.linalg.lsqr(A,
                               y,
                               iter_lim = 100,
                               calc_var = True)
param_values = res[0]
nb_freedom_degrees = len(df_prices) - len(res[0])
param_se = np.sqrt(res[3]**2/nb_freedom_degrees * res[9])
df_reg = pd.DataFrame(zip(param_names,
                          param_values,
                          param_se), columns = ['name', 'coeff', 'bse'])
df_reg['tstat'] = df_reg['coeff'] / df_reg['bse']
# Compute rsquare
y_hat = A * res[0]
df_prices['yhat'] = y_hat
df_prices['residual'] = df_prices[price_col] - df_prices['yhat'] 
rsquare = 1 - ((df_prices[price_col] - df_prices['yhat'])**2).sum() /\
                ((df_prices[price_col] - df_prices[price_col].mean())**2).sum()
