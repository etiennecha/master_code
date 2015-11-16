#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import httplib
import urllib, urllib2
import json
import pandas as pd
from functions_generic_qlmc import *
import numpy as np
import matplotlib.pyplot as plt

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

# ###########
# LOAD DATA
# ###########

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

df_prices = df_prices[~((df_prices['family'] == u'Traiteur') &\
                        (df_prices['product'] == u"DANIEL DESSAINT CRÊPES " +\
                                                 u"MOELLEUSE SUCRÉES X8 400G " +\
                                                 u"DANIEL DESSAINT"))]

# todo: move to data building

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        encoding = 'utf-8')

df_qlmc_comparisons = pd.read_csv(os.path.join(path_built_csv,
                                               'df_qlmc_competitors.csv'),
                                  encoding = 'utf-8')

df_products = df_prices[['section', 'family', 'product']].drop_duplicates()

## Check product unicity
#print df_products['product'].value_counts()[0:10]
## one issue detected: treated

# ##################
# STATS DES PRODUCTS
# ##################

se_prod_vc = df_prices['product'].value_counts()
df_products.set_index('product', inplace = True)
df_products['nb_obs'] = se_prod_vc
df_products.sort('nb_obs', ascending = False, inplace = True)

print u'\nOverview nb obs by product:'
print df_products['nb_obs'].describe()

# Weight of each section

print u'\nWeight of each section dpding on min nb obs:'
ls_min_nb_obs = [400, 500, 600, 700]
ls_nb_prods = []
ls_se_section_vc = []
for min_nb_obs in ls_min_nb_obs:
  se_section_vc = df_products[df_products['nb_obs'] >= min_nb_obs]\
                             ['section'].value_counts()
  ls_nb_prods.append(se_section_vc.sum())
  se_section_vc = se_section_vc / se_section_vc.sum() * 100
  ls_se_section_vc.append(se_section_vc)

df_su_sections = pd.concat(ls_se_section_vc,
                           axis = 1,
                           keys = ls_min_nb_obs)
df_su_sections.ix['Nb produits'] = ls_nb_prods
print df_su_sections.to_string()

# Weight of each family (see: groupby to have family and section?)

print u'\nWeight of each family dpding on min nb obs:'
ls_min_nb_obs = [400, 500, 600, 700]
ls_nb_prods = []
ls_se_family_vc = []
for min_nb_obs in ls_min_nb_obs:
  #se_family_vc = df_products[df_products['nb_obs'] >= min_nb_obs]\
  #                          ['family'].value_counts()
  se_family_vc = df_products[df_products['nb_obs'] >= min_nb_obs]\
                            .groupby(['section', 'family']).agg('count')['nb_obs']
  ls_nb_prods.append(se_family_vc.sum())
  se_family_vc = se_family_vc / se_family_vc.sum() * 100
  ls_se_family_vc.append(se_family_vc)

df_su_familys = pd.concat(ls_se_family_vc,
                           axis = 1,
                           keys = ls_min_nb_obs)
## Fix index to keep display
#df_su_familys.ix['Nb produits'] = ls_nb_prods
print df_su_familys.to_string()

# Overview of products (top 50 in nb obs) by section and family

df_products.reset_index(drop = False, inplace = True)
df_prod = df_products[['section', 'family', 'product', 'nb_obs']][0:50].copy()
df_prod.set_index(['section', 'family', 'product'], inplace = True)
df_prod.sort_index(inplace = True)
print u'\nTop 50 products by section family:'
print df_prod.to_string()

# todo: section weight by value?
