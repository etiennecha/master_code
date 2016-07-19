#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
import os, sys
import subprocess
from subprocess import PIPE, Popen
import re
import string
import json
import pprint
import pandas as pd

pd.set_option('float_format', '{:,.2f}'.format)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def read_pdftotext(path_file, path_pdftotext):
  temp_file = subprocess.Popen([path_pdftotext,
                           '-layout' ,
                           path_file,
                           '-'], stdout=PIPE)
  data = temp_file.communicate()[0].split('\r\n') # not good on linux?
  return data

ls_chains = [u'AUCHAN',
             u'CARREFOUR',
             u'MARKET',
             u'CARREFOUR MARKET',
             u'HYPER CASINO',
             u'CASINO',
             u'CORA',
             u'CENTRE E.LECLERC',
             u'E.LECLERC DRIVE',
             u'GEANT CASINO',
             u'HYPER U',
             u'INTERMARCHE',
             u'INTERMARCHE HYPER',
             u'INTERMARCHE SUPER',
             u'SUPER U']

path_source = os.path.join(path_data,
                           'data_supermarkets',
                           'data_source',
                           'data_qlmc_2013')
path_source_pdf = os.path.join(path_source, 'data_pdf')
path_source_pdftotext = os.path.join(path_source_pdf, 'pdftotext.exe')
path_source_csv = os.path.join(path_source, 'data_csv')

#ls_folders = ['201405_by_chain',
#              '201409_by_chain']
#folder = ls_folders[0]
#path_folder = os.path.join(path_source_pdf, folder)

path_folder = path_source_pdf
ls_pdf_files = [x for x in os.listdir(path_folder) if x[-4:] == '.pdf']

for pdf_file in ls_pdf_files[0:1]: 
  print ''
  data = read_pdftotext(os.path.join(path_folder, pdf_file),
                        path_source_pdftotext)
  ls_rows = [re.split('\s{2,}', row.decode('latin-1').strip())\
               for row in data if row.strip()]
  ls_raw_rows = [row.decode('latin-1') for row in data if row.strip()]

ls_rows = ls_rows[363:]
ls_raw_rows = ls_raw_rows[363:]

dict_len = {}
for row in ls_rows:
  dict_len.setdefault(len(row), []).append(row)

for k,v in dict_len.items():
  print k, len(v)

for i, row in enumerate(ls_rows):
  if len(row) == 2:
    print ''
    print ls_raw_rows[i-1]
    print ls_raw_rows[i]
    break

#ls_rows = [row for row in ls_rows if not row[0] == 'Tous rayons']

# Fix
ls_rows_final = []
for i, row in enumerate(ls_rows):
  # Get rid of page numbers
  if not row[0] == 'Tous rayons':
    # Assume if 6 items: assume 2 columns for product
    if len(row) == 6:
      row_final = row[:1] + [u' '.join(row[1:3])] + row[3:]
    # Assume if 4 items: 1 column for store and price
    elif len(row) == 4:
      row_final = row[:2] + [u' '.join(row[2].split(' ')[:-1]),
                             row[2].split(' ')[-1]] + row[3:]
    else:
      row_final = row
    ls_rows_final.append(row_final)

df_qlmc = pd.DataFrame(ls_rows_final,
                       columns = ['section', 'product', 'store_name', 'price', 'date'])

# Get chain
df_qlmc['store_chain'] = None
for chain in ls_chains:
  #df_qlmc['store_chain'] =\
  #  df_qlmc.apply(lambda x: chain if re.match(chain, x['store'])\
  #                                else x['store_chain'],
  #                axis = 1)
  df_qlmc.loc[(df_qlmc['store_name'].str.match(u'^{:s}'.format(chain))),
              'store_chain'] = chain

print()
print(df_qlmc[df_qlmc['store_chain'].isnull()]['store_name'].value_counts())
print(df_qlmc['store_chain'].value_counts())

# Get price
df_qlmc['price'] =\
  df_qlmc['price'].apply(lambda x: x.replace(',', '.')).astype(float)

print()
print(df_qlmc['price'].describe())

## Get date
# df_chain['Date'] = pd.to_datetime(df_chain['Date'], format = '%d/%m/%Y')

# Check unicity of store / product
print()
print(len(df_qlmc[df_qlmc.duplicated(['store_chain', 'product'])]))
df_dup = df_qlmc[(df_qlmc.duplicated(['store_name', 'product'], take_last = True)) |\
                 (df_qlmc.duplicated(['store_name', 'product'], take_last = False))].copy()
df_dup.sort(['store_name', 'product'], inplace = True)
# weird... get rid of concerned product(s)
ls_drop_prods = df_dup['product'].unique().tolist()
df_qlmc = df_qlmc[~df_qlmc['product'].isin(ls_drop_prods)]

# Output
df_qlmc.to_csv(os.path.join(path_source_csv,
                            'df_qlmc_201305.csv'),
               encoding = 'utf-8',
               float_format='%.2f',
               index = False)

## Stats des
#dict_df_chains = {}
#for chain in df_qlmc['store_chain'].unique():
#  df_chain = df_qlmc[df_qlmc['store_chain'] == chain].groupby('product')\
#                                                     .agg('describe').unstack()['price']
#  df_chain.sort('count', ascending = False, inplace = True)
#  dict_df_chains[chain] = df_chain
#
#for chain in [u'GEANT CASINO', u'CENTRE E.LECLERC', u'AUCHAN', u'CARREFOUR']:
#  print()
#  print(chain)
#  print(dict_df_chains[chain][0:30].to_string())
