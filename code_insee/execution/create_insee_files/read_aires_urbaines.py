﻿#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import xlrd
import re
import pandas as pd

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_communes = os.path.join(path_dir_insee, 'communes')
path_dir_insee_built = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:10,.0f}'.format)
pd.set_option('display.max_colwidth', 30)

# #######################
# AIRES URBAINES 2010
# #######################

path_xls_au = os.path.join(path_dir_communes,
                           'AiresUrbaines',
                           'AU2010.xls')
wb_au = xlrd.open_workbook(path_xls_au)
print u'\nSheets in file Aires Urbaines:', wb_au.sheet_names()

# Sheet: aires urbaines (info par au)
sh_au_info = wb_au.sheet_by_name(u'Zonage en aires urbaines 2010')
ls_columns = sh_au_info.row_values(1)
ls_rows = [sh_au_info.row_values(i) for i in range(2, sh_au_info.nrows)]
df_au_info = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

# Sheet: communes (appartenance des communes aux au)
sh_au_com = wb_au.sheet_by_name(u'Composition communale')
ls_columns = sh_au_com.row_values(1)
ls_rows = [sh_au_com.row_values(i) for i in range(2, sh_au_com.nrows)]
df_au_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

## No need to merge: all info in df_au_com
#df_au = df_au_com

# Identification of Commune at center of Aire Urbaine (if any)
se_libau_is_libgeo = df_au_com['LIBAU2010'][df_au_com['LIBGEO'] ==\
                                            df_au_com['LIBAU2010']]
## Check if city uniquely identified, no pbm if not
#se_temp_vc = se_libau_is_libgeo.value_counts()
#print se_temp_vc[se_temp_vc > 1]
ls_libau_unique = se_libau_is_libgeo.unique()
ls_libau_abroad = df_au_com['LIBAU2010'][\
                  df_au_com['LIBAU2010'].str.contains(u'\(partie française\)')].unique()
ls_libau_nopbm = list(ls_libau_unique) + list(ls_libau_abroad)
# print df_au_com['LIBAU2010'][df_au_com['LIBAU2010'].str.contains(u' - ')].value_counts()
ls_libau_pbm = [x for x in df_au_info['LIBGEO'].unique() if x not in ls_libau_nopbm]
print u'\nLIBAU not corresponding to one city:'
print ls_libau_pbm
# Check if 'LIBGEO' in 'LIBAU2010'
# (ok for AU with two central cities + '(partie française)')
# i.e. can be two AU centers
df_au_com['AU_CT'] = df_au_com.apply(\
                        lambda row: 'YES' if row['LIBGEO'] in row['LIBAU2010']\
                                          else 'NO', axis=1)
# print df_au_com[['AU2010', 'CODGEO']][df_au_com['AU_Center'] == 'YES'].to_string()
df_center = df_au_com[['AU2010', 'CODGEO']][df_au_com['AU_CT'] == 'YES']
se_au_vc = df_center['AU2010'].value_counts()
# print se_au_vc[se_au_vc > 1] # AU with more than one central city
## Might be more reasonable to exclude those.. e.g. "Marseille - Aix-en-Provence"
df_center.drop_duplicates('AU2010',
                          take_last = False,
                          inplace = True)
df_center.set_index('AU2010', inplace = True)
df_center['NB_CT'] = se_au_vc
df_center.rename(columns = {'CODGEO' : 'CODGEO_CT'}, inplace = True)

# Merge back central city codgeo with df_au
df_au_com = pd.merge(df_au_com,
                     df_center,
                     how = 'left',
                     left_on = 'AU2010',
                     right_index = True)
df_au_com.index = df_au_com['CODGEO']

# ##################
# COMMUNE LEVEL DATA
# ##################

# DOMTOM data not captured through following section so far
# todo: read and store those to make importation easy

# #######################
# POPULATION 2010

path_xls_population = os.path.join(path_dir_communes,
                                   'Pop',
                                   'base-cc-evol-struct-pop-2010.xls')

wb_population = xlrd.open_workbook(path_xls_population)
print u'\nSheets in Population', wb_population.sheet_names()

sh_population_com = wb_population.sheet_by_name(u'COM')
ls_columns = sh_population_com.row_values(5)
ls_rows = [sh_population_com.row_values(i) for i in range(6, sh_population_com.nrows)]
df_population_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

sh_population_arm = wb_population.sheet_by_name(u'ARM')
ls_columns = sh_population_arm.row_values(5)
ls_rows = [sh_population_arm.row_values(i) for i in range(6, sh_population_arm.nrows)]
df_population_arm = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

df_population = pd.concat([df_population_com, df_population_arm], ignore_index = True)
ls_population_select_columns = ['CODGEO', 'LIBGEO', 'REG', 'DEP',
                                'ZE2010', 'P10_POP', 'SUPERF']
df_population = df_population[ls_population_select_columns]
df_population.index = df_population['CODGEO']

# #######################
# LOGEMENT 2010

path_xls_logement = os.path.join(path_dir_communes,
                                 'Logement',
                                 'base-cc-logement-2010.xls')

wb_logement = xlrd.open_workbook(path_xls_logement)
print u'\nSheets in Logement', wb_logement.sheet_names()

sh_logement_com = wb_logement.sheet_by_name(u'COM')
ls_columns = sh_logement_com.row_values(5)
ls_rows = [sh_logement_com.row_values(i) for i in range(6, sh_logement_com.nrows)]
df_logement_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

sh_logement_arm = wb_logement.sheet_by_name(u'ARM')
ls_columns = sh_logement_arm.row_values(5)
ls_rows = [sh_logement_arm.row_values(i) for i in range(6, sh_logement_arm.nrows)]
df_logement_arm = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

df_logement = pd.concat([df_logement_com, df_logement_arm], ignore_index = True)
# P10_RP = P10_MEN and P_10_PMEN = P10_NPER_NP (resp. nb menages, nb habitants)
ls_logement_select_columns = [u'CODGEO', u'LIBGEO',
                              u'P10_LOG', u'P10_MEN', u'P10_PMEN',
                              u'P10_RP_VOIT1P', 'P10_RP_VOIT1', 'P10_RP_VOIT2P']
df_logement = df_logement[ls_logement_select_columns] 
df_logement.index = df_logement['CODGEO']

# #######################
# REVENUS FISCAUX 2010

path_xls_revenus = os.path.join(path_dir_communes,
                                'Revenus_fiscaux',
                                'base-cc-rev-fisc-loc-menage-10.xls')

wb_revenus = xlrd.open_workbook(path_xls_revenus)
print u'\nSheets in Revenus fisc', wb_revenus.sheet_names()

sh_revenus_com = wb_revenus.sheet_by_name(u'REVME_COM')
ls_columns = sh_revenus_com.row_values(5)
ls_rows = [sh_revenus_com.row_values(i) for i in range(6, sh_revenus_com.nrows)]
df_revenus_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

sh_revenus_arm = wb_revenus.sheet_by_name(u'REVME_ARM')
ls_columns = sh_revenus_arm.row_values(5)
ls_rows = [sh_revenus_arm.row_values(i) for i in range(6, sh_revenus_arm.nrows)]
df_revenus_arm = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

df_revenus = pd.concat([df_revenus_com, df_revenus_arm], ignore_index = True)
ls_revenus_select_columns = [u'CODGEO', u'MENFIS10', u'PMENFIS10', u'MENIMP10',
                             u'QUAR1UC10', u'QUAR2UC10', u'QUAR3UC10', u'RDUC10',
                             u'PTSA10', u'PPEN10', u'PBEN10', u'PAUT10']
df_revenus = df_revenus[ls_revenus_select_columns] 
df_revenus.index = df_revenus['CODGEO']

# Stats provided at AU (& UU) level!
sh_revenus_au = wb_revenus.sheet_by_name(u'REVME_AU2010')
ls_columns = sh_revenus_au.row_values(5)
ls_rows = [sh_revenus_au.row_values(i) for i in range(6, sh_revenus_au.nrows)]
df_revenus_au = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)
df_revenus_au = df_revenus_au[ls_revenus_select_columns] 
df_revenus_au.set_index('CODGEO', inplace=True)

# ######################
# BUILD DF AU AGGREGATED
# ######################

# population variables
ls_population_var_names = ['P10_POP', 'SUPERF']
for var_name in ls_population_var_names:
  df_au_com[var_name] = df_population[var_name].convert_objects(convert_numeric = True)
df_au_com['POPDENSITY10'] = df_au_com['P10_POP'] / df_au_com['SUPERF']
# logement variables
ls_logement_var_names = [u'P10_LOG', u'P10_MEN', u'P10_PMEN',
                         u'P10_RP_VOIT1P', 'P10_RP_VOIT1', 'P10_RP_VOIT2P']
for var_name in ls_logement_var_names:
  df_au_com[var_name] = df_logement[var_name].convert_objects(convert_numeric = True)

# could do more elaborate groupby (with dedicated function)
# http://pandas.pydata.org/pandas-docs/dev/groupby.html
# http://stackoverflow.com/questions/15262134/ (ctd on next line)
# apply-different-functions-to-different-items-in-group-object-python-pandas
df_au_agg = df_au_com[['AU2010'] +\
                      ls_population_var_names +\
                      ls_logement_var_names].groupby('AU2010').sum()
df_au_agg['POPDENSITY10'] = df_au_agg['P10_POP'] / df_au_agg['SUPERF']

df_au_agg = pd.merge(df_revenus_au,
                     df_au_agg,
                     how = 'right', # missing AUs in revenus
                     left_index = True,
                     right_index = True)

# prepare df_au_info for merger with df_au_agg
df_au_info.rename(columns={'CODGEO': 'AU2010',
                           'LIBGEO' : 'LIBAU2010'},
                  inplace=True)
df_au_info.set_index('AU2010', inplace = True)

df_au_agg_final = pd.merge(df_au_info,
                           df_au_agg,
                           how = 'right',
                           left_index = True,
                           right_index = True)

# Add center and indicator of nb of centers (only first is kept then)
df_au_center = df_au_com[['AU2010', 'CODGEO', 'LIBGEO']]\
                        [df_au_com['AU_CT'] == 'YES']
df_au_center.drop_duplicates('AU2010', take_last = False, inplace = True)
df_au_center.set_index('AU2010', inplace = True)
df_au_center['NB_CT'] = se_au_vc
df_au_center.rename(columns = {'CODGEO' : 'CODGEO_CT',
                               'LIBGEO' : 'LIBGEO_CT'}, inplace = True)

df_au_agg_final = pd.merge(df_au_center,
                           df_au_agg_final,
                           how = 'right',
                           left_index = True,
                           right_index = True)

df_au_agg_final.sort(inplace = True)
df_au_agg_final.to_csv(os.path.join(path_dir_insee_built,
                                    'df_au_agg_final.csv'),
                       float_format='%.2f',
                       encoding='utf-8',
                       index_label = 'AU2010')

print u'\nOverview df_au_agg_final:'
print df_au_agg_final[['LIBAU2010', 'CODGEO_CT', 'LIBGEO_CT', 'NB_CT',
                       'P10_PMEN', 'PMENFIS10', 'MENFIS10', 'QUAR2UC10']][0:10].to_string()

#print df_au_agg_final[['LIBAU2010', 'CODGEO_CT', 'LIBGEO_CT', 'NB_CT',
#                       'P10_PMEN', 'PMENFIS10', 'MENFIS10', 'QUAR2UC10']].to_string()
## check total pop consistant with insee data (ok 64.6)
## codes AU2010: 000, 997 and 998: not one geog area
#print df_au_agg_final['P10_POP'].sum()
#print df_au_agg_final.ix['000']

# ###################
# BUILD FINAL DF AU
# ###################

# need df with au info at commune level (i.e. index = insee code)
# keep TAU2010, CATAEU2010 and if commune = center or not
df_au_com_final = df_au_com[['LIBGEO', 'AU2010', 'LIBAU2010',
                             'TAU2010', 'CATAEU2010',
                             'AU_CT', 'NB_CT', 'CODGEO_CT']]

# get rid of lines not corresponding to a geographic area (want nan in all cols)
df_au_agg_geo = df_au_agg.reset_index()
df_au_agg_geo = df_au_agg_geo[~(df_au_agg_geo['AU2010'].isin(['000', '997', '998']))]

df_au_com_final.reset_index(inplace = True) # save column COGEO

df_au_com_final = pd.merge(df_au_com_final,
                           df_au_agg_geo,
                           how = 'left',
                           left_on = 'AU2010',
                           right_on = 'AU2010')

df_au_com_final.set_index('CODGEO', inplace = True)
df_au_com_final.sort(inplace = True)

df_au_com_final.to_csv(os.path.join(path_dir_insee_built,
                                    'df_au_com_final.csv'),
                       float_format = '%.2f',
                       encoding = 'utf-8', 
                       index_label = u'CODGEO')

print u'\nOverview df_au_com_final:'
print df_au_com_final[['LIBGEO', 'AU2010', 'LIBAU2010',
                       'CODGEO_CT', 'AU_CT', 'NB_CT',
                       'P10_PMEN', 'PMENFIS10', 'MENFIS10', 'QUAR2UC10']][0:10].to_string()
