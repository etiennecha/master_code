#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt

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

# ############
# LOAD DATA
# ############

# LOAD DF PRICES
df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_res_ln_prices.csv'),
                        encoding = 'utf-8')
df_prices['log_pd'] = np.log(df_prices['price'] /\
                               df_prices.groupby('product')['price'].transform('mean'))

# LOAD DF FES
price_col = 'ln_price'
df_fes = pd.read_csv(os.path.join(path_built_csv,
                     'df_res_{:s}_fes.csv'.format(price_col)),
                     encoding = 'utf-8')

# LOAD QLMC STORE DATA
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str},
                        encoding = 'utf-8')

# fix issue
df_stores.loc[df_stores['store_name'].str.contains('CARREFOUR CITY'),
              'store_chain'] = 'CARREFOUR CITY' # should not be in CARREFOUR...

# HARMONZATION OF CHAINS
ls_ls_enseigne_lsa_to_qlmc = [[['CENTRE E.LECLERC'], 'LECLERC'],
                              [['GEANT CASINO'], 'GEANT CASINO'],
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

# add price (store fes)
df_store_fes = df_fes[df_fes['name'].str.startswith('C(store_id)')].copy()
df_store_fes['store_id'] = df_store_fes['name'].apply(\
                             lambda x: x.replace('C(store_id)', '').strip())
df_store_fes['price'] = (df_store_fes['coeff'] + 1) * 100

df_stores = pd.merge(df_stores,
                     df_store_fes[['store_id', 'price']],
                     how = 'left',
                     on = 'store_id')

# Build log variables
for col in ['price', 'surface',
            '1025km_hhi', '1025km_ac_hhi',
            'UU_med_rev', 'AU_med_rev',
            '10_pop', '10km_ac_pop', '20km_ac_pop']:
  df_stores['ln_{:s}'.format(col)] = np.log(df_stores[col])

# Avoid error msg on condition number
df_stores['surface'] = df_stores['surface'].apply(lambda x: x/1000.0)
df_stores['AU_med_rev'] = df_stores['AU_med_rev'].apply(lambda x: x/1000.0)
df_stores['UU_med_rev'] = df_stores['UU_med_rev'].apply(lambda x: x/1000.0)
df_stores['hhi'] = df_stores['1025km_hhi'] 

# Create dummy high hhi
df_stores['dum_high_hhi'] = 0
df_stores.loc[df_stores['hhi'] >= 0.25, 'dum_high_hhi'] = 1
df_stores['hhi'] = df_stores['hhi'] * 100

df_stores = df_stores[~(df_stores['qlmc_chain'].isin(['SUPERMARCHE MATCH',
                                                      'ATAC',
                                                      'MIGROS',
                                                      'RECORD',
                                                      'G 20']))]

ls_tup_dum_reg = [[u'Ile-de-France', 'd_idf'],
                  [u"Provence-Alpes-Cote-d'Azur", 'd_paca'],
                  [u"Rhone-Alpes", 'd_ra'],
                  [u'Corse', 'd_co']]

for region, d_region in ls_tup_dum_reg:
  df_stores[d_region] = 0
  df_stores.loc[df_stores['region'] == region,
                d_region] = 1

# QLMC COMP WITH TRAVEL DURATIONS
df_qlmc_competitors = pd.read_csv(os.path.join(path_built_csv,
                                               'df_qlmc_competitors_final.csv'),
                                  encoding = 'utf-8')

# #########################
# INSPECT DATA
# #########################

df_stores = df_stores[~df_stores['region'].isin(['Corse'])]
df_stores = df_stores[df_stores['surface'] >= 2.5]

# Avoid error msg on condition number
df_stores['surface'] = df_stores['surface'].apply(lambda x: x/1000.0)
df_stores['dpt'] = df_stores['c_insee'].str.slice(stop = 2)

# ADD STORE PRICE FREQUENCIES
df_chain_store_price_fq = pd.read_csv(os.path.join(path_built_csv,
                                                   'df_chain_store_price_freq.csv'),
                                      encoding = 'utf-8')

df_chain_store_price_fq.drop('store_chain', axis = 1, inplace = True)

df_stores = pd.merge(df_stores,
                     df_chain_store_price_fq,
                     on = 'store_id',
                     how = 'left')

# ADD STORE PRICE FE
df_fes = pd.read_csv(os.path.join(path_built_csv,
                                  'df_res_ln_price_fes.csv'),
                     encoding = 'utf-8')

df_store_fes = df_fes[df_fes['name'].str.startswith('C(store_id)')].copy()
df_store_fes['store_id'] = df_store_fes['name'].apply(\
                             lambda x: x.replace('C(store_id)', '').strip())
df_store_fes['store_price'] = (df_store_fes['coeff'] + 1) * 100

df_stores = pd.merge(df_stores,
                     df_store_fes,
                     on = 'store_id',
                     how = 'left')

# ADD STORE DISPERSION
df_prices['res'] = df_prices['ln_price'] - df_prices['ln_price_hat']

# robustness: reject residuals if beyond 40%
df_prices = df_prices[df_prices['res'].abs() < 0.4]

se_store_disp = df_prices[['store_id', 'res']].groupby('store_id')\
                                              .agg('std')
#se_store_disp = df_prices[['store_id', 'res']].groupby('store_id')\
#                                              .agg(lambda x: x.abs().mean())
df_stores.set_index('store_id', inplace = True)
df_stores['store_dispersion'] = se_store_disp

# ####################
# INVESTIGATE LECLERC
# ####################

ls_some_chains = ['LECLERC',
                  'INTERMARCHE', # +7.0%
                  'SYSTEME U', # +6.7% for both hyper and super
                  'CARREFOUR MARKET', # +13.5%
                  'AUCHAN',  # +7.6%
                  'CORA', # +10.2%
                  'CARREFOUR', # +7.8%
                  'GEANT CASINO', #+1.8% (only Geant? also Hyper?)
                  'CASINO',  # +16.7%
                  'SIMPLY MARKET'] # +12.9%

print()
print('Store FEs by chain')
df_su_store_fes = df_stores[['store_price', 'qlmc_chain']].groupby('qlmc_chain')\
                                              .describe().unstack()
print(df_su_store_fes.ix[ls_some_chains].to_string(float_format = format_float_int))

print()
print('Dispersion by chain')
df_su_disp = df_stores[['store_dispersion', 'qlmc_chain']].groupby('qlmc_chain')\
                                                          .describe().unstack()
print(df_su_disp.ix[ls_some_chains].to_string())

for chain in ls_some_chains:
  print()
  print(chain)
  df_chain = df_stores[df_stores['qlmc_chain'] == chain]
  print(df_chain[['store_price', 'store_dispersion', 'hhi']].corr())
  print(smf.ols('store_price ~ store_dispersion + hhi + C(region) + surface',
                data = df_chain).fit().summary())

# ###################################################
# INSPECT RELATION BETWEEN PRICE LEVEL AND DISPERSION
# ###################################################

for chain in ['GEANT CASINO', 'AUCHAN', 'CARREFOUR', 'LECLERC']:
  df_stores[df_stores['store_chain'] == chain].plot(kind = 'scatter',
                                                    x = 'store_price',
                                                    y = 'store_dispersion')
  plt.title(chain)
  plt.show()

lsdo = ['store_name', 'store_price', 'store_dispersion',
        'price_1', 'price_2', 'surface', 'region']

# some outliers with low price
print(df_stores[(df_stores['store_chain'] == 'GEANT CASINO') &\
                (df_stores['store_price'] <= 96.5)][lsdo].to_string())
