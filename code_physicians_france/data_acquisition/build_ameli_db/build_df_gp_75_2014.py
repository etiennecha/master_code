#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
import re
import time
from collections import Counter
import pprint
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels as sm
import statsmodels.formula.api as smf

path_source_ameli = os.path.join(path_data,
                                 u'data_ameli',
                                 u'data_source',
                                 u'ameli_2014')

path_built_ameli = os.path.join(path_data,
                                u'data_ameli',
                                u'data_built')

path_built_csv= os.path.join(path_built_ameli, 'data_csv')
path_built_json = os.path.join(path_built_ameli, u'data_json')

# #########
# LOAD DATA
# #########

dict_physicians = {}
for i in range(1, 21):
  dict_physicians.update(\
    dec_json(os.path.join(path_source_ameli,
                          u'dict_medecin-generaliste_750{:02d}'.format(i))))

# Content for each physician: [ls_address_name, ls_places, ls_infos, ls_actes]
# Explore field contents (all are lists, None are not counted)
ls_dict_counters = [{} for i in dict_physicians[dict_physicians.keys()[0]]]
for id_physician, ls_physician in dict_physicians.items():
  for i, field in enumerate(ls_physician):
    if field:
      ls_dict_counters[i].setdefault(len(field), []).append(id_physician)
print u'\nComponents by diversity of contents'
for i, dict_counters in enumerate(ls_dict_counters):
  print 'field', i, ':', [(k, len(v)) for k,v in dict_counters.items()]

# Clean (0) name-address-phone component and (2) info component (checked always 3 same items)
ls_formatted = []
for id_physician, ls_physician in dict_physicians.items():
  # e.g. u"M\xe9decin g\xe9n\xe9raliste \u2013 Acupuncteur en mode d'exercice exclusif"
  ind_name = None # breaks if following does not match
  for i, elt in enumerate(ls_physician[0]):
    if re.match(u'Médecin généraliste', elt):
      ind_name = i
      specialty = elt.replace(u'\u2013', u'-')
  ls_name = ls_physician[0][:ind_name]
  ls_address_phone = ls_physician[0][ind_name + 1:]
  if re.match(u'0[0-9]{9}$', ls_address_phone[-1]):
    phone = ls_address_phone[-1]
    ls_address = ls_address_phone[:-1]
  else:
    ls_address = ls_address_phone
    phone = None
  # specific to paris for now!
  if not re.match(u'75[0-9]{3}.*', ls_address[-1]):
    print 'Problem end of address, no zip:', ls_address
  # todo: further improve (not ok for geocoding now)
  if not re.match(u'[0-9]+', ls_address[-2]):
    print 'Want to keep more than last two items?', ls_address
    ls_address = ls_address [-3:]
  else:
    ls_address = ls_address[-2:]
  dict_physicians[id_physician][0] = [ls_name, phone, ls_address]
  dict_physicians[id_physician][2] = [x for ls_x in ls_physician[2] for x in ls_x] +\
                                     [specialty]
# Check addresses with more than 2 components
# Standard extraction: ls_address[0] => street, ls_address[-1] => zip_city
# Fix if would yield bad result
for k,v in dict_physicians.items():
	if len(v[0][2]) != 2:
		print v[0][2]

# Clean (1) multiple location component
ls_nb_other_locations = [len(v[1]) if v[1] else 0 for k,v in dict_physicians.items()]
print u'\nPhysicians with multiple locations'
print pd.Series(ls_nb_other_locations).value_counts()
# build mapping between id_physicians: how to work with it?
dict_other_locations = {k:[re.search('autre-lieu-(.*?)-', x[0]).group(1) for x in v[1]]\
                          if v[1] else [] for k,v in dict_physicians.items()}
# check those not available i.e. a priori other location(s?) not in paris
dict_not_paris = {}
for k,v in dict_other_locations.items():
	for x in v:
		if x not in dict_other_locations.keys():
			dict_not_paris.setdefault(k, []).append(x)

# Can NOT safely keep only first component as name of services i.e. service[0][0][0]
ls_secondary_title = []
ls_all_physician_services = []
for id_physician, ls_physician in dict_physicians.items():
  ls_physician_services = []
  if ls_physician[3]:
    for service in ls_physician[3]:
      # designed to break if not sure
      title, ind_title_service = None, None
      if service[0][0] == ['Consultation']:
        title = u'Consultation'
      else:
        for i, x in enumerate(service[0][0]):
          if (x == u'En savoir plus') |\
             (x == u"Qu'est-ce que c'est?"):
            ind_title_service = i
            break
        title = ' '.join(service[0][0][:ind_title_service])
      rembt = service[0][1]
      ls_secondary_title.append(service[0][2])
      ls_tarifs = zip(*[[' '.join(ls_elts) for ls_elts in ls_elt] for ls_elt in service[1]])
      ls_physician_services.append([title, rembt, ls_tarifs])
  dict_physicians[id_physician][3] = ls_physician_services

# Clean (3) services/prices component
ls_unique_services = []
for id_physician, ls_physician in dict_physicians.items():
  if ls_physician[3]:
    for service in ls_physician[3]:
      ls_unique_services.append(service[0])
ls_unique_services = list(set(ls_unique_services))
# ls_unique_services = [service[0] for service in ls_unique_services]

# Seems ok: stats desc about service available and price (vs. sec 1. sec.2...)
ls_consultations = []
ls_consultations_prices = []
for id_physician, ls_physician in dict_physicians.items():
  avg_price = None
  for service in ls_physician[3]:
    if service[0] == u'Consultation' and service[2]:
      ls_consultations.append((i, service[2]))
      if len(service[2]) == 1:
        # ls_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][0][1])
        ls_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\u20ac', service[2][0][1])
      else:
        # ls_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][1][1])
        ls_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\u20ac', service[2][1][1])
      ls_consultations_prices.append(ls_prices)
      avg_price = np.mean(map(lambda x: float(x.rstrip(u'\u20ac').replace(u',', u'.')),
                          ls_prices))
ls_consultations_avg = [np.mean(map(lambda x:\
                                    float(x.rstrip(u'\u20ac').replace(u',', u'.')),
                                  ls_prices))\
                            for ls_prices in ls_consultations_prices]

# ########
# BUILD DF
# ########

ls_unique_services.remove('Consultation')

ls_rows_physicians = []
for id_physician, ls_physician in dict_physicians.items():
  # [1] : Gender, Last Name, First Name, [2] : Street, [3]: Zip, City
  # [4] : Convention, Carte vitale, Status, Specialty [5] : Nb of locations
  ls_physician_info = [id_physician] +\
                      ls_physician[0][0] +\
                      ls_physician[0][2][0:1]+\
                      ls_physician[0][2][-1:]+\
                      ls_physician[2]+\
                      [len(ls_physician[1]) + 1 if ls_physician[1] else 1]
  # prices
  ls_consultation_prices = [None, None, None, None]
  ls_other_prices = [None for i in ls_unique_services]
  for service in ls_physician[3]:
    # todo: generalize
    if service[0] == u'Consultation':
      ls_consultation_prices = get_service_price(id_physician,
                                                 [ls_x[-1] for ls_x in service[2]])
    else:
      service_ind = ls_unique_services.index(service[0])
      if service[2]:
        if len(service[2]) == 1:
          # ls_service_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][0][1])
          ls_service_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\u20ac', service[2][0][1])
        else:
          # ls_service_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][1][1])
          ls_service_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\u20ac', service[2][1][1])
        avg_price = np.mean(map(lambda x: float(x.rstrip(u'\u20ac').replace(u',', u'.')),
                                ls_service_prices))
        ls_other_prices[service_ind] = avg_price
  ls_rows_physicians.append(ls_physician_info + ls_consultation_prices + ls_other_prices)
columns = ['id_physician', 'gender', 'name', 'surname', 'street',
           'zip_city', 'convention', 'carte_vitale', 'status', 'spe', 'nb_loc'] +\
          ['c_base', 'c_proba', 'c_min', 'c_max'] +\
          ls_unique_services
df_physicians = pd.DataFrame(ls_rows_physicians, columns = columns)
df_physicians.set_index('id_physician', inplace= True)

print u'\nPhysician dataframe'
print df_physicians.info() #seems displays column count only if index set

#print df_physicians[['gender', 'name', 'surname', 'street', 'zip_city',
#                     'convention', 'carte_vitale', 'status', 'Consultation']].to_string() 

# #########
# FORMAT DF
# #########

# overview of fields to be standardized
for field in ['gender', 'zip_city', 'convention', 'carte_vitale', 'status']:
  print u'\n', field
  print df_physicians[field].value_counts()

# convention
dict_convention_rep = {u"Conventionné secteur 2" : u'2',
                       u"Conventionné secteur 1" : u'1',
                       u"Conventionné secteur 2 avec contrat d'accès aux soins" : u'2 AS',
                       u"Conventionné secteur 1 avec droit permanent à dépassement" : u'1 DPD',
                       u"Conventionné secteur 1 avec contrat d'accès aux soins" : u'1 AS',
                       u"Non conventionné" : u'NC'}
df_physicians['convention'] =\
  df_physicians['convention'].apply(
     lambda x: dict_convention_rep.get(x, None))

# carte_vitale
dict_carte_vitale_rep = {u"Carte Vitale : Oui" : u'oui',
                         u"Carte Vitale : Non" : u'non'}
df_physicians['carte_vitale'] =\
  df_physicians['carte_vitale'].apply(
     lambda x: dict_carte_vitale_rep.get(x, None))

# status
dict_status_rep =\
  {u"Temps partagé entre activité libérale et activité hospitalière" : u'Mixte H',
   u"Libéral intégral": u"Liberal",
   u"Temps partagé entre activité libérale et activité salariée (hors hôpital)" : u'Mixte NH',
   u"Hospitalier avec activité libérale au sein de l'hôpital" : u"Hopital L"}
df_physicians['status'] =\
  df_physicians['status'].apply(
     lambda x: dict_status_rep.get(x, None))

# specialty
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
df_physicians['spe'] =\
  df_physicians['spe'].apply(
     lambda x: dict_spe_rep.get(x, None))

# Some standardization of service columns
df_physicians.rename(\
  columns = {# u'Consultation' : 'consultation',
             u'Consultation spécifique pour un enfant de moins de 2 ans' :\
                u'c_0-2a',
             u"Consultation spécifique pour un enfant entre 2 et 6 ans" :\
                u"c_2-6a",
             u"Électrocardiographie [ECG]" : "ecg"}, inplace = True)

# ###############
# GET INSEE CODES
# ###############

# zip_city
def standardize_string(dict_search_replace, str_to_std):
  for k,v in dict_search_replace.items():
    if re.search(k, str_to_std):
      return v
  return str_to_std
# not sure if bad in case of geocoding to replace 75116 by 75016: check
dict_zip_city_rep = {u'CEDEX 14' : u'75014 PARIS',
                     u'CEDEX 12' : u'75012 PARIS',
                     u'PARIS CEDEX 20': u'75020 PARIS',
                     u'PARIS CEDEX 10' : u'75010 PARIS',
                     u'75116 PARIS' : u'75016 PARIS'}
df_physicians['zip_city'] =\
  df_physicians['zip_city'].apply(
     lambda x: standardize_string(dict_zip_city_rep, x))
# df_physicians = df_physicians[df_physicians['zip_city'] != '75175 ROUEN CEDEX'].copy()

df_physicians['zip'] = df_physicians['zip_city'].str.slice(stop = 5)
df_physicians['city'] = df_physicians['zip_city'].str.slice(start = 5).str.strip()
df_physicians['CODGEO'] = df_physicians['zip'].apply(\
                            lambda x: re.sub(u'750([0-9]{2})', u'751\\1', x))
df_physicians.drop(['zip_city'], axis = 1, inplace = True)

# ########
# DISPLAY
# ########

ls_disp_base_1 = ['gender', 'name', 'surname', 'street', 'zip', 'city',
                  'convention', 'carte_vitale', 'status', 'spe', 'nb_loc']
ls_disp_base_2 = ['gender', 'name', 'surname', 'zip', 'city',
                  'convention', 'carte_vitale', 'status', 'spe', 'nb_loc']
ls_disp_services = ['c_base', 'c_proba', 'c_min', 'c_max',
                    'c_0-2a', 'c_2-6a', 'ecg']

#print df_physicians[ls_disp_base_1].to_string()
#print df_physicians[ls_disp_base_2 + ls_disp_services].to_string()

# DEAL WITH DUPLICATES I.E. PHYSICIANS WITH SEVERAL LOCATIONS
# locations to be kept.. ok for several line but identify (propagate tarifs?)

# #######
# OUTPUT
# #######

file_extension = 'gp_75_2014'

# CSV
df_physicians[ls_disp_base_1 + ls_disp_services].\
  to_csv(os.path.join(path_built_csv, 'df_{:s}.csv'.format(file_extension)),
         encoding = u'utf-8',
         float_format = u'%.1f')

## JSON
#df_physicians = df_physicians[ls_disp_base_1 + ls_disp_services].copy()
#df_physicians.reset_index(inplace = True)
#ls_ls_physicians = [list(x) for x in df_physicians.values]
##enc_json(ls_ls_physicians,
##         os.path.join(path_dir_built_json,
##                      'ls_{:s}.json'.format(file_extension))
