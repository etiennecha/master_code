#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_source = os.path.join(path_data,
                           'data_supermarkets',
                           'data_source',
                           'data_qlmc_2007-12')

path_source_csv = os.path.join(path_source,
                               'data_csv')

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

# #######################
# FIX DF QLMC
# #######################

df_qlmc = pd.read_csv(os.path.join(path_source_csv,
                                   'df_qlmc_raw.csv'),
                      encoding = 'UTF-8')

# MERGE DF QLMC STORES

print u'\nMerge df_qlmc with df_stores (store info)'
df_stores = pd.read_csv(os.path.join(path_source_csv,
                                     'df_stores_w_municipality_and_lsa_id.csv'),
                        dtype = {'id_lsa': str,
                                 'c_insee' : str},
                        encoding = 'UTF-8')

# todo: do before and drop
df_qlmc = pd.merge(df_stores,
                   df_qlmc,
                   on = ['period', 'store'],
                   how = 'right')

# MERGE DF QLMC PRODUCTS

print u'\nMerge df_qlmc with df_product_names (standardizaton)'
df_prod_names = pd.read_csv(os.path.join(path_source_csv,
                                         'df_product_names.csv'),
                          encoding='utf-8')
df_qlmc = pd.merge(df_prod_names,
                   df_qlmc,
                   on = 'product',
                   how = 'right')

# BUILD NORMALIZED PRODUCT INDEX (needed? rather inter periods?)
print u'\nAdd Product_norm: normalized product name'
for field in ['product_brand', 'product_name', 'product_format']:
  df_qlmc[field].fillna(u'', inplace = True)

df_qlmc.loc[df_qlmc['product_brand'] == u'',
            'product_brand'] = 'Sans Marque'

df_qlmc['product_norm'] = df_qlmc['product_brand'] + ' - ' +\
                          df_qlmc['product_name'] + ' - ' +\
                          df_qlmc['product_format']

# FIX STORES WHICH WERE LISTED UNDER TWO DIFFERENT NAMES WITHIN A PERIOD
ls_fix_stores = [[4, u'SUPER U ANGERS BOURG DE PAILLE',
                  u'SUPER U', u'BEAUCOUZE'],
                 [5, u'CHAMPION ST GERMAIN DU PUY',
                  u'CARREFOUR MARKET', u'ST GERMAIN DU PUY'],
                 [9, u'CARREFOUR MARKET CLERMONT CARRE JAUDE',
                  u'CARREFOUR MARKET', u'CLERMONT FERRAND JAUDE']]

for period, old_store, new_store_chain, new_store_municipality in ls_fix_stores:
  df_qlmc.loc[(df_qlmc['period'] == period) &\
              (df_qlmc['store'] == old_store),
              ['store_chain', 'store_municipality', 'store']] =\
                [new_store_chain,
                 new_store_municipality,
                 new_store_chain + ' ' + new_store_municipality]

# To have perfect harmonization
df_qlmc.loc[(df_qlmc['store'] == 'SUPER U BEAUCOUZE'),
            'insee_municipality'] == u'BEAUCOUZE'

# #######################
# DESC STATS (here?)
# #######################

pd.set_option('float_format', '{:4,.2f}'.format)

# PRODUCTS PRESENT IN ALL PERIODS
ls_ls_prod = []
for per in df_qlmc['period'].unique():
  ls_ls_prod.append(list(df_qlmc['product_norm'][df_qlmc['period'] == per].unique()))
set_prod = set(ls_ls_prod[0])
for ls_prod in ls_ls_prod[1:]:
	set_prod.intersection_update(set(ls_prod))
ls_prod_allp = list(set_prod)

# INSPECT/FIX PRICES

df_qlmc.sort('price', ascending = False, inplace = True)
print u'\nInspect 100 most expensive (period) products:'
print df_qlmc[['period', 'product_norm', 'price']][0:100].to_string()

# Prices to be divided by 10 (which periods are concerned?)
# todo: increase robustness?
pr_exception = u'Philips - Cafeti\xe8re filtre Cucina lilas 1000W 1.2L (15 tasses) , X1'
df_qlmc.loc[(df_qlmc['price'] > 35.5) &\
            (df_qlmc['product'] != pr_exception) , 'price'] =\
  df_qlmc.loc[(df_qlmc['price'] > 35.5) &\
              (df_qlmc['product'] != pr_exception), 'price'] / 100.0

# Inspect prices by product (regarless of period)
df_price_su = df_qlmc[['product_norm', 'price']].groupby('product_norm').\
                agg([np.median, np.mean, np.std, min, max])['price']
df_price_su.sort('mean', inplace = True, ascending = False)
print u'\nInspect prices of 20 most expensive products (all periods pooled):'
print df_price_su[0:20].to_string()

# Inspect average product prices by period (regarless of period)
ls_se_avg_prices = []
for i in range(13):
  df_qlmc_per = df_qlmc[df_qlmc['period'] == i]
  se_avg_prices = df_qlmc_per[['product_norm', 'price']]\
                    .groupby('product_norm').agg(np.mean)['price']
  ls_se_avg_prices.append(se_avg_prices)
df_per_prices = pd.DataFrame(ls_se_avg_prices, index = range(13)).T
df_per_prices['spread'] = df_per_prices.max(axis = 1) - df_per_prices.min(axis = 1)
df_per_prices.sort('spread', inplace = True, ascending = False)
df_per_prices.reset_index(inplace = True)
print '\nInspect 100 highest (period) product price spread'
print df_per_prices[0:100].to_string()
# Issues fixed in build_final (periods 6, 8 ,9)

#pr_pbm, period_pbm = u"Gemey Volum'Express mascara noir 10ml", 6
#print df_qlmc[['store', 'price']][(df_qlmc['product_norm'] == pr_pbm) &\
#                                   (df_qlmc['period'] == period_pbm)].to_string()
#
#pr_pbm, period_pbm = u"Viva Lait TGV demi-écrémé vitaminé 6x50cl", 7
#print df_qlmc[['store', 'price']][(df_qlmc['product_norm'] == pr_pbm) &\
#                                   (df_qlmc['period'] == period_pbm)].to_string()

## Period 6, 8, 9: pbm with goods of price above 10?
## Compare mean price with other periods and fix if large diff
## Check if prices are consistent (/10 and rounded?)
#for i in range(13):
#  print '\n', i
#  print df_qlmc[df_qlmc['period'] == i]['Price'].describe()

# Check good average price across periods => see pbms in 6, 8, 9

# Get rid of products with several prices records
#print df_qlmc[['product_norm', 'period', 'price']]\
#        [(df_qlmc['product_norm'] == 'Elle & Vire Beurre doux tendre 250g') &\
#         (df_qlmc['id_lsa'] == '1525')].to_string()

# TODO: examine duplicates (associated with high/low price: way to solve!)
se_dup_bool = df_qlmc.duplicated(subset = ['period', 'store', 'product_norm'])
df_dup = df_qlmc[['period', 'store', 'product_norm', 'price']][se_dup_bool]

df_dup['product_norm'][df_dup['period'] == 0].value_counts()[0:10]

df_check = df_qlmc[['period', 'store', 'product_norm', 'price']]\
             [(df_qlmc['period'] == 0) &\
              (df_qlmc['product_norm'] == u'Blédina Pêche - fraise dès 4 mois - 2 s - 260g')].copy()
df_check.sort('store', inplace = True)

df_check_2 = df_qlmc[['period', 'store', 'product_norm', 'price']]\
               [(df_qlmc['period'] == 0) &\
                (df_qlmc['product_norm'] == u'La-pie-qui-chante - Menthe claire Bonbons 360g')].copy()
df_check_2.sort('store', inplace = True)

print u'\nInspect specific product (duplicate issue):'
print df_qlmc[(df_qlmc['period'] == 0) &\
              (df_qlmc['product_norm'] == u'La-pie-qui-chante - Menthe claire Bonbons 360g') &\
              (df_qlmc['store'] == u'GEANT CARCASSONNE')].T.to_string()

#df_qlmc.drop_duplicates(subset = ['p', 'store', 'product_norm'],
#                        take_last = True,
#                        inplace = True)

# STORE LEVEL (could be suited to examine before after..)

# 14343 (lsa index) closed on 2009-10-31 i.e. between periods 5 and 6
# impact for 1525 (0 to 12) and 1581 (1 and 6... short)

# 10248 closed on 2011-01-01 i.e. beg of period 8 (?)
# impact for 502 (0, 2, 4, 5, 8, 9, 10, 11, 12)

id_lsa = '1525'

# Comparison between two periods for one store
df_temp_1 = df_qlmc[['product_norm', 'price']][(df_qlmc['period'] == 0) &\
                                              (df_qlmc['id_lsa'] == id_lsa)].copy()
df_temp_2 = df_qlmc[['product_norm', 'price']][(df_qlmc['period'] == 9) &\
                                              (df_qlmc['id_lsa'] == id_lsa)].copy()
df_temp_3 = pd.merge(df_temp_1, df_temp_2, on = 'product_norm',
                     how = 'inner', suffixes = ('_1', '_2'))
df_temp_3['d_value'] = df_temp_3['price_2'] - df_temp_3['price_1']
df_temp_3['d_percent'] = df_temp_3['d_value'] / df_temp_3['price_1']

# Comparison between all periods available for one store
ls_store_per_ind = [int(x) for x in df_qlmc['period']\
                     [df_qlmc['id_lsa'] == id_lsa].unique()]
ls_store_per_ind.sort()
df_store = df_qlmc[['product_norm', 'price']][(df_qlmc['period'] == ls_store_per_ind[0]) &\
                                             (df_qlmc['id_lsa'] == id_lsa)].copy()
for per_ind in ls_store_per_ind[1:]:
  df_temp = df_qlmc[['product_norm', 'price']]\
              [(df_qlmc['period'] == per_ind) &\
               (df_qlmc['id_lsa'] == id_lsa)]
  df_store = pd.merge(df_store,
                      df_temp,
                      on = 'product_norm',
                      how = 'outer', suffixes = ('', '_{:02d}'.format(per_ind)))

# Finally harmonize first Price column name
df_store.rename(columns = {'price': 'price_{:02d}'.format(ls_store_per_ind[0])},
                inplace = True)
df_store.columns = [x.replace('price_', 'period') for x in df_store.columns]

# Trivial mistake in price reported: look for problems by product
# might need to add price folder and work on prices

print u'\nComparison across periods for one store:'
print df_store[0:30].to_string()

## ########################
## DATE PARSING
## ########################
#
#df_qlmc['date_2'] = pd.to_datetime(df_qlmc['date'], product_format = '%d/%m/%y')
#for i in range(13):
#  print u'Beg of period {:2d}'.Product_format(i),
#        df_qlmc['date_2'][df_qlmc['period'] == i].min()
#  print u'End of period {:2d}'.Product_format(i),
#        df_qlmc['date_2'][df_qlmc['period'] == i].max()
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
#ls_prod_0 = df_qlmc['Produit'][df_qlmc['Period'] == 0].unique()
#ls_prod_8 = df_qlmc['Produit'][df_qlmc['Period'] == 8].unique()
#ls_prod_08 = [x for x in ls_prod_0 if x in ls_prod_8]
#ls_store_0 = df_qlmc['Store'][df_qlmc['Period'] == 0].unique()
#ls_store_8 = df_qlmc['Store'][df_qlmc['Period'] == 8].unique()
#ls_store_08 = [x for x in ls_store_0 if x in ls_store_8]
#for x in ls_store_08:
#  df_mag_prod = df_qlmc[(df_qlmc['Store'] == x) & (df_qlmc['Produit'] == ls_prod_08[0])]
#  ls_mag_prod_periods = df_mag_prod['Period'].unique()
#  if 0 in ls_mag_prod_periods and 8 in ls_mag_prod_periods:
#    print '\n', x
#    print df_mag_prod[['Period', 'Produit', 'Price']]

## Can check evolution of products of same brand
## Draw evo of prices of different Product_formats of Coca Cola at various stores

# ##################
# PRODUCT DISPERSION
# ##################

## Check product dispersion
#ex_product = u'Nutella - Pâte à tartiner chocolat noisette, 400g'
#ex_se_prices = df_qlmc[u'Price'][(df_qlmc[u'Produit'] == ex_product) &\
#                                   (df_qlmc[u'Period'] == 1)]
#ex_pd = compute_price_dispersion(ex_se_prices)
#df_ex_pd = pd.DataFrame(ex_pd, ['N', 'min', 'max', 'mean', 'std', 'cv', 'range', 'gfs'])
#print df_ex_pd

# df_qlmc['Rayon'] = df_qlmc['Rayon'].map(lambda x: x.encode('utf-8'))
# df_qlmc[df_qlmc['Rayon'] == 'Boissons']
# df_qlmc[(df_qlmc['Rayon'] == 'Boissons') & (df_qlmc['Period'] == 0)]
# len(df_qlmc[(df_qlmc['Rayon'] == 'Boissons') & (df_qlmc['Period'] == 0)]['Produit'].unique())

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
#                           (df_qlmc['Period'] == i)]['Produit'].unique())
#
#ls_boissons_0 = [x for x in ls_ls_boissons[0] if x in ls_ls_boissons[1]]
#ls_boissons_1 = [x for x in ls_ls_boissons[1] if x in ls_ls_boissons[2]]
#ls_boissons_2 = [x for x in ls_boissons_0 if x in ls_boissons_1]
#
#ls_ls_sale = []
#for i in range(3):
#	ls_ls_sale.append(\
#    df_qlmc[(df_qlmc['Rayon'] == u'Epicerie sal\xe9e') &\
#            (df_qlmc['Period'] == i)]['Produit'].unique())
#
#ls_sale_0 = [x for x in ls_ls_sale[0] if x in ls_ls_sale[1]]
#ls_sale_1 = [x for x in ls_ls_sale[1] if x in ls_ls_sale[2]]
#ls_sale_2 = [x for x in ls_sale_0 if x in ls_sale_1]

### Stores which survive (all stores for now...)
#ls_ls_stores_2 = []
#for i in range(0,3):
#  ls_ls_stores_2.append(df_qlmc[df_qlmc['Period'] == i]['Store'].unique())
#ls_lasting_stores = [x for x in ls_ls_stores_2[0] if x in ls_ls_stores_2[1]]
#
#ls_prod_0 = df_qlmc['Produit'][(df_qlmc['Store'] == ls_lasting_stores[0]) &\
#                               (df_qlmc['Period'] == 0)].values
#ls_prod_1 = df_qlmc['Produit'][(df_qlmc['Store'] == ls_lasting_stores[0]) &\
#                               (df_qlmc['Period'] == 1)].values
#ls_lasting_prods = [x for x in ls_prod_0 if x in ls_prod_1]
#
#df_auchan_arras = df_qlmc[(df_qlmc['Store'] == ls_lasting_stores[0])]
#for prod in ls_lasting_prods[0:10]:
#	print df_auchan_arras[['Period', 'Produit', 'Price']]\
#          [df_auchan_arras['Produit'] == prod].to_string(index=False)

## #################
## STORE DISPERSION
## #################
#
#pd.options.display.float_Product_format = '{:,.2f}'.Product_format
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
