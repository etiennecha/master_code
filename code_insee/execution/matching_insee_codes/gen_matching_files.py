#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import pandas as pd

# ##############
# LOAD OLD FILES
# ##############

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_match_insee = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

# Basic correspondence file (a bit old)
ls_corr = open(os.path.join(path_dir_match_insee,
                            'backup',
                            'corr_cinsee_cpostal'),
               'r').read().split('\n')
ls_corr = ls_corr[1:-1]
ls_corr = [row.split(';') for row in ls_corr]

# Update file (update based on work with gas addresses)
ls_corr_update = open(os.path.join(path_dir_match_insee,
                                   'backup',
                                   'corr_cinsee_cpostal_update'),
                      'r').read().split('\n')
ls_corr_update = ls_corr_update[1:]
ls_corr_update = [row.split(';') for row in ls_corr_update]

ls_corr_final = ls_corr + ls_corr_update

# File ad hoc for gas stations (cedexes or mistakes... should drop)
ls_corr_gas = open(os.path.join(path_dir_match_insee,
                                'backup',
                                'corr_cinsee_cpostal_gas_patch'),
                   'r').read().split('\n')
ls_corr_gas = [row.split(';') for row in ls_corr_gas]

# ################
# BUILD DFS
# ################

ls_columns = ['commune', 'code_postal', 'dpt', 'code_insee']
df_corr = pd.DataFrame(ls_corr_final, columns = ls_columns)
df_corr_gas = pd.DataFrame(ls_corr_final + ls_corr_gas, columns = ls_columns)

for df_temp in [df_corr, df_corr_gas]:
  for field in ['code_insee', 'code_postal']:
    df_temp[field] = df_temp[field].apply(lambda x: x.rjust(5, '0'))

# TODO: think of (manual) update process
ls_csv_output = [(df_corr, 'df_corr.csv', 0),
                 (df_corr, 'df_corr_quotes.csv', 1),
                 (df_corr_gas, 'df_corr_gas.csv', 0),
                 (df_corr_gas, 'df_corr_gas_quotes.csv', 1)]
for df_temp, file_name, quoting in ls_csv_output:
  df_temp.to_csv(os.path.join(path_dir_match_insee,
                              file_name),
                 quoting = quoting,
                 encoding = 'UTF-8',
                 index = False)

# ################################
# COMPARE WITH CURRENT INSEE FILES
# ################################

df_com = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_communes.csv'),
                     encoding = 'UTF-8',
                     dtype = {'DEP': str,
                              'CODGEO' : str})
set_current = set(df_com['CODGEO'].values)
set_outdated = set(df_corr['code_insee'].values).difference(set_current)
ls_outdated = list(set_outdated)
# print df_corr[df_corr['code_insee'].isin(ls_outdated)][0:20].to_string()

# ######################
# UPDATE CORRESPONDENCE?
# ######################

# Evolution in municipalities (?)
ls_com_maj = open(os.path.join(path_data,
                               'data_insee',
                               'communes',
                               'Communes_chgts',
                               'majcom2013.txt'),'r').read().split('\n')
#ls_com_maj_columns = ls_com_maj[0].split('\t')
ls_com_maj = [row.split('\t') for row in ls_com_maj if row.split('\t') != ['']]
df_com_maj = pd.DataFrame(ls_com_maj[1:], columns = ls_com_maj[0])
for field in ['ARTMAJ', 'NCC', 'ARTMIN', 'NCCENR', 'ARTICLCT', 'NCCCT']:
  df_com_maj[field] = df_com_maj[field].apply(lambda x: x.decode('latin-1'))

##example with (old) commune of Bohas in dpt 01
#print df_com_maj[df_com_maj['DEP'] == '01'].to_string()
## appears that old insee code is 'DEP' + 'COM' and new in 'POLE'
## can be several changes (here then merger but not chge in insee code)
#df_com_maj['EX_CI'] = df_com_maj['DEP'] + df_com_maj['COM']
#df_update = df_com_maj[['EX_CI', 'POLE']][(df_com_maj['EX_CI'] != '') &\
#                                          (df_com_maj['POLE'] != '')]
## only 81 elements, more to extract?


# Historical municipalities (?)
ls_com_hist = open(os.path.join(path_data,
                                'data_insee',
                                'communes',
                                'Communes_chgts',
                                'historiq2013.txt'),'r').read().split('\n')
#ls_com_hist_columns = ls_com_hist[0].split('\t')
ls_com_hist = [row.split('\t') for row in ls_com_hist if row.split('\t') != ['']]
df_com_hist = pd.DataFrame(ls_com_hist[1:], columns = ls_com_hist[0])
for field in ['NCCOFF', 'NCCANC']:
  df_com_hist[field] = df_com_hist[field].apply(lambda x: x.decode('latin-1'))

print df_com_hist[['DEP', 'COM', 'NCCOFF', 'COMECH', 'NCCANC']]\
        [df_com_hist['DEP'] == '01'].to_string()

## Large cities: arrdts (any use here?)
#Large_cities = {'13055' : ['%s' %elt for elt in range(13201, 13217)], # Marseille
#                '69123' : ['%s' %elt for elt in range(69381, 69390)], # Lyon
#                '75056' : ['%s' %elt for elt in range(75101, 75121)]} # Paris
