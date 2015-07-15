#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_dir_qlmc = os.path.join(path_data,
                             'data_supermarkets',
                             'data_qlmc_2007-12')

path_dir_built_csv = os.path.join(path_dir_qlmc,
                                  'data_built',
                                  'data_csv')

pd.set_option('float_format', '{:4,.2f}'.format)
format_str = lambda x: u'{:}'.format(x[:20])

# #######################
# LOAD DF QLMC
# #######################

print u'Loading df_qlmc'
df_qlmc = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_qlmc.csv'),
                      encoding = 'utf-8')
# date parsing slow... better if specified format?

# ##########################
# OVERVIEW OF EACH PERIOD
# ##########################

ls_unique_prod_cols = ['Department',
                       'Family',
                       'Product']

ls_unique_store_cols = ['Store_Chain',
                        'Store']

# Store departments & sub departments by period
df_prod = df_qlmc[['Period'] + ls_unique_prod_cols].drop_duplicates()
df_rayons = pd.pivot_table(data = df_prod[['Period', 'Department', 'Product']],
                           index = 'Department',
                           columns = 'Period',
                           aggfunc = len,
                           fill_value = 0).astype(int)['Product']
print u'\nStore departments by period:'
print df_rayons.to_string()
# Obs: discontinuity after period 9

df_familles = pd.pivot_table(data = df_prod[['Period', 'Family', 'Product']],
                             index = 'Family',
                             columns = 'Period',
                             aggfunc = len,
                             fill_value = 0).astype(int)['Product']
print u'\nProduct families by period:'
print df_familles.to_string()
# Obs: small discontinuity after period 6 and larger after period 9

# Store retail chains by period
df_store = df_qlmc[['Period'] + ls_unique_store_cols].drop_duplicates()
df_chains = pd.pivot_table(data = df_store[['Period', 'Store_Chain', 'Store']],
                           index = 'Store_Chain',
                           columns = 'Period',
                           aggfunc = len,
                           fill_value = 0).astype(int)['Store']
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
#  df_qlmc_per = df_qlmc[df_qlmc['Period'] == per]
#  
#  # Nb unique products (incl by dpt)
#  df_prod_per = df_qlmc_per[ls_unique_prod_cols].drop_duplicates()
#  df_rayons_per = pd.pivot_table(data = df_prod_per[['Department', 'Product']],
#                                 index = 'Department',
#                                 aggfunc = len,
#                                 fill_value = 0).astype(int)
#  df_rayons_per.sort('Product', ascending = False, inplace = True)
#  print u'\nNb unique products by department:'
#  print df_rayons_per.to_string()
#  print u'TOTAL : {:d}'.format(len(df_prod_per))
# 
#  # Nb unique stores (incl by chain)
#  
#  df_store_per = df_qlmc_per[ls_unique_store_cols].drop_duplicates()
#  df_chains_per = pd.pivot_table(data = df_store_per[['Store_Chain', 'Store']],
#                                 index = 'Store_Chain',
#                                 aggfunc = len,
#                                 fill_value = 0).astype(int)
#  df_chains_per.sort('Store', ascending = False, inplace = True)
#  print u'\nNb unique stores by chain:'
#  print df_chains_per.to_string()
#  print u'TOTAL : {:d}'.format(len(df_store_per))
