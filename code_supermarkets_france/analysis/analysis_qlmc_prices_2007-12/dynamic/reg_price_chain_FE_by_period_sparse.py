#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import scipy
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import re

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

pd.set_option('float_format', '{:,.2f}'.format)

# ############
# LOAD DATA
# ############

print u'loading df_qlmc'
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      dtype = {'id_lsa' : str,
                               'insee_zip' : str,
                               'insee_code' : str},
                      encoding = 'utf-8')

print u'loading df_stores_final'
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores.csv'),
                        dtype = {'id_lsa' : str,
                                 'insee_zip' : str,
                                 'insee_code' : str},
                        encoding = 'utf-8')

# Period restriction
per_min, per_max = 0, 8
nb_per_min = 3

# SUBSET STORES
df_stores_sub = df_stores[(df_stores['Period'] >= per_min) &\
                          (df_stores['Period'] <= per_max)].copy()
se_vc_id_lsa = df_stores_sub['id_lsa'].value_counts()
# keep top 100? which criterion?
df_stores_sub = df_stores_sub[df_stores_sub['id_lsa']\
                  .isin(se_vc_id_lsa[se_vc_id_lsa >= nb_per_min].index)]

df_qlmc_sub = df_qlmc[(df_qlmc['Period'] >= per_min) &\
                      (df_qlmc['Period'] <= per_max) &\
                      (df_qlmc['id_lsa'].isin(se_vc_id_lsa[se_vc_id_lsa >= nb_per_min].index))].copy()

# Make one to one relation between id_lsa and Store (across periods)
df_stores_id_lsa_sub = df_stores_sub[['id_lsa', 'Store']].drop_duplicates()
dict_stores_id_lsa = {row['id_lsa'] : row['Store'] for row_i, row in\
                       df_stores_id_lsa_sub.iterrows()}
df_qlmc_sub['Store'] = df_qlmc_sub['id_lsa'].apply(lambda x : dict_stores_id_lsa[x])

# SUBSET PRODUCTS

df_products = df_qlmc_sub[['Period', 'Product']].drop_duplicates()
se_vc_products = df_qlmc_sub['Product'].value_counts()
# top 100 for now
df_qlmc_sub = df_qlmc_sub[df_qlmc_sub['Product']\
                .isin(se_vc_products[0:400].index)]

# GET RID OF Chain-Period WITH INSUFFICIENT OBS
# todo
se_chain_period = pd.pivot_table(df_qlmc_sub[['Store_Chain', 'Period']],
                                 index = ['Store_Chain', 'Period'],
                                 aggfunc = len)
se_pbms = se_chain_period[se_chain_period < 50]

# #############
# REGRESSION
# #############

#reg = smf.ols("Price ~ C(Product):C(Period)" +\
#              "+ C(Store, Treatment(reference='CORA ARCUEIL')):C(Period)",
#              data  = df_qlmc_sub).fit()
#print reg.summary()

from patsy import dmatrix, dmatrices
X = dmatrix("C(Product) + C(Period)" +\
            "+ C(Store_Chain):C(Period)",
            data = df_qlmc_sub,
            return_type = "matrix")

from scipy.sparse import csr_matrix
A = csr_matrix(X)

res = scipy.sparse.linalg.lsqr(A,
                               df_qlmc_sub['Price'].values,
                               iter_lim = 100,
                               calc_var = True)
# X.design_info
param_names = X.design_info.column_names
param_values = res[0]
nb_freedom_degrees = len(df_qlmc_sub) - len(res[0])
param_se = np.sqrt(res[3]**2/nb_freedom_degrees * res[9])

# todo: check if can get same results as with smf.ols
df_reg = pd.DataFrame(zip(param_names,
                          param_values,
                          param_se), columns = ['name', 'coeff', 'bse'])

# for now: need to filter out unobserved store-period from output
def get_chain_period_fe(var_name):
  match = re.match('C\(Store_Chain.*?\[T\.(.*?)\]:C\(Period\)\[(.*?)\]',
                   var_name)
  if match:
    return match.group(1), int(match.group(2))
  else:
    return None, None

df_reg['Store_Chain'], df_reg['Period'] = zip(*df_reg['name'].apply(lambda x: get_chain_period_fe(x)))
df_fe = df_reg[~df_reg['Store_Chain'].isnull()].copy()
df_fe.drop('name', axis = 1, inplace = True)
df_fe.set_index(['Store_Chain', 'Period'], inplace = True)
# subselect those with observations
df_test = df_fe.reindex(se_chain_period.index)
df_test.reset_index(drop = False, inplace = True)

df_su_fe = df_test.pivot(index = 'Store_Chain', columns = 'Period', values = 'coeff')

print u'\nEvo in store FE across periods:'
print df_su_fe.to_string()

# todo: add R2 (not urgent)
# todo: add confidence interval to check whether chges are significant

# todo: (here?) ctrl for store size, competitiveness of market, pop revenues etc?
