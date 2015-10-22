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

# ##############
# LOAD DATA
# ##############

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')


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

df_stores = pd.merge(df_lsa[['Ident', 'Enseigne_Alt', 'Groupe', 'Surface']],
                     df_stores,
                     left_on = 'Ident',
                     right_on = 'id_lsa',
                     how = 'right')

# ###################################
# LOOP: COMPARISON WITHIN EACH PERIOD
# ###################################

# Adhoc fixes
df_stores.loc[df_stores['Store'] == u'LECLERC LA FERTE BERNARD',
              'Enseigne_Alt'] = u'CENTRE E.LECLERC'
#df_stores.loc[df_stores['Store'] == u'INTERMARCHE MORIERES LES AVIGNON',
#              'Enseigne_Alt'] = u'INTERMARCHE'
#df_stores.loc[df_stores['Store'] == u'SYSTEME U VERMELLES',
#              'Enseigne_Alt'] = u'SUPER U'
## pbm: would need to fix df_comp_pairs too
ls_temp_exclude = [u'INTERMARCHE MORIERES LES AVIGNON',
                   u'SYSTEME U VERMELLES']

ls_df_repro_compa = []
for per in range(9):

  # RESTRICT TO ONE PERIOD AND MERGE
  
  #per = 2
  df_prices_per = df_prices[df_prices['Period'] == per]
  df_stores_per = df_stores[df_stores['Period'] == per]
  
  df_prices_per = pd.merge(df_prices_per,
                           df_stores_per,
                           on = ['Store'],
                           how = 'right')
   
  df_stores_per.set_index('Store', inplace = True)

  # Costly to search by store_id within df_prices
  # hence first split df_prices in chain dataframes
  dict_chain_dfs = {chain: df_prices_per[df_prices_per['Enseigne_Alt'] == chain]\
                      for chain in df_prices_per['Enseigne_Alt'].unique()}
  
  # COMPETITOR PAIRS
  
  df_comp_pairs = pd.read_csv(os.path.join(path_built_csv,
                                           'df_comp_store_pairs.csv'),
                                    encoding = 'utf-8')
  
  df_comp_pairs_per = df_comp_pairs[df_comp_pairs['Period'] == per]
  
  # LOOP ON PAIRS

  start = timeit.default_timer()
  ls_rows_compa = []
  lec_chain = 'CENTRE E.LECLERC'
  lec_id_save = None
  for row_i, row in df_comp_pairs_per.iterrows():
    if row['Groupe_0'] == 'LECLERC':
      lec_id, comp_id = row['Store_0'], row['Store_1']
      comp_chain = row['Enseigne_Alt_1']
    elif row['Groupe_1'] == 'LECLERC':
      lec_id, comp_id = row['Store_1'], row['Store_0']
      comp_chain, comp_groupe = row['Enseigne_Alt_0'], row['Groupe_0']
    else:
      comp_chain = None
    # only if leclerc pair
    if comp_chain and (lec_id not in ls_temp_exclude):
      # taking advantage of order requires caution on first loop
      if lec_id != lec_id_save:
        df_lec  = dict_chain_dfs[lec_chain][dict_chain_dfs[lec_chain]['Store'] == lec_id]
        lec_id_save = df_lec['Store'].iloc[0]
      df_comp = dict_chain_dfs[comp_chain][dict_chain_dfs[comp_chain]['Store'] == comp_id]
      
      # todo: see if need family and subfamily for matching (not much chge)
      df_duel = pd.merge(df_lec,
                         df_comp,
                         how = 'inner',
                         on = ['Family', 'Subfamily', 'Product'],
                         suffixes = ['_lec', '_comp'])
      if not df_duel.empty:
        ls_rows_compa.append((per,
                              lec_id,
                              comp_id,
                              df_stores_per.ix[lec_id]['Surface'],
                              df_stores_per.ix[comp_id]['Surface'],
                              row['dist'],
                              comp_chain,
                              comp_groupe,
                              len(df_duel),
                              len(df_duel[df_duel['Price_lec'] < df_duel['Price_comp']]),
                              len(df_duel[df_duel['Price_lec'] > df_duel['Price_comp']]),
                              len(df_duel[df_duel['Price_lec'] == df_duel['Price_comp']]),
                              (df_duel['Price_comp'].sum() / df_duel['Price_lec'].sum() - 1) * 100,
                              df_duel['Price_comp'].mean() - df_duel['Price_lec'].mean()))
        lec_id_save = None
  
  df_repro_compa = pd.DataFrame(ls_rows_compa,
                                columns = ['period',
                                           'lec_id',
                                           'comp_id',
                                           'lec_surface',
                                           'comp_surface',
                                           'dist',
                                           'comp_enseigne_alt',
                                           'comp_groupe',
                                           'nb_obs',
                                           'nb_lec_wins',
                                           'nb_comp_wins',
                                           'nb_draws',
                                           'pct_compa',
                                           'mean_compa'])
  print u'Time for loop', timeit.default_timer() - start
  ls_df_repro_compa.append(df_repro_compa)

df_compa_all_periods = pd.concat(ls_df_repro_compa,
                                 axis = 0,
                                 ignore_index = True)

df_compa_all_periods['rr'] = df_compa_all_periods['nb_comp_wins'] /\
                               df_compa_all_periods['nb_obs'] * 100

df_compa_all_periods.loc[df_compa_all_periods['nb_comp_wins'] >\
                     df_compa_all_periods['nb_lec_wins'],
                   'rr'] = df_compa_all_periods['nb_lec_wins'] /\
                                   df_compa_all_periods['nb_obs'] * 100

df_compa_all_periods.loc[df_compa_all_periods['nb_obs'] == 0,
                         'rr'] = np.nan

## ##############
## STATS DES
## ##############
#
#ls_pctiles = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
#
#print u'\nDescribe pct_compa:'
#print df_repro_compa['pct_compa'].describe(percentiles = ls_pctiles)
#
#df_repro_compa['rr'] = df_repro_compa['nb_comp_wins'] /\
#                         df_repro_compa['nb_obs'] * 100
#
#df_repro_compa.loc[df_repro_compa['nb_comp_wins'] >\
#                     df_repro_compa['nb_lec_wins'],
#                   'rr'] = df_repro_compa['nb_lec_wins'] /\
#                             df_repro_compa['nb_obs'] * 100
#
#import matplotlib.pyplot as plt
#df_repro_compa.plot(kind = 'scatter', x = 'pct_compa', y = 'rr')
#plt.show()
#
## todo:
## add precision in price comparison: product family level rank reversals
## enrich compara dataframe: distance, brands, competition/environement vars
## try to account for dispersion
## also investigate link between dispersion and price levels?
## do same exercise with non leclerc pairs (control for differentiation)
## would be nice to check if products on which leclerc is beaten are underpriced vs market
