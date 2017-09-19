#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import numpy as np
import pandas as pd
from functions_generic_qlmc import *
import matplotlib.pyplot as plt

path_built = os.path.join(path_data, 'data_supermarkets', 'data_built')
path_built_csv = os.path.join(path_built, 'data_qlmc_2014_2015', 'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

df_prices = pd.read_csv(os.path.join(path_built_csv, 'df_prices_201503.csv'),
                        encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv, 'df_stores_final_201503.csv'),
                        encoding = 'utf-8')

df_qlmc_comparisons = pd.read_csv(os.path.join(path_built_csv,
                                               'df_qlmc_competitors_201503.csv'),
                                  encoding = 'utf-8')

ls_prod_cols = ['section', 'family', 'product']
df_products = (df_prices[ls_prod_cols + ['price']].groupby(ls_prod_cols)
                                                  .agg([len, 'mean'])['price'])
df_products.reset_index(drop = False, inplace = True)
df_products.rename(columns = {'len': 'nb_obs'}, inplace = True)

# ##################
# STATS DES PRODUCTS
# ##################

## Check record dates (move)
#df_prices['date'] = pd.to_datetime(df_prices['date'], format = '%d/%m/%Y')
#print df_prices['date'].describe()
## From 2015-02-05 to 2015-03-17
#print len(df_prices[df_prices['date'] < '2015-02-17']) / float(len(df_prices))
## less than 2% obs lost to have only 1 month
#print len(df_prices[df_prices['date'] < '2015-03-01']) / float(len(df_prices))
## only 17% records before 2015-03-01

print()
print(u'Overview nb obs by product:')
print(df_products['nb_obs'].describe())

# Check effect of min nb_obs requirement on section / families
ls_min_nb_obs = [0, 400, 500, 600, 700]

print()
print(u'Weight of each section dpding on min nb obs:')

ls_nb_prods = []
ls_val_prods = []
ls_se_section_len = []
ls_se_section_sum = []
for min_nb_obs in ls_min_nb_obs:
  df_sections = (df_products[df_products['nb_obs'] >= min_nb_obs]
                            [['section', 'mean']].groupby('section')
                                                 .agg([len, sum])['mean'])
  ls_se_section_len.append(df_sections['len'] / df_sections['len'].sum() * 100)
  ls_se_section_sum.append(df_sections['sum'] / df_sections['sum'].sum() * 100)
  ls_nb_prods.append(df_sections['len'].sum())
  ls_val_prods.append(df_sections['sum'].sum())

dict_df_su_sections = {}
for title, ls_se_temp, ls_agg in [['Nb prods', ls_se_section_len, ls_nb_prods],
                                  ['Value prods', ls_se_section_sum, ls_val_prods]]:
  df_su_sections = pd.concat(ls_se_temp,
                             axis = 1,
                             keys = ls_min_nb_obs)
  df_su_sections.ix[title] = ls_agg
  dict_df_su_sections[title] = df_su_sections
  print()
  print(title)
  print(df_su_sections.to_string())

print()
print(u'Weight of each family dpding on min nb obs:')

ls_nb_prods = []
ls_val_prods = []
ls_se_family_len = []
ls_se_family_sum = []
for min_nb_obs in ls_min_nb_obs:
  df_families = (df_products[df_products['nb_obs'] >= min_nb_obs]
                            [['section', 'family', 'mean']]
                            .groupby(['section', 'family'])
                            .agg([len, sum])['mean'])
  ls_se_family_len.append(df_families['len'] / df_families['len'].sum() * 100)
  ls_se_family_sum.append(df_families['sum'] / df_families['sum'].sum() * 100)
  ls_nb_prods.append(df_families['len'].sum())
  ls_val_prods.append(df_families['sum'].sum())

dict_df_su_families = {}
for title, ls_se_temp, ls_agg in [['Nb prods', ls_se_family_len, ls_nb_prods],
                                  ['Value prods', ls_se_family_sum, ls_val_prods]]:
  df_su_families = pd.concat(ls_se_temp,
                             axis = 1,
                             keys = ls_min_nb_obs)
  # df_su_families.ix[title] = ls_agg # breaks multi-index
  dict_df_su_families[title] = df_su_families
  print()
  print(title)
  print(df_su_families.to_string())

# Overview of products (top 50 in nb obs) by section and family

df_products.sort('nb_obs', ascending = False, inplace = True)
df_prod = df_products[['section', 'family', 'product', 'nb_obs']][0:50].copy()
df_prod.set_index(['section', 'family', 'product'], inplace = True)
df_prod.sort_index(inplace = True)
print()
print(u'Top 50 products by section family:')
print(df_prod.to_string())

# todo: section weight by value?
