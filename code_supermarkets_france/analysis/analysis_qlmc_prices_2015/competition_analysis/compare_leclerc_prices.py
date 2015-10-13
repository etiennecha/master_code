#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import httplib
import urllib, urllib2
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from functions_generic_qlmc import *
import numpy as np
import matplotlib.pyplot as plt
import textwrap

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_csv = os.path.join(path_data,
                        'data_supermarkets',
                        'data_qlmc_2015',
                        'data_built',
                        'data_csv_201503')

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'df_stores_final.csv'),
                        encoding = 'utf-8')

df_comp = pd.read_csv(os.path.join(path_csv,
                                   'df_competitors.csv'),
                      encoding = 'utf-8')

df_france = pd.read_csv(os.path.join(path_csv,
                                     'df_france.csv'),
                        encoding = 'utf-8')

# Restrict to leclerc (could drop rest?)
df_leclerc = df_france[df_france['chain'] == 'LEC'].copy()

# Count stores present in data
print u'\nNb Leclerc: {:d}'.format(len(df_leclerc['store_id'].unique()))

# Count products present in data
# (todo: never same product under two families/subfamilies?)
print u'\nNb products: {:d}'.format(len(df_leclerc['product'].unique()))

# Nb of products by leclerc
se_nb_prod = df_leclerc[['store_id', 'product']].groupby('store_id').agg([len])['product']
print u'\nDescribe nb prod by store:'
print se_nb_prod.describe()

# Most common products
print u'\nShow most common products:'
se_prod_vc = df_leclerc['product'].value_counts()
print se_prod_vc[0:30].to_string()

# Price distribution of most common products
ls_df_desc = []
for product in se_prod_vc.index[0:30]:
  if len(df_leclerc[df_leclerc['product'] == product]['store_id'].unique()) !=\
      se_prod_vc[product]:
    print 'Pbm: product {:s} listed twice for one store'.format(product)
  ls_df_desc.append(df_leclerc[df_leclerc['product'] == product]['price'].describe())
df_desc = pd.concat(ls_df_desc, keys = se_prod_vc.index[0:30], axis = 1)
df_desc = df_desc.T

df_desc['cv'] = df_desc['std'] / df_desc['mean']
df_desc['gfs'] = df_desc['mean'] - df_desc['min']
df_desc['range'] = df_desc['max'] - df_desc['min']
df_desc['range_2'] = df_desc['75%'] - df_desc['25%']

print df_desc[['mean', 'std', 'cv', 'gfs', 'range', 'range_2']].to_string()

df_prod_prices = df_leclerc[df_leclerc['product'].isin(se_prod_vc[0:1].index)]\
                   [['product', 'price', 'store_id']].copy()
df_prod_prices = df_prod_prices.pivot(index='store_id', columns='product', values='price')
# improve boxplot display
# http://matplotlib.org/examples/pylab_examples/boxplot_demo2.html
# todo: update matplotlib http://stackoverflow.com/questions/21997897/ (ctd)
# changing-what-the-ends-of-whiskers-represent-in-matplotlibs-boxplot-function
ax = df_prod_prices.plot(kind = 'box') #, whis = [0.10, 0.90])
# ax.get_xticklabels()[0].get_text()
# textwrap.fill(ax.get_xticklabels()[0].get_text(), width = 20)
ax.set_xticklabels([textwrap.fill(x.get_text(), 20) for x in ax.get_xticklabels()])
plt.show()

# todo: find most common prod within important categories and draw maps
# todo: restrict to most common prod and run regressions (check robustness?)
# moustache plot by product?

nb_prod = 15

product = se_prod_vc.index[0]
set_prod_stores = set(df_leclerc[df_leclerc['product'] == product]\
                        ['store_id'].values)

ls_set_prod_stores = []
for i, product in enumerate(se_prod_vc.index[1:nb_prod], start = 1):
  set_prod_stores = set_prod_stores.intersection(set(\
                       df_leclerc[df_leclerc['product'] == product]\
                          ['store_id'].values))
  ls_set_prod_stores.append(set_prod_stores)

ls_stores = list(ls_set_prod_stores[-1])

df_test = df_leclerc[(df_leclerc['product'].isin(se_prod_vc.index[0:nb_prod])) &\
                     (df_leclerc['store_id'].isin(ls_stores))].copy()
se_store_sum = df_test[['store_id', 'price']].groupby('store_id').agg(sum)

df_stores.set_index('store_id', inplace = True)
df_stores['sum'] = se_store_sum

df_stores_comp = df_stores[~df_stores['sum'].isnull()]

df_stores_comp[['Nbr de caisses', 'Nbr emp', 'Surf Vente']].corr()

plt.scatter(df_stores_comp['Surf Vente'].values, df_stores_comp['sum'].values)
plt.show()

plt.scatter(df_stores_comp['Nbr de caisses'].values, df_stores_comp['sum'].values)
plt.show()

plt.scatter(df_stores_comp['Nbr emp'].values, df_stores_comp['sum'].values)
plt.show()

# check competition intensity proxies?
# regions (dist to warehouse?), distance to city center?
# competition as shown by leclerc? prices of competitors?
