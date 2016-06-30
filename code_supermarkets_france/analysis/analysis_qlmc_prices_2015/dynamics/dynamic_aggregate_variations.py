#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_built_2015 = os.path.join(path_data,
                               'data_supermarkets',
                               'data_built',
                               'data_qlmc_2015')
path_built_201415_csv = os.path.join(path_built_2015,
                                     'data_csv_2014-2015')
path_built_201415_json = os.path.join(path_built_2015,
                                     'data_json_2014-2015')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

df_qlmc = pd.read_csv(os.path.join(path_built_201415_csv,
                                   'df_qlmc_2014-2015.csv'),
                      dtype = {'ean' : str,
                               'id_lsa' : str},
                      encoding = 'utf-8')


df_comp_pairs = pd.read_csv(os.path.join(path_built_201415_csv,
                                         'df_comp_store_pairs.csv'),
                            dtype = {'id_lsa_0' : str,
                                     'id_lsa_1' : str},
                            encoding = 'utf-8')

df_comp_pairs = df_comp_pairs[df_comp_pairs['dist'] <= 10]

# ############################################
# VARIATIONS OF STORE PRODUCT PRICES BY CHAIN
# ############################################

# All obs are pooled within each period by chain (no average)

print(u'Distrs of store/product variations over time')
ls_tup_pers = [('0', '1'), ('1', '2'), ('0', '2')]
for tup_per in ls_tup_pers:
  df_qlmc['pct_var_{:s}{:s}'.format(*tup_per)] =\
    (df_qlmc['price_{:s}'.format(tup_per[1])] /\
      df_qlmc['price_{:s}'.format(tup_per[0])] - 1) * 100

# drop suspect price variations
df_qlmc = df_qlmc[(~((df_qlmc['pct_var_01'] >= 100) &\
                     (df_qlmc['pct_var_02'].isnull()))) &\
                  (~((df_qlmc['pct_var_01'] >= 100) &\
                     (df_qlmc['pct_var_02'] <= 100))) &\
                  (~(df_qlmc['pct_var_12'] >= 100))]

ls_pct_var_cols = ['pct_var_{:s}{:s}'.format(*tup_per)\
                      for tup_per in ls_tup_pers]

for chain in ['LECLERC', 'GEANT CASINO', 'CARREFOUR']:
  print()
  print(chain)
  print(df_qlmc[df_qlmc['store_chain'] == chain]\
               [ls_pct_var_cols].describe().to_string())

# All periods observed? 670 stores with 158 to 1599 obs
df_full = df_qlmc[(~df_qlmc['price_0'].isnull()) &\
                  (~df_qlmc['price_1'].isnull()) &\
                  (~df_qlmc['price_2'].isnull())]

# Could also consider 0 to 2
df_02 = df_qlmc[(~df_qlmc['price_0'].isnull()) &\
                (~df_qlmc['price_2'].isnull())]

# Check indiv price vars for suspicious changes
# Quite a few pbms to fix... should check price distributions in static
# print(df_02[df_02['store_chain'] == 'INTERMARCHE']['pct_var_02'].describe())
# print(df_full[df_full['pct_var_01'] > 1].to_string())

# #########################################
# VARIATIONS OF PRODUCT MEAN PRICE BY CHAIN
# #########################################

# - Classical Method: compare avg chain prices across periods
# - Can restrict products to avoid comp effects

# Average price by period/chain/product
ls_prod_cols = ['ean'] # ['section', 'family' , 'product']
ls_price_cols = ['price_0', 'price_1', 'price_2']
dict_df_mcp = {}
for price_col in ls_price_cols:
  ls_col_gb = ['store_chain'] + ls_prod_cols + [price_col]
  df_mcp = df_qlmc.groupby(ls_col_gb[:-1]).agg([len, 'mean'])[price_col]
  df_mcp = df_mcp[(~df_mcp['mean'].isnull()) &\
                  (df_mcp['len'] >= 20)]
  df_mcp.reset_index(drop = False, inplace = True)
  dict_df_mcp[price_col] = df_mcp

df_per_0, df_per_1, df_per_2 = dict_df_mcp['price_0'],\
                               dict_df_mcp['price_1'],\
                               dict_df_mcp['price_2']

ls_scs = ['LECLERC',
          'AUCHAN',
          'CARREFOUR',
          'CARREFOUR MARKET',
          'GEANT CASINO',
          'CASINO',
          'SUPER U',
          'INTERMARCHE',
          'CORA']

ls_rows_02 = []
for chain in ls_scs:
  df_chain_0 = df_per_0[df_per_0['store_chain'] == chain]
  df_chain_2 = df_per_2[df_per_2['store_chain'] == chain]
  df_compa = pd.merge(df_chain_0[ls_prod_cols + ['mean']],
                      df_chain_2[ls_prod_cols + ['mean']],
                      on = ls_prod_cols,
                      how = 'inner',
                      suffixes = ('_t', '_t+1'))
  nb_prods = len(df_compa)
  agg_chge = np.nan
  if nb_prods != 0:
    agg_chge = ((df_compa['mean_t+1'].sum() / df_compa['mean_t'].sum()) - 1) * 100
  ls_rows_02.append((chain, nb_prods, agg_chge))
df_02 = pd.DataFrame(ls_rows_02,
                     columns = ['store_chain', 'nb_prods', 'var'])
print()
print(u'Var 2014/05 - 2015/03')
print(df_02.to_string())


ls_scs_12 = ['LECLERC',
             'CARREFOUR',
             'CARREFOUR MARKET',
             'GEANT CASINO',
             'CASINO']

ls_rows_12 = []
for chain in ls_scs_12:
  df_chain_1 = df_per_1[df_per_1['store_chain'] == chain]
  df_chain_2 = df_per_2[df_per_2['store_chain'] == chain]
  df_compa = pd.merge(df_chain_1[ls_prod_cols + ['mean']],
                      df_chain_2[ls_prod_cols + ['mean']],
                      on = ls_prod_cols,
                      how = 'inner',
                      suffixes = ('_t', '_t+1'))
  nb_prods = len(df_compa)
  agg_chge = np.nan
  if nb_prods != 0:
    agg_chge = ((df_compa['mean_t+1'].sum() / df_compa['mean_t'].sum()) - 1) * 100
  ls_rows_12.append((chain, nb_prods, agg_chge))
df_12 = pd.DataFrame(ls_rows_12,
                     columns = ['store_chain', 'nb_prods', 'var'])
print()
print(u'Var 2014/09 - 2015/03')
print(df_12.to_string())

# #################################
# VARIATIONS BY STORE (BY CHAIN?)
# #################################

# Average price by period/chain/product
ls_prod_cols = ['ean'] # ['section', 'family' , 'product']j
ls_col_gb = ['store_chain', 'store_name']

price_inds = (0, 1)
df_temp = df_qlmc[(~df_qlmc['price_{:d}'.format(price_inds[0])].isnull()) &\
                  (~df_qlmc['price_{:d}'.format(price_inds[1])].isnull())]
gbcs = df_temp.groupby(ls_col_gb)
def comp_var(df):
  return (df['price_{:d}'.format(price_inds[1])].sum() /\
            df['price_{:d}'.format(price_inds[0])].sum() - 1) * 100
df_cs = gbcs.apply(comp_var)
df_cs = df_cs.reset_index(drop = False)
df_su_cs = df_cs.groupby('store_chain').agg('describe').unstack()

#df_scp = df_mcp[(~df_mcp['mean'].isnull()) &\
#                (df_mcp['len'] >= 20)]
#df_mcp.reset_index(drop = False, inplace = True)
#dict_df_mcp[price_col] = df_mcp
