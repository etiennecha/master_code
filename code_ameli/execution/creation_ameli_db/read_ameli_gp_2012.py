#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
import pprint
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Working with "old" (around 2012?) ameli files

# SHORT TERM
# todo: to be integrated with more recent data / specialist data (paris/idf only?)
# todo: lack of competition among ophtalmo/gyneco?

# MEDIUM TERM
# todo: integrate official stats by dpt to evaluate representativity / density
# todo: see if easy to assess where medecins missing (dpt with > 500: zip codes etc?)
# todo: medecins by insee code area (usual matching from commune + zip to insee code)
# todo: are prices useless ? only share or non conv etc? (btw salaries? location?)

path_folder_ameli = os.path.join(path_data, 'data_ameli', u'data_source', 'ameli_2012')

ls_ameli_file_names = [u'actes_medecins',
                       u'actes_medecins2',
                       u'actes_medecins3',
                       u'dbtoprint_json',
                       u'all_out']

ls_files_ameli = [dec_json(os.path.join(path_folder_ameli, file_name))\
                    for file_name in ls_ameli_file_names]

print u'\nRead and describe ameli files'
ls_indiv_ids =[]
for file_ameli_name, file_ameli in zip(ls_ameli_file_names, ls_files_ameli):
  print u'\nFile name:',file_ameli_name
  print u'File type:', type(file_ameli)
  print u'File length:', len(file_ameli)
  print u'First line (key: %s):' % file_ameli.keys()[0]
  pprint.pprint(file_ameli[file_ameli.keys()[0]])
  ls_indiv_ids += file_ameli.keys()
ls_unique_indiv_ids = list(set(ls_indiv_ids))

# Check services
dict_services = {}
for indiv_id, indiv_info in ls_files_ameli[0].items():
  for service in indiv_info['services']:
    dict_services.setdefault(service['titre_prestation'], []).append(indiv_id)

ls_services_todf = []
for k,v in dict_services.items():
  if len(v) > 1000:
    # print k, len(v)
    ls_services_todf.append(k)

# Check consultation
print u'\nSecteur 1 with depassements:'
ls_consultations = []
ls_consultations_prices = []
for indiv_id, indiv_info in ls_files_ameli[0].items():
  avg_price = None
  for service in indiv_info['services']:
    if service['titre_prestation'] == u'Consultation' and service['prix_prestation']:
      ls_consultations.append((indiv_id, service['prix_prestation']))
      if len(service['prix_prestation']) == 1:
        # ls_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][0][1])
        ls_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac', service['prix_prestation'][0])
      else:
        # ls_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][1][1])
        ls_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac', service['prix_prestation'][1])
        # check depassements for secteur1?
        if (indiv_id in ls_files_ameli[4]) and\
           (ls_files_ameli[4][indiv_id]['convention'] == 'secteur1'):
          print indiv_id, service['prix_prestation']
      ls_consultations_prices.append(ls_prices)
      avg_price = np.mean(map(lambda x: float(x.rstrip(u'\u20ac').replace(u',', u'.')), ls_prices))
ls_consultations_avg = [np.mean(map(lambda x:\
                                    float(x.rstrip(u'\u20ac').replace(u',', u'.')),
                                  ls_prices))\
                            for ls_prices in ls_consultations_prices]

# Build df

# Services kept apart from Consultation
ls_services_todf.remove('Consultation')

print u'\nCollect info to build df (print exceptions)'
ls_columns = ['name', 'zip_code', 'city', 'sector', 'card']
ls_c_cols = ['c_norm', 'c_occu', 'c_min', 'c_max']
ls_indexes = []
ls_ls_df_indiv_info = []
for indiv_id, indiv_info in ls_files_ameli[0].items():
  ls_indexes.append(indiv_id)
  # Info physician
  indiv_name = indiv_info['name']
  indiv_zip, indiv_city = None, None
  #for i in range(5):
  #  if (len(indiv_info['address']) > i) and\
  #     (re.match('([0-9]{5,5}) (.*)', indiv_info['address'][i])):
  #    indiv_zip = re.match('([0-9]{5,5}) (.*)', indiv_info['address'][i]).group(1)
  #    indiv_city = re.match('([0-9]{5,5}) (.*)', indiv_info['address'][i]).group(2)
  #    break
  #if not indiv_zip:
  #  print indiv_id, indiv_info['address']
  if re.match('([0-9]{5,5}) (.*)', indiv_info['address'][-2]):
    indiv_zip = re.match('([0-9]{5,5}) (.*)', indiv_info['address'][-2]).group(1)
    indiv_city = re.match('([0-9]{5,5}) (.*)', indiv_info['address'][-2]).group(2)
  else:
    print indiv_id, indiv_info['address']
  indiv_secteur = None
  indiv_carte_vitale = None
  if indiv_id in ls_files_ameli[4]:
    indiv_secteur = ls_files_ameli[4][indiv_id]['convention']
    indiv_carte_vitale = ls_files_ameli[4][indiv_id]['carte_vitale']
  ls_physician_prices = [None for i in ls_services_todf]
  ls_consultation_prices = [None, None, None, None]
  for service in indiv_info['services']:
    # Services apart from Consultation
    if service['titre_prestation'] in ls_services_todf:
      service_ind = ls_services_todf.index(service['titre_prestation'])
      if service['prix_prestation']:
        if len(service['prix_prestation']) == 1:
          ls_service_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac',
                                           service['prix_prestation'][0])
        else:
          ls_service_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac',
                                         service['prix_prestation'][1])
        avg_price = np.mean(map(lambda x: float(x.rstrip(u'\u20ac').replace(u',', u'.')),
                                ls_service_prices))
      ls_physician_prices[service_ind] = avg_price
    # Consultation
    elif service['titre_prestation'] == 'Consultation':
      normal_price, occu_np, min_price, max_price = None, None, None, None
      if len(service['prix_prestation']) == 1:
        normal_price = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac',
                            service['prix_prestation'][0])
        if len(ls_normal_prices) == 1:
          normal_price = ls_normal_prices[0].rstrip(u'\u20ac').replace(u',', u'.')
        else:
          print 'Pbm too many normal prices:', id_physician, service['prix_prestation']
        occu_np, min_price, max_price = '10', normal_price, normal_price
        ls_consultation_prices = [normal_price, occu_np, min_price, max_price]
      elif len(service['prix_prestation']) == 2:
        # normal price
        ls_normal_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac',
                                      service['prix_prestation'][1]) 
        if len(ls_normal_prices) == 1:
          normal_price = ls_normal_prices[0].rstrip(u'\u20ac').replace(u',', u'.')
        else:
          print 'Pbm too many normal prices:', id_physician, service['prix_prestation']
        # occurence of normal price
        re_occu_np = re.search(u'\(([0-9]) cas', service['prix_prestation'][1])
        if re_occu_np:
          occu_np = re_occu_np.group(1)
        else:
          print service['prix_prestation'][1]
        # min and max prices
        ls_minmax_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac',
                                      service['prix_prestation'][0]) 
        if len(ls_minmax_prices) == 2:
          min_price = ls_minmax_prices[0].rstrip(u'\u20ac').replace(u',', u'.')
          max_price = ls_minmax_prices[1].rstrip(u'\u20ac').replace(u',', u'.')
        else:
          print 'Pbm no min / max prices:', id_physician, service['prix_prestation']
        ls_consultation_prices = [normal_price, occu_np, min_price, max_price]
      else:
        print 'Pbm too many lines:', id_physician, service['prix_prestation']
  ls_df_indiv_info = [indiv_name, indiv_zip, indiv_city,
                      indiv_secteur, indiv_carte_vitale]+\
                     ls_consultation_prices +\
                     ls_physician_prices
  ls_ls_df_indiv_info.append(ls_df_indiv_info)

df_ameli = pd.DataFrame(ls_ls_df_indiv_info,
                        index = ls_indexes,
                        columns = ls_columns + ls_c_cols + ls_services_todf)

# Number by sector
print u'\nNb of physicians by "secteur"'
print df_ameli['sector'].value_counts()

## Overview
#print df_ameli[(df_ameli['dpt'] == '01') & (df_ameli['sector'] == 'secteur2')]\
#        [ls_columns + ['Consultation']].to_string()

# Number by dpt and sector
print u'\nNb of physicians by "département" and "secteur"'
df_ameli['dpt'] = df_ameli['zip_code'].apply(lambda x: x[:2])
se_nb_by_dpt_and_sector = df_ameli.groupby(['sector', 'dpt']).size()
# print se_nb_by_dpt_and_sector.to_string()
ls_str_sectors = ('nonconv', 'secteur2', 'secteur1')
ls_se_sectors_by_dpt = []
for str_sector in ls_str_sectors:
  df_sector = df_ameli[df_ameli['sector'] == str_sector]
  ls_se_sectors_by_dpt.append(df_sector.groupby('dpt').size())
df_sectors_by_dpt = pd.concat(dict(zip(ls_str_sectors, ls_se_sectors_by_dpt)), axis= 1)
df_sectors_by_dpt = df_sectors_by_dpt.fillna(0)
df_sectors_by_dpt['total'] = df_sectors_by_dpt.sum(axis = 1)
#df_sectors_by_dpt['total'] = df_sectors_by_dpt['nonconv'] +\
#                             df_sectors_by_dpt['secteur2'] +\
#                             df_sectors_by_dpt['secteur1']
print df_sectors_by_dpt.to_string()

# plt.scatter(df_sectors_by_dpt['total'], df_sectors_by_dpt['secteur2'])
# plt.show()

# REMARKS:
# Paris 16: only zip 75116... not 75016
# Issue can be similar for other zip codes
# Can bias nb of competitors for a physician/within an area
# Still in any not too small area: should have a big enough sample of physicians (biases?)
