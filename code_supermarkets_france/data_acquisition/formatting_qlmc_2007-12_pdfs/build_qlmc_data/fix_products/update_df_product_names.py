#!/usr/bin/env python
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


path_source = os.path.join(path_data,
                           'data_supermarkets',
                           'data_qlmc_2007-12',
                           'data_source')

path_source_json = os.path.join(path_source, 'data_json')                          
path_source_csv = os.path.join(path_source, 'data_csv')

pd.set_option('display.max_colwidth', 80) # default 50 ? 

df_products = pd.read_csv(os.path.join(path_source_csv,
                                       'df_products_raw.csv'),
                   encoding = 'utf-8')

df_products['Product_O'] = df_products['Product']

# ###############################
# REPLACE PRODUCTS
# ###############################

ls_replace_product = [[u'mozzarella 19% mat. gr. environ - 125 g environ',
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
                      [u"Ballantines - Whisky blend ecossais 7 ans d'âge 40%, 70cl", # todo more
                       u"Ballantines - Whisky blend écossais 7ans d'âge 40 degrés, 70cl"]]

def replace_product(product, ls_replace_product = ls_replace_product):
  for old, new in ls_replace_product:
    if product == old:
      return new
  return product

df_products['Product'] = df_products['Product'].apply(lambda x: replace_product(x))

# #####################################
# FIX PRODUCTS (SPECIAL CHARS + SPACES)
# #####################################

ls_fix_product = [[u'gazeuze', u'gazeuse'],
                  [u'Âoeuf', u"oeuf"],
                  [u', ,', u','],
                  [u' ,', u',']]

def fix_product(product, ls_fix_product = ls_fix_product):
  for old, new in ls_fix_product:
    product = product.replace(old, new)
  return u' '.join([x for x in product.split(u' ') if x])

df_products['Product'] = df_products['Product'].apply(lambda x: fix_product(x))

# ###########
# FIX ACCENTS
# ###########

# "Marie - Paà«lla royale, 1,1kg"
# "Matines Å'ufs frais (...?)"
print u'\nOverview accent issues:'
for str_pbm in [u'Å"', u"à´", u'à´', u"à»", u"à¯", u'à´', ]:
  print df_products['Product'][df_products['Product'].str.contains(str_pbm)].to_string()

ls_fix_accent = [(u"à»", u"û"),
                 (u"à¯", u"ï"),
                 (u"à´", u"ô"),
                 (u'Å"', u'oe'),
                 (u"Å'", u'oe'),
                 (u'à´', u'oe'),
                 (u'à«', u'ë')]

def fix_accent(product, ls_fix_accent = ls_fix_accent):
  for old, new in ls_fix_accent:
    product = product.replace(old, new)
  return product

df_products['Product'] = df_products['Product'].apply(lambda x: fix_accent(x))

# ##########
# FIX ALCOOL
# ##########

# u'degré' vs. u'\xb0' => check robustness

def fix_alcool(product):
  product = re.sub(u'\xb0C?', u' degrés', product)
  return u' '.join([x for x in product.split(u' ') if x])

df_products.loc[(df_products['Department'] == u'Boissons') |\
                (df_products['Department'] == u'Bières et alcool'),
                'Product'] = \
  df_products.loc[(df_products['Department'] == u'Boissons') |\
                  (df_products['Department'] == u'Bières et alcool'),
                  'Product'].apply(lambda x: fix_alcool(x))

df_products.loc[df_products['Product'].str.contains(u'vinaigre', case=False),
               'Product'] =\
  df_products.loc[df_products['Product'].str.contains(u'vinaigre', case=False),
                  'Product'].apply(lambda x: fix_alcool(x))

# #######
# FIX FAT
# #######

# MG / u'matière grasse' (see case etc)
df_products['Product'] = df_products['Product'].apply(\
                           lambda x: re.sub(u'% de MG', u'% de matière grasse', x))

## Check ',' right after int + 'x'
#for x in df_products['Produit'].unique():
#	if re.search(u'[0-9]x,', x, re.IGNORECASE):
#		print x
## fix but might want to check if 6*0.16=1L or 6*1L=6L
df_products['Product'] = df_products['Product'].apply(\
                           lambda x: re.sub(u'([0-9])x,\s?', '\\1x', x, re.IGNORECASE))

# Spaces between numbers (some to be dropped)
print u'\nOverview: spaces between numbers:'
for x in df_products['Product'].unique():
  if re.search(u'[0-9]\s[0-9]', x):
    print x

# todo: fix u'Vieux Papes - Vin de table rouge Vieux Papes 12°, 7 5cl' etc.

# ########################
# SPLIT marque AND libelle
# ########################

df_products['Product_brand'], df_products['Product_desc'] =\
  zip(*df_products['Product'].map(\
    lambda x: get_marque_and_libelle(x, ls_brand_patches = ls_brand_patches)))

## Inspect marque
#print df_products['Product_brand'].value_counts().to_string()

# ##################
# STANDARDIZE marque
# ##################

# todo: standardize accents and small variations generating duplicates

# ###################
# STANDARDIZE libelle
# ###################

df_products['Product_desc'] = df_products['Product_desc'].apply(\
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

print u'\nFixing libelle:'
df_products['Product_desc'] = df_products['Product_desc'].apply(lambda x: convert_float(x))

## inspect no ',' in libelle
## u'Eau de javel traditionnelle 3 doses de 250ml'
## u'salami danois 20 tranches 200g'
## u'Moutarde Forte en verre de 195g'
#for libelle in df_products['Product_desc'].values:
#  if (not u',' in libelle) and (not u'-' in libelle):
#    print libelle

# ####################
# SPLIT nom AND format
# ####################

df_products['Product_name'], df_products['Product_format'] =\
  zip(*df_products['Product_desc'].map(lambda x: get_nom_and_format(x)))

df_products['Product_format'] = df_products['Product_format'].apply(\
                          lambda x: x.lstrip(u',').lstrip(u'-').strip())

print u'\nOverview no format in period 0:'
print df_products['Product_name'][(df_products['Period'] == 0) &\
                               (df_products['Product_format'] == u'')].to_string()
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

df_products['Product_format'] = df_products['Product_format'].apply(lambda x: clean_format(x))

# Conservative fix for u'x 80' => u'x80' (other spaces pbms to deal with)
df_products['Product_format'] = df_products['Product_format'].apply(\
                                  lambda x: re.sub(u'^x ([0-9])', u'x\\1', x, flags=re.IGNORECASE))

# ########################
# POST TREATMENT OVERVIEW
# ########################

# PRODUCT SURVIVAL

ls_alive_products = df_products['Product'][df_products['Period'] == 1].unique()
ls_dead_products = []
per_start, per_end = 1, 9
print u'\nProduct turnover (products surviving per period)', per_start, 'to', per_end
for period in range(per_start, per_end):
  ls_products = df_products['Product'][df_products['Period'] == period].unique()
  ls_dead_products.append([x for x in ls_alive_products if x not in ls_products])
  ls_alive_products = [x for x in ls_alive_products if x in ls_products]
  print period, len(ls_alive_products)

# Inspect Contrex, Evian, Taillefine, Boursin, St Moret, Bledina (accents?) at per 2: disappear
per_start, per_end = 1, 9
Product_brand = 'Contrex'
df_products['Product_brand_and_name'] = df_products['Product_brand'] +\
                                        u' ' +\
                                        df_products['Product_name']

ls_disp_1 = ['Period', 'Department', 'Family', 'Product']
print u'\nProduct of brand', Product_brand, 'from period', per_start, 'to', per_end
for period in range(per_start, per_end):
  print '\n', df_products[ls_disp_1][(df_products['Product_brand'] == Product_brand) &\
                                     (df_products['Period'] == period)].to_string()

print u'\nOverview of one Product_brand_Product_name over time:'
print df_products[['Period', 'Product_brand', 'Product_name', 'Product_format']]\
        [df_products['Product_brand_and_name'] == u'Contrex Eau minérale naturelle plate']
# Contrex: pbm with presence or not of word "plate'
# Taillefine: "0% de mg" vs. "0% de matière grasse"

# MOST POPULAR BRANDS (PER PERIOD)

per_ind = 2
print '\nMost popular brands at period:', per_ind
for rayon in df_products['Department'][df_products['Period'] == per_ind].unique():
  print '\n', rayon, len(df_products[(df_products['Period'] == per_ind) &\
                                     (df_products['Department'] == rayon)])
  print df_products['Product_brand'][(df_products['Period'] == per_ind) &\
                                     (df_products['Department'] == rayon)]\
                                        .value_counts()[0:10].to_string()

# PRODUCTS WITH SAME CONTENT/DIFFERENT FORMATS (PER PERIOD)

per_ind = 2
ls_disp_expl = ['Product_brand', 'Product_name', 'Product_format']

print '\nProducts with different Product_formats (similar content a priori)'
# Multi brand with same name... need Product_brand_Product_name
df_products['Product_brand_and_name'] = df_products['Product_brand'] +\
                                            u' ' +\
                                            df_products['Product_name']
ls_several_Product_formats = list(df_products['Product_brand_and_name']\
                            [df_products['Period'] == per_ind].value_counts().index[0:10])
for Product_brand_Product_name in ls_several_Product_formats:
  print '\n', Product_brand_Product_name
  print df_products[ls_disp_expl][(df_products['Period'] == per_ind) &\
                                  (df_products['Product_brand_and_name'] ==\
                                     Product_brand_Product_name)].to_string()

se_mn_vc = df_products['Product_brand_and_name']\
             [df_products['Period'] == per_ind].value_counts()
se_mn_multi = se_mn_vc[se_mn_vc > 1]
# print se_mn_multi.to_string() # can merge back to df_products...

# Example of evolution of product name:
# u'Lesieur Huile Tournesol 1ère Pression' # 0-7
# u'Lesieur Huile tournesol 1ère Pression' # 8-11 (compare lower case)
# u'Lesieur Huile de tournesol 1ère pression' # 12 (compare lower case and get rid of 'de')

## Check that can use ' _ ' to safely generate standardized product field
#print df_products[(df_products['Product_brand'].str.contains('_')) |
#                  (df_products['Product_name'].str.contains('_')) |
#                  (df_products['Product_format'].str.contains('_'))].to_string()

# NB: non NaN here: no Product_format => u''
df_products['product'] = df_products['Product_brand'].str.lower() + u' _ ' +\
                         df_products['Product_name'].str.lower() + u' _ ' +\
                         df_products['Product_format'].str.lower()

se_produits_vc = df_products['product'].value_counts()

print '\nNb products across all periods:', len(se_produits_vc[se_produits_vc == 13])

print '\nProducts which lack one period:'
print se_produits_vc[se_produits_vc == 12][0:10] # look missing one...

# Check if products with 10/11/12 records follow same period pattern
ls_pmp = []
for prod in se_produits_vc[se_produits_vc == 12].index:
  ls_prod_pers = df_products['Period'][df_products['product'] == prod].values
  ls_pmp.append(([i for i in range(13) if i not in ls_prod_pers], prod))

# With 11 (since 12 seems mostly due to period 9 where fewer products collected)
# (u'melitta _ filtres \xe0 caf\xe9 papier filtration cors\xe9e 1x4 + d\xe9tartrant _ x 80', [2, 9])
# pbm 'x 80' vs 'x80'
# clear pattern of exit too...

print u'\nInspect Product_brand:'
print df_products[['Product_brand', 'Product_name', 'Product_format']]\
        [(df_products['Product_brand'] == u'Le Ster') &\
         (df_products['Period'] == 0)].to_string()

prod = u"schweppes _ schweppes agrum' boisson gazeuse agrume _ 6x33cl"
print df_products[['Period', 'product']][df_products['product'] == prod].to_string()

# Visual Examination
#pd.set_option('display.max_colwidth', 50)
#print df_products[['P', 'Product_brand', 'Product_name', 'Product_format']][0:10].to_string()
pd.set_option('display.max_colwidth', 100)
df_temp = df_products[['product', 'Product_brand', 'Product_name', 'Product_format']].copy()
df_temp.drop_duplicates('product', take_last = True, inplace = True)
df_temp.sort(columns = ['Product_brand', 'Product_name', 'Product_format'], inplace = True)
# todo: add value counts if possible (then need to load all)

print u'\nOverview of processed info:'
print df_temp[['Product_brand', 'Product_name', 'Product_format']][0:10].to_string()

# ######
# OUTPUT
# ######

df_products_op = df_products[['Product_O',
                              'Product_brand',
                              'Product_name',
                              'Product_format']].copy()
df_products_op.rename(columns={'Product_O': 'Product'}, inplace = True)
df_products_op.drop_duplicates('Product', take_last=True, inplace=True)

# CSV (no ',' in fields? how is it dealt with?)
df_products_op.to_csv(os.path.join(path_source_csv,
                                   'df_product_names.csv'),
                      float_Product_format='%.2f',
                      encoding='utf-8',
                      index=False)
