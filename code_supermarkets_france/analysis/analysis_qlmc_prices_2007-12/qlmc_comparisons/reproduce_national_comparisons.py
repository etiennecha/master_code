#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import timeit

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built = os.path.join(path_data,
                        'data_supermarkets',
                        'data_built',
                        'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_built_lsa = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa')

path_built_csv_lsa = os.path.join(path_built_lsa,
                                  'data_csv')

# ####################
# LOAD DATA
# ####################

# STORE DATA (NEED CHAIN)

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores.csv'),
                         encoding='utf-8')

df_lsa = pd.read_csv(os.path.join(path_built_csv_lsa,
                                  'df_lsa.csv'),
                     dtype = {u'C_INSEE' : str,
                              u'C_INSEE_Ardt' : str,
                              u'C_Postal' : str,
                              u'SIREN' : str,
                              u'NIC' : str,
                              u'SIRET' : str},
                     parse_dates = [u'Date_Ouv', u'Date_Fer', u'Date_Reouv',
                                    u'Date_Chg_Enseigne', u'Date_Chg_Surface'],
                     encoding = 'UTF-8')

df_stores = pd.merge(df_lsa[['Ident', 'Latitude', 'Longitude', 'Enseigne_Alt', 'Groupe']],
                     df_stores,
                     left_on = 'Ident',
                     right_on = 'id_lsa',
                     how = 'right')

# PRICE DATA

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

# RESTRICT TO ONE PERIOD AND MERGE

per = 2
df_prices_per = df_prices[df_prices['Period'] == per]
df_stores_per = df_stores[df_stores['Period'] == per]

df_prices_per = pd.merge(df_prices_per,
                         df_stores_per,
                         on = ['Store'],
                         how = 'right')

# #########################
# REPRODUCE QLMC COMPARISON
# #########################

# Average price by product / chain
ls_col_gb = ['Enseigne_Alt', 'Family', 'Subfamily', 'Product', 'Price']
df_chain_prod_prices = df_prices_per.groupby(ls_col_gb[:-1]).agg([len, np.mean])['Price']

# Compare two chains
ls_some_chains = ['INTERMARCHE SUPER',
                  'SUPER U',
                  'CARREFOUR MARKET',
                  'AUCHAN',
                  'HYPER U',
                  'CORA',
                  'CARREFOUR',
                  'GEANT CASINO']
ls_compare_chains = [['CENTRE E.LECLERC', chain] for chain in ls_some_chains]
for chain_a, chain_b in ls_compare_chains:
  # chain_a, chain_b = 'CENTRE E.LECLERC', 'CARREFOUR'
  df_chain_a = df_chain_prod_prices.loc[(chain_a),:]
  df_chain_b = df_chain_prod_prices.loc[(chain_b),:]
  # print df_test.loc[(slice(None), u'CENTRE E.LECLERC'),:].to_string()
  
  df_duel = pd.merge(df_chain_a,
                     df_chain_b,
                     left_index = True,
                     right_index = True,
                     how = 'inner',
                     suffixes = (u'_{:s}'.format(chain_a), u'_{:s}'.format(chain_b)))
  
  # Nb obs required varies by chain (figure below for october..)
  # Min 16 for CORA, Max 21 for Carrefour Market, Intermarche and Systeme U
  # Leclerc: 20, Auchan 19, Carrefour 19, Geant 18
  
  df_duel_sub = df_duel[(df_duel['len_{:s}'.format(chain_a)] >= 15) &\
                        (df_duel['len_{:s}'.format(chain_b)] >= 15)].copy()

  if df_duel_sub.empty:
    print u'\nNot enough obs for:', chain_a, chain_b
  else:
    df_duel_sub['diff'] = df_duel_sub['mean_{:s}'.format(chain_b)] -\
                            df_duel_sub['mean_{:s}'.format(chain_a)]
    
    df_duel_sub['pct_diff'] = (df_duel_sub['mean_{:s}'.format(chain_b)] /\
                                df_duel_sub['mean_{:s}'.format(chain_a)] - 1)*100

    print u'\nReplicate QLMC comparison: {:s} vs {:s}'.format(chain_a, chain_b)
    res = (df_duel_sub['mean_{:s}'.format(chain_b)].mean().round(2) /\
             df_duel_sub['mean_{:s}'.format(chain_a)].mean().round(2) - 1) * 100
    print u'{:.1f}'.format(res)
    percentiles = [0.1, 0.25, 0.5, 0.75, 0.9]
    print df_duel_sub[['diff', 'pct_diff']].describe(percentiles = percentiles)

    # Manipulate or assume consumer is somewhat informed
    df_duel_sub.sort('diff', ascending = False, inplace = True)
    df_duel_sub = df_duel_sub[len(df_duel_sub)/10:]
    res = (df_duel_sub['mean_{:s}'.format(chain_b)].mean().round(2) /\
             df_duel_sub['mean_{:s}'.format(chain_a)].mean().round(2) - 1) * 100
    print u'After manip against Leclerc: {:.1f}'.format(res)

##print df_duel[0:10].to_string()
