#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
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

path_built_json = os.path.join(path_built,
                               'data_json')

df_comp_pairs = pd.read_csv(os.path.join(path_built_csv,
                                         'df_comp_store_pairs.csv'),
                            encoding = 'utf-8')

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

# ###############
# COMPARE PAIRS
# ###############

ls_df_repro_compa = []
ls_ls_prod_draws = []
for period in range(0, 13):
  df_comp_pairs_per = df_comp_pairs[df_comp_pairs['period'] == period]
  df_prices_per = df_prices[df_prices['period'] == period]
  ls_rows_compa = []
  ls_prod_draws = []
  store_0_save = None
  for row_i, row in df_comp_pairs_per.iterrows():
    store_0 = row['store_0']
    store_1 = row['store_1']
    dist = row ['dist']
    same_municipality = 0
    if row['store_municipality_0'] == row['store_municipality_1']:
      same_municipality = 1
    # taking advantage of order requires caution on first loop
    if store_0 != store_0_save:
      df_prices_0 = df_prices_per[df_prices_per['store'] == store_0]
      store_0_save = df_prices_per['store'].iloc[0]
    df_prices_1 = df_prices_per[df_prices_per['store'] == store_1]
    
    # todo: see if need family and subfamily for matching (not much chge)
    df_duel = pd.merge(df_prices_0,
                       df_prices_1,
                       how = 'inner',
                       on = ['section', 'family', 'product'],
                       suffixes = ['_0', '_1'])
    mean_diff = (df_duel['price_0'] - df_duel['price_1']).mean()
    # mean saving
    if len(df_duel[df_duel['price_0'] < df_duel['price_1']]) >\
         len(df_duel[df_duel['price_0'] > df_duel['price_1']]):
       df_rr = df_duel[df_duel['price_1'] < df_duel['price_0']]
       mean_rr_saving = (df_rr['price_0'] - df_rr['price_1']).mean()
    else:
       df_rr = df_duel[df_duel['price_0'] < df_duel['price_1']]
       mean_rr_saving = (df_rr['price_1'] - df_rr['price_0']).mean()
    # df_duel['price_0_ctld'] = df_duel['price_0'] - mean_diff
    ls_rows_compa.append((period,
                          store_0,
                          store_1,
                          dist,
                          same_municipality,
                          len(df_duel),
                          len(df_duel[df_duel['price_0'] < df_duel['price_1']]),
                          len(df_duel[df_duel['price_0'] > df_duel['price_1']]),
                          len(df_duel[df_duel['price_0'] == df_duel['price_1']]),
                          df_duel[['price_0', 'price_1']].sum().argmin(),
                          np.abs((df_duel[['price_0', 'price_1']].sum().min() /\
                                    df_duel[['price_0', 'price_1']].sum().max()-1)*100),
                          mean_diff,
                          (df_duel['price_0'] - df_duel['price_1']).abs().mean(),
                          mean_rr_saving))

    # Save product names when equal prices
    ls_prod_draws += list(df_duel[df_duel['price_0'] ==\
                            df_duel['price_1']]['product'].values)
  
  # Pbm: pct compa does not make sense: todo do always cheapest / most expensive
  df_repro_compa = pd.DataFrame(ls_rows_compa,
                                columns = ['period',
                                           'store_0',
                                           'store_1',
                                           'dist',
                                           'same_municipality',
                                           'nb_obs',
                                           'nb_0_wins',
                                           'nb_1_wins',
                                           'nb_draws',
                                           'winner_value',
                                           'winner_value_pct',
                                           'mean_diff',
                                           'mean_abs_gfs',
                                           'mean_rr_saving'])
  ls_df_repro_compa.append(df_repro_compa)
  ls_ls_prod_draws.append(ls_prod_draws)

# #############
# OUTPUT
# #############

df_compa_all_periods = pd.concat(ls_df_repro_compa,
                                 axis = 0,
                                 ignore_index = True)

df_compa_all_periods['rank_rev'] = df_compa_all_periods['nb_1_wins'] /\
                               df_compa_all_periods['nb_obs'] * 100

df_compa_all_periods.loc[df_compa_all_periods['nb_1_wins'] >\
                     df_compa_all_periods['nb_0_wins'],
                   'rank_rev'] = df_compa_all_periods['nb_0_wins'] /\
                                   df_compa_all_periods['nb_obs'] * 100

df_compa_all_periods.loc[df_compa_all_periods['nb_obs'] == 0,
                         'rank_rev'] = np.nan

#df_compa_all_periods.to_csv(os.path.join(path_built_csv,
#                                         'df_compa_all_periods.csv'),
#                            encoding = 'utf-8')
#
#enc_json(ls_ls_prod_draws, os.path.join(path_built_json,
#                                        'ls_ls_prod_draws.json'))

# #############
# STATS DES
# #############

pd.set_option('float_format', '{:,.3f}'.format)

ls_pctiles = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]

print()
print(u'Overview of winner value pct:')
print(df_repro_compa['winner_value_pct'].describe(percentiles = ls_pctiles))

df_repro_compa['rank_rev'] = df_repro_compa['nb_1_wins'] /\
                               df_repro_compa['nb_obs'] * 100

df_repro_compa.loc[df_repro_compa['nb_1_wins'] >\
                     df_repro_compa['nb_0_wins'],
                   'rank_rev'] = df_repro_compa['nb_0_wins'] /\
                                   df_repro_compa['nb_obs'] * 100

print()
print(u'General overview')
print(df_repro_compa.describe().to_string())

import matplotlib.pyplot as plt
df_repro_compa.plot(kind = 'scatter',
                    x = 'winner_value_pct',
                    y = 'rank_rev')
plt.show()

# Check if some products are prone to draws? how to do efficiently?
# More dispersion among pairs further away (try discrete)

# Todo: add from LSA: Enseigne_Alt and Group to have correct df_comp and df_same

print(smf.ols('rank_rev ~ winner_value_pct + dist',
        data = df_repro_compa).fit().summary())

df_repro_compa['close'] = 0
df_repro_compa.loc[df_repro_compa['dist'] <= 5, 'close'] = 1

print(df_repro_compa[['close', 'same_municipality']].describe())

print(smf.ols('rank_rev ~ winner_value_pct + close',
        data = df_repro_compa).fit().summary())

print(smf.ols('rank_rev ~ winner_value_pct + same_municipality',
        data = df_repro_compa).fit().summary())

# Product draw
se_prod_draws_vc = pd.Series(ls_prod_draws).value_counts()
print(u'Top 20 products in terms of draws:')
print(se_prod_draws_vc[0:20])
