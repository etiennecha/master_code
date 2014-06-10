#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
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

def get_split_chain_city(string_to_split, ls_split_string):
  result = []
  for split_string in ls_split_string:
    split_search = re.search('%s' %split_string, string_to_split)
    if split_search:
      result = [string_to_split[:split_search.end()].strip(),\
                  string_to_split[split_search.end():].strip()]
      break
  if not split_search:
    print 'Could not split on chain:', string_to_split
  return result

def get_split_brand_product(string_to_split, ls_brand_patches):
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
    for brand_patch in ls_brand_patches:
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

def compute_price_dispersion(se_prices):
  price_mean = se_prices.mean()
  price_std = se_prices.std()
  coeff_var = se_prices.std() / se_prices.mean()
  price_range = se_prices.max() - se_prices.min()
  gain_from_search = se_prices.mean() - se_prices.min()
  return [len(se_prices), se_prices.min(), se_prices.max(), price_mean, 
          price_std, coeff_var, price_range, gain_from_search]

def compare_stores(store_a, store_b, df_period, period_ind, category):
  # pandas df for store a
  df_store_a= df_period[['Prix','Produit','Rayon','Famille']]\
                    [(df_period['Magasin'] == store_a) & (df_period['P']==period_ind)]
  df_store_a['Prix_a'] = df_store_a['Prix']
  df_store_a = df_store_a.set_index('Produit')
  df_store_a = df_store_a[['Prix_a', 'Rayon', 'Famille']]
  # pandas df for store b
  df_store_b = df_period[['Prix','Produit','Magasin']]\
                         [(df_period['Magasin'] == store_b) & (df_period['P']==period_ind)]
  df_store_b['Prix_b'] = df_store_b['Prix']
  df_store_b = df_store_b.set_index('Produit')
  df_store_b= df_store_b[['Prix_b']]
  # merge pandas df a and b
  df_both = df_store_a.join(df_store_b)
  # analysis of price dispersion
  ls_str_categories = []
  ls_a_cheaper, ls_b_cheaper, ls_a_equal_b = [], [], []
  for str_category in df_both[category].unique():
    df_cat = df_both[df_both[category] == str_category]
    ls_str_categories.append(str_category)
    ls_a_cheaper.append(len(df_cat[df_cat['Prix_a'] < df_cat['Prix_b']]))
    ls_b_cheaper.append(len(df_cat[df_cat['Prix_a'] > df_cat['Prix_b']]))
    ls_a_equal_b.append(len(df_cat[df_cat['Prix_a'] == df_cat['Prix_b']]))
  return (ls_str_categories, ls_a_cheaper, ls_b_cheaper, ls_a_equal_b)

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')

path_dir_source_json = os.path.join(path_dir_qlmc, 'data_source', 'data_json_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

list_files = [r'200705_releves_QLMC',
              r'200708_releves_QLMC',
              r'200801_releves_QLMC',
              r'200804_releves_QLMC',
              r'200903_releves_QLMC',
              r'200909_releves_QLMC',
              r'201003_releves_QLMC',
              r'201010_releves_QLMC', 
              r'201101_releves_QLMC',
              r'201104_releves_QLMC',
              r'201110_releves_QLMC', # "No brand" starts to be massive
              r'201201_releves_QLMC',
              r'201206_releves_QLMC']

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

# 32bit: can load only up to 5 enriched files (8 w/o) 

list_masters = []
list_set_shop = []
list_set_chain = []
list_set_city = []
list_set_brand = []
list_set_product = []

for file_name in list_files[0:5]:
  print '\n', file_name
  master = dec_json(os.path.join(path_dir_source_json, file_name))
  master = [row + get_split_chain_city(row[3], list_shop_brands) for row in master]
  master =  [row + get_split_brand_product(row[2], list_brand_patches) for row in master]
  list_masters.append(master)
  list_set_shop.append(set([row[3] for row in master]))
  list_set_chain.append(set([row[6] for row in master]))
  list_set_city.append(set([row[7] for row in master]))
  list_set_brand.append(set([row[8] for row in master]))
  list_set_product.append(set([row[9] for row in master]))

# enc_json(list_masters, os.path.join(path_dir_built_json, 'master_all_periods'))

# ########################
# ALL PERIODS: STATS DES
# ########################

# todo: write python object stats des generic functions

# (Survival) Products across periods
# todo: check for minor product name differences? (e.g. within brands...?)
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
# enc_json(ls_ls_tuple_stores, os.path.join(path_dir_built_json, 'ls_ls_tuple_stores'))

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

# todo: see if to be generalized or => pandas ?
master = list_masters[0]

# dicts of indexes list
dict_dpt_ind      = get_dict_indexes(master, 0)
dict_subdpt_ind   = get_dict_indexes(master, 1)
dict_products_ind = get_dict_indexes(master, 2)
dict_magasins_ind = get_dict_indexes(master, 3)

# products which are available at all stores?
list_products_full = []
for product, list_product_ind in dict_products_ind.iteritems():
  if len(list_product_ind) == len(dict_magasins_ind):
    list_products_full.append(product)

# dicts of category components (dict of list of string)
dict_dpt_subdpts = get_dict_components(master, 0, 1)
dict_dpt_products = get_dict_components(master, 0, 2)
dict_subdpt_products = get_dict_components(master, 1, 2)
dict_chain_stores = get_dict_components(master, 6, 3)

# get price dispersion of a given subdpt's products
for subdpt in dict_subdpt_ind.keys()[0:2]:
  print '\n', subdpt
  ls_products = dict_subdpt_products[subdpt]
  ls_ls_product_ind = [dict_products_ind[products] for products in ls_products]
  ls_price_dispersion = [[len(ls_indexes)] + get_product_pd(master, ls_indexes) \
                              for ls_indexes in ls_ls_product_ind]
  title_pd = ['nb', 'avg', 'rge', 'gfs', 'std', 'cfv']
  print "{:>5s}\t{:>5s}\t{:>5s}\t{:>5s}\t{:>5s}\t{:>5s}\t".\
           format(*title_pd), "{:12s}\t".format('Product Name')
  ls_product_pd = [ls_pd + [product] for (product, ls_pd) in zip(ls_products, ls_price_dispersion)]
  ls_product_pd_sorted = sorted(ls_product_pd, key=lambda row: row[6])
  for row in ls_product_pd_sorted:
    print u"{:5.0f}\t{:5.2f}\t{:5.2f}\t{:5.2f}\t{:5.2f}\t{:5.2f}\t{:s}".format(*row)

# #######################
# ANALYSIS WITH PANDAS
# #######################

# load first period(s) data in pandas and do stats descs
# evaluate differences in product labels across periods
# explanation of price levels (nb of prods recorded as a proxy for store size???)
# relation between price level and dispersion within store (randomization over margins)
# store's expensiveness vs. nearby competitors (Pairs over time?)
# price dispersion within chains
# price dispersion within dpts/sub-dpts/brands
# seek normal pricing products vs. others etc. (price distributions)

# do not include "Libelle" and "Date" (5 and 9 before P added)
#ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin',
#              'Prix', 'Date', 'Enseigne', 'Ville', 'Marque', 'Libelle']
ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin',
              'Prix', 'Enseigne', 'Ville', 'Marque']
ls_master_periods = [[[i] + row[:5] + row[6:9] for row in master_per]\
                       for i, master_per in enumerate(list_masters)]
ls_master = [a for b in ls_master_periods for a in b]
df_period = pd.DataFrame(ls_master, columns = ls_columns)
df_period['Prix'] = df_period['Prix'].astype(np.float32)

# Check product dispersion
ex_product = u'Nutella - Pâte à tartiner chocolat noisette, 400g'
ex_se_prices = df_period[u'Prix'][(df_period[u'Produit'] == ex_product) &\
                                   (df_period[u'P'] == 1)]
ex_pd = compute_price_dispersion(ex_se_prices)
df_ex_pd = pd.DataFrame(ex_pd, ['N', 'min', 'max', 'mean', 'std', 'cv', 'range', 'gfs'])
print df_ex_pd

# df_period['Rayon'] = df_period['Rayon'].map(lambda x: x.encode('utf-8'))
# df_period[df_period['Rayon'] == 'Boissons']
# df_period[(df_period['Rayon'] == 'Boissons') & (df_period['P'] == 0)]
# len(df_period[(df_period['Rayon'] == 'Boissons') & (df_period['P'] == 0)]['Produit'].unique())

def clean_product(product):
  ls_replace = [(u'.', u','),
                (u' ,', u','),
                (u'\xb0', u' degr\xe9s'),
                (u'gazeuze', u'gazeuse')]
  ls_sub = [ur'(pack|,\s+)bo\xeete',
            ur'(,\s+)bouteilles?',
            ur'(,\s+)pet',
            ur'(,\s+)bocal',
            ur'(,\s+)bidon',
            ur'(,\s+)brique',
            ur'(,\s+)plastique',
            ur'(,\s+)verre']
  product = product.lower()
  for tup_repl in ls_replace:
    product = product.replace(tup_repl[0], tup_repl[1])
  for str_sub in ls_sub:
    product = re.sub(str_sub, ur'\1 ', product)
  return ' '.join(product.split())

df_period['Produit']=df_period['Produit'].map(lambda x: clean_product(x))

# todo: re.sub 'Bocal', 'Pet', 'Bidon' ?
# 'barquettes?' '1 assiette', 'paquet', 'sachet', 'coffret'
# brand u'b\xe9n\xe9dicta' => benedicta, ', 2 briques - 60cl' =>  '2 - 60cl'
# brand u'bl\xe9did\xe9j' => u"bl\xe9di'dej (?) , '2 - 50cl' => '2*50cl'
# todo : harmonize '1.5L' vs '1,5L' (temporary fix... to be improved)
# todo: may want to remove 'Bouteille(s)', 'Pet' and likes before removing ','
# todo... would be better to generally ignore text in the quantity part ! 

ls_ls_boissons = []
for i in range(3):
	ls_ls_boissons.append(df_period[(df_period['Rayon'] == 'Boissons') &\
                           (df_period['P'] == i)]['Produit'].unique())

ls_boissons_0 = [x for x in ls_ls_boissons[0] if x in ls_ls_boissons[1]]
ls_boissons_1 = [x for x in ls_ls_boissons[1] if x in ls_ls_boissons[2]]
ls_boissons_2 = [x for x in ls_boissons_0 if x in ls_boissons_1]

ls_ls_sale = []
for i in range(3):
	ls_ls_sale.append(\
    df_period[(df_period['Rayon'] == u'Epicerie sal\xe9e') &\
              (df_period['P'] == i)]['Produit'].unique())

ls_sale_0 = [x for x in ls_ls_sale[0] if x in ls_ls_sale[1]]
ls_sale_1 = [x for x in ls_ls_sale[1] if x in ls_ls_sale[2]]
ls_sale_2 = [x for x in ls_sale_0 if x in ls_sale_1]

# Stores which survive (all stores for now...)
ls_ls_stores_2 = []
for i in range(0,3):
  ls_ls_stores_2.append(df_period[df_period['P'] == i]['Magasin'].unique())
ls_lasting_stores = [x for x in ls_ls_stores_2[0] if x in ls_ls_stores_2[1]]

ls_prod_0 = df_period['Produit'][(df_period['Magasin'] == ls_lasting_stores[0]) &\
                                 (df_period['P'] == 0)].values
ls_prod_1 = df_period['Produit'][(df_period['Magasin'] == ls_lasting_stores[0]) &\
                                 (df_period['P'] == 1)].values
ls_lasting_prods = [x for x in ls_prod_0 if x in ls_prod_1]

df_auchan_arras = df_period[(df_period['Magasin'] == ls_lasting_stores[0])]
for prod in ls_lasting_prods[0:10]:
	print df_auchan_arras[['Produit', 'Prix']]\
          [df_auchan_arras['Produit'] == prod].to_string(index=False)

# Find stores in same location
ls_ls_store_insee = dec_json(os.path.join(path_dir_built_json, 'ls_ls_store_insee'))
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

# todo: see if product prices are available at these stores across all periods (or 2 at least..)

store_a = 'GEANT BEZIERS'
store_b = 'AUCHAN MONTAUBAN'
test = compare_stores(store_a, store_b, df_period, 0, 'Rayon')

pd.options.display.float_format = '{:,.2f}'.format
ls_ls_comparisons = []
for per_ind, ls_pairs in enumerate(ls_ls_pairs):
  ls_comparisons = []
  for (i,j) in ls_pairs:
    store_a, store_b = ls_ls_stores[per_ind][i], ls_ls_stores[per_ind][j]
    comparison_result = compare_stores(store_a, store_b, df_period, per_ind, 'Rayon')
    ls_comparisons.append(zip(*comparison_result))
    print '\n', store_a, store_b
    ls_columns = ['Category', '#PA<PB', '#PA>PB', '#PA=PB']
    df_comparison = pd.DataFrame(zip(*comparison_result), columns = ls_columns)
    df_comparison['%PA<PB'] = df_comparison['#PA<PB'] /\
                                df_comparison[['#PA<PB', '#PA>PB', '#PA=PB']].sum(1)
    df_comparison['%PA>PB'] = df_comparison['#PA>PB'] /\
                                df_comparison[['#PA<PB', '#PA>PB', '#PA=PB']].sum(1)
    df_comparison['%PA=PB'] = df_comparison['#PA=PB'] /\
                                df_comparison[['#PA<PB', '#PA>PB', '#PA=PB']].sum(1)
    print df_comparison.to_string(index=False)
  ls_ls_comparisons.append(ls_comparisons)

# todo: take amount into account (enrich function...)
# todo: see if all categories equally concerned (average...)
# todo: see if specific products concerned ? (for which stores...?)

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
