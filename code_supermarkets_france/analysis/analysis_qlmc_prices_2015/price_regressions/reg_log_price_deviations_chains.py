#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import timeit
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import scipy
from patsy import dmatrix, dmatrices
from scipy.sparse import csr_matrix

pd.set_option('float_format', '{:,.3f}'.format)

format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

# #############
# LOAD DATA
# #############

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

# Add store chars / environement
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        encoding = 'utf-8')

# Add qlmc_chain
ls_ls_enseigne_lsa_to_qlmc = [[['CENTRE E.LECLERC'], 'LECLERC'],
                              [['GEANT CASINO'], 'GEANT'],
                              [['HYPER CASINO'], 'CASINO'],
                              [['INTERMARCHE SUPER',
                                'INTERMARCHE HYPER',
                                'INTERMARCHE CONTACT'], 'INTERMARCHE'],
                              [['HYPER U',
                                'SUPER U',
                                'U EXPRESS'], 'SYSTEME U'],
                              [['MARKET'], 'CARREFOUR MARKET'],
                              [["LES HALLES D'AUCHAN"], 'AUCHAN']]

df_stores['qlmc_chain'] = df_stores['store_chain']
for ls_enseigne_lsa_to_qlmc in ls_ls_enseigne_lsa_to_qlmc:
  df_stores.loc[df_stores['store_chain'].isin(ls_enseigne_lsa_to_qlmc[0]),
              'qlmc_chain'] = ls_enseigne_lsa_to_qlmc[1]

# LOAD STORE COMPETITION (todo: aggregate elsewhere)

df_comp_h = pd.read_csv(os.path.join(path_built_lsa_csv,
                                     '201407_competition',
                                     'df_store_prospect_comp_H_v_all.csv'),
                        encoding = 'utf-8')

df_comp_s = pd.read_csv(os.path.join(path_built_lsa_csv,
                                     '201407_competition',
                                     'df_store_prospect_comp_S_v_all.csv'), 
                        encoding = 'utf-8')

df_comp = pd.concat([df_comp_h, df_comp_s],
                    axis = 0,
                    ignore_index = True)

ls_lsa_info_cols = [u'surface',
                    u'nb_caisses',
                    u'nb_emplois',
                    u'nb_parking',
                    u'int_ind',
                    u'groupe',
                    u'groupe_alt',
                    u'enseigne_alt',
                    u'type_alt']

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
                    'c_departement',
                    'region']

df_stores = pd.merge(df_stores,
                     df_comp[['id_lsa'] +\
                             ls_lsa_info_cols +\
                             ls_lsa_comp_cols],
                     left_on = 'id_lsa',
                     right_on = 'id_lsa',
                     how = 'left')

# LOAD STORE DEMAND

df_demand_h = pd.read_csv(os.path.join(path_built_lsa_csv,
                                     '201407_competition',
                                     'df_store_prospect_demand_H.csv'),
                        encoding = 'utf-8')

df_demand_s = pd.read_csv(os.path.join(path_built_lsa_csv,
                                       '201407_competition',
                                       'df_store_prospect_comp_S_v_all.csv'), 
                        encoding = 'utf-8')

df_demand = pd.concat([df_demand_h, df_demand_s],
                      axis = 0,
                      ignore_index = True)

df_stores = pd.merge(df_stores,
                     df_demand[['id_lsa', 'pop', 'ac_pop']],
                     left_on = 'id_lsa',
                     right_on = 'id_lsa',
                     how = 'left')

# Merge store chars and prices

print len(df_prices)

# drop redundant columns
df_prices.drop(['store_chain'], axis = 1, inplace = True)
df_qlmc = pd.merge(df_prices,
                   df_stores,
                   how = 'left',
                   on = 'store_id')

print len(df_qlmc)

# Avoid error msg on condition number
df_qlmc['surface'] = df_qlmc['surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_price'] = np.log(df_qlmc['price'])

# ###############################
# RESTRICTIONS ON PRODUCTS/STORES
# ###############################

# drop chain(s) with too few stores
df_qlmc = df_qlmc[~(df_qlmc['qlmc_chain'].isin(['SUPERMARCHE MATCH',
                                                'ATAC',
                                                'MIGROS',
                                                'RECORD',
                                                'G 20']))]

# keep only if products observed w/in at least 1000 stores (or more: memory..)
df_qlmc['nb_prod_obs'] =\
  df_qlmc.groupby('product')['product'].transform(len).astype(int)
df_qlmc = df_qlmc[df_qlmc['nb_prod_obs'] >= 1000]

# keep only stores w/ at least 400 products
df_qlmc['nb_store_obs'] =\
 df_qlmc.groupby('store_id')['store_id'].transform(len).astype(int)
df_qlmc = df_qlmc[df_qlmc['nb_store_obs'] >= 400]

# count product obs again
df_qlmc['nb_prod_obs'] =\
  df_qlmc.groupby('product')['product'].transform(len).astype(int)

print df_qlmc[['nb_prod_obs', 'nb_store_obs']].describe()

# PRICE LEVEL

# generate log price deviation
df_qlmc['log_pd'] = np.log(df_qlmc['price'] /\
                      df_qlmc.groupby('product')['price'].transform('mean'))

# pbm with patsy with python 2.7.10? update or use python2.7.6
res_a = smf.ols("log_pd ~ C(qlmc_chain, Treatment(reference='LECLERC'))",
                data = df_qlmc).fit()
print res_a.summary()
#rob_cov_a = sm.stats.sandwich_covariance.cov_hc0(res_a)

res_b = smf.ols("log_pd ~ C(section) + surface + ac_hhi + " +\
                "C(qlmc_chain, Treatment(reference = 'LECLERC'))",
                data = df_qlmc).fit()
print res_b.summary()
# todo: cluster std errors by store and/or product?

# PRIE DISPERSION

# generate national prod price deviation
df_qlmc['cv'] = df_qlmc.groupby('product')['price'].transform('std') /\
                  df_qlmc.groupby('product')['price'].transform('mean')

df_qlmc['range'] = df_qlmc.groupby('product')['price'].transform('max') -\
                  df_qlmc.groupby('product')['price'].transform('in')


df_disp = df_qlmc.drop_duplicates('product')

res_c = smf.ols("cv ~ C(section, Treatment(reference = 'Frais'))", data = df_disp).fit()
print res_c.summary()

res_d = smf.ols("range ~ C(section, Treatment(reference = 'Frais'))", data = df_disp).fit()
print res_c.summary()
