#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import xlrd
import re
import pandas as pd

path_dir_insee = os.path.join(path_data, 'data_insee')
print path_dir_insee

path_dir_communes = os.path.join(path_dir_insee, 'communes')
path_xls_logement = os.path.join(path_dir_communes, 'Logement', 'base-cc-logement-2010.xls')

wb_logement = xlrd.open_workbook(os.path.join(path_dir_communes, 'Logement', 'base-cc-logement-2010.xls'))
print 'Sheets in file', wb_logement.sheet_names()

sh_logement_com = wb_logement.sheet_by_name(u'COM')
ls_columns = sh_logement_com.row_values(5)
ls_rows = []
for row_ind in range(6, sh_logement_com.nrows):
  ls_rows.append(sh_logement_com.row_values(row_ind))
df_logement_com = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

sh_logement_arm = wb_logement.sheet_by_name(u'ARM')
ls_columns = sh_logement_arm.row_values(5)
ls_rows = []
for row_ind in range(6, sh_logement_arm.nrows):
  ls_rows.append(sh_logement_arm.row_values(row_ind))
df_logement_arm = pd.DataFrame(ls_rows, columns = ls_columns, dtype = str)

ls_select_columns = [u'CODGEO', u'LIBGEO',
                     u'P10_LOG', u'P10_RP',
                     u'P10_MEN', u'P10_PMEN', u'P10_NPER_RP',
                     u'P10_RP_VOIT1P', 'P10_RP_VOIT1', 'P10_RP_VOIT2P']

df_logement = pd.concat([df_logement_com, df_logement_arm], ignore_index = True)
df_logement = df_logement[ls_select_columns]
