#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
# STATS DES PRICES
# #############################

# todo: add functions to describe prices (dispersion, ref prices)

df_qlmc_per = df_qlmc[df_qlmc['Period'] == 1]
df_qlmc_per = df_qlmc_per[df_qlmc_per['Store_Chain'] == 'CARREFOUR']

print u'\nStats des prices within period'
df_prod_per = pd.pivot_table(data = df_qlmc_per[['Department', 'Product', 'Price']],
                             index = ['Department', 'Product'],
                             values = 'Price',
                             aggfunc = [len, np.mean, np.std],
                             fill_value = np.nan)
print df_prod_per.describe()
#df_prod_per.sort('len', ascending = False, inplace = True)
#print df_prod_per[0:10].to_string()
#df_prod_per.sort('mean', ascending = False, inplace = True)
#print df_prod_per[0:10].to_string()
#df_prod_per.sort('mean', ascending = True, inplace = True)
#print df_prod_per[0:10].to_string()

# Not much to see with first and last: prefer graph
df_prod_per[(df_prod_per['len'] >= df_prod_per['len'].quantile(0.25)) &\
            (df_prod_per['mean'] <= df_prod_per['mean'].quantile(0.75))]\
               .plot(kind = 'scatter', x = 'mean', y = 'std')
plt.show()
# todo: replicate for each brand and output
# todo: distinguish families by colors

## Want to describe but without 0 within each period
#ls_se_pp = []
#for i in range(13):
#  ls_se_pp.append(df_prod_per[df_prod_per[i] != 0][i].describe())
#df_su_prod_per = pd.concat(ls_se_pp, axis= 1, keys = range(13))
#print df_su_prod_per.to_string()

## NB OBS BY PRODUCT AND CHAIN
#
#print u'\nProduct nb of obs by period for each chain'
#df_prod_chain_per = pd.pivot_table(data = df_qlmc[['Period',
#                                                   'Store_Chain',
#                                                   'Department',
#                                                   'Product']],
#                                   index = ['Store_Chain', 'Department', 'Product'],
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
#                       (df_qlmc['Product_norm'] == str_some_prod)]
#df_some_prod['Price'].plot(kind = 'box')
## pbm... quite far away and other prices quite concentrated
#plt.show()
