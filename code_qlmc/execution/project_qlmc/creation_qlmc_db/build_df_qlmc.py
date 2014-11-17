﻿#!/usr/bin/env python
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

# #######################
# DESC STATS (here?)
# #######################

# PRODUCTS IN ALL PERIODS

# improve following... need empty for concat as it is
for field in ['marque', 'nom', 'format']:
  df_qlmc[field].fillna(u'', inplace = True)
df_qlmc['Produit_norm'] = df_qlmc['marque'] + ' ' + df_qlmc['nom']+ ' ' + df_qlmc['format']

ls_ls_prod = []
for per in df_qlmc['P'].unique():
  ls_ls_prod.append(list(df_qlmc['Produit_norm'][df_qlmc['P'] == per].unique()))
set_prod = set(ls_ls_prod[0])
for ls_prod in ls_ls_prod[1:]:
	set_prod.intersection_update(set(ls_prod))
ls_prod_allp = list(set_prod)

# TEST BEFORE/AFTER: IMPACT OF STORE CLOSED

# 14343 (lsa index) closed on 2009-10-31 i.e. between periods 5 and 6
# impact for 1525 (0 to 12) and 1581 (1 and 6... short)

# 10248 closed on 2011-01-01 i.e. beg of period 8 (?)
# impact for 502 (0, 2, 4, 5, 8, 9, 10, 11, 12)

id_lsa = '1525'

# Comparison between two periods for one store
df_temp_1 = df_qlmc[['Produit_norm', 'Prix']][(df_qlmc['P'] == 0) &\
                                              (df_qlmc['id_lsa'] == id_lsa)].copy()
df_temp_2 = df_qlmc[['Produit_norm', 'Prix']][(df_qlmc['P'] == 9) &\
                                              (df_qlmc['id_lsa'] == id_lsa)].copy()
df_temp_3 = pd.merge(df_temp_1, df_temp_2, on = 'Produit_norm',
                     how = 'inner', suffixes = ('_1', '_2'))
df_temp_3['D_value'] = df_temp_3['Prix_2'] - df_temp_3['Prix_1']
df_temp_3['D_percent'] = df_temp_3['D_value'] / df_temp_3['Prix_1']

# Comparison between all periods available for one store
ls_store_per_ind = [int(x) for x in df_qlmc['P']\
                     [df_qlmc['id_lsa'] == id_lsa].unique()]
df_store = df_qlmc[['Produit_norm', 'Prix']][(df_qlmc['P'] == ls_store_per_ind[0]) &\
                                             (df_qlmc['id_lsa'] == id_lsa)].copy()
for per_ind in ls_store_per_ind[1:]:
  df_temp = df_qlmc[['Produit_norm', 'Prix']]\
              [(df_qlmc['P'] == per_ind) &\
               (df_qlmc['id_lsa'] == id_lsa)]
  df_store = pd.merge(df_store,
                      df_temp,
                      on = 'Produit_norm',
                      how = 'outer', suffixes = ('', '_{:02d}'.format(per_ind)))

# Finally harmonize first Prix column name
df_store.rename(columns = {'Prix': 'Prix_00'}, inplace = True)
df_store.columns = [x.replace('Prix_', 'P') for x in df_store.columns]

# Trivial mistake in price reported: look for problems by product
# might need to add price folder and work on prices

pd.set_option('float_format', '{:4,.2f}'.format)
print df_store[0:10].to_string()

# Pbms with text: TODO: clean before extraction?
# Bonduelle - Maà¯s doux en grain, 400g
# Taillefine - Eau plate arà´me pêche, 1.5L
# df_qlmc[df_qlmc['Produit'] == u'Bonduelle - Maà¯s doux en grain, 400g'].iloc[0]

df_price_su = df_qlmc[['Produit_norm', 'Prix']].groupby('Produit_norm').\
                agg([np.median, np.mean, np.std, min, max])['Prix']
df_price_su.sort('mean', inplace = True, ascending = False)
print df_price_su[0:1000].to_string()

# Test: no good seems to have an average price above 50e... so easy general fix?
df_qlmc.loc[df_qlmc['Prix'] > 50, 'Prix'] =\
  df_qlmc.loc[df_qlmc['Prix'] > 50, 'Prix'] / 100.0

# Check Philips Cafetière filtre Cucina lilas 1000W
# Period 6, 8, 9: no good for inter period comparison if price above 10?
# Compare mean price with other periods and see if large difference...
# Check if prices are consistent (/10 and rounded?)
for i in range(13):
	print '\n', i
	df_qlmc[df_qlmc['P'] == i]['Prix'].describe()

## TODO: get rid of products with several price records (either their mistake or my prod harmo)
#print df_qlmc[['Produit_norm', 'P', 'Prix']]\
#        [(df_qlmc['Produit_norm'] == 'Elle & Vire Beurre doux tendre 250g') &\
#         (df_qlmc['ind_lsa_stores'] == 1525)].to_string()

#for prod_norm in se_vc_pn[se_vc_pn > 1].index:
#  df_store = df_store[df_store['Produit_norm'] != prod_norm]

# Check high prices and divide by 100 (e.g. period 7)
# Check with other Cora stores: same pool of products

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

# ##############
# STORE DF QLMC
# ##############

# CSV

## All
#ls_qlmc_all = ['P', 'Rayon', 'Famille', 'Produit',
#               'Enseigne', 'Commune', 'Prix', 'Date',
#               'marque', 'nom', 'format']
#df_qlmc[ls_qlmc_all].to_csv(os.path.join(path_dir_built_csv, 'df_qlmc_all_latin-1.csv'),
#                            float_format='%.3f',
#                            encoding='latin-1', # 'latin-1' for stata
#                            index=False)

## Light
#ls_qlmc_light = ['P', 'Rayon', 'Famille', 'Produit',
#                 'Enseigne', 'Commune', 'Prix', 'Date']
#df_qlmc[ls_qlmc_light].to_csv(os.path.join(path_dir_built_csv, 'df_qlmc_all_light.csv'),
#                              float_format='%.3f',
#                              encoding='utf-8',
#                              index=False)

## Each period (e.g. if want to read only 3 periods bc 32 bit op. sys)
#for i in range(9):
#  df_qlmc[df_qlmc['P'] == i].to_csv(os.path.join(path_dir_built_csv,
#                                                 'df_qlmc_per_%s.csv' %i),
#                                    float_format='%.3f', encoding='utf-8', index=False)

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

## #################
## STORE DISPERSION
## #################
#
#pd.options.display.float_format = '{:,.2f}'.format
#
#store_a = 'GEANT BEZIERS'
#store_b = 'AUCHAN MONTAUBAN'
#test = compare_stores(store_a, store_b, df_qlmc, 0, 'Rayon')
#
## pbm: assumes ls_ls_store_insee has same order as ls_ls_tuple_stores
## but probably not the case any more... do agasin
#
#ls_ls_store_insee = dec_json(os.path.join(path_dir_built_json, 'ls_ls_store_insee'))
#ls_ls_pairs = []
#for ls_store_insee in ls_ls_store_insee:
#  ls_pairs = []
#  for j, store in enumerate(ls_store_insee):
#    for k, store_2 in enumerate(ls_store_insee[j+1:], start = j+1):
#      if store and store_2 and store[0] == store_2[0]:
#        ls_pairs.append((j,k))
#  ls_ls_pairs.append(ls_pairs)
#
#for i, ls_pairs in enumerate(ls_ls_pairs):
#  for (j,k) in ls_pairs:
#    print ls_ls_stores[i][j], ls_ls_stores[i][k]
#
## todo: see if product prices are available at these stores across all periods (or 2 at least..)
#
#ls_ls_comparisons = []
#for per_ind, ls_pairs in enumerate(ls_ls_pairs):
#  ls_comparisons = []
#  for (i,j) in ls_pairs:
#    store_a, store_b = ls_ls_stores[per_ind][i], ls_ls_stores[per_ind][j]
#    comparison_result = compare_stores(store_a, store_b, df_qlmc, per_ind, 'Rayon')
#    ls_comparisons.append(zip(*comparison_result))
#    print '\n', store_a, store_b
#    ls_columns = ['Category', '#PA<PB', '#PA>PB', '#PA=PB']
#    df_comparison = pd.DataFrame(zip(*comparison_result), columns = ls_columns)
#    df_comparison['%PA<PB'] = df_comparison['#PA<PB'] /\
#                                df_comparison[['#PA<PB', '#PA>PB', '#PA=PB']].sum(1)
#    df_comparison['%PA>PB'] = df_comparison['#PA>PB'] /\
#                                df_comparison[['#PA<PB', '#PA>PB', '#PA=PB']].sum(1)
#    df_comparison['%PA=PB'] = df_comparison['#PA=PB'] /\
#                                df_comparison[['#PA<PB', '#PA>PB', '#PA=PB']].sum(1)
#    print df_comparison.to_string(index=False)
#  ls_ls_comparisons.append(ls_comparisons)
#
## todo: take amount into account (enrich function...)
## todo: see if all categories equally concerned (average...)
## todo: see if specific products concerned ? (for which stores...?)
