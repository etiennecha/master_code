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
# UNITES URBAINES 2010
# #######################

path_xls_uu = os.path.join(path_dir_communes,
                           'UnitesUrbaines',
                           'UU2010.xls')
wb_uu = xlrd.open_workbook(path_xls_uu)
print u'\nSheets in file Unites Urbaines:', wb_uu.sheet_names()

# Sheet: aires urbaines (info par au)
sh_uu_info = wb_uu.sheet_by_name(u'Liste des unités urbaines 2010')
ls_columns = sh_uu_info.row_values(1)
ls_rows = [sh_uu_info.row_values(i) for i in range(2, sh_uu_info.nrows)]
df_uu_info = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

# Sheet: communes (appartenance des communes aux au)
sh_uu_com = wb_uu.sheet_by_name(u'Communes')
ls_columns = sh_uu_com.row_values(1)
ls_rows = [sh_uu_com.row_values(i) for i in range(2, sh_uu_com.nrows)]
df_uu_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

## No need to merge: all info in df_uu_com
#df_uu = df_uu_com

# Identification of Commune at center of Unite Urbaine (if any)
se_libuu_is_libgeo = df_uu_com['LIBUU2010'][df_uu_com['LIBGEO'] ==\
                                            df_uu_com['LIBUU2010']]
## Check if city uniquely identified, no pbm if not
#se_temp_vc = se_libuu_is_libgeo.value_counts()
#print se_temp_vc[se_temp_vc > 1]
ls_libuu_unique = se_libuu_is_libgeo.unique()
ls_libuu_abroad = df_uu_com['LIBUU2010'][\
                  df_uu_com['LIBUU2010'].str.contains(u'\(partie française\)')].unique()
ls_libuu_nopbm = list(ls_libuu_unique) + list(ls_libuu_abroad)
# print df_au_com['LIBUU2010'][df_uu_com['LIBUU2010'].str.contains(u' - ')].value_counts()
ls_libuu_pbm = [x for x in df_uu_info['LIBUU2010'].unique() if x not in ls_libuu_nopbm]
print u'\nLIBUU not corresponding to one city:'
print ls_libuu_pbm
# Check if 'LIBGEO' in 'LIBUU2010'
# (ok for UU with two central cities + '(partie française)')
# i.e. can be two UU centers
df_uu_com['UU_CT'] = df_uu_com.apply(\
                        lambda row: 'YES' if row['LIBGEO'] in row['LIBUU2010']\
                                          else 'NO', axis=1)
# print df_uu_com[['UU2010', 'CODGEO']][df_uu_com['UU_Center'] == 'YES'].to_string()
df_center = df_uu_com[['UU2010', 'CODGEO']][df_uu_com['UU_CT'] == 'YES']
se_uu_vc = df_center['UU2010'].value_counts()
# print se_uu_vc[se_uu_vc > 1] # UU with more than one central city
## Might be more reasonable to exclude those.. e.g. "Marseille - Aix-en-Provence"
df_center.drop_duplicates('UU2010',
                          take_last = False,
                          inplace = True)
df_center.set_index('UU2010', inplace = True)
df_center['NB_CT'] = se_uu_vc
df_center.rename(columns = {'CODGEO' : 'CODGEO_CT'}, inplace = True)

# Merge back central city codgeo with df_au
df_uu_com = pd.merge(df_uu_com,
                     df_center,
                     how = 'left',
                     left_on = 'UU2010',
                     right_index = True)
df_uu_com.index = df_uu_com['CODGEO']

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

# Stats provided at AU (& UU) level!
sh_revenus_uu = wb_revenus.sheet_by_name(u'REVME_UU2010')
ls_columns = sh_revenus_uu.row_values(5)
ls_rows = [sh_revenus_uu.row_values(i) for i in range(6, sh_revenus_uu.nrows)]
df_revenus_uu = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)
df_revenus_uu = df_revenus_uu[ls_revenus_select_columns] 
df_revenus_uu.set_index('CODGEO', inplace=True)

# ######################
# BUILD DF AU AGGREGATED
# ######################

# population variables
ls_population_var_names = ['P10_POP', 'SUPERF']
for var_name in ls_population_var_names:
  df_uu_com[var_name] = df_population[var_name].convert_objects(convert_numeric = True)
df_uu_com['POPDENSITY10'] = df_uu_com['P10_POP'] / df_uu_com['SUPERF']
# logement variables
ls_logement_var_names = [u'P10_LOG', u'P10_MEN', u'P10_PMEN',
                         u'P10_RP_VOIT1P', 'P10_RP_VOIT1', 'P10_RP_VOIT2P']
for var_name in ls_logement_var_names:
  df_uu_com[var_name] = df_logement[var_name].convert_objects(convert_numeric = True)

# could do more elaborate groupby (with dedicated function)
# http://pandas.pydata.org/pandas-docs/dev/groupby.html
# http://stackoverflow.com/questions/15262134/ (ctd on next line)
# apply-different-functions-to-different-items-in-group-object-python-pandas
df_uu_agg = df_uu_com[['UU2010'] +\
                      ls_population_var_names +\
                      ls_logement_var_names].groupby('UU2010').sum()
df_uu_agg['POPDENSITY10'] = df_uu_agg['P10_POP'] / df_uu_agg['SUPERF']
## next two lines for temp display / can be dropped if better groupby
#df_uu_info.index = df_uu_info['UU2010']
#df_uu_agg['LIBUU2010'] = df_uu_info['LIBUU2010']
df_uu_agg = pd.merge(df_revenus_uu,
                     df_uu_agg,
                     how = 'right', # missing UUs in revenus?
                     left_index = True,
                     right_index = True)

# specific additions (could do before?)
df_uu_agg['NB_COMUU'] = df_uu_info['NB_COM']
df_uu_agg['TAILLEUU'] = df_uu_info['TAILLE']
df_uu_agg['TYPEUU'] = df_uu_info['TYPE']

df_uu_info.set_index('UU2010', inplace = True)

# todo: check missing UU... mainly DOMTOM: all info avail included??
ls_disp_info = ['LIBUU2010', 'NB_COM', 'TAILLE', 'TYPE', 'POP_MUN_2007']
df_uu_agg_final = pd.merge(df_uu_info[ls_disp_info],
                           df_uu_agg,
                           how = 'right',
                           left_index = True,
                           right_index = True)

# Add center and indicator of nb of centers (only first is kept then)
df_uu_center = df_uu_com[['UU2010', 'CODGEO', 'LIBGEO']]\
                        [df_uu_com['UU_CT'] == 'YES']
df_uu_center.drop_duplicates('UU2010', take_last = False, inplace = True)
df_uu_center.set_index('UU2010', inplace = True)
df_uu_center['NB_CT'] = se_uu_vc
df_uu_center.rename(columns = {'CODGEO' : 'CODGEO_CT',
                               'LIBGEO' : 'LIBGEO_CT'}, inplace = True)

df_uu_agg_final = pd.merge(df_uu_center,
                           df_uu_agg_final,
                           how = 'right',
                           left_index = True,
                           right_index = True)

df_uu_agg_final.sort(inplace = True)
df_uu_agg_final.to_csv(os.path.join(path_dir_insee_built,
                                    'df_uu_agg_final.csv'),
                       float_format='%.2f',
                       encoding = 'utf-8', 
                       index_label = 'UU2010')

print u'\nOverview df_au_agg_final:'
print df_uu_agg_final[['LIBUU2010', 'CODGEO_CT', 'LIBGEO_CT', 'NB_CT',
                       'P10_PMEN', 'PMENFIS10', 'MENFIS10', 'QUAR2UC10']][0:10].to_string()

ls_rural_uus = list(df_uu_agg_final.index[\
                      pd.isnull(df_uu_agg_final['CODGEO_CT'])])

# ######################
# BUILD FINAL DF UU COM
# ######################

# need df with au info at commune level (i.e. index = insee code)
# keep TYPE AND STATUT and if commune = center or not
df_uu_com_final = df_uu_com[['LIBGEO', 'UU2010', 'LIBUU2010',
                             'TYPE_2010', 'STATUT_2010',
                             'UU_CT', 'NB_CT', 'CODGEO_CT']]

# get rid of lines not corresponding to a geographic area (want nan in all cols)
df_uu_agg_geo = df_uu_agg.reset_index()
ls_drop_uu = list(df_uu_agg_final.index[\
                    pd.isnull(df_uu_agg_final['CODGEO_CT'])])
df_uu_agg_geo = df_uu_agg_geo[~(df_uu_agg_geo['UU2010'].isin(ls_drop_uu))]

df_uu_com_final.reset_index(inplace = True) # save column COGEO

df_uu_com_final = pd.merge(df_uu_com_final,
                           df_uu_agg_geo,
                           how='left',
                           left_on = 'UU2010',
                           right_on = 'UU2010')

df_uu_com_final.set_index('CODGEO', inplace = True)
df_uu_com_final.sort(inplace=True) # sort by index (was sorted by AU2010)

df_uu_com_final.to_csv(os.path.join(path_dir_insee_built,
                                    'df_uu_com_final.csv'),
                       float_format = '%.2f',
                       encoding = 'utf-8', 
                       index_label = u'CODGEO')

print u'\nOverview df_au_com_final:'
print df_uu_com_final[['LIBGEO', 'UU2010', 'LIBUU2010',
                       'CODGEO_CT', 'UU_CT', 'NB_CT',
                       'P10_PMEN', 'PMENFIS10', 'MENFIS10', 'QUAR2UC10']][0:10].to_string()
