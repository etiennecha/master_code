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

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# #######################
# LOAD DATA
# #######################

# LOAD DF PRICES

#df_prices = pd.read_csv(os.path.join(path_built_csv,
#                                     'df_prices.csv'),
#                        encoding = 'utf-8')

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                    'df_res_ln_prices.csv'),
                        encoding = 'utf-8')
df_prices['res'] = df_prices['ln_price'] - df_prices['ln_price_hat']

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

# Residual product price distribution
df_desc_2 = pd.pivot_table(df_prices,
                           values = 'res',
                           index = ls_prod_cols,
                           aggfunc = 'describe').unstack()
df_desc_2['iq_rg'] = df_desc_2['75%'] - df_desc_2['25%']
df_desc_2['iq_pct'] = df_desc_2['75%'] / df_desc_2['25%']
# if Q25 null: inf
df_desc_2.loc[~np.isfinite(df_desc_2['iq_pct']),
              'iq_pct'] = np.nan

# Most common prices (and kurtosis / skew): only with raw prices
df_freq = df_prices[ls_prod_cols + ['price']]\
                  .groupby(ls_prod_cols).agg([PD.kurtosis,
                                              PD.skew,
                                              PD.price_1,
                                              PD.price_1_fq,
                                              PD.price_2,
                                              PD.price_2_fq])['price']
df_freq.columns = [col.replace('PD.', '') for col in df_freq.columns]
df_freq['price_12_fq'] = df_freq[['price_1_fq', 'price_2_fq']].sum(axis = 1)

# Merge raw price stats des and freq
df_overview = pd.merge(df_desc,
                       df_freq,
                       left_index = True,
                       right_index = True,
                       how = 'outer')

print()
print('Stats des national product price distributions:')
print(df_overview.describe().to_string())

print()
print('Overview common product price distributions:')
df_overview.sort('count', ascending = False, inplace = True)
df_overview = df_overview[df_overview['count'] >= 200]
print(df_overview[0:20].to_string())

print()
print('Stats des national product price res distributions:')
print(df_desc_2.describe().to_string())

# Merge res price stats des
df_desc_2.drop(['count', '25%', '75%'], axis = 1, inplace = True)
df_overview = pd.merge(df_overview,
                       df_desc_2,
                       left_index = True,
                       right_index = True,
                       suffixes = ('', '_res'),
                       how = 'outer')

df_overview.reset_index(drop = False, inplace = True)

# ########################
# STATS DES
##########################

# FILTER OUT PRODUCTS FOR WHICH TOO FEW CHAINS
df_sub = df_overview[df_overview['ch_count'] >= 4].copy()

## a few outliers based on std (car batteries)
#df_sub = df_sub[df_sub['std'] <= 2]
#df_prices[df_prices['product'] == u'TOTAL ACTIVA 5000 DIESEL 15W40']\
#  [['store_chain', 'price']].groupby('store_chain').agg('describe').unstack()

## todo: restrict view
#for ch_count in [4, 8]:
#  print()
#  print(df_sub[df_sub['ch_count'] >= ch_count].describe().to_string())

for col_disp in ['std', 'cv', 'std_res']:
  df_sub.plot(kind = 'scatter', x = 'mean', y = col_disp)
  plt.show()

# FILTER OUT CATEGORIES WITH TOO FEW PRODUCTS
df_sub = df_sub[~df_sub['section'].isin([u'Bazar et textile',
                                         u'Fruits et Légumes'])]

print()
print(df_sub[['mean', 'section']].groupby('section').agg('describe').unstack())

## REFINE SECTIONS
#df_sub.loc[df_sub['family'].isin([u'Alcools et Apéritifs',
#                                  u'Vins, Champagnes et Cidres']),
#           'section'] = 'Boissons - Alcool'

# ##############
# REGRESSIONS
# ##############

# Regs to run:
# - std of raw prices
# - cv of raw prices
# - freq_1 of raw prices (do not include?)
# - std of res prices

# REG OF STORE PRICE - NAIVE BRAND
ls_formulas = ["std ~ C(section) + mean",
               "cv ~ C(section) + mean",
               "std_res ~ C(section) + mean",
               "iq_rg ~ C(section) + mean",
               "iq_rg_res ~ C(section) + mean"]

ls_res = [smf.ols(formula, data = df_sub).fit() for formula in ls_formulas]

from statsmodels.iolib.summary2 import summary_col
#print(summary_col(ls_res,
#                  stars=True,
#                  float_format='%0.2f'))

print()
print(summary_col(ls_res,
                  stars=True,
                  float_format='%0.3f',
                  model_names=['{:d}'.format(i) for i in range(len(ls_formulas))],
                  info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                             'R2':lambda x: "{:.2f}".format(x.rsquared)}))

print()
print(summary_col(ls_res,
                  stars=True,
                  float_format='%0.3f',
                  model_names=['{:d}'.format(i) for i in range(len(ls_formulas))],
                  info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                             'R2':lambda x: "{:.2f}".format(x.rsquared)}).as_latex())

# todo: stats des by family (mean std)
# (two tables + merge under excel?)
# nb prods / price / std / cv / res std / iq / iq res ?
ls_desc_cols = ['mean', 'std', 'cv', 'std_res', 'iq_rg', 'iq_rg_res']

print()
print('Desc mean table')
print(df_sub[ls_desc_cols + ['section']].groupby('section')\
                                        .agg('mean').to_string())

print('Desc std table')
print(df_sub[ls_desc_cols + ['section']].groupby('section')\
                                        .agg('std').to_string())

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
