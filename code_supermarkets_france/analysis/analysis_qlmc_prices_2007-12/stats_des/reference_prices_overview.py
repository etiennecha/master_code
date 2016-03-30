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

# #######################
# LOAD DATA
# #######################

# LOAD DF QLMC
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      parse_dates = ['date'],
                      dayfirst = True,
                      encoding = 'utf-8')

# Fix Store_Chain for prelim stats des
ls_sc_drop = ['CARREFOUR CITY',
              'CARREFOUR CONTACT',
              'CARREFOUR PLANET',
              'GEANT DISCOUNT',
              'HYPER CHAMPION',
              'INTERMARCHE HYPER',
              'LECLERC EXPRESS',
              'MARCHE U',
              'U EXPRESS']

df_qlmc = df_qlmc[~df_qlmc['store_chain'].isin(ls_sc_drop)]

ls_sc_replace = [('CENTRE E. LECLERC', 'LECLERC'),
                 ('CENTRE LECLERC', 'LECLERC'),
                 ('E. LECLERC', 'LECLERC'),
                 ('E.LECLERC', 'LECLERC'),
                 ('SYSTEME U', 'SUPER U'),
                 ('GEANT', 'GEANT CASINO'),
                 ('CHAMPION', 'CARREFOUR MARKET')]
for sc_old, sc_new in ls_sc_replace:
  df_qlmc.loc[df_qlmc['store_chain'] == sc_old,
              'store_chain'] = sc_new

# #############################################
# PRICE DISTRIBUTION PER CHAIN FOR TOP PRODUCTS
# #############################################

PD = PriceDispersion()

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
              'price_1_fq', 'price_2_fq', 'price_12_fq']

# One period (need product to be available in this one)
df_qlmc_prod_per = df_qlmc_prod[df_qlmc_prod['period'] == 1]
df_pd =  df_qlmc_prod_per[['price', 'store_chain']]\
           .groupby('store_chain').agg([len,
                                        PD.price_1,
                                        PD.price_1_fq,
                                        PD.price_2,
                                        PD.price_2_fq])['price']
df_pd.columns = [col.replace('PD.', '') for col in df_pd.columns]
df_pd.rename(columns = {'len': 'nb_obs'}, inplace = True)
df_pd.sort('nb_obs', ascending = False, inplace = True)
df_pd['price_12_fq'] = df_pd[['price_1_fq', 'price_2_fq']].sum(axis = 1)

print()
print(u'price frequencies per chains for one product in period 1')
print(df_pd[ls_pd_disp].to_string())

# All periods
df_pd_2 = df_qlmc_prod[['period', 'price', 'store_chain']]\
            .groupby(['period', 'store_chain']).agg([len,
                                                     PD.price_1,
                                                     PD.price_1_fq,
                                                     PD.price_2,
                                                     PD.price_2_fq])['price']
df_pd_2.columns = [col.replace('PD.', '') for col in df_pd_2.columns]
df_pd_2.rename(columns = {'len': 'nb_obs'}, inplace = True)
# Sort by nb of obs within each period             
df_pd_2.reset_index('period', drop = False, inplace = True)
df_pd_2.sort(['period', 'nb_obs'], ascending = False, inplace = True)
df_pd_2.set_index('period', append = True, inplace = True)
df_pd_2 = df_pd_2.swaplevel(0, 1, axis = 0)
df_pd_2['price_12_fq'] = df_pd_2[['price_1_fq', 'price_2_fq']].sum(axis = 1)

print()
print(u'price frequencies per chains for one product in all periods')
print(df_pd_2[df_pd_2['nb_obs'] >= 10][ls_pd_disp].to_string())

# Extract by chain
df_pd_2.sortlevel(inplace = True)
print()
print(u'price frequencies for one product and chain in all periods')
print(df_pd_2.loc[(slice(None), u'LECLERC'),:][ls_pd_disp].to_string())

# Todo: Expand 
# => over products if can be
# => baskets of good (by period / chain given product scarcity)

# For one chain within period, if no need to take same store sample:
df_sub = df_qlmc[(df_qlmc['period'] == 0) &\
                 (df_qlmc['store_chain'] == 'LECLERC')]
ls_sub_top_prods = df_sub['product'].value_counts().index[0:20].tolist()
df_sub = df_sub[df_sub['product'].isin(ls_sub_top_prods)]

df_pd_3 =  df_sub[['price', 'product']]\
             .groupby(['product']).agg([len,
                                        PD.price_1,
                                        PD.price_1_fq,
                                        PD.price_2,
                                        PD.price_2_fq])['price']
df_pd_3.columns = [col.replace('PD.', '') for col in df_pd_3.columns]
df_pd_3.rename(columns = {'len': 'nb_obs'}, inplace = True)
df_pd_3['price_12_fq'] = df_pd_3[['price_1_fq', 'price_2_fq']].sum(axis = 1)

print()
print(u'price frequencies for 20 products and one chain in one period')
print(df_pd_3[ls_pd_disp].to_string())

# Todo: 
# for one chain: one row by period (could add by dpt)
# price distribution for each unique product (rayon/famille/prod)
# take avg of first freq and second freq (could take interquartile gap etc)
# keep only if enough products
