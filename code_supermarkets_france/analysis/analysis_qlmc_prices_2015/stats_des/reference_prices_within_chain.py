#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import textwrap

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

# ############
# LOAD DATA
# ############

# LOAD DF PRICES
df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')


# LOAD DF STORES (INCLUDING LSA INFO)
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'c_insee' : str,
                                 'id_lsa' : str},
                        encoding = 'utf-8')

df_lsa = pd.read_csv(os.path.join(path_lsa_csv,
                                  'df_lsa_active.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

df_stores = pd.merge(df_stores,
                     df_lsa[['id_lsa', 'enseigne_alt', 'groupe', 'surface']],
                     on = 'id_lsa',
                     how = 'left')

# BUILD DF QLMC WITH PRICE AND STORE INFO
# Restrict to leclerc (could drop rest?)
df_prices = df_prices[df_prices['store_chain'] == 'LECLERC'].copy()
df_prices.drop(['store_chain'], axis = 1, inplace = True) # in df_stores too
df_qlmc = pd.merge(df_prices,
                   df_stores,
                   left_on = 'store_id',
                   right_on = 'store_id',
                   how = 'left')
df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]

# Avoid error msg on condition number
df_qlmc['surface'] = df_qlmc['surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_price'] = np.log(df_qlmc['price'])
# Control for dpt (region?)
df_qlmc['dpt'] = df_qlmc['c_insee'].str.slice(stop = 2)
pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ################
# STATS DISPERSION
# ################

# Count stores present in data
print()
print(u'Nb Leclerc: {:d}'.format(len(df_qlmc['store_id'].unique())))

# Count products present in data
# (todo: never same product under two families/subfamilies?)
print()
print(u'Nb products: {:d}'.format(len(df_qlmc['product'].unique())))

# Nb of products by leclerc
se_nb_prod = df_qlmc[['store_id', 'product']]\
                       .groupby('store_id').agg([len])['product']
print()
print(u'Describe nb prod by store:')
print(se_nb_prod.describe())

# Most common products
print()
print(u'Show most common products:')
se_prod_vc = df_qlmc['product'].value_counts()
print(se_prod_vc[0:30].to_string())

# Price distribution of most common products
ls_df_desc = []
for product in se_prod_vc.index[0:100]:
  if len(df_qlmc[df_qlmc['product'] == product]['store_id'].unique()) !=\
      se_prod_vc[product]:
    print('Pbm: product {:s} listed twice for one store'.format(product))
  ls_df_desc.append(df_qlmc[df_qlmc['product'] == product]['price'].describe())
df_desc = pd.concat(ls_df_desc, keys = se_prod_vc.index[0:30], axis = 1)
df_desc = df_desc.T

df_desc['cv'] = df_desc['std'] / df_desc['mean']
df_desc['gfs'] = df_desc['mean'] - df_desc['min']
df_desc['range'] = df_desc['max'] - df_desc['min']
df_desc['range_2'] = df_desc['75%'] - df_desc['25%']

print(df_desc[['mean', 'std', 'cv', 'gfs', 'range', 'range_2']].to_string())

df_prod_prices = df_qlmc[df_qlmc['product'].isin(se_prod_vc[0:1].index)]\
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

nb_prod = 100

product = se_prod_vc.index[0]
set_prod_stores = set(df_qlmc[df_qlmc['product'] == product]\
                        ['store_id'].values)

ls_set_prod_stores = []
for i, product in enumerate(se_prod_vc.index[1:nb_prod], start = 1):
  set_prod_stores = set_prod_stores.intersection(set(\
                       df_qlmc[df_qlmc['product'] == product]\
                          ['store_id'].values))
  ls_set_prod_stores.append(set_prod_stores)

ls_stores = list(ls_set_prod_stores[-1])

df_test = df_qlmc[(df_qlmc['product'].isin(se_prod_vc.index[0:nb_prod])) &\
                     (df_qlmc['store_id'].isin(ls_stores))].copy()
se_store_sum = df_test[['store_id', 'price']].groupby('store_id').agg(sum)

df_stores.set_index('store_id', inplace = True)
df_stores['sum'] = se_store_sum

df_stores_comp = df_stores[~df_stores['sum'].isnull()]

#df_stores_comp[['surface']].corr()

plt.scatter(df_stores_comp['surface'].values, df_stores_comp['sum'].values)
plt.show()

# check competition intensity proxies?
# regions (dist to warehouse?), distance to city center?
# competition as shown by leclerc? prices of competitors?
