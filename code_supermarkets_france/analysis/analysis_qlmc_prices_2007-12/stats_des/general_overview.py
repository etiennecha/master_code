#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
#path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

# #######################
# BUILD DF QLMC
# #######################

# LOAD DF PRICES

## CSV (no ',' in fields? how is it dealt with?)
print u'Loading qlmc prices'
df_qlmc = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_qlmc_prices.csv'),
                      encoding = 'utf-8')
# date parsing slow... better if specified format?

# MERGE DF QLMC STORES

print u'Adding store lsa indexes'
df_stores = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_qlmc_stores.csv'),
                        dtype = {'id_lsa': str,
                                 'INSE_ZIP' : str,
                                 'INSEE_Dpt' : str,
                                 'INSEE_Code' : str,
                                 'QLMC_Dpt' : str},
                        encoding = 'UTF-8')

df_stores['Magasin'] = df_stores['Enseigne'] + u' ' + df_stores['Commune']
df_qlmc = pd.merge(df_stores,
                   df_qlmc,
                   on = ['P', 'Magasin'],
                   how = 'right')

# MERGE DF QLMC PRODUCTS

print u'Adding product std names and info'
df_products = pd.read_csv(os.path.join(path_dir_built_csv,
                                       'df_qlmc_products.csv'),
                          encoding='utf-8')
df_qlmc = pd.merge(df_products,
                   df_qlmc,
                   on = 'Produit',
                   how = 'right')

# BUILD NORMALIZED PRODUCT INDEX (needed? rather inter periods?)
print u'Adding Produit_norm: normalized product name'
for field in ['marque', 'nom', 'format']:
  df_qlmc[field].fillna(u'', inplace = True)
df_qlmc['Produit_norm'] = df_qlmc['marque'] + ' ' + df_qlmc['nom']+ ' ' + df_qlmc['format']

# ################
# GENERAL OVERVIEW
# ################

## BUILD DATETIME DATE COLUMN
#print u'\nParse dates'
#df_qlmc['Date_str'] = df_qlmc['Date']
#df_qlmc['Date'] = pd.to_datetime(df_qlmc['Date'], format = '%d/%m/%Y')
#
## DF DATES
#df_go_date = df_qlmc[['Date', 'P']].groupby('P').agg([min, max])['Date']
#df_go_date['spread'] = df_go_date['max'] - df_go_date['min']
#
## DF ROWS
#df_go_rows = df_qlmc[['Produit', 'P']].groupby('P').agg(len)
#
## DF UNIQUE STORES / PRODUCTS
#df_go_unique = df_qlmc[['Produit', 'Magasin', 'P']].groupby('P').agg(lambda x: len(x.unique()))
#
## DF GO
#df_go = pd.merge(df_go_date, df_go_unique, left_index = True, right_index = True)
#df_go['Nb rows'] = df_go_rows['Produit']
#for field in ['Nb rows', 'Magasin', 'Produit']:
#  df_go[field] = df_go[field].astype(float) # to have thousand separator
#df_go['Date start'] = df_go['min'].apply(lambda x: x.strftime('%d/%m/%Y'))
#df_go['Date end'] = df_go['max'].apply(lambda x: x.strftime('%d/%m/%Y'))
#df_go['Avg nb products/store'] = df_go['Nb rows'] / df_go['Magasin']
#df_go.rename(columns = {'Magasin' : 'Nb stores',
#                        'Produit' : 'Nb products'},
#             inplace = True)
#df_go.reset_index(inplace = True)
#
#pd.set_option('float_format', '{:4,.0f}'.format)
#
#print '\nGeneral overview of period records'
#
#print '\nString version:'
#print df_go[['P', 'Date start', 'Date end',
#             'Nb rows', 'Nb stores', 'Nb products', 'Avg nb products/store']].to_string(index = False)
#
#print '\nLatex version:'
#print df_go[['P', 'Date start', 'Date end',
#             'Nb rows', 'Nb stores', 'Nb products', 'Avg nb products/store']].to_latex(index = False)

# TODO: product categories

# ##########################
# OVERVIEW OF EACH PERIOD
# ##########################

# Check min, max price by period
print '\nPeriod min and max price:'
for per in range(13):
 df_per_prices = df_qlmc['Prix'][df_qlmc['P'] == per]
 print 'Period', per, ':', df_per_prices.min(), df_per_prices.max()

# Overview of product prices per period
pd.set_option('float_format', '{:4,.2f}'.format)
format_str = lambda x: u'{:}'.format(x[:20])

for per in range(13):
  print u'\n', u'-'*80
  print u'-'*80, u'\n'
  print 'Stats descs: per', per
  df_qlmc_per = df_qlmc[df_qlmc['P'] == per]
  df_pero = df_qlmc_per[['Produit_norm', 'Prix']].groupby('Produit_norm').\
              agg([len, np.median, np.mean, np.std, min, max])['Prix']
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
  print df_temp.to_string(formatters = {'Produit_norm' : format_str})
  
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
  
  # Summary of Rayons and Familles
  
  # Get Rayon DF
  df_qlmc_r = df_qlmc_per[['Rayon', 'Produit_norm']].groupby('Rayon').agg([len])['Produit_norm']
  
  # Get unique Rayons and Famille DF
  df_qlmc_per_rayons =\
     df_qlmc_per[['Rayon', 'Famille']].drop_duplicates(['Rayon', 'Famille'])
  df_qlmc_per_prod = df_qlmc_per.drop_duplicates('Produit_norm')
  df_qlmc_per_familles =\
      df_qlmc_per_prod[['Famille', 'Produit_norm']].groupby('Famille').agg([len])['Produit_norm']
  df_qlmc_per_familles.reset_index(inplace = True)
  if len(df_qlmc_per_familles) == len(df_qlmc_per_rayons):
    df_pero_su = pd.merge(df_qlmc_per_rayons,
                          df_qlmc_per_familles,
                          left_on = 'Famille',
                          right_on = 'Famille') 
  
  # Get SE Famille by Rayon
  print '\nNb of products in famille by rayon\n'
  df_qlmc_per_rp =\
    df_qlmc_per[['Rayon', 'Famille', 'Produit_norm']].\
      drop_duplicates(['Rayon', 'Famille', 'Produit_norm'])
  for rayon in df_qlmc_per_rp['Rayon'].unique():
    se_rp_vc = df_qlmc_per_rp['Famille'][df_qlmc_per_rp['Rayon'] == rayon].value_counts()
    # display with total line... (function? + add bar?)
    se_rp_vc.ix[rayon] = se_rp_vc.sum()
    len_ind = max([len(x) for x in se_rp_vc.index])
    print u'\n', u'-'*(len_ind + 6)
    print u"{:s}   {:3d}".format(se_rp_vc.index[-1].ljust(len_ind), se_rp_vc[-1])
    print u'-'*(len_ind + 6)
    for i, x in zip(se_rp_vc.index, se_rp_vc)[:-1]:
      print u"{:s}   {:3d}".format(i.ljust(len_ind), x)
    print u'-'*(len_ind + 6)

# #############################
# INSPECT LSA DUPLICATE PRICES
# #############################

df_matched = df_stores[~pd.isnull(df_stores['id_lsa'])]
print '\nNb id_lsa associated with two different stores:',\
       len(df_matched[df_matched.duplicated(subset = ['P', 'id_lsa'])])
ls_tup_dup = df_matched[['P', 'id_lsa']]\
               [df_matched.duplicated(subset = ['P', 'id_lsa'])].values

ls_nodup_cols = ['P', 'Magasin', 'Rayon', 'Famille', 'Produit_norm']
df_qlmc_keep = df_qlmc[~df_qlmc['id_lsa'].isnull()]
df_duplicates = df_qlmc_keep[(df_qlmc_keep.duplicated(ls_nodup_cols, take_last = False)) |\
                             (df_qlmc_keep.duplicated(ls_nodup_cols, take_last = True))]

print u'\nNb duplicated rows: {:d}'.format(len(df_duplicates))

print u'\nConcerned stores:'
print df_duplicates[['P', 'id_lsa', 'Magasin']].drop_duplicates(['P', 'Magasin'])

print u'\nInspect some duplicates:'
print df_duplicates[0:30][ls_nodup_cols + ['Prix', 'Magasin', 'Date']].to_string()

# Inspect store
for per, id_lsa in ls_tup_dup:
  print '\nProd for dups', per, id_lsa
  df_store = df_qlmc[(df_qlmc['P'] == per) & (df_qlmc['id_lsa'] == id_lsa)]
  len(df_store[['Produit_norm', 'Prix']]\
        [df_store.duplicated(subset = ['Produit_norm'])])
  ls_prod_dup = df_store['Produit_norm']\
                  [df_store.duplicated(subset = ['Produit_norm'])].values
  print df_store[['Magasin', 'Produit_norm', 'Prix', 'Date']]\
          [df_store['Produit_norm'].isin(ls_prod_dup)].to_string()
# first and last: same store... middle probably not: disambiguate
# probably a mistake: CHAMPION is carrefour contact here:

u'CHAMPION ST GERMAIN DU PUY', '2131' # period 3 and 5
u'CARREFOUR MARKET ST GERMAIN DU PUY', '169094' # period 5
u'CARREFOUR MARKET ST GERMAIN DU PUY', '2131' # period 9 if one believes in surface?
