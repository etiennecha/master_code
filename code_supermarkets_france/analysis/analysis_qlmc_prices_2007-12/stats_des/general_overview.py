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

# #######################
# LOAD DF QLMC
# #######################

dateparse = lambda x: pd.datetime.strptime(x, '%d/%m/%Y')
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      dtype = {'id_lsa' : str},
                      parse_dates = ['date'],
                      encoding = 'utf-8')

# ################
# GENERAL OVERVIEW
# ################

## BUILD DATETIME DATE COLUMN

# DF DATES
df_go_date = df_qlmc[['date', 'period']].groupby('period').agg([min, max])['date']
df_go_date['spread'] = df_go_date['max'] - df_go_date['min']

# DF ROWS
df_go_rows = df_qlmc[['product', 'period']].groupby('period').agg(len)

# DF UNIQUE STORES / PRODUCTS
df_go_unique = df_qlmc[['product', 'store', 'period']]\
                       .groupby('period').agg(lambda x: len(x.unique()))

# DF GO
df_go = pd.merge(df_go_date, df_go_unique, left_index = True, right_index = True)
df_go['nb_rows'] = df_go_rows['product']
for field in ['nb_rows', 'store', 'product']:
  df_go[field] = df_go[field].astype(float) # to have thousand separator
df_go['date_start'] = df_go['min'].apply(lambda x: x.strftime('%d/%m/%Y'))
df_go['date_end'] = df_go['max'].apply(lambda x: x.strftime('%d/%m/%Y'))
df_go['avg_nb_prods_by_store'] = df_go['nb_rows'] / df_go['store']
df_go.rename(columns = {'store' : 'nb_stores',
                        'product' : 'nb_prods'},
             inplace = True)
df_go.reset_index(inplace = True)

lsd0 = ['period', 'date_start', 'date_end',
        'nb_rows', 'nb_stores', 'nb_prods',
        'avg_nb_prods_by_store']

pd.set_option('float_format', '{:4,.0f}'.format)

print()
print('General overview of period records')

print()
print('String version:')
print(df_go[lsd0].to_string(index = False))

print()
print('Latex version:')
print(df_go[lsd0].to_latex(index = False))

pd.set_option('float_format', '{:4,.2f}'.format)
format_str = lambda x: u'{:}'.format(x[:20])

print()
print('Overview of period prices:')
# To check consistency... else compute product avg price first?
ls_se_per_prices_desc = []
for per in range(13):
 se_per_prices = df_qlmc['price'][df_qlmc['period'] == per]
 ls_se_per_prices_desc.append(se_per_prices.describe())
df_per_prices_desc = pd.concat(ls_se_per_prices_desc, axis = 1, keys = range(13)).T
df_per_prices_desc['count'] = df_per_prices_desc.astype(int)
print(df_per_prices_desc.to_string())

# ##########################
# OVERVIEW OF EACH PERIOD
# ##########################

# Overview of product families / sections and prices per period

for per in range(13):
  df_qlmc_per = df_qlmc[df_qlmc['period'] == per]
  df_pero = df_qlmc_per[['product', 'price']].groupby('product').\
              agg([len, np.median, np.mean, np.std, min, max])['price']
  df_pero['spread'] = df_pero['max'] - df_pero['min']
  df_pero['r_spread'] = (df_pero['max'] - df_pero['min']) / df_pero['mean']
  df_pero['cv'] = df_pero['std'] / df_pero['mean']
  df_pero['len'] = df_pero['len'].astype(int)
  
  print()
  print(u'-'*80)
  print('Stats descs: per', per)
  
  # Top XX most and least common products
  print()
  print('Top 10 most and least common products')
  df_pero.sort('len', inplace = True, ascending = False)
  df_temp = pd.concat([df_pero[0:10], df_pero[-10:]])
  print(df_temp.to_string())
  #df_temp.reset_index(inplace = True)
  #print(df_temp.to_string(formatters = {'product' : format_str}))
  
  # Top XX most and lest expensive products
  print()
  print('Top 10 most and least expensive products')
  df_pero.sort('mean', inplace = True, ascending = False)
  print(pd.concat([df_pero[0:10], df_pero[-10:]]).to_string())
  
  # Top XX highest spread (or else but look for errors!)
  print()
  print('Top 10 highest relative spread products')
  df_pero.sort('r_spread', inplace = True, ascending = False)
  print(df_pero[0:10].to_string())
  
  # Get section / families (incl nb products by family)
  print()
  print('Nb of products in famille by rayon')
  df_qlmc_per_rp =\
    df_qlmc_per[['section', 'family', 'product']].\
      drop_duplicates(['section', 'family', 'product'])
  se_families = pd.pivot_table(data = df_qlmc_per_rp,
                               index = ['section', 'family'],
                               aggfunc = len,
                               fill_value = 0).astype(int)['product']
  print(se_families.to_string())
