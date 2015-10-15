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
                      encoding = 'utf-8')
# date parsing slow... better if specified format?

# ################
# GENERAL OVERVIEW
# ################

# BUILD DATETIME DATE COLUMN
print u'\nParse dates'
df_qlmc['Date_str'] = df_qlmc['Date']
df_qlmc['Date'] = pd.to_datetime(df_qlmc['Date'], format = '%d/%m/%Y')

# DF DATES
df_go_date = df_qlmc[['Date', 'Period']].groupby('Period').agg([min, max])['Date']
df_go_date['spread'] = df_go_date['max'] - df_go_date['min']

# DF ROWS
df_go_rows = df_qlmc[['Product', 'Period']].groupby('Period').agg(len)

# DF UNIQUE STORES / PRODUCTS
df_go_unique = df_qlmc[['Product', 'Store', 'Period']].groupby('Period').agg(lambda x: len(x.unique()))

# DF GO
df_go = pd.merge(df_go_date, df_go_unique, left_index = True, right_index = True)
df_go['Nb rows'] = df_go_rows['Product']
for field in ['Nb rows', 'Store', 'Product']:
  df_go[field] = df_go[field].astype(float) # to have thousand separator
df_go['Date start'] = df_go['min'].apply(lambda x: x.strftime('%d/%m/%Y'))
df_go['Date end'] = df_go['max'].apply(lambda x: x.strftime('%d/%m/%Y'))
df_go['Avg nb products/store'] = df_go['Nb rows'] / df_go['Store']
df_go.rename(columns = {'Store' : 'Nb stores',
                        'Product' : 'Nb products'},
             inplace = True)
df_go.reset_index(inplace = True)

pd.set_option('float_format', '{:4,.0f}'.format)

print '\nGeneral overview of period records'

print '\nString version:'
print df_go[['Period', 'Date start', 'Date end',
             'Nb rows', 'Nb stores', 'Nb products', 'Avg nb products/store']].to_string(index = False)

print '\nLatex version:'
print df_go[['Period', 'Date start', 'Date end',
             'Nb rows', 'Nb stores', 'Nb products', 'Avg nb products/store']].to_latex(index = False)

# todo: product categories

# ##########################
# OVERVIEW OF EACH PERIOD
# ##########################

# Check min, max price by period
print '\nPeriod min and max price:'
for per in range(13):
 df_per_prices = df_qlmc['Price'][df_qlmc['Period'] == per]
 print 'Period', per, ':', df_per_prices.min(), df_per_prices.max()

# Overview of product prices per period
pd.set_option('float_format', '{:4,.2f}'.format)
format_str = lambda x: u'{:}'.format(x[:20])

for per in range(13):
  print u'\n', u'-'*80
  print u'-'*80, u'\n'
  print 'Stats descs: per', per
  df_qlmc_per = df_qlmc[df_qlmc['Period'] == per]
  df_pero = df_qlmc_per[['Product', 'Price']].groupby('Product').\
              agg([len, np.median, np.mean, np.std, min, max])['Price']
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
  print df_temp.to_string(formatters = {'Product' : format_str})
  
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
  
  # Summary of Familys and Subfamilys
  
  # Get Family DF
  df_qlmc_r = df_qlmc_per[['Family', 'Product']]\
                .groupby('Family').agg([len])['Product']
  
  # Get unique Familys and Subfamily DF
  df_qlmc_per_rayons =\
     df_qlmc_per[['Family', 'Subfamily']].drop_duplicates(['Family', 'Subfamily'])
  df_qlmc_per_prod = df_qlmc_per.drop_duplicates('Product')
  df_qlmc_per_familles =\
      df_qlmc_per_prod[['Subfamily', 'Product']].groupby('Subfamily').agg([len])['Product']
  df_qlmc_per_familles.reset_index(inplace = True)
  if len(df_qlmc_per_familles) == len(df_qlmc_per_rayons):
    df_pero_su = pd.merge(df_qlmc_per_rayons,
                          df_qlmc_per_familles,
                          left_on = 'Subfamily',
                          right_on = 'Subfamily') 
  
  # Get SE Subfamily by Family
  print '\nNb of products in famille by rayon\n'
  df_qlmc_per_rp =\
    df_qlmc_per[['Family', 'Subfamily', 'Product']].\
      drop_duplicates(['Family', 'Subfamily', 'Product'])
  for rayon in df_qlmc_per_rp['Family'].unique():
    se_rp_vc = df_qlmc_per_rp['Subfamily'][df_qlmc_per_rp['Family'] == rayon].value_counts()
    # display with total line... (function? + add bar?)
    se_rp_vc.ix[rayon] = se_rp_vc.sum()
    len_ind = max([len(x) for x in se_rp_vc.index])
    print u'\n', u'-'*(len_ind + 6)
    print u"{:s}   {:3d}".format(se_rp_vc.index[-1].ljust(len_ind), se_rp_vc[-1])
    print u'-'*(len_ind + 6)
    for i, x in zip(se_rp_vc.index, se_rp_vc)[:-1]:
      print u"{:s}   {:3d}".format(i.ljust(len_ind), x)
    print u'-'*(len_ind + 6)
