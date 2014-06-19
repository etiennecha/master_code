#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path_sub
from add_to_path_sub import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

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

# master_all_periods = dec_json(os.path.join(path_dir_built_json, 'master_all_periods'))

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

ls_ls_comparisons = []
for per in range(9,10):
  json_file = ls_json_files[per]
  ls_rows = dec_json(os.path.join(path_dir_source_json, json_file))
  ls_rows = [row + get_split_chain_city(row[3], ls_chain_brands) for row in ls_rows]
  ls_rows =  [row + get_split_brand_product(row[2], ls_brand_patches) for row in ls_rows]
  ls_rows = [[per] + row[:5] + row[6:9] for row in ls_rows]
  ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin',
                'Prix', 'Enseigne', 'Ville', 'Marque']
  df_prices = pd.DataFrame(ls_rows, columns = ls_columns)
  
  # ls_ls_tuple_stores = dec_json(os.path.join(path_dir_built_json, 'ls_ls_tuple_stores'))
  ## fragile for now...
  ls_pairs = ls_ls_pairs[per]
  ls_stores = list(set(df_prices['Magasin'].unique()))
  
  ls_ls_store_fe = dec_json(os.path.join(path_dir_built_json, 'ls_ls_store_fe')) 
  ls_store_fe = ls_ls_store_fe[per]
  dict_store_fe = {k:v for k,v in ls_store_fe}
  
ls_ls_comparisons = dec_json(os.path.join(path_dir_built_json, 'ls_ls_comparisons'))

ls_rayons = [u'Epicerie sucrée',
             u'Epicerie salée',
             u'Boissons',
             u'Droguerie',
             u'Produits frais',
             u'Parfumerie',
             u'Non alimentaire']

ls_rows = []
ls_all_comparisons = [comparison for ls_comparisons in ls_ls_comparisons\
                        for comparison in ls_comparisons]
for comparison in ls_all_comparisons:
  ls_comp = comparison[4]
  nb_a_cheaper = np.sum([rayon[1] for rayon in ls_comp])
  nb_b_cheaper = np.sum([rayon[2] for rayon in ls_comp])
  nb_a_equal_b = np.sum([rayon[3] for rayon in ls_comp])
  rr = 0
  nb_prods = nb_a_cheaper + nb_b_cheaper + nb_a_equal_b
  same = nb_a_equal_b / float(nb_a_cheaper + nb_b_cheaper + nb_a_equal_b)
  
  if nb_a_cheaper < nb_b_cheaper:
    cheaper_store = 'b'
    rr = nb_a_cheaper / float(nb_a_cheaper + nb_b_cheaper + nb_a_equal_b)
  elif nb_a_cheaper > nb_b_cheaper:
    cheaper_store = 'a'
    rr = nb_b_cheaper / float(nb_a_cheaper + nb_b_cheaper + nb_a_equal_b)
  elif nb_a_cheaper == nb_b_cheaper:
    cheaper_store = 'e'
    rr = nb_b_cheaper / float(nb_a_cheaper + nb_b_cheaper + nb_a_equal_b)
  
  # should np.nan if too few values
  dict_comp = {x[0]:x[1:] for x in ls_comp}
  if cheaper_store == 'b':
    comp_ind = 0
  else:
    comp_ind = 1
  rr_detailed = []
  for rayon in ls_rayons:
    comp_rayon = dict_comp.get(rayon, [])
    nb_rayon = sum(comp_rayon)
    if comp_rayon and nb_rayon >= 4:
      rr_detailed.append(comp_rayon[comp_ind]/float(nb_rayon))
    else:
      rr_detailed.append(np.nan)
  ls_rows.append(comparison[0:4] + [cheaper_store, nb_prods, rr, same] + rr_detailed)

ls_columns = ['Store_a', 'Store_b', 'Fe_a', 'Fe_b', 'Nch', 'nb', 'rr', 'same',
              'EpiSu', 'EpiSa', 'Boissons', 'Droguerie', 'Frais',
              'Parfumerie', 'NonAlim']
df_rr = pd.DataFrame(ls_rows, columns = ls_columns)

pd.options.display.float_format = '{:4,.2f}'.format

df_rr['Diff'] = df_rr['Fe_a'] - df_rr['Fe_b']
df_rr['Mch'] = 'e'
df_rr['Mch'][df_rr['Diff'] > 0] = 'b'
df_rr['Mch'][df_rr['Diff'] < 0] = 'a'

ls_disp_1 = ['Store_a', 'Store_b', 'Fe_a', 'Fe_b', 
             'Diff', 'Mch', 'Nch', 'nb', 'rr', 'same',
             'EpiSu', 'EpiSa', 'Boissons', 'Frais',
             'Parfumerie', 'Droguerie', 'NonAlim']

ls_disp_2 = ['Store_a', 'Store_b', 'Fe_a', 'Fe_b',
             'Diff', 'Mch', 'Nch', 'nb', 'rr', 'same',
             'EpiSu', 'EpiSa', 'Boissons', 'Frais']

df_rr = df_rr[df_rr['nb'] > 100]

print '\nNb pairs', len(df_rr)
print 'Nb pairs: Average vs. Nb', len(df_rr[ls_disp_2][df_rr['Mch'] != df_rr['Nch']])
# looks like there are mistakes in one period in particular.. big diffs
print 'More conservative', len(df_rr[ls_disp_2][(df_rr['Mch'] != df_rr['Nch']) &\
                                             (df_rr['Diff'].abs() <= 1.0)])
# In fact probably half of these wrong still...
print df_rr[ls_disp_2][(df_rr['Mch'] != df_rr['Nch']) &\
                       (df_rr['Diff'] <= 1.0)].to_string()

# print df_rr[ls_disp_2].to_string()

ax = plt.subplot()
ax.scatter(df_rr['Diff'][df_rr['Diff'].abs() <= 1.0].abs(),
           df_rr['rr'][df_rr['Diff'].abs() <= 1.0])
ax.set_xlim(0.0, 1.0)
ax.set_ylim(0.0, 0.5)
ax.set_xlabel('Estimated price difference')
ax.set_ylabel('Rank reversals')
plt.show()

print len(df_rr['Diff'][df_rr['Diff'].abs() <= 1.0].abs()), 'point on graphs'

ls_stats_desc = ['nb', 'rr', 'same', 'EpiSu', 'EpiSa', 'Boissons', 'Frais']
print '\nGeneral stats descs'
print df_rr[ls_stats_desc].describe()
print 'General stats descs, limiting differentiation'
print df_rr[df_rr['Diff'].abs() <= 0.08][ls_stats_desc].describe()
