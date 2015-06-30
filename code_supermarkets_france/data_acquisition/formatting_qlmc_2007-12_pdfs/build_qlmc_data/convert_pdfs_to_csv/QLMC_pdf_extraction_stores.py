#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import *
import os, sys
import subprocess
from subprocess import PIPE, Popen
import re
import json
import pandas as pd

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)
 
def read_pdftotext(path_file, path_pdftotext):
  temp_file = subprocess.Popen([path_pdftotext,
                                '-layout',
                                '-enc',
                                'UTF-8',
                                path_file,
                                '-'], stdout=PIPE)
  #temp_file = subprocess.Popen([path_pdftotext,
  #                              '-layout',
  #                              '-enc',
  #                              'Latin1' ,
  #                              path_file,
  #                              '-'], stdout=PIPE)
  data = temp_file.communicate()[0] # .split('\r\n') change for linux
  return data

path_source = os.path.join(path_data,
                           'data_supermarkets',
                           'data_qlmc_2007-12',
                           'data_source')
                          
path_source_pdf = os.path.join(path_source, 'data_pdf')
path_source_json = os.path.join(path_source, 'data_json')                          

path_pdftotext = os.path.join(path_source_pdf, 'pdftotext.exe')

path_folder_pdf_stores = os.path.join(path_source_pdf, 'store_information')

ls_file_names = ['200801-02_listeMagasins', # 542
                 # '200904_listeMagasins', # 542
                 '200909_listeMagasins', # 739
                 # '201003-04_listeMagasins', # 739
                 '201010-11_listeMagasinsQlmc', # 624
                 # '201101-02_listeMagasinsQlmc', # 624
                 '201104-05_listeMagasinsQlmc', # 857
                 '201201-01_listeMagasinsQlmc', # 833
                 '201208-09_listeMagasins'] # 839

ls_ls_qlmc_stores = []

for file_name in ls_file_names:
  qlmc_stores_raw = read_pdftotext(os.path.join(path_folder_pdf_stores, file_name + '.pdf'),
                                   path_pdftotext)
  ls_qlmc_stores = qlmc_stores_raw.split('\r\n')
  ls_qlmc_stores = [row.decode('utf-8').replace(u'\x0c', u'') for row in ls_qlmc_stores]
  
  ls_qlmc_stores = [re.split(u'\s{2,}', row) for row in ls_qlmc_stores]
  ls_qlmc_stores = [[x for x in row if x] for row in ls_qlmc_stores]
  ls_qlmc_stores = [row for row in ls_qlmc_stores if len(row) == 3]

  ls_ls_qlmc_stores.append(ls_qlmc_stores)

# Get rid of title line if needed
for i in range(3): # 6 if duplicates not excluded
  ls_ls_qlmc_stores[i] = ls_ls_qlmc_stores[i][1:]

print u'\nReading store files:'
for file_name, ls_qlmc_stores in zip(ls_file_names, ls_ls_qlmc_stores):
  print u'\n', file_name
  print u'Nb stores:', len(ls_qlmc_stores)
  print ls_qlmc_stores[0]
  print ls_qlmc_stores[-1]

print u'\nDisplay store files:'
for i, ls_qlmc_stores in enumerate(ls_ls_qlmc_stores):
  df_qlmc_stores = pd.DataFrame(ls_qlmc_stores)
  print u'\nFile:', i
  print df_qlmc_stores.to_string()

enc_json(ls_ls_qlmc_stores, os.path.join(path_source_json,
                                         'ls_ls_qlmc_store_info.json'))
