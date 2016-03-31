#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
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
# LOAD DATA
# #######################

df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      parse_dates = ['date'],
                      dayfirst = True,
                      encoding = 'utf-8')

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

df_prices = df_qlmc

# #############################
# STATS DES PRICES
# #############################

PD = PriceDispersion()

ls_prod_cols = ['period', 'section', 'family', 'product']

# Product price distributions
df_desc = pd.pivot_table(df_prices,
                         values = 'price',
                         index = ls_prod_cols,
                         aggfunc = 'describe').unstack()
df_desc['cv'] = df_desc['std'] / df_desc['mean']
df_desc['iq_rg'] = df_desc['75%'] - df_desc['25%']
df_desc['iq_pct'] = df_desc['75%'] / df_desc['25%']
df_desc.drop(['25%', '75%'], axis = 1, inplace = True)
df_desc['count'] = df_desc['count'].astype(int)

# Most common prices (and kurtosis / skew)
df_freq = df_prices[ls_prod_cols + ['price']]\
                  .groupby(ls_prod_cols).agg([PD.kurtosis,
                                              PD.skew,
                                              PD.price_1,
                                              PD.price_1_fq,
                                              PD.price_2,
                                              PD.price_2_fq])['price']
df_freq.columns = [col.replace('PD.', '') for col in df_freq.columns]
df_freq['price_12_fq'] = df_freq[['price_1_fq', 'price_2_fq']].sum(axis = 1)

# Merge
df_overview = pd.merge(df_desc,
                       df_freq,
                       left_index = True,
                       right_index = True,
                       how = 'outer')
df_overview.sort('count', ascending = False, inplace = True)

##drop prod if too few obs?
#df_overview = df_overview[df_overview['count'] >= 200]

for per in range(13):
  df_overview_per = df_overview.loc[(per,)].copy()
  print()
  print('Period:', per)
  print()
  print('Stats des national product price distributions:')
  print(df_overview_per.describe().to_string())
  print()
  print('Overview national product price distributions:')
  print(df_overview_per[0:20].to_string())

  for var, ascending in [('cv', True),
                         ('cv', False),
                         ('price_1_fq', True),
                         ('price_1_fq', False)]:
    print()
    print('Overview products with higher or lowest {:s}:'.format(var))
    df_overview_per.sort(var, ascending = ascending, inplace = True)
    print(df_overview_per[0:20].to_string(index = False))

# stackoverflow.com/questions/21654635/scatter-plots-in-pandas-pyplot-how-to-plot-by-category

## Want to describe but without 0 within each period
#ls_se_pp = []
#for i in range(13):
#  ls_se_pp.append(df_prod_per[df_prod_per[i] != 0][i].describe())
#df_su_prod_per = pd.concat(ls_se_pp, axis= 1, keys = range(13))
#print(df_su_prod_per.to_string())

## PRICE DISPERSION (DYNAMIC)
#
## todo: identify products which are present across 0-8 periods
#prod = u'Coca Cola - Coca Cola avec caféine - 2L'
#for i in range(9):
#	se_prod_prices = df_qlmc[(df_qlmc['product'] == prod) &\
#                           (df_qlmc['period'] == i)]['price']
#	print(u'{:d}, Nb: {:d}, Mean: {:.2f}, CV: {:.2f}, iq_range: {:.2f}, id_range: {:.2f}'\
#          .format(i,
#                  len(se_prod_prices),
#                  se_prod_prices.mean(),
#                  PD.cv(se_prod_prices),
#                  PD.iq_range(se_prod_prices),
#                  PD.id_range(se_prod_prices)))
## Can draw all iq_range or id_range Coca products followed
## Regressions on CV (neutralize product values) for trend


## PRICE DISPERSION BY PRODUCT FAMILY
#
#fig, ax = plt.subplots()
#for dpt, c_dpt in [(u'Produits frais', 'b'),
#                   (u'Boissons', 'r')]:
#  df_temp = df_prod_per.loc[dpt]
#  df_temp = df_temp[(df_temp['len'] >= df_temp['len'].quantile(0.25)) &\
#                    (df_temp['mean'] <= df_temp['mean'].quantile(0.75))]
#  ax.plot(df_temp['mean'].values,
#          df_temp['cv'].values,
#          marker = 'o',
#          linestyle = '',
#          c = c_dpt,
#          label = dpt)
#ax.legend()
#plt.show()
## todo: replicate for each brand and output
## todo: distinguish families by colors


# # BOX PLOT
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
