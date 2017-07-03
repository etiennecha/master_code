#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import os, sys
import re
import pandas as pd

path_source_pdf = os.path.join(path_data, 'data_supermarkets', 'data_source',
                           'data_qlmc_2014_2015', 'data_pdf')
path_exe_pdftotext = os.path.join(path_source_pdf, 'pdftotext.exe')

path_built_csv = os.path.join(path_data, 'data_supermarkets', 'data_built',
                              'data_qlmc_2014_2015', 'data_csv')

ls_chains = ['AUCHAN',
             'MARKET',
             'CARREFOUR MARKET',
             'CARREFOUR',
             'HYPER CASINO',
             'CASINO',
             'CORA',
             'CENTRE E.LECLERC',
             'E.LECLERC DRIVE',
             'GEANT CASINO',
             'HYPER U',
             'INTERMARCHE HYPER',
             'INTERMARCHE SUPER',
             'SUPER U']

path_folder = os.path.join(path_source_pdf, '201602_comparisons')
ls_pdf_names = [x for x in os.listdir(path_folder) if x[-4:] == '.pdf']

ls_columns = ['leclerc_date', 'product',
              'leclerc_name', 'leclerc_price',
              'comp_chain', 'comp_name', 'comp_price', 'comp_date']

ls_df_temp = []
for pdf_name in ls_pdf_names: 
  print()
  print(pdf_name)
  data = read_pdftotext(os.path.join(path_folder, pdf_name), path_exe_pdftotext)
  ls_rows = [re.split('\s{2,}', row.decode('latin-1').strip()) for row in data]
  ls_raw_rows = [row.decode('latin-1') for row in data]

  ls_rows = ls_rows[5:]
  ls_raw_rows = ls_raw_rows[5:]
  
  dict_len = {}
  for row in ls_rows:
    dict_len.setdefault(len(row), []).append(row)
  
  for k,v in dict_len.items():
    print(k, len(v))
  
  #for i, row in enumerate(ls_rows):
  #  if len(row) == 1:
  #    print()
  #    print(ls_raw_rows[i-1])
  #    print(ls_raw_rows[i])
  #    break

  ls_rows_ok = [row for row in ls_rows if (len(row) == 8) and (len(row[0]) == 8)]
  # need second condition too to ensure ok
  
  df_temp = pd.DataFrame(ls_rows_ok, columns = ls_columns)
  ls_df_temp.append(df_temp)

df_qlmc = pd.concat(ls_df_temp)

# One item only: can belong to normal (i.e. 8 item) line for which fields too long
# idea: use string position (with ls_raw_rows) to find field to which it belongs
# 2/3 item lines: this issue (also some page numbers to get rid of, other?)
# 4/5/6/7 item lines: (only?) splitting issues (deal with them first?)

print()
print(df_qlmc['comp_name'].value_counts())

print()
print(df_qlmc[df_qlmc['comp_name'] == 'MIRIBEL'].iloc[0])

print()
print(df_qlmc['comp_chain'].value_counts())
