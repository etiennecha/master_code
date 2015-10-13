#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import httplib
import urllib, urllib2
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
import timeit

def enc_json(data, path_file):
  with open(path_file, 'w') as f:
    json.dump(data, f)

def dec_json(path_file):
  with open(path_file, 'r') as f:
    return json.loads(f.read())

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_csv = os.path.join(path_data,
                        'data_supermarkets',
                        'data_built',
                        'data_qlmc_2015',
                        'data_csv_201503')

df_qlmc_comparisons = pd.read_csv(os.path.join(path_csv,
                                               'df_qlmc_competitors.csv'),
                                  encoding = 'utf-8')

df_prices = pd.read_csv(os.path.join(path_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

# Costly to search by store_id within df_prices
# hence first split df_prices in chain dataframes
dict_chain_dfs = {chain: df_prices[df_prices['chain'] == chain]\
                    for chain in df_prices['chain'].unique()}

# #########################
# REPRODUCE QLMC COMPARISON
# #########################

# Pick any scraped comparison
print u'\nExample of comparison displayed on QLMC:'
print df_qlmc_comparisons[~df_qlmc_comparisons['qlmc_nb_obs'].isnull()].iloc[0]

# Replicate comparison

lec_chain = 'LEC'
lec_id, comp_id, comp_chain = df_qlmc_comparisons[~df_qlmc_comparisons['qlmc_nb_obs'].isnull()]\
                                .iloc[0][['lec_id', 'comp_id', 'comp_chain']].values

start = timeit.default_timer()
df_lec  = dict_chain_dfs[lec_chain][dict_chain_dfs[lec_chain]['store_id'] == lec_id].copy()
df_comp = dict_chain_dfs[comp_chain][dict_chain_dfs[comp_chain]['store_id'] == comp_id].copy()
print u'Time to select', timeit.default_timer() - start

start = timeit.default_timer()
df_duel = pd.merge(df_lec,
                   df_comp,
                   how = 'inner',
                   on = ['family', 'subfamily', 'product'],
                   suffixes = ['_lec', '_comp'])
# df_duel.drop(['chain_lec', 'chain_comp'], axis = 1, inplace = True)
print u'Time to merge', timeit.default_timer() - start

print u'\nReplication of comparison:'
print (df_duel['price_comp'].sum() / df_duel['price_lec'].sum() - 1) * 100

print u'\nOverview product prices:'
print df_duel[['price_lec', 'price_comp']].describe()

print u'\nAverage on product by product comparison'
# (todo: add weighted pct (Leclerc's method?))
df_duel['diff'] = df_duel['price_comp'] - df_duel['price_lec']
df_duel['pct_diff'] = df_duel['price_comp'] / df_duel['price_lec'] - 1
print df_duel[['diff', 'pct_diff']].describe()

print u'\nDesc of abs value of percent difference:'
print df_duel['pct_diff'].abs().describe(\
        percentiles = [0.1, 0.25, 0.5, 0.75, 0.9])

#df_duel.sort('diff', ascending = False, inplace = True)
#print df_duel[0:10].to_string()

# ############
# LOOP
# ############

start = timeit.default_timer()
ls_rows_compa = []
lec_chain = 'LEC'
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
    df_lec  = dict_chain_dfs[lec_chain][dict_chain_dfs[lec_chain]['store_id'] == lec_id]
    lec_id_save = df_lec['store_id'].iloc[0]
  df_comp = dict_chain_dfs[comp_chain][dict_chain_dfs[comp_chain]['store_id'] == comp_id]
  
  # todo: see if need family and subfamily for matching (not much chge)
  df_duel = pd.merge(df_lec,
                     df_comp,
                     how = 'inner',
                     on = ['family', 'subfamily', 'product'],
                     suffixes = ['_lec', '_comp'])
  ls_rows_compa.append((lec_id,
                        comp_id,
                        len(df_duel),
                        len(df_duel[df_duel['price_lec'] < df_duel['price_comp']]),
                        len(df_duel[df_duel['price_lec'] > df_duel['price_comp']]),
                        len(df_duel[df_duel['price_lec'] == df_duel['price_comp']]),
                        (df_duel['price_comp'].sum() / df_duel['price_lec'].sum() - 1) * 100))

df_repro_compa = pd.DataFrame(ls_rows_compa,
                              columns = ['lec_id',
                                         'comp_id',
                                         'nb_obs',
                                         'nb_lec_wins',
                                         'nb_comp_wins',
                                         'nb_draws',
                                         'pct_compa'])
print u'Time for loop', timeit.default_timer() - start

ls_pctiles = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
print df_repro_compa['pct_compa'].describe(percentiles = ls_pctiles)

df_repro_compa['rr'] = df_repro_compa['nb_comp_wins'] /\
                         df_repro_compa['nb_obs'] * 100

df_repro_compa.loc[df_repro_compa['nb_comp_wins'] >\
                     df_repro_compa['nb_lec_wins'],
                   'rr'] = df_repro_compa['nb_lec_wins'] /\
                             df_repro_compa['nb_obs'] * 100

import matplotlib.pyplot as plt
df_repro_compa.plot(kind = 'scatter', x = 'pct_compa', y = 'rr')
plt.show()

# todo:
# add precision in price comparison: product family level rank reversals
# enrich compara dataframe: distance, brands, competition/environement vars
# try to account for dispersion
# also investigate link between dispersion and price levels?
# do same exercise with non leclerc pairs (control for differentiation)
# would be nice to check if products on which leclerc is beaten are underpriced vs market
