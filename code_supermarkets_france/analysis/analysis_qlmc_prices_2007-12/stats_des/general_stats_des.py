#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

pd.set_option('float_format', '{:4,.2f}'.format)
format_str = lambda x: u'{:}'.format(x[:20])

# #######################
# LOAD DF QLMC
# #######################

print u'Loading df_qlmc'
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      encoding = 'utf-8')
# date parsing slow... better if specified format?

# ##################
# STATS DES: PRELIM
# ##################

ls_unique_prod_cols = ['Family',
                       'Subfamily',
                       'Product']

ls_unique_store_cols = ['Store_Chain',
                        'Store']

# PRODUCT DEPARTMENTS

print u'\nProduct departments by period:'
df_prod = df_qlmc[['Period'] + ls_unique_prod_cols].drop_duplicates()
df_rayons = pd.pivot_table(data = df_prod[['Period', 'Family', 'Product']],
                           index = 'Family',
                           columns = 'Period',
                           aggfunc = len,
                           fill_value = 0).astype(int)['Product']
print df_rayons.to_string()
# Obs: discontinuity after period 9

# PRODUCT FAMILIES

print u'\nProduct families by period:'
df_familles = pd.pivot_table(data = df_prod[['Period', 'Family', 'Product']],
                             index = 'Family',
                             columns = 'Period',
                             aggfunc = len,
                             fill_value = 0).astype(int)['Product']
print df_familles.to_string()
# Obs: small discontinuity after period 6 and larger after period 9

# STORE CHAINS (ORIGINAL)

print u'\nStore chains (qlmc classification) by period:'
df_store = df_qlmc[['Period'] + ls_unique_store_cols].drop_duplicates()
df_chains = pd.pivot_table(data = df_store[['Period', 'Store_Chain', 'Store']],
                           index = 'Store_Chain',
                           columns = 'Period',
                           aggfunc = len,
                           fill_value = 0).astype(int)['Store']
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

# Fix Store_Chain for prelim stats des
ls_sc_drop = ['CARREFOUR CITY',
              'CARREFOUR CONTACT',
              'CARREFOUR PLANET',
              'GEANT DISCOUNT',
              'HYPER CHAMPION',
              'INTERMARCHE HYPER',
              'LECLERC EXPRESS',
              'MARCHE U',
              'U EXPRESS']
df_qlmc = df_qlmc[~df_qlmc['Store_Chain'].isin(ls_sc_drop)]
ls_sc_replace = [('CENTRE E. LECLERC', 'LECLERC'),
                 ('CENTRE LECLERC', 'LECLERC'),
                 ('E. LECLERC', 'LECLERC'),
                 ('E.LECLERC', 'LECLERC'),
                 ('SYSTEME U', 'SUPER U'),
                 ('GEANT', 'GEANT CASINO')]
for sc_old, sc_new in ls_sc_replace:
  df_qlmc.loc[df_qlmc['Store_Chain'] == sc_old,
              'Store_Chain'] = sc_new

# #############################
# STATS DES: NB OBS AND PRICES
# #############################

# NB OBS BY PRODUCT

print u'\nProduct nb of obs by period'
df_prod_per = pd.pivot_table(data = df_qlmc[['Period', 'Family', 'Product']],
                             index = ['Family', 'Product'],
                             columns = 'Period',
                             aggfunc = len,
                             fill_value = 0).astype(int)
# Want to describe but without 0 within each period
ls_se_pp = []
for i in range(13):
  ls_se_pp.append(df_prod_per[df_prod_per[i] != 0][i].describe())
df_su_prod_per = pd.concat(ls_se_pp, axis= 1, keys = range(13))
print df_su_prod_per.to_string()

## NB OBS BY PRODUCT AND CHAIN
#
#print u'\nProduct nb of obs by period for each chain'
#df_prod_chain_per = pd.pivot_table(data = df_qlmc[['Period',
#                                                   'Store_Chain',
#                                                   'Family',
#                                                   'Product']],
#                                   index = ['Store_Chain', 'Family', 'Product'],
#                                   columns = 'Period',
#                                   aggfunc = len,
#                                   fill_value = 0).astype(int)
#for chain in df_qlmc['Store_Chain'].unique():
#  ls_se_chain_pp = []
#  for i in range(13):
#    df_temp_chain_prod = df_prod_chain_per.loc[chain]
#    ls_se_chain_pp.append(df_temp_chain_prod[df_temp_chain_prod[i] != 0][i].describe())
#  df_su_chain_prod_per = pd.concat(ls_se_chain_pp, axis= 1, keys = range(13))
#  print u'\n', chain
#  print df_su_chain_prod_per.to_string()

# #################
# STATS DES: PRICES
# #################

## potential issue outlier detection
## example: boxplot
#import matplotlib.pyplot as plt
##str_some_prod = u'Philips - Cafetière filtre Cucina lilas 1000W 1.2L (15 tasses) - X1'
#str_some_prod = u'Canard-Duchene - Champagne brut 12 degrés - 75cl'
#df_some_prod = df_qlmc[(df_qlmc['Period'] == 0) &\
#                       (df_qlmc['Product'] == str_some_prod)]
#df_some_prod['Price'].plot(kind = 'box')
## pbm... quite far away and other prices quite concentrated
#plt.show()
