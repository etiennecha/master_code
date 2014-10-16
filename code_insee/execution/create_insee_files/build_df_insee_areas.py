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

# #######################
# UNITES URBAINES 2010
# #######################

path_xls_uu = os.path.join(path_dir_communes,
                           'UnitesUrbaines',
                           'UU2010.xls')
wb_uu = xlrd.open_workbook(path_xls_uu)
print 'Sheets in file', wb_uu.sheet_names()

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

# #######################
# AIRES URBAINES 2010
# #######################

path_xls_au = os.path.join(path_dir_communes,
                           'AiresUrbaines',
                           'AU2010.xls')
wb_au = xlrd.open_workbook(path_xls_au)
print 'Sheets in file', wb_au.sheet_names()

# Sheet: aires urbaines (info par au)
sh_au_info = wb_au.sheet_by_name(u'Zonage en aires urbaines 2010')
ls_columns = sh_au_info.row_values(1)
ls_rows = [sh_au_info.row_values(i) for i in range(2, sh_au_info.nrows)]
df_au_info = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

# todo: exclude '000'

# Sheet: communes (appartenance des communes aux au)
sh_au_com = wb_au.sheet_by_name(u'Composition communale')
ls_columns = sh_au_com.row_values(1)
ls_rows = [sh_au_com.row_values(i) for i in range(2, sh_au_com.nrows)]
df_au_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

# #######################
# BASSINS DE VIE 2012
# #######################

path_xls_bv = os.path.join(path_dir_communes,
                           'BassinsVie',
                           'bv-2012.xls')
wb_bv = xlrd.open_workbook(path_xls_bv)
print 'Sheets in file', wb_bv.sheet_names()

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

# ####################
# BUILD DF INSEE AREAS
# ####################

df_insee_areas = df_uu_com[['CODGEO', 'LIBGEO', 'UU2010',
                            'TYPE_2010', 'STATUT_2010', 'POP_MUN_2007']].copy()
df_insee_areas.set_index('CODGEO', inplace = True)

df_au_com.set_index('CODGEO', inplace = True)
df_insee_areas['AU2010'] = df_au_com['AU2010']

df_bv_com.set_index('COM', inplace = True)
df_insee_areas['BV'] = df_bv_com['BV']

# get rid of meaningless UU2010 & AU2010 (i.e. no real area)
df_insee_areas['UU2010_O'] = df_insee_areas['UU2010']
ls_uu2010_drop = [u'%02d000' %i for i in range(1, 96)] +\
                 [u'2A000', u'2B000'] +\
                 [u'9%s000' %i for i in ['A', 'B', 'C', 'D', 'E', 'F']]
df_insee_areas['UU2010'] = df_insee_areas['UU2010'].apply(\
                             lambda x: x if x not in ls_uu2010_drop else '')

df_insee_areas['AU2010_O'] = df_insee_areas['AU2010']
ls_au2010_drop = [u'000', u'997', u'998']
df_insee_areas['AU2010'] = df_insee_areas['AU2010'].apply(\
                             lambda x: x if x not in ls_au2010_drop else '')

ls_disp = ['CODGEO', 'LIBGEO', 'TYPE_2010', 'STATUT_2010', 'POP_MUN_2007',
           'AU2010', 'UU2010', 'BV', 'AU2010_O', 'UU2010_O']

df_insee_areas.reset_index(inplace=True)
df_insee_areas[ls_disp].to_csv(os.path.join(path_dir_insee_built, 'df_insee_areas.csv'),
                               float_format='%.2f', encoding='utf-8', index=False)

# add au/uu/bv libelles
# caution: df with info must contain unique row per occurence
# todo: be cautious with border (e.g. Geneve misses)
# todo: add dummy for communes with '(partie française'))


df_au_info.rename(columns = {'CODGEO': 'AU2010', 'LIBGEO' : 'LIBAU2010'},
                  inplace = True)
df_insee_areas_2 = pd.merge(df_au_info,
                            df_insee_areas,
                            on='AU2010',
                            how='right')

df_insee_areas_2 = pd.merge(df_uu_info[['UU2010', 'LIBUU2010']],
                            df_insee_areas_2, 
                            on='UU2010', 
                            how='right')

df_insee_areas_2 = pd.merge(df_bv_info[['BV', 'LIBBV']],
                            df_insee_areas_2, 
                            on='BV', 
                            how='right')

df_insee_areas_2.sort('CODGEO', inplace = True)
ls_disp_2 = ['CODGEO', 'LIBGEO', 'TYPE_2010', 'STATUT_2010', 'POP_MUN_2007',
             'AU2010', 'LIBAU2010', 'UU2010', 'LIBUU2010', 'BV', 'LIBBV',
             'AU2010_O', 'UU2010_O']
# print df_insee_areas_2[ls_disp][0:500].to_string()

df_insee_areas_2[ls_disp_2].to_csv(os.path.join(path_dir_insee_built, 'df_insee_areas_w_libs.csv'),
                                   float_format='%.2f', encoding='utf-8', index=False)
