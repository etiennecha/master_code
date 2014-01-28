#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import os
import sys
import sqlite3
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:/Bureau/Etienne_work/Data'):
  path_data = r'W:/Bureau/Etienne_work/Data'
else:
  path_data = r'C:/Users/etna/Desktop/Etienne_work/Data'
# structure of the data folder should be the same
folder_built_qlmc_sql = r'/data_qlmc/data_built/data_sql_qlmc'

conn = sqlite3.connect(path_data + folder_built_qlmc_sql + r'/mydatabase.db')
cursor = conn.cursor()

print 'tables in master', cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
print 'columns in table', cursor.execute("PRAGMA table_info(qlmc_global)").fetchall()
print 'nb of records in table', cursor.execute("SELECT COUNT(*) FROM qlmc_global").fetchall()[0][0]

list_produits = cursor.execute("SELECT DISTINCT produit FROM qlmc_global").fetchall()
list_magasins = cursor.execute("SELECT DISTINCT magasin FROM qlmc_global").fetchall()

# #############################################
# PRICE DIPSERSION OF A PRODUCT ACROSS PERIODS
# #############################################

ind_product = 2133
print 'Produit etudie:', list_produits[ind_product][0]
# get a list of prices set at each period for a product
list_lists_prices = []
for i in range(0,7):
  t = (list_produits[ind_product][0], i)
  list_prices = []
  for row in cursor.execute('SELECT prix FROM qlmc_global WHERE produit=? and period=?', t).fetchall():
    list_prices.append(row[0])
  list_lists_prices.append(list_prices)

list_lists_prices = [(period_index, list_prices) for period_index, list_prices in enumerate(list_lists_prices)\
                                       if list_prices]

# compare (dispersion) stats of a product across periods
dico_results = {'list_nb':[],
                'list_mean':[],
                'list_range':[],
                'list_std':[],
                'list_coefvar':[]}
for (period_index, list_prices) in list_lists_prices:
  if list_prices:
    dico_results['list_nb'].append(len(list_prices))
    dico_results['list_mean'].append(np.mean(list_prices))
    dico_results['list_range'].append(np.max(list_prices) - np.min(list_prices))
    dico_results['list_std'].append(np.std(list_prices))
    dico_results['list_coefvar'].append(np.std(list_prices) / np.mean(list_prices))
  else:
    dico_results['list_nb'].append(np.nan)
    dico_results['list_mean'].append(np.nan)
    dico_results['list_range'].append(np.nan)
    dico_results['list_std'].append(np.nan)
    dico_results['list_coefvar'].append(np.nan)
for k,v in dico_results.iteritems():
  print k, np.around(ma.array(np.array(v)), 2)

list_lists_prices_light = [elt[1] for elt in list_lists_prices]
# draw histograms of period prices for a product
lower_bound = np.min([j for i in list_lists_prices_light for j in i])
upper_bound = np.max([j for i in list_lists_prices_light for j in i])
for ind, list_prices in enumerate(list_lists_prices_light):
  ax = plt.subplot(len(list_lists_prices_light), 1, ind)
  n, bins, patches = ax.hist(list_prices, 20, range=[lower_bound, upper_bound], normed=0, facecolor='green', alpha=1)
  ax.set_xlim(lower_bound, upper_bound)
#plt.show()

"""                   
# gives 46 stores * 146 products * 7 periods
# Create table with those and see if interesting... (check product titles...)
cursor.execute("CREATE TABLE qlmc_test AS SELECT * FROM qlmc_global WHERE magasin IN\
                (SELECT magasin FROM qlmc_global GROUP BY magasin HAVING COUNT(DISTINCT period) = 7)\
                AND produit IN\
                (SELECT produit FROM qlmc_global GROUP BY produit HAVING COUNT(DISTINCT period) = 7)")
list_produits = cursor.execute("SELECT DISTINCT produit FROM qlmc_test").fetchall()
list_magasins = cursor.execute("SELECT DISTINCT magasin FROM qlmc_test").fetchall()

# extract price series and get usual stats... Not so interesting.. just 3 brands... not close to each other
"""
# #######################################
# COMPARISON OF PRICES BETWEEN TWO SHOPS
# #######################################

# TODO: Create INDEX(ES)

"""
# Find stores present all the time
# No LECLERC store among them => HYPOTHESIS: Stores which survive are more expensive than average: check that?
list_store_3_periods = cursor.execute("SELECT magasin FROM qlmc_global GROUP BY magasin HAVING COUNT(DISTINCT period) = 3").fetchall()

# Average price per product for a brand in a given period
params = (list_brands[0] + '%', 0)
list_avg_prices_brand = cursor.execute("SELECT produit, AVG(prix), COUNT(prix) FROM qlmc_global\
                                         WHERE magasin LIKE ? AND period = ? GROUP BY produit", params).fetchall()

# Get prices of common products at two stores
params = (list_store_3_periods[0][0], 0, list_store_3_periods[1][0], 0)
list_price_tuples = cursor.execute("SELECT a.produit, a.prix, b.prix FROM \
                                       (SELECT * FROM qlmc_global WHERE magasin = ? AND period = ?) a,\
                                       (SELECT * FROM qlmc_global WHERE magasin = ? AND period = ?) b\
                                       WHERE a.produit = b.produit", params).fetchall()
                                         
# A store prices vs. same brand prices in a given period
params = (list_brands[0] + '%', 0, list_store_3_periods[0][0], 0)
list_shop_vs_brand = cursor.execute("SELECT a.produit, a.prix, b.prix FROM \
                                       (SELECT produit, AVG(prix) AS prix FROM qlmc_global\
                                         WHERE magasin LIKE ? AND period = ? GROUP BY produit) a,\
                                       (SELECT * FROM qlmc_global WHERE magasin = ? AND period = ?) b\
                                       WHERE a.produit = b.produit", params).fetchall()

cum_gap = 0
count_more_expensive = 0
for (product, brand_average_price, shop_price) in list_shop_vs_brand:
  cum_gap += shop_price - brand_average_price
  count_more_expensive += (shop_price > brand_average_price)
print '{0:35s};    cum price minus avg: {1: 3.2f};    % of price > avg: {2: 2.2f};    nb of products: {3: 4d}'\
                    .format(list_store_3_periods[0][0], round(cum_gap,2),\
                    round(count_more_expensive/float(len(list_shop_vs_brand)),2), len(list_shop_vs_brand))

# All surviving stores vs. brand in a given period
period_cond = 2
for (store_3_periods,) in list_store_3_periods:
  for brand in ['AUCHAN', 'CARREFOUR MARKET', 'CENTRE E. LECLERC', 'GEANT CASINO', 'INTERMARCHE SUPER', 'SUPER U']:
  # take sub_list_brands so far (TODO: replace LIKE by REGEX in sql request)
    if brand in store_3_periods:
      params = (brand + '%', period_cond, store_3_periods, period_cond)
      list_shop_vs_brand = cursor.execute("SELECT a.produit, a.prix, b.prix FROM \
                                       (SELECT produit, AVG(prix) AS prix FROM qlmc_global\
                                         WHERE magasin LIKE ? AND period = ? GROUP BY produit) a,\
                                       (SELECT * FROM qlmc_global WHERE magasin = ? AND period = ?) b\
                                       WHERE a.produit = b.produit", params).fetchall()
      cum_gap = 0
      count_more_expensive = 0
      for (product, brand_average_price, shop_price) in list_shop_vs_brand:
        cum_gap += shop_price - brand_average_price
        count_more_expensive += (shop_price > brand_average_price)
      print '{0:35s};    cum price minus avg: {1:> 3.2f};    % of price > avg: {2:> 2.2f};    nb of products: {3:> 4d}'\
                               .format(store_3_periods, round(cum_gap, 2),\
                               round(count_more_expensive / float(len(list_shop_vs_brand)), 2), len(list_shop_vs_brand))
                               
# DO IT AS LECLERC: WOULD THE BRAND BE CHEAPER WITHOUT THEM OR NOT ?
# BY THE WAY: CHECK HOW PRODUCTS PICKED CHANGE OVER TIME (CHEAPEST AT LECLERC MORE LIKELY TO SURVIVE?)
"""

# SQL REMINDER                  
"""
# count distinct values in a column
print cursor.execute("SELECT COUNT(DISTINCT produit) FROM qlmc_global").fetchall()[0][0]
# like query
list_test_like_prix = cursor.execute("SELECT prix FROM qlmc_global WHERE produit LIKE 'Lorenz%'").fetchall()
"""