#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import timeit
from functions_generic_qlmc import *
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

pd.set_option('float_format', '{:,.1f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.1f}'.format(x)

path_built_2015 = os.path.join(path_data,
                               'data_supermarkets',
                               'data_built',
                               'data_qlmc_2015')

path_built_201503_csv =  os.path.join(path_built_2015,
                                      'data_csv_201503')

path_built_201415_csv = os.path.join(path_built_2015,
                                     'data_csv_2014-2015')

df_prices = pd.read_csv(os.path.join(path_built_201503_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')
ls_prod_cols = ['section', 'family', 'product']
store_col = 'store_id'

#ls_qlmc_dates = ['201405',
#                 '201409',
#                 '201503']
#date_str = ls_qlmc_dates[2]
#df_prices = pd.read_csv(os.path.join(path_built_201415_csv,
#                                     'df_qlmc_{:s}.csv'.format(date_str)),
#                        encoding = 'utf-8')
#ls_prod_cols = ['ean', 'product']
#store_col = 'store_name'
#if date_str == '201503':
#  ls_prod_cols = ['section', 'family', 'product']
#  store_col = 'store_id'

# Costly to search by store_id within df_prices
# hence first split df_prices in chain dataframes
dict_chain_dfs = {chain: df_prices[df_prices['store_chain'] == chain]\
                    for chain in df_prices['store_chain'].unique()}

# #########################
# REPRODUCE QLMC COMPARISON
# #########################

# Rename chains to have similar chains as on qlmc
ls_replace_chains = [['HYPER U', 'SUPER U'],
                     ['U EXPRESS', 'SUPER U'],
                     ['HYPER CASINO', 'CASINO'],
                     ["LES HALLES D'AUCHAN", 'AUCHAN']]
for old_chain, new_chain in ls_replace_chains:
  df_prices.loc[df_prices['store_chain'] == old_chain,
                'store_chain'] = new_chain

# Average price by product / chain
ls_col_gb = ['store_chain'] + ls_prod_cols + ['price']
df_chain_prod_prices = df_prices.groupby(ls_col_gb[:-1]).agg([len, np.mean])['price']
#df_chain_prod_prices.reset_index(level = 'store_chain', drop = False, inplace = True)

#ls_tup_chains = [('LECLERC', 'GEANT CASINO'),
#                 ('LECLERC', 'CARREFOUR'),
#                 ('GEANT CASINO', 'CARREFOUR'),
#                 ('CARREFOUR', 'AUCHAN'),
#                 ('CARREFOUR', 'INTERMARCHE'),
#                 ('CARREFOUR', 'SUPER U'),
#                 ('AUCHAN', 'INTERMARCHE'),
#                 ('AUCHAN', 'SUPER U'),
#                 ('INTERMARCHE', 'SUPER U')]

ls_tup_chains = [('LECLERC', 'GEANT CASINO'),
                 ('LECLERC', 'CARREFOUR'),
                 ('GEANT CASINO', 'CARREFOUR'),
                 ('SUPER U', 'AUCHAN'),
                 ('SUPER U', 'INTERMARCHE'),
                 ('SUPER U', 'CARREFOUR'),
                 ('AUCHAN', 'INTERMARCHE'),
                 ('AUCHAN', 'CARREFOUR'),
                 ('INTERMARCHE', 'CARREFOUR')]

ls_res = []
for chain_a, chain_b in ls_tup_chains:
  df_chain_a = df_chain_prod_prices.loc[(chain_a),:]
  df_chain_b = df_chain_prod_prices.loc[(chain_b),:]
  
  df_duel = pd.merge(df_chain_a,
                     df_chain_b,
                     left_index = True,
                     right_index = True,
                     how = 'inner',
                     suffixes = (u'_{:s}'.format(chain_a), u'_{:s}'.format(chain_b)))
  
  df_duel_sub = df_duel[(df_duel['len_{:s}'.format(chain_a)] >= 20) &\
                        (df_duel['len_{:s}'.format(chain_b)] >= 20)].copy()
  
  df_duel_sub['diff'] = df_duel_sub['mean_{:s}'.format(chain_b)] -\
                          df_duel_sub['mean_{:s}'.format(chain_a)]
  
  df_duel_sub['pct_diff'] = (df_duel_sub['mean_{:s}'.format(chain_b)] /\
                              df_duel_sub['mean_{:s}'.format(chain_a)] - 1)*100

  print()
  print(u'Replicate QLMC comparison: {:s} vs {:s}'.format(chain_a, chain_b))
  res = (df_duel_sub['mean_{:s}'.format(chain_b)].mean().round(2) /\
           df_duel_sub['mean_{:s}'.format(chain_a)].mean().round(2) - 1) * 100
  
  # Save both nb stores of chain b and res
  nb_stores_a = len(df_prices[df_prices['store_chain'] ==\
                                chain_a][store_col].drop_duplicates())
  nb_stores_b = len(df_prices[df_prices['store_chain'] ==\
                                chain_b][store_col].drop_duplicates())
  nb_prods = len(df_duel_sub)
  pct_a_wins = len(df_duel_sub[df_duel_sub['diff'] > 10e-3]) / float(nb_prods) * 100
  pct_b_wins = len(df_duel_sub[df_duel_sub['diff'] < -10e-3]) / float(nb_prods) * 100
  pct_draws = len(df_duel_sub[df_duel_sub['diff'].abs() <= 10e-3]) / float(nb_prods) * 100
  # Save both nb stores of chain b and res
  ls_res.append([chain_a,
                 chain_b,
                 nb_stores_a,
                 nb_stores_b,
                 nb_prods,
                 res,
                 pct_a_wins,
                 pct_b_wins,
                 pct_draws])

  percentiles = [0.1, 0.25, 0.5, 0.75, 0.9]
  print(df_duel_sub[['diff', 'pct_diff']].describe(percentiles = percentiles))

  # Manipulate or assume consumer is somewhat informed
  df_duel_sub.sort('pct_diff', ascending = False, inplace = True)
  df_duel_sub = df_duel_sub[len(df_duel_sub)/5:]
  res_2 = (df_duel_sub['mean_{:s}'.format(chain_b)].mean().round(2) /\
           df_duel_sub['mean_{:s}'.format(chain_a)].mean().round(2) - 1) * 100
  
  print()
  print(u'Aggregate comparison vs. Leclerc: {:.1f}%'.format(res))
  print(u'After manip against Leclerc: {:.1f}%'.format(res_2))

##print df_duel[0:10].to_string()

df_res = pd.DataFrame(ls_res,
                      columns = [u'Chain_A',
                                 u'Chain_B',
                                 u'Nb stores A',
                                 u'Nb stores B',
                                 u'Nb prods',
                                 u'Compa B vs A',
                                 u'A wins (%)',
                                 u'B wins (%)',
                                 u'Draws (%)'])

print()
print(df_res.to_string())
