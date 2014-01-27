#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import os, sys
import json
import pprint
import numpy as np
import re
import itertools
import pandas as pd
# from pyper import *

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def get_split_chain_city(string_to_split, list_split_string):
  result = []
  for split_string in list_split_string:
    split_search = re.search('%s' %split_string, string_to_split)
    if split_search:
      result = [string_to_split[:split_search.end()].strip(),\
                  string_to_split[split_search.end():].strip()]
      break
  if not split_search:
    print 'Could not split on chain:', string_to_split
  return result

def get_split_brand_product(string_to_split, list_brand_patches):
  """
  word_1 = u'Liebig,'
  word_2 = u'Liebig - '
  string_of_interest = u'Liebig, Pursoup velouté légumes, 1L'
  re.sub(ur'^%s\s?,\s?(.*)' %word_1, ur'%s\1' %word_2, string_of_interest)
  """
  split_search = re.search('(\s-)|(-\s)|(-\s-)', string_to_split)
  if split_search:
    result = [string_to_split[:split_search.start()].strip(),\
              string_to_split[split_search.end():].strip()]
  else:
    for brand_patch in list_brand_patches:
      brand_patch_corr = brand_patch + u' - '
      string_to_split = re.sub(ur'^%s\s?,\s?(.*)' %brand_patch,\
                               ur'%s\1' %brand_patch_corr,\
                               string_to_split)
    split_search = re.search('(\s-)|(-\s)|(-\s-)', string_to_split)
    if split_search:
      result = [string_to_split[:split_search.start()].strip(),\
                string_to_split[split_search.end():].strip()]
      # print 'Correction brand:', result
    else:
      result = [u'No brand',\
                string_to_split.strip()]
      # print 'No brand:', result
  return result

def get_dict_indexes(master, index):
  dict_result = {}
  for row_id, row in enumerate(master):
    dict_result.setdefault(row[index], []).append(row_id)
  return dict_result

def get_dict_components(master, category_index, component_index):
  dict_components = {}
  for row in master:
    dict_components.setdefault(row[category_index], set([])).add(row[component_index])
  for category, set_components in dict_components.iteritems():
    dict_components[category] = list(set_components)
  return dict_components

def print_dict_stats(dict_column):
  # add option to sort by length of list_indexes
  for key, list_indexes in dict_column.iteritems():
    print key, len(list_indexes)

def get_product_pd(master, list_indexes):
  list_prices = [master[index][4] for index in list_indexes]
  array_prices = np.array(list_prices)
  mean_price = np.mean(array_prices)
  range = np.max(array_prices) - np.min(array_prices)
  gain_from_search = np.mean(array_prices) - np.min(array_prices)
  std_price = np.std(array_prices)
  coeff_var = np.std(array_prices) / np.mean(array_prices)
  tuple_result = [mean_price, range, gain_from_search, std_price, coeff_var]
  # array_result = np.around(np.array(tuple_result), 2)
  return  tuple_result

def compare_stores(store_a, store_b, df_period, period_ind, category):
  # pandas df for store a
  pd_df_test_a= df_period[['Prix','Produit','Rayon','Famille']]\
                         [(df_period['Magasin'] == store_a) & (df_period['P']==period_ind)]
  pd_df_test_a['Prix_a'] = pd_df_test_a['Prix']
  pd_df_test_a = pd_df_test_a.set_index('Produit')
  pd_df_test_a = pd_df_test_a[['Prix_a', 'Rayon', 'Famille']]
  # pandas df for store b
  pd_df_test_b= df_period[['Prix','Produit','Magasin']]\
                         [(df_period['Magasin'] == store_b) & (df_period['P']==period_ind)]
  pd_df_test_b['Prix_b'] = pd_df_test_b['Prix']
  pd_df_test_b = pd_df_test_b.set_index('Produit')
  pd_df_test_b = pd_df_test_b[['Prix_b']]
  # merge pandas df a and b
  pd_df_merged = pd_df_test_a.join(pd_df_test_b)
  # analysis of price dispersion
  ls_a_cheaper = []
  ls_b_cheaper = []
  ls_a_equal_b = []
  ls_str_categories = []
  for str_category in np.unique(pd_df_merged[category]):
    ls_str_categories.append(str_category)
    ls_a_cheaper.append(np.sum((pd_df_merged['Prix_a'][pd_df_merged[category]== str_category] <\
                                pd_df_merged['Prix_b'][pd_df_merged[category]== str_category])))
    ls_b_cheaper.append(np.sum((pd_df_merged['Prix_a'][pd_df_merged[category]== str_category] >\
                                pd_df_merged['Prix_b'][pd_df_merged[category]== str_category])))
    ls_a_equal_b.append(np.sum((pd_df_merged['Prix_a'][pd_df_merged[category]== str_category] ==\
                                pd_df_merged['Prix_b'][pd_df_merged[category]== str_category])))
  return (ls_str_categories, ls_a_cheaper, ls_b_cheaper, ls_a_equal_b)

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:/Bureau/Etienne_work/Data'):
  path_data = r'W:/Bureau/Etienne_work/Data'
elif os.path.exists(r'C:/Users/etna/Desktop/Etienne_work/Data'):
  path_data = r'C:/Users/etna/Desktop/Etienne_work/Data'
else:
  path_data = r'/mnt/Data'
# structure of the data folder should be the same
folder_source_qlmc_json = '/data_qlmc/data_source/data_json'
folder_built_qlmc_json = '/data_qlmc/data_built/data_json_qlmc'

list_files = [r'/200705_releves_QLMC',
              r'/200708_releves_QLMC',
              r'/200801_releves_QLMC',
              r'/200804_releves_QLMC',
              r'/200903_releves_QLMC',
              r'/200909_releves_QLMC',
              r'/201003_releves_QLMC',
              r'/201010_releves_QLMC', 
              r'/201101_releves_QLMC',
              r'/201104_releves_QLMC',
              r'/201110_releves_QLMC', # "No brand" starts to be massive
              r'/201201_releves_QLMC',
              r'/201206_releves_QLMC']

list_shop_brands = ['HYPER CHAMPION',
                    'CHAMPION',
                    'INTERMARCHE SUPER',
                    'INTERMARCHE',
                    'AUCHAN',
                    'CARREFOUR MARKET',
                    'CARREFOUR',
                    'CORA',
                    'CENTRE E. LECLERC',
                    'CENTRE LECLERC',
                    'E. LECLERC',
                    'LECLERC',
                    'GEANT CASINO',
                    'GEANT DISCOUNT',
                    'GEANT',
                    'CASINO',
                    'HYPER U',
                    'SUPER U',
                    'SYSTEME U',
                    'U EXPRESS',
                    'MARCHE U']

list_brand_patches = [u'Pepito',
                      u'Liebig',
                      u'Babette',
                      u'Grany',
                      u'Père Dodu',
                      u'Lustucru',
                      u'La Baleine',
                      u'Ethiquable', 
                      u'Bn']

# 32bit: can load up to 5 enriched files (8 w/o) 
# 64 bit: all files can be loaded

list_masters = []
list_set_shop = []
list_set_chain = []
list_set_city = []
list_set_brand = []
list_set_product = []

for file in list_files[0:3]:
  print '\n', file
  master = dec_json(path_data + folder_source_qlmc_json + file)
  master = [row + get_split_chain_city(row[3], list_shop_brands) for row in master]
  master =  [row + get_split_brand_product(row[2], list_brand_patches) for row in master]
  list_masters.append(master)
  list_set_shop.append(set([row[3] for row in master]))
  list_set_chain.append(set([row[6] for row in master]))
  list_set_city.append(set([row[7] for row in master]))
  list_set_brand.append(set([row[8] for row in master]))
  list_set_product.append(set([row[9] for row in master]))

# enc_json(list_masters, path_data + folder_built_qlmc_json + r'/master_all_periods')

# ########################
# ALL PERIODS: STATS DES
# ########################

# TODO: write python object stats des generic functions

# (Survival) Products across periods
# TODO: check for minor product name differences? (e.g. within brands...?)
dict_product_periods = {}
for i, list_period in enumerate(list_set_product):
	for product in list_period:
		dict_product_periods.setdefault(product, []).append(i)

dict_product_stats = {key: value for key, value in [i for i in itertools.product(range(15), [0])]}
for shop, list_product_periods in dict_product_periods.iteritems():
  dict_product_stats[len(list_product_periods)] += 1

# (Survival) Stores across periods
dict_shop_periods = {}
for i, list_period in enumerate(list_set_shop):
	for product in list_period:
		dict_shop_periods.setdefault(product, []).append(i)

dict_shop_stats = {key: value for key, value in [i for i in itertools.product(range(15), [0])]}
for shop, list_shop_periods in dict_shop_periods.iteritems():
  dict_shop_stats[len(list_shop_periods)] += 1

# Encode file with store lists for geocoding
ls_ls_stores = [list(set_shop) for set_shop in list_set_shop]
ls_ls_tuple_stores = []
for list_stores in ls_ls_stores:
  ls_ls_tuple_stores.append([get_split_chain_city(store, list_shop_brands) for store in list_stores])
path_ls_ls_tuple_stores = path_data + folder_built_qlmc_json + r'/ls_ls_tuple_stores'
enc_json(ls_ls_tuple_stores, path_ls_ls_tuple_stores)

# # Encode file with product lists for product reconciliation across periods (TAKES TIME)
# ls_ls_products = []
# for master in list_masters:
  # ls_products = []
  # for row in master:
    # if row[0:3] not in ls_products:
      # ls_products.append(row[0:3])
  # ls_ls_products.append(ls_products)
# enc_json(ls_ls_products, path_data + folder_built_qlmc_json + r'/ls_ls_products')

# #######################
# ONE PERIOD: STATS DES
# #######################

# # TODO: see if to be generalized or => pandas ?
# master = list_masters[0]

# # dicts of indexes list
# dict_dpt_ind      = get_dict_indexes(master, 0)
# dict_subdpt_ind   = get_dict_indexes(master, 1)
# dict_products_ind = get_dict_indexes(master, 2)
# dict_magasins_ind = get_dict_indexes(master, 3)

# # products which are available at all stores?
# list_products_full = []
# for product, list_product_ind in dict_products_ind.iteritems():
  # if len(list_product_ind) == len(dict_magasins_ind):
    # list_products_full.append(product)

# # dicts of category components (dict of list of string)
# dict_dpt_subdpts = get_dict_components(master, 0, 1)
# dict_dpt_products = get_dict_components(master, 0, 2)
# dict_subdpt_products = get_dict_components(master, 1, 2)
# dict_chain_stores = get_dict_components(master, 6, 3)

# # get price dispersion of a given subdpt's products
# for subdpt in dict_subdpt_ind.keys()[0:2]:
  # print '\n', subdpt
  # list_products = dict_subdpt_products[subdpt]
  # list_list_product_ind = [dict_products_ind[products] for products in list_products]
  # list_price_dispersion = [[len(list_indexes)] + get_product_pd(master, list_indexes) \
                                              # for list_indexes in list_list_product_ind]
  # # print price dispersion of product list
  # title_pd = ['nb', 'avg', 'rge', 'gfs', 'std', 'cfv']
  # print "{:>5s}\t{:>5s}\t{:>5s}\t{:>5s}\t{:>5s}\t{:>5s}\t".format(*title_pd),\
        # "{:12s}\t".format('Product Name')
  # list_product_pd = [list_pd + [product] for (product, list_pd) in zip(list_products, list_price_dispersion)]
  # list_product_pd_sorted = sorted(list_product_pd, key=lambda row: row[6])
  # for row in list_product_pd_sorted:
    # print u"{:5.0f}\t{:5.2f}\t{:5.2f}\t{:5.2f}\t{:5.2f}\t{:5.2f}\t{:s}".format(*row)

# #######################
# ANALYSIS WITH PANDAS
# #######################

# TODO: load first period(s) data in pandas and do stats descs
# TODO: evaluate differences in product labels across periods
# TODO: explanation of price levels
# TODO: relation between price level and dispersion within store (randomization over margins)
# TODO: store's expensiveness vs. nearby competitors (Pairs over time?)
# TODO: price dispersion within chains
# TODO: price dispersion within dpts/sub-dpts/brands
# TODO: seek normal pricing products vs. others etc. (price distributions)

# do not include "Libelle" and "Date" (5 and 9 before P added)
# title_cols = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin', 'Prix', 'Date', 'Enseigne', 'Ville', 'Marque', 'Libelle']
title_cols = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin', 'Prix', 'Enseigne', 'Ville', 'Marque']
list_masters_per = [[[i] + row[:5] + row[6:9] for row in master_per] for i, master_per in enumerate(list_masters)]
list_master = [a for b in list_masters_per for a in b]
df_period = pd.DataFrame(zip(*list_master), title_cols).T # TODO: must be a more direct way...
df_period['Prix'] = df_period['Prix'].astype(np.float32)

# # df_period['Rayon'] = df_period['Rayon'].map(lambda x: x.encode('utf-8'))
# # df_period[df_period['Rayon'] == 'Boissons']
# # df_period[(df_period['Rayon'] == 'Boissons') & (df_period['P'] == 0)]
# # len(df_period[(df_period['Rayon'] == 'Boissons') & (df_period['P'] == 0)]['Produit'].unique())

# df_period['Produit']=df_period['Produit'].map(lambda x: x.lower().replace(u'.', u',').replace(u' ,', u','))
# df_period['Produit']=df_period['Produit'].map(lambda x: re.sub(u'\xb0', u' degr\xe9s', x))
# df_period['Produit']=df_period['Produit'].map(lambda x: re.sub(u'gazeuze', u'gazeuse', x))
# df_period['Produit']=df_period['Produit'].map(lambda x: re.sub(ur'(pack|,\s+)bo\xeete', ur'\1 ', x))
# df_period['Produit']=df_period['Produit'].map(lambda x: re.sub(ur'(,\s+)bouteilles?', ur'\1 ', x))
# df_period['Produit']=df_period['Produit'].map(lambda x: re.sub(ur'(,\s+)pet', ur'\1 ', x))
# df_period['Produit']=df_period['Produit'].map(lambda x: re.sub(ur'(,\s+)bocal', ur'\1 ', x))
# df_period['Produit']=df_period['Produit'].map(lambda x: re.sub(ur'(,\s+)bidon', ur'\1 ', x))
# df_period['Produit']=df_period['Produit'].map(lambda x: re.sub(ur'(,\s+)brique', ur'\1 ', x))
# df_period['Produit']=df_period['Produit'].map(lambda x: re.sub(ur'(,\s+)plastique', ur'\1 ', x))
# df_period['Produit']=df_period['Produit'].map(lambda x: re.sub(ur'(,\s+)verre', ur'\1 ', x))
# df_period['Produit']=df_period['Produit'].map(lambda x: ' '.join(x.split()))

# # TODO: re.sub 'Bocal', 'Pet', 'Bidon' ?
# # 'barquettes?' '1 assiette', 'paquet', 'sachet', 'coffret'
# # brand u'b\xe9n\xe9dicta' => benedicta, ', 2 briques - 60cl' =>  '2 - 60cl'
# # brand u'bl\xe9did\xe9j' => u"bl\xe9di'dej (?) , '2 - 50cl' => '2*50cl'
# # TODO : harmonize '1.5L' vs '1,5L' (temporary fix... to be improved)
# # TODO: may want to remove 'Bouteille(s)', 'Pet' and likes before removing ','
# # TODO... would be better to generally ignore text in the quantity part ! 

list_list_boissons = []
for i in range(0,3):
	list_list_boissons.append(df_period[(df_period['Rayon'] == 'Boissons') & (df_period['P'] == i)]['Produit'].unique())

boissons_0 = [elt for elt in list_list_boissons[0] if elt in list_list_boissons[1]]
boissons_1 = [elt for elt in list_list_boissons[1] if elt in list_list_boissons[2]]
boissons_2 = [elt for elt in boissons_0 if elt in boissons_1]

list_list_sale = []
for i in range(0,3):
	list_list_sale.append(\
    df_period[(df_period['Rayon'] == u'Epicerie sal\xe9e') & (df_period['P'] == i)]['Produit'].unique())

sale_0 = [elt for elt in list_list_sale[0] if elt in list_list_sale[1]]
sale_1 = [elt for elt in list_list_sale[1] if elt in list_list_sale[2]]
sale_2 = [elt for elt in sale_0 if elt in sale_1]

# Stores which survive
ls_ls_lasting_stores = []
for i in range(0,3):
  ls_ls_lasting_stores.append(df_period[df_period['P'] == i]['Magasin'].unique())

# Find stores in same location
ls_ls_store_insee = dec_json(path_data + folder_built_qlmc_json + r'/ls_ls_store_insee')
ls_ls_pairs = []
for ls_store_insee in ls_ls_store_insee:
  ls_pairs = []
  for j, store in enumerate(ls_store_insee):
    for k, store_2 in enumerate(ls_store_insee[j+1:], start = j+1):
      if store and store_2 and store[0] == store_2[0]:
        ls_pairs.append((j,k))
  ls_ls_pairs.append(ls_pairs)

for i, ls_pairs in enumerate(ls_ls_pairs):
  for (j,k) in ls_pairs:
    print ls_ls_stores[i][j], ls_ls_stores[i][k]

# TODO: see if product prices are available at these stores across all periods (or 2 at least..)

store_a = 'GEANT BEZIERS'
store_b = 'AUCHAN MONTAUBAN'
test = compare_stores(store_a, store_b, df_period, 0, 'Rayon')

ls_ls_comparisons = []
for per_ind, ls_pairs in enumerate(ls_ls_pairs):
  ls_comparisons = []
  for (i,j) in ls_pairs:
    store_a, store_b = ls_ls_stores[per_ind][i], ls_ls_stores[per_ind][j]
    comparison_result = compare_stores(store_a, store_b, df_period, per_ind, 'Rayon')
    ls_comparisons.append(zip(*comparison_result))
    print '\n', store_a, store_b
    pprint.pprint(zip(*comparison_result))
    for rayon in zip(*comparison_result):
      print u'{0:20s} Nb products: {1:>3.0f}   A cheaper: {2:>3.0f}%   B cheaper: {3: 3.0f}%   A equal B {4: 3.0f}%'.\
                format(rayon[0],\
                sum(rayon[1:]),float(rayon[1])/sum(rayon[1:])*100,\
                float(rayon[2])/sum(rayon[1:])*100,\
                float(rayon[3])/sum(rayon[1:])*100)
  ls_ls_comparisons.append(ls_comparisons)

# TODO: take amount into account (enrich function...)
# TODO: see if all categories equally concerned (average...)
# TODO: see if specific products concerned ? (for which stores...?)

# #####################
# Some reminder (temp)
# #####################

# reminder on intersection of two lists: set(list_1).intersection(list_2)
# test = get_product_pd(master, dict_products_ind[u'Bridelice - Cr\xe8me anglaise UHT , Brique 50cl'])  

# ###########
# Pyper
# ###########

# # Load data in R using pyper
# # Does not work at CREST: too slow...
# # may consider just printing to text file and working on R (for this dataset)
# # The need to think of automated price disperspion analysis remains
# r = R()
# r.database = np.array(master_final[0:100000],\
          				 # dtype=[('rayon', '<s4'), ('famille', '<s4'), ('produit', '|s4'),\
                          # ('magasin', '|s4'), ('prix', '<f4'), ('date', '|s4')])