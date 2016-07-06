#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import re
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

path_built_lsa_comp_csv = os.path.join(path_built_lsa_csv,
                                       '201407_competition')

path_insee_extracts = os.path.join(path_data,
                                   'data_insee',
                                   'data_extracts')

# #############
# LOAD DATA
# #############

# LOAD PRICES
df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

# LOAD QLMC STORE DATA
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str},
                        encoding = 'utf-8')

# HARMONZATION OF CHAINS
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

# LOAD LSA STORE DATA
df_lsa = pd.read_csv(os.path.join(path_built_lsa_csv,
                                  'df_lsa_active_hsx.csv'),
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

# LOAD COMPETITION
ls_comp_files = ['df_store_prospect_comp_HS_v_all_10km.csv',
                 'df_store_prospect_comp_HS_v_all_20km.csv',
                 'df_store_prospect_comp_HS_v_all_1025km.csv']
df_comp = pd.read_csv(os.path.join(path_built_lsa_comp_csv,
                                   ls_comp_files[1]),
                      dtype = {'id_lsa' : str},
                      encoding = 'utf-8')

# LOAD DEMAND
df_demand = pd.read_csv(os.path.join(path_built_lsa_comp_csv,
                                     'df_store_prospect_demand.csv'),
                        dtype = {'id_lsa' : str},
                        encoding = 'utf-8')

# LOAD REVENUE (would be better to dedicate a script)
df_insee_areas = pd.read_csv(os.path.join(path_insee_extracts,
                                          u'df_insee_areas.csv'),
                             encoding = 'UTF-8')

## add municipality revenue
#df_com = pd.read_csv(os.path.join(path_insee_extracts,
#                                  'data_insee_extract.csv'),
#                     encoding = 'UTF-8')

# add AU revenue
df_au_agg = pd.read_csv(os.path.join(path_insee_extracts,
                                     u'df_au_agg_final.csv'),
                        encoding = 'UTF-8')
df_au_agg['med_rev_au'] = df_au_agg['QUAR2UC10']
df_insee_areas = pd.merge(df_insee_areas,
                          df_au_agg[['AU2010', 'med_rev_au']],
                          left_on = 'AU2010',
                          right_on = 'AU2010')

# add UU revenue
df_uu_agg = pd.read_csv(os.path.join(path_insee_extracts,
                                     u'df_uu_agg_final.csv'),
                        encoding = 'UTF-8')
df_uu_agg['med_rev_uu'] = df_uu_agg['QUAR2UC10']
df_insee_areas = pd.merge(df_insee_areas,
                          df_uu_agg[['UU2010', 'med_rev_uu']],
                          left_on = 'UU2010',
                          right_on = 'UU2010')

# MERGE DATA
df_lsa = pd.merge(df_lsa,
                  df_comp,
                  on = 'id_lsa',
                  how = 'left')

df_lsa = pd.merge(df_lsa,
                  df_demand,
                  on = 'id_lsa',
                  how = 'left')

df_lsa = pd.merge(df_lsa,
                  df_insee_areas[['CODGEO', 'med_rev_au', 'med_rev_uu']],
                  left_on = 'c_insee',
                  right_on = 'CODGEO',
                  how = 'left')

ls_lsa_cols = ['id_lsa',
               'region', # robustness check: exclude Ile-de-France
               'surface',
               'nb_caisses',
               'nb_emplois'] +\
               list(df_comp.columns[1:]) +\
               list(df_demand.columns[1:]) +\
               ['med_rev_au', 'med_rev_uu']

df_stores = pd.merge(df_stores,
                     df_lsa[ls_lsa_cols],
                     on = 'id_lsa',
                     how = 'left')

df_prices.drop('store_chain', axis = 1, inplace = True)

df_qlmc = pd.merge(df_prices,
                   df_stores,
                   on = ['store_id'],
                   how = 'left')

# Avoid error msg on condition number
df_qlmc['surface'] = df_qlmc['surface'].apply(lambda x: x/1000.0)
#df_qlmc['ac_hhi'] = df_qlmc['ac_hhi'] * 10000
#df_qlmc['hhi'] = df_qlmc['hhi'] * 10000

# Build log variables
for col in ['price', 'surface', 'hhi', 'ac_hhi',
            'med_rev_uu', 'med_rev_au',
            'pop_cont_10', 'pop_ac_10km', 'pop_ac_20km']:
  df_qlmc['ln_{:s}'.format(col)] = np.log(df_qlmc[col])

# Create dummy high hhi
df_qlmc['dum_high_hhi'] = 0
df_qlmc.loc[df_qlmc['hhi'] >= 0.20, 'dum_high_hhi'] = 1

# Filter out some observations

# Exclude Ile-de-France as robustness check
df_qlmc = df_qlmc[df_qlmc['region'] != u'Ile-de-France']

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
#print df_qlmc[['nb_prod_obs', 'nb_store_obs']].describe()

# ###############################
# RESTRICTIONS ON PRODUCTS/STORES
# ###############################

# drop chain(s) with too few stores
df_qlmc = df_qlmc[~(df_qlmc['qlmc_chain'].isin(['SUPERMARCHE MATCH',
                                                'ATAC',
                                                'MIGROS',
                                                'RECORD',
                                                'G 20']))]

## keep only if products observed w/in at least 1000 stores (or more: memory..)
#df_qlmc['nb_prod_obs'] =\
#  df_qlmc.groupby('product')['product'].transform(len).astype(int)
#df_qlmc = df_qlmc[df_qlmc['nb_prod_obs'] >= 1000]
#
## keep only stores w/ at least 400 products
#df_qlmc['nb_store_obs'] =\
# df_qlmc.groupby('store_id')['store_id'].transform(len).astype(int)
#df_qlmc = df_qlmc[df_qlmc['nb_store_obs'] >= 400]
#
## count product obs again
#df_qlmc['nb_prod_obs'] =\
#  df_qlmc.groupby('product')['product'].transform(len).astype(int)
#
#print df_qlmc[['nb_prod_obs', 'nb_store_obs']].describe()

# generate log price deviation to prod mean price
df_qlmc['log_pd'] = np.log(df_qlmc['price'] /\
                      df_qlmc.groupby('product')['price'].transform('mean'))

## can also use log price deviation to prod region price
#df_prices = df_prices[~df_prices['region'].isnull()]
#df_prices['ln_pd'] = np.log(df_prices['price'] /\
#                      df_prices.groupby(['product', 'region'])['price'].transform('mean'))
#df_prices = df_prices[~df_prices['ln_pd'].isnull()]

# pbm with patsy with python 2.7.10? update or use python2.7.6
res_a = smf.ols("log_pd ~ C(qlmc_chain, Treatment(reference='LECLERC'))",
                data = df_qlmc).fit()
print res_a.summary()
#rob_cov_a = sm.stats.sandwich_covariance.cov_hc0(res_a)
# todo: cluster std errors by store and/or product?

dict_vars = {'chains' : "C(qlmc_chain, Treatment(reference = 'LECLERC'))",
             'region' : "C(region)"}

ls_exo = [[dict_vars['chains']],
          [dict_vars['chains'], 'surface', 'hhi'],
          [dict_vars['chains'], 'surface', 'ac_hhi'],
          [dict_vars['chains'], 'surface', 'hhi', 'ln_med_rev_au'],
          [dict_vars['chains'], 'surface', 'hhi', 'ln_med_rev_au', 'ln_pop_cont_10'],
          [dict_vars['chains'], 'surface', 'ac_hhi', 'ln_med_rev_uu', 'ln_pop_ac_10km'],
          [dict_vars['chains'], dict_vars['region'],
           'surface', 'hhi', 'ln_med_rev_au', 'ln_pop_cont_10'],
          ['surface', 'hhi', 'ln_med_rev_au', 'ln_pop_cont_10']]

ls_formulas = ["log_pd ~ " + " + ".join(exo) for exo in ls_exo]

ls_res = []
for formula in ls_formulas:
  print ''
  print formula
  res = smf.ols(formula, data = df_qlmc).fit()
  ls_res.append(res)
  print res.summary()

ls_se_res = [res.params for res in ls_res]
df_params = pd.concat(ls_se_res, axis = 1)

df_params_2 = df_params[(~pd.Series(df_params.index)\
                            .str.contains('region')).values].copy()

df_params_2.index = [re.search('C\(region\)\[T\.(.*?)\]', x).group(1)\
                       if re.search('C\(region\)\[T\.(.*?)\]', x)
                       else x for x in df_params_2.index]

print ''
for i, formula in enumerate(ls_formulas):
	print i, formula

print df_params_2.to_string()
