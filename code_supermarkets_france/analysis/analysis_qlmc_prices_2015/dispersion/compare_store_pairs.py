#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
from functions_generic_qlmc import *
import statsmodels.api as sm
import statsmodels.formula.api as smf

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)

# #############
# LOAD DATA
# #############

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str,
                                 'c_insee' : str},
                        encoding = 'utf-8')

df_qlmc = pd.merge(df_prices,
                   df_stores[['store_id', 'id_lsa']],
                   on = 'store_id',
                   how = 'left')

df_comp_pairs = pd.read_csv(os.path.join(path_built_csv,
                                         'df_comp_store_pairs.csv'),
                            dtype = {'id_lsa_0' : str,
                                     'id_lsa_1' : str},
                            encoding = 'utf-8')

df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]
ls_keep_stores = list(df_qlmc['id_lsa'].unique())
ls_prod_cols = ['section', 'family', 'product']

# #####################################
# PREPARE DF PAIRS BASED ON TUP CHAINS
# #####################################

# Build df based on chain tuples
# e.g. LECLERC in cols A, GEANT CASINO in cols B

df_pairs = df_comp_pairs

ls_tup_chains = [('LECLERC', 'GEANT CASINO'),
                 ('LECLERC', 'CARREFOUR'),
                 ('GEANT CASINO', 'CARREFOUR'),
                 ('CARREFOUR', 'AUCHAN'),
                 ('CARREFOUR', 'INTERMARCHE'),
                 ('CARREFOUR', 'SUPER U'),
                 ('AUCHAN', 'INTERMARCHE'),
                 ('AUCHAN', 'SUPER U'),
                 ('INTERMARCHE', 'SUPER U')]
  
ls_copy_cols = ['id_lsa', 'store_id',
                'store_chain', 'store_municipality',
                'enseigne_alt', 'groupe']

ls_df_cp = []
for tup_chains in ls_tup_chains:
  df_cp = df_pairs[(df_pairs['store_chain_0'].isin(tup_chains)) &\
                   (df_pairs['store_chain_1'].isin(tup_chains))].copy()
  tup_sufs = ['A', 'B']
  for brand, suf in zip(tup_chains, tup_sufs):
    for col in ls_copy_cols:
      df_cp[u'{:s}_{:s}'.format(col, suf)] = 0
      df_cp.loc[df_cp['store_chain_0'] == brand,
                     u'{:s}_{:s}'.format(col, suf)] =\
        df_cp[u'{:s}_0'.format(col)]
      df_cp.loc[df_cp['store_chain_1'] == brand,
                     u'{:s}_{:s}'.format(col, suf)] =\
        df_cp[u'{:s}_1'.format(col)]
  ls_drop_cols = [u'{:s}_0'.format(x) for x in ls_copy_cols] +\
                 [u'{:s}_1'.format(x) for x in ls_copy_cols]
  df_cp.drop(ls_drop_cols, axis = 1, inplace = True)
  ls_df_cp.append(df_cp)

df_cp_all = pd.concat(ls_df_cp)

# ##############################
# COMPARE TUP CHAIN STORE PAIRS
# ##############################

# Costly to search by store_id within df_prices
# hence first split df_prices in chain dataframes
dict_chain_dfs = {store_chain: df_qlmc[df_qlmc['store_chain'] == store_chain]\
                    for store_chain in df_qlmc['store_chain'].unique()}

ls_rows_compa = []
for sc_0, sc_1 in ls_tup_chains:
  df_cp = df_cp_all[(df_cp_all['store_chain_A'] == sc_0) &\
                    (df_cp_all['store_chain_B'] == sc_1)]
  df_chain_0 = dict_chain_dfs[sc_0]
  df_chain_1 = dict_chain_dfs[sc_1]
  for row_i, row in df_cp.iterrows():
    id_lsa_0, id_lsa_1 = row[['id_lsa_A', 'id_lsa_B']].values
    if (id_lsa_0 in ls_keep_stores) and (id_lsa_1 in ls_keep_stores):
      df_price_0 = df_chain_0[df_chain_0['id_lsa'] == id_lsa_0][ls_prod_cols + ['price']]
      df_price_1 = df_chain_1[df_chain_1['id_lsa'] == id_lsa_1][ls_prod_cols + ['price']]
      df_duel = pd.merge(df_price_0,
                         df_price_1,
                         how = 'inner',
                         on = ls_prod_cols,
                         suffixes = ['_1', '_2'])
      # Intersection can be null...
      if len(df_duel) != 0:
        
        # Comparison on nb products cheaper / more expensive
        nb_1_win = len(df_duel[df_duel['price_1'] < df_duel['price_2']])
        nb_2_win = len(df_duel[df_duel['price_1'] > df_duel['price_2']])
        nb_draws = len(df_duel[df_duel['price_1'] == df_duel['price_2']])
        if nb_1_win > nb_2_win:
          nb_winner = 'store_1' # row['store_id_1']
          nb_won, nb_lost = nb_1_win, nb_2_win
        elif nb_2_win > nb_1_win:
          nb_winner = 'store_2' # row['store_id_2']
          nb_won, nb_lost = nb_2_win, nb_1_win
        else:
          nb_winner = 'draw'
          nb_won, nb_lost = nb_1_win, nb_2_win
  
        # Comparison on total sum (basket with all goods)
        price_1 = df_duel['price_1'].sum()
        price_2 = df_duel['price_2'].sum()
        compa_pct_o = (price_2 / price_1 - 1) * 100
        if price_2 - price_1 > 10e-4:
          compa_pct = (price_2 / price_1 - 1) * 100
          compa_mean = (price_2 - price_1) / len(df_duel)
          compa_winner = 'store_1' # row['store_id_1']
        elif price_1 - price_2 > 10e-4:
          compa_pct = (price_1 / price_2 - 1) * 100
          compa_mean = (price_1 - price_2) / len(df_duel)
          compa_winner = 'store_2' # row['store_id_2']
        else:
          compa_pct = 0.0
          compa_mean = 0
          compa_winner = 'draw'
        ls_rows_compa.append((row['id_lsa_A'],
                              row['id_lsa_B'],
                              row['store_id_A'],
                              row['store_id_B'],
                              row['store_chain_A'],
                              row['store_chain_B'],
                              row['dist'],
                              len(df_duel),
                              nb_1_win,
                              nb_2_win,
                              nb_winner,
                              nb_won,
                              nb_lost,
                              nb_draws,
                              compa_pct_o,
                              compa_pct,
                              compa_mean,
                              compa_winner))

df_repro_compa = pd.DataFrame(ls_rows_compa,
                              columns = ['id_lsa_A',
                                         'id_lsa_B',
                                         'store_id_A',
                                         'store_id_B',
                                         'store_chain_A',
                                         'store_chain_B',
                                         'dist',
                                         'nb_obs',
                                         'nb_win_A',
                                         'nb_win_B',
                                         'nb_winner',
                                         'nb_won',
                                         'nb_lost',
                                         'nb_draws',
                                         'compa_pct_o',
                                         'compa_pct',
                                         'compa_mean',
                                         'compa_winner'])

# Convert product counts to percentages
for var in ['win_A', 'win_B', 'draws', 'lost', 'won']:
  df_repro_compa['pct_{:s}'.format(var)] =\
      df_repro_compa['nb_{:s}'.format(var)] * 100 / df_repro_compa['nb_obs'].astype(float)
df_repro_compa.drop(['nb_draws', 'nb_lost', 'nb_won'],
                    axis = 1,
                    inplace = True)

for tup_chain in ls_tup_chains:
  df_tc_compa = df_repro_compa[(df_repro_compa['store_chain_A'] == tup_chain[0]) &\
                               (df_repro_compa['store_chain_B'] == tup_chain[1]) &\
                               (df_repro_compa['dist'] <= 15) &\
                               (df_repro_compa['nb_obs'] >= 100)]
  print()
  print(tup_chain)
  print(df_tc_compa.describe().to_string())
  print('Pct pairs won by A: {:.2f}'.format(\
        len(df_tc_compa[df_tc_compa['compa_pct_o'] > 0]) /\
            float(len(df_tc_compa)) * 100))
  print('Pct pairs draw: {:.2f}'.format(\
        len(df_tc_compa[df_tc_compa['compa_pct_o'] == 0]) /\
            float(len(df_tc_compa)) * 100))

# ###################
# REG RR ON DISTANCE
# ###################

# see if relation between rank reversals and distance
# control by tup chain (concat)
# create distance dummy?
# create closest competitor dummy? (how? take chain into account?)
