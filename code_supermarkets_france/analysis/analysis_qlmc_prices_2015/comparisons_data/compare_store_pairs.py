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

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015')

path_built_201503_csv = os.path.join(path_built_csv, 'data_csv_201503')
path_built_201415_csv = os.path.join(path_built_csv, 'data_csv_2014-2015')

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)

# #############
# LOAD DATA
# #############

df_prices = pd.read_csv(os.path.join(path_built_201503_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_201503_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str,
                                 'c_insee' : str},
                        encoding = 'utf-8')

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

df_store_markets = pd.read_csv(os.path.join(path_built_lsa_csv,
                                            '201407_competition',
                                            'df_store_market_chars.csv'),
                               dtype = {'id_lsa' : str},
                               encoding = 'utf-8')

ls_lsa_cols = ['type_alt', 'region', 'surface',
               'nb_caisses', 'nb_pompes', 'drive']

df_store_chars = pd.merge(df_lsa[['id_lsa'] + ls_lsa_cols],
                          df_store_markets,
                          on = 'id_lsa',
                          how = 'left')

df_stores = pd.merge(df_stores,
                     df_store_chars,
                     on = 'id_lsa',
                     how = 'left')

for col in ['surface',
            'hhi_1025km', 'ac_hhi_1025km',
            'UU_med_rev', 'AU_med_rev', 'CO_med_rev',
            'AU_pop', 'UU_pop', 'CO_pop',
            'pop_cont_10', 'pop_ac_10km', 'pop_ac_20km']:
  df_stores['ln_{:s}'.format(col)] = np.log(df_stores[col])

# avoid error msg on condition number (regressions)
df_stores['surface'] = df_stores['surface'].apply(lambda x: x/1000.0)
df_stores['AU_med_rev'] = df_stores['AU_med_rev'].apply(lambda x: x/1000.0)
df_stores['UU_med_rev'] = df_stores['UU_med_rev'].apply(lambda x: x/1000.0)
df_stores['hhi'] = df_stores['hhi_1025km'] 

# add id_lsa only (to be used later)
df_qlmc = pd.merge(df_prices,
                   df_stores[['store_id', 'id_lsa']],
                   on = 'store_id',
                   how = 'left')

df_comp_pairs = pd.read_csv(os.path.join(path_built_201415_csv,
                                         'df_comp_store_pairs_final.csv'),
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
  
ls_copy_cols = ['id_lsa', 'store_name',
                'store_chain', 'enseigne_alt', 'groupe']

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
                              row['store_name_A'],
                              row['store_name_B'],
                              row['store_chain_A'],
                              row['store_chain_B'],
                              row['dist'],
                              row['gg_dist_val'],
                              row['gg_dur_val'],
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
                                         'store_name_A',
                                         'store_name_B',
                                         'store_chain_A',
                                         'store_chain_B',
                                         'dist',
                                         'gg_dist',
                                         'gg_dur',
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

df_repro_compa['pct_rr'] = df_repro_compa['pct_win_A']
df_repro_compa.loc[df_repro_compa['pct_win_A'] > df_repro_compa['pct_win_B'],
                   'pct_rr'] = df_repro_compa['pct_win_B']

# ###################
# REG RR ON DISTANCE
# ###################

print()
print(df_repro_compa[['dist', 'gg_dist', 'gg_dur']].describe())

for dist in [5, 10, 12]:
  for dist_col in ['dist', 'gg_dist', 'gg_dur']:
    df_repro_compa['d_{:s}_{:d}'.format(dist_col, dist)] = np.nan
    df_repro_compa.loc[df_repro_compa[dist_col] <= dist,
                       'd_{:s}_{:d}'.format(dist_col, dist)] = 1
    df_repro_compa.loc[df_repro_compa[dist_col] > dist,
                       'd_{:s}_{:d}'.format(dist_col, dist)] = 0

df_compa = df_repro_compa[(df_repro_compa['compa_pct'].abs() <= 2)]

# ADD VARS FOR CONTROLS
ls_ev = ['hhi', 'ln_pop_cont_10', 'ln_CO_med_rev', 'region']
str_ev = " + ".join(ls_ev)
df_compa_ctrl = pd.merge(df_compa,
                         df_stores[['id_lsa'] + ls_ev],
                         left_on = 'id_lsa_A',
                         right_on = 'id_lsa',
                         how = 'left')

for d_dist in ['d_dist_5', 'd_gg_dur_12']:
  
  print()
  print(u'-'*30)
  print(u'Variable for close distance:', d_dist)
  
  # NO CONTROL
  print()
  print(smf.ols('pct_rr ~ {:s}'.format(d_dist),
                data = df_compa).fit().summary())
  
  ls_res = []
  ls_quantiles = [0.25, 0.5, 0.75] # use 0.7501 if issue
  for quantile in ls_quantiles:
    #print()
    #print(quantile)
    #print(smf.quantreg('pct_rr~d_dist_5', data = df_repro_compa).fit(quantile).summary())
    ls_res.append(smf.quantreg('pct_rr ~ {:s}'.format(d_dist),
                               data = df_compa[~df_compa[d_dist].isnull()]).fit(quantile))
  
  print(summary_col(ls_res,
                    stars=True,
                    float_format='%0.2f',
                    model_names=[u'Q{:2.0f}'.format(quantile*100) for quantile in ls_quantiles],
                    info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                               'R2':lambda x: "{:.2f}".format(x.rsquared)}))
  
  # WITH CONTROLS
  print()
  print(smf.ols('pct_rr ~ {:s}'.format(d_dist, str_ev),
                data = df_compa_ctrl).fit().summary())
  
  ls_res_ctrl =[smf.quantreg('pct_rr ~ {:s} + {:s}'.format(d_dist, str_ev),
                             data = df_compa_ctrl[~df_compa_ctrl[d_dist].isnull()]).fit(quantile)\
                  for quantile in ls_quantiles]
  
  print(summary_col(ls_res_ctrl,
                    stars=True,
                    float_format='%0.2f',
                    model_names=[u'Q{:2.0f}'.format(quantile*100) for quantile in ls_quantiles],
                    info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                               'R2':lambda x: "{:.2f}".format(x.rsquared)}))

# see if relation between rank reversals and distance
# control by tup chain (concat)
# create distance dummy?
# create closest competitor dummy? (how? take chain into account?)
