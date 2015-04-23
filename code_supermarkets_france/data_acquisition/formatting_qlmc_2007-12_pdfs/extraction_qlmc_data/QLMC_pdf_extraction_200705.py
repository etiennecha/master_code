import os
import sys
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
  
# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:/Bureau/Etienne_work/Data'):
  path_data = r'W:/Bureau/Etienne_work/Data'
else:
  path_data = r'C:/Users/etna/Desktop/Etienne_work/Data'

folder_source_pdftottext = r'/data_qlmc/data_source/data_pdf_qlmc'
path_pdftotext = path_data + folder_source_pdftottext

file_rotten = r'/data_qlmc/data_source/data_pdf_qlmc/0_old_with_recent_format/sauvable/200705_releves_QLMC.pdf'

data = read_pdftotext(path_data + file_rotten, path_pdftotext)
data = zip(data[1:554692], data[554693:-1])
data = [elt[0] + '  ' + elt[1] for elt in data]
master, dict_len, list_reconstitutions = format_simple(data)
familles, magasins, produits = get_preliminary_check(master)

"""
# master directly corresponds to data (in terms of index):
# master[554691] = ['Produits frais', 'Yaourts et Desserts', 'Yoplait - Iles flottantes Vanille...', ...]
# master[554692] = ['', 'DATE']
# master[554693] = ['14/05/2007']
# len(master[554693:-1]) = 554691
# len(master[1:554692]) = 554691
# => looks like one row = one product | one date hence easy to put them back together:

master_temp = [re.split('\s{2,}', row) for row in data]
master = zip(master_temp[1:554692], master_temp[554693:-1])
master = [elt[0] + elt[1] for elt in master]
"""