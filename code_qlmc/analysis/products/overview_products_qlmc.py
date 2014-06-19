#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path_sub
from add_to_path_sub import *
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

ls_json_files = [u'200705_releves_QLMC',
                 u'200708_releves_QLMC',
                 u'200801_releves_QLMC',
                 u'200804_releves_QLMC',
                 u'200903_releves_QLMC',
                 u'200909_releves_QLMC',
                 u'201003_releves_QLMC',
                 u'201010_releves_QLMC', 
                 u'201101_releves_QLMC',
                 u'201104_releves_QLMC',
                 u'201110_releves_QLMC', # "No brand" starts to be massive
                 u'201201_releves_QLMC',
                 u'201206_releves_QLMC']

ls_ls_products = dec_json(os.path.join(path_dir_built_json, 'ls_ls_products'))
ls_rows = [[i] + product for i, ls_products in enumerate(ls_ls_products) for product in ls_products]
ls_rows =  [row + get_split_brand_product(row[3], ls_brand_patches) for row in ls_rows]

ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Marque', 'Libelle']
df_products = pd.DataFrame(ls_rows, columns = ls_columns)

ls_disp_1 = ['P', 'Rayon', 'Famille', 'Produit']
ls_disp_2 = ['P', 'Rayon', 'Marque', 'Libelle']
ls_disp_3 = ['P', 'Rayon', 'Famille', 'Produit_bu']
ls_disp_4 = ['P', 'Rayon', 'Famille', 'Produit_bu', 'Format']

# STANDARDIZATION OF PRODUCT TITLES

pd.set_option('display.max_colwidth', 80) # default 50 ? 
#print df_products[ls_disp][df_products['P'] == 2].to_string()

df_products['Produit_bu'] = df_products['Produit']
df_products['Produit'] = df_products['Produit'].map(lambda x: clean_product(x))
# todo: clean Marque and Libelle too

# PRODUCT FORMAT

df_products['Format'] = df_products['Produit'].map(get_product_format)
df_format_null = df_products[df_products['Format'].isnull()]
#print df_format_null[ls_disp_4].to_string()
#print df_products['Format'].value_counts()[-100:].to_string()
## looks ok but get rid of format in Libelle_light

# PRODUCT TURNOVER

ls_alive_products = df_products['Produit'][df_products['P'] == 1].unique()
ls_dead_products = []
per_start, per_end = 1, 9
print u'Product turnover (products surviving per period)', per_start, 'to', per_end
for period in range(per_start, per_end):
  ls_products = df_products['Produit'][df_products['P'] == period].unique()
  ls_dead_products.append([x for x in ls_alive_products if x not in ls_products])
  ls_alive_products = [x for x in ls_alive_products if x in ls_products]
  print period, len(ls_alive_products)

# Inspect Contrex, Evian, Taillefine, Boursin, St Moret, Bledina (accents?) at per 2: disappear...
per_start, per_end = 1, 9
marque = 'Contrex'
print u'\nProduct of brand', marque, 'from period', per_start, 'to', per_end
for period in range(per_start, per_end):
  print '\n', df_products[ls_disp_1][(df_products['Marque'] == marque) &\
                                     (df_products['P'] == period)].to_string()
# Contrex: pbm with presence or not of word "plate'
# Taillefine: "0% de mg" vs. "0% de matière grasse"

# MOST POPULAR BRANDS (PER PERIOD)

per = 2
print '\nMost popular brands at period', per
for rayon in df_products['Rayon'][df_products['P'] == per].unique():
  print '\n', rayon, len(df_products[(df_products['P'] == per) & (df_products['Rayon'] == rayon)])
  print df_products['Marque'][(df_products['P'] == per) &\
                              (df_products['Rayon'] == rayon)].value_counts()[0:10].to_string()

# PRODUCTS WITH MOST FORMAT (PER PERIOD)

per = 2
df_products['Libelle_nf'] = df_products.apply(lambda x: clean_product(x['Libelle']).\
                                                rstrip(x['Format']),
                                              axis = 1)

# Caution... seems that multi brands in fact
print df_products['Libelle_nf'][df_products['P'] == 2].value_counts()[0:10]

# for period 2 (could get rid and simply loop over 10 most popular)
ls_sim_libs = [u'eau minérale naturelle',
               u'eau minérale naturelle gazeuse',
               u'lait uht demi-écrémé',
               u'coca cola avec caféine',
               u'ricard pastis 45 degrés',
               u'ravioli pur boeuf',
               u'spagheto sauce pleine saveur bolognaise',
               u'thon albacore naturel entier']

print '\nProducts with similar libelles (sev. Marque/Format)'
for lib in ls_sim_libs:
  print '\n', lib
  print df_products[ls_disp_3][(df_products['P'] == per) &\
                               (df_products['Libelle_nf'] == lib)].to_string()
