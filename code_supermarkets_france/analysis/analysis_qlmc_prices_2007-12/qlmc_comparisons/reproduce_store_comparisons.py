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

df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      encoding = 'utf-8')

# harmonize store chains according to qlmc
df_qlmc['store_chain_alt'] = df_qlmc['store_chain']
ls_sc_replace = [('CENTRE E. LECLERC', 'LECLERC'),
                 ('CENTRE LECLERC', 'LECLERC'),
                 ('E. LECLERC', 'LECLERC'),
                 ('E.LECLERC', 'LECLERC'),
                 ('LECLERC EXPRESS', 'LECLERC'),
                 ('INTERMARCHE HYPER', 'INTERMARCHE'),
                 ('INTERMARCHE SUPER', 'INTERMARCHE'),
                 ('SUPER U', 'SYSTEME U'),
                 ('HYPER U', 'SYSTEME U'),
                 ('U EXPRESS', 'SYSTEME U'),
                 ('MARCHE U', 'SYSTEME U'),
                 ('CARREFOUR PLANET', 'CARREFOUR'),
                 ('GEANT CASINO', 'GEANT'),
                 ('GEANT DISCOUNT', 'GEANT'),
                 ('CARREFOUR MARKET', 'CHAMPION'),
                 ('HYPER CHAMPION', 'CHAMPION'),
                 ('CARREFOUR CITY', 'CHAMPION'),
                 ('CARREFOUR CONTACT', 'CHAMPION')]
for sc_old, sc_new in ls_sc_replace:
  df_qlmc.loc[df_qlmc['store_chain'] == sc_old,
              'store_chain_alt'] = sc_new

# harmonize store chains in comp pairs too
df_comp_pairs = pd.read_csv(os.path.join(path_built_csv,
                                         'df_comp_store_pairs.csv'),
                                  encoding = 'utf-8')

df_comp_pairs['store_chain_0_alt'] = df_comp_pairs['store_chain_0']
df_comp_pairs['store_chain_1_alt'] = df_comp_pairs['store_chain_1']
for sc_old, sc_new in ls_sc_replace:
  df_comp_pairs.loc[df_comp_pairs['store_chain_0'] == sc_old,
                    'store_chain_0_alt'] = sc_new
  df_comp_pairs.loc[df_comp_pairs['store_chain_1'] == sc_old,
                    'store_chain_1_alt'] = sc_new
  
# ###################################
# LOOP: COMPARISON WITHIN EACH PERIOD
# ###################################

## Adhoc fixes
#df_stores.loc[df_stores['store'] == u'LECLERC LA FERTE BERNARD',
#              'Enseigne_Alt'] = u'CENTRE E.LECLERC'
##df_stores.loc[df_stores['Store'] == u'INTERMARCHE MORIERES LES AVIGNON',
##              'Enseigne_Alt'] = u'INTERMARCHE'
##df_stores.loc[df_stores['Store'] == u'SYSTEME U VERMELLES',
##              'Enseigne_Alt'] = u'SUPER U'
## pbm: would need to fix df_comp_pairs too
ls_temp_exclude = [u'INTERMARCHE MORIERES LES AVIGNON',
                   u'SYSTEME U VERMELLES']

ls_df_repro_compa = []
for i in range(0, 9):

  # Restrict to period
  print ''
  print 'Period {:d}'.format(i)
  df_qlmc_per = df_qlmc[df_qlmc['period'] == i]
  # Costly to search by store_id within df_prices
  # hence first split df_prices in chain dataframes
  dict_chain_dfs = {chain: df_qlmc_per[df_qlmc_per['store_chain_alt'] == chain]\
                      for chain in df_qlmc_per['store_chain_alt'].unique()}
  
  # COMPETITOR PAIRS
  df_comp_pairs_per = df_comp_pairs[df_comp_pairs['period'] == i]
  
  # LOOP ON PAIRS
  start = timeit.default_timer()
  ls_rows_compa = []
  lec_chain = 'LECLERC'
  lec_id_save = None
  for row_i, row in df_comp_pairs_per.iterrows():
    if row['store_chain_0_alt'] == 'LECLERC':
      lec_id, comp_id = row['store_0'], row['store_1']
      comp_chain = row['store_chain_1_alt']
    elif row['store_chain_1_alt'] == 'LECLERC':
      lec_id, comp_id = row['store_1'], row['store_0']
      comp_chain, comp_groupe = row['store_chain_0_alt'], row['groupe_0']
    else:
      comp_chain = None
    # only if leclerc pair
    if comp_chain and (lec_id not in ls_temp_exclude):
      # taking advantage of order requires caution on first loop
      if lec_id != lec_id_save:
        df_lec  = dict_chain_dfs[lec_chain]\
                      [dict_chain_dfs[lec_chain]['store'] == lec_id]
        lec_id_save = df_lec['store'].iloc[0]
      df_comp = dict_chain_dfs[comp_chain]\
                    [dict_chain_dfs[comp_chain]['store'] == comp_id]
      
      # todo: see if need family and subfamily for matching (not much chge)
      df_duel = pd.merge(df_lec,
                         df_comp,
                         how = 'inner',
                         on = ['section', 'family', 'product'],
                         suffixes = ['_lec', '_comp'])
      if not df_duel.empty:
        ls_rows_compa.append((i,
                              lec_id,
                              comp_id,
                              row['dist'],
                              comp_chain,
                              comp_groupe,
                              len(df_duel),
                              len(df_duel[df_duel['price_lec'] < df_duel['price_comp']]),
                              len(df_duel[df_duel['price_lec'] > df_duel['price_comp']]),
                              len(df_duel[df_duel['price_lec'] == df_duel['price_comp']]),
                              (df_duel['price_comp'].sum() /\
                                 df_duel['price_lec'].sum() - 1) * 100,
                              df_duel['price_comp'].mean() - df_duel['price_lec'].mean()))
        lec_id_save = None
  
  df_repro_compa = pd.DataFrame(ls_rows_compa,
                                columns = ['period',
                                           'lec_id',
                                           'comp_id',
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

print df_compa_all_periods[0:10].to_string()

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
