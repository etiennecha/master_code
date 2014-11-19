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

# Period 0:
## Duplicates: probably two stores(check further)
#df_inspect = df_qlmc[['Produit_norm', 'Prix', 'Date']]\
#               [(df_qlmc['Magasin'] == u'GEANT CARCASSONNE') &\
#                (df_qlmc['P'] == 0)].copy()
#df_inspect.sort(['Produit_norm', 'Date'], inplace = True)
#print df_inspect[0:100].to_string()
df_qlmc = df_qlmc[~((df_qlmc['P'] == 0) & (df_qlmc['Magasin'] == u'GEANT CARCASSONNE'))].copy()

# ##########################
# OVERVIEW OF EACH PERIOD
# ##########################

pd.set_option('float_format', '{:4,.2f}'.format)

for per in range(13):
  print '\n', u'-'*40, '\n'
  print 'Stats descs: per', per
  df_qlmc_per = df_qlmc[df_qlmc['P'] == per]
  df_pero = df_qlmc_per[['Produit_norm', 'Prix']].groupby('Produit_norm').\
              agg([len, np.median, np.mean, np.std, min, max])['Prix']
  df_pero['spread'] = df_pero['max'] - df_pero['min']
  
  # Top XX most and least common products
  print '\nTop 10 most and least common products'
  df_pero.sort('len', inplace = True, ascending = False)
  #print df_pero[:10].to_string()
  #print df_pero[-10:].to_string()
  print pd.concat([df_pero[0:10], df_pero[-10:]]).to_string()
  
  # Top XX most and lest expensive products
  print '\nTop 10 most and least expensive products'
  df_pero.sort('mean', inplace = True, ascending = False)
  #print df_pero[:10].to_string()
  #print df_pero[-10:].to_string()
  print pd.concat([df_pero[0:10], df_pero[-10:]]).to_string()
  
  # Top XX highest spread (or else but look for errors!)
  print '\nTop 20 highest spread products'
  df_pero.sort('spread', inplace = True, ascending = False)
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
#
## STORE LEVEL (could be suited to examine before after..)
#
## 14343 (lsa index) closed on 2009-10-31 i.e. between periods 5 and 6
## impact for 1525 (0 to 12) and 1581 (1 and 6... short)
#
## 10248 closed on 2011-01-01 i.e. beg of period 8 (?)
## impact for 502 (0, 2, 4, 5, 8, 9, 10, 11, 12)
#
#id_lsa = '1525'
#
## Comparison between two periods for one store
#df_temp_1 = df_qlmc[['Produit_norm', 'Prix']][(df_qlmc['P'] == 0) &\
#                                              (df_qlmc['id_lsa'] == id_lsa)].copy()
#df_temp_2 = df_qlmc[['Produit_norm', 'Prix']][(df_qlmc['P'] == 9) &\
#                                              (df_qlmc['id_lsa'] == id_lsa)].copy()
#df_temp_3 = pd.merge(df_temp_1, df_temp_2, on = 'Produit_norm',
#                     how = 'inner', suffixes = ('_1', '_2'))
#df_temp_3['D_value'] = df_temp_3['Prix_2'] - df_temp_3['Prix_1']
#df_temp_3['D_percent'] = df_temp_3['D_value'] / df_temp_3['Prix_1']
#
## Comparison between all periods available for one store
#ls_store_per_ind = [int(x) for x in df_qlmc['P']\
#                     [df_qlmc['id_lsa'] == id_lsa].unique()]
#df_store = df_qlmc[['Produit_norm', 'Prix']][(df_qlmc['P'] == ls_store_per_ind[0]) &\
#                                             (df_qlmc['id_lsa'] == id_lsa)].copy()
#for per_ind in ls_store_per_ind[1:]:
#  df_temp = df_qlmc[['Produit_norm', 'Prix']]\
#              [(df_qlmc['P'] == per_ind) &\
#               (df_qlmc['id_lsa'] == id_lsa)]
#  df_store = pd.merge(df_store,
#                      df_temp,
#                      on = 'Produit_norm',
#                      how = 'outer', suffixes = ('', '_{:02d}'.format(per_ind)))
#
## Finally harmonize first Prix column name
#df_store.rename(columns = {'Prix': 'Prix_00'}, inplace = True)
#df_store.columns = [x.replace('Prix_', 'P') for x in df_store.columns]
#
## Trivial mistake in price reported: look for problems by product
## might need to add price folder and work on prices
#
#print df_store[0:10].to_string()

# #############################################
# ONE LSA IND FOR TWO STORE NAMES WITHIN PERIOD
# #############################################

#len(df_qlmc[(df_qlmc['P'] == 9) &\
#            (df_qlmc['Commune'] == 'CARREFOUR MARKET CLERMONT CARRE JAUDE')])
#len(df_qlmc[(df_qlmc['P'] == 9) &\
#            (df_qlmc['Commune'] == 'CARREFOUR MARKET CLERMONT FERRAND JAUDE')])
#
#len(df_qlmc[(df_qlmc['P'] == 5) & (df_qlmc['Magasin'] == 'CHAMPION ST GERMAIN DU PUY')])
#len(df_qlmc[(df_qlmc['P'] == 5) & (df_qlmc['Magasin'] == 'CARREFOUR MARKET ST GERMAIN DU PUY')])
#
#len(df_qlmc[(df_qlmc['P'] == 4) & (df_qlmc['Magasin'] == 'SUPER U ANGERS BOURG DE PAILLE')])
#len(df_qlmc[(df_qlmc['P'] == 4) & (df_qlmc['Magasin'] == 'SUPER U BEAUCOUZE')])
#
#df_pbm = df_qlmc[(df_qlmc['P'] == 4) & ((df_qlmc['Magasin'] == 'SUPER U BEAUCOUZE') |\
#                                        (df_qlmc['Magasin'] == 'SUPER U ANGERS BOURG DE PAILLE'))].copy()
#df_pbm.sort(columns = ['Produit'], inplace = True)
#se_vc_pbms = df_pbm['Produit'].value_counts()
#df_pbm[df_pbm['Produit'] == u'Elle & Vire - Beurre doux tendre, 250g']


## ########################
## DATE PARSING
## ########################
#
#df_qlmc['Date_2'] = pd.to_datetime(df_qlmc['Date'], format = '%d/%m/%Y')
#for i in range(13):
#  print u'Beg of period {:2d}'.format(i), df_qlmc['Date_2'][df_qlmc['P'] == i].min()
#  print u'End of period {:2d}'.format(i), df_qlmc['Date_2'][df_qlmc['P'] == i].max()
## todo: check dates by store

# ########################
# ALL PERIODS: STATS DES
# ########################

## todo: write python object stats des generic functions
#
## (Survival) Products across periods
## todo: check for minor product name differences? (e.g. within brands...?)
#dict_product_periods = {}
#for i, ls_period_products in enumerate(dict_describe['product']):
#	for product in ls_period_products:
#		dict_product_periods.setdefault(product, []).append(i)
#
#dict_product_stats = {key: value for key, value in [i for i in itertools.product(range(15), [0])]}
#for shop, list_product_periods in dict_product_periods.iteritems():
#  dict_product_stats[len(list_product_periods)] += 1
#
## (Survival) Stores across periods
#dict_store_periods = {}
#for i, ls_period_stores in enumerate(dict_describe['store']):
#	for store in ls_period_stores:
#		dict_store_periods.setdefault(store, []).append(i)
#
#dict_store_stats = {key: value for key, value in [i for i in itertools.product(range(15), [0])]}
#for shop, ls_store_periods in dict_store_periods.iteritems():
#  dict_store_stats[len(ls_store_periods)] += 1

## Evo of prices among surviving stores (generalize)
#ls_prod_0 = df_qlmc['Produit'][df_qlmc['P'] == 0].unique()
#ls_prod_8 = df_qlmc['Produit'][df_qlmc['P'] == 8].unique()
#ls_prod_08 = [x for x in ls_prod_0 if x in ls_prod_8]
#ls_store_0 = df_qlmc['Magasin'][df_qlmc['P'] == 0].unique()
#ls_store_8 = df_qlmc['Magasin'][df_qlmc['P'] == 8].unique()
#ls_store_08 = [x for x in ls_store_0 if x in ls_store_8]
#for x in ls_store_08:
#  df_mag_prod = df_qlmc[(df_qlmc['Magasin'] == x) & (df_qlmc['Produit'] == ls_prod_08[0])]
#  ls_mag_prod_periods = df_mag_prod['P'].unique()
#  if 0 in ls_mag_prod_periods and 8 in ls_mag_prod_periods:
#    print '\n', x
#    print df_mag_prod[['P', 'Produit', 'Prix']]

## Can check evolution of products of same brand
## Draw evo of prices of different formats of Coca Cola at various stores

# ##################
# PRODUCT DISPERSION
# ##################

## Check product dispersion
#ex_product = u'Nutella - Pâte à tartiner chocolat noisette, 400g'
#ex_se_prices = df_qlmc[u'Prix'][(df_qlmc[u'Produit'] == ex_product) &\
#                                   (df_qlmc[u'P'] == 1)]
#ex_pd = compute_price_dispersion(ex_se_prices)
#df_ex_pd = pd.DataFrame(ex_pd, ['N', 'min', 'max', 'mean', 'std', 'cv', 'range', 'gfs'])
#print df_ex_pd

# df_qlmc['Rayon'] = df_qlmc['Rayon'].map(lambda x: x.encode('utf-8'))
# df_qlmc[df_qlmc['Rayon'] == 'Boissons']
# df_qlmc[(df_qlmc['Rayon'] == 'Boissons') & (df_qlmc['P'] == 0)]
# len(df_qlmc[(df_qlmc['Rayon'] == 'Boissons') & (df_qlmc['P'] == 0)]['Produit'].unique())

#df_qlmc['Produit'] = df_qlmc['Produit'].map(lambda x: clean_product(x))
#
## todo: re.sub 'Bocal', 'Pet', 'Bidon' ?
## 'barquettes?' '1 assiette', 'paquet', 'sachet', 'coffret'
## brand u'b\xe9n\xe9dicta' => benedicta, ', 2 briques - 60cl' =>  '2 - 60cl'
## brand u'bl\xe9did\xe9j' => u"bl\xe9di'dej (?) , '2 - 50cl' => '2*50cl'
## todo : harmonize '1.5L' vs '1,5L' (temporary fix... to be improved)
## todo: may want to remove 'Bouteille(s)', 'Pet' and likes before removing ','
## todo... would be better to generally ignore text in the quantity part ! 
#
#ls_ls_boissons = []
#for i in range(3):
#	ls_ls_boissons.append(df_qlmc[(df_qlmc['Rayon'] == 'Boissons') &\
#                           (df_qlmc['P'] == i)]['Produit'].unique())
#
#ls_boissons_0 = [x for x in ls_ls_boissons[0] if x in ls_ls_boissons[1]]
#ls_boissons_1 = [x for x in ls_ls_boissons[1] if x in ls_ls_boissons[2]]
#ls_boissons_2 = [x for x in ls_boissons_0 if x in ls_boissons_1]
#
#ls_ls_sale = []
#for i in range(3):
#	ls_ls_sale.append(\
#    df_qlmc[(df_qlmc['Rayon'] == u'Epicerie sal\xe9e') &\
#            (df_qlmc['P'] == i)]['Produit'].unique())
#
#ls_sale_0 = [x for x in ls_ls_sale[0] if x in ls_ls_sale[1]]
#ls_sale_1 = [x for x in ls_ls_sale[1] if x in ls_ls_sale[2]]
#ls_sale_2 = [x for x in ls_sale_0 if x in ls_sale_1]

### Stores which survive (all stores for now...)
#ls_ls_stores_2 = []
#for i in range(0,3):
#  ls_ls_stores_2.append(df_qlmc[df_qlmc['P'] == i]['Magasin'].unique())
#ls_lasting_stores = [x for x in ls_ls_stores_2[0] if x in ls_ls_stores_2[1]]
#
#ls_prod_0 = df_qlmc['Produit'][(df_qlmc['Magasin'] == ls_lasting_stores[0]) &\
#                               (df_qlmc['P'] == 0)].values
#ls_prod_1 = df_qlmc['Produit'][(df_qlmc['Magasin'] == ls_lasting_stores[0]) &\
#                               (df_qlmc['P'] == 1)].values
#ls_lasting_prods = [x for x in ls_prod_0 if x in ls_prod_1]
#
#df_auchan_arras = df_qlmc[(df_qlmc['Magasin'] == ls_lasting_stores[0])]
#for prod in ls_lasting_prods[0:10]:
#	print df_auchan_arras[['P', 'Produit', 'Prix']]\
#          [df_auchan_arras['Produit'] == prod].to_string(index=False)
