#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import timeit

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

#df_prices = pd.read_csv(os.path.join(path_built_201503_csv,
#                                     'df_prices.csv'),
#                        encoding = 'utf-8')
#ls_prod_cols = ['section', 'family', 'product']
#store_col = 'store_id'

ls_qlmc_dates = ['201405',
                 '201409',
                 '201503']

date_str = ls_qlmc_dates[0]

df_prices = pd.read_csv(os.path.join(path_built_201415_csv,
                                     'df_qlmc_{:s}.csv'.format(date_str)),
                        encoding = 'utf-8')


ls_prod_cols = ['ean', 'product']
store_col = 'store_name'

if date_str == '201503':
  ls_prod_cols = ['section', 'family', 'product']
  store_col = 'store_id'

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
ls_compare_chains = [['LECLERC', chain] for chain in ls_some_chains\
                                        if chain in df_prices['store_chain'].unique()]
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

  print()
  print(u'Replicate QLMC comparison: {:s} vs {:s}'.format(chain_a, chain_b))
  res = (df_duel_sub['mean_{:s}'.format(chain_b)].mean().round(2) /\
           df_duel_sub['mean_{:s}'.format(chain_a)].mean().round(2) - 1) * 100
  
  # Save both nb stores of chain b and res
  nb_stores = len(df_prices[df_prices['store_chain'] ==\
                                chain_b][store_col].drop_duplicates())
  nb_prods = len(df_duel_sub)
  pct_a_wins = len(df_duel_sub[df_duel_sub['diff'] > 10e-4]) / float(nb_prods) * 100
  pct_b_wins = len(df_duel_sub[df_duel_sub['diff'] < -10e-4]) / float(nb_prods) * 100
  pct_draws = len(df_duel_sub[df_duel_sub['diff'].abs() <= 10e-4]) / float(nb_prods) * 100
  # Save both nb stores of chain b and res
  ls_res.append([chain_b,
                 nb_stores,
                 res,
                 nb_prods,
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

# todo:
# add precision in price comparison: product family level rank reversals
# enrich compara dataframe: distance, brands, competition/environement vars
# try to account for dispersion
# also investigate link between dispersion and price levels?
# do same exercise with non leclerc pairs (control for differentiation)
# would be nice to check if products on which leclerc is beaten are underpriced vs market

dict_qlmc_official = {}

dict_qlmc_official['201503'] = [['AUCHAN'          ,  140,  125,  '7.6%'],
                                ['CARREFOUR'       ,  226,  188,  '7.8%'],
                                ['CARREFOUR MARKET',  930,  421, '13.5%'],
                                ['CASINO'          ,  388,  151, '16.7%'],
                                ['CORA'            ,   58,   58, '10.2%'],
                                ['GEANT CASINO'    ,  108,  108,  '1.8%'],
                                ['LECLERC'         ,  581,  581,      ''],
                                ['INTERMARCHE'     , 1815, 1022,  '7.0%'],
                                ['SIMPLY MARKET'   ,  303,   50, '12.9%'],
                                ['SYSTEME U'       , 1044,  632,  '6.7%']]

dict_qlmc_official['201409'] = [['AUCHAN'          ,  140,    108,  '6.0%'],
                                ['CARREFOUR'       ,  226,    180,  '2.6%'],
                                ['CARREFOUR MARKET',  930,    210, '12.0%'],
                                ['CASINO'          ,  388, np.nan,      ''],
                                ['CORA'            ,   58,     54,  '9.3%'],
                                ['GEANT CASINO'    ,  108,     95,  '2.4%'],
                                ['LECLERC'         ,  581,    576,      ''],
                                ['INTERMARCHE'     , 1815,    470,  '6.2%'],
                                ['SIMPLY MARKET'   ,  303, np.nan,      ''],
                                ['SYSTEME U'       , 1044,    336,  '5.3%']]

dict_qlmc_official['201402'] = [['AUCHAN'          ,  140,    107,  '5.5%'],
                                ['CARREFOUR'       ,  226,    182,  '3.0%'],
                                ['CARREFOUR MARKET',  930,    208,  '8.8%'],
                                ['CASINO'          ,  388, np.nan,      ''],
                                ['CORA'            ,   58,     54, '10.1%'],
                                ['GEANT CASINO'    ,  108,     94,  '2.9%'],
                                ['LECLERC'         ,  581,    572,      ''],
                                ['INTERMARCHE'     , 1815,    458,  '3.8%'],
                                ['SIMPLY MARKET'   ,  303, np.nan,      ''],
                                ['SYSTEME U'       , 1044,    332,  '4.6%']]

dict_qlmc_official['201405'] = dict_qlmc_official['201402'] # a bit of a delay...

df_recap = pd.DataFrame(dict_qlmc_official.get(date_str, None),
                        columns = [u'Chain',
                                   u'Nb stores (LSA)',
                                   u'Nb stores (QLMC)',
                                   u'COMP vs. LEC'])
df_recap.set_index(u'Chain', inplace = True)

# Merge with my results
df_res = pd.DataFrame(ls_res,
                      columns = [u'Chain',
                                 u'Nb stores (data)',
                                 u'COMP vs. LEC (data)',
                                 u'Nb prods',
                                 u'LEC wins (%)',
                                 u'COMP wins (%)',
                                 u'DRAWS (%)'])
df_res.set_index(u'Chain', inplace = True)
df_res.rename(index = {u'SUPER U' : u'SYSTEME U'}, inplace = True)
df_res[u'COMP vs. LEC (data)'].apply(lambda x: u'{:.1f}%'.format(x))
df_res.loc[u'LECLERC', u'Nb stores (data)'] =\
              len(df_prices[df_prices['store_chain'] ==\
                              u'LECLERC'][store_col].drop_duplicates())

df_recap = pd.merge(df_recap,
                    df_res,
                    left_index = True,
                    right_index = True,
                    how = 'outer')

pd.set_option('float_format', '{:,.0f}'.format)

print()
print(u'Summary of {:s} national comparisons:'.format(date_str))
print(df_recap.to_string(formatters = {u'COMP vs. LEC (data)' : format_float_float,
                                       u'LEC wins (%)' : format_float_float,
                                       u'COMP wins (%)' : format_float_float,
                                       u'DRAWS (%)': format_float_float}))
