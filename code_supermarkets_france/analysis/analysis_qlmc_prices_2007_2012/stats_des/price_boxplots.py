#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import textwrap

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)

# #######################
# LOAD DATA
# #######################

# LOAD DF QLMC
df_qlmc = pd.read_csv(os.path.join(path_built_csv, 'df_qlmc.csv'),
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
                 ('GEANT', 'GEANT CASINO'),
                 ('CHAMPION', 'CARREFOUR MARKET'),
                 ('INTERMARCHE SUPER', 'INTERMARCHE'),
                 ('HYPER U', 'SUPER U')]
for sc_old, sc_new in ls_sc_replace:
  df_qlmc.loc[df_qlmc['store_chain'] == sc_old,
              'store_chain'] = sc_new

df_prices = df_qlmc[df_qlmc['period'] == 12].copy()

ls_prod_cols = ['section', 'family', 'product']
df_prices['nb_obs'] = df_prices[ls_prod_cols + ['store_chain']]\
                        .groupby(ls_prod_cols).transform(len)
df_prods = df_prices[ls_prod_cols + ['nb_obs']]\
             .drop_duplicates(ls_prod_cols)
df_prods.sort('nb_obs', ascending = False, inplace = True)

pd.set_option('display.max_colwidth', 200)
for brand in ['Herta', 'Fleury Michon', 'Coca', 'Danone',
              'Cristaline', u'Président', u'President']:
  print(df_prods[df_prods['product'].str.contains(brand,
                                                  case = False)].to_string())

# pick some products among most famous brands
ls_ref_products = [u'Herta - Le Bon Paris Jambon cuit supérieur 6 tranches - 270g',
                   u'Fleury Michon - Jambon 4 tranches - 160g',
                   u'Coca Cola - Coca Cola light sans caféine - 1.5L',
                   u'Coca-Cola - Coca Cola zero avec caféine - 1.5L',
                   u'Danone - Yaourt Activia nature - 4x 125g',
                   u'Président - Camembert pasteurisé 45% mg - 250g',
                   u'Président - Emmental rapé 45% mg - 200g']

# ###########
# STATS DES
# ###########

for ref_product in ls_ref_products:
  print()
  print(ref_product)
  df_product = df_prices[df_prices['product'] == ref_product]
  
  se_chain_vc = df_prices['store_chain'].value_counts()
  ls_df_desc = []
  for chain in se_chain_vc.index:
    ls_df_desc.append(df_product[df_product['store_chain'] == chain]['price'].describe())
  df_desc = pd.concat(ls_df_desc, keys = se_chain_vc.index[0:30], axis = 1)
  df_desc = df_desc.T
  
  df_desc['cv'] = df_desc['std'] / df_desc['mean']
  df_desc['gfs'] = df_desc['mean'] - df_desc['min']
  df_desc['range'] = df_desc['max'] - df_desc['min']
  df_desc['range_2'] = df_desc['75%'] - df_desc['25%']
  
  #print df_desc[['count', 'mean', 'std', 'cv', 'gfs', 'range', 'range_2']].to_string()
  print(df_desc.to_string())
  
  # following filled with nan... must be better way
  df_prod_prices = df_product.pivot(index='store',
                                    columns='store_chain',
                                    values='price')
  # improve boxplot display
  # http://matplotlib.org/examples/pylab_examples/boxplot_demo2.html
  # todo: update matplotlib http://stackoverflow.com/questions/21997897/ (ctd)
  # changing-what-the-ends-of-whiskers-represent-in-matplotlibs-boxplot-function
  
  # display by price order (median)
  ls_chains = ['INTERMARCHE',
               'SUPER U',
               'CARREFOUR',
               'LECLERC',
               'AUCHAN',
               'GEANT CASINO']
  se_med = df_desc.ix[ls_chains]['50%'].copy()
  se_med.sort(ascending = True, inplace = True)
  ls_chains = list(se_med.index)
  ax = df_prod_prices[ls_chains].plot(kind = 'box') #, whis = [0.10, 0.90])
  
  # ax.get_xticklabels()[0].get_text()
  # textwrap.fill(ax.get_xticklabels()[0].get_text(), width = 20)
  ax.set_xticklabels([textwrap.fill(x.get_text(), 20) for x in ax.get_xticklabels()])
  plt.title(ref_product)
  plt.show()
  
  # todo: find most common prod within important categories and draw maps
  # todo: restrict to most common prod and run regressions (check robustness?)
  # moustache plot by product?
