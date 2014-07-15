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

# #######################
# AIRES URBAINES 2010
# #######################

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

## No need to merge: all info in df_au_com
#df_au = df_au_com

# Identification of Commune at center of Aire Urbaine (if any)
ls_libgeo_1 = df_au_com['LIBAU2010'][df_au_com['LIBGEO'] == df_au_com['LIBAU2010']].values
ls_libgeo_2 = df_au_com['LIBAU2010'][\
                df_au_com['LIBAU2010'].str.contains(u'\(partie française\)')].unique()
ls_ok = set(list(ls_libgeo_1) + list(ls_libgeo_2))
# print df_au_com['LIBAU2010'][df_au_com['LIBAU2010'].str.contains(u' - ')].value_counts()
ls_check = [x for x in df_au_info['LIBGEO'].values if x not in ls_ok]
# Check if 'LIBGEO' in 'LIBAU2010'
# (ok for AU with two central cities + '(partie française)')
# i.e. can be two AU centers
df_au_com['AU_Center'] = df_au_com.apply(\
                           lambda row: 'YES' if row['LIBGEO'] in row['LIBAU2010']\
                                             else 'NO', axis=1)
# print df_au_com[['AU2010', 'CODGEO']][df_au_com['AU_Center'] == 'YES'].to_string()
df_corr_center = df_au_com[['AU2010', 'CODGEO']][df_au_com['AU_Center'] == 'YES']
se_au_vc = df_corr_center['AU2010'].value_counts()
print se_au_vc[se_au_vc > 1] # AU with more than one central city
# Might be more reasonable to exclude those.. e.g. "Marseille - Aix-en-Provence"
df_corr_ucenter =  df_corr_center.groupby(df_corr_center['AU2010']).first()

# Merge back central city codgeo with df_au
df_au_com.index = df_au_com['AU2010']
df_corr_ucenter.index = df_corr_ucenter['AU2010']
df_au_com['CODGEO_Center'] = df_corr_ucenter['CODGEO']
df_au_com.index = df_au_com['CODGEO'] # set index back to CODGEO

# ##################
# COMMUNE LEVEL DATA
# ##################

# todo: read and store those to make importation easy

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
df_population.index = df_population['CODGEO']

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

# #################
# BUILD/ENRICH DF AU
# #################

df_au_com['POP10'] = df_population['P10_POP'].convert_objects(convert_numeric = True)
df_au_com['SUPERF'] = df_population['SUPERF'].convert_objects(convert_numeric = True)
# todo: groupby...

## #################################### 
## 1E/ Merge INSEE communes dataframes
#
#print '\n', df_uu.info()
#print '\n', df_au.info()
#print '\n', df_population.info()
#print '\n', df_logement.info()
#del(df_au['LIBGEO'], df_population['LIBGEO'], df_logement['LIBGEO'])
#df_insee = pd.merge(df_uu, df_au, on = 'CODGEO')
#df_insee = pd.merge(df_insee, df_population, on = 'CODGEO')
#df_insee = pd.merge(df_insee, df_logement, on = 'CODGEO') 
#
#print '\nINSEE EXTRACT\n', df_insee.info()
#
#path_dir_insee_built = os.path.join(path_dir_insee, 'data_extracts')
#df_insee.to_csv(os.path.join(path_dir_insee_built, 'data_insee_extract.csv'),
#                  float_format='%.3f', encoding='utf-8', index=False)
##path_dir_gas_source = os.path.join(path_data, 'data_gasoline', 'data_source', 'data_other')
##df_insee.to_csv(os.path.join(path_dir_gas_source, 'data_insee_extract.csv')
##                float_format='%.3f', encoding='utf-8', index=False)
#
## Adding columns with aggregated data using groupby
## check : http://bconnelly.net/2013/10/22/summarizing-data-in-python-with-pandas/
#ls_columns_interest = ['P10_LOG', 'P10_MEN', 'P10_PMEN',
#                       'P10_RP_VOIT1P', 'P10_RP_VOIT1', 'P10_RP_VOIT2P']
#for column in ls_columns_interest:
#  df_insee[column] = df_insee[column].apply(lambda x: float(x) if x else float('nan'))
#df_uu_agg = df_insee.groupby('UU2010')[ls_columns_interest].sum()
#df_insee = pd.merge(df_insee, df_uu_agg, left_on = "UU2010",
#                    right_index = True, suffixes = ('_COM', '_UU'))
#print '\nINSEE EXTRACT ENRICHED\n', df_insee.info() 
#
## http://pandas.pydata.org/pandas-docs/dev/groupby.html
## todo: read # http://stackoverflow.com/questions/15262134/apply-different-functions-to-different-items-in-group-object-python-pandas
#
### If only one: series
##se_uu_men = df_insee.groupby('UU2010')['P10_MEN'].sum()
##df_uu_men = pd.Series(se_uu_men, name = 'P10_MEN_UU').reset_index()
##df_insee = pd.merge(df_insee, df_uu_men, on = "UU2010")
