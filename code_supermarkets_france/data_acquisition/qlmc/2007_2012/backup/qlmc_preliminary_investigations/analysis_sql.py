#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import os
import sys
import sqlite3
import numpy as np
import scipy
import matplotlib.pyplot as plt

def get_product_price_dispersion(product_title, graph = None):
  print 'Produit etudie:', product_title
  # get a list product prices set by stores at each period
  list_lists_prices = []
  for i in range(0,3):
    t = (product_title, i)
    list_prices = []
    for row in cursor.execute('SELECT prix FROM qlmc WHERE produit=? and period=?', t):
     list_prices.append(row[0])
    list_lists_prices.append(list_prices)
  # compare (dispersion) stats of a product across periods
  dico_results = {'list_nb':[],
                  'list_mean':[],
                  'list_range':[],
                  'list_std':[],
                  'list_coefvar':[]}
  for list_prices in list_lists_prices:
    dico_results['list_nb'].append(len(list_prices))
    dico_results['list_mean'].append(np.mean(list_prices))
    dico_results['list_range'].append(np.max(list_prices) - np.min(list_prices))
    dico_results['list_std'].append(np.std(list_prices))
    dico_results['list_coefvar'].append(np.std(list_prices) / np.mean(list_prices))
  for k,v in dico_results.iteritems():
    print k, np.around(v, decimals = 3)
  if graph:
    # draw histograms of period prices for a product
    lower_bound = np.min([j for i in list_lists_prices for j in i])
    upper_bound = np.max([j for i in list_lists_prices for j in i])
    for i in range(len(list_lists_prices)):
      ax = plt.subplot(3,1,i)
      n, bins, patches = ax.hist(list_lists_prices[i], 20,\
                                     range=[lower_bound, upper_bound], normed=0, facecolor='green', alpha=1)
      ax.set_xlim(lower_bound, upper_bound)
    plt.show()
  return dico_results

def get_two_shop_prices(shop_1_cond, shop_2_cond, period_cond):
  print '\nComparaison des magasins', shop_1_cond, 'et', shop_2_cond, '( periode', period_cond, ')\n'
  params = (shop_1_cond, period_cond, shop_2_cond, period_cond)
  list_product_prices = cursor.execute("SELECT a.produit, a.rayon, a.famille, a.prix, b.prix FROM \
                                         (SELECT * FROM qlmc WHERE magasin = ? AND period = ?) a,\
                                         (SELECT * FROM qlmc WHERE magasin = ? AND period = ?) b\
                                         WHERE a.produit = b.produit", params).fetchall()
  dict_rayons = {}
  for (produit, rayon, famille, prix_a, prix_b) in list_product_prices:
    dict_rayons.setdefault(rayon, []).append((produit, prix_a, prix_b))
  for rayon, list_produits in dict_rayons.iteritems():
    list_prix_a = []
    list_prix_b = []
    for produit in list_produits:
      list_prix_a.append(produit[1])
      list_prix_b.append(produit[2])
    array_a = np.array(list_prix_a, dtype = np.float32)
    array_b = np.array(list_prix_b, dtype = np.float32)
    spread = array_a - array_b
    nb_produits = len(list_prix_a)
    a_plus_cher = ((spread > np.float32(0))).sum()
    b_plus_cher = ((spread < np.float32(0))).sum()
    a_plus_cher_avg_spread = 0
    if a_plus_cher > 0:
      a_plus_cher_avg_spread = sum(spread[spread > np.float32(0)]) / float(a_plus_cher)
    b_plus_cher_avg_spread = 0
    if b_plus_cher > 0:
      b_plus_cher_avg_spread = sum(spread[spread < np.float32(0)]) / float(b_plus_cher)
    max_price = np.max([array_a, array_b], axis = 0)
    cum_price = np.sum(max_price)
    cum_spread = np.sum(abs(spread))
    cum_rel_spread = cum_spread / cum_price
    rel_spread = spread / max_price
    avg_rel_spread = np.mean(abs(rel_spread))
    # print nb_produits, a_plus_cher, b_plus_cher, cum_price, cum_spread
    print rayon, '; nb produits:', nb_produits
    print 'a plus cher:', a_plus_cher, np.round(a_plus_cher_avg_spread, 2)
    print 'b plus cher:', b_plus_cher, np.round(b_plus_cher_avg_spread, 2)
    print 'cum price of products, cum spread:', cum_price, cum_spread
    print 'rel spread, avg relative spread:', \
                  np.around(np.array([cum_rel_spread, avg_rel_spread], dtype = np.float32), decimals = 2), '\n'
  return list_product_prices

def get_two_shop_prices_two_periods(shop_1_cond, shop_2_cond, per_1_cond, per_2_cond):
  print '\nComparaison des magasins', shop_1_cond, 'et', shop_2_cond, '( periodes',per_1_cond, per_2_cond, ')\n'
  params = (shop_1_cond, per_1_cond, per_2_cond, shop_2_cond, per_1_cond, per_2_cond)
  list_product_prices = cursor.execute("SELECT a.period, a.produit, a.rayon, a.famille, a.prix, b.prix FROM \
                                         (SELECT * FROM qlmc WHERE magasin = ? AND period in (?,?)) a,\
                                         (SELECT * FROM qlmc WHERE magasin = ? AND period in (?,?)) b\
                                         WHERE a.produit = b.produit AND a.period = b.period", params).fetchall()
  dict_rayons = {}
  for (period, produit, rayon, famille, prix_a, prix_b) in list_product_prices:
    if period == per_1_cond:
      dict_rayons.setdefault(rayon, [[],[]])[0].append((produit, prix_a, prix_b))
    else:
      dict_rayons.setdefault(rayon, [[],[]])[1].append((produit, prix_a, prix_b))
  for rayon, list_period_produits in dict_rayons.iteritems():
    for period_index, list_produits in enumerate(list_period_produits):
      if list_produits:
        list_prix_a = []
        list_prix_b = []
        for produit in list_produits:
          list_prix_a.append(produit[1])
          list_prix_b.append(produit[2])
        array_a = np.array(list_prix_a, dtype = np.float32)
        array_b = np.array(list_prix_b, dtype = np.float32)
        spread = array_a - array_b
        nb_produits = len(list_prix_a)
        a_plus_cher = ((spread > np.float32(0))).sum()
        b_plus_cher = ((spread < np.float32(0))).sum()
        a_plus_cher_avg_spread = 0
        if a_plus_cher > 0:
          a_plus_cher_avg_spread = sum(spread[spread > np.float32(0)]) / float(a_plus_cher)
        b_plus_cher_avg_spread = 0
        if b_plus_cher > 0:
          b_plus_cher_avg_spread = sum(spread[spread < np.float32(0)]) / float(b_plus_cher)
        max_price = np.max([array_a, array_b], axis = 0)
        cum_price = np.sum(max_price)
        cum_spread = np.sum(abs(spread))
        cum_rel_spread = cum_spread / cum_price
        rel_spread = spread / max_price
        avg_rel_spread = np.mean(abs(rel_spread))
        # print nb_produits, a_plus_cher, b_plus_cher, cum_price, cum_spread
        print period_index
        print rayon, '; nb produits:', nb_produits
        print 'a plus cher:', a_plus_cher, np.round(a_plus_cher_avg_spread, 2)
        print 'b plus cher:', b_plus_cher, np.round(b_plus_cher_avg_spread, 2)
        print 'cum price of products, cum spread:', cum_price, cum_spread
        print 'rel spread, avg relative spread:', \
                   np.around(np.array([cum_rel_spread, avg_rel_spread], dtype = np.float32), decimals = 2), '\n'
  return list_product_prices
  
def get_shop_prices_across_periods(shop_cond, per_1_cond, per_2_cond):
  params = (shop_cond, per_1_cond, shop_cond, per_2_cond)
  list_product_prices = cursor.execute("SELECT a.produit, a.rayon, a.famille, a.prix, b.prix FROM \
                                       (SELECT * FROM qlmc WHERE magasin = ? AND period = ?) a,\
                                       (SELECT * FROM qlmc WHERE magasin = ? AND period = ?) b\
                                       WHERE a.produit = b.produit", params).fetchall()
  # add comparison of product prices: nb of changes, size of change etc.
  return list_product_prices                              

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
print 'columns in table', cursor.execute("PRAGMA table_info(qlmc)").fetchall()
print 'nb of records in table', cursor.execute("SELECT COUNT(*) FROM qlmc").fetchall()[0][0]
list_marques_magasins = cursor.execute("SELECT DISTINCT marque_magasin FROM qlmc").fetchall()
list_magasins = cursor.execute("SELECT DISTINCT magasin FROM qlmc").fetchall()
# list_rayons = cursor.execute("SELECT DISTINCT rayon FROM qlmc").fetchall()
# list_familles = cursor.execute("SELECT DISTINCT famille FROM qlmc").fetchall()
list_produits = cursor.execute("SELECT DISTINCT produit FROM qlmc").fetchall()

# ########################################
# PRODUCT PRICE DISPERSION
# ########################################

some_prod_pd = get_product_price_dispersion(list_produits[0][0], graph = False)

# #######################################
# COMPARISON OF PRICES BETWEEN TWO STORES
# #######################################

# SAME BRAND

# Lille (opposite suburbs of LilLe, 17 km distant (car), both are Hypers)
two_auchan_lille_1 = get_two_shop_prices(u"AUCHAN ENGLOS", u"AUCHAN VILLENEUVE D''ASCQ", 1)
two_auchan_lille_2 = get_two_shop_prices(u"AUCHAN ENGLOS", u"AUCHAN VILLENEUVE D''ASCQ", 2)

# Nantes: (opposite sides of Nantes, c. 15. km distant (car))
two_auchan_nantes_1 = get_two_shop_prices(u"AUCHAN ST HERBLAIN", u"AUCHAN ST SEBASTIEN SUR LOIRE",1)
two_auchan_nantes_2 = get_two_shop_prices(u"AUCHAN ST HERBLAIN", u"AUCHAN ST SEBASTIEN SUR LOIRE",2)

# DIFFERENT BRANDS

# Lille (Villeneuve d'Ascq): Cora vs. Auchan (4km distant (car), both are Hypers)
auchan_cora_lille_0 = get_two_shop_prices(u"CORA VILLENEUVE D''ASCQ", u"AUCHAN VILLENEUVE D''ASCQ", 0)
auchan_cora_lille_1 = get_two_shop_prices(u"CORA VILLENEUVE D''ASCQ", u"AUCHAN VILLENEUVE D''ASCQ", 1)
auchan_cora_lille_2 = get_two_shop_prices(u"CORA VILLENEUVE D''ASCQ", u"AUCHAN VILLENEUVE D''ASCQ", 2)

# ANGERS: "CARREFOUR ANGERS", "GEANT CASINO ANGERS ESPACE ANJOU", "LECLERC ANGERS", "SUPER U ANGERS"
carrefour_leclerc_angers_1 = get_two_shop_prices(u"CARREFOUR ANGERS", u"LECLERC ANGERS", 1)
geant_leclerc_angers_1 = get_two_shop_prices(u"GEANT CASINO ANGERS ESPACE ANJOU", u"LECLERC ANGERS", 1)
geant_carrefour_angers_1 = get_two_shop_prices(u"GEANT CASINO ANGERS ESPACE ANJOU", u"CARREFOUR ANGERS", 1)
geant_superu_angers_2 = get_two_shop_prices(u"GEANT CASINO ANGERS ESPACE ANJOU", u"SUPER U ANGERS", 2)
carrefour_superu_angers_2 = get_two_shop_prices(u"CARREFOUR ANGERS", u"SUPER U ANGERS", 2)

"""
# Lille: "AUCHAN ENGLOS", "AUCHAN VILLENEUVE D''ASCQ", "CORA VILLENEUVE D''ASCQ"
# Two auchan have no products in common at first period...
par_test = (u"AUCHAN VILLENEUVE D''ASCQ", 0)
query_test = cursor.execute("SELECT produit, prix FROM qlmc WHERE magasin = ? AND period = ?", par_test).fetchall()
par_test = (u"AUCHAN ENGLOS", 0)
query_test = cursor.execute("SELECT produit, prix FROM qlmc WHERE magasin = ? AND period = ?", par_test).fetchall()
"""

# test = get_two_shop_prices_two_periods(u"AUCHAN ENGLOS", u"AUCHAN VILLENEUVE D''ASCQ", 1, 2)
# seems like they target different products from one period to the other unfortuately

# #######################################
# STORES WHICH SURVIVE
# #######################################

# Stores which are present across all periods
# No Leclerc among them: could be only stores which are over expensive
list_store_3_periods = cursor.execute("SELECT magasin, marque_magasin FROM qlmc \
                                        GROUP BY magasin HAVING COUNT(DISTINCT period) = 3").fetchall()

# EACH SURVIVING STORE VS. SAME BRAND STORES IN A GIVEN PERIOD
"""
period_cond = 2
for (store_3_periods, brand_store_3_periods) in list_store_3_periods:
  params = (brand_store_3_periods, period_cond, store_3_periods, period_cond)
  list_shop_vs_brand = cursor.execute("SELECT a.produit, a.prix, b.prix FROM \
                                   (SELECT produit, AVG(prix) AS prix FROM qlmc\
                                     WHERE marque_magasin = ? AND period = ? GROUP BY produit) a,\
                                   (SELECT * FROM qlmc WHERE magasin = ? AND period = ?) b\
                                   WHERE a.produit = b.produit", params).fetchall()
  cum_gap = 0
  count_more_expensive = 0
  for (product, brand_average_price, shop_price) in list_shop_vs_brand:
    cum_gap += shop_price - brand_average_price
    count_more_expensive += (shop_price > brand_average_price)
  print '{0:35s};    cum price minus avg: {1:> 3.2f};    % of price > avg: {2:> 2.2f};    nb of products: {3:> 4d}'\
                           .format(store_3_periods, round(cum_gap, 2),\
                           round(count_more_expensive / float(len(list_shop_vs_brand)), 2), len(list_shop_vs_brand))
"""                   

# #############################################
# COMPARISON OF PRICES OF A STORE VS SAME BRAND
# #############################################
                            
# A STORE VS. SAME BRAND STORES IN A GIVEN PERIOD => create a function
params = (list_store_3_periods[0][1], 0, list_store_3_periods[0][0], 0)
list_shop_vs_brand = cursor.execute("SELECT a.produit, a.prix, b.prix FROM \
                                       (SELECT produit, AVG(prix) AS prix FROM qlmc\
                                         WHERE marque_magasin = ? AND period = ? GROUP BY produit) a,\
                                       (SELECT * FROM qlmc WHERE magasin = ? AND period = ?) b\
                                       WHERE a.produit = b.produit", params).fetchall()
cum_gap = 0
count_more_expensive = 0
for (product, brand_average_price, shop_price) in list_shop_vs_brand:
  cum_gap += shop_price - brand_average_price
  count_more_expensive += (shop_price > brand_average_price)
print '{0:35s};    cum price minus avg: {1: 3.2f};    % of prices > avg: {2: 2.2f};    nb of products: {3: 4d}'\
                    .format(list_store_3_periods[0][0], round(cum_gap,2),\
                    round(count_more_expensive/float(len(list_shop_vs_brand)),2), len(list_shop_vs_brand))

# TODO: Create INDEX(ES)
# DO IT AS LECLERC: WOULD THE BRAND BE CHEAPER WITHOUT THEM OR NOT ?
# BY THE WAY: CHECK HOW PRODUCTS PICKED CHANGE OVER TIME (CHEAPEST AT LECLERC MORE LIKELY TO SURVIVE?)        
 
# #############################################
# COMPARISON OF PRICES OF A STORE OVER TIME
# #############################################

# TODO: survival on 3 periods...
# checks only among 3 period survivors => extend

list_interesting_survivors = []
for store in list_store_3_periods:
  produits_1_2 = get_shop_prices_across_periods(store[0], 1, 2)
  if len(produits_1_2) > 50:
    print store[0], 'has', len(produits_1_2),' products in periods 1 and 2'
    list_interesting_survivors.append((store[0], len(produits_1_2), produits_1_2))

"""
# SQL BACKUP & REMINDER

# GET PRICES OF COMMON PRODUCTS AT TWO STORES
params = (list_store_3_periods[0][0], 0, list_store_3_periods[1][0], 0)
list_price_tuples = cursor.execute("SELECT a.produit, a.prix, b.prix FROM \
                                      (SELECT * FROM qlmc WHERE magasin = ? AND period = ?) a,\
                                      (SELECT * FROM qlmc WHERE magasin = ? AND period = ?) b\
                                      WHERE a.produit = b.produit", params).fetchall()
     
# AVERAGE PRICE PER PRODUCT IN A GIVEN PERIOD
params = (list_brands[0] + '%', 0)
list_avg_prices_brand = cursor.execute("SELECT produit, AVG(prix), COUNT(prix) FROM qlmc\
                                          WHERE magasin LIKE ? AND period = ? GROUP BY produit", params).fetchall()
     

# count distinct values in a column
print cursor.execute("SELECT COUNT(DISTINCT produit) FROM qlmc").fetchall()[0][0]
# like query
list_test_like_prix = cursor.execute("SELECT prix FROM qlmc WHERE produit LIKE 'Lorenz%'").fetchall()

# COMPARE TWO STORES IN A GIVEN PERIOD
# WITHOUT USING marque_magasin => LIKE (maybe slower without index...)
params = (list_brands[0] + '%', 0, list_store_3_periods[0][0], 0)
list_shop_vs_brand = cursor.execute("SELECT a.produit, a.prix, b.prix FROM \
                                       (SELECT produit, AVG(prix) AS prix FROM qlmc\
                                         WHERE magasin LIKE ? AND period = ? GROUP BY produit) a,\
                                       (SELECT * FROM qlmc WHERE magasin = ? AND period = ?) b\
                                       WHERE a.produit = b.produit", params).fetchall()

# WITHOUT USING marque_magasin => LIKE (maybe slower without index...)
period_cond = 2
for (store_3_periods,) in list_store_3_periods:
  for brand in ['AUCHAN', 'CARREFOUR MARKET', 'CENTRE E. LECLERC', 'GEANT CASINO', 'INTERMARCHE SUPER', 'SUPER U']:
  # take sub_list_brands so far (TODO: replace LIKE by REGEX in sql request)
    if brand in store_3_periods:
      params = (brand + '%', period_cond, store_3_periods, period_cond)
      list_shop_vs_brand = cursor.execute("SELECT a.produit, a.prix, b.prix FROM \
                                       (SELECT produit, AVG(prix) AS prix FROM qlmc\
                                         WHERE magasin LIKE ? AND period = ? GROUP BY produit) a,\
                                       (SELECT * FROM qlmc WHERE magasin = ? AND period = ?) b\
                                       WHERE a.produit = b.produit", params).fetchall()
      cum_gap = 0
      count_more_expensive = 0
      for (product, brand_average_price, shop_price) in list_shop_vs_brand:
        cum_gap += shop_price - brand_average_price
        count_more_expensive += (shop_price > brand_average_price)
      print '{0:35s};    cum price minus avg: {1:> 3.2f};    % of price > avg: {2:> 2.2f};    nb of products: {3:> 4d}'\
                               .format(store_3_periods, round(cum_gap, 2),\
                               round(count_more_expensive / float(len(list_shop_vs_brand)), 2), len(list_shop_vs_brand))
"""