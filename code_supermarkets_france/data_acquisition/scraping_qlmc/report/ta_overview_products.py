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
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import textwrap

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_qlmc_scraped = os.path.join(path_data,
                                  'data_qlmc',
                                  'data_source',
                                  'data_scraped')

path_csv = os.path.join(path_data,
                        'data_qlmc',
                        'data_built',
                        'data_csv')

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'qlmc_scraped',
                                     'df_stores.csv'),
                        encoding = 'utf-8')

df_comp = pd.read_csv(os.path.join(path_csv,
                                   'qlmc_scraped',
                                   'df_competitors.csv'),
                      encoding = 'utf-8')

df_france = pd.read_csv(os.path.join(path_csv,
                                     'qlmc_scraped',
                                     'df_france.csv'),
                        encoding = 'utf-8')

## Most common products
se_prod_vc = df_france['product'].value_counts()
#print u'\nShow most common products'
#print se_prod_vc[0:30].to_string()

## Most common chains
se_chain_vc = df_france['chain'].value_counts()
#print u'\nShow most common chains'
#print se_chain_vc[0:30].to_string()

## todo: check for each trigram if name starts with cor. dict entry
#dict_chains = {'ITM' : 'INTERMARCHE SUPER',
#               'USM' : 'SUPER U',
#               'CAR' : 'CARREFOUR',
#               'CRM' : 'CARREFOUR MARKET', # or MARKET
#               'AUC' : 'AUCHAN',
#               'GEA' : 'GEANT CASINO',
#               'COR' : 'CORA',
#               'SCA' : 'CASINO',
#               'HSM' : 'HYPER U',
#               'SIM' : 'SIMPLY MARKET',
#               'MAT' : 'SUPERMARCHE MATCH',
#               'HCA' : 'HYPER CASINO',
#               'UEX' : 'U EXPRESS',
#               'ATA' : 'ATAC',
#               'CAS' : 'CASINO',
#               'UHM' : 'HYPER U',
#               'MIG' : 'MIGROS',
#               'G20' : 'G 20',
#               'REC' : 'RECORD',
#               'HAU' : "LES HALLES D'AUCHAN"}

# todo: transform in one line with groupby
df_france.set_index('product', inplace = True)
df_france['freq_prod'] = se_prod_vc
df_france.reset_index(inplace = True)

df_u_prod = df_france.drop_duplicates('product')
df_u_prod.sort('freq_prod', ascending = False, inplace = True)
df_u_prod = df_u_prod[['family', 'subfamily', 'product', 'freq_prod']][0:50]

df_u_prod.set_index(['family', 'subfamily', 'product'], inplace = True)
df_u_prod.sort_index(inplace = True)
print df_u_prod.to_string()

# ###################
# COMPARE TWO STORES
# ###################

# todo: use Leclerc's markets btw

# Build DataFrame with two (or more) store prices

store_a, store_b = u'atac-autun', u'atac-auxerre'
df_sub = df_france[df_france['store_id'].isin([store_a, store_b])]

#df_comparison_prelim = df_sub[['product', 'store_id', 'price']].\
#                         pivot('product', 'store_id', 'price')

df_comparison =  pd.pivot_table(df_sub,
                                index = ['family', 'subfamily', 'product'],
                                columns = ['store_id'],
                                values = 'price',
                                aggfunc = 'min')


## Slicing with Multi-Index DataFrame
#print df_comparison.ix[(u'Aliments bébé et Diététique', u'Aliments Bébé')].to_string()
#print df_comparison.loc[(slice(None), u'Aliments Bébé'),:].to_string()

# Comparison
# df_comparison.reset_index(level = 'product', drop = False, inplace = True)

store_a, store_b = 'atac-autun', 'atac-auxerre'

cust = lambda g: (df_comparison.ix[g.index][store_a] -\
                    df_comparison.ix[g.index][store_b]).sum()

def nb_products(df_temp):
  return len(df_temp.index)

def value_total(df_temp):
  return df_comparison.ix[df_temp.index][[store_a, store_b]].mean(1).sum()

def mean_value(df_temp):
  return df_comparison.ix[df_temp.index][[store_a, store_b]].mean(1).mean()

#def value_diff(df_temp):
#  return (df_comparison.ix[df_temp.index][store_a] -\
#            df_comparison.ix[df_temp.index][store_b]).sum()
#
#def abs_value_diff(df_temp):
#  return (df_comparison.ix[df_temp.index][store_a] -\
#            df_comparison.ix[df_temp.index][store_b]).abs().sum()

def mean_value_diff(df_temp):
  return (df_comparison.ix[df_temp.index][store_a] -\
            df_comparison.ix[df_temp.index][store_b]).mean()

def mean_pct_diff(df_temp):
  return (df_comparison.ix[df_temp.index][store_a] /\
            df_comparison.ix[df_temp.index][store_b] - 1).mean()

def mean_abs_value_diff(df_temp):
  return (df_comparison.ix[df_temp.index][store_a] -\
            df_comparison.ix[df_temp.index][store_b]).abs().mean()

def mean_abs_pct_diff(df_temp):
  return (df_comparison.ix[df_temp.index][[store_a, store_b]].min(1) /\
            df_comparison.ix[df_temp.index][[store_a, store_b]].max(1) - 1).abs().mean()

def nb_a_cheaper(df_temp):
  return (df_comparison.ix[df_temp.index][store_a] <\
           df_comparison.ix[df_temp.index][store_b]).sum()

def nb_b_cheaper(df_temp):
  return (df_comparison.ix[df_temp.index][store_a] >\
           df_comparison.ix[df_temp.index][store_b]).sum()

def nb_draw(df_temp):
  return (df_comparison.ix[df_temp.index][store_a] ==\
           df_comparison.ix[df_temp.index][store_b]).sum()

def pct_rank_reversals(df_temp):
  return min((df_comparison.ix[df_temp.index][store_a] >\
                df_comparison.ix[df_temp.index][store_b]).sum(),
              (df_comparison.ix[df_temp.index][store_a] <\
                    df_comparison.ix[df_temp.index][store_b]).sum()) /\
           float(len(df_temp.index))

def pct_draws(df_temp):
  return (df_comparison.ix[df_temp.index][store_a] ==\
           df_comparison.ix[df_temp.index][store_b]).sum() /\
           float(len(df_temp.index))

df_comparison.dropna(inplace = True)
df_comparison.reset_index(drop = False, inplace = True)

ls_func_1 = [nb_products,
             value_total,
             mean_value_diff,
             mean_pct_diff,
             mean_abs_value_diff,
             mean_abs_pct_diff,
             nb_a_cheaper,
             nb_b_cheaper,
             nb_draw]

ls_func_2 = [nb_products,
             mean_value,
             mean_value_diff,
             mean_pct_diff,
             mean_abs_value_diff,
             mean_abs_pct_diff,
             pct_rank_reversals,
             pct_draws]

df_res_pre = df_comparison[['family', store_a, store_b]]\
               .groupby('family').agg({store_a : ls_func_1})[store_a]

print u'\nFirst set of functions:'
print df_res_pre.to_string()

df_res = df_comparison[['family', store_a, store_b]]\
           .groupby('family').agg({store_a : ls_func_2})[store_a]

print u'\nSecond set of functions:'
print df_res.to_string()

print u'\nSecond set of functions w/ all products:'
print df_comparison.groupby(lambda idx: 0).agg(ls_func_2)['family'].T.to_string()

# todo: 
# stack all competitor pairs and use groupby to make global stats
# could keep rayons btw?
# for this: loop over leclerc competitor pairs and index with pair

print u'Nb stores by chain:'
print df_france[['chain', 'store_id']]\
        .drop_duplicates(['chain', 'store_id']).groupby('chain').agg('size')

import itertools
some_chain = 'ATA'
df_chain = df_france[df_france['chain'] == some_chain]
ls_chain_stores = df_chain['store_id'].unique().tolist()
ls_chain_pairs = [x for x in itertools.combinations(ls_chain_stores, 2)]

ls_df_comparison = []
for store_a, store_b in ls_chain_pairs:
  df_sub = df_chain[df_chain['store_id'].isin([store_a, store_b])]
  df_comparison =  pd.pivot_table(df_sub,
                                  index = ['family', 'subfamily', 'product'],
                                  columns = ['store_id'],
                                  values = 'price',
                                  aggfunc = 'min')
  df_comparison.rename(columns = {store_a : 'price_a',
                                  store_b : 'price_b'},
                       inplace = True)
  df_comparison['store_pair'] = u'{:s} vs. {:s}'.format(store_a, store_b)
  ls_df_comparison.append(df_comparison)

df_chain_comparison = pd.concat(ls_df_comparison)
df_chain_comparison.dropna(inplace = True)
df_chain_comparison.reset_index(drop = False, inplace = True)

store_a, store_b = 'price_a', 'price_b' # global vars in comp functions
df_comparison = df_chain_comparison # global var in comp functions
df_res_chain = df_chain_comparison[['store_pair', store_a, store_b]]\
                 .groupby('store_pair').agg({store_a : ls_func_2})[store_a]

print u'\nOverview chain pairs:'
print df_res_chain.to_string()

# todo: add distance between pairs
