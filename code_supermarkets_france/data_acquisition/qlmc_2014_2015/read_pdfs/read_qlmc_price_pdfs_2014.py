#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import os, sys
import re
import pandas as pd

path_source = os.path.join(path_data, 'data_supermarkets', 'data_source', 'data_qlmc_2014')
path_source_pdf = os.path.join(path_source, 'data_pdf')
path_source_csv = os.path.join(path_source, 'data_csv')
path_exe_pdftotext = os.path.join(path_source_pdf, 'pdftotext.exe')

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

# ########
# 2014/05
# ########

# READ PDFS
print()
print('Read Pdfs 2014/05')
path_folder = os.path.join(path_source_pdf, '201405_by_chain')
ls_pdf_names = [x for x in os.listdir(path_folder) if x[-4:] == '.pdf']

ls_df_chain = []
for pdf_name in ls_pdf_names: 
  print()
  print(pdf_name)
  data = read_pdftotext(os.path.join(path_folder, pdf_name), path_exe_pdftotext)
  ls_rows = [re.split('\s{2,}', row.decode('latin-1').strip()) for row in data]
  
  # Check what will be lost (todo: avoid priting titles)
  print()
  print('Following rows dropped:')
  for row_i, row in enumerate(ls_rows):
  	if len(row) != 6:
  		print(row, row_i)
  ls_rows = [row for row in ls_rows if len(row) == 6]
  # Safe to assume first is title?
  ls_columns = ls_rows[0]
  ls_rows = ls_rows[1:]
  
  # Build dataframe
  df_chain = pd.DataFrame(ls_rows, columns = ls_columns)
  df_chain['Prix'] = df_chain['Prix'].apply(lambda x: x.replace(',', '.')).astype(float)
  # df_chain['Date'] = pd.to_datetime(df_chain['Date'], format = '%d/%m/%Y')
  ls_df_chain.append(df_chain)

df_qlmc = pd.concat(ls_df_chain)

## LSA more precise than Magasin
#df_stores = df_qlmc[['LSA', 'Magasin']].drop_duplicates()
#print(df_stores[df_stores['Magasin'].duplicated()].to_string())

# ADD STORE CHAIN
df_qlmc['Chaine'] = None
for chain in ls_chains:
  (df_qlmc.loc[(df_qlmc['Magasin'].str.match(u'^{:s}'.format(chain))) &\
               (df_qlmc['Chaine'].isnull()),
               'Chaine'] = chain)

# Check unicity of LSA, EAN (/Produit) ?
# Produit likely less precise than EAN (field too short to contain all info?)
print(len(df_qlmc[df_qlmc.duplicated(['LSA', 'EAN'])]))

## Need to drop a few products if want to have unicity... else EAN
#print df_qlmc[(df_qlmc.duplicated(['LSA', 'Produit'], take_last = True)) |\
#              (df_qlmc.duplicated(['LSA', 'Produit'], take_last = False))][0:10].to_string()

# HARMONIZE COLUMN NAMES
df_qlmc.rename(columns = {'LSA'     : 'id_lsa',
                          'Magasin' : 'store_name',
                          'Chaine'  : 'store_chain',
                          'EAN'     : 'ean',
                          'Produit' : 'product',
                          'Prix'    : 'price',
                          'Date'    : 'date'},
               inplace = True)

df_qlmc['date'] = pd.to_datetime(df_qlmc['date'], format = '%d/%m/%Y')

df_qlmc.to_csv(os.path.join(path_source_csv,
                            'df_qlmc_201405.csv'),
               encoding = 'utf-8',
               float_format='%.2f',
               index = False,
               date_format='%Y-%m-%d')

# ########
# 2014/09
# ########

# READ PDFS
print()
print('Read Pdfs 2014/09')
path_folder = os.path.join(path_source_pdf, '201409_by_chain')
ls_pdf_names = [x for x in os.listdir(path_folder) if x[-4:] == '.pdf']

ls_columns_2 = [u'LSA', u'Magasin', u'Groupe', u'EAN', u'Produit', u'Prix', u'Date']
ls_df_chain_2 = []

for pdf_name in ls_pdf_names: 
  print()
  print(pdf_name)
  data = read_pdftotext(os.path.join(path_folder, pdf_name), path_exe_pdftotext)
  ls_rows = [re.split('\s{2,}', row.decode('latin-1').strip()) for row in data]

  # Default (except for title?): 6 fields (EAN Product mixed)
  # Seems often product split in two... hence 7.. or 8
  set_check = set()
  ls_rows_3 = []
  ls_pbms = []
  for row_i, row in enumerate(ls_rows):
    if (len(row) != 6) and (len(row) != 7) and (len(row) != 8):
      print('Drop:', row, row_i)
    # Solve general length pbms
    if ((len(row) == 7) or (len(row) == 8)) and\
       (row[0] != 'LSA'):
      row_2 = row[:3] + [' '.join(row[3:-2])] + row[-2:]
      set_check.add(' '.join(row[3:-2]))
    else:
      row_2 = row
    # Split EAN and Product
    if len(row_2) == 6:
      res = re.match('([0-9]{,13})\s(.*)', row_2[3])
      if res:
        row_3 = row_2[:3] + [res.group(1), res.group(2)] + row_2[4:]
        ls_rows_3.append(row_3)
      else:
        ls_pbms.append(row_2)
  if ls_pbms:
    print(pdf_file, ls_pbms[0])

  df_chain_2 = pd.DataFrame(ls_rows_3,
                            columns = ls_columns_2)
  ls_df_chain_2.append(df_chain_2)

df_qlmc_2 = pd.concat(ls_df_chain_2)
df_qlmc_2['Prix'] = df_qlmc_2['Prix'].apply(lambda x: x.replace(',', '.')).astype(float)

### LSA more precise than Magasin
#df_stores_2 = df_qlmc_2[['LSA', 'Magasin']].drop_duplicates()
#print(df_stores_2[df_stores_2['Magasin'].duplicated()].to_string())

# Check unicity of LSA, EAN (/Produit) ?
# Produit likely less precise than EAN (field too short to contain all info?)
print('Unicity of LSA (store) / EAN')
print(len(df_qlmc_2[df_qlmc_2.duplicated(['LSA', 'EAN'])]))

# ADD STORE CHAIN
df_qlmc_2['Chaine'] = None
for chain in ls_chains:
  (df_qlmc_2.loc[(df_qlmc_2['Magasin'].str.match(u'^{:s}'.format(chain))) &
                 (df_qlmc_2['Chaine'].isnull()),
                 'Chaine'] = chain)

## Need to drop a few products if want to have unicity... else EAN
#print df_qlmc[(df_qlmc.duplicated(['LSA', 'Produit'], take_last = True)) |\
#              (df_qlmc.duplicated(['LSA', 'Produit'], take_last = False))][0:10].to_string()

df_qlmc_2.rename(columns = {'LSA'     : 'id_lsa',
                            'Magasin' : 'store_name',
                            'Chaine'  : 'store_chain',
                            'EAN'     : 'ean',
                            'Produit' : 'product',
                            'Prix'    : 'price',
                            'Date'    : 'date',
                            'Groupe'  : 'store_group'},
                 inplace = True)

df_qlmc_2['date'] = pd.to_datetime(df_qlmc_2['date'], format = '%d/%m/%Y')

df_qlmc_2.to_csv(os.path.join(path_source_csv,
                              'df_qlmc_201409.csv'),
                 encoding = 'utf-8',
                 float_format='%.2f',
                 index = False,
                 date_format='%Y-%m-%d')
