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

# ####################
# LOAD DATA
# ####################

dateparse = lambda x: pd.datetime.strptime(x, '%d/%m/%Y')
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      dtype = {'id_lsa' : str},
                      parse_dates = ['date'],
                      date_parser = dateparse,
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

# Average price by period/chain/product
ls_prod_cols = ['product'] # ['section', 'family' , 'product']
ls_col_gb = ['period', 'store_chain_alt'] + ls_prod_cols + ['price']
df_mcpp = df_qlmc.groupby(ls_col_gb[:-1]).agg([len, np.mean])['price']
df_mcpp.reset_index(drop = False, inplace = True)

dict_df_chain_su = {}
for chain in df_mcpp['store_chain_alt'].unique():
  df_chain = df_mcpp[(df_mcpp['store_chain_alt'] == chain) &\
                     (df_mcpp['len'] >= 10)]
  
  ls_rows = []
  # tup_per = (0, 1)
  ls_tup_per = [(i, i+1) for i in range(0, 12)]
  for tup_per in ls_tup_per:
    df_chain_0 = df_chain[df_chain['period'] == tup_per[0]]
    df_chain_1 = df_chain[df_chain['period'] == tup_per[1]]
    df_compa = pd.merge(df_chain_0[ls_prod_cols + ['mean']],
                        df_chain_1[ls_prod_cols + ['mean']],
                        on = ls_prod_cols,
                        how = 'inner',
                        suffixes = ('_t', '_t+1'))
    nb_prods = len(df_compa)
    agg_chge = np.nan
    if nb_prods != 0:
      agg_chge = ((df_compa['mean_t+1'].sum() / df_compa['mean_t'].sum()) - 1) * 100
    ls_rows.append((tup_per[0], tup_per[1], nb_prods, agg_chge))
  
  df_chain_su = pd.DataFrame(ls_rows,
                             columns = ['per_t', 'per_t+1', 'nb_obs', 'var'])
  dict_df_chain_su[chain] = df_chain_su
  print ''
  print chain
  print df_chain_su.to_string()

# Gather in one table
ls_keys, ls_se_var = [], []
for chain, df_chain_su in dict_df_chain_su.items():
  ls_keys.append(chain)
  ls_se_var.append(df_chain_su['var'])
df_var_su = pd.concat(ls_se_var, axis = 1, keys = ls_keys)

# Add periods and day delta (if date is parsed)
ls_dates = [df_qlmc[df_qlmc['period'] == i]['date'].max() for i in range(0, 13)]
ls_tup_dates = [(some_date.strftime('%m/%Y'), ls_dates[i+1].strftime('%m/%Y'))\
                   for i, some_date in enumerate(ls_dates[:-1])]
ls_delta_dates = [ls_dates[i+1] - some_date\
                    for i, some_date in enumerate(ls_dates[:-1])]
ls_str_dates = ['-'.join(tup_dates) for tup_dates in ls_tup_dates]
df_var_su['period'] = ls_str_dates
df_var_su['length'] = ls_delta_dates

# From 05/2007 to 06/2012 (or 05/2011 if using section/family)
print()
print('Inflation over 05/2007 - 06/2012')
for chain in dict_df_chain_su.keys():
  y = 1
  for x in df_var_su[chain].values:
    y = y * (x + 100)/100
  y = (y-1) * 100
  print 'Chge for brand {:s} : {:.2f}'.format(chain, y)

# FROM 05/2007 to 02/2011 (supposed to be stable?)
print()
print('Inflation over 05/2007 - 02/2011')
for chain in dict_df_chain_su.keys():
  y = 1
  for x in df_var_su[chain][:8].values:
    y = y * (x + 100)/100
  y = (y-1) * 100
  print 'Chge for brand {:s} : {:.2f}'.format(chain, y)

# From 05/2007 to 05/2011
print()
print('Inflation over 05/2007 - 02/2011')
for chain in dict_df_chain_su.keys():
  y = 1
  for x in df_var_su[chain][4:8].values:
    y = y * (x + 100)/100
  y = (y-1) * 100
  print 'Chge for brand {:s} : {:.2f}'.format(chain, y)

# Try to merge across periods within same chain? (could pool all chains?)
chain = 'LECLERC'
df_chain = df_mcpp[(df_mcpp['store_chain_alt'] == chain)]
df_ap = df_chain[df_chain['period'] == 0][ls_prod_cols + ['mean']]
for period in range(1, 10):
  df_ap = pd.merge(df_ap,
                   df_chain[df_chain['period'] == period]\
                           [ls_prod_cols + ['mean']],
                   on = ls_prod_cols,
                   how = 'inner',
                   suffixes = ('', '_{:d}'.format(period)))

df_ap.set_index(ls_prod_cols, inplace = True)
se_per_sum = df_ap.sum()
(se_per_sum / se_per_sum.shift(1) - 1) * 100
