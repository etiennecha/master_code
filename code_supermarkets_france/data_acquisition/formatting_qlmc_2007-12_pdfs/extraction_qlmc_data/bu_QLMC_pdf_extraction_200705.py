#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
import os, sys
import subprocess
from subprocess import PIPE, Popen
import re
import string
import sqlite3
import json
import pprint

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)
    
def read_pdftotext(path_file, path_pdftotext):
  file = subprocess.Popen([path_pdftotext + r'/pdftotext.exe',\
                            '-layout' , path_file, '-'], stdout=PIPE)
  data = file.communicate()[0].split('\r\n') # not good on linux?
  return data
  
path_source_pdf = os.path.join(path_data,
                               'data_supermarkets',
                               'data_qlmc_2007-12',
                               'data_source',
                               'data_pdf')

data = read_pdftotext(os.path.join(path_source_pdf,
                                   '0_old_with_recent_format',
                                   '200705_releves_QLMC.pdf'),
                      path_source_pdf)

#data = zip(data[1:554692], data[554693:-1])
#data = [elt[0] + '  ' + elt[1] for elt in data]

#master, dict_len, list_reconstitutions = format_simple(data)
#familles, magasins, produits = get_preliminary_check(master)

## master directly corresponds to data (in terms of index):
## master[554691] = ['Produits frais', 'Yaourts et Desserts', 'Yoplait - Iles flottantes Vanille...', ...]
## master[554692] = ['', 'DATE']
## master[554693] = ['14/05/2007']
## len(master[554693:-1]) = 554691
## len(master[1:554692]) = 554691
## => looks like one row = one product | one date hence easy to put them back together:
#
#master_temp = [re.split('\s{2,}', row) for row in data]
#master = zip(master_temp[1:554692], master_temp[554693:-1])
#master = [elt[0] + elt[1] for elt in master]
