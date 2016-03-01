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
from sklearn.feature_extraction import DictVectorizer

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
                                   ls_comp_files[0]),
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

# Filter out some observations...

# Exclude Ile-de-France as robustness check
df_qlmc = df_qlmc[df_qlmc['region'] != u'Ile-de-France']

ls_suspicious_prods = ['VIVA LAIT TGV 1/2 ÉCRÉMÉ VIVA BP 6X50CL']
df_qlmc = df_qlmc[~df_qlmc['product'].isin(ls_suspicious_prods)]

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

## ##############
## REGRESSION
## ##############
#
#price_col = 'ln_pd'
#
#df_qlmc['intercept'] = 'intercept'
#pd_as_dicts = [dict(r.iteritems())\
#                 for _, r in df_qlmc[['store_id', 'intercept']].iterrows()]
##pd_as_dicts_2 = [dict(dict_temp.items() + [('intercept', 'intercept')])\
##                   for dict_temp in pd_as_dicts]
#ref = u'centre-e-leclerc-les-angles' # ref = pd_as_dicts[0]['store_id']
#pd_as_dicts_2 = [dict_temp if dict_temp['store_id'] != ref \
#                     else {'intercept' : 'intercept'} for dict_temp in pd_as_dicts]
#
#sparse_mat_prod_store = DictVectorizer(sparse=True).fit_transform(pd_as_dicts_2)
#res_01 = scipy.sparse.linalg.lsqr(sparse_mat_prod_store,
#                                  df_qlmc[price_col].values,
#                                  iter_lim = 100,
#                                  calc_var = True)
#nb_fd_01 = len(df_qlmc) - len(res_01[0])
#ar_std_01 = np.sqrt(res_01[3]**2/nb_fd_01 * res_01[9])
#ls_stores = sorted(df_qlmc['store_id'].copy().drop_duplicates().values)
#
## Compute rsquare
#y_hat = sparse_mat_prod_store * res_01[0]
#df_qlmc['yhat'] = y_hat
#df_qlmc['residual'] = df_qlmc[price_col] - df_qlmc['yhat'] 
#rsquare = 1 - ((df_qlmc[price_col] - df_qlmc['yhat'])**2).sum() /\
#                ((df_qlmc[price_col] - df_qlmc[price_col].mean())**2).sum()
#ls_stores.remove(ref)
#
#ls_rows_01 = zip(ls_stores, res_01[0], ar_std_01)
#df_res_01 = pd.DataFrame(ls_rows_01, columns = ['Name', 'Coeff', 'Std'])
#df_res_01['t_stat'] = df_res_01['Coeff'] / df_res_01['Std']
#df_stores_fe = df_res_01.copy()
#
## Analyse store FEs
#df_stores.set_index('store_id', inplace = True)
#df_stores_fe.set_index('Name', inplace = True)
#df_stores = pd.merge(df_stores,
#                     df_stores_fe,
#                     left_index = True,
#                     right_index = True,
#                     how = 'left')
## check syntax update in pandas 0.17
#df_chains_su = df_stores.groupby('qlmc_chain')['Coeff']\
#                        .agg('describe').reset_index()\
#                        .pivot(index='qlmc_chain',
#                               values=0,
#                               columns='level_1')
#df_chains_su = df_chains_su[df_chains_su['count'] >= 10]
#lsddesc = ['count', 'mean', 'std', 'min', '25%', '50%', '75%', 'max']
#print df_chains_su[lsddesc].to_string()

# #########################
# REGRESSION: PATSY DUMMIES
# #########################

price_col = 'ln_price'

# create df to convert to sparse (use df_qlmc.index: not 0 to nobs)
df_i = pd.DataFrame('intercept',
                    columns = ['col'],
                    index = df_qlmc.index)
df_i.index.name = 'row'

df_0 = df_qlmc[['product']].copy()
df_0.index.name = 'row'
df_0.rename(columns = {'product': 'col'}, inplace = True)

df_2 = pd.concat([df_i, df_0], axis = 0)

# omit one category for each categorical variable (reference)
# a priori can simply drop row if there is an intercept (mat row created)
df_2['val'] = 1
ref_id = df_qlmc['product'].iloc[0]
ls_refs = [ref_id]
for ref in ls_refs:
  df_2 = df_2[~(df_2['col'] == ref)]
df_2.set_index('col', append = True, inplace = True)

# add variables which are not dummies: need to append multiindex df
ls_df_3 = []
for var in ['surface', 'hhi', 'ln_med_rev_au', 'ln_pop_cont_10']:
  df_3 = pd.DataFrame(df_qlmc[var].values,
                      columns = ['val'],
                      index = df_qlmc.index)
  df_3.index.name = 'row'
  df_3['col'] = var
  df_3.set_index('col', append = True, inplace = True)
  ls_df_3.append(df_3)

# concat dfs
df_2 = pd.concat([df_2] + ls_df_3, axis = 0)

# build sparse matrix
s = pd.Series(df_2['val'].values)
s.index = df_2.index
ss = s.to_sparse()
A, rows, columns = ss.to_coo(row_levels=['row'],
                             column_levels = ['col'],
                             sort_labels = True)
y = df_qlmc[price_col].values
param_names = columns
res = scipy.sparse.linalg.lsqr(A,
                               y,
                               iter_lim = 100,
                               calc_var = True)
param_values = res[0]
nb_freedom_degrees = len(df_qlmc) - len(res[0])
param_se = np.sqrt(res[3]**2/nb_freedom_degrees * res[9])
df_reg = pd.DataFrame(zip(param_names,
                          param_values,
                          param_se), columns = ['name', 'coeff', 'bse'])
df_reg['tstat'] = df_reg['coeff'] / df_reg['bse']
# Compute rsquare
y_hat = A * res[0]
df_qlmc['yhat'] = y_hat
df_qlmc['residual'] = df_qlmc[price_col] - df_qlmc['yhat'] 
rsquare = 1 - ((df_qlmc[price_col] - df_qlmc['yhat'])**2).sum() /\
                ((df_qlmc[price_col] - df_qlmc[price_col].mean())**2).sum()
