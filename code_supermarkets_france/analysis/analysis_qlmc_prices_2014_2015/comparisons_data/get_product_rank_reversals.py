#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import timeit
from functions_generic_qlmc import *
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.iolib.summary2 import summary_col
import matplotlib.pyplot as plt

pd.set_option('float_format', '{:,.0f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built = os.path.join(path_data, 'data_supermarkets', 'data_built')
path_built_csv = os.path.join(path_built, 'data_qlmc_2014_2015', 'data_csv')
path_built_lsa_csv = os.path.join(path_built, 'data_lsa', 'data_csv')
path_built_lsa_comp_csv = os.path.join(path_built_lsa_csv, '201407_competition')

pd.set_option('float_format', '{:,.2f}'.format)

# #############
# LOAD DATA
# #############

df_prices = pd.read_csv(os.path.join(path_built_csv, 'df_prices_201503.csv'),
                        encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv, 'df_stores_final_201503.csv'),
                        dtype = {'id_lsa' : str,
                                 'c_insee' : str},
                        encoding = 'utf-8')

df_comp_pairs = pd.read_csv(os.path.join(path_built_csv,
                                         'df_comp_pairs_2014_2015.csv'),
                            dtype = {'id_lsa_0' : str,
                                     'id_lsa_1' : str},
                            encoding = 'utf-8')

# add id_lsa only (to be used later)
df_qlmc = pd.merge(df_prices,
                   df_stores[['store_id', 'id_lsa']],
                   on = 'store_id',
                   how = 'left')

df_comp_pairs = pd.read_csv(os.path.join(path_built_csv,
                                         'df_comp_pairs_2014_2015.csv'),
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
                 ('LECLERC', 'AUCHAN'),
                 ('GEANT CASINO', 'CARREFOUR'),
                 ('CARREFOUR', 'AUCHAN'),
                 ('CARREFOUR', 'INTERMARCHE'),
                 ('CARREFOUR', 'SUPER U'),
                 ('AUCHAN', 'INTERMARCHE'),
                 ('AUCHAN', 'SUPER U'),
                 ('INTERMARCHE', 'SUPER U')]
  
ls_copy_cols = ['id_lsa', 'store_name',
                'store_chain', 'enseigne_alt', 'groupe']

ls_df_cp = []
for tup_chains in ls_tup_chains:
  df_cp = (df_pairs[(df_pairs['store_chain_0'].isin(tup_chains)) &
                    (df_pairs['store_chain_1'].isin(tup_chains))].copy())
  tup_sufs = ['A', 'B']
  for brand, suf in zip(tup_chains, tup_sufs):
    for col in ls_copy_cols:
      df_cp[u'{:s}_{:s}'.format(col, suf)] = 0
      df_cp.loc[df_cp['store_chain_0'] == brand,
                     u'{:s}_{:s}'.format(col, suf)] = df_cp[u'{:s}_0'.format(col)]
      df_cp.loc[df_cp['store_chain_1'] == brand,
                u'{:s}_{:s}'.format(col, suf)] = df_cp[u'{:s}_1'.format(col)]
  ls_drop_cols = ([u'{:s}_0'.format(x) for x in ls_copy_cols] +
                  [u'{:s}_1'.format(x) for x in ls_copy_cols])
  df_cp.drop(ls_drop_cols, axis = 1, inplace = True)
  ls_df_cp.append(df_cp)

df_cp_all = pd.concat(ls_df_cp)

# ##############################
# COMPARE TUP CHAIN STORE PAIRS
# ##############################

# Costly to search by store_id within df_prices
# hence first split df_prices in chain dataframes
dict_chain_dfs = ({store_chain: df_qlmc[df_qlmc['store_chain'] == store_chain]
                     for store_chain in df_qlmc['store_chain'].unique()})

# subset to make lighter
ls_tup_chains = ls_tup_chains[0:3]

ls_ct, ls_rr, ls_eq = [], [], []
for sc_0, sc_1 in ls_tup_chains:
  df_cp = (df_cp_all[(df_cp_all['store_chain_A'] == sc_0) &
                     (df_cp_all['store_chain_B'] == sc_1)])
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
        df_1_win = df_duel[df_duel['price_1'] < df_duel['price_2']]
        df_2_win = df_duel[df_duel['price_1'] > df_duel['price_2']]
        df_draw = df_duel[df_duel['price_1'] == df_duel['price_2']]
        
        # if draw: consider no information (even for draws...)
        if len(df_1_win) != len(df_2_win):
          ls_ct += df_duel['product'].values.tolist()
          ls_eq += df_draw['product'].values.tolist()
          if len(df_1_win) > len(df_2_win):
            ls_rr += df_2_win['product'].values.tolist()
          else:
            ls_rr += df_1_win['product'].values.tolist()

se_ct = pd.Series(ls_ct).value_counts()
se_eq = pd.Series(ls_eq).value_counts()
se_rr = pd.Series(ls_rr).value_counts()

df = pd.concat([se_ct, se_eq, se_rr], axis = 1, keys = ['tot', 'eq', 'rr'])
df = df.fillna(0)

df['pct_rr'] = df['rr'] / df['tot'] * 100
df['pct_eq'] = df['eq'] / df['tot'] * 100
df['pct_rr_or_eq'] = df['pct_rr'] + df['pct_eq']

ls_top_products = [u'COCA COLA COCA-COLA PET 1.5L',
                   u'COCA COLA COCA-COLA PET 2L',
                   u'CRISTALINE EAU CRISTALINE BOUTEILLE 1.5 LITRE X6',
                   u'CRISTALINE EAU CRISTALINE BOUTEILLE 1.5 LITRE',
                   #u'VITTEL EAU MINÉRALE GRANDE SOURCE VITTEL 6X 1L', # too few6*1.5L..
                   #u'VOLVIC EAU VOLVIC PET 6X0.5L', # tto few 6*1.5L...
                   u'PRESIDENT BEURRE DOUX PRÉSIDENT GASTRONOMIQUE PLAQUETTE 82%MG 250G',
                   u'RICARD RICARD 45° 1 LITRE',
                   u'HEINEKEN BIÈRE HEINEKEN 5D PACK 20X25CL',
                   u'WILLIAM PEEL WHISKY WILLIAM PEEL OLD 40 DEGRÉS 70CL',
                   u'WILLIAM PEEL WHISKY WILLIAM PEEL OLD 40 DÉGRÉS 1 LITRE',
                   u'NUTELLA PÂTE À TARTINER NUTELLA POT 1KG']

print()
print('Stats des by product')
print(df[df['tot'] >= 100].describe().to_string())

print()
print('Stats des top sales')
print(df[df.index.isin(ls_top_products)].to_string())

print()
print('Stats des top sales')
print(df[df.index.isin(ls_top_products)].describe().to_string())

# Inspect prods with highet rr / eq
for col in ['pct_rr', 'pct_eq']:
  df.sort_values(col, ascending = False, inplace = True)
  print()
  print('Top 10 products in terms of {:s}'.format(col))
  print(df[df['tot'] >= 100][0:10].to_string())
