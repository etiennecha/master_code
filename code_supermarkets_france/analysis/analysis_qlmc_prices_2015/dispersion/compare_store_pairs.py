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
from functions_generic_qlmc import *
import matplotlib.pyplot as plt
import textwrap
import timeit
import numpy as np
import scipy as sp
import scipy.stats

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)

# #############
# LOAD DATA
# #############

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
print u'\nExample of comparison displayed on QLMC:'
print df_qlmc_comparisons[~df_qlmc_comparisons['qlmc_nb_obs'].isnull()].iloc[0]

# Replicate comparison

lec_chain = 'LECLERC'
lec_id, comp_id, comp_chain = 'centre-e-leclerc-saint-gregoire',\
                              'geant-casino-saint-gregoire',\
                              'GEANT CASINO'

#lec_id, comp_id, comp_chain =\
#   df_qlmc_comparisons[~df_qlmc_comparisons['qlmc_nb_obs'].isnull()]\
#                      .iloc[0][['lec_id', 'comp_id', 'comp_chain']].values

start = timeit.default_timer()
df_lec  = dict_chain_dfs[lec_chain]\
                        [dict_chain_dfs[lec_chain]['store_id'] == lec_id].copy()
df_comp = dict_chain_dfs[comp_chain]\
                        [dict_chain_dfs[comp_chain]['store_id'] == comp_id].copy()
print u'Time to select', timeit.default_timer() - start

start = timeit.default_timer()
df_duel = pd.merge(df_lec,
                   df_comp,
                   how = 'inner',
                   on = ['section', 'family', 'product'],
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

print scipy.stats.ttest_1samp(df_duel['diff'].values, 0)

def mean_confidence_interval(data, confidence=0.95):
  a = 1.0*np.array(data)
  n = len(a)
  m, se = np.mean(a), scipy.stats.sem(a)
  h = se * sp.stats.t._ppf((1+confidence)/2., n-1)
  return m, m-h, m+h

print mean_confidence_interval(df_duel['diff'].values)
