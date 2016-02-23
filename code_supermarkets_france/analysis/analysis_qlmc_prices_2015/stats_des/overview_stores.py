#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
from functions_string import *
from functions_generic_qlmc import *
import os, sys
import re
import json
import pandas as pd

path_qlmc_scraped = os.path.join(path_data,
                                 'data_supermarkets',
                                 'data_qlmc_2015',
                                 'data_source',
                                 'data_scraped_201503')

path_built_csv = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_qlmc_2015',
                              'data_csv_201503')

path_lsa_csv = os.path.join(path_data,
                            'data_supermarkets',
                            'data_built',
                            'data_lsa',
                            'data_csv')

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

# ##########
# LOAD DATA
# ##########

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
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

df_stores = pd.merge(df_stores,
                     df_lsa,
                     on = 'id_lsa',
                     how = 'left')

# ###############
# STATS DES
# ###############

print()
print(u'Nf of hypers and supers:')
print(df_stores['type'].value_counts())

print()
print(u'Nb of stores by retail group:')
print(df_stores['groupe'].value_counts())

print()
print(u'Nb of stores by chain:')
print(df_stores['enseigne_alt'].value_counts())

# todo: check H/S split of sample vs. H/S split by retail group

se_rg_vc = df_stores['groupe'].value_counts()
ls_rg = list(se_rg_vc.index[se_rg_vc >= 1])
pd.set_option('float_format', '{:,.0f}'.format)

# Drop and use pivot_tables?
print()
print(u'Surface distribution by retail group:')
ls_df_desc_surf = []
for rg in ls_rg:
  ls_df_desc_surf.append(df_stores[df_stores['groupe'] == rg]['surface'].describe())
df_surf_by_rg = pd.concat(ls_df_desc_surf,
                          keys = ls_rg,
                          axis = 1)
df_surf_by_rg.columns = ['{:7s}'.format(x[0:7]) for x in df_surf_by_rg.columns]
print(df_surf_by_rg.to_string())

print()
print(u'Nb employees by retail group:')
ls_df_desc_nemp = []
for rg in ls_rg:
  ls_df_desc_nemp.append(df_stores[df_stores['groupe'] == rg]['nb_emplois'].describe())
df_nemp_by_rg = pd.concat(ls_df_desc_nemp,
                          keys = ls_rg,
                          axis = 1)
df_nemp_by_rg.columns = ['{:>7s}'.format(x[0:7]) for x in df_nemp_by_rg.columns]
print(df_nemp_by_rg.to_string())

## CHAIN FROM LSA VS. QLMC (a bit large tho)
#print(pd.pivot_table(df_stores[['store_chain', 'enseigne_alt']],
#                     index = 'enseigne_alt',
#                     columns = 'store_chain',
#                     aggfunc = len,
#                     fill_value=0).to_string())
