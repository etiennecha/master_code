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

#Period = 5
ls_df_repro_compa = []
ls_ls_prod_draws = []
for Period in range(9):
  df_comp_pairs_per = df_comp_pairs[df_comp_pairs['Period'] == Period]
  df_prices_per = df_prices[df_prices['Period'] == Period]
  ls_rows_compa = []
  ls_prod_draws = []
  store_0_save = None
  for row_i, row in df_comp_pairs_per.iterrows():
    store_0 = row['Store_0']
    store_1 = row['Store_1']
    dist = row ['dist']
    same_municipality = 0
    if row['Store_Municipality_0'] == row['Store_Municipality_1']:
      same_municipality = 1
    # taking advantage of order requires caution on first loop
    if store_0 != store_0_save:
      df_prices_0 = df_prices_per[df_prices_per['Store'] == store_0]
      store_0_save = df_prices_per['Store'].iloc[0]
    df_prices_1 = df_prices_per[df_prices_per['Store'] == store_1]
    
    # todo: see if need family and subfamily for matching (not much chge)
    df_duel = pd.merge(df_prices_0,
                       df_prices_1,
                       how = 'inner',
                       on = ['Family', 'Subfamily', 'Product'],
                       suffixes = ['_0', '_1'])
    mean_diff = (df_duel['Price_0'] - df_duel['Price_1']).mean()
    # df_duel['Price_0_ctld'] = df_duel['Price_0'] - mean_diff
    ls_rows_compa.append((Period,
                          store_0,
                          store_1,
                          dist,
                          same_municipality,
                          len(df_duel),
                          len(df_duel[df_duel['Price_0'] < df_duel['Price_1']]),
                          len(df_duel[df_duel['Price_0'] > df_duel['Price_1']]),
                          len(df_duel[df_duel['Price_0'] == df_duel['Price_1']]),
                          df_duel[['Price_0', 'Price_1']].sum().argmin(),
                          np.abs((df_duel[['Price_0', 'Price_1']].sum().min() /\
                                    df_duel[['Price_0', 'Price_1']].sum().max() - 1)* 100),
                          mean_diff,
                          (df_duel['Price_0'] - df_duel['Price_1']).abs().mean()))

    # Save product names when equal prices
    ls_prod_draws += list(df_duel[df_duel['Price_0'] == df_duel['Price_1']]['Product'].values)
  
  # Pbm: pct compa does not make sense: todo do always cheapest / most expensive
  df_repro_compa = pd.DataFrame(ls_rows_compa,
                                columns = ['Period',
                                           'Store_0',
                                           'Store_1',
                                           'Dist',
                                           'Same_municipality',
                                           'Nb_obs',
                                           'Nb_0_wins',
                                           'Nb_1_wins',
                                           'Nb_draws',
                                           'Winner_value',
                                           'Winner_value_pct',
                                           'Mean_diff',
                                           'Mean_gfs'])
  ls_df_repro_compa.append(df_repro_compa)
  ls_ls_prod_draws.append(ls_prod_draws)

# #############
# OUTPUT
# #############

df_compa_all_periods = pd.concat(ls_df_repro_compa,
                                 axis = 0,
                                 ignore_index = True)

df_compa_all_periods['Rank_rev'] = df_compa_all_periods['Nb_1_wins'] /\
                               df_compa_all_periods['Nb_obs'] * 100

df_compa_all_periods.loc[df_compa_all_periods['Nb_1_wins'] >\
                     df_compa_all_periods['Nb_0_wins'],
                   'Rank_rev'] = df_compa_all_periods['Nb_0_wins'] /\
                                   df_compa_all_periods['Nb_obs'] * 100

df_compa_all_periods.loc[df_compa_all_periods['Nb_obs'] == 0,
                         'Rank_rev'] = np.nan

df_compa_all_periods.to_csv(os.path.join(path_built_csv,
                                         'df_compa_all_periods.csv'),
                            encoding = 'utf-8')

enc_json(ls_ls_prod_draws, os.path.join(path_built_json,
                                        'ls_ls_prod_draws.json'))

# #############
# STATS DES
# #############

ls_pctiles = [0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95]
print df_repro_compa['Winner_value_pct'].describe(percentiles = ls_pctiles)

df_repro_compa['Rank_rev'] = df_repro_compa['Nb_1_wins'] /\
                               df_repro_compa['Nb_obs'] * 100

df_repro_compa.loc[df_repro_compa['Nb_1_wins'] >\
                     df_repro_compa['Nb_0_wins'],
                   'Rank_rev'] = df_repro_compa['Nb_0_wins'] /\
                                   df_repro_compa['Nb_obs'] * 100

print df_repro_compa['Rank_rev'].describe()

import matplotlib.pyplot as plt
df_repro_compa.plot(kind = 'scatter', x = 'Winner_value_pct', y = 'Rank_rev')
plt.show()

# Check if some products are prone to draws? how to do efficiently?
# More dispersion among pairs further away (try discrete)

# Todo: add from LSA: Enseigne_Alt and Group to have correct df_comp and df_same

print smf.ols('Rank_rev ~ Winner_value_pct + Dist',
        data = df_repro_compa).fit().summary()

df_repro_compa['Close'] = 0
df_repro_compa.loc[df_repro_compa['Dist'] <= 5, 'Close'] = 1

print df_repro_compa[['Close', 'Same_municipality']].describe()

print smf.ols('Rank_rev ~ Winner_value_pct + Close',
        data = df_repro_compa).fit().summary()

print smf.ols('Rank_rev ~ Winner_value_pct + Same_municipality',
        data = df_repro_compa).fit().summary()

# Product draw
se_prod_draws_vc = pd.Series(ls_prod_draws).value_counts()
print u'Top 20 products in terms of draws:'
print se_prod_draws_vc[0:20]
