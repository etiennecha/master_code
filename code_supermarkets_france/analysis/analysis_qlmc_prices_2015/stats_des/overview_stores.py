#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
from functions_string import *
from functions_generic_qlmc import *
import os, sys
import re
import json
import pandas as pd

path_qlmc_scraped = os.path.join(path_data,
                                 'data_supermarkets',
                                 'data_qlmc_2015',
                                 'data_source',
                                 'data_scraped_201503')

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

path_lsa_csv = os.path.join(path_data,
                            'data_supermarkets',
                            'data_built',
                            'data_lsa',
                            'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##########
# LOAD DATA
# ##########

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'c_insee' : str,
                                 'id_lsa' : str},
                        encoding = 'utf-8')

df_lsa = pd.read_csv(os.path.join(path_lsa_csv,
                                  'df_lsa_active.csv'),
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

df_stores = pd.merge(df_stores,
                     df_lsa,
                     on = 'id_lsa',
                     how = 'left')

# overwrite store_chain
ls_replace_chains = [['HYPER U', 'SUPER U'],
                     ['U EXPRESS', 'SUPER U'],
                     ['HYPER CASINO', 'CASINO'],
                     ["LES HALLES D'AUCHAN", 'AUCHAN']]
for old_chain, new_chain in ls_replace_chains:
  df_stores.loc[df_stores['store_chain'] == old_chain,
                'store_chain'] = new_chain

ls_some_chains = ['LECLERC',
                  'INTERMARCHE',
                  'SUPER U',
                  'CARREFOUR MARKET',
                  'AUCHAN',
                  'CORA',
                  'CARREFOUR',
                  'GEANT CASINO',
                  'CASINO',
                  'SIMPLY MARKET']

df_stores_excl = df_stores[~df_stores['store_chain'].isin(ls_some_chains)].copy()
df_stores = df_stores[df_stores['store_chain'].isin(ls_some_chains)]

# ###############
# STATS DES
# ###############

# http://pbpython.com/pandas-pivot-table-explained.html

# NB STORES / HYPERS / SUPERS BY CHAINS
df_type = pd.pivot_table(df_stores,
                         index = 'store_chain',
                         columns = 'type',
                         values = 'id_lsa',
                         aggfunc  = 'count').fillna(0).astype(int)
df_type['Tot'] = df_type.sum(1)
df_type.ix['Total'] = df_type.sum(0)
#df_type['Pct_Hypers'] = df_type['H'] / df_type['Tot'].astype(float) * 100
#df_type['Pct_Supers'] = df_type['S'] / df_type['Tot'].astype(float) * 100
print()
print(df_type.to_string())

# DESCRIBE SOME COLS BY CHAIN
ls_cols = ['surface',
           'nb_caisses',
           'nb_emplois',
           'nb_parking',
           'nb_pompes']
# caution for some vars, missing means 0
for col in ['nb_parking', 'nb_pompes']:
  df_stores.loc[(~df_stores['id_lsa'].isnull()) &\
                (df_stores[col].isnull()), col] = 0

dict_df_cols = {}
for col in ls_cols:
  df_col = df_stores[['store_chain', col]].groupby('store_chain')\
                                          .describe()[col].unstack().astype(int)
  dict_df_cols = df_col
  print()
  print(col)
  print(df_col.to_string())

# DESCRIBE SOME COLS BY CHAIN WITH HYPER / SUPER SPLIT
ls_cols.sort()
dict_aggfunc = {col : ['mean'] for col in ls_cols}
dict_aggfunc[ls_cols[0]] = ['count', 'mean']
df_su_0 = pd.pivot_table(df_stores,
                         index = ['store_chain', 'type'],
                         values = ls_cols,
                         aggfunc = dict_aggfunc).astype(int)
print()
print(df_su_0.to_string())

print()
df_su_1 = pd.pivot_table(df_stores,
                         index = ['store_chain'],
                         values = ls_cols,
                         aggfunc = dict_aggfunc).astype(int)
print(df_su_1.to_string())
