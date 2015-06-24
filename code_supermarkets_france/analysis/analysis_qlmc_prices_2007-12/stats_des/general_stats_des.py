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

pd.set_option('float_format', '{:4,.2f}'.format)
format_str = lambda x: u'{:}'.format(x[:20])

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

# ##########################
# OVERVIEW OF EACH PERIOD
# ##########################

ls_unique_prod_cols = ['Rayon',
                       'Famille',
                       'Produit']

ls_unique_store_cols = ['Enseigne',
                        'Magasin']

# Store departments & sub departments by period
df_prod = df_qlmc[['P'] + ls_unique_prod_cols].drop_duplicates()
df_rayons = pd.pivot_table(data = df_prod[['P', 'Rayon', 'Produit']],
                           index = 'Rayon',
                           columns = 'P',
                           aggfunc = len,
                           fill_value = 0).astype(int)['Produit']
print u'\nStore departments by period:'
print df_rayons.to_string()
# Obs: discontinuity after period 9

df_familles = pd.pivot_table(data = df_prod[['P', 'Famille', 'Produit']],
                             index = 'Famille',
                             columns = 'P',
                             aggfunc = len,
                             fill_value = 0).astype(int)['Produit']
print u'\nProduct families by period:'
print df_familles.to_string()
# Obs: small discontinuity after period 6 and larger after period 9

# Store retail chains by period
df_store = df_qlmc[['P'] + ls_unique_store_cols].drop_duplicates()
df_chains = pd.pivot_table(data = df_store[['P', 'Enseigne', 'Magasin']],
                           index = 'Enseigne',
                           columns = 'P',
                           aggfunc = len,
                           fill_value = 0).astype(int)['Magasin']
print u'\nStore retail chains by period:'
print df_chains.to_string()

# Obs:
# AUCHAN: ok

# CARREFOUR: ok
# CHAMPION stops after 5 (normal..)
# CARREFOUR MARKET starts at 4

# LECLERC: need to standardize to "LECLERC"
# "CENTRE E. LECLERC", "CENTRE LECLERC", "E. LECLERC', "E.LECLERC"
# maybe also 'LECLERC EXPRESS" (very few)

# CASINO:
# need to rename "GEANT" to "GEANT CASINO"

# U:
# can rename "SYSTEME U" to "SUPER U"
# (but may include some "HYPER U" which are then distinguished

## ###############
## DEPRECATED
## ###############
#
## Loop over period to describe store departments and retail chains
#for per in range(13):
#  print u'\n', u'-'*80
#  print u'Stats des of per: {:d}'.format(per)
#  
#  df_qlmc_per = df_qlmc[df_qlmc['P'] == per]
#  
#  # Nb unique products (incl by dpt)
#  df_prod_per = df_qlmc_per[ls_unique_prod_cols].drop_duplicates()
#  df_rayons_per = pd.pivot_table(data = df_prod_per[['Rayon', 'Produit']],
#                                 index = 'Rayon',
#                                 aggfunc = len,
#                                 fill_value = 0).astype(int)
#  df_rayons_per.sort('Produit', ascending = False, inplace = True)
#  print u'\nNb unique products by department:'
#  print df_rayons_per.to_string()
#  print u'TOTAL : {:d}'.format(len(df_prod_per))
# 
#  # Nb unique stores (incl by chain)
#  
#  df_store_per = df_qlmc_per[ls_unique_store_cols].drop_duplicates()
#  df_chains_per = pd.pivot_table(data = df_store_per[['Enseigne', 'Magasin']],
#                                 index = 'Enseigne',
#                                 aggfunc = len,
#                                 fill_value = 0).astype(int)
#  df_chains_per.sort('Magasin', ascending = False, inplace = True)
#  print u'\nNb unique stores by chain:'
#  print df_chains_per.to_string()
#  print u'TOTAL : {:d}'.format(len(df_store_per))
