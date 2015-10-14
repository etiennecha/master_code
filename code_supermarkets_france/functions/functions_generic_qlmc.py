#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json
import re
import math
import pandas as pd
import numpy as np

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def parse_kml(kml_str):
  ls_kml_data = []
  ls_placemarks = re.findall('<Placemark>(.*?)<\\/Placemark>', kml_str)
  for placemark in ls_placemarks:
    name = re.search('<name>(.*?)<\\/name>', placemark).group(1)
    coordinates = re.search('<coordinates>(.*?)<\\/coordinates>', placemark).group(1)
    coordinates = map(lambda x: float(x), coordinates.split(',')[0:2][::-1])
    ls_kml_data.append((name, coordinates))
  return ls_kml_data

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

def get_product_format(str_product):
  # pattern = re.compile(',[^,]*[0-9]+[^,]*$|,[^,][0-9]+\s?,\s?[0-9]+[^,]$,')
  pattern = re.compile(',[^,]*[0-9]+[^,]*$|,[^,][0-9]+\s?,\s?[0-9]+[^,]$|-\s?[0-9]+\s?k?g$|-\s?[0-9]+\s?c?l$')
  re_result = pattern.search(str_product)
  if re_result:
    str_format = re_result.group(0)
  else:
    str_format = None
  return str_format

def get_marque_and_libelle(product, ls_brand_patches):
  """
  word_1 = u'Liebig,'
  word_2 = u'Liebig - '
  string_of_interest = u'Liebig, Pursoup velouté légumes, 1L'
  re.sub(ur'^%s\s?,\s?(.*)' %word_1, ur'%s\1' %word_2, string_of_interest)
  """
  split_search = re.search('(\s-)|(-\s)|(-\s-)', product)
  if split_search:
    ls_marque_libelle = [product[:split_search.start()].strip(),
                         product[split_search.end():].strip()]
  else:
    for brand_patch in ls_brand_patches:
      brand_patch_corr = brand_patch + u' - '
      product = re.sub(ur'^%s\s?,\s?(.*)' %brand_patch,\
                       ur'%s\1' %brand_patch_corr,\
                       product)
    split_search = re.search('(\s-)|(-\s)|(-\s-)', product)
    if split_search:
      ls_marque_libelle = [product[:split_search.start()].strip(),
                           product[split_search.end():].strip()]
      # print 'Correction brand:', result
    else:
      ls_marque_libelle = [u'',\
                           product.strip()]
      # print 'No brand:', result
  return ls_marque_libelle

def get_nom_and_format(libelle):
  # pattern = re.compile(',[^,]*[0-9]+[^,]*$|,[^,][0-9]+\s?,\s?[0-9]+[^,]$|-\s?[0-9]+\s?k?g$|-\s?[0-9]+\s?c?l$')
  pattern = re.compile(u'-\s?[0-9]+(\.\s?[0-9]+)?\s?(c?\s?l$|m?\s?l$|k?\s?g$)|'+\
                       u',[^,]*[0-9]+(\.\s?[0-9]+)?[^,]*$', flags=re.IGNORECASE)
  re_result = pattern.search(libelle)
  if re_result:
    ls_nom_format = [libelle[:re_result.start()].strip(),
                     re_result.group(0)]
  else:
    ls_nom_format = [libelle,
                     u'']
  return ls_nom_format

def compute_price_dispersion(se_prices):
  price_mean = se_prices.mean()
  price_std = se_prices.std()
  coeff_var = se_prices.std() / se_prices.mean()
  price_range = se_prices.max() - se_prices.min()
  gain_from_search = se_prices.mean() - se_prices.min()
  return [len(se_prices), se_prices.min(), se_prices.max(), price_mean, 
          price_std, coeff_var, price_range, gain_from_search]

def compare_stores_det(field_store, store_a, store_b, df_prices, category, period_ind = None):
  if period_ind:
    df_prices_per = df_prices[df_prices['P'] == period_ind]
  else:
    df_prices_per = df_prices
  df_store_a = df_prices_per[['Prix', 'Produit', 'Rayon', 'Famille']]\
                           [(df_prices_per[field_store] == store_a)].copy()
  df_store_a.rename(columns = {'Prix' : 'Prix_a'}, inplace = True)
  df_store_b = df_prices_per[['Prix','Produit']]\
                            [(df_prices_per[field_store] == store_b)].copy()
  df_store_b.rename(columns = {'Prix' : 'Prix_b'}, inplace = True)
  df_both = pd.merge(df_store_a, df_store_b,
                     on = 'Produit', how = 'inner')
  ls_str_categories = []
  ls_a_cheaper, ls_b_cheaper, ls_a_equal_b = [], [], []
  for str_category in df_both[category].unique():
    df_cat = df_both[df_both[category] == str_category]
    ls_str_categories.append(str_category)
    ls_a_cheaper.append(len(df_cat[df_cat['Prix_a'] < df_cat['Prix_b']]))
    ls_b_cheaper.append(len(df_cat[df_cat['Prix_a'] > df_cat['Prix_b']]))
    ls_a_equal_b.append(len(df_cat[df_cat['Prix_a'] == df_cat['Prix_b']]))
  return [ls_str_categories, ls_a_cheaper, ls_b_cheaper, ls_a_equal_b]

def compare_stores(df_prices, field_id, id_0, id_1):
  df_store_0 = df_prices[['Prix', 'Produit', 'Rayon', 'Famille']]\
                           [(df_prices[field_id] == id_0)].copy()
  df_store_0.rename(columns = {'Prix' : 'Prix_0'}, inplace = True)
  df_store_1 = df_prices[['Prix','Produit']]\
                            [(df_prices[field_id] == id_1)].copy()
  df_store_1.rename(columns = {'Prix' : 'Prix_1'}, inplace = True)
  df_both = pd.merge(df_store_0, df_store_1,
                     on = 'Produit', how = 'inner')
  df_both['Diff'] = df_both['Prix_1'] - df_both['Prix_0']
  nb_products = len(df_both)
  nb_equal = len(df_both[df_both['Diff'].abs() < 1e-05])
  nb_cheaper_0 = len(df_both[df_both['Diff'] >= 1e-05])
  nb_cheaper_1 = len(df_both[df_both['Diff'] <= -1e-05])
  tot_sum_0 = df_both['Prix_0'].sum()
  tot_sum_1 = df_both['Prix_1'].sum()
  abs_pct_tot_diff = np.abs(df_both['Diff'].sum()) /\
                              df_both[['Prix_0', 'Prix_1']].sum(0).min() * 100
  avg_abs_pct_diff = (df_both['Diff'] / df_both[['Prix_0', 'Prix_1']].min(1)).abs().mean() * 100
  return [nb_products, nb_equal,
          nb_cheaper_0, nb_cheaper_1,
          tot_sum_0, tot_sum_1,
          np.round(abs_pct_tot_diff, 1), np.round(avg_abs_pct_diff, 1)]

def compute_distance(coordinates_A, coordinates_B):
  d_lat = math.radians(float(coordinates_B[0]) - float(coordinates_A[0]))
  d_lon = math.radians(float(coordinates_B[1]) - float(coordinates_A[1]))
  lat_1 = math.radians(float(coordinates_A[0]))
  lat_2 = math.radians(float(coordinates_B[0]))
  a = math.sin(d_lat/2.0) * math.sin(d_lat/2.0) + \
        math.sin(d_lon/2.0) * math.sin(d_lon/2.0) * math.cos(lat_1) * math.cos(lat_2)
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  distance = 6371 * c
  return round(distance, 2)

def compute_distance_ar(ar_lat_A, ar_lng_A, ar_lat_B, ar_lng_B):
  d_lat = np.radians(ar_lat_B - ar_lat_A)
  d_lng = np.radians(ar_lng_B - ar_lng_A)
  lat_1 = np.radians(ar_lat_A)
  lat_2 = np.radians(ar_lat_B)
  ar_a = np.sin(d_lat/2.0) * np.sin(d_lat/2.0) + \
           np.sin(d_lng/2.0) * np.sin(d_lng/2.0) * np.cos(lat_1) * np.cos(lat_2)
  ar_c = 2 * np.arctan2(np.sqrt(ar_a), np.sqrt(1-ar_a))
  ar_distance = 6371 * ar_c
  return np.round(ar_distance, 2)

def get_ls_ls_cross_distances(ls_gps):
  # Size can be lowered by filling only half the matrix
  ls_ls_cross_distances = [[np.nan for gps in ls_gps] for gps in ls_gps]
  for i, gps_i in enumerate(ls_gps):
    for j, gps_j in enumerate(ls_gps[i+1:], start = i+1):
      if gps_i and gps_j:
        distance_i_j = compute_distance(gps_i, gps_j)
        ls_ls_cross_distances[i][j] = distance_i_j
        ls_ls_cross_distances[j][i] = distance_i_j
  return ls_ls_cross_distances

ls_chain_brands = [u'HYPER CHAMPION',
                   u'CHAMPION',
                   u'INTERMARCHE HYPER',
                   u'INTERMARCHE SUPER',
                   u'INTERMARCHE',
                   u'AUCHAN',
                   u'CARREFOUR MARKET',
                   u'CARREFOUR CITY',
                   u'CARREFOUR CONTACT',
                   u'CARREFOUR PLANET',
                   u'CARREFOUR',
                   u'CORA',
                   u'CENTRE E. LECLERC',
                   u'CENTRE LECLERC',
                   u'E. LECLERC',
                   u'LECLERC EXPRESS',
                   u'LECLERC',
                   u'GEANT CASINO',
                   u'GEANT DISCOUNT',
                   u'GEANT',
                   u'CASINO',
                   u'HYPER U',
                   u'SUPER U',
                   u'SYSTEME U',
                   u'U EXPRESS',
                   u'MARCHE U']

ls_brand_patches = [u'Pepito',
                    u'Liebig',
                    u'Babette',
                    u'Grany',
                    u'Père Dodu',
                    u'Lustucru',
                    u'La Baleine',
                    u'Ethiquable', 
                    u'Bn']
