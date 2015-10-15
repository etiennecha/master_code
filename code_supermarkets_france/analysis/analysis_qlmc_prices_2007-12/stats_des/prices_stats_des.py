#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

class PriceDispersion:
  def cv(self, se_prices):
    return se_prices.std() / se_prices.mean()
  def iq_range(self, se_prices):
    return se_prices.quantile(0.75) - se_prices.quantile(0.25)
  def id_range(self, se_prices):
    return se_prices.quantile(0.90) - se_prices.quantile(0.10)
  def minmax_range(self, se_prices):
    return se_prices.max() - se_prices.min()

PD = PriceDispersion()

# todo: add functions to describe prices (dispersion, ref prices)

df_qlmc_per = df_qlmc[df_qlmc['Period'] == 1]

print u'\nStats des prices within period'
df_prod_per = pd.pivot_table(data = df_qlmc_per[['Family', 'Product', 'Price']],
                             index = ['Family', 'Product'],
                             values = 'Price',
                             aggfunc = [len,
                                        np.mean,
                                        np.std,
                                        PD.cv,
                                        PD.iq_range,
                                        PD.id_range,
                                        PD.minmax_range],
                             fill_value = np.nan)
print df_prod_per.describe()
#df_prod_per.sort('len', ascending = False, inplace = True)
#print df_prod_per[0:10].to_string()
#df_prod_per.sort('mean', ascending = False, inplace = True)
#print df_prod_per[0:10].to_string()
#df_prod_per.sort('mean', ascending = True, inplace = True)
#print df_prod_per[0:10].to_string()

# stackoverflow.com/questions/21654635/scatter-plots-in-pandas-pyplot-how-to-plot-by-category

# PRICE DISPERSION BY PRODUCT FAMILY

#                   (u'Epicerie salée', 'g'),
#                   (u'Epicerie sucrée', 'k'),

fig, ax = plt.subplots()
for dpt, c_dpt in [(u'Produits frais', 'b'),
                   (u'Boissons', 'r')]:
  df_temp = df_prod_per.loc[dpt]
  df_temp = df_temp[(df_temp['len'] >= df_temp['len'].quantile(0.25)) &\
                    (df_temp['mean'] <= df_temp['mean'].quantile(0.75))]
  ax.plot(df_temp['mean'].values,
          df_temp['cv'].values,
          marker = 'o',
          linestyle = '',
          c = c_dpt,
          label = dpt)
ax.legend()
plt.show()
# todo: replicate for each brand and output
# todo: distinguish families by colors

## Want to describe but without 0 within each period
#ls_se_pp = []
#for i in range(13):
#  ls_se_pp.append(df_prod_per[df_prod_per[i] != 0][i].describe())
#df_su_prod_per = pd.concat(ls_se_pp, axis= 1, keys = range(13))
#print df_su_prod_per.to_string()

## PRICE DISPERSION BY STORE CHAIN
#fig, ax = plt.subplots()
#for chain, c_chain in [(u'LECLERC', 'b'),
#                       (u'AUCHAN', 'g'),
#                       (u'CARREFOUR', 'r'),
#                       (u'INTERMARCHE', 'k')]:
#  df_qlmc_per_chain = df_qlmc_per[(df_qlmc_per['Store_Chain'] == chain) &\
#                                  (df_qlmc_per['Family'] == u'Produits frais')]
#  df_prod_per_chain = pd.pivot_table(data = df_qlmc_per_chain[['Family',
#                                                               'Product',
#                                                               'Price']],
#                                     index = ['Family', 'Product'],
#                                     values = 'Price',
#                                     aggfunc = [len, np.mean, np.std],
#                                     fill_value = np.nan)
#  df_temp = df_prod_per_chain
#  df_temp = df_temp[(df_temp['len'] >= df_temp['len'].quantile(0.25)) &\
#                    (df_temp['mean'] <= df_temp['mean'].quantile(0.75))]
#  ax.plot(df_temp['mean'].values,
#          df_temp['std'].values,
#          marker = 'o',
#          linestyle = '',
#          c = c_chain,
#          label = chain)
#ax.legend()
#plt.show()

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

## BACKUP: NB OBS BY PRODUCT AND CHAIN
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
