#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
#path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

# #######################
# BUILD DF QLMC
# #######################

# LOAD DF PRICES

## CSV (no ',' in fields? how is it dealt with?)
print u'Loading qlmc prices'
df_qlmc = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_qlmc_prices.csv'),
                      encoding = 'utf-8')
# date parsing slow... better if specified format?

# MERGE DF QLMC STORES

print u'Adding store lsa indexes'
df_stores = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_qlmc_stores.csv'),
                        dtype = {'id_lsa': str,
                                 'INSE_ZIP' : str,
                                 'INSEE_Dpt' : str,
                                 'INSEE_Code' : str,
                                 'QLMC_Dpt' : str},
                        encoding = 'UTF-8')

df_stores['Magasin'] = df_stores['Enseigne'] + u' ' + df_stores['Commune']
df_qlmc = pd.merge(df_stores,
                   df_qlmc,
                   on = ['P', 'Magasin'],
                   how = 'right')

# MERGE DF QLMC PRODUCTS

print u'Adding product std names and info'
df_products = pd.read_csv(os.path.join(path_dir_built_csv,
                                       'df_qlmc_products.csv'),
                          encoding='utf-8')
df_qlmc = pd.merge(df_products,
                   df_qlmc,
                   on = 'Produit',
                   how = 'right')

# BUILD NORMALIZED PRODUCT INDEX (needed? rather inter periods?)
print u'Adding Produit_norm: normalized product name'
for field in ['marque', 'nom', 'format']:
  df_qlmc[field].fillna(u'', inplace = True)
df_qlmc['Produit_norm'] = df_qlmc['marque'] + ' ' + df_qlmc['nom']+ ' ' + df_qlmc['format']

# ################
# GENERAL OVERVIEW
# ################

## BUILD DATETIME DATE COLUMN
#print u'\nParse dates'
#df_qlmc['Date_str'] = df_qlmc['Date']
#df_qlmc['Date'] = pd.to_datetime(df_qlmc['Date'], format = '%d/%m/%Y')
#
## DF DATES
#df_go_date = df_qlmc[['Date', 'P']].groupby('P').agg([min, max])['Date']
#df_go_date['spread'] = df_go_date['max'] - df_go_date['min']
#
## DF ROWS
#df_go_rows = df_qlmc[['Produit', 'P']].groupby('P').agg(len)
#
## DF UNIQUE STORES / PRODUCTS
#df_go_unique = df_qlmc[['Produit', 'Magasin', 'P']].groupby('P').agg(lambda x: len(x.unique()))
#
## DF GO
#df_go = pd.merge(df_go_date, df_go_unique, left_index = True, right_index = True)
#df_go['Nb rows'] = df_go_rows['Produit']
#for field in ['Nb rows', 'Magasin', 'Produit']:
#  df_go[field] = df_go[field].astype(float) # to have thousand separator
#df_go['Date start'] = df_go['min'].apply(lambda x: x.strftime('%d/%m/%Y'))
#df_go['Date end'] = df_go['max'].apply(lambda x: x.strftime('%d/%m/%Y'))
#df_go['Avg nb products/store'] = df_go['Nb rows'] / df_go['Magasin']
#df_go.rename(columns = {'Magasin' : 'Nb stores',
#                        'Produit' : 'Nb products'},
#             inplace = True)
#df_go.reset_index(inplace = True)
#
#pd.set_option('float_format', '{:4,.0f}'.format)
#
#print '\nGeneral overview of period records'
#
#print '\nString version:'
#print df_go[['P', 'Date start', 'Date end',
#             'Nb rows', 'Nb stores', 'Nb products', 'Avg nb products/store']].to_string(index = False)
#
#print '\nLatex version:'
#print df_go[['P', 'Date start', 'Date end',
#             'Nb rows', 'Nb stores', 'Nb products', 'Avg nb products/store']].to_latex(index = False)

# TODO: product categories

# ##########################
# OVERVIEW OF EACH PERIOD
# ##########################

# Check min, max price by period
print '\nPeriod min and max price:'
for per in range(13):
 df_per_prices = df_qlmc['Prix'][df_qlmc['P'] == per]
 print 'Period', per, ':', df_per_prices.min(), df_per_prices.max()

# Overview of product prices per period
pd.set_option('float_format', '{:4,.2f}'.format)
format_str = lambda x: u'{:}'.format(x[:20])

ls_unique_prod_cols = ['Rayon',
                       'Famille',
                       'Produit']

ls_unique_store_cols = ['Enseigne',
                        'Magasin']

for per in range(13):
  print u'\n', u'-'*80
  print u'Stats des of per: {:d}'.format(per)
  
  df_qlmc_per = df_qlmc[df_qlmc['P'] == per]
  
  # Nb unique products (incl by dpt)
  df_prod_per = df_qlmc_per[ls_unique_prod_cols].drop_duplicates()
  df_rayons = pd.pivot_table(data = df_prod_per[['Rayon', 'Produit']],
                             index = 'Rayon',
                             aggfunc = len,
                             fill_value = 0).astype(int)
  df_rayons.sort('Produit', ascending = False, inplace = True)
  print u'\nNb unique products by department:'
  print df_rayons.to_string()
  print u'TOTAL : {:d}'.format(len(df_prod_per))
 
  # Nb unique stores (incl by chain)
  
  df_store_per = df_qlmc_per[ls_unique_store_cols].drop_duplicates()
  df_chains = pd.pivot_table(data = df_store_per[['Enseigne', 'Magasin']],
                             index = 'Enseigne',
                             aggfunc = len,
                             fill_value = 0).astype(int)
  df_chains.sort('Magasin', ascending = False, inplace = True)
  print u'\nNb unique stores by chain:'
  print df_chains.to_string()
  print u'TOTAL : {:d}'.format(len(df_store_per))

# Rather: pivot with periods

## #############################
## INSPECT LSA DUPLICATE PRICES
## #############################
#
#df_matched = df_stores[~pd.isnull(df_stores['id_lsa'])]
#print '\nNb id_lsa associated with two different stores:',\
#       len(df_matched[df_matched.duplicated(subset = ['P', 'id_lsa'])])
#ls_tup_dup = df_matched[['P', 'id_lsa']]\
#               [df_matched.duplicated(subset = ['P', 'id_lsa'])].values
#
#ls_nodup_cols = ['P', 'Magasin', 'Rayon', 'Famille', 'Produit_norm']
#df_qlmc_keep = df_qlmc[~df_qlmc['id_lsa'].isnull()]
#df_duplicates = df_qlmc_keep[(df_qlmc_keep.duplicated(ls_nodup_cols, take_last = False)) |\
#                             (df_qlmc_keep.duplicated(ls_nodup_cols, take_last = True))]
#
#print u'\nNb duplicated rows: {:d}'.format(len(df_duplicates))
#
#print u'\nConcerned stores:'
#print df_duplicates[['P', 'id_lsa', 'Magasin']].drop_duplicates(['P', 'Magasin'])
#
#print u'\nInspect some duplicates:'
#print df_duplicates[0:30][ls_nodup_cols + ['Prix', 'Magasin', 'Date']].to_string()
#
## Inspect store
#for per, id_lsa in ls_tup_dup:
#  print '\nProd for dups', per, id_lsa
#  df_store = df_qlmc[(df_qlmc['P'] == per) & (df_qlmc['id_lsa'] == id_lsa)]
#  len(df_store[['Produit_norm', 'Prix']]\
#        [df_store.duplicated(subset = ['Produit_norm'])])
#  ls_prod_dup = df_store['Produit_norm']\
#                  [df_store.duplicated(subset = ['Produit_norm'])].values
#  print df_store[['Magasin', 'Produit_norm', 'Prix', 'Date']]\
#          [df_store['Produit_norm'].isin(ls_prod_dup)].to_string()
## first and last: same store... middle probably not: disambiguate
## probably a mistake: CHAMPION is carrefour contact here:
#
#u'CHAMPION ST GERMAIN DU PUY', '2131' # period 3 and 5
#u'CARREFOUR MARKET ST GERMAIN DU PUY', '169094' # period 5
#u'CARREFOUR MARKET ST GERMAIN DU PUY', '2131' # period 9 if one believes in surface?
