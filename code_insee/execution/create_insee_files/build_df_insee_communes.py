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
                                'P10_POP', 'SUPERF',
                                'P10_POP0014', 'P10_POP6074', 'P10_POP75P']
df_population = df_population[ls_population_select_columns]
df_population.index = df_population['CODGEO']

# #######################
# LOGEMENT 2010

path_xls_logement = os.path.join(path_dir_communes,
                                 'Logement',
                                 'base-cc-logement-2010.xls')

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
df_logement.index = df_logement['CODGEO']

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
df_revenus.index = df_revenus['CODGEO']

# #######################
# BUILD DF COMMUNES
# #######################

# todo: add statu / type from UU file (or AU?): rural, urbain etc.

df_communes = df_population.copy()

lsd_logement = ['P10_LOG', 'P10_MEN', 'P10_PMEN', 
                'P10_RP_VOIT1P', 'P10_RP_VOIT1', 'P10_RP_VOIT2P'] 

df_communes = pd.merge(df_communes,
                       df_logement[lsd_logement],
                       how = 'left',
                       left_index = True,
                       right_index = True)

lsd_revenus = ['MENFIS10', 'PMENFIS10', 'MENIMP10', 
               'QUAR1UC10', 'QUAR2UC10', 'QUAR3UC10',
               'RDUC10', 'PTSA10', 'PPEN10', 'PBEN10', 'PAUT10']

df_communes = pd.merge(df_communes,
                       df_revenus[lsd_revenus],
                       how = 'left',
                       left_index = True,
                       right_index = True)

df_communes.to_csv(os.path.join(path_dir_insee_built,
                                'df_communes.csv'),
                   float_format='%.2f',
                   encoding='utf-8',
                   index=False)
