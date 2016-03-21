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

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

ls_periods = ['201405', '201409']
dict_dfs = {}
for period in ls_periods:
  dict_dfs['qlmc_{:s}'.format(period)] =\
      pd.read_csv(os.path.join(path_built_csv,
                               'df_qlmc_{:s}.csv'.format(period)),
                  dtype = {'ean' : str,
                           'id_lsa' : str}, # to update soon
                  encoding = 'utf-8')
  
  dict_dfs['freq_prods_{:s}'.format(period)] =\
    pd.read_csv(os.path.join(path_built_csv,
                             'df_chain_product_price_freq_{:s}.csv'.format(period)),
                encoding = 'utf-8')
  
  dict_dfs['freq_stores_{:s}'.format(period)] =\
      pd.read_csv(os.path.join(path_built_csv,
                               'df_chain_store_price_freq_{:s}.csv'.format(period)),
                  encoding = 'utf-8')

ls_prod_cols = ['EAN', 'product']
ls_store_cols = ['id_lsa', 'store_name']

# store chain harmonization per qlmc
ls_replace_chains = [['HYPER CASINO', 'CASINO'],
                     ['HYPER U', 'SUPER U'],
                     ['U EXPRESS', 'SUPER U'],
                     ["LES HALLES D'AUCHAN", 'AUCHAN'],
                     ['INTERMARCHE SUPER', 'INTERMARCHE'],
                     ['INTERMARCHE HYPER', 'INTERMARCHE'], # any?
                     ['MARKET', 'CARREFOUR MARKET'],
                     ['CENTRE E.LECLERC', 'LECLERC']]

ls_df_qlmc = [dict_dfs['qlmc_{:s}'.format(period)] for period in ls_periods]
for df_qlmc in ls_df_qlmc:
  for old_chain, new_chain in ls_replace_chains:
    df_qlmc.loc[df_qlmc['store_chain'] == old_chain,
                'store_chain'] = new_chain

## Robustness check: 3000 most detained products only
#se_prod_vc = df_qlmc[ls_prod_cols].groupby(ls_prod_cols).agg(len)
#ls_keep_products = [x[-1] for x in list(se_prod_vc[0:3000].index)]
#df_qlmc = df_qlmc[df_qlmc[ls_prod_cols[-1]].isin(ls_keep_products)]

# ############################################
# COMPARE LECLERC AND GEANT CASINO REF PRICES
# ############################################

ls_df_freq_prods = [dict_dfs['freq_prods_{:s}'.format(period)] for period in ls_periods]

lsd_compa = ls_prod_cols + ['price_1_gc', 'price_1_lec',
                            'price_1_fq_gc', 'price_1_fq_lec',
                            'diff', 'diff_pct']

ls_df_compa = []
for df_freq_prods in ls_df_freq_prods:
  df_gc = df_freq_prods[df_freq_prods['store_chain'] == 'GEANT CASINO']
  df_lec = df_freq_prods[df_freq_prods['store_chain'] == 'LECLERC']

  df_compa = pd.merge(df_gc,
                      df_lec,
                      on = ls_prod_cols,
                      suffixes = ('_gc', '_lec'),
                      how = 'inner')
  df_compa['diff'] = df_compa['price_1_gc'] - df_compa['price_1_lec']
  df_compa['diff_pct'] = (df_compa['price_1_gc'] - df_compa['price_1_lec'])\
                            * 100 / df_compa['price_1_lec']
  ls_df_compa.append(df_compa)

df_dc = pd.merge(ls_df_compa[0],
                 ls_df_compa[1],
                 on = ls_prod_cols,
                 suffixes = ('_1', '_2'),
                 how = 'inner')

print('Nb std prices which have chged:',
      len(df_dc[(df_dc['diff_1'] - df_dc['diff_2']).abs() > 10e-4]))

print('Nb std prices for which compa reversed:',
      len(df_dc[(df_dc['diff_1'] * df_dc['diff_2']) < -10e-4]))

# Both trend downwards... how about other LEC / GC Prices
# How about other brand prices?

(df_dc['price_1_lec_2'] - df_dc['price_1_lec_1']).describe()
(df_dc['price_1_gc_2'] - df_dc['price_1_gc_1']).describe()

## #######
## BACKUP
## #######
##
#df_gc = dict_df_chain_product_stats['GEANT CASINO'].copy()
#df_lec = dict_df_chain_product_stats['LECLERC'].copy()
#
#df_compa = pd.merge(df_gc,
#                    df_lec,
#                    on = ls_prod_cols,
#                    suffixes = ('_gc', '_lec'),
#                    how = 'inner')
#df_compa['diff'] = df_compa['price_1_gc'] - df_compa['price_1_lec']
#df_compa['diff_pct'] = (df_compa['price_1_gc'] - df_compa['price_1_lec'])\
#                          * 100 / df_compa['price_1_lec']
#
#lsd_compa = ls_prod_cols + ['price_1_gc', 'price_1_lec',
#                            'price_1_fq_gc', 'price_1_fq_lec',
#                            'diff', 'diff_pct']
#
#print()
#print(u'-'*60)
#print(u'Compare Leclerc and Geant Casino baseline prices')
#print()
#print()
#print(df_compa[lsd_compa].describe().to_string())
#
#print()
#print(df_compa[df_compa['price_1_fq_lec'] >= 0.33][lsd_compa].describe().to_string())
#
#print()
#print(u'Pct draws: {:.2f}'.format(len(df_compa[(df_compa['diff'].abs() <= 10e-4)]) /\
#                                  float(len(df_compa))* 100))
#print(u'Pct LEC wins: {:.2f}'.format(len(df_compa[(df_compa['diff'] > 10e-4)]) /\
#                                  float(len(df_compa))* 100))
#print(u'Pct GC wins: {:.2f}'.format(len(df_compa[(df_compa['diff'] < -10e-4)]) /\
#                                  float(len(df_compa))* 100))
#
## todo: compare in both periods (and third i.e. 2015 if possible)
#
