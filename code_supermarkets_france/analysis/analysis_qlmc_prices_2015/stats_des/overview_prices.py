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

# #######################
# LOAD DATA
# #######################

# LOAD DF PRICES
df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')
# store chain harmonization per qlmc
ls_replace_chains = [['HYPER U', 'SUPER U'],
                     ['U EXPRESS', 'SUPER U'],
                     ['HYPER CASINO', 'CASINO'],
                     ["LES HALLES D'AUCHAN", 'AUCHAN']]
for old_chain, new_chain in ls_replace_chains:
  df_prices.loc[df_prices['store_chain'] == old_chain,
                'store_chain'] = new_chain

# drop small chains
ls_drop_chains = [u'SIMPLY MARKET',
                  u'SUPERMARCHE MATCH',
                  u'ATAC',
                  u'MIGROS',
                  u'RECORD']
df_prices = df_prices[~df_prices['store_chain'].isin(ls_drop_chains)]

# adhoc fixes
ls_suspicious_prods = [u'VIVA LAIT TGV 1/2 ÉCRÉMÉ VIVA BP 6X50CL']
df_prices = df_prices[~df_prices['product'].isin(ls_suspicious_prods)]
df_prices['product'] =\
  df_prices['product'].apply(lambda x: x.replace(u'\x8c', u'OE'))

# ########################
# BUILD DF OVERVIEW
##########################

PD = PriceDispersion()

ls_prod_cols = ['section', 'family', 'product']

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

df_desc['ch_count'] = df_prices[ls_prod_cols + ['store_chain']].groupby(ls_prod_cols)\
                                                               .agg(lambda x: len(x.unique()))

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
df_overview = df_overview[df_overview['count'] >= 200]

# ########################
# STATS DES
##########################

print()
print('Stats des national product price distributions:')
print(df_overview.describe().to_string())

print()
print('Overview national product price distributions:')
print(df_overview[0:20].to_string())

ls_top_products = [u'COCA COLA COCA-COLA PET 1.5L',
                   u'COCA COLA ZERO COCA-COLA ZERO PET CONTOUR 1,5L',
                   u'CRISTALINE EAU CRISTALINE BOUTEILLE 1.5 LITRE X6',
                   u'CRISTALINE EAU CRISTALINE BOUTEILLE 1.5 LITRE',
                   u'PRESIDENT CAMEMBERT PRÉSIDENT ENTIER 20%MG 250G',
                   u'PRESIDENT EMMENTAL PRESIDENT 28%MG 250G']

## High dispersion on ham?
# u'HERTA JAMBON LE BON PARIS -25% DE SEL HERTA 4TRANCHES 120G',
# u'FLEURY MICHON JAMBON S/COUENNE TENEUR SEL RÉDUIT OMEGA3 4TR.160G'

df_overview.reset_index(drop = False, inplace = True)

df_overview['dtp'] = 0
df_overview.loc[df_overview['product'].isin(ls_top_products), 'dtp'] = 1

ls_top_brands = ['Herta', 'Fleury', 'Coca', 'Cristaline', 'President']
df_overview['dtb'] = 0
for brand in ls_top_brands:
  df_overview.loc[df_overview['product'].str.contains(brand, case = False), 'dtb'] = 1

# FILTER OUT PRODUCTS FOR WHICH TOO FEW CHAINS
df_sub = df_overview[df_overview['ch_count'] >= 4].copy()

# a few outliers based on std (car batteries)
df_sub = df_sub[df_sub['std'] <= 2]

df_sub.plot(kind = 'scatter', x = 'mean', y = 'std')
df_sub.plot(kind = 'scatter', x = 'mean', y = 'cv')

for ch_count in [4, 8]:
  print()
  print(df_sub[df_sub['ch_count'] >= ch_count].describe().to_string())

#df_prices[df_prices['product'] == u'TOTAL ACTIVA 5000 DIESEL 15W40']\
#  [['store_chain', 'price']].groupby('store_chain').agg('describe').unstack()

## FILTER OUT CATEGORIES WITH TOO FEW PRODUCTS
#df_sub = df_sub[~df_sub['section'].isin([u'Bazar et textile',
#                                         u'Fruits et Légumes'])]

# todo: check if enough chains represented when price_1_fq low
# todo: check product with only Bledina as name??? (+ short names?)

print()
print(df_sub[['mean', 'section']].groupby('section').agg('describe').unstack())

print()
print(smf.ols('std ~ C(section) + mean + dtp', data = df_sub).fit().summary())

print()
print(smf.ols('cv ~ C(section) + mean + dtp', data = df_sub).fit().summary())

print()
print(smf.ols('price_1_fq ~ C(section) + mean + dtp', data = df_sub).fit().summary())

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
