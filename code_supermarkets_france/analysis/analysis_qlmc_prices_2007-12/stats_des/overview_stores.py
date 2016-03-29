#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2007-12')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_lsa_csv = os.path.join(path_data,
                            'data_supermarkets',
                            'data_built',
                            'data_lsa',
                            'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

df_qlmc = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc.csv'),
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

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                   'df_stores.csv'),
                      dtype = {'c_insee' : str,
                               'id_lsa' : str},
                      encoding = 'utf-8')

df_lsa = pd.read_csv(os.path.join(path_lsa_csv,
                                  'df_lsa_active.csv'),
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

# check no dup in df_stores
df_stores_dup =\
  df_stores[(~df_stores['id_lsa'].isnull()) &\
            ((df_stores.duplicated(['period', 'id_lsa'], take_last = False)) |\
             (df_stores.duplicated(['period', 'id_lsa'], take_last = True)))]

ls_lsa_cols = ['enseigne_alt',
               'groupe',
               'type',
               'ex_surface',
               'surface',
               'nb_caisses',
               'nb_emplois',
               'nb_pompes',
               'nb_parking']

df_qlmc_stores = df_stores.copy()
df_stores = pd.merge(df_qlmc_stores,
                     df_lsa[['id_lsa'] + ls_lsa_cols],
                     on = 'id_lsa',
                     how = 'inner')

# ###############
# STATS DES
# ###############

print()
print(u'Nb of stores by retail group:')
print(df_stores_per['groupe'].value_counts())
df_rg = pd.pivot_table(df_stores,
                       index = 'groupe',
                       columns = 'period',
                       values = 'store',
                       aggfunc = len,
                       fill_value = 0)
print(df_rg.to_string())

print()
print(u'Nb of stores by retail group and type:')
df_rgt = pd.pivot_table(df_stores,
                        index = ['groupe', 'type'],
                        columns = 'period',
                        values = 'store',
                        aggfunc = len,
                        fill_value = 0)
print(df_rgt.to_string())

print()
print(u'Nb of stores by enseigne_alt:')
df_ea = pd.pivot_table(df_stores,
                       index = 'enseigne_alt',
                       columns = 'period',
                       values = 'store',
                       aggfunc = len,
                       fill_value = 0)
print(df_ea.to_string())

for per in range(13):
  df_stores_per = df_stores[df_stores['period'] == per]
  print()
  print(u'Period:', per)
  
  # Drop and use pivot_tables?
  print()
  print(u'Surface distribution by retail group:')
  ls_df_desc_surf = []
  for rg in ls_rg:
    ls_df_desc_surf.append(df_stores_per[df_stores_per['groupe'] == rg]['surface'].describe())
  df_surf_by_rg = pd.concat(ls_df_desc_surf,
                            keys = ls_rg,
                            axis = 1)
  df_surf_by_rg.columns = ['{:7s}'.format(x[0:7]) for x in df_surf_by_rg.columns]
  print(df_surf_by_rg.to_string())
  
  print()
  print(u'Nb employees by retail group:')
  ls_df_desc_nemp = []
  for rg in ls_rg:
    ls_df_desc_nemp.append(df_stores_per[df_stores_per['groupe'] == rg]['nb_emplois'].describe())
  df_nemp_by_rg = pd.concat(ls_df_desc_nemp,
                            keys = ls_rg,
                            axis = 1)
  df_nemp_by_rg.columns = ['{:>7s}'.format(x[0:7]) for x in df_nemp_by_rg.columns]
  print(df_nemp_by_rg.to_string())
  
  ## CHAIN FROM LSA VS. QLMC (a bit large tho)
  #print(pd.pivot_table(df_stores_per[['store_chain', 'enseigne_alt']],
  #                     index = 'enseigne_alt',
  #                     columns = 'store_chain',
  #                     aggfunc = len,
  #                     fill_value=0).to_string())
