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
    df_spread['nb_1_wins'] = df_spread[ls_df_price_cols[1:]]\
                               .apply(lambda x: (x > 10e-4).sum(), axis = 1)
    df_spread['nb_0_wins'] = df_spread[ls_df_price_cols[1:]]\
                               .apply(lambda x: (x < -10e-4).sum(), axis = 1)
    # Nb products with a change in rank
    nb_obs = len(df_spread)
    nb_rr = len(df_spread[(df_spread['nb_1_wins'] > 0) &\
                          (df_spread['nb_0_wins'] > 0)])
    # Total amounts
    se_sum_0 = df_price_0.ix[df_spread.index].sum(0)
    se_sum_1 = df_price_1.ix[df_spread.index].sum(0)
    se_delta = se_sum_1 - se_sum_0

    ls_rows_compa.append([id_lsa_0, id_lsa_1,
                          nb_obs, nb_rr] +\
                         se_sum_0.values.tolist() +\
                         se_delta.values.tolist())

df_compa = pd.DataFrame(ls_rows_compa,
                        columns = ['id_lsa_0', 'id_lsa_1',
                                   'nb_obs', 'nb_rr',
                                   'price_0_0', 'price_1_0', 'price_2_0',
                                   'delta_0', 'delta_1', 'delta_2'])

ls_pair_cols = ['id_lsa_0', 'id_lsa_1', 'dist',
                'store_name_0', 'store_name_1',
                'store_chain_0', 'store_chain_1']

df_compa_2 = pd.merge(df_compa,
                      df_comp_pairs[ls_pair_cols],
                      on = ['id_lsa_0', 'id_lsa_1'],
                      how = 'left')

df_compa_2['pct_rr'] = df_compa_2['nb_rr'] / df_compa_2['nb_obs'].astype(float)

tup_brands = ('LECLERC', 'GEANT CASINO')
print(df_compa_2[(df_compa_2['store_chain_0'].isin(tup_brands)) &\
                 (df_compa_2['store_chain_1'].isin(tup_brands))].describe().to_string())
