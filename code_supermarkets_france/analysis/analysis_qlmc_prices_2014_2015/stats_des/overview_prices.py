#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

path_built = os.path.join(path_data, 'data_supermarkets', 'data_built')
path_built_csv = os.path.join(path_built, 'data_qlmc_2014_2015', 'data_csv')
path_built_lsa_csv = os.path.join(path_built, 'data_lsa', 'data_csv')

pd.set_option('display.max_colwidth', 40)
pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##########
# LOAD DATA
# ##########

# LOAD DF PRICES
df_prices = pd.read_csv(os.path.join(path_built_csv, 'df_prices_201503.csv'),
                        encoding = 'utf-8')
# store chain harmonization per qlmc
ls_replace_chains = [['HYPER U', 'SUPER U'],
                     ['U EXPRESS', 'SUPER U'],
                     ['HYPER CASINO', 'CASINO'],
                     ["LES HALLES D'AUCHAN", 'AUCHAN']]
for old_chain, new_chain in ls_replace_chains:
  df_prices.loc[df_prices['store_chain'] == old_chain, 'store_chain'] = new_chain
# drop small chains
ls_drop_chains = [u'SIMPLY MARKET', u'SUPERMARCHE MATCH', u'ATAC', u'MIGROS',  u'RECORD']
df_prices = df_prices[~df_prices['store_chain'].isin(ls_drop_chains)]

# #############
# PREPARE DATA
###############

PD = PriceDispersion()

ls_prod_cols = ['section', 'family', 'product']

PD = PriceDispersion()
df_desc = pd.pivot_table(df_prices,
                         values = 'price',
                         index = ls_prod_cols,
                         aggfunc = [len, np.mean, np.std, PD.cv,
                                    PD.gfs, PD.iq_pct, PD.id_pct])
df_desc.rename(columns = {'len': 'count'}, inplace = True)

df_desc['count'] = df_desc['count'].astype(int)
df_desc['ch_count'] = (
  df_prices[ls_prod_cols + ['store_chain']].groupby(ls_prod_cols)
                                           .agg(lambda x: len(x.unique())))

# Most common prices (and kurtosis / skew)
df_freq = (df_prices[ls_prod_cols + ['price']]
                    .groupby(ls_prod_cols).agg([PD.kurtosis,
                                                PD.skew,
                                                PD.price_1,
                                                PD.price_1_fq,
                                                PD.price_2,
                                                PD.price_2_fq])['price'])
df_freq.columns = [col.replace('PD.', '') for col in df_freq.columns]
df_freq['price_12_fq'] = df_freq[['price_1_fq', 'price_2_fq']].sum(axis = 1)

# Merge
df_overview = pd.merge(df_desc,
                       df_freq,
                       left_index = True,
                       right_index = True,
                       how = 'outer')
df_overview.sort('count', ascending = False, inplace = True)
df_overview = df_overview[df_overview['count'] >= 200]
df_overview.reset_index(drop = False, inplace = True)

lsd0 = df_overview.columns.tolist()

# Buils dummies for most widely available products
for n in [20, 50]:
  df_overview['top_ct_{:d}'.format(n)] = 0
  df_overview['top_ct_{:d}'.format(n)][:n] = 1

# Build dummy for top sales (Nielsen)
ls_top_products = [u'COCA COLA COCA-COLA PET 1.5L',
                   u'COCA COLA COCA-COLA PET 2L',
                   u'CRISTALINE EAU CRISTALINE BOUTEILLE 1.5 LITRE X6',
                   u'CRISTALINE EAU CRISTALINE BOUTEILLE 1.5 LITRE',
                   #u'VITTEL EAU MINÉRALE GRANDE SOURCE VITTEL 6X 1L', # too few6*1.5L..
                   #u'VOLVIC EAU VOLVIC PET 6X0.5L', # tto few 6*1.5L...
                   u'PRESIDENT BEURRE DOUX PRÉSIDENT GASTRONOMIQUE PLAQUETTE 82%MG 250G',
                   u'RICARD RICARD 45° 1 LITRE',
                   u'HEINEKEN BIÈRE HEINEKEN 5D PACK 20X25CL',
                   u'WILLIAM PEEL WHISKY WILLIAM PEEL OLD 40 DEGRÉS 70CL',
                   u'WILLIAM PEEL WHISKY WILLIAM PEEL OLD 40 DÉGRÉS 1 LITRE',
                   u'NUTELLA PÂTE À TARTINER NUTELLA POT 1KG']
df_overview['top_sales'] = 0
df_overview.loc[df_overview['product'].isin(ls_top_products), 'top_sales'] = 1

# Build dummy for top sale brands (Nielsen)
ls_top_brands = ['coca cola', 'cristaline', 'vittel', 'volvic', 'president'
                 'ricard', 'heineken', 'william peel', 'nutella']
df_overview['top_brands'] = 0
for brand in ls_top_brands:
  df_overview.loc[df_overview['product'].str.contains(brand, case = False), 'top_brands'] = 1

# Filter out products with too few chains
df_sub = df_overview[df_overview['ch_count'] >= 4].copy()
# Filter out outliers (4 here): ad hoc... see below
df_sub = df_sub[df_sub['std'] <= 2]

# ############
# STATS DES
##############

print()
print('Stats des national product price distributions:')
print(df_overview[lsd0].describe().to_string())

print()
print('Overview national product price distributions:')
print(df_overview[lsd0][0:50].to_string())

# a few outliers based on std (car batteries)
df_sub.plot(kind = 'scatter', x = 'mean', y = 'std', grid = True)
plt.show()
df_sub.plot(kind = 'scatter', x = 'mean', y = 'cv', grid = True)
plt.show()

print()
for ch_count in [4, 8]:
  print('Overview of products with prices avail. at {:d} chains +'.format(ch_count))
  print(df_sub[df_sub['ch_count'] >= ch_count][lsd0].describe().to_string())

print()
print('Overview of product prices by section')
print(df_sub[['mean', 'section']].groupby('section').agg('describe').unstack())

print()
print('Regressions: price dispersion of "top" products')
for dum in ['top_ct_20', 'top_ct_50', 'top_sales', 'top_brands']:
  print()
  print(smf.ols('cv ~ C(section) + mean + {:s}'.format(dum),
                data = df_sub).fit(cov_type = 'HC0').summary())
  
  print()
  print(smf.ols('price_1_fq ~ C(section) + mean + {:s}'.format(dum),
                data = df_sub).fit(cov_type = 'HC0').summary())

# ############
# INSPECT DATA
# ############

df_ol0 = (df_overview[(df_overview['ch_count'] >= 4) &
                      (df_overview['std'] > 2)])

df_ol1 = (df_overview[(df_overview['ch_count'] >= 4) &
                      (df_overview['cv'] > 0.20)])

## Graph better to understand/visualize
#(df_prices[df_prices['product'] == u'TOTAL ACTIVA 5000 DIESEL 15W40']
#          [['store_chain', 'price']].groupby('store_chain').agg('describe').unstack())

## Outliers based on std
#for prod in df_ol0['product'].values:
#  df_prod = df_prices[df_prices['product'] == prod]
#  plt.hist([df_prod[df_prod['store_chain'] == x]['price'].values
#                   for x in df_prod['store_chain'].unique()],
#                stacked = True,
#                label = list(df_prod['store_chain'].unique()))
#  plt.title(prod)
#  plt.legend()
#  plt.grid(True)
#  plt.show()
#
## Outliers based on CV (less clear cut)
#for prod in df_ol1['product'][0:2].values:
#  df_prod = df_prices[df_prices['product'] == prod]
#  plt.hist([df_prod[df_prod['store_chain'] == x]['price'].values
#                   for x in df_prod['store_chain'].unique()],
#                stacked = True,
#                label = list(df_prod['store_chain'].unique()))
#  plt.title(prod)
#  plt.legend()
#  plt.grid(True)
#  plt.show()
#
## Most common products
#for prod in ls_top_products[0:2]:
#  df_prod = df_prices[df_prices['product'] == prod]
#  plt.hist([df_prod[df_prod['store_chain'] == x]['price'].values
#                   for x in df_prod['store_chain'].unique()],
#                stacked = True,
#                label = list(df_prod['store_chain'].unique()))
#  plt.title(prod)
#  plt.legend()
#  plt.grid(True)
#  plt.show()

# ###########
# BACKUP
# ###########

## Product price distributions

#df_desc = pd.pivot_table(df_prices,
#                         values = 'price',
#                         index = ls_prod_cols,
#                         aggfunc = 'describe').unstack()
#df_desc['cv'] = df_desc['std'] / df_desc['mean']
#df_desc['iq_rg'] = df_desc['75%'] - df_desc['25%']
#df_desc['iq_pct'] = df_desc['75%'] / df_desc['25%']
#df_desc.drop(['25%', '75%'], axis = 1, inplace = True)

#print()
#print('Overview top purchased (likely) products:')
#print(df_sub[df_sub['dtp'] == 1].to_string())
#
#df_sub.drop(['dtp', 'dtb'], axis = 1, inplace = True)
#for var, ascending in [('cv', True),
#                       ('cv', False),
#                       ('price_1_fq', True),
#                       ('price_1_fq', False)]:
#  print()
#  print('Overview products with higher or lowest {:s}:'.format(var))
#  df_sub.sort(var, ascending = ascending, inplace = True)
#  print(df_sub[0:20].to_string(index = False))
