#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

pd.set_option('float_format', '{:,.2f}'.format)

path_built_csv = os.path.join(path_data, 'data_supermarkets', 'data_built',
                              'data_qlmc_2007_2012', 'data_csv')

format_str = lambda x: u'{:}'.format(x[:20])

# #######################
# LOAD DF QLMC
# #######################

#dateparse = lambda x: pd.datetime.strptime(x, '%d/%m/%Y')*
df_qlmc = pd.read_csv(os.path.join(path_built_csv, 'df_qlmc.csv'),
                      dtype = {'id_lsa' : str},
                      parse_dates = ['date'],
                      dayfirst = True,
                      infer_datetime_format = True,
                      encoding = 'utf-8')

# ################
# GENERAL OVERVIEW
# ################

# General overview
df_su = (df_qlmc.groupby('period')['date'].agg([min, max])
                .rename(columns = {'min' : 'date_beg',
                                   'max' : 'date_end'}))
df_su['time_span'] = df_su['date_end'] - df_su['date_beg']
df_su['nb_rows'] = df_qlmc.groupby('period')['product'].agg(len)
df_su['nb_prods'] = df_qlmc.groupby('period')['product'].nunique()
df_su['nb_stores'] = df_qlmc.groupby('period')['store'].nunique()
df_su['avg_nb_prods_by_store'] = (df_su['nb_rows'] / df_su['nb_stores']).astype(int)
df_su['price_min'] = df_qlmc.groupby('period')['price'].min()
df_su['price_max'] = df_qlmc.groupby('period')['price'].max()
#df_su['date_beg'] = df_su['date_beg'].apply(lambda x: x.strftime('%d/%m/%Y'))
#df_su['date_end'] = df_su['date_end'].apply(lambda x: x.strftime('%d/%m/%Y'))
df_su.reset_index(inplace = True)

print()
print('General overview of period records')
print(df_su.to_string(index = False))
print()
#print(df_su.to_latex(index = False))

#print()
#print('Overview of period prices:')
#df_su_prices = df_qlmc.groupby('period')['price'].agg('describe').unstack()
#df_su_prices['count'] = df_su_prices.astype(int)
#df_su_prices.reset_index(inplace = True)
#print(df_su_prices.to_string())

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
