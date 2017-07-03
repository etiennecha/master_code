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

path_built_csv = os.path.join(path_data, 'data_supermarkets', 'data_built',
                              'data_qlmc_2014_2015', 'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

# Load 2014 data
ls_periods = ['201405', '201409']
dict_dfs = {}
for period in ls_periods:
  dict_dfs['qlmc_{:s}'.format(period)] = (
    pd.read_csv(os.path.join(path_built_csv,
                             'df_qlmc_{:s}.csv'.format(period)),
                dtype = {'ean' : str,
                         'id_lsa' : str}, # to update soon
                encoding = 'utf-8'))
ls_prod_cols = ['ean', 'product']
ls_store_cols = ['id_lsa', 'store_name']

# Load 2015 data
df_qlmc_2015 = pd.read_csv(os.path.join(path_built_csv,
                                        'df_prices_201503.csv'),
                           encoding = 'utf-8')
ls_prod_cols_2015 = ['section', 'family', 'product']
ls_store_cols_2015 = ['store_id'] # todo add id_lsa (and check it)

# store chain harmonization (as per qlmc)
ls_replace_chains = [['HYPER CASINO', 'CASINO'],
                     ['HYPER U', 'SUPER U'],
                     ['U EXPRESS', 'SUPER U'],
                     ["LES HALLES D'AUCHAN", 'AUCHAN'],
                     ['INTERMARCHE SUPER', 'INTERMARCHE'],
                     ['INTERMARCHE HYPER', 'INTERMARCHE'], # any?
                     ['MARKET', 'CARREFOUR MARKET'],
                     ['CENTRE E.LECLERC', 'LECLERC']]

ls_df_qlmc = [dict_dfs['qlmc_{:s}'.format(period)] for period in ls_periods]
ls_df_qlmc = ls_df_qlmc + [df_qlmc_2015]
for df_qlmc in ls_df_qlmc:
  for old_chain, new_chain in ls_replace_chains:
    df_qlmc.loc[df_qlmc['store_chain'] == old_chain,
                'store_chain'] = new_chain

## Robustness check: 3000 most detained products only
#se_prod_vc = df_qlmc[ls_prod_cols].groupby(ls_prod_cols).agg(len)
#ls_keep_products = [x[-1] for x in list(se_prod_vc[0:3000].index)]
#df_qlmc = df_qlmc[df_qlmc[ls_prod_cols[-1]].isin(ls_keep_products)]

# #######################
# PRODUCT RECONCILIATIONS
# #######################

# For 2014 pdf data: 
# - drop all lines if one ean for several prods: ambiguous for 2015 match
# - drop all lines if several ean for one prod: ambiguous for 2015 match
# - neglect risk that both could happen at the same time

# Clearly: something wrong with ean of new products in 201409
# Keep only products for which ean/product already known in 201405

# one product for several ean: 2601 => 2595 (-6 prods only)
ls_df_prods_2014 = []
ls_df_qlmc_2014 = []

df_qlmc_201405, df_qlmc_201409 = ls_df_qlmc[0], ls_df_qlmc[1]
df_prod_2014 = df_qlmc_201405[ls_prod_cols].drop_duplicates()

# pbm: several ean for one product (product not precise enough or mistake)
# then: drop all products / ean concerned
ls_ean_todrop_0 = (df_prod_2014[df_prod_2014.duplicated('product',keep = False)]
                               ['ean'].values.tolist())
df_prod_2014.drop_duplicates('product', keep = False)

# there are never several products for one ean
ls_ean_todrop_1 = (df_prod_2014[df_prod_2014.duplicated('ean', keep = False)]
                               ['ean'].values.tolist())
df_prod_2014.drop_duplicates('ean', keep = False)
  
# todo: drop all problematic ean
ls_ean_todrop = ls_ean_todrop_0 + ls_ean_todrop_1
df_qlmc_201405 = df_qlmc_201405[~df_qlmc_201405['ean'].isin(ls_ean_todrop)]

# merge left with next record (no need to touch df_prod_2014)
df_prod_201409 = df_qlmc_201409[ls_prod_cols].drop_duplicates()
ls_exclude_ean = (set(df_prod_201409['ean'].unique())
                    .difference(set(df_prod_2014['ean'].unique())))
df_qlmc_201409 = df_qlmc_201409[~df_qlmc_201409['ean'].isin(ls_exclude_ean)]
# make sure no ambiguitu (?)
df_prod_201409 = df_qlmc_201409[ls_prod_cols].drop_duplicates()
len(df_prod_201409[(df_prod_201409.duplicated('product', keep = False))])

df_qlmc_2014 = pd.merge(df_qlmc_201405[['id_lsa', 'ean', 'price', 'date']],
                        df_qlmc_201409[['id_lsa', 'ean', 'price', 'date']],
                        on = ['id_lsa', 'ean'],
                        suffixes = ('', '_1'),
                        how = 'outer')

# Check no pbm left

# For 2015 data:
# No need to check no product duplicate here (already done)
df_prod_2015 = df_qlmc_2015[ls_prod_cols_2015].drop_duplicates()

# nb product matches: 2282
df_prod_all = pd.merge(df_prod_2014,
                       df_prod_2015,
                       on = ['product'],
                       how = 'inner')

df_qlmc_2015 = pd.merge(df_qlmc_2015,
                        df_prod_all,
                        on = ls_prod_cols_2015,
                        how = 'inner')

# #####################
# STORE RECONCILIATIONS
# #####################

df_stores_2015 = pd.read_csv(os.path.join(path_built_csv,
                                          'df_stores_final_201503.csv'),
                             dtype = {'id_lsa' : str},
                             encoding = 'utf-8')

df_stores_pbm = df_stores_2015[(df_stores_2015.duplicated('id_lsa', keep = False))]

df_stores_2015.drop_duplicates('id_lsa', keep = False, inplace = True)

df_qlmc_2015 = pd.merge(df_qlmc_2015,
                        df_stores_2015[['store_id', 'id_lsa']],
                        on = 'store_id',
                        how = 'inner')

# Build proper df_stores_2015 w/ store_name, store_chain
df_stores_2015_temp = df_qlmc_2015[['store_chain', 'id_lsa']].drop_duplicates()
df_stores_2015_bu = df_stores_2015.copy()
df_stores_2015 = pd.merge(df_stores_2015_temp,
                          df_stores_2015[['store_name', 'id_lsa']],
                          on = 'id_lsa',
                          how = 'left')

# Build df_stores_2014
ls_store_cols_2014 = ['id_lsa', 'store_name', 'store_chain']
df_stores_201405 = df_qlmc_201405[ls_store_cols_2014].drop_duplicates()
df_stores_201409 = df_qlmc_201409[ls_store_cols_2014].drop_duplicates()

df_stores_2014 = pd.concat([df_stores_201405, df_stores_201409])
df_stores_2014.drop_duplicates('id_lsa', keep  = 'first', inplace = True)                         
## could check for issues... only +56 (2284 => 2340)
#print(df_stores_2014[-100:].to_string())

# Build df_stores_all
df_stores_all = pd.concat([df_stores_2014, df_stores_2015])
df_stores_all.drop_duplicates('id_lsa', keep = 'first', inplace = True)
# 2340 => 3142 : 802 stores more (not sure should keep them in df_qlmc_all)

## ########################
## BUILD DF QLMC 3 PERIODS
## ########################

df_qlmc_all = pd.merge(df_qlmc_2014,
                       df_qlmc_2015[['id_lsa', 'ean', 'price', 'date']],
                       on = ['id_lsa', 'ean'],
                       suffixes = ('', '_2'),
                       how = 'outer')

df_qlmc_all.rename(columns = {'price' : 'price_0',
                              'date' : 'date_0'}, inplace = True)

# add store and product info
# inner eliminates right prods of 2014 but with no prod/section/family

df_qlmc_all = pd.merge(df_qlmc_all, df_prod_all,
                       on = 'ean', how = 'outer')

df_qlmc_all = pd.merge(df_qlmc_all, df_stores_all,
                       on = 'id_lsa', how = 'outer')

df_qlmc_all = df_qlmc_all[['id_lsa', 'store_name', 'store_chain',
                           'ean', 'section', 'family', 'product',
                           'price_0', 'date_0',
                           'price_1', 'date_1',
                           'price_2', 'date_2']]

# ######
# OUTPUT
# ######

df_qlmc_all.to_csv(os.path.join(path_built_csv, 'df_qlmc_2014_2015.csv'),
                    encoding = 'utf-8',
                    float_format='%.2f',
                    index = False)

df_prod_all.to_csv(os.path.join(path_built_csv, 'df_prod_2014_2015.csv'),
                   encoding = 'utf-8',
                   float_format='%.2f',
                   index = False)

df_qlmc_201405.to_csv(os.path.join(path_built_csv, 'df_qlmc_201405_final.csv'),
                      encoding = 'utf-8',
                      float_format='%.2f',
                      index = False)

df_qlmc_201409.to_csv(os.path.join(path_built_csv, 'df_qlmc_201409_final.csv'),
                      encoding = 'utf-8',
                      float_format='%.2f',
                      index = False)

# #########
# OVERVIEW
# #########

# All periods observed? 670 stores with 158 to 1599 obs
df_full = (df_qlmc_all[(~df_qlmc_all['price_0'].isnull()) &
                       (~df_qlmc_all['price_1'].isnull()) &
                      (~df_qlmc_all['price_2'].isnull())])
print()
print('Overview nb of prods by store w/ data in 3 periods')
print(df_full['id_lsa'].value_counts().describe())

print()
print('Overview store chains')
print((df_full[['store_chain', 'id_lsa']].drop_duplicates()
                                         .groupby('store_chain').agg(len)))

print()
print('Top 10 stores in terms of nb obs')
print(df_full['id_lsa'].value_counts()[0:20].to_string())
df_store = df_full[df_full['id_lsa'] == '460']

# Can also consider 0 to 2
df_sub = (df_qlmc_all[(~df_qlmc_all['price_0'].isnull()) &
                      (~df_qlmc_all['price_2'].isnull())])

## Overview data from april-may 2014
#print(df_qlmc_201405[['store_chain', 'id_lsa']].drop_duplicates()\
#                                        .groupby('store_chain').agg(len))

## Overview data from septembrer 2014
## Exact same number as in "groupe" ad campaign
#print(df_qlmc_201409[['store_chain', 'id_lsa']].drop_duplicates()\
#                                        .groupby('store_chain').agg(len))
