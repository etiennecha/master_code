#!/usr/bin/env python
# -*- coding: utf-8 -*- 

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

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)

# #######################
# LOAD DF QLMC
# #######################

# LOAD DF QLMC
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      dtype = {'INSEE_Code' : str},
                      encoding = 'utf-8')
# date parsing slow... better if specified format?

# LOAD DF LSA
df_lsa = pd.read_csv(os.path.join(path_built_lsa_csv,
                                  'df_lsa_for_qlmc.csv'),
                     dtype = {u'C_INSEE' : str,
                              u'C_INSEE_Ardt' : str,
                              u'C_Postal' : str,
                              u'SIREN' : str,
                              u'NIC' : str,
                              u'SIRET' : str},
                     parse_dates = [u'Date_Ouv', u'Date_Fer', u'Date_Reouv',
                                    u'Date_Chg_Enseigne', u'Date_Chg_Surface'],
                     encoding = 'UTF-8')

# drop null id_lsa else gets too big
# todo: take Period into account (chges of chains)
df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]
df_qlmc = pd.merge(df_qlmc,
                   df_lsa[['Ident', 'Enseigne_Alt', 'Groupe', 'Surface']],
                   left_on = 'id_lsa',
                   right_on = 'Ident',
                   how = 'left')
# high memory usage..

# Avoid error msg on condition number
df_qlmc['Surface'] = df_qlmc['Surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_Price'] = np.log(df_qlmc['Price'])
# Control for dpt (region?)
df_qlmc['Dpt'] = df_qlmc['INSEE_Code'].str.slice(stop = 2)

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

se_prod = df_qlmc.groupby(['Family', 'Subfamily', 'Product']).agg('size')
se_prod.sort(ascending = False, inplace = True)

# WITH ONE PRODUCT
family, subfamily, product = se_prod.index[0]
# produit = u'Coca Cola - Coca Cola avec caféine, 1,5L'

df_qlmc_prod = df_qlmc[(df_qlmc['Family'] == family) &\
                       (df_qlmc['Subfamily'] == subfamily) &\
                       (df_qlmc['Product'] == product)].copy()
ls_pd_disp = ['nb_obs',
              'price_1', 'price_2',
              'price_1_freq', 'price_2_freq', 'price_12_freq']

# One period (need product to be available in this one)
df_qlmc_prod_per = df_qlmc_prod[df_qlmc_prod['Period'] == 1]
df_pd =  df_qlmc_prod_per[['Price', 'Enseigne_Alt']]\
           .groupby('Enseigne_Alt').agg([nb_obs,
                                         price_1,
                                         price_1_freq,
                                         price_2,
                                         price_2_freq])['Price']
df_pd.sort('nb_obs', ascending = False, inplace = True)
df_pd['price_12_freq'] = df_pd[['price_1_freq', 'price_2_freq']].sum(axis = 1)

print u'\nPrice frequencies per chains for one product in period 1'
print df_pd[ls_pd_disp].to_string()

# All periods
df_pd_2 =  df_qlmc_prod[['Period', 'Price', 'Enseigne_Alt']]\
             .groupby(['Period', 'Enseigne_Alt']).agg([nb_obs,
                                                       price_1,
                                                       price_1_freq,
                                                       price_2,
                                                       price_2_freq])['Price']

# Sort by nb of obs within each period             
df_pd_2.reset_index('Period', drop = False, inplace = True)
df_pd_2.sort(['Period', 'nb_obs'], ascending = False, inplace = True)
df_pd_2.set_index('Period', append = True, inplace = True)
df_pd_2 = df_pd_2.swaplevel(0, 1, axis = 0)
df_pd_2['price_12_freq'] = df_pd_2[['price_1_freq', 'price_2_freq']].sum(axis = 1)

print u'\nPrice frequencies per chains for one product in all periods'
print df_pd_2[df_pd_2['nb_obs'] >= 10][ls_pd_disp].to_string()

# Extract by chain
df_pd_2.sortlevel(inplace = True)
print u'\nPrice frequencies for one product and chain in all periods'
print df_pd_2.loc[(slice(None), u'CENTRE E.LECLERC'),:][ls_pd_disp].to_string()

# Todo: Expand 
# => over products if can be
# => baskets of good (by period / chain given product scarcity)

# For one chain within period, if no need to take same store sample:
df_sub = df_qlmc[(df_qlmc['Period'] == 0) &\
                 (df_qlmc['Enseigne_Alt'] == 'CENTRE E.LECLERC')]
ls_sub_top_prods = df_sub['Product'].value_counts().index[0:20].tolist()
df_sub = df_sub[df_sub['Product'].isin(ls_sub_top_prods)]

df_pd_3 =  df_sub[['Price', 'Product']]\
             .groupby(['Product']).agg([nb_obs,
                                        price_1,
                                        price_1_freq,
                                        price_2,
                                        price_2_freq])['Price']
df_pd_3['price_12_freq'] = df_pd_3[['price_1_freq', 'price_2_freq']].sum(axis = 1)

print u'\nPrice frequencies for 20 products and one chain in one period'
print df_pd_3[ls_pd_disp].to_string()

# Todo: 
# for one chain: one row by period (could add by dpt)
# price distribution for each unique product (rayon/famille/prod)
# take avg of first freq and second freq (could take interquartile gap etc)
# keep only if enough products
