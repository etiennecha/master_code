#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import json
import numpy as np
import re
import pprint
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

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

def print_brand_products(str_marque):
  df_brand_products = df_products[['P','Produit']][df_products['Marque'] == str_marque]
  df_brand_products = df_brand_products.sort(('Produit','P'))
  print df_brand_products.to_string()

ls_brand_patches = [u'Pepito',
                    u'Liebig',
                    u'Babette',
                    u'Grany',
                    u'Père Dodu',
                    u'Lustucru',
                    u'La Baleine',
                    u'Ethiquable', 
                    u'Bn']

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')

path_dir_source_json = os.path.join(path_dir_qlmc, 'data_source', 'data_json_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

ls_ls_products = dec_json(os.path.join(path_dir_built_json, 'ls_ls_products'))

# Generates pandas dataframe
for i, ls_products in enumerate(ls_ls_products):
  ls_ls_products[i] =  [row + get_split_brand_product(row[2], ls_brand_patches) for row in ls_products]
ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Marque', 'Libelle']
ls_ls_products_temp = [[[i] + row for row in ls_products] for i, ls_products in enumerate(ls_ls_products)]
ls_rows = [a for b in ls_ls_products_temp for a in b]
df_products = pd.DataFrame(ls_rows, columns = ls_columns)

# Set pandas dataframe print option to allow full display of columns etc.
pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 200)
pd.set_option('display.max_colwidth', 150)

# Products present in several periods before treatment
print '\nProducts across periods before any treatment'
df_products_count = df_products['Produit'].value_counts()
for i in range(1, 14):
  print "%02d" %i, np.sum((df_products_count == i))

# Products present in two successive periods
print '\nProducts in two successive periods'
for per_ind in range(13):
  ls_temp =  df_products['Produit'][(df_products['P'] == per_ind) &\
                                    (df_products['Produit'].isin(\
                                        list(df_products['Produit'][df_products['P'] == per_ind+1]
                                                                )))]
  print 'Nb products in both',per_ind, per_ind+1, ':', len(ls_temp)

# Overview of product name differences (In progress)
# 1/ Identify most group of products through brands (ideally across all categories)
# 2/ Print their label at each period (using brand) and compare
# 3/ Look for best correction...

df_marques_count =  df_products['Marque'].value_counts()
brand_example = u'Nutella'
print u'\nNom des produits à chaque période, marque', brand_example
print df_products[['P','Produit']][df_products['Marque'] == brand_example]
# 0  Nutella - Pâte à tartiner chocolat noisette , PotVerre 220g
# 1            Nutella - Pâte à tartiner chocolat noisette, 220g
# ... same as 1
# 9 nothing ! (todo: check if because problem with Marque...)
# 12        Nutella - Pâte à tartiner chocolat et noisettes, 220g
# Hence: 1 => 11 except 9 seem standard, 0 and 12 are to be standardized

# df_products[df_products['Produit'] == u'Nutella - Pâte à tartiner chocolat noisette, 750g']
# df_products[df_products['Produit'] == u'Nutella - Pâte à tartiner chocolat noisette, 220g']
# df_products[df_products['Produit'] == u'Nutella - Pâte à tartiner chocolat noisette, 400g']

ls_marques_ex = [u'Fleury Michon',
                 u'Lu', 
                 u'Tropicana', 
                 u'Volvic', 
                 u'Blédina', 
                 u'Président', 
                 u'Le Petit Marseillais']
# print_brand_products(ls_marques_ex[0])
# print_brand_products(u'Heineken')

# String standardization (general enough)
# 1/ Supress all accents
# 2/ Lower case all string
# 3/ Fix ' ,' (see about '-' instead of ',')
# 4/ Replace 'degrés' and '°C' by '°'... or choose
# 5/ Regular expression for format part: get rid of text (check that it is harmless, try to create new field)
# 5bis/ Take into account ' Fleury Michon - Filets de poulet fines herbes 4 tranches fines , Barquette 120g, viande'
# 6/ Can check results with some more standardization: remove 'et' etc.

# todo: other stuffs (more speficic...)
# 'Filet de poulet rà´ti 4 tranches' at period 7

def get_product_format(str_product):
  # pattern = re.compile(',[^,]*[0-9]+[^,]*$|,[^,][0-9]+\s?,\s?[0-9]+[^,]$,')
  pattern = re.compile(',[^,]*[0-9]+[^,]*$|,[^,][0-9]+\s?,\s?[0-9]+[^,]$|-\s?[0-9]+\s?k?g$|-\s?[0-9]+\s?c?l$')
  re_result = pattern.search(str_product)
  if re_result:
    str_format = re_result.group(0)
  else:
    str_format = None
  return str_format

# print get_product_format(ls_ls_products[0][1618][2]) # corrected in pandas df
# print get_product_format(ls_ls_products[0][500][2]) # ok

df_products['Produit'] = df_products['Produit'].map(lambda x: re.sub(u', viande$', u'', x))
df_products['Format'] = df_products['Produit'].map(get_product_format)

ls_formats_test = list(np.unique(df_products['Format']))
# pprint.pprint(ls_formats_test)
# todo: Check Garnier, Panzani, Dim, Amora, Maille => No format but internally consistent..

df_format_null = df_products[df_products['Format'].isnull()]
# print df_format_null['Produit'].to_string()
# todo: Check products with  remaining ',' (also '-'?)

# todo: match products after standardization of format: 
# todo: require equality (more or less) on product name (w/o format) and format
# todo: check that relation 1 to 1 between original product and product name + stdzed format
