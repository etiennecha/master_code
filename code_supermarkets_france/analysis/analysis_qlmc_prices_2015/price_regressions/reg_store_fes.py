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

# LOAD FEs
price_col = 'ln_price'
df_fes = pd.read_csv(os.path.join(path_built_csv,
                     'df_res_{:s}_fes.csv'.format(price_col)),
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


# add price (store fes)
df_store_fes = df_fes[df_fes['name'].str.startswith('C(store_id)')].copy()
df_store_fes['store_id'] = df_store_fes['name'].apply(\
                             lambda x: x.replace('C(store_id)', '').strip())
df_store_fes['price'] = (df_store_fes['coeff'] + 1) * 100

df_stores = pd.merge(df_stores,
                     df_store_fes[['store_id', 'price']],
                     how = 'left',
                     on = 'store_id')

# Avoid error msg on condition number
df_stores['surface'] = df_stores['surface'].apply(lambda x: x/1000.0)

# Create dummy high hhi
df_stores['dum_high_hhi'] = 0
df_stores.loc[df_stores['hhi'] >= 0.3, 'dum_high_hhi'] = 1

# Build log variables
for col in ['price', 'surface', 'hhi', 'ac_hhi',
            'med_rev_uu', 'med_rev_au',
            'pop_cont_10', 'pop_ac_10km', 'pop_ac_20km']:
  df_stores['ln_{:s}'.format(col)] = np.log(df_stores[col])

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

ls_exclude_chains = ['CARREFOUR MARKET',
                     'CASINO',
                     'SIMPLY MARKET']
df_stores = df_stores[~df_stores['qlmc_chain'].isin(ls_exclude_chains)]
df_stores = df_stores[df_stores['surface'] >= 2.5]

print()
print(u'Inspect corr of main explanatory vars by chain:')
print(df_stores[['surface', 'hhi', 'med_rev_au', 'pop_cont_10']].corr())

print()
print(u'Inspect main explanatory vars by chain:')
for var in ['surface', 'hhi', 'med_rev_au', 'pop_cont_10']:
  print()
  print(df_stores[[var, 'qlmc_chain']][df_stores['surface'] >= 2.5]\
                 .groupby('qlmc_chain').describe()[var].unstack().T.to_string())
 
print(u'Inspect hhi by region:')
print(df_stores[['hhi', 'region']][df_stores['surface'] >= 2.5]\
               .groupby('region').describe()['hhi'].unstack().to_string())

# #########################
# REG PRICE ON STORES CHARS
# #########################

res_a = smf.ols("ln_price ~ C(qlmc_chain, Treatment(reference='LECLERC')) + " +\
                "surface + dum_high_hhi + ln_med_rev_au + ln_pop_cont_10",
                data = df_stores).fit()
print(res_a.summary())

res_b = smf.ols("ln_price ~ surface + dum_high_hhi + ln_med_rev_au + ln_pop_cont_10",
                data = df_stores).fit()
print(res_b.summary())

res_c = smf.ols("ln_price ~ C(qlmc_chain, Treatment(reference='LECLERC')) + " +\
                "surface + hhi + ln_med_rev_au + ln_pop_cont_10 + "\
                "d_paca + d_ra + d_co + d_idf",
                data = df_stores).fit()
print(res_c.summary())

res_d = smf.ols("ln_price ~ C(qlmc_chain, Treatment(reference='LECLERC')) + " +\
                "surface + ln_med_rev_au + ln_pop_cont_10 + "\
                "d_paca + d_ra + d_co + d_idf*hhi",
                data = df_stores).fit()
print(res_d.summary())

res_d = smf.ols("ln_price ~ surface + dum_high_hhi + ln_med_rev_au + ln_pop_cont_10 + d_idf",
                data = df_stores[df_stores['store_chain'] == 'AUCHAN']).fit()

# #################################
# REG LECLERC PRICE ON STORES CHARS
# #################################

df_lec = df_stores[df_stores['store_chain'] == 'LECLERC'].copy()
df_lec.set_index('store_id', inplace = True)

dict_df_lec_dist = {}
for var in ['dist', 'gg_dist_val', 'gg_dur_val']:
  df_lec_dist = df_qlmc_competitors[['lec_id', var]]\
                                   .groupby(['lec_id'])\
                                   .describe()[var].unstack()
  dict_df_lec_dist[var] = df_lec_dist

df_lec['nb_comp'] = df_lec_dist['count']
df_lec['comp_min_dur'] = df_lec_dist['min']
df_lec['d_close_comp'] = 0
df_lec.loc[df_lec['comp_min_dur'] <= 3, 'd_close_comp'] = 1

ls_geant_comp = df_qlmc_competitors[df_qlmc_competitors['comp_chain'] ==\
                                      'GEANT CASINO']['lec_id'].unique().tolist()

df_lec['comp_geant'] = 0
df_lec.loc[df_lec.index.isin(ls_geant_comp), 'comp_geant'] = 1

res_l = smf.ols("ln_price ~ surface + comp_min_dur + comp_geant + d_idf",
                data = df_lec[df_lec['region'] != 'Corse']).fit()
print(res_l.summary())

res_m = smf.ols("ln_price ~ surface + nb_comp + comp_geant + d_idf",
                data = df_lec[df_lec['region'] != 'Corse']).fit()
print(res_m.summary())
