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
import matplotlib
import matplotlib.pyplot as plt
import textwrap

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_csv = os.path.join(path_data,
                        'data_supermarkets',
                        'data_built',
                        'data_qlmc_2015',
                        'data_csv_201503')

df_prices = pd.read_csv(os.path.join(path_csv,
                                     'df_prices.csv'))

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'df_stores_final.csv'))

## Most common products
se_prod_vc = df_prices['product'].value_counts()
#print u'\nShow most common products'
#print se_prod_vc[0:30].to_string()

## Most common chains
se_chain_vc = df_prices['store_chain'].value_counts()
#print u'\nShow most common chains'
#print se_chain_vc[0:30].to_string()

# Price distribution of one product at each chain
# todo: make sure each store caries each product only once in data
ls_df_desc = []
ref_product = u'DANONE YAOURT DANONE NATURE 4X125G' # se_prod_vc.index[0]
df_product = df_prices[df_prices['product'] == ref_product]

for chain in se_chain_vc.index[0:30]:
  ls_df_desc.append(df_product[df_product['store_chain'] == chain]['price'].describe())
df_desc = pd.concat(ls_df_desc, keys = se_chain_vc.index[0:30], axis = 1)
df_desc = df_desc.T

df_desc['cv'] = df_desc['std'] / df_desc['mean']
df_desc['gfs'] = df_desc['mean'] - df_desc['min']
df_desc['range'] = df_desc['max'] - df_desc['min']
df_desc['range_2'] = df_desc['75%'] - df_desc['25%']

#print df_desc[['count', 'mean', 'std', 'cv', 'gfs', 'range', 'range_2']].to_string()
print df_desc.to_string()

# following filled with nan... must be better way
df_prod_prices = df_product.pivot(index='store_id',
                                  columns='store_chain',
                                  values='price')
# improve boxplot display
# http://matplotlib.org/examples/pylab_examples/boxplot_demo2.html
# todo: update matplotlib http://stackoverflow.com/questions/21997897/ (ctd)
# changing-what-the-ends-of-whiskers-represent-in-matplotlibs-boxplot-function

ls_sb = ['INTERMARCHE',
         'SUPER U',
         'CARREFOUR',
         'LECLERC',
         'AUCHAN',
         'GEANT CASINO']

ax = df_prod_prices[ls_sb].plot(kind = 'box') #, whis = [0.10, 0.90])

# ax.get_xticklabels()[0].get_text()
# textwrap.fill(ax.get_xticklabels()[0].get_text(), width = 20)
ax.set_xticklabels([textwrap.fill(x.get_text(), 20) for x in ax.get_xticklabels()])
plt.show()

# todo: find most common prod within important categories and draw maps
# todo: restrict to most common prod and run regressions (check robustness?)
# moustache plot by product?
