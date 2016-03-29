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
                      parse_dates = ['date'],
                      encoding = 'utf-8')
# date parsing slow? specify format?
#print u'\nParse dates'
#df_qlmc['date_str'] = df_qlmc['date']
#df_qlmc['date'] = pd.to_datetime(df_qlmc['date'], format = '%d/%m/%Y')

# ##################
# STATS DES: PRELIM
# ##################

ls_prod_cols = ['section', 'family', 'product']
ls_store_cols = ['store_chain', 'store']

# PRODUCT DEPARTMENTS

print u'\nproduct departments by period:'
df_prod = df_qlmc[['period'] + ls__prod_cols].drop_duplicates()
df_rayons = pd.pivot_table(data = df_prod[['period', 'section', 'product']],
                           index = 'section',
                           columns = 'period',
                           aggfunc = len,
                           fill_value = 0).astype(int)['product']
print df_rayons.to_string()
# Obs: discontinuity after period 9

# PRODUCT FAMILIES

print u'\nproduct families by period:'
df_familles = pd.pivot_table(data = df_prod[['period', 'section', 'product']],
                             index = 'section',
                             columns = 'period',
                             aggfunc = len,
                             fill_value = 0).astype(int)['product']
print df_familles.to_string()
# Obs: small discontinuity after period 6 and larger after period 9

# STORE CHAINS (ORIGINAL)

print u'\nstore chains (qlmc classification) by period:'
df_store = df_qlmc[['period'] + ls_store_cols].drop_duplicates()
df_chains = pd.pivot_table(data = df_store[['period', 'store_chain', 'store']],
                           index = 'store_chain',
                           columns = 'period',
                           aggfunc = len,
                           fill_value = 0).astype(int)['store']
print df_chains.to_string()

# Remarks on chains
# CHAMPION stops after 5 (normal..)
# CARREFOUR MARKET starts at 4
# Rename "SYSTEME U" to "SUPER U"
# (but may include some "HYPER U" which are distinguished later)

# Fix store_chain for prelim stats des
ls_sc_drop = ['CARREFOUR CITY',
              'CARREFOUR CONTACT',
              'CARREFOUR PLANET',
              'GEANT DISCOUNT',
              'HYPER CHAMPION',
              'INTERMARCHE HYPER',
              'LECLERC EXPRESS',
              'MARCHE U',
              'U EXPRESS']

df_qlmc = df_qlmc[~df_qlmc['store_chain'].isin(ls_sc_drop)]
ls_sc_replace = [('CENTRE E. LECLERC', 'LECLERC'),
                 ('CENTRE LECLERC', 'LECLERC'),
                 ('E. LECLERC', 'LECLERC'),
                 ('E.LECLERC', 'LECLERC'),
                 ('SYSTEME U', 'SUPER U'),
                 ('GEANT', 'GEANT CASINO')]
for sc_old, sc_new in ls_sc_replace:
  df_qlmc.loc[df_qlmc['store_chain'] == sc_old,
              'store_chain'] = sc_new

# #############################
# STATS DES: NB OBS AND PRICES
# #############################

# NB OBS BY PRODUCT

print u'\nproduct nb of obs by period'
df_prod_per = pd.pivot_table(data = df_qlmc[['period', 'section', 'product']],
                             index = ['section', 'product'],
                             columns = 'period',
                             aggfunc = len,
                             fill_value = 0).astype(int)
# Want to describe but without 0 within each period
# In fact: same res if fill_value = np.nan and then use describe
ls_se_pp = []
for i in range(13):
  ls_se_pp.append(df_prod_per[df_prod_per[i] != 0][i].describe())
df_su_prod_per = pd.concat(ls_se_pp, axis= 1, keys = range(13))
print df_su_prod_per.to_string()

# todo: check those w/ few obs if fix them when possible

# NB OBS BY PRODUCT AND CHAIN

print u'\nproduct nb of obs by period for each chain'
df_prod_chain_per = pd.pivot_table(data = df_qlmc[['period',
                                                   'store_chain',
                                                   'section',
                                                   'product']],
                                   index = ['store_chain', 'section', 'product'],
                                   columns = 'period',
                                   aggfunc = len,
                                   fill_value = 0).astype(int)
for chain in df_qlmc['store_chain'].unique():
  ls_se_chain_pp = []
  for i in range(13):
    df_temp_chain_prod = df_prod_chain_per.loc[chain]
    ls_se_chain_pp.append(df_temp_chain_prod[df_temp_chain_prod[i] != 0][i].describe())
  df_su_chain_prod_per = pd.concat(ls_se_chain_pp, axis= 1, keys = range(13))
  print u'\n', chain
  print df_su_chain_prod_per.to_string()

# #################
# STATS DES: PRICES
# #################

## potential issue outlier detection
## example: boxplot
#import matplotlib.pyplot as plt
##str_some_prod = u'Philips - Cafetière filtre Cucina lilas 1000W 1.2L (15 tasses) - X1'
#str_some_prod = u'Canard-Duchene - Champagne brut 12 degrés - 75cl'
#df_some_prod = df_qlmc[(df_qlmc['period'] == 0) &\
#                       (df_qlmc['product'] == str_some_prod)]
#df_some_prod['Price'].plot(kind = 'box')
## pbm... quite far away and other prices quite concentrated
#plt.show()
