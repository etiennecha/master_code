#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      parse_dates = ['date'],
                      dayfirst = True,
                      encoding = 'utf-8')

# todo: check mapping product vs. section/family (if not done?)
df_products = df_qlmc[['period', 'product',
                       'product_brand', 'product_name', 'product_format',
                       'section', 'family']].drop_duplicates()

# consistency with 2015 analysis
df_prices = df_qlmc

# #####################
# ADD NB OBS BY PRODUCT
# #####################

ls_prod_cols = ['period', 'section', 'family', 'product']
se_prod_vc = df_prices[ls_prod_cols].groupby(ls_prod_cols).agg(len)

df_prices.set_index(ls_prod_cols, inplace = True)
df_prices['nb_obs'] = se_prod_vc
df_prices.reset_index(drop = False, inplace = True)

df_products.set_index(ls_prod_cols, inplace = True)
df_products['nb_obs'] = se_prod_vc
df_products.reset_index(drop = False, inplace = True)

PD = PriceDispersion()

df_stats = df_prices[ls_prod_cols + ['price']]\
             .groupby(ls_prod_cols).agg([len,
                                         np.mean,
                                         np.std,
                                         min,
                                         np.median,
                                         max,
                                         PD.cv,
                                         PD.iq_rg,
                                         PD.id_rg,
                                         PD.minmax_rg])['price']
df_stats.rename(columns = {'len': 'nb_obs',
                           'median' : 'med'},
                inplace = True)
df_stats['nb_obs'] = df_stats['nb_obs'].astype(int)

print()
print(u'General overview')
print(df_stats.describe().to_string())

print()
print(u'Inspect large minmax ranges')
df_stats.sort('minmax_rg', ascending = False, inplace = True)
print(df_stats[0:30].to_string())

print()
print(u'Inspect large id ranges')
df_stats.sort('id_rg', ascending = False, inplace = True)
print(df_stats[0:30].to_string())

print()
print(u'Inspect large cvs')
df_stats.sort('cv', ascending = False, inplace = True)
print(df_stats[0:30].to_string())

print()
print(u'Inspect top nb_obs')
df_stats.sort('nb_obs', ascending = False, inplace = True)
print(df_stats[0:30].to_string())

# PRODUCT SECTIONS
df_prods = df_prices[ls_prod_cols + ['nb_obs']].drop_duplicates(ls_prod_cols)
print()
print(u'Product sections')
df_sections = pd.pivot_table(data = df_prods[['period', 'section', 'product']],
                             index = 'section',
                             columns = 'period',
                             aggfunc = len,
                             fill_value = 0).astype(int)['product']
print(df_sections.to_string())

# PRODUCT FAMILIES
print()
print(u'Product families')
df_families = pd.pivot_table(data = df_prods[['period', 'section', 'family', 'product']],
                             index = ['section', 'family'],
                             columns = 'period',
                             aggfunc = len,
                             fill_value = 0).astype(int)['product']
print(df_families.to_string())

# #######################
# BASKET COMPO BY SECTION
# #######################

# todo: add product mean price to have idea of value

df_products_p = df_products[df_products['period'] == 12].copy()
df_products_p.sort('nb_obs', ascending = False, inplace = True)

df_sections_p_rep = pd.concat([df_products_p['section'].value_counts(),
                               df_products_p['section'].value_counts(normalize = True) * 100],
                              axis = 1,
                              keys = ['Nb prod', 'Share (%)'])
print()
print(df_sections_p_rep.to_string(float_format = format_float_int))

# ##############################
# COMPARE FAMILY IN PER 9 VS. 10
# ##############################

ls_prod_cols_np = ls_prod_cols[1:]
df_prods_a = df_prices[df_prices['period'] == 9]\
                      [ls_prod_cols_np].drop_duplicates(ls_prod_cols_np)
df_prods_b = df_prices[df_prices['period'] == 10]\
                      [ls_prod_cols_np].drop_duplicates(ls_prod_cols_np)

df_prods_ab = pd.merge(df_prods_a,
                       df_prods_b,
                       on = 'product',
                       how = 'inner',
                       suffixes = ('_a', '_b'))

df_sections_ab = pd.pivot_table(data = df_prods_ab[['product', 'section_a', 'section_b']],
                                index = 'section_a',
                                columns = 'section_b',
                                aggfunc = len,
                                fill_value = 0).astype(int)['product']

print()
print('Sections: per 9 vs. per 10')
print(df_sections_ab.to_string())

df_families_ab = pd.pivot_table(data = df_prods_ab[['product', 'family_a', 'family_b']],
                                index = 'family_a',
                                columns = 'family_b',
                                aggfunc = len,
                                fill_value = 0).astype(int)['product']

#print()
#print('Families: per 9 vs. per 10')
#for row_i, row in df_families_ab.iterrows():
#  print()
#  print(row_i)
#  for k,v in row[row > 0].to_dict().items():
#    print(k, v)
