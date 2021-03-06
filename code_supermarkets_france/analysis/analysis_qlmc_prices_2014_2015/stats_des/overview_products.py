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

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2014_2015',
                              'data_csv')

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
df_prices = pd.read_csv(os.path.join(path_built_csv, 'df_prices_201503.csv'),
                        encoding = 'utf-8')

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

## need to comment out when outputing section / families
#df_prices = df_prices[df_prices['nb_obs'] >= 200]

PD = PriceDispersion()
df_stats = pd.pivot_table(df_prices,
                          values = 'price',
                          index = ls_prod_cols,
                          aggfunc = [len, np.mean, np.std,
                                     min, np.median, max,
                                     PD.cv, PD.iq_rg, PD.id_rg, PD.minmax_rg])
df_stats.rename(columns = {'len': 'nb_obs',
                           'median' : 'med'},
                inplace = True)
df_stats['nb_obs'] = df_stats['nb_obs'].astype(int)

#df_stats = df_prices[ls_prod_cols + ['price']]\
#             .groupby(ls_prod_cols).agg([len,
#                                         np.mean,
#                                         np.std,
#                                         min,
#                                         np.median,
#                                         max,
#                                         PD.cv,
#                                         PD.iq_rg,
#                                         PD.id_rg,
#                                         PD.minmax_rg])['price']
#df_stats.rename(columns = {'len': 'nb_obs',
#                           'median' : 'med'},
#                inplace = True)
#df_stats['nb_obs'] = df_stats['nb_obs'].astype(int)

print()
print(u'General overview')
print(df_stats.describe().to_string())

for col in ['minmax_rg', 'id_rg', 'cv', 'nb_obs']:
  print()
  print(u'Inspect products with largest {:s}'.format(col))
  df_stats.sort_values(col, ascending = False, inplace = True)
  print(df_stats[0:30].to_string())

# PRODUCT SECTIONS
df_prods = df_prices[ls_prod_cols + ['nb_obs']].drop_duplicates(ls_prod_cols)
print()
print(u'Product sections')
se_sections = pd.pivot_table(data = df_prods[['section', 'product']],
                             index = 'section',
                             aggfunc = len,
                             fill_value = 0).astype(int)['product']
print(se_sections.to_string())

# PRODUCT FAMILIES
print()
print(u'Product families')
se_families = pd.pivot_table(data = df_prods[['section', 'family', 'product']],
                             index = ['section', 'family'],
                             aggfunc = len,
                             fill_value = 0).astype(int)['product']
print(se_families.to_string())

# DF WITH FAMILIES, SECTIONS AND NB OBS (FOR PAPER)
dict_section_families = {}
for (section, family), nb_prods in se_families.iteritems():
  dict_section_families.setdefault(section, [])\
                       .append(u'{:s} ({:d})'.format(family, nb_prods)) 
dict_section_families = {k: '; '.join(v) for k,v in dict_section_families.items()}
se_section_families = pd.Series(dict_section_families)
df_section_families = se_section_families.to_frame()
df_section_families.reset_index(inplace = True, drop = False)
df_section_families['index'] =\
    df_section_families['index'].apply(\
      lambda x: u'{:s} ({:d})'.format(x, se_sections.ix[x]))
df_section_families.rename(columns = {'index' : 'section',
                                      0 : 'families'},
                           inplace = True)

pd.set_option("display.max_colwidth", 10000)
print()
print(df_section_families.to_string(index = False))
pd.set_option("display.max_colwidth", 50)

## todo: detection of very high prices (do with reference prices)
## (typically: observed only at few stores)
#print(df_prices[df_prices['product'] == u'HASBRO LA BONNE PAYE'].to_string())
#print(df_prices[df_prices['product'] == u'GOLIATH TRIOMINOS DE LUXE'].to_string())

# (with high nb obs)
# df_prod = df_prices[df_prices['product'] == 'RICARD RICARD 45° 1 LITRE'].copy()
# df_prod.sort('price', ascending = False, inplace = True)

# ############################
# STATS BY SECTION AND FAMILY
# ############################

# Describe product (mean) price by section
df_stats.reset_index(drop = False, inplace = True)
df_desc = pd.pivot_table(df_stats,
                         values = 'mean',
                         index = ['section'],
                         aggfunc = 'describe').unstack()

## #############################
## GRAPH: DISPERSION BY SECTION
## ############################
#
#fig, ax = plt.subplots()
#for family, c_family in [(u'Colas, Boissons gazeuses et aux Fruits', 'g'),
#                         (u'Eaux', 'b')]:
#  df_temp = df_stats[df_stats['family'] == family]
#  #df_temp = df_temp[(df_temp['len'] >= df_temp['len'].quantile(0.25)) &\
#  #                  (df_temp['mean'] <= df_temp['mean'].quantile(0.75))]
#  ax.plot(df_temp['mean'].values,
#          df_temp['cv'].values,
#          marker = 'o',
#          markersize = 4,
#          linestyle = '',
#          lw = 0,
#          c = c_family,
#          label = family)
#ax.legend()
#plt.show()
