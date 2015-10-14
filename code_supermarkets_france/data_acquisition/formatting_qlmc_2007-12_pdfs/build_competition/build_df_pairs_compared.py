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

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

df_comp_pairs = pd.read_csv(os.path.join(path_built_csv,
                                         'df_comp_store_pairs.csv'),
                            encoding = 'utf-8')

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

# ###############
# COMPARE PAIRS
# ###############

Period = 2
df_comp_pairs_per = df_comp_pairs[df_comp_pairs['Period'] == Period]
df_prices_per = df_prices[df_prices['Period'] == Period]

ls_rows_compa = []
store_0_save = None
for store_0, store_1 in df_comp_pairs_per[['Store_0', 'Store_1']].values:
  # taking advantage of order requires caution on first loop
  if store_0 != store_0_save:
    df_prices_0 = df_prices_per[df_prices_per['Store'] == store_0]
    store_0_save = df_prices_per['Store'].iloc[0]
  df_prices_1 = df_prices_per[df_prices_per['Store'] == store_1]
  
  # todo: see if need family and subfamily for matching (not much chge)
  df_duel = pd.merge(df_prices_0,
                     df_prices_1,
                     how = 'inner',
                     on = ['Department', 'Family', 'Product_norm'],
                     suffixes = ['_0', '_1'])
  ls_rows_compa.append((Period,
                        store_0,
                        store_1,
                        len(df_duel),
                        len(df_duel[df_duel['Price_0'] < df_duel['Price_1']]),
                        len(df_duel[df_duel['Price_0'] > df_duel['Price_1']]),
                        len(df_duel[df_duel['Price_0'] == df_duel['Price_1']]),
                        df_duel[['Price_0', 'Price_1']].sum().argmin(),
                        np.abs((df_duel[['Price_0', 'Price_1']].sum().min() /\
                                  df_duel[['Price_0', 'Price_1']].sum().max() - 1)* 100)))

# Pbm: pct compa does not make sense: todo do always cheapest / most expensive
df_repro_compa = pd.DataFrame(ls_rows_compa,
                              columns = ['Period',
                                         'Store_0',
                                         'Store_1',
                                         'Nb_obs',
                                         'Nb_0_wins',
                                         'Nb_1_wins',
                                         'Nb_draws',
                                         'Winner_value',
                                         'Winner_value_pct'])

ls_pctiles = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
print df_repro_compa['Winner_value_pct'].describe(percentiles = ls_pctiles)

df_repro_compa['Rank_Rev'] = df_repro_compa['Nb_1_wins'] /\
                               df_repro_compa['Nb_obs'] * 100

df_repro_compa.loc[df_repro_compa['Nb_1_wins'] >\
                     df_repro_compa['Nb_0_wins'],
                   'Rank_rev'] = df_repro_compa['Nb_0_wins'] /\
                                   df_repro_compa['Nb_obs'] * 100

print df_repro_compa['Rank_rev'].describe()

import matplotlib.pyplot as plt
df_repro_compa.plot(kind = 'scatter', x = 'Winner_value_pct', y = 'Rank_Rev')
plt.show()

# Check if some products are always draws? how to do efficiently?

## ##############
## BUILD DF PAIRS
## ##############
#
#ls_comparisons = []
#for per in range(4): #df_pairs['P'].unique():
#  # COMPAIR PRICES BETWEEN PAIRS
#  df_qlmc_per = df_qlmc[df_qlmc['P'] == per].copy()
#  df_pairs_per = df_pairs[df_pairs['P'] == per].copy()
#  for row_i, row in df_pairs_per.iterrows():
#    ls_comparisons.append([per,
#                           row['id_lsa_0'],
#                           row['id_lsa_1'],
#                           row['dist']] +\
#                           compare_stores(df_qlmc_per,
#                                          'id_lsa',
#                                          row['id_lsa_0'],
#                                          row['id_lsa_1']))
#ls_columns = ['P', 'id_lsa_0', 'id_lsa_1', 'dist'] +\
#             ['nb_prod', 'nb_equal', 'nb_0_cheap', 'nb_1_cheap',
#              'tot_0', 'tot_1', 'pct_tot_diff', 'pct_avg_diff']
#
#df_comparison = pd.DataFrame(ls_comparisons, columns = ls_columns)
#df_comparison['pct_rr'] = df_comparison[['nb_0_cheap', 'nb_1_cheap']].min(1) /\
#                            df_comparison['nb_prod']
#df_comparison['pct_equal'] = df_comparison['nb_equal'] / df_comparison['nb_prod']
#
## ADD ENSEIGNE (can add competition intensity etc same way)
## delete duplicate for matching
#df_stores.drop_duplicates(['P', 'id_lsa'], inplace = True)
#
#df_comparison = pd.merge(df_comparison,
#                         df_stores[['P', 'id_lsa', 'Enseigne', 'Magasin']],
#                         left_on = ['P', 'id_lsa_0'],
#                         right_on = ['P', 'id_lsa'],
#                         how = 'left')
## Caution if merge lsa data: Enseigne too...
#df_comparison.rename(columns = {'Enseigne' : 'Enseigne_0',
#                                'Magasin' : 'Magasin_0'}, inplace = True)
#df_comparison.drop(['id_lsa'], axis = 1, inplace = True)
#
#df_comparison = pd.merge(df_comparison,
#                         df_stores[['P', 'id_lsa', 'Enseigne', 'Magasin']],
#                         left_on = ['P', 'id_lsa_1'],
#                         right_on = ['P', 'id_lsa'],
#                         how = 'left')
#df_comparison.rename(columns = {'Enseigne' : 'Enseigne_1',
#                                'Magasin' : 'Magasin_1'}, inplace = True)
#df_comparison.drop(['id_lsa'], axis = 1, inplace = True)
#
#df_comparison = df_comparison[df_comparison['nb_prod'] != 0]
#df_pairs = df_comparison[df_comparison['Enseigne_0'] != df_comparison['Enseigne_1']]
#df_same = df_comparison[df_comparison['Enseigne_0'] == df_comparison['Enseigne_1']]
#
#pd.set_option('float_format', '{:5.2f}'.format)
#ls_disp = ['dist', 'nb_prod', 'pct_equal', 'pct_rr', 'tot_0', 'pct_tot_diff', 'pct_avg_diff']
#
#print '\nPairs of stores belonging to the same chain'
#print df_same[ls_disp].describe()
#
#print '\nPairs of competing stores'
#print df_pairs[ls_disp].describe()
#
#print df_pairs[df_pairs['pct_equal'] > 0.3].T.to_string()
#ls_disp_equal = ['P', 'dist', 'nb_prod', 'pct_equal',
#                 'id_lsa_0', 'id_lsa_1', 'Magasin_0', 'Magasin_1']
#print df_pairs[ls_disp_equal][df_pairs['pct_equal'] > 0.2].to_string()
#
### TEST NEW FUNCTION
### good ex with "SYSTEME U THEZAN LES BEZIERS", "CHAMPION VILLENEUVE LES BEZIERS" (P0)
#def get_df_both(df_qlmc, per, field_id, id_0, id_1): 
#  df_prices = df_qlmc[df_qlmc['P'] == per]
#  df_store_0 = df_prices[['Prix','Produit','Rayon','Famille']]\
#                           [(df_prices[field_id] == id_0)].copy()
#  df_store_0.rename(columns = {'Prix' : 'Prix_0'}, inplace = True)
#  df_store_1 = df_prices[['Prix','Produit']]\
#                            [(df_prices[field_id] == id_1)].copy()
#  df_store_1.rename(columns = {'Prix' : 'Prix_1'}, inplace = True)
#  df_both = pd.merge(df_store_0, df_store_1,
#                     on = 'Produit', how = 'inner')
#  return df_both
#
#df_test = get_df_both(df_qlmc, 0, 'id_lsa', '374', '394')
##print compare_stores_new(df_prices, field_id, id_0, id_1)



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
