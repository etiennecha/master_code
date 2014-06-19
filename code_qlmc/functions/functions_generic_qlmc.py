#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json
import re

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
                    [(df_period['Magasin'] == store_a) & (df_period['P'] == period_ind)]
  df_store_a['Prix_a'] = df_store_a['Prix']
  df_store_a = df_store_a.set_index('Produit')
  df_store_a = df_store_a[['Prix_a', 'Rayon', 'Famille']]
  # pandas df for store b
  df_store_b = df_period[['Prix','Produit','Magasin']]\
                         [(df_period['Magasin'] == store_b) & (df_period['P'] == period_ind)]
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

ls_chain_brands = [u'HYPER CHAMPION',
                   u'CHAMPION',
                   u'INTERMARCHE SUPER',
                   u'INTERMARCHE',
                   u'AUCHAN',
                   u'CARREFOUR MARKET',
                   u'CARREFOUR CITY',
                   u'CARREFOUR CONTACT',
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
