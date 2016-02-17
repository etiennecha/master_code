#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
from functions_string import *
from functions_generic_qlmc import *
import os, sys
import re
import json
import pandas as pd
import matplotlib.pyplot as plt

path_qlmc_scraped = os.path.join(path_data,
                                 'data_supermarkets',
                                 'data_qlmc_2015',
                                 'data_source',
                                 'data_scraped_201503')

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

path_lsa_csv = os.path.join(path_data,
                            'data_supermarkets',
                            'data_built',
                            'data_lsa',
                            'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##########
# LOAD DATA
# ##########

# LOAD DF PRICES
df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

# todo: move
df_prices['product'] = df_prices['product'].apply(lambda x: x.replace(u'\x8c', u'OE'))

# can restrict chain (move?)
df_prices = df_prices[df_prices['store_chain'] == 'AUCHAN'].copy()

# ###############
# STATS DES
# ###############

# DESCRIBE SECTION AND FAMILIES

# add nb of observations for each product (defined as section family product)
ls_prod_cols = ['section', 'family', 'product']
se_prod_vc = df_prices[ls_prod_cols].groupby(ls_prod_cols).agg(len)
df_prices.set_index(ls_prod_cols, inplace = True)
df_prices['nb_obs'] = se_prod_vc
df_prices.reset_index(drop = False, inplace = True)

df_prods = df_prices[ls_prod_cols + ['nb_obs']].drop_duplicates(ls_prod_cols)

# PRODUCT SECTIONS
print()
print(u'Product sections')
df_sections = pd.pivot_table(data = df_prods[['section', 'product']],
                             index = 'section',
                             aggfunc = len,
                             fill_value = 0).astype(int)['product']
print(df_sections.to_string())

# PRODUCT FAMILIES
print()
print(u'Product families')
df_families = pd.pivot_table(data = df_prods[['section', 'family', 'product']],
                             index = ['section', 'family'],
                             aggfunc = len,
                             fill_value = 0).astype(int)['product']
print(df_families.to_string())

# PRODUCT PRICE STATS

# todo: table with product min, max, mean, std, cv, interquartile

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

df_stats = df_prices[ls_prod_cols + ['price']].groupby(ls_prod_cols).\
            agg([len,
                 np.median, np.mean, np.std, min, max,
                 PD.cv, PD.iq_range, PD.id_range, PD.minmax_range])['price']

print()
print(u'General overview')
print(df_stats.describe().to_string())

df_stats.sort('len', ascending = False, inplace = True)
print()
print(df_stats[0:20].to_string())

# run regressions + do graphs
# by section (/family?) and brand?

## PRICE DISPERSION BY PRODUCT FAMILY
#
##                   (u'Epicerie salée', 'g'),
##                   (u'Epicerie sucrée', 'k'),
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
#
### Want to describe but without 0 within each period
##ls_se_pp = []
##for i in range(13):
##  ls_se_pp.append(df_prod_per[df_prod_per[i] != 0][i].describe())
##df_su_prod_per = pd.concat(ls_se_pp, axis= 1, keys = range(13))
##print df_su_prod_per.to_string()
#
### PRICE DISPERSION BY STORE CHAIN
##fig, ax = plt.subplots()
##for chain, c_chain in [(u'LECLERC', 'b'),
##                       (u'AUCHAN', 'g'),
##                       (u'CARREFOUR', 'r'),
##                       (u'INTERMARCHE', 'k')]:
##  df_qlmc_per_chain = df_qlmc_per[(df_qlmc_per['Store_Chain'] == chain) &\
##                                  (df_qlmc_per['Family'] == u'Produits frais')]
##  df_prod_per_chain = pd.pivot_table(data = df_qlmc_per_chain[['Family',
##                                                               'Product',
##                                                               'Price']],
##                                     index = ['Family', 'Product'],
##                                     values = 'Price',
##                                     aggfunc = [len, np.mean, np.std],
##                                     fill_value = np.nan)
##  df_temp = df_prod_per_chain
##  df_temp = df_temp[(df_temp['len'] >= df_temp['len'].quantile(0.25)) &\
##                    (df_temp['mean'] <= df_temp['mean'].quantile(0.75))]
##  ax.plot(df_temp['mean'].values,
##          df_temp['std'].values,
##          marker = 'o',
##          linestyle = '',
##          c = c_chain,
##          label = chain)
##ax.legend()
##plt.show()
