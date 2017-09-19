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

path_built = os.path.join(path_data, 'data_supermarkets', 'data_built')
path_built_csv = os.path.join(path_built, 'data_qlmc_2014_2015', 'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

df_qlmc = pd.read_csv(os.path.join(path_built_csv, 'df_qlmc_2014_2015.csv'),
                      dtype = {'ean' : str,
                               'id_lsa' : str},
                      encoding = 'utf-8')

# ADD COLUMNS FOR PRODUCT PRICE VARIATIONS
ls_tup_pers = [('0', '1'), ('1', '2'), ('0', '2')]
for tup_per in ls_tup_pers:
  df_qlmc['pct_var_{:s}{:s}'.format(*tup_per)] = (
    (df_qlmc['price_{:s}'.format(tup_per[1])] /
       df_qlmc['price_{:s}'.format(tup_per[0])] - 1) * 100)

ls_pct_var_cols = ['pct_var_{:s}{:s}'.format(*tup_per) for tup_per in ls_tup_pers]

# DROP SUSPECT PRICE VARIATIONS
df_qlmc = (df_qlmc[(~((df_qlmc['pct_var_01'] >= 100) & (df_qlmc['pct_var_02'].isnull()))) &
                   (~((df_qlmc['pct_var_01'] >= 100) & (df_qlmc['pct_var_02'] <= 100))) &
                   (~(df_qlmc['pct_var_12'] >= 100))])

# All periods observed? 670 stores with 158 to 1599 obs
df_full = (df_qlmc[(~df_qlmc['price_0'].isnull()) &
                   (~df_qlmc['price_1'].isnull()) &
                   (~df_qlmc['price_2'].isnull())])

# Could also consider 0 to 2
df_02 = df_qlmc[(~df_qlmc['price_0'].isnull()) & (~df_qlmc['price_2'].isnull())]

# Check indiv price vars for suspicious changes
# Quite a few pbms to fix... should check price distributions in static
# print(df_02[df_02['store_chain'] == 'INTERMARCHE']['pct_var_02'].describe())
# print(df_full[df_full['pct_var_01'] > 1].to_string())

# ################################################
# VARIATIONS BY CHAINS (STORE AND PRODUCTS POOLED)
# ################################################

# All obs are pooled within each period by chain (no average)
print(u'Distrs of store/product variations over time')
for chain in ['LECLERC', 'GEANT CASINO', 'CARREFOUR']:
  print()
  print(chain)
  print(df_qlmc[df_qlmc['store_chain'] == chain][ls_pct_var_cols].describe().to_string())

# #########################################
# VARIATIONS OF PRODUCT MEAN PRICE BY CHAIN
# #########################################

print()
print(u'Aggregate inter-period variations by chain:')

# - Classical Method: compare avg chain prices across periods
# - Can restrict products to avoid comp effects

# Average price by period/chain/product
ls_prod_cols = ['ean'] # ['section', 'family' , 'product']
ls_price_cols = ['price_0', 'price_1', 'price_2']
dict_df_mcp = {}
for price_col in ls_price_cols:
  ls_col_gb = ['store_chain'] + ls_prod_cols
  df_mcp = df_qlmc.groupby(ls_col_gb).agg([len, 'mean'])[price_col]
  df_mcp = df_mcp[(~df_mcp['mean'].isnull()) & (df_mcp['len'] >= 20)]
  df_mcp.reset_index(drop = False, inplace = True)
  dict_df_mcp[price_col] = df_mcp

dict_df_per = {'201409' : dict_df_mcp['price_0'],
               '201405' : dict_df_mcp['price_1'],
               '201503' : dict_df_mcp['price_2']}

ls_evo_loop = [['201405', '201409'],
               ['201409', '201503'],
               ['201405', '201503']]

dict_df_evo = {}
for date_str_t0, date_str_t1 in ls_evo_loop:
  df_per_t0 = dict_df_per[date_str_t0]
  df_per_t1 = dict_df_per[date_str_t1]
  ls_chains = set(df_per_t0['store_chain'].unique())\
                .intersection(set(df_per_t1['store_chain'].unique()))
  ls_rows_evo = []
  for chain in ls_chains:
    df_chain_a = df_per_t0[df_per_t0['store_chain'] == chain]
    df_chain_b = df_per_t1[df_per_t1['store_chain'] == chain]
    df_compa = pd.merge(df_chain_a[ls_prod_cols + ['mean']],
                        df_chain_b[ls_prod_cols + ['mean']],
                        on = ls_prod_cols,
                        how = 'inner',
                        suffixes = ('_t', '_t+1'))
    nb_prods = len(df_compa)
    agg_chge = np.nan
    if nb_prods != 0:
      agg_chge = ((df_compa['mean_t+1'].sum() / df_compa['mean_t'].sum()) - 1) * 100
    ls_rows_evo.append((chain, nb_prods, agg_chge))
  df_evo = pd.DataFrame(ls_rows_evo,
                       columns = ['store_chain', 'nb_prods', 'var'])
  evo_str = u'{:s} to {:s}'.format(date_str_t0, date_str_t1)
  dict_df_evo[evo_str] = df_evo
  print()
  print(evo_str)
  print(df_evo.to_string())

# #################################
# VARIATIONS BY STORE (BY CHAIN?)
# #################################

# todo: drop stores with too few obs

print()
print(u'Inter-period distributions of store variation by chain:')

# Average price by period/chain/product
ls_prod_cols = ['ean'] # ['section', 'family' , 'product']j
ls_col_gb = ['store_chain', 'store_name']

ls_evo_loop_2 = [[['201405', '201409'], (0, 1)],
                 [['201409', '201503'], (1, 2)],
                 [['201405', '201503'], (0, 2)]]

dict_df_evo_2 = {}
dict_df_evo_2_stores = {}
for tup_date_str, tup_price_ind in ls_evo_loop_2:
  df_temp = (df_qlmc[(~df_qlmc['price_{:d}'.format(tup_price_ind[0])].isnull()) &
                     (~df_qlmc['price_{:d}'.format(tup_price_ind[1])].isnull())])
  gbcs = df_temp.groupby(ls_col_gb)
  def comp_var(df):
    return ((df['price_{:d}'.format(tup_price_ind[1])].sum() /
               df['price_{:d}'.format(tup_price_ind[0])].sum() - 1) * 100)
  df_cs = gbcs.apply(comp_var)
  df_cs = df_cs.reset_index(drop = False)
  df_su_cs = df_cs.groupby('store_chain').agg('describe').unstack()[0]
  evo_str_2 = u'{:s} to {:s}'.format(tup_date_str[0], tup_date_str[1])
  dict_df_evo_2[evo_str_2] = df_su_cs
  dict_df_evo_2_stores[evo_str_2] = df_cs
  print()
  print(evo_str_2)
  print(df_su_cs.to_string())
