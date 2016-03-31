#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_built = os.path.join(path_data,
                         'data_supermarkets',
                         'data_built',
                         'data_qlmc_2007-12')
path_built_csv = os.path.join(path_built, 'data_csv')

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

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
pd.set_option('float_format', '{:,.2f}'.format)

# ############
# LOAD DATA
# ############

df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
                      dtype = {'id_lsa' : str},
                      parse_dates = ['date'],
                      dayfirst = True,
                      encoding = 'utf-8')

# Fix Store_Chain for prelim stats des
ls_sc_drop = ['CARREFOUR CITY',
              'CARREFOUR CONTACT',
              'CARREFOUR PLANET',
              'GEANT DISCOUNT',
              'HYPER CHAMPION',
              'INTERMARCHE HYPER',
              'LECLERC EXPRESS',
              'MARCHE U',
              'U EXPRESS']

df_qlmc = df_qlmc[~df_qlmc['store_chain'].isin(ls_sc_drop)]

ls_sc_replace = [('CENTRE E. LECLERC', 'LECLERC'),
                 ('CENTRE LECLERC', 'LECLERC'),
                 ('E. LECLERC', 'LECLERC'),
                 ('E.LECLERC', 'LECLERC'),
                 ('SYSTEME U', 'SUPER U'),
                 ('GEANT', 'GEANT CASINO')]
for sc_old, sc_new in ls_sc_replace:
  df_qlmc.loc[df_qlmc['store_chain'] == sc_old,
              'store_chain'] = sc_new

# LOAD QLMC STORE DATA
df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores.csv'),
                        dtype = {'id_lsa' : str},
                        encoding = 'utf-8')
# same field (fixed tho) in df_qlmc
df_stores.drop(['store_chain',
                'store_municipality',
                'insee_municipality',
                'qlmc_surface',
                'c_insee'], axis = 1, inplace = True)

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
               'type',
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

# STORE INFO IN DF QLMC
df_qlmc = df_qlmc[~df_qlmc['id_lsa'].isnull()]
df_qlmc = pd.merge(df_qlmc,
                   df_stores,
                   on = ['period', 'id_lsa'],
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

# ######################################
# REG MOST COMMON PRODUCT PRICES ON COMP
# ######################################

## get rid of closed (so far but should accomodate later)
#df_qlmc = df_qlmc[~df_qlmc['enseigne_alt'].isnull()]

se_prod = df_qlmc.groupby(['section', 'family', 'product']).agg('size')
se_prod.sort(ascending = False, inplace = True)

# Aavoid error msg on condition number
df_qlmc['surface'] = df_qlmc['surface'].apply(lambda x: x/1000.0)
# df_qlmc_prod['ac_hhi'] = df_qlmc_prod['ac_hhi'] * 10000
# Try with log of price (semi elasticity)
df_qlmc['ln_price'] = np.log(df_qlmc['price'])
## Control for dpt (region?)
#df_qlmc['Dpt'] = df_qlmc['INSEE_Code'].str.slice(stop = 2)

# WITH ONE PRODUCT
section, family, product = se_prod.index[0]
df_qlmc_prod = df_qlmc[(df_qlmc['section'] == section) &\
                       (df_qlmc['family'] == family) &\
                       (df_qlmc['product'] == product)].copy()

print(u'Regression of price of {:s}'.format(product))
reg = smf.ols('price ~ C(period) + surface + store_chain + ac_hhi',
              data = df_qlmc_prod[df_qlmc_prod['type'] == 'H'],
              missing = 'drop').fit()
print(reg.summary())

print(u'Regression of log price of {:s}'.format(product))
reg = smf.ols('ln_price ~ C(period) + surface + store_chain + ac_hhi',
              data = df_qlmc_prod[df_qlmc_prod['type'] == 'H'],
              missing = 'drop').fit()
print(reg.summary())

# Pbm: one or a few ref prices (per brand)... so reg is not very meaningful
# More convincing with store FE? set of products? 
# Do with LECLERC products?

# WITH TOP 20 PRODUCTS
ls_top_prod = [x[-1] for x in se_prod.index[0:100]]
df_qlmc_prods = df_qlmc[df_qlmc['product'].isin(ls_top_prod)].copy()

print(u'Regression of price of top 20 products (avail in data)')
reg = smf.ols('price ~ C(period) + C(product) + surface + store_chain + ac_hhi',
              data = df_qlmc_prods[df_qlmc_prods['type'] == 'H'],
              missing = 'drop').fit()
print(reg.summary())

print(u'Regression of log price of top 20 products (avail in data)')
reg = smf.ols('ln_price ~ C(period) + C(product) + surface + store_chain + ac_hhi',
              data = df_qlmc_prods[df_qlmc_prods['type'] == 'H'],
              missing = 'drop').fit()
print(reg.summary())
