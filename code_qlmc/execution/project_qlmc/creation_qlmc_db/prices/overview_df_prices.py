#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')

path_dir_source_json = os.path.join(path_dir_qlmc, 'data_source', 'data_json_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

ls_json_files = [u'200705_releves_QLMC',
                 u'200708_releves_QLMC',
                 u'200801_releves_QLMC',
                 u'200804_releves_QLMC',
                 u'200903_releves_QLMC',
                 u'200909_releves_QLMC',
                 u'201003_releves_QLMC',
                 u'201010_releves_QLMC', 
                 u'201101_releves_QLMC',
                 u'201104_releves_QLMC',
                 u'201110_releves_QLMC', # "No brand" starts to be massive
                 u'201201_releves_QLMC',
                 u'201206_releves_QLMC']

qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))

# 32bit: can load only up to 5 enriched files (8 w/o) 
print u'\nReading json qlmc price records:'
ls_ls_records = []
for json_file in ls_json_files:
  print json_file
  ls_records = dec_json(os.path.join(path_dir_source_json, json_file))
  ls_ls_records.append(ls_records)

# ##############################
# EXTRACT STORE AND PRODUCT LIST
# ##############################

print u'\nExtract stores per period to json'
ls_ls_stores = []
for ls_records in ls_ls_records:
  ls_stores = list(set([record[3] for record in ls_records]))
  ls_ls_stores.append(ls_stores)
enc_json(ls_ls_stores, os.path.join(path_dir_built_json, 'ls_ls_stores'))

print u'\nExtract products per period to json'
ls_ls_products = []
for ls_records in ls_ls_records:
  set_products = set()
  for record in ls_records:
    set_products.add(tuple(record[0:3]))
  ls_ls_products.append([list(x) for x in list(set_products)])
enc_json(ls_ls_products,
         os.path.join(path_dir_built_json, 'ls_ls_products.json'))

# #######################
# BUILD DF QLMC
# #######################

print u'\nBuild df_qlmc prices'
ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin', 'Prix', 'Date']
ls_rows = [[i] + record for i, ls_records in enumerate(ls_ls_records)\
             for record in ls_records]
df_qlmc = pd.DataFrame(ls_rows, columns = ls_columns)

df_qlmc['Prix'] = df_qlmc['Prix'].astype(np.float32)

# MERGE DF QLMC STORES

print u'\nAdd store lsa indexes'
df_stores = pd.read_csv(os.path.join(path_dir_built_csv,
                             'df_qlmc_stores.csv'),
                        dtype = {'id_lsa': str,
                                 'INSE_ZIP' : str,
                                 'INSEE_Dpt' : str,
                                 'INSEE_Code' : str,
                                 'QLMC_Dpt' : str},
                        encoding = 'UTF-8')
# todo: do before and drop
df_stores['Magasin'] = df_stores['Enseigne'] + u' ' + df_stores['Commune']
df_qlmc = pd.merge(df_stores,
                   df_qlmc,
                   on = ['P', 'Magasin'],
                   how = 'right')

# MERGE DF QLMC PRODUCTS

print u'\nAdd product std names and info'
df_products = pd.read_csv(os.path.join(path_dir_built_csv,
                                       'df_qlmc_products.csv'),
                          encoding='utf-8')
df_qlmc = pd.merge(df_products,
                   df_qlmc,
                   on = 'Produit',
                   how = 'right')

# BUILD NORMALIZED PRODUCT INDEX (needed? rather inter periods?)
print u'\nAdd Produit_norm: normalized product name'
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
# REMEDIATION TO PERIOD PBMS
# ##########################

# Check min, max price by period
print '\nPeriod min and max price:'
for per in range(13):
 df_per_prices = df_qlmc['Prix'][df_qlmc['P'] == per]
 print 'Period', per, ':', df_per_prices.min(), df_per_prices.max()

# Check if only one Famille/Rayon per product within each period
print '\nExamination of Rayon and Famille by product:'
for per in range(13):
  ls_col_temp = ['P', 'Rayon', 'Famille', 'Produit_norm', 'marque', 'nom', 'format']
  df_products_per_st = df_qlmc[ls_col_temp][df_qlmc['P'] == per].\
                         drop_duplicates(subset = ['marque', 'nom', 'format', 'Rayon', 'Famille'])
  df_products_per = df_qlmc[ls_col_temp][df_qlmc['P'] == per].\
                      drop_duplicates(subset = ['marque', 'nom', 'format'])
  if len(df_products_per) == len(df_products_per_st):
    print 'Rayon / Famille regular for period:', per
  else:
    print 'Rayon / Famille can differ for the same product in period:', per

# Drop "perfect" duplicates: same period, same product, same store and same price
df_qlmc.drop_duplicates(subset = ['P', 'Magasin', 'Produit_norm', 'Prix'],
                        inplace = True)

# Period 0:
## Duplicates: probably two stores(check further)
#df_inspect = df_qlmc[['Produit_norm', 'Prix', 'Date']]\
#               [(df_qlmc['Magasin'] == u'GEANT CARCASSONNE') &\
#                (df_qlmc['P'] == 0)].copy()
#df_inspect.sort(['Produit_norm', 'Date'], inplace = True)
#print df_inspect[0:100].to_string()
df_qlmc = df_qlmc[~((df_qlmc['P'] == 0) & (df_qlmc['Magasin'] == u'GEANT CARCASSONNE'))].copy()

# Period 7
## Look for highest legitimate price
#print df_qlmc['Prix'][(df_qlmc['P'] == 7) &\
#                      (df_qlmc['Produit_norm'] == u"Mumm Cordon rouge champagne brut 75cl")].max()
## All those between 10 and 35 appear legit
#print df_qlmc['Produit_norm'][(df_qlmc['P'] == 7) &\
#                              (df_qlmc['Prix'] >= 10) &\
#                              (df_qlmc['Prix'] <= 35)].value_counts()
## Products the price of which is above 35 and should not
#print df_qlmc['Produit_norm'][(df_qlmc['P'] == 7) &\
#                              (df_qlmc['Prix'] >= 35)].value_counts().to_string()
df_qlmc.loc[(df_qlmc['P'] == 7) &\
            (df_qlmc['Prix'] >= 35), 'Prix'] =\
  df_qlmc.loc[(df_qlmc['P'] == 7) &\
              (df_qlmc['Prix'] >= 35), 'Prix'] / 100

# Period 6, 8, 9:

# Spread above 7/8 (makes sense... but won't capture high value goods)
for per in [6, 8, 9]:
  df_qlmc_per = df_qlmc[df_qlmc['P'] == per]
  df_pero = df_qlmc_per[['Produit_norm', 'Prix']].groupby('Produit_norm').\
              agg([len, np.median, np.mean, np.std, min, max])['Prix']
  df_pero['spread'] = df_pero['max'] - df_pero['min']
  ls_fix = list(df_pero.index[df_pero['spread'] > 8])
  df_qlmc.loc[(df_qlmc['P'] == per) &\
              (df_qlmc['Produit_norm'].isin(ls_fix)) &\
              (df_qlmc['Prix'] <= 3.5), 'Prix'] =\
    df_qlmc.loc[(df_qlmc['P'] == per) &\
                (df_qlmc['Produit_norm'].isin(ls_fix)) &\
                (df_qlmc['Prix'] <= 3.5), 'Prix'] * 10

# High value goods... check Produit_norm with high prices of other periods
set_hv = set()
for i in range(6) + [7] + range(10,13):
  df_qlmc_per = df_qlmc[df_qlmc['P'] == i]
  df_pero = df_qlmc_per[['Produit_norm', 'Prix']].groupby('Produit_norm').\
              agg([len, np.median, np.mean, np.std, min, max])['Prix']
  set_hv.update(set(df_pero.index[df_pero['max'] >= 10]))

# Find Produit_norm to fix (+ still need to check for goods not present in other periods)
for per in [6, 8, 9]:
  df_qlmc_per = df_qlmc[df_qlmc['P'] == per]
  df_pero = df_qlmc_per[['Produit_norm', 'Prix']].groupby('Produit_norm').\
              agg([len, np.median, np.mean, np.std, min, max])['Prix']
  df_pero.reset_index(inplace = True)
  ls_fix = list(df_pero['Produit_norm'][(df_pero['mean'] < 5) &\
                                        (df_pero['Produit_norm'].isin(list(set_hv)))])
  df_qlmc.loc[(df_qlmc['P'] == per) &\
              (df_qlmc['Produit_norm'].isin(ls_fix)), 'Prix'] =\
    df_qlmc.loc[(df_qlmc['P'] == per) &\
                (df_qlmc['Produit_norm'].isin(ls_fix)), 'Prix'] * 10

# Annoying duplicates (based on spread / relative spread) => drop low values?
# "Viva Lait TGV demi-écrémé vitaminé 6x50cl"
# in periods: 0, 1, 2, 3, 4, 5, 7, 8, 10

# ##########################
# OVERVIEW OF EACH PERIOD
# ##########################

pd.set_option('float_format', '{:4,.2f}'.format)
format_str = lambda x: u'{:}'.format(x[:20])

for per in range(13):
  print '\n', u'-'*40, '\n'
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
  print '\nTop 20 highest relative spread products'
  df_pero.sort('r_spread', inplace = True, ascending = False)
  print df_pero[0:20].to_string()
  
  # Products with duplicate records
  print '\nDuplicates within period'
  se_dup_bool = df_qlmc.duplicated(subset = ['P', 'Magasin', 'Produit_norm'])
  df_dup = df_qlmc[['P', 'Magasin', 'Produit_norm', 'Prix']][se_dup_bool]
  print df_dup['Produit_norm'][df_dup['P'] == per].value_counts()[0:10]
  ## check if not b/c of Produit_norm losing information
  #df_qlmc['Produit'][(df_qlmc['P'] == 0) &\
  #                   (df_qlmc['Produit_norm'] == u'Viva Lait TGV demi-écrémé vitaminé 6x50cl')].value_counts()
  # df_qlmc['Produit_norm'][(se_dup_bool) & (df_qlmc['P'] == 0)].value_counts()
  
  # A lot of duplicates... get rid but check if smth can be done
  
  ## Summary of Rayons and Familles
  #
  ## Get Rayon DF
  #df_qlmc_r = df_qlmc_per[['Rayon', 'Produit']].groupby('Rayon').agg([len])['Produit']
  #
  ## Get unique Rayons and Famille DF
  #df_qlmc_per_rayons = df_qlmc_per[['Rayon', 'Famille']].drop_duplicates(['Rayon', 'Famille'])
  #df_qlmc_per_familles = df_qlmc_per_prod[['Famille', 'Produit']].groupby('Famille').agg([len])['Produit']
  #df_qlmc_per_familles.reset_index(inplace = True)
  #if len(df_qlmc_per_familles) == len(df_qlmc_per_rayons):
  #  df_pero_su = pd.merge(df_qlmc_per_rayons,
  #                        df_qlmc_per_familles,
  #                        left_on = 'Famille',
  #                        right_on = 'Famille') 
  #
  ## Get SE Famille by Rayon
  #df_qlmc_per_rp = df_qlmc_per[['Rayon', 'Famille', 'Produit']].\
  #                   drop_duplicates(['Rayon', 'Famille', 'Produit'])
  #for rayon in df_qlmc_per_rp['Rayon'].unique():
  #  se_rp_vc = df_qlmc_per_rp['Famille'][df_qlmc_per_rp['Rayon'] == rayon].value_counts()
  #  print '\n', rayon, se_rp_vc.sum()
  #  print se_rp_vc

# ############################
# OVERVIEW DUPLICATES
# ############################

se_dup_bool = df_qlmc.duplicated(subset = ['P', 'Magasin', 'Produit_norm'])
df_dup = df_qlmc[['P', 'Magasin', 'Produit_norm', 'Prix']][se_dup_bool]
for per in range(13):
  print '\nDuplicates in period:', per
  se_dup_vc = df_dup['Produit_norm'][(df_dup['P'] == per)].value_counts()
  ls_dup_prod_1 = list(se_dup_vc.index[se_dup_vc <= 10])
  se_dup_stores = df_dup['Magasin'][df_dup['Produit_norm'].isin(ls_dup_prod_1)].value_counts()
  print '-'*20
  print 'Stores to check:'
  print se_dup_stores[0:10]
  # only significant in periods 1 and 12... check stores (systematic?)
  ls_dup_prod_2 = list(se_dup_vc.index[se_dup_vc > 10])
  print '-'*20
  print 'Products to check:'
  print se_dup_vc[se_dup_vc > 10]

# ############################
# OVERVIEW ACROSS ALL PERIODS
# ############################

## PRODUCTS PRESENT IN ALL PERIODS
#ls_ls_prod = []
#for per in df_qlmc['P'].unique():
#  ls_ls_prod.append(list(df_qlmc['Produit_norm'][df_qlmc['P'] == per].unique()))
#set_prod = set(ls_ls_prod[0])
#for ls_prod in ls_ls_prod[1:]:
#	set_prod.intersection_update(set(ls_prod))
#ls_prod_allp = list(set_prod)
#
## INSPECT/FIX PRICES
#
#df_qlmc.sort('Prix', ascending = False, inplace = True)
#print df_qlmc[['P', 'Produit_norm', 'Prix']][0:100].to_string()
#
## Prices to be divided by 10 (which periods are concerned?)
## todo: increase robustness?
#pr_exception = u'Philips - Cafeti\xe8re filtre Cucina lilas 1000W 1.2L (15 tasses) , X1'
#df_qlmc.loc[(df_qlmc['Prix'] > 35.5) &\
#            (df_qlmc['Produit'] != pr_exception) , 'Prix'] =\
#  df_qlmc.loc[(df_qlmc['Prix'] > 35.5) &\
#              (df_qlmc['Produit'] != pr_exception), 'Prix'] / 100.0
#
## TODO: prices to be multiplied or erased?
#
## Inspect prices by product (regarless of period)
#df_price_su = df_qlmc[['Produit_norm', 'Prix']].groupby('Produit_norm').\
#                agg([np.median, np.mean, np.std, min, max])['Prix']
#df_price_su.sort('mean', inplace = True, ascending = False)
#print df_price_su[0:20].to_string()
#
## Inspect average product prices by period (regarless of period)
#print '\nProduct prices by period (highest variations)'
#ls_se_avg_prices = []
#for i in range(13):
#  df_qlmc_per = df_qlmc[df_qlmc['P'] == i]
#  se_avg_prices = df_qlmc_per[['Produit_norm', 'Prix']].groupby('Produit_norm').agg(np.mean)['Prix']
#  ls_se_avg_prices.append(se_avg_prices)
#df_per_prices = pd.DataFrame(ls_se_avg_prices, index = range(13)).T
#df_per_prices['spread'] = df_per_prices.max(axis = 1) - df_per_prices.min(axis = 1)
#df_per_prices.sort('spread', inplace = True, ascending = False)
#df_per_prices.reset_index(inplace = True)
#print df_per_prices[0:100].to_string()
#
##pr_pbm, period_pbm = u"Gemey Volum'Express mascara noir 10ml", 6
##print df_qlmc[['Magasin', 'Prix']][(df_qlmc['Produit_norm'] == pr_pbm) &\
##                                   (df_qlmc['P'] == period_pbm)].to_string()
##
##pr_pbm, period_pbm = u"Viva Lait TGV demi-écrémé vitaminé 6x50cl", 7
##print df_qlmc[['Magasin', 'Prix']][(df_qlmc['Produit_norm'] == pr_pbm) &\
##                                   (df_qlmc['P'] == period_pbm)].to_string()
#
### Period 6, 8, 9: no good for inter period comparison if price above 10?
### Compare mean price with other periods and see if large difference...
### Check if prices are consistent (/10 and rounded?)
##for i in range(13):
##  print '\n', i
##  print df_qlmc[df_qlmc['P'] == i]['Prix'].describe()
#
## Check good average price across periods => see pbms in 6, 8, 9
#
## Get rid of products with several prices records
##print df_qlmc[['Produit_norm', 'P', 'Prix']]\
##        [(df_qlmc['Produit_norm'] == 'Elle & Vire Beurre doux tendre 250g') &\
##         (df_qlmc['id_lsa'] == '1525')].to_string()
#
## TODO: examine duplicates (associated with high/low price: way to solve!)
#se_dup_bool = df_qlmc.duplicated(subset = ['P', 'Magasin', 'Produit_norm'])
#df_dup = df_qlmc[['P', 'Magasin', 'Produit_norm', 'Prix']][se_dup_bool]
#
#df_dup['Produit_norm'][df_dup['P'] == 0].value_counts()[0:10]
#
#df_check = df_qlmc[['P', 'Magasin', 'Produit_norm', 'Prix']]\
#             [(df_qlmc['P'] == 0) &\
#              (df_qlmc['Produit_norm'] == u'Blédina Pêche fraise dès 4 mois 2 s - 260g')].copy()
#df_check.sort('Magasin', inplace = True)
#
#df_check_2 = df_qlmc[['P', 'Magasin', 'Produit_norm', 'Prix']]\
#               [(df_qlmc['P'] == 0) &\
#                (df_qlmc['Produit_norm'] == u'La-pie-qui-chante Menthe claire Bonbons 360g')].copy()
#df_check_2.sort('Magasin', inplace = True)
#print df_qlmc[(df_qlmc['P'] == 0) &\
#              (df_qlmc['Produit_norm'] == u'La-pie-qui-chante Menthe claire Bonbons 360g') &\
#              (df_qlmc['Magasin'] == u'GEANT CARCASSONNE')].T.to_string()
#
##df_qlmc.drop_duplicates(subset = ['P', 'Magasin', 'Produit_norm'],
##                        take_last = True,
##                        inplace = True)
