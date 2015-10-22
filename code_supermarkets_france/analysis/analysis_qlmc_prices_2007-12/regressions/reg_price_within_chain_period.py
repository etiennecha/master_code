#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

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

# LOAD DF QLMC

print u'Loading df_qlmc'
df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      dtype = {'id_lsa' : str,
                               'INSEE_ZIP' : str,
                               'INSEE_Code' : str},
                      encoding = 'utf-8')

# LOAD DF COMP

print u'Loading df_comp'
#'df_comp_H_ac_vs_cont.csv'),
df_comp_h = pd.read_csv(os.path.join(path_built_lsa_csv,
                                     '201407_competition',
                                     'df_store_prospect_comp_H_v_all.csv'),
                        dtype = {'Ident': str},
                        encoding = 'utf-8')

#'df_comp_S_ac_vs_cont.csv'),
df_comp_s = pd.read_csv(os.path.join(path_built_lsa_csv,
                                     '201407_competition',
                                     'df_store_prospect_comp_S_v_all.csv'), 
                        dtype = {'Ident': str},
                        encoding = 'utf-8')

df_comp = pd.concat([df_comp_h, df_comp_s],
                    axis = 0,
                    ignore_index = True)

ls_lsa_info_cols = [u'Surface',
                    u'Nb_Caisses',
                    u'Nb_Emplois',
                    u'Nb_Parking',
                    u'Int_Ind',
                    u'Groupe',
                    u'Groupe_Alt',
                    u'Enseigne_Alt',
                    u'Type_Alt']

ls_lsa_comp_cols = ['ac_nb_stores',
                    'ac_nb_comp',
                    'ac_store_share',
                    'ac_group_share',
                    'ac_hhi',
                    'dist_cl_comp',
                    'dist_cl_groupe',
                    'hhi',
                    'store_share',
                    'group_share',
                    'Reg'] # should not need to add it here

df_qlmc = pd.merge(df_qlmc,
                   df_comp[['Ident'] +\
                           ls_lsa_info_cols +\
                           ls_lsa_comp_cols],
                   left_on = 'id_lsa',
                   right_on = 'Ident',
                   how = 'left')

# Get rid of no id_lsa match
df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]
# Get rid of closed (so far but should accomodate later)
df_qlmc = df_qlmc[~df_qlmc['Enseigne_Alt'].isnull()]
# Avoid error msg on condition number
df_qlmc['Surface'] = df_qlmc['Surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_Price'] = np.log(df_qlmc['Price'])
# Control for dpt (region?)
df_qlmc['Dpt'] = df_qlmc['INSEE_Code'].str.slice(stop = 2)

# ############
# REGRESSIONS
# ############

df_qlmc = df_qlmc[(df_qlmc['Period'] == 1) &\
                  (df_qlmc['Enseigne_Alt'] == 'AUCHAN')]

se_prod = df_qlmc.groupby(['Family', 'Subfamily', 'Product']).agg('size')
se_prod.sort(ascending = False, inplace = True)

# WITH ONE PRODUCT
rayon, famille, produit = se_prod.index[0]
df_qlmc_prod = df_qlmc[(df_qlmc['Family'] == rayon) &\
                       (df_qlmc['Subfamily'] == famille) &\
                       (df_qlmc['Product'] == produit)].copy()

print u'\nRegression of price of {:s}'.format(produit)
reg = smf.ols('Price ~ Surface + ac_hhi + C(Reg)',
              data = df_qlmc_prod,
              missing = 'drop').fit()
print reg.summary()

print u'\nRegression of log price of {:s}'.format(produit)
reg = smf.ols('ln_Price ~ Surface + ac_hhi + C(Reg)',
              data = df_qlmc_prod,
              missing = 'drop').fit()
print reg.summary()

# Pbm: one or a few ref prices (per brand)... so reg is not very meaningful
# More convincing with store FE? set of products? 
# Do with LECLERC products?

# WITH TOP 100 PRODUCTS
ls_top_prod = [x[-1] for x in se_prod.index[0:200]]
df_qlmc_prods = df_qlmc[df_qlmc['Product'].isin(ls_top_prod)].copy()

print u'\nRegression of price of top 20 products (avail in data)'
reg = smf.ols('Price ~ C(Product) + Surface + hhi + C(Reg)',
              data = df_qlmc_prods,
              missing = 'drop').fit()
print reg.summary()

print u'\nRegression of log price of top 20 products (avail in data)'
reg = smf.ols('ln_Price ~ C(Product) + Surface + hhi + C(Reg)',
              data = df_qlmc_prods,
              missing = 'drop').fit()
print reg.summary()

print u'\nBuild market power variable (dummy so far)'
print df_qlmc_prods[['ac_hhi', 'ac_group_share']].describe()
df_qlmc_prods['dum_mp'] = 0
df_qlmc_prods.loc[(df_qlmc_prods['hhi'] >= df_qlmc_prods['hhi'].quantile(0.75)) &\
                  (df_qlmc_prods['group_share'] >=\
                     df_qlmc_prods['group_share'].quantile(0.75)),
                  'dum_mp'] = 1

# todo: endogenize
print df_qlmc_prods['dum_mp'].describe()

reg = smf.ols('ln_Price ~ C(Product) + Surface + dum_mp + C(Reg)',
              data = df_qlmc_prods,
              missing = 'drop').fit()
print reg.summary()

## try: control by region or biggests UUs but few stores for most brands
#df_qlmc[df_qlmc['Product'] == u'Coca Cola - Coca Cola IVP avec caf\xe9ine - 8x25cl']\
#  .plot(kind = 'Scatter', x = 'Surface', y = 'Price')

## #############################################
## PRICE DISTRIBUTION PER CHAIN FOR TOP PRODUCTS
## #############################################
#
#def nb_obs(se_prices):
#  return len(se_prices)
#
#def price_1(se_prices):
#  return se_prices.value_counts().index[0]
#
#def price_1_freq(se_prices):
#  return se_prices.value_counts().iloc[0] / float(len(se_prices))
#
#def price_2(se_prices):
#  if len(se_prices.value_counts()) > 1:
#    return se_prices.value_counts().index[1]
#  else:
#    return np.nan
#
#def price_2_freq(se_prices):
#  if len(se_prices.value_counts()) > 1:
#    return se_prices.value_counts().iloc[1] / float(len(se_prices))
#  else:
#    return 0
#
#ls_pd_disp = ['nb_obs',
#              'price_1', 'price_2',
#              'price_1_freq', 'price_2_freq', 'price_12_freq']
#
## One period (need product to be available in this one)
#df_qlmc_prod_per = df_qlmc_prod[df_qlmc_prod['Period'] == 1]
#df_pd =  df_qlmc_prod_per[['Price', 'Enseigne_Alt']]\
#           .groupby('Enseigne_Alt').agg([nb_obs,
#                                         price_1,
#                                         price_1_freq,
#                                         price_2,
#                                         price_2_freq])['Price']
#df_pd.sort('nb_obs', ascending = False, inplace = True)
#df_pd['price_12_freq'] = df_pd[['price_1_freq', 'price_2_freq']].sum(axis = 1)
#
#print u'\nOverview most frequent prices by retail chain in period 1:'
#print df_pd[ls_pd_disp].to_string()
#
## All periods
#df_pd_2 =  df_qlmc_prod[['Period', 'Price', 'Enseigne_Alt']]\
#             .groupby(['Period', 'Enseigne_Alt']).agg([nb_obs,
#                                                       price_1,
#                                                       price_1_freq,
#                                                       price_2,
#                                                       price_2_freq])['Price']
#
## Sort by nb of obs within each period             
#df_pd_2.reset_index('Period', drop = False, inplace = True)
#df_pd_2.sort(['Period', 'nb_obs'], ascending = False, inplace = True)
#df_pd_2.set_index('Period', append = True, inplace = True)
#df_pd_2 = df_pd_2.swaplevel(0, 1, axis = 0)
#df_pd_2['price_12_freq'] = df_pd_2[['price_1_freq', 'price_2_freq']].sum(axis = 1)
#
#df_pd_2_final = df_pd_2[df_pd_2['nb_obs'] >= 10].copy()
#
#print u'\nOverview most frequent prices by retail chain and period:'
#print u'(Single product, only if >= 20 obs within period)'
#print df_pd_2_final[ls_pd_disp].to_string()
#
## Extract by chain
#
#df_pd_2_final.sortlevel(inplace = True)
#
#retail_chain = 'CENTRE E.LECLERC'
#print u'\nOverview most frequent prices among {:s} stores by period:'.format(retail_chain)
#print u'(Single product, only if >= 20 obs within period)'
#print df_pd_2_final.loc[(slice(None), retail_chain),:][ls_pd_disp].to_string()
#
## Todo: Expand 
## => over products if can be
## => baskets of good (by period / chain given product scarcity)
#
## For one chain within period, if no need to take same store sample:
#
#retail_chain = 'CENTRE E.LECLERC'
#
#df_sub = df_qlmc[(df_qlmc['Period'] == 1) &\
#                 (df_qlmc['Enseigne_Alt'] == retail_chain)]
#ls_sub_top_prods = df_sub['Product'].value_counts().index[0:20].tolist()
#df_sub = df_sub[df_sub['Product'].isin(ls_sub_top_prods)]
#
#df_pd_3 =  df_sub[['Price', 'Product']]\
#             .groupby(['Product']).agg([nb_obs,
#                                        price_1,
#                                        price_1_freq,
#                                        price_2,
#                                        price_2_freq])['Price']
#df_pd_3['price_12_freq'] = df_pd_3[['price_1_freq', 'price_2_freq']].sum(axis = 1)
#
#print u'\nOverview most freq. prices among {:s} stores by product:'.format(retail_chain)
#print u'(Top 20 avail. products and in period 1)'
#print df_pd_3[ls_pd_disp].to_string()
#
## Todo: 
## for one chain: one row by period (could add by dpt)
## price distribution for each unique product (rayon/famille/prod)
## take avg of first freq and second freq (could take interquartile gap etc)
## keep only if enough products
