#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

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
path_built_lsa_csv = os.path.join(path_built_lsa, 'data_csv')
path_built_lsa_json = os.path.join(path_built_lsa, 'data_json')
path_built_lsa_comp_csv = os.path.join(path_built_lsa_csv,
                                       '201407_competition')
path_built_lsa_comp_json = os.path.join(path_built_lsa_json,
                                        '201407_competition')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ############
# LOAD DATA
# ############

# LOAD DF PRICES
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                        encoding = 'utf-8')


# LOAD DF STORES (INCLUDING LSA INFO)
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores.csv'),
                        dtype = {'c_insee' : str,
                                 'id_lsa' : str},
                        encoding = 'utf-8')

# Fix Store_Chain for prelim stats des
ls_sc_drop = ['CARREFOUR CITY',
              'CARREFOUR CONTACT',
              'CARREFOUR PLANET',
              'GEANT DISCOUNT',
              'HYPER CHAMPION',
              'INTERMARCHE HYPER',
              'LECLERC EXPRESS',
              'MARCHE U',
              'U EXPRESS']

df_qlmc = df_qlmc[~df_qlmc['store_chain'].isin(ls_sc_drop)]
df_stores = df_stores[~df_stores['store_chain'].isin(ls_sc_drop)]

ls_sc_replace = [('CENTRE E. LECLERC', 'LECLERC'),
                 ('CENTRE LECLERC', 'LECLERC'),
                 ('E. LECLERC', 'LECLERC'),
                 ('E.LECLERC', 'LECLERC'),
                 ('SYSTEME U', 'SUPER U'),
                 ('GEANT', 'GEANT CASINO'),
                 ('CHAMPION', 'CARREFOUR MARKET'),
                 ('INTERMARCHE SUPER', 'INTERMARCHE'),
                 ('HYPER U', 'SUPER U')]

for sc_old, sc_new in ls_sc_replace:
  df_qlmc.loc[df_qlmc['store_chain'] == sc_old,
              'store_chain'] = sc_new
  df_stores.loc[df_stores['store_chain'] == sc_old,
              'store_chain'] = sc_new

# USE df_prices (forward consistency...switch to load directly df_prices?)
df_prices = df_qlmc

# LOAD DICT CLOSE
dict_close = dec_json(os.path.join(path_built_lsa_comp_json,
                                   'dict_ls_close_hsx.json'))

# Restrict df_stores to stores present in df_prices
ls_keep_store_ids = list(df_prices['store'].unique())
df_stores = df_stores[df_stores['store'].isin(ls_keep_store_ids)]

# Also need to drop duplicates (temp... to fix ASAP)
# df_dup = df_stores[(df_stores.duplicated(['id_lsa'], take_last = False)) |\
#                    (df_stores.duplicated(['id_lsa'], take_last = True))]
df_stores = df_stores[~((df_stores.duplicated(['id_lsa'], take_last = False)) |\
                        (df_stores.duplicated(['id_lsa'], take_last = True)))]

# LOAD LSA STORE DATA
df_lsa = pd.read_csv(os.path.join(path_built_lsa_csv,
                                  'df_lsa_active_hsx.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

df_lsa.set_index('id_lsa', inplace = True)

# ########################
# CLOSEST SAME CHAIN PAIRS
# ########################

ls_df_close_pairs = []

for per in range(13):
  df_stores_per = df_stores[df_stores['period'] == per]

  dict_chain_ids = {}
  for row_i, row in df_stores_per[~df_stores_per['id_lsa'].isnull()].iterrows():
    dict_chain_ids.setdefault(row['store_chain'], []).append(row['id_lsa'])
  
  # A bit costly to check if closest same group (see later?)
  # dict_close contains only stores within 25 km
  # this distance may not allow to cover many stores: change method?
  dict_chain_pairs = {}
  for chain, ls_chain_ids in dict_chain_ids.items():
    # save id pairs to restrict to unique id pairs
    ls_chain_pairs_bu = []
    for id_lsa in ls_chain_ids:
      # only active id_lsa kept but discontinued may be here?
      ls_close = dict_close.get(id_lsa, [])
      for close in ls_close:
        if (close[0] in ls_chain_ids) and\
           ((close[0], id_lsa) not in ls_chain_pairs_bu):
            dict_chain_pairs.setdefault(chain, [])\
                            .append((id_lsa, close[0], close[1]))
            ls_chain_pairs_bu.append((id_lsa, close[0]))
            break
  ls_rows_close_qlmc = [(chain,) + chain_pair\
                          for chain, ls_chain_pairs in dict_chain_pairs.items()\
                              for chain_pair in ls_chain_pairs]
  df_close_pairs = pd.DataFrame(ls_rows_close_qlmc,
                                columns = ['store_chain',
                                           'id_lsa_1',
                                           'id_lsa_2',
                                           'dist'])
  df_close_pairs['period'] = per
  ls_df_close_pairs.append(df_close_pairs)

df_close_pairs = pd.concat(ls_df_close_pairs)

df_stores.set_index('id_lsa', inplace = True)
for i in [1, 2]:
  df_close_pairs['store_{:d}'.format(i)] =\
    df_close_pairs.apply(\
      lambda row: df_stores.ix[row['id_lsa_{:d}'.format(i)]]['store'],
      axis = 1)

# #####################
# COMPARE PRICES
# #####################

dict_chain_dfs = {chain: df_prices[df_prices['store_chain'] == chain]\
                    for chain in df_prices['store_chain'].unique()}

ls_rows_compa = []
for row_i, row in df_close_pairs.iterrows():
  df_chain = dict_chain_dfs[row['store_chain']]
  df_store_1  = df_chain[(df_chain['period'] == row['period']) &\
                         (df_chain['store'] == row['store_1'])]
  df_store_2  = df_chain[(df_chain['period'] == row['period']) &\
                         (df_chain['store'] == row['store_2'])]
  df_duel = pd.merge(df_store_1,
                     df_store_2,
                     how = 'inner',
                     on = ['section', 'family', 'product'],
                     suffixes = ['_1', '_2'])
  # Fails if one empty product intersection (not expected to happen given data)
  
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
  ls_rows_compa.append((row['period'],
                        row['store_1'],
                        row['id_lsa_1'],
                        row['store_2'],
                        row['id_lsa_2'],
                        row['store_chain'],
                        row['dist'],
                        len(df_duel),
                        nb_winner,
                        nb_won,
                        nb_lost,
                        nb_draws,
                        compa_pct,
                        compa_mean,
                        compa_winner))

df_repro_compa = pd.DataFrame(ls_rows_compa,
                              columns = ['period',
                                         'store_id_1',
                                         'id_lsa_1',
                                         'store_id_2',
                                         'id_lsa_2',
                                         'store_chain',
                                         'dist',
                                         'nb_obs',
                                         'nb_winner',
                                         'nb_won',
                                         'nb_lost',
                                         'nb_draws',
                                         'compa_pct',
                                         'compa_mean',
                                         'compa_winner'])

# Convert product counts to percentages
for var in ['draws', 'lost', 'won']:
  df_repro_compa['pct_{:s}'.format(var)] =\
      df_repro_compa['nb_{:s}'.format(var)] * 100 / df_repro_compa['nb_obs'].astype(float)
df_repro_compa.drop(['nb_draws', 'nb_lost', 'nb_won'],
                    axis = 1,
                    inplace = True)

df_repro_compa = df_repro_compa[df_repro_compa['nb_obs'] >= 200]

ls_chains = ['INTERMARCHE', 'LECLERC', 'SUPER U',
             'CARREFOUR MARKET', 'CARREFOUR',
             'AUCHAN', 'CASINO', 'SIMPLY MARKET',
             'CORA', 'GEANT CASINO']

ls_stats = ['mean', '50%']
dict_ls_se_stat = {}
for chain in ls_chains:
  print()
  print(chain)
  print(df_repro_compa[df_repro_compa['store_chain'] == chain].describe().to_string())
  for stat in ls_stats:
    se_stat = df_repro_compa[df_repro_compa['store_chain'] == chain].describe().ix[stat]
    se_stat.ix['count'] = df_repro_compa[df_repro_compa['store_chain'] ==\
                                           chain].describe().ix['count'].iloc[0]
    dict_ls_se_stat.setdefault(stat, []).append(se_stat)

dict_df_stat = {}
for stat, ls_se_stat in dict_ls_se_stat.items():
  df_stat = pd.concat(ls_se_stat,
                      axis = 1,
                      keys = ls_chains)
  df_stat = df_stat.T
  df_stat_o = df_stat[['count', 'compa_pct', 'pct_draws', 'pct_lost', 'pct_won']].copy()
  df_stat_o.sort('pct_draws', ascending = False, inplace = True)
  dict_df_stat[stat] = df_stat_o

print()
print(dict_df_stat['mean'].to_string())

# print(df_repro_compa[df_repro_compa['compa_pct'] >= 20][0:10].to_string())
# len(df_repro_compa[df_repro_compa['winner_compa'] != df_repro_compa['nb_winner']])

# ####################
# CENTRAL PROCUREMENT
# ####################

# Check with Leclerc and LSA data: centrale d'achat?
df_repro = df_repro_compa.copy()
df_repro['cp_1'] = df_repro['id_lsa_1'].apply(lambda x: df_lsa.ix[x]['etb_affiliation'])
df_repro['cp_2'] = df_repro['id_lsa_2'].apply(lambda x: df_lsa.ix[x]['etb_affiliation'])

df_lec_sub = df_repro[(df_repro['store_chain'] == 'LECLERC')]
print()
print(df_lec_sub[df_lec_sub['cp_1'] == df_lec_sub['cp_2']].describe().to_string())
