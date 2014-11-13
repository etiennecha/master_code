#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import numpy as np
import pandas as pd
import itertools
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')

path_dir_source_json = os.path.join(path_dir_qlmc, 'data_source', 'data_json_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

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

# #########
# LOAD DATA
# #########

# LOAD PRICES RECORDS

print u'Reading json qlmc price records:'
ls_ls_records = []
for json_file in ls_json_files:
  print json_file
  ls_records = dec_json(os.path.join(path_dir_source_json, json_file))
  ls_ls_records.append(ls_records)

ls_columns = ['P', 'Rayon', 'Famille', 'Produit', 'Magasin', 'Prix', 'Date']
ls_rows = [[i] + record for i, ls_records in enumerate(ls_ls_records)\
             for record in ls_records]
df_qlmc = pd.DataFrame(ls_rows, columns = ls_columns)

df_qlmc['Prix'] = df_qlmc['Prix'].astype(np.float32)

# LOAD STORES AND PRODUCTS

qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))

df_stores = qlmc_data['df_qlmc_lsa_stores']
df_stores['Magasin'] = df_stores['Enseigne'] + u' ' + df_stores['Commune']

df_products = qlmc_data['df_qlmc_products']

# ###########################
# PAIRS IN SAME MUNICIPALITY
# ###########################

# todo: distance (separate file?)
ls_store_pairs = []
ls_comparisons = []
for per_ind in df_stores['P'].unique():
  # GET STORE PAIRS
  se_ic_vc = df_stores['INSEE_Code'][df_stores['P'] == per_ind].value_counts()
  se_ic_mult = se_ic_vc.index[se_ic_vc > 1]
  ls_per_store_pairs = []
  for ic in se_ic_mult:
    ls_stores = list(df_stores['Magasin'][(df_stores['P'] == per_ind) &\
                    (df_stores['INSEE_Code'] == ic)].values)
    ls_ic_store_pairs = list(itertools.combinations(ls_stores, 2))
    ls_ic_store_pairs = [[per_ind] + list(store_pair) for store_pair in ls_ic_store_pairs]
    ls_per_store_pairs += ls_ic_store_pairs
  ls_store_pairs += ls_per_store_pairs
  # COMPAIR PRICES BETWEEN PAIRS
  df_qlmc_per = df_qlmc[df_qlmc['P'] == per_ind]
  for per_ind, store_a, store_b in ls_per_store_pairs:
    ls_comparisons.append([per_ind,
                           store_a,
                           store_b,
                           compare_stores(store_a, store_b, df_qlmc_per, u'Rayon')])

df_pairs = pd.DataFrame(ls_store_pairs,
                        columns = ['P', 'Store_A', 'Store_B'])
# if matching: index or multi criteria

# ###################################
# BUILD DF RANK REVERSALS
# ###################################

ls_rows_comparison = []
for comparison in ls_comparisons:
  nb_a_cheaper = np.sum(comparison[3][1])
  nb_b_cheaper = np.sum(comparison[3][2])
  nb_a_equal_b = np.sum(comparison[3][3])
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
  ls_rows_comparison.append(comparison[:3] +\
                            [nb_prods, same, rr])

ls_columns = ['P', 'Store_A', 'Store_B', 'Nb Products', 'Equality', 'Rank reversals']
df_comparison = pd.DataFrame(ls_rows_comparison,
                             columns = ls_columns)

# ADD ENSEIGNE (can add competition intensity etc same way)
df_comparison = pd.merge(df_comparison, df_stores[['P', 'Magasin', 'Enseigne']],
                         left_on = ['P', 'Store_A'], right_on = ['P', 'Magasin'], how = 'left')
df_comparison.rename(columns = {'Enseigne' : 'Enseigne_A'}, inplace = True)
df_comparison.drop(['Magasin'], axis = 1, inplace = True)

df_comparison = pd.merge(df_comparison, df_stores[['P', 'Magasin', 'Enseigne']],
                         left_on = ['P', 'Store_B'], right_on = ['P', 'Magasin'], how = 'left')
df_comparison.rename(columns = {'Enseigne' : 'Enseigne_B'}, inplace = True)
df_comparison.drop(['Magasin'], axis = 1, inplace = True)

# ##########
# STATS DES
# ##########

df_comp = df_comparison[df_comparison['Enseigne_A'] != df_comparison['Enseigne_B']]

pd.set_option('float_format', '{:5.2f}'.format)

print u'\nPairs with product intersection < 100: Intersection size'
df_comp['Nb Products'][df_comp['Nb Products'] < 100].value_counts()

# Restrict to sufficient intersection
print u'\nDesc statistics for pairs with sufficient product intersection'
df_comp = df_comp[df_comp['Nb Products'] >= 100].copy()
print df_comp.describe()

# INSPECTION (make function?)
print u'\nHighest number of product price equality:'
print df_comp[df_comp['Equality'] == df_comp['Equality'].max()].T.to_string()

print u'\nInspect product price equalities'
store_a, store_b, per_ind = 'CHAMPION LE MANS', 'INTERMARCHE LE MANS', 4
df_store_a= df_qlmc[['Prix','Produit','Rayon','Famille']]\
                  [(df_qlmc['Magasin'] == store_a) & (df_qlmc['P'] == per_ind)].copy()
df_store_a.rename(columns = {'Prix' : 'Prix_a'}, inplace = True)
df_store_a = df_store_a.set_index('Produit')
# pandas df for store b
df_store_b = df_qlmc[['Prix','Produit']]\
                       [(df_qlmc['Magasin'] == store_b) & (df_qlmc['P'] == per_ind)].copy()
df_store_b.rename(columns = {'Prix' : 'Prix_b'}, inplace = True)
df_store_b = df_store_b.set_index('Produit')
# merge pandas df a and b
df_both = df_store_a.join(df_store_b)

pd.set_option('display.max_colwidth', 50)
df_both.reset_index(inplace = True) # max_colwidth does not apply to index
df_both['Spread_pct'] = (df_both['Prix_a'] - df_both['Prix_b']) / df_both['Prix_b']

#print df_both['Spread_pct'].describe()
#print len(df_both[df_both['Spread_pct'] == 0])
#ls_both_disp = ['Rayon', 'Famille', 'Produit', 'Prix_a', 'Prix_b', 'Spread_pct']
#print df_both[ls_both_disp][0:10].to_string()
## probably a mistake...?

# HIGH SHARE OF EQUAL PRICES
print '\nPairs with over 30% products with same price'
print df_comp[df_comp['Equality'] > 0.3].to_string()

# HIGH SHARE OF RANK REVERSALS
print '\nPairs with over 30% rank reversals'
print df_comp[df_comp['Rank reversals'] > 0.45].to_string()
