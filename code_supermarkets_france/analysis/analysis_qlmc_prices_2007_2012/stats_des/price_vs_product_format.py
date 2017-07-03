#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

# ###########
# LOAD DATA
#############

dateparse = lambda x: pd.datetime.strptime(x, '%d/%m/%Y')
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      parse_dates = ['date'],
                      date_parser = dateparse,
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

# restrict to period 2 here...
df_prices = df_qlmc[df_qlmc['period'] == 2]
df_prices = df_prices[~df_prices['id_lsa'].isnull()]

# ###############
# FORMAT ANALYSIS
# ###############

ls_prod_pairs = [[u'Ricard - Ricard pastis 45 degrés - 50cl',
                  u'Ricard - Ricard pastis 45 degrés - 70cl'],
                 [u'Ricard - Ricard pastis 45 degrés - 70cl',
                  u'Ricard - Ricard pastis 45 degrés - 1L'],
                 [u'Ricard - Ricard pastis 45 degrés - 1L',
                  u'Ricard - Ricard pastis 45 degrés - 1.5L'],
                 [u'Coca Cola - Coca Cola avec caféine - 1.5L',
                  u'Coca Cola - Coca Cola avec caféine - 2L'],
                 [u'Panzani - Spagheto Sauce pleine saveur bolognaise - 210g',
                  u'Panzani - Spagheto Sauce pleine saveur bolognaise - 425g'],
                 [u'Panzani - Spagheto Sauce pleine saveur bolognaise - 425g',
                  u'Panzani - Spagheto Sauce pleine saveur bolognaise - 600g']]
                 
for prod_1, prod_2 in ls_prod_pairs:
  print()
  print(prod_1)
  print(prod_2)
  df_prod_1 = df_prices[['id_lsa', 'price']][df_prices['product'] == prod_1]
  df_prod_2 = df_prices[['id_lsa', 'price']][df_prices['product'] == prod_2]
  df_prod_1.set_index('id_lsa', inplace = True)
  df_prod_2.set_index('id_lsa', inplace = True)
  df_prod_f = df_prod_1.join(df_prod_2, how = 'inner', lsuffix='_1', rsuffix='_2')
  # outer may allow to see manipulation or small stores with less inventory
  df_prod_f['spread'] = df_prod_f['price_2'] - df_prod_f['price_1']
  
  df_prod_f = df_prod_f[df_prod_f['spread'] <\
                          df_prod_f['spread'].mean() + 1*df_prod_f['spread'].std()]
  df_prod_f = df_prod_f[df_prod_f['spread'] >\
                          df_prod_f['spread'].mean() - 1*df_prod_f['spread'].std()]
  
  #plt.scatter(df_prod_f['price_1'], df_prod_f['spread'])
  #plt.show()
  #
  #plt.scatter(df_prod_f['price_2'], df_prod_f['spread'])
  #plt.show()
   
  # spread not so easy to interpret, just focus on that for now:
  ax = plt.subplot()
  ax.scatter(df_prod_f['price_1'], df_prod_f['price_2'])
  ax.set_xlabel('price %s' %prod_1)
  ax.set_ylabel('price %s' %prod_2)
  plt.show()

  ## caution: get rid of outliers (how to automate?)
  #df_prod_f = df_prod_f[(df_prod_f['spread'] < 10) & (df_prod_f['spread'] > 5)]
  print(smf.ols('spread ~ price_1', data = df_prod_f).fit().summary())
  print(smf.ols('spread ~ price_2', data = df_prod_f).fit().summary())
