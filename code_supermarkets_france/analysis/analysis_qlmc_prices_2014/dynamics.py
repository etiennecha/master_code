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

path_built_2015 = os.path.join(path_data,
                               'data_supermarkets',
                               'data_built',
                               'data_qlmc_2015')
path_built_201415_csv = os.path.join(path_built_2015,
                                     'data_csv_2014-2015')
path_built_201415_json = os.path.join(path_built_2015,
                                     'data_json_2014-2015')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

df_qlmc = pd.read_csv(os.path.join(path_built_201415_csv,
                                   'df_qlmc_2014-2015.csv'),
                      dtype = {'ean' : str,
                               'id_lsa' : str},
                      encoding = 'utf-8')

df_comp_pairs = pd.read_csv(os.path.join(path_built_201415_csv,
                                         'df_comp_store_pairs.csv'),
                            dtype = {'id_lsa_0' : str,
                                     'id_lsa_1' : str},
                            encoding = 'utf-8')

# ##################
# DYNA RANK REVERSAL
# ##################


# All periods observed? 670 stores with 158 to 1599 obs
df_full = df_qlmc[(~df_qlmc['price_0'].isnull()) &\
                  (~df_qlmc['price_1'].isnull()) &\
                  (~df_qlmc['price_2'].isnull())]

# Can also consider 0 to 2
df_02 = df_qlmc[(~df_qlmc['price_0'].isnull()) &\
                (~df_qlmc['price_2'].isnull())]

# todo:
# - get competitor pairs
# - subtract price dataframes

ls_df_price_cols = ['ean', 'price_0', 'price_1', 'price_2']

id_lsa_0, id_lsa_1 = df_comp_pairs[['id_lsa_0', 'id_lsa_1']].iloc[0].values

df_qlmc_temp = df_full
ls_store_cols = ['id_lsa', 'store_name', 'store_chain']
df_stores_temp =  df_full[ls_store_cols].drop_duplicates()
ls_keep_stores = list(df_stores_temp['id_lsa'].values)

ls_rows_compa = []

for row_i, row in df_comp_pairs.iterrows():
  id_lsa_0, id_lsa_1 = row[['id_lsa_0', 'id_lsa_1']].values
  # id_lsa_0, id_lsa_1 = '455', '54'
  if (id_lsa_0 in ls_keep_stores) and (id_lsa_1 in ls_keep_stores):
  
    df_price_0 = df_full[df_full['id_lsa'] == id_lsa_0][ls_df_price_cols]
    df_price_0.set_index('ean', inplace = True)
    
    df_price_1 = df_full[df_full['id_lsa'] == id_lsa_1][ls_df_price_cols]
    df_price_1.set_index('ean', inplace = True)
    
    df_spread = df_price_0 - df_price_1
    # filter nan lines (could as well use first col)
    df_spread = df_spread[df_spread.count(1) == 3]
    
    nb_obs = len(df_spread)
    
    # nb of products cheaper at each store within each period
    se_nb_prod_0_wins = df_spread[df_spread < -10e-4].count()
    se_nb_prod_1_wins = df_spread[df_spread >  10e-4].count()
    
    # nb of periods where product is cheaper
    df_spread['nb_per_1_wins'] = df_spread[ls_df_price_cols[1:]]\
                                   .apply(lambda x: (x >  10e-4).sum(), axis = 1)
    df_spread['nb_per_0_wins'] = df_spread[ls_df_price_cols[1:]]\
                                   .apply(lambda x: (x < -10e-4).sum(), axis = 1)
    # nb products which exhibit dynamic rank reversals
    nb_rr = len(df_spread[(df_spread['nb_per_1_wins'] > 0) &\
                          (df_spread['nb_per_0_wins'] > 0)])
    # nb products with no dynamic rank reversal
    nb_dom = len(df_spread[((df_spread['nb_per_1_wins'] == 0) |\
                            (df_spread['nb_per_0_wins'] == 0)) &\
                           ((df_spread['nb_per_1_wins'] != 0) |\
                            (df_spread['nb_per_0_wins'] != 0))])
    # nb products with always exact same price
    nb_draw = len(df_spread[(df_spread['nb_per_1_wins'] == 0) &\
                            (df_spread['nb_per_0_wins'] == 0)])
    # total amounts
    se_sum_0 = df_price_0.ix[df_spread.index].sum(0)
    se_sum_1 = df_price_1.ix[df_spread.index].sum(0)
    se_delta = se_sum_1 - se_sum_0

    ls_rows_compa.append([id_lsa_0, id_lsa_1,
                          nb_obs, nb_rr, nb_dom, nb_draw] +\
                         se_nb_prod_0_wins.tolist() +\
                         se_nb_prod_1_wins.tolist() +\
                         se_sum_0.values.tolist() +\
                         se_sum_1.values.tolist())

df_compa = pd.DataFrame(ls_rows_compa,
                        columns = ['id_lsa_0', 'id_lsa_1',
                                   'nb_obs', 'nb_rr', 'nb_dom', 'nb_draw',
                                   'nb_wins_0_0', 'nb_wins_1_0', 'nb_wins_2_0',
                                   'nb_wins_0_1', 'nb_wins_1_1', 'nb_wins_2_1',
                                   'price_0_0', 'price_1_0', 'price_2_0',
                                   'price_0_1', 'price_1_1', 'price_2_1'])

ls_pair_cols = ['id_lsa_0', 'id_lsa_1', 'dist',
                'store_name_0', 'store_name_1',
                'store_chain_0', 'store_chain_1']

df_compa_2 = pd.merge(df_compa,
                      df_comp_pairs[ls_pair_cols],
                      on = ['id_lsa_0', 'id_lsa_1'],
                      how = 'left')

df_compa_2['pct_rr'] = df_compa_2['nb_rr'] / df_compa_2['nb_obs'].astype(float)
df_compa_2['pct_dom'] = df_compa_2['nb_dom'] / df_compa_2['nb_obs'].astype(float)
df_compa_2['pct_draw'] = df_compa_2['nb_draw'] / df_compa_2['nb_obs'].astype(float)

# Brand comparison: need to sort order to have one brand per column

tup_chains = ('LECLERC', 'GEANT CASINO')
df_cc = df_compa_2[(df_compa_2['store_chain_0'].isin(tup_chains)) &\
                   (df_compa_2['store_chain_1'].isin(tup_chains))].copy()

lsd0 = ['dist', 'nb_obs', 'pct_rr', 'pct_dom', 'pct_draw']
print(df_cc[lsd0].describe().to_string())

ls_copy_cols = ['store_name', 'store_chain', 'id_lsa',
                'nb_wins_0', 'nb_wins_1', 'nb_wins_2',
                'price_0', 'price_1', 'price_2']

tup_sufs = ['A', 'B']
for brand, suf in zip(tup_chains, tup_sufs):
  for col in ls_copy_cols:
    df_cc[u'{:s}_{:s}'.format(col, suf)] = 0
    df_cc.loc[df_cc['store_chain_0'] == brand,
                   u'{:s}_{:s}'.format(col, suf)] =\
      df_cc[u'{:s}_0'.format(col)]
    df_cc.loc[df_cc['store_chain_1'] == brand,
                   u'{:s}_{:s}'.format(col, suf)] =\
      df_cc[u'{:s}_1'.format(col)]

ls_drop_cols = [u'{:s}_0'.format(x) for x in ls_copy_cols] +\
               [u'{:s}_1'.format(x) for x in ls_copy_cols]

df_cc.drop(ls_drop_cols, axis = 1, inplace = True)

# add cols:

# - % prod wins within period 
# - % prod draws within period
# - % prod rank reversals within period
# - % aggregate compa within period
# - avg value aggreate compa within period

ls_per = ['0', '1', '2']
for per in ls_per:
  df_cc['pct_prod_wins_{:s}_A'.format(per)] =\
      df_cc['nb_wins_{:s}_A'.format(per)] / df_cc['nb_obs'].astype(float)
  df_cc['pct_prod_wins_{:s}_B'.format(per)] =\
      df_cc['nb_wins_{:s}_B'.format(per)] / df_cc['nb_obs'].astype(float)
  df_cc['pct_prod_draws_{:s}'.format(per)] =\
      1 - df_cc[['pct_prod_wins_{:s}_A'.format(per),
                 'pct_prod_wins_{:s}_B'.format(per)]].sum(1)
  df_cc['pct_prod_rr_{:s}'.format(per)] = df_cc[['pct_prod_wins_{:s}_A'.format(per),
                 'pct_prod_wins_{:s}_B'.format(per)]].min(1)
  df_cc['pct_agg_compa_{:s}'.format(per)] =\
    df_cc['price_{:s}_B'.format(per)] / df_cc['price_{:s}_A'.format(per)] - 1
  df_cc['avg_agg_compa_{:s}'.format(per)] =\
    (df_cc['price_{:s}_B'.format(per)] - df_cc['price_{:s}_A'.format(per)]) /\
       df_cc['nb_obs']

ls_dcc = ['pct_prod_wins_{:s}_A'.format(per) for per in ls_per] +\
         ['pct_prod_draws_{:s}'.format(per) for per in ls_per] +\
         ['pct_prod_rr_{:s}'.format(per) for per in ls_per] +\
         ['pct_agg_compa_{:s}'.format(per) for per in ls_per]

print(df_cc[ls_dcc].describe().to_string())

# todo: rr at agg level?
ls_pct_agg_compa_cols = ['pct_agg_compa_{:s}'.format(per) for per in ls_per]
df_cc['nb_per_A_wins'] = df_cc[ls_pct_agg_compa_cols]\
                               .apply(lambda x: (x >  10e-4).sum(), axis = 1)
df_cc['nb_per_B_wins'] = df_cc[ls_pct_agg_compa_cols]\
                               .apply(lambda x: (x < -10e-4).sum(), axis = 1)

nb_rr_agg = len(df_cc[(df_cc['nb_per_A_wins'] > 0) &\
                      (df_cc['nb_per_B_wins'] > 0)])
nb_dom_agg = len(df_cc[((df_cc['nb_per_A_wins'] == 0) |\
                        (df_cc['nb_per_B_wins'] == 0)) &\
                       ((df_cc['nb_per_A_wins'] != 0) |\
                        (df_cc['nb_per_B_wins'] != 0))])
nb_draw_agg = len(df_cc[(df_cc['nb_per_A_wins'] == 0) &\
                        (df_cc['nb_per_B_wins'] == 0)])
nb_some_draw_agg = len(df_cc[df_cc[['nb_per_A_wins',
                                    'nb_per_B_wins']].sum(1) < 3])
