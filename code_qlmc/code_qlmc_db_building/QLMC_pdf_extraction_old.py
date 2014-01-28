import os
import sys
import subprocess
from subprocess import PIPE, Popen
import re
import string
import sqlite3
import json

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:/Bureau/Etienne_work/Data'):
  path_data = r'W:/Bureau/Etienne_work/Data'
else:
  path_data = r'C:/Users/etna/Desktop/Etienne_work/Data'

folder_source_pdftottext = r'/data_qlmc/data_source/data_pdf_qlmc'
list_folders_source_pdf = [r'/data_qlmc/data_source/data_pdf_qlmc/1_previous_format',
                           r'/data_qlmc/data_source/data_pdf_qlmc/2_recent_format']
folder_built_sql = r'/data_qlmc/data_built/data_sql_qlmc'
folder_built_json = r'/data_qlmc/data_built/data_json_qlmc'

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def get_destring(price):
  return float(price.replace(',','.'))
  
def extract_from_pdf_1(path):
  file = subprocess.Popen(\
           [path_data + folder_source_pdftottext + r'/pdftotext.exe', '-layout' , path, '-'], stdout=PIPE)
  data = file.communicate()[0].split('\r\n')
  master_period = []
  for observation_index, observation in enumerate(data):
    observation_list = re.split('\s{2,}', observation)
    if '/' in observation_list[-1]:
      if ';' in observation_list[-1]:
        observation_list = observation_list[:-1] + observation_list[-1].split(';')
      else:
        observation_list = observation_list[:-1] + observation_list[-1].strip().split(' ')
      # list_ad_hoc_corrections.append(observation_list)
    if len(observation_list) < 6:
      print observation_list
    else:
      master_period.append(observation_list[:2] + [' '.join(observation_list[2:-3])] + observation_list[-3:])
  # Remove first line (title), clean a bit and add to master
  print '\nCheck that first line is to be removed'
  print master_period[0], '\n', master_period[1], '\n'
  master_period = master_period[1:]
  for observation_index, observation in enumerate(master_period):
    master_period[observation_index] = [elt.strip().replace('\x0c', '') for elt in master_period[observation_index]]
    # here: elt[4] is date and elt[5] price => inverse
    # .replace('"','') used for one specific line
    # date of this observation is to be corrected too
    master_period[observation_index] = master_period[observation_index][:4] +\
                                       [get_destring(master_period[observation_index][5].replace('"',''))] +\
                                       master_period[observation_index][4:5]
  return master_period

def extract_from_pdf_2(path):
  file = subprocess.Popen(\
           [path_data + folder_source_pdftottext + r'\pdftotext.exe', '-layout' , path, '-'], stdout=PIPE)
  data = file.communicate()[0].split('\r\n')
  master_period = []
  for observation_index, observation in enumerate(data):
    observation_list = re.split('\s{2,}', observation)
    if len(observation_list) < 6:
      print observation_list
    else:
      master_period.append(observation_list[:2] + [' '.join(observation_list[2:-3])] + observation_list[-3:])
  # Remove first line (title), clean a bit and add to master
  print '\nCheck that first line is to be removed'
  print master_period[0], '\n', master_period[1], '\n'
  master_period = master_period[1:]
  for observation_index, observation in enumerate(master_period):
    master_period[observation_index] = [elt.strip().replace('\x0c', '') for elt in master_period[observation_index]]
    master_period[observation_index] = master_period[observation_index][:4] +\
                                       [get_destring(master_period[observation_index][4])] +\
                                       master_period[observation_index][5:]
  return master_period

# build master
master = []
folder_source_pdf = list_folders_source_pdf[0]
for file in os.listdir(path_data + folder_source_pdf):
  if file[-3:] == 'pdf':
    master.append(extract_from_pdf_1(path_data + folder_source_pdf + r'/%s' %file))
folder_source_pdf = list_folders_source_pdf[1]
for file in os.listdir(path_data + folder_source_pdf):
  if file[-3:] == 'pdf':
    master.append(extract_from_pdf_2(path_data + folder_source_pdf + r'/%s' %file))

# add period index, decode string
for master_period_index, master_period in enumerate(master):
  for observation_index, observation in enumerate(master_period):
    master[master_period_index][observation_index].append(master_period_index)
    master[master_period_index][observation_index] = [elt.decode('latin-1') if isinstance(elt, basestring) else elt\
                                                          for elt in master[master_period_index][observation_index]]

# #########################                                         
# PRODUCT BRANDS AND NAMES
# #########################
# essentially good: some corrections can be made
# TODO: add product brand (after correction) and product name fields
set_product_brands = set()
for master_period_index, master_period in enumerate(master):
  for observation_index, observation in enumerate(master_period):
    list_no_union = []
    if ' - ' in observation[2]:
      set_product_brands.add(observation[2].split(' - ')[0])
    else:
      list_no_union.append(observation[2])

# ######################                                           
# SHOP BRANDS AND CITIES
# ######################
# Creates a specific field for shop brand
# TODO: add city
set_shop_brands = set()
for master_period_index, master_period in enumerate(master):
  for observation_index, observation in enumerate(master_period):
    set_shop_brands.add(observation[3])
# beware if using just 'in' since come brands contain others
# hence put the longest one at the end (Carrefour & Leclerc)
list_shop_brands = ['AUCHAN',
                    'CARREFOUR',
                    'CARREFOUR MARKET',
                    'CORA',
                    'LECLERC',
                    'E. LECLERC',
                    'CENTRE E. LECLERC',
                    'GEANT CASINO',
                    'GEANT DISCOUNT',
                    'HYPER U',
                    'INTERMARCHE',
                    'INTERMARCHE SUPER',
                    'SUPER U',
                    'U EXPRESS']
for master_period_index, master_period in enumerate(master):
  for observation_index, observation in enumerate(master_period):
    brand = None
    for shop_brand in list_shop_brands:
      if shop_brand in observation[3]:
        brand = shop_brand
    city = observation[3][len(brand):]
    # breaks if brand still None (not found in list)
    master[master_period_index][observation_index] += [brand.strip(), city.strip()]

conn = sqlite3.connect(path_data + folder_built_sql+ r'/mydatabase.db')
cursor = conn.cursor()
# cursor.execute("DROP TABLE qlmc_global")
cursor.execute("CREATE TABLE qlmc_global (rayon TEXT, famille TEXT, produit TEXT, magasin TEXT, prix REAL, date TEXT, period INTEGER, marque_magasin TEXT, ville_magasin TEXT)")
for master_period_index, master_period in enumerate(master):
  cursor.executemany("INSERT INTO qlmc_global VALUES (?,?,?,?,?,?,?,?,?)", master_period)
conn.commit()
enc_stock_json(master, path_data + folder_built_json + r'/master_global')

"""
#can't give a name given used for indexes in other tables
#print 'indexes in table', cursor.execute("PRAGMA index_list(qlmc_global)").fetchall()
#cursor.execute("CREATE INDEX MagProdPer_global ON qlmc_global (magasin, produit, period)")
#cursor.execute("CREATE INDEX MagPer_global ON qlmc_global (magasin, period)")
"""

# enrichment of data set:
# could try to have something on brands (text search...)
# could try to take into account quantities (regex)
# information on stores (to be collected)

# cross section price dispersion: coefficient of variation per product, compare product categories etc. + between store: some average (?)
# evolution of price dispersion (same stores same products, or all stores sames products...)