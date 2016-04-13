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
#df_prices = pd.read_csv(os.path.join(path_built_csv,
#                                     'df_prices.csv'),
#                        encoding = 'utf-8')
df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_res_ln_prices.csv'),
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

#se_store_disp = df_prices[['store_id', 'res']].groupby('store_id').agg(lambda x: (x**2).mean())
se_store_disp = df_prices[['store_id', 'res']].groupby('store_id').agg(lambda x: x.abs().mean())
df_stores.set_index('store_id', inplace = True)
df_stores['disp'] = se_store_disp

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
print(df_su_store_fes.ix[ls_some_chains].to_string())

print()
print('Dispersion by chain')
df_su_disp = df_stores[['disp', 'qlmc_chain']].groupby('qlmc_chain')\
                                              .describe().unstack()
print(df_su_disp.ix[ls_some_chains].to_string())

for chain in ls_some_chains:
  print()
  print(chain)
  df_chain = df_stores[df_stores['qlmc_chain'] == chain]
  print(df_chain[['store_price', 'disp', 'hhi']].corr())
  print(smf.ols('store_price ~ disp + hhi + C(region) + surface', data = df_chain).fit().summary())


# INSPECT GEANT CASINO

df_stores[df_stores['store_chain'] == 'GEANT CASINO'].plot(kind = 'scatter', x = 'store_price', y = 'disp')
plt.show()

lsdo = ['store_name', 'store_price', 'disp', 'price_1', 'price_2', 'surface', 'region']

# some outliers with low price
print(df_stores[(df_stores['store_chain'] == 'GEANT CASINO') &\
                (df_stores['store_price'] <= 96.5)][lsdo].to_string())
