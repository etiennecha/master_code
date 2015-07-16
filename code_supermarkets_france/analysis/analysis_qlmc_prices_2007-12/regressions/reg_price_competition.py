#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_qlmc = os.path.join(path_data,
                             'data_supermarkets',
                             'data_qlmc_2007-12')

path_dir_built_csv = os.path.join(path_dir_qlmc,
                                  'data_built',
                                  'data_csv')

path_lsa = os.path.join(path_data,
                        'data_supermarkets',
                        'data_lsa',
                        'data_built',
                        'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)

# LOAD DF QLMC

print u'Loading df_qlmc'
df_qlmc = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_qlmc.csv'),
                      dtype = {'id_lsa' : str,
                               'INSEE_ZIP' : str,
                               'INSEE_Code' : str},
                      encoding = 'utf-8')

# LOAD DF COMP

print u'Loading df_comp'
df_comp_h = pd.read_csv(os.path.join(path_lsa,
                                     'df_eval_comp_H_v_all.csv'), #'df_comp_H_ac_vs_cont.csv'),
                        dtype = {'Ident': str},
                        encoding = 'latin-1')

df_comp_s = pd.read_csv(os.path.join(path_lsa,
                                     'df_eval_comp_S_v_all.csv'), #'df_comp_S_ac_vs_cont.csv'),
                        dtype = {'Ident': str},
                        encoding = 'latin-1')

df_comp = pd.concat([df_comp_h, df_comp_s],
                    axis = 0,
                    ignore_index = True)

df_comp.rename(columns = {u'Ident': 'id_lsa',
                          u'Surf Vente' : 'Surface',
                          u'Nbr de caisses' : u'Nb_checkouts',
                          u'Nbr emp' : 'Nb_emp',
                          u'Nbr parking' : 'Nb_parking',
                          u'Intégré / Indépendant' : u'Indpt'},
               inplace = True)

ls_lsa_info_cols = [u'Surface',
                    u'Nb_checkouts',
                    u'Nb_emp',
                    u'Nb_parking',
                    u'Indpt',
                    u'Groupe',
                    u'Groupe_alt',
                    u'Enseigne_alt',
                    u'Type_alt']

ls_lsa_comp_cols = ['ac_nb_stores',
                    'ac_nb_comp',
                    'ac_store_share',
                    'ac_group_share',
                    'ac_hhi']

df_qlmc = pd.merge(df_qlmc,
                   df_comp[['id_lsa'] +\
                           ls_lsa_info_cols +\
                           ls_lsa_comp_cols],
                   on = 'id_lsa',
                   how = 'left')

# ######################################
# REG MOST COMMON PRODUCT PRICES ON COMP
# ######################################

# get rid of no id_lsa match
df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]
# get rid of closed (so far but should accomodate later)
df_qlmc = df_qlmc[~df_qlmc['Enseigne_alt'].isnull()]

se_prod = df_qlmc.groupby(['Department', 'Family', 'Product']).agg('size')
se_prod.sort(ascending = False, inplace = True)

# Aavoid error msg on condition number
df_qlmc['Surface'] = df_qlmc['Surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_Price'] = np.log(df_qlmc['Price'])
# Control for dpt (region?)
df_qlmc['Dpt'] = df_qlmc['INSEE_Code'].str.slice(stop = 2)

# WITH ONE PRODUCT
rayon, famille, produit = se_prod.index[0]
df_qlmc_prod = df_qlmc[(df_qlmc['Department'] == rayon) &\
                       (df_qlmc['Family'] == famille) &\
                       (df_qlmc['Product'] == produit)].copy()

print u'\nRegression of price of {:s}'.format(produit)
reg = smf.ols('Price ~ C(Period) + Surface + Enseigne_alt + ac_hhi',
              data = df_qlmc_prod[df_qlmc_prod['Type_alt'] == 'H'],
              missing = 'drop').fit()
print reg.summary()

print u'\nRegression of log price of {:s}'.format(produit)
reg = smf.ols('ln_Price ~ C(Period) + Surface + Enseigne_alt + ac_hhi',
              data = df_qlmc_prod[df_qlmc_prod['Type_alt'] == 'H'],
              missing = 'drop').fit()
print reg.summary()

# Pbm: one or a few ref prices (per brand)... so reg is not very meaningful
# More convincing with store FE? set of products? 
# Do with LECLERC products?

# WITH TOP 20 PRODUCTS
ls_top_prod = [x[-1] for x in se_prod.index[0:20]]
df_qlmc_prods = df_qlmc[df_qlmc['Product'].isin(ls_top_prod)].copy()

print u'\nRegression of price of top 20 products (avail in data)'
reg = smf.ols('Price ~ C(Period) + C(Product) + Surface + Enseigne_alt + ac_hhi',
              data = df_qlmc_prods[df_qlmc_prods['Type_alt'] == 'H'],
              missing = 'drop').fit()
print reg.summary()

print u'\nRegression of log price of top 20 products (avail in data)'
reg = smf.ols('ln_Price ~ C(Period) + C(Product) + Surface + Enseigne_alt + ac_hhi',
              data = df_qlmc_prods[df_qlmc_prods['Type_alt'] == 'H'],
              missing = 'drop').fit()
print reg.summary()

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

ls_pd_disp = ['nb_obs',
              'price_1', 'price_2',
              'price_1_freq', 'price_2_freq', 'price_12_freq']

# One period (need product to be available in this one)
df_qlmc_prod_per = df_qlmc_prod[df_qlmc_prod['Period'] == 1]
df_pd =  df_qlmc_prod_per[['Price', 'Enseigne_alt']]\
           .groupby('Enseigne_alt').agg([nb_obs,
                                         price_1,
                                         price_1_freq,
                                         price_2,
                                         price_2_freq])['Price']
df_pd.sort('nb_obs', ascending = False, inplace = True)
df_pd['price_12_freq'] = df_pd[['price_1_freq', 'price_2_freq']].sum(axis = 1)

print u'\nOverview most frequent prices by retail chain in period 1:'
print df_pd[ls_pd_disp].to_string()

# All periods
df_pd_2 =  df_qlmc_prod[['Period', 'Price', 'Enseigne_alt']]\
             .groupby(['Period', 'Enseigne_alt']).agg([nb_obs,
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

df_pd_2_final = df_pd_2[df_pd_2['nb_obs'] >= 10].copy()

print u'\nOverview most frequent prices by retail chain and period:'
print u'(Single product, only if >= 20 obs within period)'
print df_pd_2_final[ls_pd_disp].to_string()

# Extract by chain

df_pd_2_final.sortlevel(inplace = True)

retail_chain = 'CENTRE E.LECLERC'
print u'\nOverview most frequent prices among {:s} stores by period:'.format(retail_chain)
print u'(Single product, only if >= 20 obs within period)'
print df_pd_2_final.loc[(slice(None), retail_chain),:][ls_pd_disp].to_string()

# Todo: Expand 
# => over products if can be
# => baskets of good (by period / chain given product scarcity)

# For one chain within period, if no need to take same store sample:

retail_chain = 'CENTRE E.LECLERC'

df_sub = df_qlmc[(df_qlmc['Period'] == 1) &\
                 (df_qlmc['Enseigne_alt'] == retail_chain)]
ls_sub_top_prods = df_sub['Product'].value_counts().index[0:20].tolist()
df_sub = df_sub[df_sub['Product'].isin(ls_sub_top_prods)]

df_pd_3 =  df_sub[['Price', 'Product']]\
             .groupby(['Product']).agg([nb_obs,
                                        price_1,
                                        price_1_freq,
                                        price_2,
                                        price_2_freq])['Price']
df_pd_3['price_12_freq'] = df_pd_3[['price_1_freq', 'price_2_freq']].sum(axis = 1)

print u'\nOverview most freq. prices among {:s} stores by product:'.format(retail_chain)
print u'(Top 20 avail. products and in period 1)'
print df_pd_3[ls_pd_disp].to_string()

# Todo: 
# for one chain: one row by period (could add by dpt)
# price distribution for each unique product (rayon/famille/prod)
# take avg of first freq and second freq (could take interquartile gap etc)
# keep only if enough products
