#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
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
                                     'df_prices_cleaned.csv'),
                        encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str,
                                 'c_insee' : str},
                        encoding = 'utf-8')

df_qlmc_comparisons = pd.read_csv(os.path.join(path_built_csv,
                                               'df_qlmc_competitors.csv'),
                                  encoding = 'utf-8')

df_prices['price_res'] = df_prices['price'] - df_prices['price_hat']
price_col = 'price_res'

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

merge_option = 'inner' # or 'outer'
# pbm with outer for now
# cheapest store cannot be cheapest on products it does not carry
# ok to check robustness of cheapest being sometimes most expensive etc.

# see if quick enough without using dict_chain_dfs
ls_df_markets = []
for lec_id, ls_comp_id in dict_markets.items():
  if ls_comp_id:
    df_market = dict_chain_dfs['LECLERC']\
                    [dict_chain_dfs['LECLERC']['store_id'] == lec_id]\
                         [['section', 'family', 'product', price_col]]
    for comp_id in ls_comp_id:
      store_chain = df_stores[df_stores['store_id'] == comp_id]['store_chain'].iloc[0]
      df_comp = dict_chain_dfs[store_chain]\
                    [dict_chain_dfs[store_chain]['store_id'] == comp_id]
      df_market = pd.merge(df_market,
                           df_comp[['section', 'family', 'product', price_col]],
                           on = ['section', 'family', 'product'],
                           suffixes = ('', '_{:s}'.format(comp_id)),
                           how = merge_option)
    # do before?
    df_market.set_index(['section', 'family', 'product'], inplace = True)
    df_market.rename(columns = {price_col : '{:s}_{:s}'.format(price_col, lec_id)},
                     inplace = True)
    df_market.columns = [x[6:] for x in df_market.columns] # get rid of 'price_'
    # if outer merge: keep only products carried by 67% stores or more
    if merge_option == 'outer':
      nb_stores = len(df_market.columns)
      df_market = df_market[df_market.count(1) >= nb_stores * 0.67]
    # df not saved if empty else pbm with next loop
    if len(df_market) != 0:
      ls_df_markets.append(df_market)

ls_market_rows = []
for df_market in ls_df_markets:
  
  # Aggregate stats: basket with all products
  nb_stores = len(df_market.columns)
  nb_prods = len(df_market) # check enough products
  agg_sum = df_market.sum() # dispersion in total sum
  ls_cols_ascending = agg_sum.sort(ascending = True, inplace = False).index.tolist()
  ls_cols_descending = agg_sum.sort(ascending = False, inplace = False).index.tolist()
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
  
  #print()
  #print('Product dispersion summary stats')
  #print(df_market[['mean', 'range', 'range_pct', 'gfs', 'gfs_pct', 'std', 'cv']].describe())
  
  # Ranking within market
  # Handling of equalities is a bit tricky (less relevant with residuals probably)
  # http://stackoverflow.com/questions/21188151/pandas-getting-the-name-of-the-minimum-column
  df_market['cheapest'] = df_market[ls_cols_ascending].T.idxmin()
  df_market['cheapest_2'] = df_market[ls_cols_descending].T.idxmin()
  df_market['priciest'] = df_market[ls_cols_descending].T.idxmax()
  df_market['priciest_2'] = df_market[ls_cols_ascending].T.idxmax()
  se_cheapest_vc = df_market['cheapest'].value_counts(normalize = 1)
  se_priciest_vc = df_market['priciest'].value_counts(normalize = 1)
  se_cheapest_2_vc = df_market['cheapest_2'].value_counts(normalize = 1)
  se_priciest_2_vc = df_market['priciest_2'].value_counts(normalize = 1)

  if se_priciest_vc.index[0] not in se_cheapest_2_vc.index:
    se_cheapest_2_vc.ix[se_priciest_vc.index[0]] = 0.0
  if se_cheapest_vc.index[0] not in se_priciest_2_vc.index:
    se_priciest_2_vc.ix[se_cheapest_vc.index[0]] = 0.0
  
  ls_market_rows.append([df_market.columns[0],
                         nb_stores,
                         nb_prods,
                         agg_range_pct,
                         agg_gfs_pct,
                         df_market['range'].mean(),
                         df_market['range_pct'].mean(),
                         df_market['gfs'].mean(),
                         df_market['gfs_pct'].mean(),
                         df_market['cv'].mean(),
                         se_cheapest_vc.index[0],
                         se_cheapest_vc.iloc[0],
                         se_priciest_vc.index[0],
                         se_priciest_vc.iloc[0],
                         se_cheapest_2_vc.ix[se_priciest_vc.index[0]],
                         se_priciest_2_vc.ix[se_cheapest_vc.index[0]]])

lsd1 = ['agg_range_pct',
        'agg_gfs_pct',
        'range',
        'range_pct',
        'gfs',
        'gfs_pct',
        'cv']

lsd2 = ['cheapest_ct_id',
        'cheapest_ct_pct',
        'priciest_ct_id',
        'priciest_ct_pct',
        'priciest_ch_pct', # nb of products on which priciest is cheapest
        'cheapest_pr_pct'] # nb of products on which cheapest is priciest

df_su = pd.DataFrame(ls_market_rows,
                     columns = ['lec_id',
                                'nb_stores',
                                'nb_prods'] + lsd1 + lsd2)

df_su = df_su[(df_su['nb_prods'] >= 50) &\
              (df_su['nb_stores'] >= 3)]

if price_col not in ['price_res']:
  print()
  print('Stats des: markets with more than 50 products:')
  print(df_su.describe().to_string())
  
  print()
  print('Stats des: markets with more than 100 products:')
  print(df_su[df_su['nb_prods'] >= 100].describe().to_string())
  
  print()
  print('Stats des: markets with more than 100 products and 4 stores:')
  print(df_su[(df_su['nb_prods'] >= 100) &\
              (df_su['nb_stores'] >= 4)].describe().to_string())
  
  print()
  print('Markets with high dispersion')
  # inspect extreme priciest_ch_pct markets
  print(df_su[df_su['priciest_ch_pct'] >= 0.33].to_string())
  
  for df_market in ls_df_markets:
    if df_market.columns[0] == 'centre-e-leclerc-loudun':
      break
  
  print(df_market[df_market['cheapest_2'] != df_market['cheapest']][0:40].to_string())

else:
  # Lighter version when using price_res
  print()
  print(df_su[['nb_stores', 'nb_prods', 'range', 'gfs'] + lsd2].describe().to_string())

  for df_market in ls_df_markets:
    if df_market.columns[0] == 'res_centre-e-leclerc-loudun':
      break

# todo: run with raw prices and price residuals (several methods?)
# then: check link between price level and price dispersion
# also with nb stores (w/ real number?)
