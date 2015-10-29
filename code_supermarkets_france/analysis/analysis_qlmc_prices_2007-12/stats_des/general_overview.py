#!/usr/bin/env python
# -*- coding: utf-8 -*- 

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

print u'Loading df_qlmc'
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      parse_dates = ['date'],
                      encoding = 'utf-8')

# date parsing slow? specify format?

#print u'\nParse dates'
#df_qlmc['date_str'] = df_qlmc['date']
#df_qlmc['date'] = pd.to_datetime(df_qlmc['date'], format = '%d/%m/%Y')

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
df_go['avg_nb_products_by_store'] = df_go['nb_rows'] / df_go['store']
df_go.rename(columns = {'store' : 'nb_stores',
                        'product' : 'nb_products'},
             inplace = True)
df_go.reset_index(inplace = True)

pd.set_option('float_format', '{:4,.0f}'.format)

print '\nGeneral overview of period records'

lsd0 = ['period', 'date_start', 'date_end',
        'nb_rows', 'nb_stores', 'nb_products',
        'avg_nb_products_by_store']

print '\nString version:'
print df_go[lsd0].to_string(index = False)

print '\nLatex version:'
print df_go[lsd0].to_latex(index = False)

# todo: product categories

# ##########################
# OVERVIEW OF EACH PERIOD
# ##########################

# Check min, max price by period
print '\nperiod min and max price:'
for per in range(13):
 df_per_prices = df_qlmc['price'][df_qlmc['period'] == per]
 print 'period', per, ':', df_per_prices.min(), df_per_prices.max()

# Overview of product prices per period
pd.set_option('float_format', '{:4,.2f}'.format)
format_str = lambda x: u'{:}'.format(x[:20])

for per in range(13):
  print u'\n', u'-'*80
  print u'-'*80, u'\n'
  print 'Stats descs: per', per
  df_qlmc_per = df_qlmc[df_qlmc['period'] == per]
  df_pero = df_qlmc_per[['product', 'price']].groupby('product').\
              agg([len, np.median, np.mean, np.std, min, max])['price']
  df_pero['spread'] = df_pero['max'] - df_pero['min']
  df_pero['r_spread'] = (df_pero['max'] - df_pero['min']) / df_pero['mean']
  df_pero['cv'] = df_pero['std'] / df_pero['mean']
  
  # Top XX most and least common products
  print '\nTop 10 most and least common products'
  df_pero.sort('len', inplace = True, ascending = False)
  #print df_pero[:10].to_string()
  #print df_pero[-10:].to_string()
  df_temp = pd.concat([df_pero[0:10], df_pero[-10:]])
  df_temp.reset_index(inplace = True)
  print df_temp.to_string(formatters = {'product' : format_str})
  
  # Top XX most and lest expensive products
  print '\nTop 10 most and least expensive products'
  df_pero.sort('mean', inplace = True, ascending = False)
  #print df_pero[:10].to_string()
  #print df_pero[-10:].to_string()
  print pd.concat([df_pero[0:10], df_pero[-10:]]).to_string()
  
  # Top XX highest spread (or else but look for errors!)
  print '\nTop 10 highest relative spread products'
  df_pero.sort('r_spread', inplace = True, ascending = False)
  print df_pero[0:10].to_string()
  
  # Summary of sections and familys
  
  # Get section DF
  df_qlmc_r = df_qlmc_per[['section', 'product']]\
                .groupby('section').agg([len])['product']
  
  # Get unique sections and family DF
  df_qlmc_per_rayons =\
     df_qlmc_per[['section', 'family']].drop_duplicates(['section', 'family'])
  df_qlmc_per_prod = df_qlmc_per.drop_duplicates('product')
  df_qlmc_per_familles =\
      df_qlmc_per_prod[['family', 'product']].groupby('family').agg([len])['product']
  df_qlmc_per_familles.reset_index(inplace = True)
  if len(df_qlmc_per_familles) == len(df_qlmc_per_rayons):
    df_pero_su = pd.merge(df_qlmc_per_rayons,
                          df_qlmc_per_familles,
                          left_on = 'family',
                          right_on = 'family') 
  
  # Get SE family by section
  print '\nNb of products in famille by rayon\n'
  df_qlmc_per_rp =\
    df_qlmc_per[['section', 'family', 'product']].\
      drop_duplicates(['section', 'family', 'product'])
  for rayon in df_qlmc_per_rp['section'].unique():
    se_rp_vc = df_qlmc_per_rp['family'][df_qlmc_per_rp['section'] == rayon].value_counts()
    # display with total line... (function? + add bar?)
    se_rp_vc.ix[rayon] = se_rp_vc.sum()
    len_ind = max([len(x) for x in se_rp_vc.index])
    print u'\n', u'-'*(len_ind + 6)
    print u"{:s}   {:3d}".format(se_rp_vc.index[-1].ljust(len_ind), se_rp_vc[-1])
    print u'-'*(len_ind + 6)
    for i, x in zip(se_rp_vc.index, se_rp_vc)[:-1]:
      print u"{:s}   {:3d}".format(i.ljust(len_ind), x)
    print u'-'*(len_ind + 6)
