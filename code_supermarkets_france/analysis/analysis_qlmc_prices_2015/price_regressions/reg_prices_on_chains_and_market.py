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

pd.set_option('float_format', '{:,.2f}'.format)
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

pd.set_option('float_format', '{:,.2f}'.format)

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

# ###############
# REGRESSIONS
# ###############

# Regression:
# - Keep 100 most common products (and check by family)
# - Enseigne (as they are or LSA)
# - LSA vars + comp vars => in built file
# - INSEE vars => via IC/AU/UU/BV : try the 4 (hence need to add codes)

# Keep only top 100 products
se_vc_prod = df_qlmc['product'].value_counts()
ls_keep_prod = list(se_vc_prod[0:200].index)
df_qlmc_sub = df_qlmc[df_qlmc['product'].isin(ls_keep_prod)]

# Keep only largest store groups
ls_keep_enseigne_alt = ['CENTRE E.LECLERC',
                        'SUPER U',
                        'INTERMARCHE SUPER',
                        'CARREFOUR MARKET',
                        'AUCHAN',
                        'HYPER U',
                        'INTERMARCHE HYPER',
                        'CORA',
                        'CARREFOUR',
                        'GEANT CASINO']
df_qlmc_sub = df_qlmc_sub[df_qlmc_sub['enseigne_alt'].isin(ls_keep_enseigne_alt)]

## todo: check representation of section
print u'\nCheck section representation:'
print df_qlmc_sub[['section', 'product']]\
                 .drop_duplicates().groupby('section').agg(len)['product']

# representativeness of store sample
print u'\nCheck retail chain representation:'
se_ens_alt = df_qlmc_sub[['enseigne_alt', 'store_id']]\
                        .drop_duplicates()\
                        .groupby('enseigne_alt').agg(len)['store_id']
se_repr = se_ens_alt.div(df_comp['enseigne_alt'].value_counts().astype(float),
                         axis = 'index')
print se_repr[~pd.isnull(se_repr)]

print u'\nNo control:'
print smf.ols("ln_price ~ C(product) + " +\
              "C(enseigne_alt, Treatment(reference = 'CENTRE E.LECLERC'))",
              data = df_qlmc_sub).fit().summary()

print u'\nWith controls:'
print smf.ols("ln_price ~ C(product) + C(c_departement) + surface + hhi + pop + " +\
              "C(enseigne_alt, Treatment(reference = 'CENTRE E.LECLERC'))",
              data = df_qlmc_sub).fit().summary()

# Check nb products by store (todo: move)
se_nb_prod_by_store = df_qlmc[['store_id', 'product']]\
                             .groupby('store_id').agg(len)['product']
df_stores.set_index('store_id', inplace = True)
df_stores['nb_records'] = se_nb_prod_by_store

df_stores[df_stores['enseigne_alt'] != 'CENTRE E.LECLERC'].plot(kind = 'scatter',
                                                                x = 'surface',
                                                                y = 'nb_records')
