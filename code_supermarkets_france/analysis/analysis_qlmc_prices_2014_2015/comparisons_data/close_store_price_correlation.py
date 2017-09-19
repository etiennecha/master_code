#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

path_built = os.path.join(path_data, 'data_supermarkets', 'data_built')
path_built_csv = os.path.join(path_built, 'data_qlmc_2014_2015', 'data_csv')
path_built_csv_stats = os.path.join(path_built, 'data_qlmc_2014_2015', 'data_csv_stats')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##########
# LOAD DATA
# ##########

df_prices = pd.read_csv(os.path.join(path_built_csv_stats, 'df_res_ln_prices.csv'),
                        encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv, 'df_stores_final_201503.csv'),
                        dtype = {'id_lsa' : str,
                                 'c_insee' : str},
                        encoding = 'utf-8')

df_qlmc_comparisons = pd.read_csv(os.path.join(path_built_csv,
                                               'df_qlmc_competitors_final_201503.csv'),
                                  encoding = 'utf-8')

# ADD STORE PRICE FE IN DF STORES
df_fes = pd.read_csv(os.path.join(path_built_csv_stats,
                                  'df_res_ln_price_fes.csv'),
                     encoding = 'utf-8')

df_store_fes = df_fes[df_fes['name'].str.startswith('C(store_id)')].copy()
df_store_fes['store_id'] = df_store_fes['name'].apply(\
                             lambda x: x.replace('C(store_id)', '').strip())
df_store_fes['store_price'] = (df_store_fes['coeff'] + 1) * 100

df_stores = pd.merge(df_stores,
                     df_store_fes,
                     on = 'store_id',
                     how = 'left')

# ADD STORE DISPERSION IN DF STORES
df_prices['res'] = df_prices['ln_price'] - df_prices['ln_price_hat']

# robustness: reject residuals if beyond 40%
df_prices = df_prices[df_prices['res'].abs() < 0.4]

#se_store_disp = (df_prices[['store_id', 'res']].groupby('store_id')
#                                              .agg(lambda x: (x**2).mean()))
se_store_disp = (df_prices[['store_id', 'res']].groupby('store_id')
                                               .agg(lambda x: x.abs().mean()))
df_stores.set_index('store_id', inplace = True)
df_stores['store_disp'] = se_store_disp

# ADD STORE FE AND DISP IN DF QLMC COMPETITORS
df_stores.reset_index(drop = False, inplace = True)
df_qlmc_comparisons.rename(columns = {'lec_id': 'store_id'}, inplace = True)
df_qlmc_comparisons = pd.merge(df_qlmc_comparisons,
                               df_stores[['store_id', 'store_price', 'store_disp']],
                               on = 'store_id',
                               how = 'left')
df_qlmc_comparisons.rename(columns = {'store_id' : 'lec_id',
                                      'store_price' : 'lec_price',
                                      'store_disp' : 'lec_disp'}, inplace = True)
df_qlmc_comparisons.rename(columns = {'comp_id': 'store_id'}, inplace = True)
df_qlmc_comparisons = pd.merge(df_qlmc_comparisons,
                               df_stores[['store_id', 'store_price', 'store_disp']],
                               on = 'store_id',
                               how = 'left')
df_qlmc_comparisons.rename(columns = {'store_id' : 'comp_id',
                                      'store_price' : 'comp_price',
                                      'store_disp' : 'comp_disp'}, inplace = True)

# #####################################
# ANALYSIS: PRICE LEC VS COMPRICE COMP
# #####################################

for chain in ['GEANT CASINO', 'CARREFOUR', 'INTERMARCHE', 'SUPER U', 'CORA']:
  df_chain = (df_qlmc_comparisons[(df_qlmc_comparisons['comp_chain'] == chain) &
                                  (df_qlmc_comparisons['gg_dur_val'] <= 20) &
                                  (df_qlmc_comparisons['lec_price'] >= 92) &
                                  (df_qlmc_comparisons['lec_price'] <= 100)])
  
  res_chain = smf.ols('comp_price ~ lec_price', data = df_chain).fit()
  print()
  print(chain)
  print(res_chain.summary())
  # graph
  intercept = res_chain.params.ix['Intercept']
  slope = res_chain.params.ix['lec_price']
  ax = df_chain.plot(kind = 'scatter', x = 'lec_price', y = 'comp_price')
  x0, x1 = ax.get_xlim()
  ax.plot([x0, x1], [intercept + slope*x0, intercept + slope*x1])
  plt.title(chain)
  plt.show()
