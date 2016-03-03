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

# adhoc fixes
ls_suspicious_prods = [u'VIVA LAIT TGV 1/2 ÉCRÉMÉ VIVA BP 6X50CL']
df_prices = df_prices[~df_prices['product'].isin(ls_suspicious_prods)]
df_prices['product'] =\
  df_prices['product'].apply(lambda x: x.replace(u'\x8c', u'OE'))

# BUILD DF REF PRICES
def nb_obs(se_prices):
  return len(se_prices)

def price_1(se_prices):
  return se_prices.value_counts().index[0]

def price_1_fq(se_prices):
  return se_prices.value_counts().iloc[0] / float(len(se_prices))

def price_2(se_prices):
  if len(se_prices.value_counts()) > 1:
    return se_prices.value_counts().index[1]
  else:
    return np.nan

def price_2_fq(se_prices):
  if len(se_prices.value_counts()) > 1:
    return se_prices.value_counts().iloc[1] / float(len(se_prices))
  else:
    return 0

# Frequency of most common prices (add dispersion measure?)
df_ref = df_prices[['section', 'family', 'product', 'price']]\
           .groupby(['section', 'family', 'product']).agg([price_1,
                                                           price_1_fq,
                                                           price_2,
                                                           price_2_fq])['price']
df_ref['price_12_fq'] = df_ref[['price_1_fq', 'price_2_fq']].sum(axis = 1)

# General statistics
df_desc = pd.pivot_table(df_prices,
                         values = 'price',
                         index = ['section', 'family', 'product'],
                         aggfunc = 'describe').unstack()
df_desc['cv'] = df_desc['std'] / df_desc['mean']
df_desc['range_iq'] = df_desc['75%'] - df_desc['25%']
df_desc['pct_iq'] = df_desc['75%'] / df_desc['25%']
df_desc.drop(['25%', '75%'], axis = 1, inplace = True)
df_desc['count'] = df_desc['count'].astype(int)

df_disp = pd.merge(df_desc,
                   df_ref,
                   left_index = True,
                   right_index = True,
                   how = 'outer')

df_disp.sort('count', ascending = False, inplace = True)

df_disp = df_disp[df_disp['count'] >= 100]

print('Stats des national product price distributions:')
print(df_disp.describe().to_string())

print('Overview national product price distributions:')
print(df_disp[0:20].to_string())

ls_top_products = [u'COCA COLA COCA-COLA PET 1.5L',
                   u'COCA COLA ZERO COCA-COLA ZERO PET CONTOUR 1,5L',
                   u'CRISTALINE EAU CRISTALINE BOUTEILLE 1.5 LITRE X6',
                   u'CRISTALINE EAU CRISTALINE BOUTEILLE 1.5 LITRE',
                   u'PRESIDENT CAMEMBERT PRÉSIDENT ENTIER 20%MG 250G',
                   u'PRESIDENT EMMENTAL PRESIDENT 28%MG 250G']

## High dispersion on ham?
# u'HERTA JAMBON LE BON PARIS -25% DE SEL HERTA 4TRANCHES 120G',
# u'FLEURY MICHON JAMBON S/COUENNE TENEUR SEL RÉDUIT OMEGA3 4TR.160G'

df_disp.reset_index(drop = False, inplace = True)

df_disp['dtp'] = 0
df_disp.loc[df_disp['product'].isin(ls_top_products), 'dtp'] = 1

ls_top_brands = ['Herta', 'Fleury', 'Coca', 'Cristaline', 'President']
df_disp['dtb'] = 0
for brand in ls_top_brands:
  df_disp.loc[df_disp['product'].str.contains(brand, case = False), 'dtb'] = 1

print(smf.ols('cv ~ C(section) + mean + dtp', data = df_disp).fit().summary())

print(df_disp[df_disp['dtp'] == 1].to_string())

# todo: check extreme cv / iq_range and price freq
df_disp.sort('cv', ascending = False, inplace = True)
print(df_disp[0:10].to_string())

# check product with only Bledina as name???
