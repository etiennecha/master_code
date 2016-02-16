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

# #######################
# LOAD DF QLMC
# #######################

# LOAD DF PRICES
df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

# LOAD DF STORES (INCLUDING LSA INFO)
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
                     df_lsa[['id_lsa', 'enseigne_alt', 'groupe', 'surface']],
                     on = 'id_lsa',
                     how = 'left')

# BUILD DF QLMC WITH PRICE AND STORE INFO
df_prices.drop(['store_chain'], axis = 1, inplace = True) # in df_stores too...
df_qlmc = pd.merge(df_prices,
                   df_stores,
                   left_on = 'store_id',
                   right_on = 'store_id',
                   how = 'left')
df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]

# Avoid error msg on condition number
df_qlmc['surface'] = df_qlmc['surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_price'] = np.log(df_qlmc['price'])
# Control for dpt (region?)
df_qlmc['ppt'] = df_qlmc['c_insee'].str.slice(stop = 2)

# #############################################
# PRICE DISTRIBUTION PER CHAIN FOR TOP PRODUCTS
# #############################################

def nb_obs(se_prices):
  return len(se_prices)

def price_1(se_prices):
  return se_prices.value_counts().index[0]

def price_1_freq(se_prices):
  return se_prices.value_counts().iloc[0] / float(len(se_prices))

def price_2(se_prices):
  if len(se_prices.value_counts()) > 1:
    return se_prices.value_counts().index[1]
  else:
    return np.nan

def price_2_freq(se_prices):
  if len(se_prices.value_counts()) > 1:
    return se_prices.value_counts().iloc[1] / float(len(se_prices))
  else:
    return 0

se_prod = df_qlmc.groupby(['section', 'family', 'product']).agg('size')
se_prod.sort(ascending = False, inplace = True)

# WITH ONE PRODUCT
family, subfamily, product = se_prod.index[0]
# produit = u'Coca Cola - Coca Cola avec caféine, 1,5L'

df_qlmc_prod = df_qlmc[(df_qlmc['section'] == family) &\
                       (df_qlmc['family'] == subfamily) &\
                       (df_qlmc['product'] == product)].copy()
ls_pd_disp = ['nb_obs',
              'price_1', 'price_2',
              'price_1_freq', 'price_2_freq', 'price_12_freq']

# One period (need product to be available in this one)
df_pd =  df_qlmc_prod[['price', 'enseigne_alt']]\
           .groupby('enseigne_alt').agg([nb_obs,
                                         price_1,
                                         price_1_freq,
                                         price_2,
                                         price_2_freq])['price']
df_pd.sort('nb_obs', ascending = False, inplace = True)
df_pd['price_12_freq'] = df_pd[['price_1_freq', 'price_2_freq']].sum(axis = 1)

print()
print(u'price frequencies per chains for one product in period 1')
print(df_pd[ls_pd_disp].to_string())

## All periods
#df_pd_2 =  df_qlmc_prod[['period', 'price', 'enseigne_alt']]\
#             .groupby(['period', 'enseigne_alt']).agg([nb_obs,
#                                                       price_1,
#                                                       price_1_freq,
#                                                       price_2,
#                                                       price_2_freq])['price']
#
## Sort by nb of obs within each period             
#df_pd_2.reset_index('period', drop = False, inplace = True)
#df_pd_2.sort(['period', 'nb_obs'], ascending = False, inplace = True)
#df_pd_2.set_index('period', append = True, inplace = True)
#df_pd_2 = df_pd_2.swaplevel(0, 1, axis = 0)
#df_pd_2['price_12_freq'] = df_pd_2[['price_1_freq', 'price_2_freq']].sum(axis = 1)
#
#print()
#print(u'price frequencies per chains for one product in all periods')
#print(df_pd_2[df_pd_2['nb_obs'] >= 10][ls_pd_disp].to_string())
#
## Extract by chain
#df_pd_2.sortlevel(inplace = True)
#print()
#print(u'price frequencies for one product and chain in all periods')
#print(df_pd_2.loc[(slice(None), u'CENTRE E.LECLERC'),:][ls_pd_disp].to_string())
#
## Todo: Expand 
## => over products if can be
## => baskets of good (by period / chain given product scarcity)

# For one chain within period, if no need to take same store sample:
df_sub = df_qlmc[(df_qlmc['enseigne_alt'] == 'CENTRE E.LECLERC')]
ls_sub_top_prods = df_sub['product'].value_counts().index[0:20].tolist()
df_sub = df_sub[df_sub['product'].isin(ls_sub_top_prods)]

df_pd_3 =  df_sub[['price', 'product']]\
             .groupby(['product']).agg([nb_obs,
                                        price_1,
                                        price_1_freq,
                                        price_2,
                                        price_2_freq])['price']
df_pd_3['price_12_freq'] = df_pd_3[['price_1_freq', 'price_2_freq']].sum(axis = 1)

print()
print(u'Price frequencies for 20 products and one chain in one period')
print(df_pd_3[ls_pd_disp].to_string())

# Todo: 
# for one chain: one row by period (could add by dpt)
# price distribution for each unique product (rayon/famille/prod)
# take avg of first freq and second freq (could take interquartile gap etc)
# keep only if enough products
