#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
from matching_insee import *
import pprint
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Working with "old" (around 2012?) ameli files

# todo:
# to be integrated with more recent data / specialist data (paris/idf only?)
# integrate official stats by dpt to evaluate representativity / density
# see if easy to assess where medecins missing (dpt with > 500: zip codes etc?)
# medecins by insee code area (usual matching from commune + zip to insee code)
# are prices useless ? only share or non conv etc? (btw salaries? location?)

path_source_ameli = os.path.join(path_data,
                                 u'data_ameli',
                                 u'data_source',
                                 u'ameli_2012')

path_built_ameli = os.path.join(path_data,
                                u'data_ameli',
                                u'data_built')

path_built_csv= os.path.join(path_built_ameli, 'data_csv')
path_built_json = os.path.join(path_built_ameli, u'data_json')

path_dir_match_insee = os.path.join(path_data,
                                    u'data_insee',
                                    u'match_insee_codes')

# #########
# LOAD DATA
# #########

ls_ameli_file_names = [u'actes_medecins',
                       u'actes_medecins2',
                       u'actes_medecins3',
                       u'dbtoprint_json',
                       u'all_out']
ls_files_ameli = [dec_json(os.path.join(path_source_ameli, file_name))\
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

# Check medecins
dict_medecins = {}
for indiv_id, indiv_info in ls_files_ameli[0].items():
  dict_medecins.setdefault(indiv_info['med_spe'], []).append(indiv_id)

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

# Check consultation (OLD)
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
        ls_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac',
                               service['prix_prestation'][0])
      else:
        # ls_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][1][1])
        ls_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\s?\u20ac',
                               service['prix_prestation'][1])
        # check depassements for secteur1?
        if (indiv_id in ls_files_ameli[4]) and\
           (ls_files_ameli[4][indiv_id]['convention'] == 'secteur1'):
          print indiv_id, service['prix_prestation']
      ls_consultations_prices.append(ls_prices)
      avg_price = np.mean(map(lambda x: float(x.rstrip(u'\u20ac').replace(u',', u'.')),
                              ls_prices))
ls_consultations_avg = [np.mean(map(lambda x:\
                                    float(x.rstrip(u'\u20ac').replace(u',', u'.')),
                                  ls_prices))\
                            for ls_prices in ls_consultations_prices]

# ###################
# BUILD DF PHYSICIANS
# ###################

# Services kept apart from Consultation
ls_services_todf.remove('Consultation')

print u'\nCollect info to build df (print exceptions)'
ls_columns = ['name', 'zip', 'city', 'sector', 'card', 'spe']
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
  # other files if not there?
  if indiv_id in ls_files_ameli[4]:
    indiv_secteur = ls_files_ameli[4][indiv_id]['convention']
    indiv_carte_vitale = ls_files_ameli[4][indiv_id]['carte_vitale']
  indiv_spe = indiv_info['med_spe'].replace(u'\u2013', u'-')
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
      ls_consultation_prices = get_service_price(indiv_id,
                                                 service['prix_prestation'])
  ls_df_indiv_info = [indiv_name, indiv_zip, indiv_city,
                      indiv_secteur, indiv_carte_vitale, indiv_spe]+\
                     ls_consultation_prices +\
                     ls_physician_prices
  ls_ls_df_indiv_info.append(ls_df_indiv_info)

df_ameli = pd.DataFrame(ls_ls_df_indiv_info,
                        index = ls_indexes,
                        columns = ls_columns + ls_c_cols + ls_services_todf)

df_ameli = df_ameli[df_ameli['spe'] != u"Médecin gériatre"].copy()

smg = u"Médecin généraliste"
dict_spe_rep =\
 {smg : u'MG',
  u"%s - Homéopathe en mode d'exercice particulier" %smg : u"MG - Hom MEP",
  u"%s - Acupuncteur en mode d'exercice particulier" %smg : u"MG - Acu MEP",
  u"%s - Angiologue en mode d'exercice particulier" %smg : u"MG - Ang MEP",
  u"%s - Angiologue en mode d'exercice exclusif" %smg : u"MG - Ang MEE",
  u"%s - Médecine appliquée aux sports" %smg +\
    "en mode d'exercice particulier" : u"MG - Spo MEP",
  u"%s - Allergologue en mode d'exercice particulier" %smg : u"MG - All MEP",
  u"%s - Allergologue en mode d'exercice exclusif" %smg : u"MG - All MEE",
  u"%s - Thermaliste en mode d'exercice particulier" %smg : u"MG - The MEP",
  u"%s - Acupuncteur en mode d'exercice exclusif" %smg : u"MG - Acu MEE",
  u"%s - Échographiste en mode d'exercice particulier" %smg : u"MG - Ech MEP",
  u"%s - Homéopathe en mode d'exercice exclusif" % smg : u"MG - Hom MEE",
  u"%s - Échographiste en mode d'exercice exclusif" % smg : u"MG - Ech MEE",
  u"%s - Médecine appliquée aux sports" %smg +\
    u"en mode d'exercice exclusif" : "MG - Spo MEE",
  u"%s - Thermaliste en mode d'exercice exclusif" %smg : "MG - The MEE"}
df_ameli['spe'] =\
  df_ameli['spe'].apply(
     lambda x: dict_spe_rep.get(x, None))

# Excludes non GP (a priori)
#df_gp_2012 = df_ameli[(~df_ameli['spe'].str.contains('exclusif')) &\
#                      (df_ameli['spe'] != u'Médecin gériatre')].copy()
df_physicians = df_ameli[df_ameli['spe'] == u'MG'].copy()

# gender
ls_fix_name = [[' HELENE ROLLAND CAPPIELLO', 'Mme  HELENE ROLLAND CAPPIELLO'],
               [' CHRISTIAN BASTIEN', 'M. CHRISTIAN BASTIEN'],
               [' ERIC DHENNAIN', 'M. ERIC DHENNAIN']]
for old_name, new_name in ls_fix_name:
  df_physicians.loc[df_physicians['name'] == old_name,
                 'name'] = new_name

df_physicians['gender'], df_physicians['full_name'] = \
  zip(*df_physicians.apply(lambda x: re.split('(M\.|Mme)', x['name'])[1:3], axis = 1))
df_physicians['full_name'] = df_physicians['full_name'].str.strip()
df_physicians.drop(['name'], axis = 1, inplace = True)

# ###############
# GET INSEE CODES
# ###############

df_physicians['dpt'] = df_physicians['zip'].str.slice(stop = 2)

matching_insee = MatchingINSEE(os.path.join(path_dir_match_insee,
                                            'df_corr_gas.csv'))

ls_match_res = []
ls_rows = []
for row_i, row in df_physicians.iterrows():
  # city, dpt_code, zip_code = format_str_city_insee(row['city']), row['dpt'], row['zip']
  match_res = matching_insee.match_city(row['city'], row['dpt'], row['zip'])
  ls_match_res.append(match_res)
# if several matched: check if only one code insee, if not: None + error message
  if not match_res[0]:
    ls_rows.append(None)
  elif (len(match_res[0]) == 1) or\
     ([x[2] == match_res[0][0][2] for x in match_res[0]]):
    ls_rows.append(match_res[0][0][2])
  else:
    ls_rows.append(None)
se_insee_codes = pd.Series(ls_rows, index = df_physicians.index)
df_physicians['CODGEO'] = se_insee_codes
# print df_physicians[df_physicians['CODGEO'].isnull()].T.to_string()

# #######
# OUTPUT
# #######

file_extension = 'gp_2012'

# CSV
df_physicians.to_csv(os.path.join(path_built_csv,
                                u'df_{:s}.csv'.format(file_extension)),
                  encoding = u'utf-8',
                  float_format = u'%.1f')

## JSON
#df_physicians = df_physicians.copy()
#df_physicians.reset_index(inplace = True)
#ls_ls_physicians = [list(x) for x in df_physicians.values]
##enc_json(ls_ls_physicians,
##         os.path.join(path_dir_built_json,
##                      ls_'%s.json' %file_extension))
