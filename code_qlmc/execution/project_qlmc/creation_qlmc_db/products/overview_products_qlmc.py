﻿#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import *
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import pandas as pd

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')

path_dir_source_json = os.path.join(path_dir_qlmc, 'data_source', 'data_json_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')

# LOAD PRODUCTS (directly from original data?)

ls_ls_products = dec_json(os.path.join(path_dir_built_json, 'ls_ls_products.json'))
ls_rows = [[i] + product for i, ls_products\
             in enumerate(ls_ls_products)\
               for product in ls_products]
ls_rows =  [row + get_split_brand_product(row[3], ls_brand_patches)\
              for row in ls_rows]

ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Marque', 'Libelle']
df_products = pd.DataFrame(ls_rows, columns = ls_columns)

ls_disp_1 = ['P', 'Rayon', 'Famille', 'Produit']

pd.set_option('display.max_colwidth', 80) # default 50 ? 

# STANDARDIZE PRODUCTS

df_products['Produit_O'] = df_products['Produit']

# Ad hoc cleaning
ls_fixed_products = [[u'mozzarella 19% mat. gr. environ - 125 g environ',
                      u'mozzarella 19% mat. gr. environ, 125 g environ'],
                     [u'Mozzarella 19% mat. gr. environ - 125 g environ',
                      u'Mozzarella 19% mat. gr. environ, 125 g environ'],
                     [u'mozzarella 18% mat. gr. minimum - 125 g environ',
                      u'mozzarella 18% mat. gr. minimum, 125 g environ'],
                     [u'Evian - Eau minérale naturelle, 1,5L',
                      u'Evian - Eau minérale naturelle plate, 1,5L'],
                     [u'Evian - Eau minéralenaturelle, 1L',
                      u'Evian - Eau minérale plate naturelle, 1L'],
                     [u'Evian - Eau minérale naturelle, 6x1,5L',
                      u'Evian - Eau minérale naturelle plate, 6x1,5L'],
                     [u'Evian - Eau minérale naturelle, 6x0,5L',
                      u'Evian - Eau minérale naturelle plate, 6 x 0,5L'], # not all periods
                     [u'Courmayeur - Eau minérale naturelle, 1,5L',
                      u'Courmayeur - Eau minérale plate naturelle, 1,5L'],
                     [u'Hepar - Eau minérale naturelle, 1L',
                      u'Hepar - Eau minérale naturelle plate, 1L'],
                     [u'Contrex - Eau minérale naturelle, 6x50cl',
                      u'Contrex - Eau minérale plate naturelle, 6x50cl'],
                     [u'Contrex - Eau minérale naturelle plate, 6x50cl',
                      u'Contrex - Eau minérale plate naturelle, 6x50cl'],
                     [u'Contrex - Eau minérale naturelle, 6x1,5L',
                      u'Contrex - Eau minérale naturelle plate, 6x1,5L'],
                     [u'Contrex - Eau minérale naturelle, 1,5L',
                      u'Contrex - Eau minérale naturelle plate, 1,5L'],
                     [u"Ballantines - Whisky blend ecossais 7 ans d'âge 40%, 70cl", # more to do
                      u"Ballantines - Whisky blend écossais 7ans d'âge 40 degrés, 70cl"]]

def fix_produit(product, ls_replace_products = ls_fixed_products):
  for old, new in ls_replace_products:
    if product == old:
      return new
  return product
df_products['Produit'] = df_products['Produit'].apply(lambda x: fix_produit(x))

ls_replace_products = [[u'gazeuze', u'gazeuse'],
                       [u', ,', u','],
                       [u' ,', u',']]
def fix_produit_2(product, ls_replace_products = ls_replace_products):
  for old, new in ls_replace_products:
    product = product.replace(old, new)
  return u' '.join([x for x in product.split(u' ') if x])

df_products['Produit'] = df_products['Produit'].apply(lambda x: fix_produit_2(x))

# Alcool: u'degré' vs. u'\xb0' => check robustness
def fix_alcool(product):
  product = re.sub(u'\xb0C?', u' degrés', product)
  return u' '.join([x for x in product.split(u' ') if x])
df_products.loc[(df_products['Rayon'] == u'Boissons') |\
                (df_products['Rayon'] == u'Bières et alcool'),
                'Produit'] = \
  df_products.loc[(df_products['Rayon'] == u'Boissons') |\
                  (df_products['Rayon'] == u'Bières et alcool'),
                  'Produit'].apply(lambda x: fix_alcool(x))

df_products.loc[df_products['Produit'].str.contains(u'vinaigre', case=False),
               'Produit'] =\
  df_products.loc[df_products['Produit'].str.contains(u'vinaigre', case=False),
                  'Produit'].apply(lambda x: fix_alcool(x))

# MG / u'matière grasse' (see case etc)
df_products['Produit'] = df_products['Produit'].apply(\
                           lambda x: re.sub(u'% de MG', u'% de matière grasse', x))

## Check ',' right after int + 'x'
#for x in df_products['Produit'].unique():
#	if re.search(u'[0-9]x,', x, re.IGNORECASE):
#		print x
## fix but might want to check if 6*0.16=1L or 6*1L=6L
df_products['Produit'] = df_products['Produit'].apply(\
                           lambda x: re.sub(u'([0-9])x,\s?', '\\1x', x, re.IGNORECASE))

# Check spaces between ints...
for x in df_products['Produit'].unique():
  if re.search(u'[0-9]\s[0-9]', x):
    print x
# todo: fix u'Vieux Papes - Vin de table rouge Vieux Papes 12°, 7 5cl' etc.

# SPLIT marque AND libelle

df_products['marque'], df_products['libelle'] =\
  zip(*df_products['Produit'].map(\
    lambda x: get_marque_and_libelle(x, ls_brand_patches = ls_brand_patches)))
## Inspect marque
#print df_products['marque'].value_counts().to_string()

# STANDARDIZE marque

# todo: standardize accents and small variations generating duplicates

# STANDARDIZE libelle

df_products['libelle'] = df_products['libelle'].apply(\
                           lambda x: re.sub(u',\s?viande$', u'', x).strip())

## todo: inspect ',' between two ints: safe to transform it to '.'?
## there are generally many spaces... so must be a float if ',' between ints
def convert_float(libelle):
  # avoid: u'Levure boulangère spécial pain Francine x6,30g'
  if not re.search(u'\sx[0-9]+,[0-9]+[a-z]$', libelle, flags=re.IGNORECASE):
    libelle = re.sub(u'([0-9]),([0-9])', u'\\1.\\2', libelle)
  else:
    print libelle
  return libelle
df_products['libelle'] = df_products['libelle'].apply(lambda x: convert_float(x))

## inspect no ',' in libelle
## u'Eau de javel traditionnelle 3 doses de 250ml'
## u'salami danois 20 tranches 200g'
## u'Moutarde Forte en verre de 195g'
#for libelle in df_products['Libelle'].values:
#  if (not u',' in libelle) and (not u'-' in libelle):
#    print libelle

# SPLIT nom AND format

df_products['nom'], df_products['format'] =\
  zip(*df_products['libelle'].map(lambda x: get_nom_and_format(x)))
df_products['format'] = df_products['format'].apply(\
                          lambda x: x.lstrip(u',').lstrip(u'-').strip())

#print df_products[['marque', 'nom', 'format']][df_products['P'] == 0].to_string()
print '\n', df_products['nom'][(df_products['P'] == 0) &\
                               (df_products['format'] == u'')].to_string()
## caution: some have a format which is wrong:
#print '\n', df_products.ix[2165] # replace ',' by '.' in float to avoid such pbms!

ls_sub_format = [u'bouteilles?',
                 u'pet',
                 u'bocal',
                 u'bidon',
                 #u'(maxi-)?brique',
                 u'plastique',
                 u'boîte',
                 u'flacon',
                 u'atomiseur',
                 u'barquettes?',
                 u'sachet',
                 u'pot',
                 u'cellophane',
                 u'paquet(-carton)?',
                 u'pack',
                 # u'plaquette',
                 u'paquets?',
                 u'packets?',
                 u'blister',
                 u'tube',
                 u'sticks?',
                 u'berlingot',
                 u'bloc',
                 u'plateau'
                 u'filet',
                 u'tablette',
                 u'verre',
                 u'papier',
                 u'carton',
                 u'relief']
def clean_format(str_format, ls_sub_format = ls_sub_format):
  for sub_format in ls_sub_format:
    str_format = re.sub(sub_format, u'', str_format, flags=re.IGNORECASE)
  return u' '.join([x for x in str_format.split(u' ') if x])
df_products['format'] = df_products['format'].apply(lambda x: clean_format(x))

# Conservative fix for u'x 80' => u'x80' (other spaces pbms to deal with)
df_products['format'] = df_products['format'].apply(\
                          lambda x: re.sub(u'^x ([0-9])', u'x\\1', x, flags=re.IGNORECASE))
                          
# PRODUCT TURNOVER

ls_alive_products = df_products['Produit'][df_products['P'] == 1].unique()
ls_dead_products = []
per_start, per_end = 1, 9
print u'\nProduct turnover (products surviving per period)', per_start, 'to', per_end
for period in range(per_start, per_end):
  ls_products = df_products['Produit'][df_products['P'] == period].unique()
  ls_dead_products.append([x for x in ls_alive_products if x not in ls_products])
  ls_alive_products = [x for x in ls_alive_products if x in ls_products]
  print period, len(ls_alive_products)

# Inspect Contrex, Evian, Taillefine, Boursin, St Moret, Bledina (accents?) at per 2: disappear
per_start, per_end = 1, 9
marque = 'Contrex'
df_products['marque_nom'] = df_products['marque'] + u' ' + df_products['nom']

print u'\nProduct of brand', marque, 'from period', per_start, 'to', per_end
for period in range(per_start, per_end):
  print '\n', df_products[ls_disp_1][(df_products['marque'] == marque) &\
                                     (df_products['P'] == period)].to_string()
print df_products[['P', 'marque', 'nom', 'format']]\
        [df_products['marque_nom'] == u'Contrex Eau minérale naturelle plate']
# Contrex: pbm with presence or not of word "plate'
# Taillefine: "0% de mg" vs. "0% de matière grasse"

# MOST POPULAR BRANDS (PER PERIOD)

per_ind = 2
print '\nMost popular brands at period', per_ind
for rayon in df_products['Rayon'][df_products['P'] == per_ind].unique():
  print '\n', rayon, len(df_products[(df_products['P'] == per_ind) &\
                                     (df_products['Rayon'] == rayon)])
  print df_products['marque'][(df_products['P'] == per_ind) &\
                              (df_products['Rayon'] == rayon)].value_counts()[0:10].to_string()

# PRODUCTS WITH SAME CONTENT/DIFFERENT FORMATS (PER PERIOD)

per_ind = 2
ls_disp_expl = ['marque', 'nom', 'format']

print '\nProducts with different formats (similar content a priori)'
# Multi brand with same name... need marque_nom
df_products['marque_nom'] = df_products['marque'] + u' ' + df_products['nom']
ls_several_formats = list(df_products['marque_nom']\
                            [df_products['P'] == per_ind].value_counts().index[0:10])
for marque_nom in ls_several_formats:
  print '\n', marque_nom
  print df_products[ls_disp_expl][(df_products['P'] == per_ind) &\
                                  (df_products['marque_nom'] == marque_nom)].to_string()

se_mn_vc = df_products['marque_nom'][df_products['P'] == per_ind].value_counts()
se_mn_multi = se_mn_vc[se_mn_vc > 1]
# print se_mn_multi.to_string() # can merge back to df_products...

# todo:
# 1/ Split brand product
# 3/ Clean product name and format name (print all format name per period etc)
# 4/ Check products across periods? (string or tuple comparison)
# todo: lower case... possibly no accent for product nom...
# todo: loopup in other periods levenshtein stat vs. other products of same format (if stded)
# todo: 'else': most popular name per marque

# e.g.
# u'Lesieur Huile Tournesol 1ère Pression' # 0-7
# u'Lesieur Huile tournesol 1ère Pression' # 8-11 (compare lower case)
# u'Lesieur Huile de tournesol 1ère pression' # 12 (compare lower case and get rid of 'de')

# NB: non NaN here: no format => u''
df_products['produit'] = df_products['marque'].str.lower() + u' _ ' +\
                         df_products['nom'].str.lower() + u' _ ' +\
                         df_products['format'].str.lower()

se_produits_vc = df_products['produit'].value_counts()

print '\nNb products across all periods:', len(se_produits_vc[se_produits_vc == 13])

print '\nProducts which lack one period'
print se_produits_vc[se_produits_vc == 12][0:10] # look missing one...

# Check if products with 10/11/12 records follow same period pattern
ls_pmp = []
for prod in se_produits_vc[se_produits_vc == 12].index:
  ls_prod_pers = df_products['P'][df_products['produit'] == prod].values
  ls_pmp.append(([i for i in range(13) if i not in ls_prod_pers], prod))

# With 11 (since 12 seems mostly due to period 9 where fewer products collected)
# (u'melitta _ filtres \xe0 caf\xe9 papier filtration cors\xe9e 1x4 + d\xe9tartrant _ x 80', [2, 9])
# pbm 'x 80' vs 'x80'
# clear pattern of exit too...

print df_products[['marque', 'nom', 'format']][(df_products['marque'] == u'Le Ster') &\
                                               (df_products['P'] == 0)].to_string()

prod = u"schweppes _ schweppes agrum' boisson gazeuse agrume _ 6x33cl"
print df_products[['P', 'produit']][df_products['produit'] == prod].to_string()

# Visual Examination
#pd.set_option('display.max_colwidth', 50)
#print df_products[['P', 'marque', 'nom', 'format']][0:10].to_string()
pd.set_option('display.max_colwidth', 100)
df_temp = df_products[['produit', 'marque', 'nom', 'format']].copy()
df_temp.drop_duplicates('produit', take_last=True, inplace=True)
df_temp.sort(columns = ['marque', 'nom', 'format'], inplace = True)
# todo: add value counts if possible (then need to load all)
print df_temp[['marque', 'nom', 'format']][0:1000].to_string()

# quite general pbms to be solved
# "Marie - Paà«lla royale, 1,1kg"
for str_pbm in [u'Å"', u'à´', u"à»", u"à¯"]:
  print df_products['Produit'][df_products['Produit'].str.contains(str_pbm)].to_string()

# OUTPUT
df_products_op = df_products[['Produit_O', 'marque', 'nom', 'format']].copy()
df_products_op.rename(columns={'Produit_O': 'Produit'}, inplace = True)
df_products_op.drop_duplicates('Produit', take_last=True, inplace=True)

# HDF5 (drop?)
path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')
qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))
qlmc_data['df_qlmc_products'] = df_products_op
qlmc_data.close()

# CSV (no ',' in fields? how is it dealt with?)
df_products_op.to_csv(os.path.join(path_dir_built_csv,
                                   'df_qlmc_products.csv'),
                      float_format='%.2f',
                      encoding='utf-8',
                      index=False)
