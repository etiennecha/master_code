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
from statsmodels.iolib.summary2 import summary_col
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

# LOAD DF PRICES (by_chain: product FE is chain specific)
df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_res_ln_prices.csv'), # _by_chain
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

# add price dispersion (std dev of store residuals)

# Build log variables
for col in ['price', 'surface',
            'hhi_1025km', 'ac_hhi_1025km',
            'UU_med_rev', 'AU_med_rev', 'CO_med_rev',
            'AU_pop', 'UU_pop', 'CO_pop',
            'pop_cont_10', 'pop_ac_10km', 'pop_ac_20km']:
  df_stores['ln_{:s}'.format(col)] = np.log(df_stores[col])

# Avoid error msg on condition number
df_stores['surface'] = df_stores['surface'].apply(lambda x: x/1000.0)
df_stores['AU_med_rev'] = df_stores['AU_med_rev'].apply(lambda x: x/1000.0)
df_stores['UU_med_rev'] = df_stores['UU_med_rev'].apply(lambda x: x/1000.0)
df_stores['hhi'] = df_stores['hhi_1025km'] 

# Create dummy high hhi
df_stores['dum_high_hhi'] = 0
df_stores.loc[df_stores['hhi'] >= 0.25, 'dum_high_hhi'] = 1
df_stores['hhi'] = df_stores['hhi'] * 100

df_stores['dpt'] = df_stores['c_insee'].str.slice(stop = 2)

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

# FILTER STORES

df_stores = df_stores[~df_stores['region'].isin(['Corse'])]
df_stores = df_stores[df_stores['surface'] >= 2.5]

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
df_stores['store_dispersion'] = se_store_disp * 100

# RESTRICTION
df_stores_bu = df_stores.copy()
df_stores = df_stores[df_stores['dist_cl_comp'] <= 5]
df_stores_nolg = df_stores[~df_stores['store_chain'].isin(['LECLERC', 'GEANT CASINO'])]

# #########
# STATS DES
# #########

# can regress 'coeff' (percentage... so essentially ln(homogeneous price)

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

ls_some_chains.sort()

print()
print('Store FEs by chain')
df_su_store_fes = df_stores[['store_price', 'qlmc_chain']].groupby('qlmc_chain')\
                                              .describe().unstack()
print(df_su_store_fes.ix[ls_some_chains].to_string(float_format = format_float_int))
print()
print(df_stores['store_price'].describe().to_string(float_format = format_float_int))

pd.set_option('float_format', '{:,.1f}'.format)
print()
print('Dispersion by chain')
df_su_disp = df_stores[['store_dispersion', 'qlmc_chain']].groupby('qlmc_chain')\
                                                          .describe().unstack()
print(df_su_disp.ix[ls_some_chains].to_string())
print()
print(df_stores['store_dispersion'].describe().to_string())

ls_ev = ['surface', 'hhi', 'ln_pop_cont_10', 'ln_CO_med_rev']
str_ev = " + ".join(ls_ev)

print()
print(u'Inspect main explanatory vars by chain:')
for ev in ls_ev:
  print()
  print(ev)
  print(df_stores[[ev, 'qlmc_chain']].groupby('qlmc_chain').describe()[ev].unstack().to_string())

print()
print(u'Inspect corr of main explanatory vars by chain:')
print(df_stores[ls_ev].corr())

print()
print(u'Su explanatory vars mean by chain:')
print(pd.pivot_table(df_stores,
                     values = ls_ev,
                     index = 'qlmc_chain',
                     aggfunc = 'mean'))

print()
print(u'Su explanatory vars std by chain:')
print(pd.pivot_table(df_stores,
                     values = ls_ev,
                     index = 'qlmc_chain',
                     aggfunc = 'std'))

print()
print(u'Inspect hhi by region:')
print(df_stores[['hhi', 'region']].groupby('region').describe()['hhi'].unstack().to_string())
print()
print(df_stores[ls_ev].corr())

# Regs to run:
# - compa replications: store chains only
# - compa fully controlled: store chains, regions and store vars
# - store vars
# - store vars + regions (useful?)

# REG OF STORE PRICE - NAIVE BRAND
ls_formulas = ["store_price ~ C(qlmc_chain, Treatment('LECLERC'))",
               "store_price ~ C(qlmc_chain, Treatment('LECLERC'))" +\
                            " + {:s} + C(region)".format(str_ev),
               "store_price ~ {:s}".format(str_ev),
               "store_price ~ {:s} +  C(region)".format(str_ev)]

ls_res = [smf.ols(formula, data = df_stores).fit() for formula in ls_formulas]

#print(summary_col(ls_res,
#                  stars=True,
#                  float_format='%0.2f'))

print(summary_col(ls_res,
                  stars=True,
                  float_format='%0.2f',
                  model_names=['(0)', '(1)', '(2)', '(3)'],
                  info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                             'R2':lambda x: "{:.2f}".format(x.rsquared)}))

# REG OF STORE PRICES BY CHAIN

ls_big_chains = ['LECLERC',
                 'GEANT CASINO',
                 'INTERMARCHE',
                 'SYSTEME U',
                 'AUCHAN',
                 'CARREFOUR']

pd.set_option('float_format', '{:,.2f}'.format)
ls_reg_bc, ls_reg_bc_wd = [], []
ls_reg_bc_disp, ls_reg_bc_disp_wp = [], []
for chain in ls_big_chains:
  print(u'-'*30)
  print()
  print(chain)
  df_chain = df_stores[df_stores['qlmc_chain'] == chain]
  print()
  print(df_chain[['store_price', 'store_dispersion', 'hhi']].corr())
  print()
  print(df_chain[ls_ev].corr())
  ls_reg_bc.append(\
    smf.ols("store_price ~ {:s}".format(str_ev),
            data = df_chain).fit())
  ls_reg_bc_wd.append(\
    smf.ols("store_price ~ {:s} + store_dispersion".format(str_ev),
            data = df_chain).fit())
  ls_reg_bc_disp.append(\
    smf.ols("store_dispersion ~ {:s}".format(str_ev),
            data = df_chain).fit())
  ls_reg_bc_disp_wp.append(\
    smf.ols("store_dispersion ~ {:s} + store_price".format(str_ev),
            data = df_chain).fit())

for ls_reg in [ls_reg_bc, ls_reg_bc_wd, ls_reg_bc_disp, ls_reg_bc_disp_wp]:
  print()
  print(summary_col(ls_reg,
                    stars=True,
                    float_format='%0.2f',
                    model_names=ls_big_chains,
                    info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                               'R2':lambda x: "{:.2f}".format(x.rsquared)}))
 
# todo: drop if dist_cl_comp too high (outliers) ?
## print(df_stores[df_stores['dist_cl_comp'] >= 5]['dist_cl_comp'].to_string())
# df_stores = df_stores[df_stores['dist_cl_comp'] <= 5]
## check that no mistake in dist_cl_comp... seem low

## ###################################################
## INSPECT RELATION BETWEEN PRICE LEVEL AND DISPERSION
## ###################################################
#
#for chain in ['GEANT CASINO', 'AUCHAN', 'CARREFOUR', 'LECLERC']:
#  df_stores[df_stores['store_chain'] == chain].plot(kind = 'scatter',
#                                                    x = 'store_price',
#                                                    y = 'store_dispersion')
#  plt.title(chain)
#  plt.show()
#
#lsdo = ['store_name', 'store_price', 'store_dispersion',
#        'price_1', 'price_2', 'surface', 'region']
#
## some outliers with low price
#print(df_stores[(df_stores['store_chain'] == 'GEANT CASINO') &\
#                (df_stores['store_price'] <= 96.5)][lsdo].to_string())

## #################################
## REG LECLERC PRICE ON STORES CHARS
## #################################
#
#print()
#print(u'Regs with Leclerc stores only')
#
#df_lec = df_stores[df_stores['store_chain'] == 'LECLERC'].copy()
#df_lec.set_index('store_id', inplace = True)
#
#dict_df_lec_dist = {}
#for var in ['dist', 'gg_dist_val', 'gg_dur_val']:
#  df_lec_dist = df_qlmc_competitors[['lec_id', var]]\
#                                   .groupby(['lec_id'])\
#                                   .describe()[var].unstack()
#  dict_df_lec_dist[var] = df_lec_dist
#
#df_lec['nb_comp'] = df_lec_dist['count']
#df_lec['comp_min_dur'] = df_lec_dist['min']
#df_lec['d_close_comp'] = 0
#df_lec.loc[df_lec['comp_min_dur'] <= 3, 'd_close_comp'] = 1
#
#ls_geant_comp = df_qlmc_competitors[df_qlmc_competitors['comp_chain'] ==\
#                                      'GEANT CASINO']['lec_id'].unique().tolist()
#
#df_lec['comp_geant'] = 0
#df_lec.loc[df_lec.index.isin(ls_geant_comp), 'comp_geant'] = 1
#
#res_l = smf.ols("ln_price ~ surface + comp_min_dur + comp_geant + d_idf",
#                data = df_lec[df_lec['region'] != 'Corse']).fit()
#print(res_l.summary())
#
#res_m = smf.ols("ln_price ~ surface + nb_comp + comp_geant + d_idf",
#                data = df_lec[df_lec['region'] != 'Corse']).fit()
#print(res_m.summary())
