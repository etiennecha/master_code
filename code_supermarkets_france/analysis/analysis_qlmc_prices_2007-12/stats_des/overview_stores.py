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

pd.set_option('float_format', '{:,.0f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###########
# LOAD DATA
# ###########

#df_qlmc = pd.read_csv(os.path.join(path_built_csv,
#                                   'df_qlmc.csv'),
#                      parse_dates = ['date'],
#                      dayfirst = True,
#                      encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                   'df_stores.csv'),
                      dtype = {'c_insee' : str,
                               'id_lsa' : str},
                      encoding = 'utf-8')

# harmonize store chains according to qlmc
ls_sc_replace = [('CENTRE E. LECLERC', 'LECLERC'),
                 ('CENTRE LECLERC', 'LECLERC'),
                 ('E. LECLERC', 'LECLERC'),
                 ('E.LECLERC', 'LECLERC'),
                 ('LECLERC EXPRESS', 'LECLERC'),
                 ('INTERMARCHE HYPER', 'INTERMARCHE'),
                 ('INTERMARCHE SUPER', 'INTERMARCHE'),
                 ('SUPER U', 'SYSTEME U'),
                 ('HYPER U', 'SYSTEME U'),
                 ('U EXPRESS', 'SYSTEME U'),
                 ('MARCHE U', 'SYSTEME U'),
                 ('CARREFOUR PLANET', 'CARREFOUR'),
                 ('GEANT CASINO', 'GEANT'),
                 ('GEANT DISCOUNT', 'GEANT'),
                 ('CARREFOUR MARKET', 'CHAMPION'),
                 ('HYPER CHAMPION', 'CHAMPION'),
                 ('CARREFOUR CITY', 'CHAMPION'),
                 ('CARREFOUR CONTACT', 'CHAMPION')]

#df_qlmc['store_chain_alt'] = df_qlmc['store_chain']
#for sc_old, sc_new in ls_sc_replace:
#  df_qlmc.loc[df_qlmc['store_chain'] == sc_old,
#              'store_chain_alt'] = sc_new

df_stores['store_chain_alt'] = df_stores['store_chain']
for sc_old, sc_new in ls_sc_replace:
  df_stores.loc[df_stores['store_chain'] == sc_old,
              'store_chain_alt'] = sc_new

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

# SU ACCROSS PERIODS

for x in ['store_chain', 'store_chain_alt', 'enseigne_alt']:
  print()
  print(u'Nb of stores by store_chain:')
  df_su = pd.pivot_table(df_stores,
                         index = x,
                         columns = 'period',
                         values = 'store',
                         aggfunc = len,
                         fill_value = 0)
  print(df_su.to_string())

print()
print(u'Nb of stores by retail group and type:')
df_rgt = pd.pivot_table(df_stores,
                        index = ['store_chain_alt', 'type'],
                        columns = 'period',
                        values = 'store',
                        aggfunc = len,
                        fill_value = 0)
print(df_rgt.to_string())

# SU FOR EACH PERIOD

ls_sc_alt = list(df_stores['store_chain_alt'].unique())

for per in range(13):
  df_stores_per = df_stores[df_stores['period'] == per]
  print()
  print(u'Period:', per)
  
  # Drop and use pivot_tables?
  print()
  print(u'Surface distribution by retail group:')
  ls_df_desc_surf = []
  for sc_alt in ls_sc_alt:
    ls_df_desc_surf.append(df_stores_per[df_stores_per['store_chain_alt'] == sc_alt]\
                                        ['surface'].describe())
  df_surf_by_rg = pd.concat(ls_df_desc_surf,
                            keys = ls_sc_alt,
                            axis = 1)
  df_surf_by_rg.columns = ['{:7s}'.format(x[0:7]) for x in df_surf_by_rg.columns]
  print(df_surf_by_rg.to_string())
  
  print()
  print(u'Nb employees by retail group:')
  ls_df_desc_nemp = []
  for sc_alt in ls_sc_alt:
    ls_df_desc_nemp.append(df_stores_per[df_stores_per['store_chain_alt'] == sc_alt]\
                                        ['nb_emplois'].describe())
  df_nemp_by_rg = pd.concat(ls_df_desc_nemp,
                            keys = ls_sc_alt,
                            axis = 1)
  df_nemp_by_rg.columns = ['{:>7s}'.format(x[0:7]) for x in df_nemp_by_rg.columns]
  print(df_nemp_by_rg.to_string())
  
  ## CHAIN FROM LSA VS. QLMC (a bit large tho)
  #print(pd.pivot_table(df_stores_per[['store_chain', 'enseigne_alt']],
  #                     index = 'enseigne_alt',
  #                     columns = 'store_chain',
  #                     aggfunc = len,
  #                     fill_value=0).to_string())
