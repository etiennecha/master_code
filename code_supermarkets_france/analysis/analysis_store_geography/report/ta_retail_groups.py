#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import datetime as datetime
import pandas as pd
import matplotlib.pyplot as plt
import pprint

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_insee = os.path.join(path_data, 'data_insee')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

# Default float format: no digit after decimal point
pd.set_option('float_format', '{:10.0f}'.format)
# Float print functions for display
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ####################
# LOAD DATA
# ####################

df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa_active_hsx.csv'),
                     dtype = {u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

# ################################
# OVERVIEW OF RETAIL GROUP STORES
# ################################

ls_stats = ['Nb_', 'Cum_S_', 'Avg_S_']
ls_store_types = ['H', 'S', 'X']
ls_columns = [''.join((y,x)) for x in ls_store_types for y in ls_stats]
# Main loop
ls_rows_rg = []
for retail_group in df_lsa['groupe_alt'].unique():
  df_lsa_rg = df_lsa[df_lsa['groupe_alt'] == retail_group]
  row = []
  for st_type in ls_store_types:
    nb_stores = float(len(df_lsa_rg[df_lsa_rg['type_alt'] == st_type]))
    cum_surf = df_lsa_rg['surface'][df_lsa_rg['type_alt'] == st_type].sum() / 1000000
    avg_surf = df_lsa_rg['surface'][df_lsa_rg['type_alt'] == st_type].mean()
    row += [nb_stores, cum_surf, avg_surf]
  ls_rows_rg.append(row)
# Bottom row
row = []
for st_type in ls_store_types:
  nb_stores = float(len(df_lsa[df_lsa['type_alt'] == st_type]))
  cum_surf = df_lsa['surface'][df_lsa['type_alt'] == st_type].sum() / 1000000
  avg_surf = df_lsa['surface'][df_lsa['type_alt'] == st_type].mean()
  row += [nb_stores, cum_surf, avg_surf]
ls_rows_rg.append(row)

df_rgs_2 = pd.DataFrame(ls_rows_rg,
                        columns = ls_columns,
                        index = list(df_lsa['groupe_alt'].unique()) + ['ALL'])

# Add Nb total and Cum surf
df_rgs_2['Nb_All'] = df_rgs_2[['Nb_H', 'Nb_S', 'Nb_X']].sum(axis = 1)
df_rgs_2['Cum_S_All'] = df_rgs_2[['Cum_S_H', 'Cum_S_S', 'Cum_S_X']].sum(axis = 1)
df_rgs_2.sort('Nb_All', ascending = False, inplace = True)

# Table percentages
df_rgs_2_pc = df_rgs_2.copy()
df_rgs_2_pc[['Nb_H', 'Nb_S', 'Nb_X', 'Nb_All']] =\
   df_rgs_2_pc[['Nb_H', 'Nb_S', 'Nb_X', 'Nb_All']].apply(\
     lambda x: x * 100 / x['Nb_All'], axis = 1)
df_rgs_2_pc[['Cum_S_H', 'Cum_S_S', 'Cum_S_X', 'Cum_S_All']] =\
   df_rgs_2_pc[['Cum_S_H', 'Cum_S_S', 'Cum_S_X', 'Cum_S_All']].apply(\
     lambda x: x * 100 / x['Cum_S_All'], axis = 1)
df_rgs_2_pc[['Avg_S_H', 'Avg_S_S', 'Avg_S_X']] = np.nan

ls_col_disp = ['Nb_All', 'Nb_H', 'Nb_S', 'Nb_X',
               'Cum_S_All', 'Cum_S_H', 'Cum_S_S', 'Cum_S_X',
               'Avg_S_H', 'Avg_S_S', 'Avg_S_X']

ls_row_disp = list(df_rgs_2.index[1:])
ls_row_disp.remove('AUTRE')
ls_row_disp += ['AUTRE', 'ALL']

dict_formatters = {'Cum_S_All' : format_float_float,
                   'Cum_S_H' : format_float_float,
                   'Cum_S_S' : format_float_float,
                   'Cum_S_X' : format_float_float}

## Pbm: prints 100.00 hence rather merge string after latex ouput (see italic?)
#ls_rows_rgs_fin = []
#for x in ls_row_disp:
#  ls_rows_rgs_fin.append(df_rgs_2[ls_col_disp].loc[x])
#  ls_rows_rgs_fin.append(df_rgs_2_pc[ls_col_disp].loc[x])
#df_rgs_2_fin = pd.concat(ls_rows_rgs_fin, axis = 1).T
#print df_rgs_2_fin[ls_col_disp].to_string(formatters = dict_formatters)

latex_rgs_2 = u''
for (x,y) in zip(df_rgs_2[ls_col_disp].loc[ls_row_disp].\
                   to_latex(formatters = dict_formatters).\
                     replace('nan', '   ').split('\n')[4:-2],
                 df_rgs_2_pc[ls_col_disp].loc[ls_row_disp].\
                   to_latex().replace('nan', '   ').split('\n')[4:-2]):
  latex_rgs_2 += u'%s\n'%x
  latex_rgs_2 += u'%s\n'%y
print latex_rgs_2

# ######################################
# OVERVIEW OF RETAIL GROUP CHAIN STORES
# ######################################

# TODO: add lines for independent/integrated when it makes sense
# TODO: add total line

dict_rename_rg = {'len' : '#Tot',
                  'mean': 'Avg S.',
                  'median': 'Med S.',
                  'min': 'Min S.',
                  'max': 'Max S.',
                  'sum': 'Cum S.',
                  'H' : '#Hyp',
                  'S' : '#Sup',
                  'X' : '#Dis'}

ls_rg_disp = ['#Tot', '#Hyp', '#Sup', '#Dis',
               'Avg S.', 'Med S.', 'Min S.', 'Max S.', 'Cum S.']

dict_formatters = {'Cum S.' : format_float_float}

ls_retail_groups = [x for x in df_lsa['groupe_alt'].unique() if x != 'AUTRE']
for retail_group in ls_retail_groups:
  print '\n', retail_group
  
  # All group stores
  df_lsa_rg = df_lsa[df_lsa['groupe_alt'] == retail_group]
  gbg = df_lsa_rg[['enseigne_alt', 'surface']].groupby('enseigne_alt',
                                                       as_index = False)
  df_surf_rg = gbg.agg([len, np.mean, np.median, min, max, np.sum])['surface']
  df_surf_rg.sort('len', ascending = False, inplace = True)
  # print df_surf_rg.to_string()
  df_types_rg = pd.DataFrame(columns = ['H', 'S', 'X']).T
  for enseigne in df_lsa_rg['enseigne_alt'].unique():
    se_types_vc = df_lsa_rg['type_alt'][df_lsa_rg['enseigne_alt'] ==\
                                          enseigne].value_counts()
    df_types_rg[enseigne] = se_types_vc
  df_types_rg.fillna(0, inplace = True)
  df_types_rg = df_types_rg.T
  # print df_types_rg.to_string()
  df_rg = pd.merge(df_types_rg, df_surf_rg, left_index = True, right_index = True)
  df_rg.sort('len', ascending = False, inplace = True)
  df_rg.rename(columns = dict_rename_rg, inplace = True)
  df_rg['Cum S.'] = df_rg['Cum S.'] / 1000000
  print df_rg[ls_rg_disp].to_latex(formatters = dict_formatters)
  
  # Independent stores
  df_lsa_rg_ind = df_lsa[(df_lsa['groupe_alt'] == retail_group) &
                             (df_lsa[u'int_ind'] == 'independant')]
  if len(df_lsa_rg_ind) != 0:
    gbg = df_lsa_rg_ind[['enseigne_alt', 'surface']].groupby('enseigne_alt',
                                                             as_index = False)
    df_surf_rg_ind = gbg.agg([len, np.mean, np.median, min, max, np.sum])['surface']
    df_surf_rg_ind.sort('len', ascending = False, inplace = True)
    # print df_surf_rg_ind.to_string()
    df_types_rg_ind = pd.DataFrame(columns = ['H', 'S', 'X']).T
    for enseigne in df_lsa_rg_ind['enseigne_alt'].unique():
      se_types_vc = df_lsa_rg_ind['type_alt'][df_lsa_rg_ind['enseigne_alt'] ==\
                                                enseigne].value_counts()
      df_types_rg_ind[enseigne] = se_types_vc
    df_types_rg_ind.fillna(0, inplace = True)
    df_types_rg_ind = df_types_rg_ind.T
    # print df_types.to_string()
    df_rg_ind = pd.merge(df_types_rg_ind, df_surf_rg_ind,
                         left_index = True, right_index = True)
    df_rg_ind.sort('len', ascending = False, inplace = True)
    df_rg_ind.rename(columns = dict_rename_rg, inplace = True)
    df_rg_ind['Cum S.'] = df_rg_ind['Cum S.'] / 1000000
    print df_rg_ind[ls_rg_disp].to_latex(formatters = dict_formatters)
  else:
    print 'No indpt store'
