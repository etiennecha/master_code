#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
import os, sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import timeit
from statsmodels.iolib.summary2 import summary_col

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

path_built_lsa_comp_csv = os.path.join(path_built_lsa_csv,
                                       '201407_competition')

path_insee_extracts = os.path.join(path_data,
                                   'data_insee',
                                   'data_extracts')

# ############
# LOAD DATA
# ############

## LOAD QLMC PRICES
#df_prices = pd.read_csv(os.path.join(path_built_csv,
#                                     'df_prices_cleaned.csv'),
#                        encoding = 'utf-8')

# LOAD QLMC STORE DATA
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str,
                                 'c_insee' : str},
                        encoding = 'utf-8')

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

# LOAD FEs
price_col = 'ln_price'
df_fes = pd.read_csv(os.path.join(path_built_csv,
                     'df_res_{:s}_fes.csv'.format(price_col)),
                     encoding = 'utf-8')
# add price (store fes)
df_store_fes = df_fes[df_fes['name'].str.startswith('C(store_id)')].copy()
df_store_fes['store_id'] = df_store_fes['name'].apply(\
                             lambda x: x.replace('C(store_id)', '').strip())
df_store_fes['price'] = (df_store_fes['coeff'] + 1) * 100

df_stores = pd.merge(df_stores,
                     df_store_fes[['store_id', 'price']],
                     how = 'left',
                     on = 'store_id')

# ADD STORE CHARS

df_store_markets = pd.read_csv(os.path.join(path_built_lsa_csv,
                                            '201407_competition',
                                            'df_store_market_chars.csv'),
                               dtype = {'id_lsa' : str},
                               encoding = 'utf-8')

ls_lsa_cols = ['type_alt', 'region', 'surface',
               'nb_caisses', 'nb_pompes', 'drive']

df_store_chars = pd.merge(df_lsa[['id_lsa'] + ls_lsa_cols],
                          df_store_markets,
                          on = 'id_lsa',
                          how = 'left')

df_stores = pd.merge(df_stores,
                     df_store_chars,
                     on = 'id_lsa',
                     how = 'left')

df_stores['surface'] = df_stores['surface'].apply(lambda x: x/1000.0)

#df_prices.drop('store_chain', axis = 1, inplace = True)
#df_qlmc = pd.merge(df_prices,
#                   df_stores,
#                   on = ['store_id'],
#                   how = 'left')
#
## Avoid error msg on condition number
##df_qlmc['ac_hhi'] = df_qlmc['ac_hhi'] * 10000
##df_qlmc['hhi'] = df_qlmc['hhi'] * 10000

# Build log variables
for col in ['price', 'surface', 'hhi_1025km', 'ac_hhi_1025km',
            'AU_med_rev', 'UU_med_rev', 'CO_med_rev',
            'pop_cont_10', 'pop_cont_12',
            'pop_ac_1025km', 'pop_ac_20km',
            'demand_cont_10', 'demand_disc_10']:
#  df_qlmc['ln_{:s}'.format(col)] = np.log(df_qlmc[col])
  df_stores['ln_{:s}'.format(col)] = np.log(df_stores[col])

# rescale for regs
df_stores['demand_cont_10'] = df_stores['demand_cont_10'] / 1000

# LOAD MARKET DISPERSION
price_col = 'price' # or 'price' for log price dev to mean of raw prices
dict_df_disp = {}
for price_col in ['lpd', 'price']: # 'price'
  
  # Save df of aggregate market dispersion stats
  dict_df_disp['disp_agg_{:s}'.format(price_col)] =\
      pd.read_csv(os.path.join(path_built_csv,
                               'df_qlmc_dispersion_agg_{:s}.csv'.format(price_col)),
                  encoding = 'utf-8')
  
  # Save df of all market product dispersion stats
  dict_df_disp['disp_{:s}'.format(price_col)] =\
      pd.read_csv(os.path.join(path_built_csv,
                                  'df_qlmc_dispersion_{:s}.csv'.format(price_col)),
                     encoding = 'utf-8')

df_disp_agg_res = dict_df_disp['disp_agg_price']
df_disp_res = dict_df_disp['disp_price']

# ##############################
# REGS - AGG MARKET DISPERSION
# ##############################

df_disp = pd.merge(df_disp_agg_res,
                   df_stores,
                   on = 'store_id',
                   how = 'left')

df_disp['ac_nb_comp'] = df_disp['ac_nb_comp_10km']
df_disp['hhi'] = df_disp['hhi_10km']
df_disp['ac_hhi'] = df_disp['ac_hhi_10km']

# high hhi values in Corsica so get rid of it
df_disp = df_disp[~df_disp['region'].isin(['Corse'])]
# if exclude 'Pays de la Loire', 'Poitou-Charentes', 'Bretagne' (low dispersion)
# hhi has positive role

df_disp.sort('std', ascending = True, inplace = True)
lsd = ['store_id', 'std', 'range', 'nb_stores', 'hhi', 'region']
print()
print(df_disp[lsd][:20].to_string())
print(df_disp[lsd][-20:].to_string())

df_disp.plot(kind = 'scatter', x = 'hhi', y = 'std')
plt.show()

df_disp.plot(kind = 'scatter', x = 'hhi', y = 'range')
plt.show()

print(df_disp[['nb_stores', 'ac_hhi', 'hhi',
               'ln_demand_cont_10', 'ln_pop_cont_10',
               'ln_AU_med_rev', 'market_price']].corr().to_string())
 
ls_ls_expl_vars = [['hhi', 'demand_cont_10'],
                   ['hhi', 'market_price_2'],
                   ['hhi', 'market_price_2', 'demand_cont_10'],
                   ['hhi', 'market_price_2', 'demand_cont_10', 'C(STATUT_2010)', 'ac_nb_comp']]

ls_res = []
for ls_expl_vars in ls_ls_expl_vars:
  str_expl_vars = '+'.join(ls_expl_vars)
  df_disp = df_disp[df_disp['ac_nb_comp'] <= 100]
  for stat in ['std_res', 'range_res']:
    res = smf.ols('{:s} ~ {:s}'.format(stat, str_expl_vars), # nb_stores
                      data = df_disp).fit()
    ls_res.append(res)

print(summary_col(ls_res,
                  stars=True,
                  float_format='%0.2f',
                  info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                             'R2':lambda x: "{:.2f}".format(x.rsquared)}))

# todo: exclude very large demand areas (check also revenue...)

# ##############################
# REGS - AGG PRODUCT DISPERSION
# ##############################

df_disp_prod = pd.merge(df_disp_res,
                        df_stores,
                        on = 'store_id',
                        how = 'left')

df_disp_prod['ac_nb_comp'] = df_disp_prod['ac_nb_comp_10km']
df_disp_prod['hhi'] = df_disp_prod['hhi_10km']
df_disp_prod['ac_hhi'] = df_disp_prod['ac_hhi_10km']

## Overview
#df_prod = df_disp_prod[df_disp_prod['product'] ==\
#            df_disp_prod['product'].iloc[0]].copy()
#df_prod.sort('mean', ascending = True, inplace = True)

# Create int indexes for 2 group clusters
df_disp_prod['int_product'], prod_levels = pd.factorize(df_disp_prod['product'])
df_disp_prod['int_store_id'], prod_levels = pd.factorize(df_disp_prod['store_id'])


df_disp_prod['nb_prods_obs'] =\
  df_disp_prod[['product', 'section']].groupby('product').transform('count')

df_disp_prod[df_disp_prod['nb_prods_obs'] >= 150]['product'].value_counts()

df_dp_sub = df_disp_prod[df_disp_prod['nb_prods_obs'] >= 130]

#ls_ls_expl_vars = [['C(product)', 'hhi', 'market_price', 'ln_demand_cont_10'],
#                   ['C(product)', 'hhi', 'market_price_2', 'ln_demand_cont_10'],
#                   ['C(product)', 'hhi', 'market_price_2'],
#                   ['C(product)', 'hhi', 'market_price_2', 'C(STATUT_2010)']]

ls_ls_expl_vars = [['C(product)'] + ls_expl_vars for ls_expl_vars in ls_ls_expl_vars]

ls_res = []
for ls_expl_vars in ls_ls_expl_vars:
  str_expl_vars = '+'.join(ls_expl_vars)
  for stat in ['std', 'range']:
    #df_dp_sub = df_dp_sub[df_dp_sub['ac_nb_comp'] <= 100]
    res = smf.ols('{:s} ~ {:s}'.format(stat, str_expl_vars), # nb_stores
                      data = df_dp_sub).fit()
    res = res.get_robustcov_results(cov_type = 'cluster',
                                    groups = df_dp_sub[['int_store_id', 'int_product']].values,
                                    use_correction = True)
    ls_res.append(res)

print(summary_col(ls_res,
                  stars=True,
                  float_format='%0.2f',
                  info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                             'R2':lambda x: "{:.2f}".format(x.rsquared)}))

print()
print('Correlations (markets)')
print(df_disp[['hhi', 'ln_demand_cont_10',
               'market_price', 'market_price_2', 'ac_nb_comp']].corr().to_string())

print()
print('Correlations (markets/products)')
print(df_disp_prod[['hhi', 'ln_demand_cont_10',
                    'market_price', 'market_price_2', 'ac_nb_comp']].corr().to_string())
