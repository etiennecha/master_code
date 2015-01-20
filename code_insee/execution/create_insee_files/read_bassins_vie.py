#!/usr/bin/python
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
# BASSINS DE VIE 2012
# #######################

path_xls_bv = os.path.join(path_dir_communes,
                           'BassinsVie',
                           'bv-2012.xls')
wb_bv = xlrd.open_workbook(path_xls_bv)
print u'\nSheets in file Bassins de Vie:', wb_bv.sheet_names()

# Sheet: aires urbaines (info par au)
sh_bv_info = wb_bv.sheet_by_name(u'Liste des bassins de vie 2012')
ls_columns = sh_bv_info.row_values(1)
ls_rows = [sh_bv_info.row_values(i) for i in range(2, sh_bv_info.nrows)]
ls_rows = [row[:3] for row in ls_rows[:1666]] # ad hoc fix...
df_bv_info = pd.DataFrame(ls_rows, columns = ls_columns[:3], dtype = str)

# Sheet: communes (appartenance des communes aux au)
sh_bv_com = wb_bv.sheet_by_name(u'Communes')
ls_columns = sh_bv_com.row_values(1)
ls_rows = [sh_bv_com.row_values(i) for i in range(2, sh_bv_com.nrows)]
ls_rows = [row[:6] for row in ls_rows] # ad hoc fix...
df_bv_com = pd.DataFrame(ls_rows, columns = ls_columns[:6], dtype = str)

# Standardization of column names
df_bv_com.rename(columns = {'COM' : 'CODGEO',
                            'LIB_COM' : 'LIBGEO'}, inplace = True)
df_bv_com.index = df_bv_com['CODGEO'] # simply to rename index

# Identification of Commune at center of BV (essentially given here actually)
ls_libbv_is_libgeo = df_bv_com['LIBBV'][df_bv_com['LIBGEO'] == df_bv_com['LIBBV']].values
ls_ok = set(list(ls_libbv_is_libgeo))
# print df_bv_com['LIBBV'][df_bv_com['LIBBV'].str.contains(u' - ')].value_counts()
ls_check = [x for x in df_bv_info['LIBBV'].values if x not in ls_ok]
# Check if 'LIBGEO' in 'LIBBV'
# (ok for BV with two central cities + '(partie française)')
# i.e. can be two BV centers
df_bv_com['BV_CT'] = df_bv_com.apply(\
                           lambda row: 'YES' if row['LIBGEO'] in row['LIBBV']\
                                             else 'NO', axis=1)

df_center = df_bv_com[['BV', 'CODGEO']][df_bv_com['BV_CT'] == 'YES']
se_bv_vc = df_center['BV'].value_counts()
# print se_uu_vc[se_uu_vc > 1] # UU with more than one central city
## Might be more reasonable to exclude those.. e.g. "Marseille - Aix-en-Provence"
df_center.drop_duplicates('BV',
                          take_last = False,
                          inplace = True)
df_center.set_index('BV', inplace = True)
df_center['NB_CT'] = se_bv_vc
df_center.rename(columns = {'CODGEO' : 'CODGEO_CT'}, inplace = True)

# Merge back central city codgeo with df_au
df_bv_com = pd.merge(df_bv_com,
                     df_center,
                     how = 'left',
                     left_on = 'BV',
                     right_index = True)
df_bv_com.index = df_bv_com['CODGEO'] # set index back to CODGEO

# ##################
# COMMUNE LEVEL DATA
# ##################

# todo: read and store those to make importation easy

# #######################
# POPULATION 2010

path_xls_population = os.path.join(path_dir_communes,
                                   'Pop',
                                   'base-cc-evol-struct-pop-2010.xls')

wb_population = xlrd.open_workbook(path_xls_population)
print u'\nSheets in file Population:', wb_population.sheet_names()

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
print u'\nSheets in file Logement:', wb_logement.sheet_names()

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
print u'\nSheets in file Revenus fisc:', wb_revenus.sheet_names()

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

## Stats provided at AU (& UU) level!
#sh_revenus_uu = wb_revenus.sheet_by_name(u'REVME_UU2010')
#ls_columns = sh_revenus_uu.row_values(5)
#ls_rows = [sh_revenus_uu.row_values(i) for i in range(6, sh_revenus_uu.nrows)]
#df_revenus_uu = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)
#df_revenus_uu = df_revenus_uu[ls_revenus_select_columns] 
#df_revenus_uu.set_index('CODGEO', inplace=True)

# ######################
# BUILD DF BV AGGREGATED
# ######################

# population variables
ls_population_var_names = ['P10_POP', 'SUPERF']
for var_name in ls_population_var_names:
  df_bv_com[var_name] = df_population[var_name].convert_objects(convert_numeric = True)
df_bv_com['POPDENSITY10'] = df_bv_com['P10_POP'] / df_bv_com['SUPERF']
# logement variables
ls_logement_var_names = [u'P10_LOG', u'P10_MEN', u'P10_PMEN',
                         u'P10_RP_VOIT1P', 'P10_RP_VOIT1', 'P10_RP_VOIT2P']
for var_name in ls_logement_var_names:
  df_bv_com[var_name] = df_logement[var_name].convert_objects(convert_numeric = True)

# could do more elaborate groupby (with dedicated function)
# http://pandas.pydata.org/pandas-docs/dev/groupby.html
# http://stackoverflow.com/questions/15262134/ (ctd on next line)
# apply-different-functions-to-different-items-in-group-object-python-pandas
df_bv_agg = df_bv_com[['BV'] +\
                      ls_population_var_names +\
                      ls_logement_var_names].groupby('BV').sum()
df_bv_agg['POPDENSITY10'] = df_bv_agg['P10_POP'] / df_bv_agg['SUPERF']
## next two lines for temp display / can be dropped if better groupby
#df_bv_info.index = df_bv_info['UU2010']
#df_bv_agg['LIBUU2010'] = df_bv_info['LIBUU2010']
#df_bv_agg = pd.merge(df_bv_agg, df_revenus_uu, left_index = True, right_index = True)

df_bv_agg['NB_COMBV'] = df_bv_info['NB_COM']

df_bv_info.set_index('BV', inplace = True)

ls_disp_info = ['LIBBV']
df_bv_agg_final = pd.merge(df_bv_info[ls_disp_info],
                           df_bv_agg,
                           how = 'right',
                           left_index = True,
                           right_index = True)

# Add center and indicator of nb of centers (only first is kept then)
df_bv_center = df_bv_com[['BV', 'CODGEO', 'LIBGEO']]\
                        [df_bv_com['BV_CT'] == 'YES']
df_bv_center.drop_duplicates('BV', take_last = False, inplace = True)
df_bv_center.set_index('BV', inplace = True)
df_bv_center['NB_CT'] = se_bv_vc
df_bv_center.rename(columns = {'CODGEO' : 'CODGEO_CT',
                               'LIBGEO' : 'LIBGEO_CT'}, inplace = True)
# essentially redundant with BV and LIBBV

df_bv_agg_final.sort(inplace = True)
df_bv_agg_final = pd.merge(df_bv_center,
                           df_bv_agg_final,
                           how = 'right',
                           left_index = True,
                           right_index = True)

df_bv_agg_final.to_csv(os.path.join(path_dir_insee_built,
                                    'df_bv_agg_final.csv'),
                       float_format='%.2f',
                       encoding='utf-8', 
                       index_label = 'BV')

print u'\nOverview df_bv_agg_final:'
print df_bv_agg_final[['LIBBV', 'CODGEO_CT', 'LIBGEO_CT', 'NB_CT',
                       'P10_PMEN']][0:10].to_string()

# ###################
# BUILD FINAL DF BV
# ###################

df_bv_agg.reset_index(inplace = True)

# need df with au info at commune level (i.e. index = insee code)
# keep TYPE AND STATUT and if commune = center or not
df_bv_com_final = df_bv_com[['LIBGEO', 'BV', 'LIBBV',
                             'BV_CT', 'NB_CT', 'CODGEO_CT']]

df_bv_com_final.reset_index(inplace = True) # save column COGEO

df_bv_com_final = pd.merge(df_bv_com_final,
                           df_bv_agg,
                           how='left',
                           left_on = 'BV',
                           right_on = 'BV')

df_bv_com_final.set_index('CODGEO', inplace = True)
df_bv_com_final.sort(inplace=True)

df_bv_com_final.to_csv(os.path.join(path_dir_insee_built,
                                    'df_bv_com_final.csv'),
                       float_format = '%.2f',
                       encoding = 'utf-8', 
                       index_label = 'CODGEO')

print u'\nOverview df_au_com_final:'
print df_bv_com_final[['LIBGEO', 'BV', 'LIBBV',
                       'CODGEO_CT', 'BV_CT', 'NB_CT',
                       'P10_PMEN']][0:10].to_string()

# todo: add info on population revenu... e.g. central city only
