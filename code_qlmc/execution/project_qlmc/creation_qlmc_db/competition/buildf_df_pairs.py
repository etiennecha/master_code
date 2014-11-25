#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json')
#path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

# #######################
# BUILD DF QLMC
# #######################

# LOAD DF PRICES

## CSV (no ',' in fields? how is it dealt with?)
print u'Loading qlmc prices'
df_qlmc = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_qlmc_prices.csv'),
                      encoding = 'utf-8')
# date parsing slow... better if specified format?

# MERGE DF QLMC STORES

print u'Adding store lsa indexes'
df_stores = pd.read_csv(os.path.join(path_dir_built_csv,
                             'df_qlmc_stores.csv'),
                        dtype = {'id_lsa': str,
                                 'INSE_ZIP' : str,
                                 'INSEE_Dpt' : str,
                                 'INSEE_Code' : str,
                                 'QLMC_Dpt' : str},
                        encoding = 'UTF-8')
df_stores['Magasin'] = df_stores['Enseigne'] + u' ' + df_stores['Commune']
df_qlmc = pd.merge(df_stores,
                   df_qlmc,
                   on = ['P', 'Magasin'],
                   how = 'right')

# MERGE DF QLMC PRODUCTS

print u'Adding product std names and info'
df_products = pd.read_csv(os.path.join(path_dir_built_csv,
                                       'df_qlmc_products.csv'),
                          encoding='utf-8')
df_qlmc = pd.merge(df_products,
                   df_qlmc,
                   on = 'Produit',
                   how = 'right')

# BUILD NORMALIZED PRODUCT INDEX (needed? rather inter periods?)
print u'Adding Produit_norm: normalized product name'
for field in ['marque', 'nom', 'format']:
  df_qlmc[field].fillna(u'', inplace = True)
df_qlmc['Produit_norm'] = df_qlmc['marque'] + ' ' + df_qlmc['nom']+ ' ' + df_qlmc['format']

# #############
# LOAD PAIRS
# #############

ls_comp_pairs = dec_json(os.path.join(path_dir_built_json,
                                      'ls_qlmc_comp_pairs.json'))
df_pairs = pd.DataFrame(ls_comp_pairs, columns = ['P', 'id_lsa_0', 'id_lsa_1', 'dist'])
se_pair_per_vc = df_pairs['P'].value_counts()
print se_pair_per_vc.to_string()

# ##############
# BUILD DF PAIRS
# ##############

ls_comparisons = []
for per in range(4): #df_pairs['P'].unique():
  # COMPAIR PRICES BETWEEN PAIRS
  df_qlmc_per = df_qlmc[df_qlmc['P'] == per].copy()
  df_pairs_per = df_pairs[df_pairs['P'] == per].copy()
  for row_i, row in df_pairs_per.iterrows():
    ls_comparisons.append([per,
                           row['id_lsa_0'],
                           row['id_lsa_1'],
                           row['dist']] +\
                           compare_stores(df_qlmc_per,
                                          'id_lsa',
                                          row['id_lsa_0'],
                                          row['id_lsa_1']))
ls_columns = ['P', 'id_lsa_0', 'id_lsa_1', 'dist'] +\
             ['nb_prod', 'nb_equal', 'nb_0_cheap', 'nb_1_cheap',
              'tot_0', 'tot_1', 'pct_tot_diff', 'pct_avg_diff']

df_comparison = pd.DataFrame(ls_comparisons, columns = ls_columns)
df_comparison['pct_rr'] = df_comparison[['nb_0_cheap', 'nb_1_cheap']].min(1) /\
                            df_comparison['nb_prod']
df_comparison['pct_equal'] = df_comparison['nb_equal'] / df_comparison['nb_prod']

# ADD ENSEIGNE (can add competition intensity etc same way)
# delete duplicate for matching
df_stores.drop_duplicates(['P', 'id_lsa'], inplace = True)

df_comparison = pd.merge(df_comparison,
                         df_stores[['P', 'id_lsa', 'Enseigne', 'Magasin']],
                         left_on = ['P', 'id_lsa_0'],
                         right_on = ['P', 'id_lsa'],
                         how = 'left')
# Caution if merge lsa data: Enseigne too...
df_comparison.rename(columns = {'Enseigne' : 'Enseigne_0',
                                'Magasin' : 'Magasin_0'}, inplace = True)
df_comparison.drop(['id_lsa'], axis = 1, inplace = True)

df_comparison = pd.merge(df_comparison,
                         df_stores[['P', 'id_lsa', 'Enseigne', 'Magasin']],
                         left_on = ['P', 'id_lsa_1'],
                         right_on = ['P', 'id_lsa'],
                         how = 'left')
df_comparison.rename(columns = {'Enseigne' : 'Enseigne_1',
                                'Magasin' : 'Magasin_1'}, inplace = True)
df_comparison.drop(['id_lsa'], axis = 1, inplace = True)

df_comparison = df_comparison[df_comparison['nb_prod'] != 0]
df_pairs = df_comparison[df_comparison['Enseigne_0'] != df_comparison['Enseigne_1']]
df_same = df_comparison[df_comparison['Enseigne_0'] == df_comparison['Enseigne_1']]

pd.set_option('float_format', '{:5.2f}'.format)
ls_disp = ['dist', 'nb_prod', 'pct_equal', 'pct_rr', 'tot_0', 'pct_tot_diff', 'pct_avg_diff']

print '\nPairs of stores belonging to the same chain'
print df_same[ls_disp].describe()

print '\nPairs of competing stores'
print df_pairs[ls_disp].describe()

print df_pairs[df_pairs['pct_equal'] > 0.3].T.to_string()
ls_disp_equal = ['P', 'dist', 'nb_prod', 'pct_equal',
                 'id_lsa_0', 'id_lsa_1', 'Magasin_0', 'Magasin_1']
print df_pairs[ls_disp_equal][df_pairs['pct_equal'] > 0.2].to_string()

## TEST NEW FUNCTION
## good ex with "SYSTEME U THEZAN LES BEZIERS", "CHAMPION VILLENEUVE LES BEZIERS" (P0)
def get_df_both(df_qlmc, per, field_id, id_0, id_1): 
  df_prices = df_qlmc[df_qlmc['P'] == per]
  df_store_0 = df_prices[['Prix','Produit','Rayon','Famille']]\
                           [(df_prices[field_id] == id_0)].copy()
  df_store_0.rename(columns = {'Prix' : 'Prix_0'}, inplace = True)
  df_store_1 = df_prices[['Prix','Produit']]\
                            [(df_prices[field_id] == id_1)].copy()
  df_store_1.rename(columns = {'Prix' : 'Prix_1'}, inplace = True)
  df_both = pd.merge(df_store_0, df_store_1,
                     on = 'Produit', how = 'inner')
  return df_both

df_test = get_df_both(df_qlmc, 0, 'id_lsa', '374', '394')


#print compare_stores_new(df_prices, field_id, id_0, id_1)

## ################
## DEPRECATED ?
## ################
#
#ls_comparisons = []
#for per in [0]: #df_pairs['P'].unique():
#  # COMPAIR PRICES BETWEEN PAIRS
#  df_qlmc_per = df_qlmc[df_qlmc['P'] == per]
#  df_pairs_per = df_pairs[df_pairs['P'] == per]
#  for row_i, row in df_pairs_per.iterrows():
#    ls_comparisons.append([per,
#                           row['id_lsa_0'],
#                           row['id_lsa_1'],
#                           row['dist'],
#                           compare_stores_det('id_lsa',
#                                              row['id_lsa_0'],
#                                              row['id_lsa_1'],
#                                              df_qlmc_per,
#                                              u'Rayon')])
#
#
#ls_rows_comparison = []
#for comparison in ls_comparisons:
#  nb_a_cheaper = np.sum(comparison[4][1])
#  nb_b_cheaper = np.sum(comparison[4][2])
#  nb_a_equal_b = np.sum(comparison[4][3])
#  rr = 0
#  nb_prods = nb_a_cheaper + nb_b_cheaper + nb_a_equal_b
#  same = nb_a_equal_b / float(nb_a_cheaper + nb_b_cheaper + nb_a_equal_b)
#  if nb_a_cheaper < nb_b_cheaper:
#    cheaper_store = 'b'
#    rr = nb_a_cheaper / float(nb_a_cheaper + nb_b_cheaper + nb_a_equal_b)
#  elif nb_a_cheaper > nb_b_cheaper:
#    cheaper_store = 'a'
#    rr = nb_b_cheaper / float(nb_a_cheaper + nb_b_cheaper + nb_a_equal_b)
#  elif nb_a_cheaper == nb_b_cheaper:
#    cheaper_store = 'e'
#    rr = nb_b_cheaper / float(nb_a_cheaper + nb_b_cheaper + nb_a_equal_b)
#  ls_rows_comparison.append(comparison[:4] +\
#                            [nb_prods, same, rr])
#
#ls_columns = ['P', 'id_lsa_0', 'id_lsa_1', 'Distance',
#              'Nb_Products', 'Equality', 'Rank_reversals']
#df_comparison = pd.DataFrame(ls_rows_comparison,
#                             columns = ls_columns)
