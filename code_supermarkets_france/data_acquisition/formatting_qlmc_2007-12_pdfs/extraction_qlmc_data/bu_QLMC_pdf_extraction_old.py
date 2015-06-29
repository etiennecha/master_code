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

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def get_destring(price):
  return float(price.replace(',','.'))
  
def extract_from_pdf_1(path_pdftotext, path_folder_pdfs):
  temp_file = subprocess.Popen(\
                [path_pdftotext, '-layout' , path_folder_pdfs, '-'], stdout=PIPE)
  data = temp_file.communicate()[0].split('\r\n')
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
  for obs_ind, obs in enumerate(master_period):
    master_period[obs_ind] = [elt.strip().replace('\x0c', '') for elt in master_period[obs_ind]]
    # here: elt[4] is date and elt[5] price => inverse
    # .replace('"','') used for one specific line
    # date of this obs is to be corrected too
    master_period[obs_ind] = master_period[obs_ind][:4] +\
                                       [get_destring(master_period[obs_ind][5].replace('"',''))] +\
                                       master_period[obs_ind][4:5]
  return master_period

def extract_from_pdf_2(path_pdftotext, path_folder_pdfs):
  temp_file = subprocess.Popen(\
           [path_pdftotext, '-layout' , path_folder_pdfs, '-'], stdout=PIPE)
  data = temp_file.communicate()[0].split('\r\n')
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
  for obs_ind, obs in enumerate(master_period):
    master_period[obs_ind] = [elt.strip().replace('\x0c', '') for elt in master_period[obs_ind]]
    master_period[obs_ind] = master_period[obs_ind][:4] +\
                                       [get_destring(master_period[obs_ind][4])] +\
                                         master_period[obs_ind][5:]
  return master_period

path_source_pdf = os.path.join(path_data,
                               'data_supermarkets',
                               'data_qlmc_2007-12',
                               'data_source',
                               'data_pdf')

path_pdftotext = os.path.join(path_source_pdf, 'pdftotext.exe')

ls_path_source_pdf_periods = [os.path.join(path_source_pdf, temp_dir)\
                                for temp_dir in ['1_previous_format',
                                                 '2_recent_format']]
path_source = os.path.join('path_data',
                           'data_supermarkets',
                           'data_qlmc_2007-12',
                           'data_source')

path_source_json = os.path.join(path_source, 'data_json')
path_source_sql = os.path.join(path_source, 'data_sql')

# build master
master = []
path_source_pdf_period = ls_path_source_pdf_periods[0]
for file_name in os.listdir(path_source_pdf_period):
  if file_name[-3:] == 'pdf':
    master.append(extract_from_pdf_1(path_pdftotext,
                                     os.path.join(path_source_pdf_period,
                                                 file_name)))

path_source_pdf_period = ls_path_source_pdf_periods[1]
for file_name in os.listdir(path_source_pdf_period):
  if file_name[-3:] == 'pdf':
    master.append(extract_from_pdf_2(path_pdftotext,
                                     os.path.join(path_source_pdf_period,
                                                  file_name)))

# add period index, decode string
for per_ind, per_master in enumerate(master):
  for obs_ind, obs_master in enumerate(per_master):
    master[per_ind][obs_ind].append(per_master)
    master[per_ind][obs_ind] = [elt.decode('latin-1') if isinstance(elt,
                                                                    basestring) else elt\
                                  for elt in master[per_ind][obs_ind]]

# #########################                                         
# PRODUCT BRANDS AND NAMES
# #########################
# essentially good: some corrections can be made
# todo: add product brand (after correction) and product name fields
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
# todo: add city
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

## #######
## OUTPUT
## #######
#
#conn = sqlite3.connect(path_b)
#cursor = conn.cursor()
## cursor.execute("DROP TABLE qlmc_global")
#cursor.execute("CREATE TABLE qlmc_global (rayon TEXT, famille TEXT, produit TEXT," +\
#               "magasin TEXT, prix REAL, date TEXT, period INTEGER," +\
#               "marque_magasin TEXT, ville_magasin TEXT)")
#for master_period_index, master_period in enumerate(master):
#  cursor.executemany("INSERT INTO qlmc_global VALUES (?,?,?,?,?,?,?,?,?)", master_period)
#conn.commit()
#enc_json(master, path_data + folder_built_json + r'/master_global')
#
##can't give a name given used for indexes in other tables
##print 'indexes in table', cursor.execute("PRAGMA index_list(qlmc_global)").fetchall()
##cursor.execute("CREATE INDEX MagProdPer_global ON qlmc_global (magasin, produit, period)")
##cursor.execute("CREATE INDEX MagPer_global ON qlmc_global (magasin, period)")
#
## enrichment of data set:
## could try to have something on brands (text search...)
## could try to take into account quantities (regex)
## information on stores (to be collected)
#
## cross section price dispersion:
## coefficient of variation per product, compare product categories etc. 
## + between store: some average (?)
## evolution of price dispersion (same stores same products, or all stores sames products...)
