#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
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
                                     'df_prices.csv'),
                        encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str,
                                 'c_insee' : str},
                        encoding = 'utf-8')

df_qlmc_comparisons = pd.read_csv(os.path.join(path_built_csv,
                                               'df_qlmc_competitors.csv'),
                                  encoding = 'utf-8')

# Costly to search by store_id within df_prices
# hence first split df_prices in chain dataframes
dict_chain_dfs = {chain: df_prices[df_prices['store_chain'] == chain]\
                    for chain in df_prices['store_chain'].unique()}

# #########################
# REPRODUCE QLMC COMPARISON
# #########################

# Pick any scraped comparison
print()
print(u'Example of comparison displayed on QLMC:')
print(df_qlmc_comparisons[~df_qlmc_comparisons['qlmc_nb_obs'].isnull()].iloc[0])

# Replicate comparison

lec_chain = 'LECLERC'
lec_id, comp_id, comp_chain =\
   df_qlmc_comparisons[~df_qlmc_comparisons['qlmc_nb_obs'].isnull()]\
                      .iloc[2][['lec_id', 'comp_id', 'comp_chain']].values

start = timeit.default_timer()
df_lec  = dict_chain_dfs[lec_chain]\
                        [dict_chain_dfs[lec_chain]['store_id'] == lec_id].copy()
df_comp = dict_chain_dfs[comp_chain]\
                        [dict_chain_dfs[comp_chain]['store_id'] == comp_id].copy()
print(u'Time to select', timeit.default_timer() - start)

start = timeit.default_timer()
df_duel = pd.merge(df_lec,
                   df_comp,
                   how = 'inner',
                   on = ['section', 'family', 'product'],
                   suffixes = ['_lec', '_comp'])
# df_duel.drop(['chain_lec', 'chain_comp'], axis = 1, inplace = True)
print(u'Time to merge', timeit.default_timer() - start)

print()
print(u'Replication of comparison:')
print((df_duel['price_comp'].sum() / df_duel['price_lec'].sum() - 1) * 100)

print()
print(u'Overview product prices:')
print(df_duel[['price_lec', 'price_comp']].describe())

print()
print(u'Average on product by product comparison')
# (todo: add weighted pct (Leclerc's method?))
df_duel['diff'] = df_duel['price_comp'] - df_duel['price_lec']
df_duel['pct_diff'] = df_duel['price_comp'] / df_duel['price_lec'] - 1
print(df_duel[['diff', 'pct_diff']].describe())

print()
print(u'Desc of abs value of percent difference:')
print(df_duel['pct_diff'].abs().describe(\
        percentiles = [0.1, 0.25, 0.5, 0.75, 0.9]))

#df_duel.sort('diff', ascending = False, inplace = True)
#print df_duel[0:10].to_string()

# ############
# LOOP
# ############

start = timeit.default_timer()
ls_rows_compa = []
lec_chain = 'LECLERC'
lec_id_save = None
for lec_id, comp_id, comp_chain\
  in df_qlmc_comparisons[~df_qlmc_comparisons['qlmc_nb_obs'].isnull()]\
       [['lec_id', 'comp_id', 'comp_chain']].values:
  
  ##before split of df_prices       
  #df_lec  = df_prices[df_prices['store_id'] == lec_id].copy()
  #df_comp = df_prices[df_prices['store_id'] == comp_id].copy()
  
  ##before taking advantage of order
  #df_lec  = dict_chain_dfs[lec_chain][dict_chain_dfs[lec_chain]['store_id'] == lec_id]
  #df_comp = dict_chain_dfs[comp_chain][dict_chain_dfs[comp_chain]['store_id'] == comp_id]
  
  # taking advantage of order requires caution on first loop
  if lec_id != lec_id_save:
    df_lec  = dict_chain_dfs[lec_chain]\
                            [dict_chain_dfs[lec_chain]['store_id'] == lec_id]
    lec_id_save = df_lec['store_id'].iloc[0]
  df_comp = dict_chain_dfs[comp_chain]\
                          [dict_chain_dfs[comp_chain]['store_id'] == comp_id]
  
  # todo: see if need family and subfamily for matching (not much chge)
  df_duel = pd.merge(df_lec,
                     df_comp,
                     how = 'inner',
                     on = ['section', 'family', 'product'],
                     suffixes = ['_lec', '_comp'])
  
  ## manipulation
  #df_duel['diff'] = df_duel['price_comp'] - df_duel['price_lec']
  #df_duel.sort('diff', ascending = False, inplace = True)
  #df_duel = df_duel[int(len(df_duel)*0.2):]
  
  ls_rows_compa.append((lec_id,
                        comp_id,
                        comp_chain,
                        len(df_duel),
                        len(df_duel[df_duel['price_lec'] < df_duel['price_comp']]),
                        len(df_duel[df_duel['price_lec'] > df_duel['price_comp']]),
                        len(df_duel[df_duel['price_lec'] == df_duel['price_comp']]),
                        (df_duel['price_comp'].sum() / df_duel['price_lec'].sum() - 1) * 100,
                        df_duel['price_comp'].mean() - df_duel['price_lec'].mean()))

df_repro_compa = pd.DataFrame(ls_rows_compa,
                              columns = ['lec_id',
                                         'comp_id',
                                         'comp_chain',
                                         'nb_obs',
                                         'nb_lec_wins',
                                         'nb_comp_wins',
                                         'nb_draws',
                                         'pct_compa',
                                         'mean_compa'])
print(u'Time for loop', timeit.default_timer() - start)



df_repro_compa['rr'] = df_repro_compa['nb_comp_wins'] /\
                         df_repro_compa['nb_obs'] * 100

df_repro_compa.loc[df_repro_compa['nb_comp_wins'] >\
                     df_repro_compa['nb_lec_wins'],
                   'rr'] = df_repro_compa['nb_lec_wins'] /\
                             df_repro_compa['nb_obs'] * 100

df_repro_compa['pct_draws'] = df_repro_compa['nb_draws'] / df_repro_compa['nb_obs']* 100

ls_pctiles = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
print()
print(u'Overview of reproduced comparisons:')
print(df_repro_compa.describe(percentiles = ls_pctiles).to_string())

print()
print(u'Overview of pair with similar prices:')
print(df_repro_compa[df_repro_compa['pct_draws'] >= 30].to_string())

import matplotlib.pyplot as plt
#df_repro_compa['pct_compa_abs'] = df_repro_compa['pct_compa'].abs()
#df_repro_compa[df_repro_compa['pct_compa' > 0].plot(kind = 'scatter', x = 'pct_compa', y = 'rr')
fig = plt.figure()
ax = fig.add_subplot(111)
ax.scatter(x=df_repro_compa['pct_compa'].values, y=df_repro_compa['rr'])
ax.grid()
ax.set_xlim([0, 50])
ax.set_ylim([0, 0.5])
plt.show()

# todo:
# add precision in price comparison: product family level rank reversals
# enrich compara dataframe: distance, brands, competition/environement vars
# try to account for dispersion
# also investigate link between dispersion and price levels?
# do same exercise with non leclerc pairs (control for differentiation)
# would be nice to check if products on which leclerc is beaten are underpriced vs market

df_delta = pd.merge(df_qlmc_comparisons[['lec_id', 'comp_id',
                                        'qlmc_nb_obs', 'qlmc_pct_compa',
                                        'qlmc_winner']],
                   df_repro_compa[['lec_id', 'comp_id', 'nb_obs', 'pct_compa']],
                   on = ['lec_id', 'comp_id'],
                   how = 'left')

# Ok with comparisons when Leclerc loses
print()
print(u'Check comparisons when Leclerc loses:')
print(df_delta[df_delta['pct_compa'] <= 0].to_string())
print(len(df_delta[df_delta['qlmc_winner'] == 'OTH']))

print(u'Check replication of qlmc comparisons:')
df_delta = df_delta[df_delta['pct_compa'] >= 0]
df_delta['delta'] = df_delta['qlmc_pct_compa'] - df_delta['pct_compa']
print(df_delta['delta'].describe())

# Summary by chain
ls_scs = ['AUCHAN',
          'CARREFOUR',
          'CARREFOUR MARKET',
          'CASINO',
          'CORA',
          'GEANT CASINO',
          'INTERMARCHE',
          'SIMPLY MARKET',
          'SUPER U']

ls_se_chain_desc =\
  [df_repro_compa[(df_repro_compa['comp_chain'] == store_chain) &\
                  (df_repro_compa['nb_obs'] >= 400)]['pct_compa'].describe()\
                      for store_chain in ls_scs]
df_su_chains = pd.concat(ls_se_chain_desc,
                         axis = 1,
                         keys = ls_scs)
pd.set_option('float_format', '{:,.1f}'.format)
print()
print(u'Summary by chain: comparison results:')
print(df_su_chains.T.to_string())

# Summary by chain: rr
ls_se_chain_rr = [df_repro_compa[df_repro_compa['comp_chain']\
                                     == store_chain]['rr'].describe()\
                        for store_chain in ls_scs]
df_chain_rr = pd.concat(ls_se_chain_rr,
                        axis = 1,
                        keys = ls_scs)
print()
print(u'Summary by chain: rank reversal results:')
print(df_chain_rr.T.to_string())

# Summary by chain / stats
dict_df_chain_stat = {}
for stat in ['rr', 'pct_draws']:
  ls_se_chain_stat = [df_repro_compa[df_repro_compa['comp_chain']\
                                         == store_chain][stat].describe()\
                            for store_chain in ls_scs]
  df_chain_stat = pd.concat(ls_se_chain_stat,
                            axis = 1,
                            keys = ls_scs)
  dict_df_chain_stat[stat] = df_chain_stat

print()
print(u'Summary by chain: pct_draws')
print(dict_df_chain_stat['pct_draws'].T.to_string())
