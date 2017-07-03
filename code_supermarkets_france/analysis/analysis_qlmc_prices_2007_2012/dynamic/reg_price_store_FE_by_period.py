#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
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
per_min, per_max = 0, 4
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
                .isin(se_vc_products[0:100].index)]

# GET RID OF Store-Period WITH INSUFFICIENT OBS
# todo
se_store_period = pd.pivot_table(df_qlmc_sub[['Store', 'Period']],
                                 index = ['Store', 'Period'],
                                 aggfunc = len)
se_pbms = se_store_period[se_store_period < 10]

# #############
# REGRESSION
# #############

# Make sure reference store appears in all periods (else?)

#print smf.ols("Price ~ C(Product):C(Period)' + C(Store):C(Period)",
#              data  = df_qlmc_sub).fit().summary()

reg = smf.ols("Price ~ C(Product):C(Period)" +\
              "+ C(Store, Treatment(reference='CORA ARCUEIL')):C(Period)",
              data  = df_qlmc_sub).fit()
print reg.summary()

df_reg = pd.DataFrame(zip(reg.params.index,
                          reg.params.values,
                          reg.bse), columns = ['name', 'coeff', 'bse'])

# for now: need to filter out unobserved store-period from output
def get_store_period_fe(var_name):
  match = re.match('C\(Store.*?\[T\.(.*?)\]:C\(Period\)\[(.*?)\]',
                   var_name)
  if match:
    return match.group(1), int(match.group(2))
  else:
    return None, None

df_reg['Store'], df_reg['Period'] = zip(*df_reg['name'].apply(lambda x: get_store_period_fe(x)))
df_fe = df_reg[~df_reg['Store'].isnull()].copy()
df_fe.drop('name', axis = 1, inplace = True)
df_fe.set_index(['Store', 'Period'], inplace = True)
# subselect those with observations
df_test = df_fe.reindex(se_store_period.index)
df_test.reset_index(drop = False, inplace = True)

df_su_fe = df_test.pivot(index = 'Store', columns = 'Period', values = 'coeff')
print df_su_fe.to_string()
