#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import xlrd
import re
import pandas as pd

# READ AND IMPLEMENT:
# http://rdf.insee.fr/
# http://rdf.insee.fr/common/appli-help.html
# http://rdf.insee.fr/common/sparql-help.html


path_dir_insee = os.path.join(path_data, 'data_insee')

# ################################# 
# 1/ DATA AT CITY LEVEL ("COMMUNE")
# #################################

path_dir_communes = os.path.join(path_dir_insee, 'communes')

# ####################################################
# MOBILITY BETWEEN HOME AND WORK (not used so far)

path_xls_mob = os.path.join(path_dir_communes,
                            'Mobilite_Dom_Travail',
                            'base-flux-mobilite-domicile-lieu-travail-2010.xls')
wb_mob = xlrd.open_workbook(path_xls_mob)
# sh = wb.sheet_by_index(0)
# sh_nb_rows = sh.nrows
# first_column = sh.col_values(0)
# cell_A1 = sh.cell(0,0).value
# cell_C4 = sh.cell(rowx=3, colx=2).value
print 'Sheets in file', wb_mob.sheet_names()

# Communes info: people working in communes vs. outside
sh_com_work = wb_mob.sheet_by_name(u'TOTAL')
ls_columns = sh_com_work.row_values(5) # 4 has details but long fields
ls_rows = [sh_com_work.row_values(i) for i in range(6, sh_com_work.nrows)]
df_com_work = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

# Mobility info: people commuting to work
sh_mob = wb_mob.sheet_by_name(u'FLUX>=100')
ls_columns = sh_mob.row_values(5)
ls_rows = [sh_mob.row_values(i) for i in range(6, sh_mob.nrows)]
df_mob = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

# ########################
# UNITES URBAINES 2010

path_xls_uu = os.path.join(path_dir_communes, 'UnitesUrbaines', 'UU2010.xls')
wb_uu = xlrd.open_workbook(path_xls_uu)
print 'Sheets in file', wb_uu.sheet_names()

# Sheet: unites urbaines (info par uu)
sh_uu_info = wb_uu.sheet_by_name(u'Liste des unit\xe9s urbaines 2010')
ls_columns = sh_uu_info.row_values(1)
ls_rows = [sh_uu_info.row_values(i) for i in range(2, sh_uu_info.nrows)]
df_uu_info = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

# Sheet: communes (appartenance des communes aux uu)
sh_uu_com = wb_uu.sheet_by_name(u'Communes')
ls_columns = sh_uu_com.row_values(1)
ls_rows = [sh_uu_com.row_values(i) for i in range(2, sh_uu_com.nrows)]
# note: statut: r(rural)/c(urbain centre)/b(urbain banlieue)/i(urbain isole)
df_uu_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

# Check, clean and merge 
df_uu_info.rename(columns={'NB_COM' : 'NB_COM_UU',
                           'POP_MUN_2007' : 'POP_MUN_07_UU',
                           'TAILLE' : 'TAILLE_UU',
                           'TYPE' : 'TYPE_UU'}, inplace=True) 
df_uu_com.rename(columns={'TYPE_2010' : 'TYPE_2010_COM',
                          'STATUT_2010' : 'STATUT_2010_COM',
                          'POP_MUN_2007': 'POP_MUN_2007_COM'}, inplace=True)  
del(df_uu_com['LIBUU2010'], df_uu_com['REG'], df_uu_com['DEP']) 
df_uu = pd.merge(df_uu_info, df_uu_com, on = 'UU2010')

# #######################
# AIRES URBAINES 2010

path_xls_au = os.path.join(path_dir_communes, 'AiresUrbaines', 'AU2010.xls')
wb_au = xlrd.open_workbook(path_xls_au)
print 'Sheets in file', wb_au.sheet_names()

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

# No need to merge: all info in df_au_com 
df_au = df_au_com

# #######################
# POPULATION 2010

path_xls_population = os.path.join(path_dir_communes, 'Pop', 'base-cc-evol-struct-pop-2010.xls')

wb_population = xlrd.open_workbook(path_xls_population)
print 'Sheets in file', wb_population.sheet_names()

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

# #######################
# LOGEMENT 2010

path_xls_logement = os.path.join(path_dir_communes, 'Logement', 'base-cc-logement-2010.xls')

wb_logement = xlrd.open_workbook(path_xls_logement)
print 'Sheets in file', wb_logement.sheet_names()

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

# #######################
# REVENUS FISCAUX 2010

path_xls_revenus = os.path.join(path_dir_communes,
                                'Revenus_fiscaux',
                                'base-cc-rev-fisc-loc-menage-10.xls')

wb_revenus = xlrd.open_workbook(path_xls_revenus)
print 'Sheets in file', wb_revenus.sheet_names()

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

# #################################### 
# 1E/ Merge INSEE communes dataframes

print '\n', df_uu.info()
print '\n', df_au.info()
print '\n', df_population.info()
print '\n', df_logement.info()
del(df_au['LIBGEO'], df_population['LIBGEO'], df_logement['LIBGEO'])
df_insee = pd.merge(df_uu, df_au, on = 'CODGEO')
df_insee = pd.merge(df_insee, df_population, on = 'CODGEO', how = 'left')
df_insee = pd.merge(df_insee, df_logement, on = 'CODGEO', how = 'left')

lsd_revenus = ['CODGEO', 'MENFIS10', 'PMENFIS10', 'MENIMP10', 
               'QUAR1UC10', 'QUAR2UC10', 'QUAR3UC10',
               'RDUC10', 'PTSA10', 'PPEN10', 'PBEN10', 'PAUT10']
df_insee = pd.merge(df_insee, df_revenus[lsd_revenus], on = 'CODGEO', how = 'left')

print '\nInsee extract:'
print df_insee.info()

# #######
# OUTPUT

path_dir_insee_built = os.path.join(path_dir_insee,
                                    'data_extracts')
df_insee.to_csv(os.path.join(path_dir_insee_built,
                             'data_insee_extract.csv'),
                float_format='%.3f',
                encoding='utf-8',
                index=False)

## todo: drop?
#path_dir_gas_source = os.path.join(path_data,
#                                   'data_gasoline',
#                                   'data_source',
#                                   'data_other')
#df_insee.to_csv(os.path.join(path_dir_gas_source,
#                             'data_insee_extract.csv'),
#                float_format='%.3f',
#                encoding='utf-8',
#                index=False)

# ########################
# ENRICHED VERSION

# Adding columns with aggregated data using groupby
# check : http://bconnelly.net/2013/10/22/summarizing-data-in-python-with-pandas/
ls_columns_interest = ['P10_LOG', 'P10_MEN', 'P10_PMEN',
                       'P10_RP_VOIT1P', 'P10_RP_VOIT1', 'P10_RP_VOIT2P']
for column in ls_columns_interest:
  df_insee[column] = df_insee[column].apply(lambda x: float(x) if x else float('nan'))
df_uu_agg = df_insee.groupby('UU2010')[ls_columns_interest].sum()
# enriched data
df_insee = pd.merge(df_insee,
                    df_uu_agg,
                    left_on = "UU2010",
                    right_index = True,
                    suffixes = ('_COM', '_UU'))

print '\nInsee extract enriched:'
print df_insee.info() 

# http://pandas.pydata.org/pandas-docs/dev/groupby.html
# todo: read # http://stackoverflow.com/questions/15262134/
# apply-different-functions-to-different-items-in-group-object-python-pandas

## If only one: series
#se_uu_men = df_insee.groupby('UU2010')['P10_MEN'].sum()
#df_uu_men = pd.Series(se_uu_men, name = 'P10_MEN_UU').reset_index()
#df_insee = pd.merge(df_insee, df_uu_men, on = "UU2010")

## ####################################### 
## 2/ DATA AT INDIVIDUAL LEVEL (BIG FILES)
## #######################################
#
#path_txt_mob_ind = os.path.join(path_dir_insee,
#                                'Mobilite_par_individu',
#                                'FD_MOBPRO_2009.txt')
#file_opened = open(path_txt_mob_ind, 'r')
#data = file_opened.read()
#data_part = data[0:10000000].split('\n') # memory error if take the whole file
#variable_names = data_part[0].split(';')
#first_observation = data_part[1].split(';')
#tuple_example = zip(variable_names, first_observation)
