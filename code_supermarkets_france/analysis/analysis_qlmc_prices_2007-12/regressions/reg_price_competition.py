#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
#path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

pd.set_option('float_format', '{:,.2f}'.format)

# #######################
# BUILD DF QLMC
# ####################### 

# LOAD DF PRICES
print u'Loading qlmc prices'
# date parsing slow... better if specified format?
df_qlmc = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_qlmc_prices.csv'),
                      encoding = 'utf-8')

# LOAD DF STORES
print u'Loading qlmc stores (inc. LSA id)'
df_stores = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_qlmc_stores.csv'),
                        dtype = {'id_lsa': str,
                                 'INSE_ZIP' : str,
                                 'INSEE_Dpt' : str,
                                 'INSEE_Code' : str,
                                 'QLMC_Dpt' : str},
                        encoding = 'UTF-8')
df_stores['Magasin'] = df_stores['Enseigne'] + u' ' + df_stores['Commune']
df_stores = df_stores[['P', 'Magasin', 'Enseigne', 'id_lsa',
                       'INSEE_Code', 'INSEE_Commune']]

# LOAD DF COMP

df_comp_h = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_comp_H_ac_vs_cont.csv'),
                        dtype = {'Ident': str},
                        encoding = 'latin-1')

df_comp_s = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_comp_S_ac_vs_cont.csv'),
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

ls_lsa_comp_cols = ['ac_nb_store',
                    'ac_nb_comp',
                    'ac_store_share',
                    'ac_group_share',
                    'ac_hhi']

df_stores = pd.merge(df_stores,
                     df_comp[['id_lsa'] +\
                             ls_lsa_info_cols +\
                             ls_lsa_comp_cols],
                     on = 'id_lsa',
                     how = 'left')

# ######################################
# REG MOST COMMON PRODUCT PRICES ON COMP
# ######################################

df_qlmc = pd.merge(df_qlmc,
                   df_stores,
                   on = ['P', 'Magasin'],
                   how = 'left')

df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]

se_prod = df_qlmc.groupby(['Rayon', 'Famille', 'Produit']).agg('size')
se_prod.sort(ascending = False, inplace = True)

# Aavoid error msg on condition number
df_qlmc['Surface'] = df_qlmc['Surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_Prix'] = np.log(df_qlmc['Prix'])
# Control for dpt (region?)
df_qlmc['Dpt'] = df_qlmc['INSEE_Code'].str.slice(stop = 2)

# WITH ONE PRODUCT
rayon, famille, produit = se_prod.index[0]
df_qlmc_prod = df_qlmc[(df_qlmc['Rayon'] == rayon) &\
                       (df_qlmc['Famille'] == famille) &\
                       (df_qlmc['Produit'] == produit)].copy()

reg = smf.ols('Prix ~ C(P) + Surface + Groupe_alt + ac_hhi',
              data = df_qlmc_prod[df_qlmc_prod['Type_alt'] == 'H'],
              missing = 'drop').fit()
print reg.summary()

# Pbm: one or a few ref prices (per brand)... so reg is not very meaningful
# More convincing with store FE? set of products? 
# Do with LECLERC products?

# WITH TOP 20 PRODUCTS
ls_top_prod = [x[-1] for x in se_prod.index[0:20]]
df_qlmc_prods = df_qlmc[df_qlmc['Produit'].isin(ls_top_prod)].copy()

reg = smf.ols('Prix ~ C(P) + C(Produit) + Surface + Groupe_alt + ac_hhi',
              data = df_qlmc_prods[df_qlmc_prods['Type_alt'] == 'H'],
              missing = 'drop').fit()
print reg.summary()


reg = smf.ols('ln_Prix ~ C(P) + C(Produit) + Surface + Groupe_alt + ac_hhi',
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

# One period (need product to be available in this one)
df_qlmc_prod_per = df_qlmc_prod[df_qlmc_prod['P'] == 1]
df_pd =  df_qlmc_prod_per[['Prix', 'Enseigne_alt']]\
           .groupby('Enseigne_alt').agg([nb_obs,
                                         price_1,
                                         price_1_freq,
                                         price_2,
                                         price_2_freq])['Prix']
df_pd.sort('nb_obs', ascending = False, inplace = True)
df_pd['price_12_freq'] = df_pd[['price_1_freq', 'price_2_freq']].sum(axis = 1)
print df_pd.to_string()

# All periods
df_pd_2 =  df_qlmc_prod[['P', 'Prix', 'Enseigne_alt']]\
             .groupby(['P', 'Enseigne_alt']).agg([nb_obs,
                                                  price_1,
                                                  price_1_freq,
                                                  price_2,
                                                  price_2_freq])['Prix']

# Sort by nb of obs within each period             
df_pd_2.reset_index('P', drop = False, inplace = True)
df_pd_2.sort(['P', 'nb_obs'], ascending = False, inplace = True)
df_pd_2.set_index('P', append = True, inplace = True)
df_pd_2 = df_pd_2.swaplevel(0, 1, axis = 0)
df_pd_2['price_12_freq'] = df_pd_2[['price_1_freq', 'price_2_freq']].sum(axis = 1)
print df_pd_2[df_pd_2['nb_obs'] >= 10].to_string()

# Extract by chain
df_pd_2.sortlevel(inplace = True)
print df_pd_2.loc[(slice(None), 'CENTRE E.LECLERC'),:]

# Todo: Expand 
# => over products if can be
# => baskets of good (by period / chain given product scarcity)

# For one chain within period, if no need to take same store sample:
df_sub = df_qlmc[(df_qlmc['P'] == 0) &\
                 (df_qlmc['Enseigne_alt'] == 'CENTRE E.LECLERC')]
ls_sub_top_prods = df_sub['Produit'].value_counts().index[0:20].tolist()
df_sub = df_sub[df_sub['Produit'].isin(ls_sub_top_prods)]

df_pd_3 =  df_sub[['Prix', 'Produit']]\
             .groupby(['Produit']).agg([nb_obs,
                                        price_1,
                                        price_1_freq,
                                        price_2,
                                        price_2_freq])['Prix']
df_pd_3['price_12_freq'] = df_pd_3[['price_1_freq', 'price_2_freq']].sum(axis = 1)
