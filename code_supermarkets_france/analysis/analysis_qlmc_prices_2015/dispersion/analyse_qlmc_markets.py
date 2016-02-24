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

ls_keep_stores = df_prices['store_id'].unique()
dict_markets = {}
for i, row in df_qlmc_comparisons.iterrows():
  if (row['lec_id'] in ls_keep_stores) and\
     (row['comp_id'] in ls_keep_stores):
    dict_markets.setdefault(row['lec_id'], []).append(row['comp_id'])

# see if quick enough without using dict_chain_dfs
ls_df_markets = []
for lec_id, ls_comp_id in dict_markets.items()[0:10]:
  if ls_comp_id:
    df_market = df_prices[df_prices['store_id'] == lec_id]\
                      [['section', 'family', 'product', 'price']]
    for comp_id in ls_comp_id:
      df_comp = df_prices[df_prices['store_id'] == comp_id]
      df_market = pd.merge(df_market,
                           df_comp[['section', 'family', 'product', 'price']],
                           on = ['section', 'family', 'product'],
                           suffixes = ('', '_{:s}'.format(comp_id)),
                           how = 'inner')
    # do before?
    df_market.set_index(['section', 'family', 'product'], inplace = True)
    df_market.rename(columns = {'price' : 'price_{:s}'.format(lec_id)},
                     inplace = True)
    df_market.columns = [x[6:] for x in df_market.columns] # get rid of 'price_'
    ls_df_markets.append(df_market)

# Aggregate stats: basket with all products
nb_products = len(df_market) # check enough products
agg_sum = df_market.sum() # dispersion in total sum
agg_range = agg_sum.max() - agg_sum.min()
agg_range_pct = agg_range / agg_sum.mean()
agg_gfs = agg_sum.mean() - agg_sum.min()
agg_gfs_pct = agg_gfs / agg_sum.mean()

# Dispersion by product
ls_cols = df_market.columns # keep cuz gona add columns
df_market['mean'] = df_market.mean(1)
df_market['range'] = df_market[ls_cols].max(1) - df_market[ls_cols].min(1)
df_market['range_pct'] = df_market['range'] / df_market[ls_cols].mean(1)
df_market['gfs'] = df_market[ls_cols].mean(1) - df_market[ls_cols].min(1)
df_market['gfs_pct'] = df_market['gfs'] / df_market[ls_cols].mean(1)
df_market['std'] = df_market[ls_cols].std(1)
df_market['cv'] = df_market[ls_cols].std(1) / df_market[ls_cols].mean(1)

print()
print('Product dispersion summary stats')
print(df_market[['mean', 'range', 'range_pct', 'gfs', 'gfs_pct', 'std', 'cv']].describe())

# Ranking within market?
# http://stackoverflow.com/questions/21188151/pandas-getting-the-name-of-the-minimum-column
df_market['cheapest'] = df_market[ls_cols].T.idxmin()
df_market['priciest'] = df_market[ls_cols].T.idxmax()

print()
print('Cheapest store (basket share)')
print(df_market['cheapest'].value_counts(normalize = 1))

print()
print('Priciest store (basket share)')
print(df_market['priciest'].value_counts(normalize = 1))

# todo: compare with aggregate result
# todo: check if cheapest always have higher share than priciest?
# todo: check avg percentage of time cheapest is most expensive and vice versa
