#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import timeit

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'))

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'))

df_qlmc_comparisons = pd.read_csv(os.path.join(path_built_csv,
                                               'df_qlmc_competitors.csv'))

# Costly to search by store_id within df_prices
# hence first split df_prices in chain dataframes
dict_chain_dfs = {chain: df_prices[df_prices['store_chain'] == chain]\
                    for chain in df_prices['store_chain'].unique()}

# #########################
# REPRODUCE QLMC COMPARISON
# #########################

# Can rename HYPER U to SUPER U to get similar groups as on website?
df_prices.loc[df_prices['store_chain'] == 'HYPER U', 'store_chain'] = 'SUPER U'
df_prices.loc[df_prices['store_chain'] == 'U EXPRESS', 'store_chain'] = 'SUPER U'
df_prices.loc[df_prices['store_chain'] == 'HYPER CASINO', 'store_chain'] = 'CASINO'
df_prices.loc[df_prices['store_chain'] == "LES HALLES D'AUCHAN", 'store_chain'] = 'CASINO'

# Average price by product / chain
ls_col_gb = ['store_chain', 'section', 'family', 'product', 'price']
df_chain_prod_prices = df_prices.groupby(ls_col_gb[:-1]).agg([len, np.mean])['price']
#df_chain_prod_prices.reset_index(level = 'store_chain', drop = False, inplace = True)

# Compare two chains (comment: displayed on website)
ls_some_chains = ['INTERMARCHE', # +7.0%
                  'SUPER U', # +6.7% for both hyper and super
                  'CARREFOUR MARKET', # +13.5%
                  'AUCHAN',  # +7.6%
                  #'HYPER U', # +6.7% for both hyper and super
                  'CORA', # +10.2%
                  'CARREFOUR', # +7.8%
                  'GEANT CASINO', #+1.8% (only Geant? also Hyper?)
                  'CASINO',  # +16.7%
                  'SIMPLY MARKET'] # +12.9%
ls_compare_chains = [['LECLERC', chain] for chain in ls_some_chains]
ls_res = []
for chain_a, chain_b in ls_compare_chains:
  # chain_a, chain_b = 'LECLERC', 'HYPER U
  df_chain_a = df_chain_prod_prices.loc[(chain_a),:]
  df_chain_b = df_chain_prod_prices.loc[(chain_b),:]
  # print df_test.loc[(slice(None), u'CENTRE E.LECLERC'),:].to_string()
  
  df_duel = pd.merge(df_chain_a,
                     df_chain_b,
                     left_index = True,
                     right_index = True,
                     how = 'inner',
                     suffixes = (u'_{:s}'.format(chain_a), u'_{:s}'.format(chain_b)))
  
  # Nb obs required varies by chain (figure below for october..)
  # Min 16 for CORA, Max 21 for Carrefour Market, Intermarche and Systeme U
  # Leclerc: 20, Auchan 19, Carrefour 19, Geant 18
  
  df_duel_sub = df_duel[(df_duel['len_{:s}'.format(chain_a)] >= 20) &\
                        (df_duel['len_{:s}'.format(chain_b)] >= 20)].copy()
  
  df_duel_sub['diff'] = df_duel_sub['mean_{:s}'.format(chain_b)] -\
                          df_duel_sub['mean_{:s}'.format(chain_a)]
  
  df_duel_sub['pct_diff'] = (df_duel_sub['mean_{:s}'.format(chain_b)] /\
                              df_duel_sub['mean_{:s}'.format(chain_a)] - 1)*100

  print u'\nReplicate QLMC comparison: {:s} vs {:s}'.format(chain_a, chain_b)
  res = (df_duel_sub['mean_{:s}'.format(chain_b)].mean().round(2) /\
           df_duel_sub['mean_{:s}'.format(chain_a)].mean().round(2) - 1) * 100
  print u'{:.1f}'.format(res)
  
  # Save both nb stores of chain b and res
  ls_res.append([len(df_prices[df_prices['store_chain'] ==\
                                 chain_b]['store_id'].unique()), res])

  percentiles = [0.1, 0.25, 0.5, 0.75, 0.9]
  print df_duel_sub[['diff', 'pct_diff']].describe(percentiles = percentiles)

  # Manipulate or assume consumer is somewhat informed
  df_duel_sub.sort('diff', ascending = False, inplace = True)
  df_duel_sub = df_duel_sub[len(df_duel_sub)/10:]
  res = (df_duel_sub['mean_{:s}'.format(chain_b)].mean().round(2) /\
           df_duel_sub['mean_{:s}'.format(chain_a)].mean().round(2) - 1) * 100
  print u'After manip against Leclerc: {:.1f}'.format(res)

##print df_duel[0:10].to_string()

# todo:
# add precision in price comparison: product family level rank reversals
# enrich compara dataframe: distance, brands, competition/environement vars
# try to account for dispersion
# also investigate link between dispersion and price levels?
# do same exercise with non leclerc pairs (control for differentiation)
# would be nice to check if products on which leclerc is beaten are underpriced vs market

ls_qlmc_official = [['AUCHAN', 140, 125, '7.6%'],
                    ['CARREFOUR', 226, 188, '7.8%'],
                    ['CARREFOUR MARKET', 930, 421, '13.5%'],
                    ['CASINO', 388, 151, '16.7%'],
                    ['CORA', 58, 58, '10.2%'],
                    ['GEANT CASINO', 108, 108, '1.8%'],
                    ['LECLERC', 581, 581, ''],
                    ['INTERMARCHE', 1815, 1022, '7%'],
                    ['SIMPLY MARKET', 303, 50, '12.9%'],
                    ['SYSTEME U', 1044, 632, '6.7%']]

df_recap = pd.DataFrame(ls_qlmc_official,
                        columns = ['Chain', 'Nb stores', 'Nb stores in QLMC', 'QLMC: vs. LEC'])
df_recap.set_index('Chain', inplace = True)

# Merge with my results
df_res = pd.DataFrame(ls_res,
                      index = ls_some_chains,
                      columns = ['Nb stores (my data)', 'vs. LEC (my data)'])
df_res.rename(index = {'SUPER U' : 'SYSTEME U'}, inplace = True)
df_res['vs. LEC (my data)'] =\
  df_res['vs. LEC (my data)'].apply(lambda x: u'{:.1f}%'.format(x))
df_res.ix['LECLERC'] = [len(df_prices[df_prices['store_chain'] ==\
                              'LECLERC']['store_id'].unique()), u'']

df_recap = pd.merge(df_recap,
                    df_res,
                    left_index = True,
                    right_index = True,
                    how = 'outer')

print()
print(df_recap.to_string())
