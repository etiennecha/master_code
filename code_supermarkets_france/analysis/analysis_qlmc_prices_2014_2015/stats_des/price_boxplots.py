#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import numpy as np
import pandas as pd
from functions_generic_qlmc import *
import matplotlib
import matplotlib.pyplot as plt
import textwrap

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2014_2015',
                              'data_csv')

# ##########
# LOAD DATA
# ##########

df_prices = pd.read_csv(os.path.join(path_built_csv, 'df_prices_201503.csv'),
                        encoding = 'utf-8')

# Unique products with nb obs
ls_cols_u_prod = ['section', 'family', 'product']
df_prices['nb_obs'] = df_prices[ls_cols_u_prod + ['store_chain']]\
                        .groupby(ls_cols_u_prod).transform(len)
df_u_prod = df_prices[ls_cols_u_prod + ['nb_obs']]\
              .drop_duplicates(ls_cols_u_prod)
df_u_prod.sort_values('nb_obs', ascending = False, inplace = True)

## Check most common products of most famous brands
#for brand in ['Herta', 'Fleury', 'Coca', 'Cristaline', 'President']:
#  print(df_u_prod[df_u_prod['product'].str.contains(brand,
##for i in range(0,30):
##	print(df_u_prod[(df_u_prod['product'].str.contains('President',
##                                                      case = False))]['product'].iloc[i])

# Price distribution of one product at each chain
ls_ref_products = [u'HERTA JAMBON LE BON PARIS -25% DE SEL HERTA 4TRANCHES 120G',
                   u'FLEURY MICHON JAMBON S/COUENNE TENEUR SEL RÉDUIT OMEGA3 4TR.160G',
                   u'COCA COLA COCA-COLA PET 1.5L',
                   u'COCA COLA ZERO COCA-COLA ZERO PET CONTOUR 1,5L',
                   u'DANONE YAOURT DANONE NATURE 4X125G',
                   u'CRISTALINE EAU CRISTALINE BOUTEILLE 1.5 LITRE X6',
                   u'CRISTALINE EAU CRISTALINE BOUTEILLE 1.5 LITRE',
                   u'PRESIDENT CAMEMBERT PRÉSIDENT ENTIER 20%MG 250G',
                   u'PRESIDENT EMMENTAL PRESIDENT 28%MG 250G']

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
  df_prod_prices = df_product.pivot(index='store_id',
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
