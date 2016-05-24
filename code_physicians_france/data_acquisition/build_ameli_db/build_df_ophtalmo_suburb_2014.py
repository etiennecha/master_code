#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
from matching_insee import *
import re
import time
from collections import Counter
import pprint
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels as sm
import statsmodels.formula.api as smf

path_source_2014 = os.path.join(path_data,
                                u'data_ameli',
                                u'data_source',
                                u'ameli_2014')

path_built = os.path.join(path_data,
                          u'data_ameli',
                          'data_built')

path_built_csv = os.path.join(path_built, 'data_csv')
path_built_json = os.path.join(path_built, 'data_json')

path_dir_match_insee = os.path.join(path_data,
                                    u'data_insee',
                                    u'match_insee_codes')

# #########
# LOAD DATA
# #########

dict_physicians = {}
for i in [77, 78, 92, 93, 94, 95]:
  dict_physicians.update(\
    dec_json(os.path.join(path_source_2014,
                          u'dict_ophtalmologiste_{:02d}'.format(i))))

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

# Adhoc name fixing (missing first name)
dict_physicians['Cbc1kjIxMTay'][0] = dict_physicians['Cbc1kjIxMTay'][0][0:2] +\
                                     ['GHASSEN'] +\
                                     dict_physicians['Cbc1kjIxMTay'][0][2:]

# Dict for adhoc address fixing
dict_adhoc_addresses = {-3 : ['Cbc1kzA3MDa2', 'B7o1kzQwOTe3', 'Cbc1mjQyMDW3',
                              'CbA1kDI5MjC7', 'Cbc1mjQzNDS3', 'CbY1kjs0Nza1',
                              'CbA1lTI1MDC7', 'B7o1kzcxNDG6', 'CbA1mjE1MzG7'],
                        -2 : ['B7U1mjM3NTG3', 'Cbc1kzI2OTC7', 'B7U1mjM3MzOz',
                              'B7U1lTI2MTa6', 'B7U1kjM3Nje0', 'Cbc1mjQzODOw',
                              'Cbc1kjIxMzSx', 'CbE1kjQ0ODW2', 'B7o1mjM3NTO1',
                              'Cbc1mjQzNzSw', 'B7U1lTI3NTCy', 'CbY1kzY1NDa0']}
dict_adhoc_addresses = {x:k for k,v in dict_adhoc_addresses.items() for x in v}

# Clean (0) name-address-phone component and (2) info component (checked always 3 same items)
ls_formatted = []
ls_ls_ap = []
for id_physician, ls_physician in dict_physicians.items():
  ind_name = ls_physician[0].index(u'Médecin ophtalmologiste')
  ls_name = ls_physician[0][:ind_name]
  ls_address_phone = ls_physician[0][ind_name + 1:]
  ls_ls_ap.append(ls_address_phone)
  if re.match(u'0[0-9]{9}$', ls_address_phone[-1]):
    phone = ls_address_phone[-1]
    ls_address = ls_address_phone[:-1]
  else:
    ls_address = ls_address_phone
    phone = None
  if not re.match(u'[0-9]{5}.*', ls_address[-1]):
    print 'Problem end of address, no zip:', ls_address
  # adhoc address fixing
  if id_physician in dict_adhoc_addresses:
    ls_address = [ls_address[dict_adhoc_addresses[id_physician]], ls_address[-1]]
  # todo: further improve (not ok for geocoding now)
  # first pass: identify pbms... second pass: keep right chunk of address
  if not re.match(u'[0-9]+', ls_address[-2]):
    print 'Keep more than last two address items?', id_physician, ls_address
    ls_address = ls_address [-3:]
  else:
    ls_address = ls_address[-2:]
  dict_physicians[id_physician][0] = [ls_name, phone, ls_address]
  dict_physicians[id_physician][2] = [x for ls_x in ls_physician[2] for x in ls_x]

## Check addresses with more than 2 components
## Standard extraction: ls_address[0] => street, ls_address[-1] => zip_city
## Fix if would yield bad result
#for k,v in dict_physicians.items():
#  if len(v[0][2]) != 2:
#    print k, v[0][2]

# Analysis of ls_address_phone
ls_len_ap = []
for ls_ap in ls_ls_ap:
  if re.match(u'^[0-9]{10}$', ls_ap[-1]):
    ls_len_ap.append(len(ls_ap)-1)
  else:
    ls_len_ap.append(len(ls_ap))
# => mess: see how to do (if -2 does not start with 1-3 numbers : check rue/bvd/street etc)

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

# Clean (3) services/prices component
ls_unique_services = []
for id_physician, ls_physician in dict_physicians.items():
  if ls_physician[3]:
    for service in ls_physician[3]:
      ls_unique_services.append(tuple(service[0][0]))
ls_unique_services = list(set(ls_unique_services))
ls_unique_services = [service[0] for service in ls_unique_services]
# Can safely keep only first component as name of services i.e. service[0][0][0]
ls_secondary_title = []
ls_all_physician_services = []
for id_physician, ls_physician in dict_physicians.items():
  ls_physician_services = []
  if ls_physician[3]:
    for service in ls_physician[3]:
      title = service[0][0][0]
      rembt = service[0][1]
      ls_secondary_title.append(service[0][2])
      ls_tarifs = zip(*[[' '.join(ls_elts) for ls_elts in ls_elt] for ls_elt in service[1]])
      ls_physician_services.append([title, rembt, ls_tarifs])
  dict_physicians[id_physician][3] = ls_physician_services

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
      avg_price = np.mean(map(lambda x: float(x.rstrip(u'\u20ac').replace(u',', u'.')), ls_prices))
ls_consultations_avg = [np.mean(map(lambda x:\
                                    float(x.rstrip(u'\u20ac').replace(u',', u'.')),
                                  ls_prices))\
                            for ls_prices in ls_consultations_prices]

## DEPRECATE (done with dataframe)
#print np.mean(ls_consultations_avg)
#bins = range(20, 220, 20)
#n, bins, patches = plt.hist(ls_consultations_avg, bins)
#plt.show()
#
##bins = range(20, 220, 10)
##n, bins, patches = plt.hist(ls_consultations_avg,
##                            bins,
##                            histtype='step',
##                            normed = 1,
##                            cumulative = True)
##plt.ylim(0,1.05)
##plt.show()
### todo: improve design and make cut-offs clear: pby need to change bins)

# BUILD DF PHYSICIANS

ls_unique_services.remove('Consultation')
ls_rows_physicians = []
for id_physician, ls_physician in dict_physicians.items():
  ls_physician_info = [id_physician] +\
                      ls_physician[0][0] +\
                      ls_physician[0][2][0:1]+\
                      ls_physician[0][2][-1:] +\
                      ls_physician[2]
  # prices
  ls_consultation_prices = [None, None, None, None]
  ls_other_prices = [None for i in ls_unique_services]
  for service in ls_physician[3]:
    if service[0] == 'Consultation':
      ls_consultation_prices = get_service_price(id_physician,
                                                 [ls_x[-1] for ls_x in service[2]])
    else:
      service_ind = ls_unique_services.index(service[0])
      ls_service_prices = get_service_price(id_physician,
                                                 [ls_x[-1] for ls_x in service[2]])
      #if len(service[2]) == 1:
      #  # ls_service_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][0][1])
      #  ls_service_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\u20ac', service[2][0][1])
      #else:
      #  # ls_service_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][1][1])
      #  ls_service_prices = re.findall(u'[0-9]{2,4}(?:,[0-9]{0,2})?\u20ac', service[2][1][1])
      #avg_price = np.mean(map(lambda x: float(x.rstrip(u'\u20ac').replace(u',', u'.')),
      #                        ls_service_prices))
      ls_other_prices[service_ind] = ls_service_prices[0]
  ls_rows_physicians.append(ls_physician_info + ls_consultation_prices + ls_other_prices)
columns = ['id_physician', 'gender', 'name', 'surname', 'street',
           'zip_city', 'convention', 'carte_vitale', 'status'] +\
          ['c_base', 'c_proba', 'c_min', 'c_max'] +\
          ls_unique_services
df_physicians = pd.DataFrame(ls_rows_physicians, columns = columns)
df_physicians.set_index('id_physician', inplace= True)

print u'\nPhysician dataframe'
print df_physicians.info() #seems displays column count only if index set

# #########
# FORMAT DF
# #########

# overview of fields to be standardized
for field in ['gender', 'zip_city', 'convention', 'carte_vitale', 'status']:
  print u'\n', field
  print df_physicians[field].value_counts()

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
                     u'75116 PARIS' : '75016 PARIS'}
df_physicians['zip_city'] =\
  df_physicians['zip_city'].apply(
     lambda x: standardize_string(dict_zip_city_rep, x))
df_physicians = df_physicians[df_physicians['zip_city'] != '75175 ROUEN CEDEX'].copy()

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

# Some standardization of service columns
df_physicians.rename(\
  columns = {u'Consultation' : 'consultation',
             u'Avis de consultant': u'avis',
             u"Fond d'oeil" : u"fond",
             u"Imagerie de la" : u"imagerie",
             u"Chirurgie de la cataracte" : u"chirurgie_cat"}, inplace = True)

# ###############
# GET INSEE CODES
# ###############

# PARSE ADDRESS
pat_zip = "([0-9]?[0-9AB][0-9]{3})\s"
df_physicians['zip'] = df_physicians['zip_city'].apply(\
                         lambda x: re.match(pat_zip, x).group(1))
pat_city = "[0-9]?[0-9AB][0-9]{3}\s([A-Za-z\s\-\']*)?"
df_physicians['city'] = df_physicians['zip_city'].apply(\
                          lambda x: re.match(pat_city, x).group(1).\
                                      replace('CEDEX', '').strip())
# df_physicians.drop(['zip_city'], axis = 1, inplace = True)
df_physicians['dpt'] = df_physicians['zip'].str.slice(stop = 2)

# FIX TYPOS
ls_city_fix = [(u'GRETZ ARMAINVILLERS', u'GRETZ ARMAINVILLIERS'),
               (u'MAREUILS LES MEAUX', u'MAREUIL LES MEAUX')]
for old_city, new_city in ls_city_fix:
  df_physicians.loc[df_physicians['city'] == old_city,
                    'city'] = new_city

# FIX ZIP CITY TO ACHIEVE COMPLETE INSEE CODE MATCHING
ls_fix_zip_city = [['95610', 'ERAGNY SUR OISE', '95610', 'ERAGNY'],
                   ['95130', 'FRANCONVILLE LA GARENNE', '95130', 'FRANCONVILLE'],
                   ['92081', 'PARIS LA DEFENSE', '92800', 'PUTEAUX'],
                   ['92092', 'PARIS LA DEFENSE', '92092', 'PUTEAUX']]
for old_zip, old_city, new_zip, new_city in ls_fix_zip_city:
  df_physicians.loc[(df_physicians['zip'] == old_zip) &\
                    (df_physicians['city'] == old_city),
                    ['zip', 'city']] = new_zip, new_city

# PERFORM MATCHING
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

df_physicians.drop(['zip_city'], axis = 1, inplace = True)

# #######
# DISPLAY
# #######

ls_disp_base_1 = ['gender','name', 'surname', 'street', 'zip', 'city',
                  'convention', 'carte_vitale', 'status']
ls_disp_base_2 = ['gender','name', 'surname', 'zip', 'city',
                  'convention', 'carte_vitale', 'status']
ls_disp_services = ['c_base', 'c_proba', 'c_min', 'c_max',
                    'avis', 'fond', 'imagerie', 'chirurgie_cat']

print u'\nOverview:'
print df_physicians[ls_disp_base_1][0:10].to_string()

# print df_physicians[ls_disp_base_2 + ls_disp_services[:3]].to_string()

# pprint.pprint(dict_physicians['B7c1mzE3MTOx'])
# pbm with Chirurgie: truncated?

# DEAL WITH DUPLICATES I.E. PHYSICIANS WITH SEVERAL LOCATIONS
# locations to be kept.. ok for several line but identify (propagate tarifs?)

# #########
# OUTPUT
# #########

file_extension = u'ophtalmo_suburb_2014' # exception: several files...

# CSV
df_physicians.\
  to_csv(os.path.join(path_built_csv,
                      'df_{:s}.csv'.format(file_extension)),
         encoding = u'utf-8',
         float_format = u'%.1f')

## JSON
#df_physicians.reset_index(inplace = True)
#ls_ls_physicians = [list(x) for x in df_physicians.values]
#enc_json(ls_ls_physicians, os.path.join(path_built_json,
#                                        'ls_%s.json' %file_extension))
