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

for col in ['surface', 'hhi', 'ac_hhi',
            'med_rev_uu', 'med_rev_au',
            'pop_cont_10', 'pop_cont_8', 'pop_cont_12',
            'pop_ac_10km', 'pop_ac_20km']:
  df_stores['ln_{:s}'.format(col)] = np.log(df_stores[col])

df_stores['ac_hhi_2'] = df_stores['ac_hhi']**2

# LOAD MARKET DISPERSION
price_col = 'lpd' # or 'price' for log price dev to mean of raw prices
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

df_disp_agg_res = dict_df_disp['disp_agg_lpd']
df_disp_res = dict_df_disp['disp_lpd']


# ##############
# REGRESSIONS
# ##############

df_disp = pd.merge(df_disp_agg_res,
                   df_stores,
                   on = 'store_id',
                   how = 'left')

# high hhi values in Corsica so get rid of it
df_disp = df_disp[~df_disp['region'].isin(['Corse'])]
# if exclude 'Pays de la Loire', 'Poitou-Charentes', 'Bretagne' (low dispersion)
# hhi has positive role

df_disp.sort('std', ascending = True, inplace = True)
lsd = ['store_id', 'std', 'range', 'nb_stores', 'ac_nb_stores', 'hhi', 'region']
print()
print(df_disp[lsd][:20].to_string())
print(df_disp[lsd][-20:].to_string())

df_disp.plot(kind = 'scatter', x = 'hhi', y = 'std')
plt.show()

df_disp.plot(kind = 'scatter', x = 'hhi', y = 'range')
plt.show()

print(df_disp[['nb_stores', 'ac_hhi', 'hhi',
               'ln_pop_cont_10', 'ln_pop_cont_12',
               'ln_med_rev_au', 'ln_med_rev_uu']].corr().to_string())

res_std = smf.ols('std ~ ac_hhi + ac_hhi_2 + ln_pop_cont_10 + ln_med_rev_au',
                  data = df_disp).fit()
print(res_std.summary())

res_range = smf.ols('range ~ ac_hhi + ac_hhi_2 + ln_pop_cont_10 + ln_med_rev_au',
                    data = df_disp).fit()
print(res_range.summary())
