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

path_dir_ameli = os.path.join(path_data, u'data_ameli', 'data_source', 'ameli_2014')
path_dir_built_json = os.path.join(path_data, u'data_ameli', 'data_built', 'json')

#file_extension = u'ophtalmologiste_75'
#ls_ls_physicians = dec_json(os.path.join(path_dir_ameli, u'ls_ls_%s' %file_extension))

dict_physicians = {}
for i in [77, 78, 92, 93, 94, 95]:
  dict_physicians.update(\
    dec_json(os.path.join(path_dir_ameli,
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

ls_rows_physicians = []
for id_physician, ls_physician in dict_physicians.items():
  ls_physician_info = [id_physician] +\
                      ls_physician[0][0] +\
                      ls_physician[0][2][0:1]+\
                      ls_physician[0][2][-1:] +\
                      ls_physician[2]
  # prices
  ls_physician_prices = [None for i in ls_unique_services]
  for service in ls_physician[3]:
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
      ls_physician_prices[service_ind] = avg_price
  ls_rows_physicians.append(ls_physician_info + ls_physician_prices)
columns = ['id_physician', 'gender', 'name', 'surname', 'street',
           'zip_city', 'convention', 'carte_vitale', 'status'] + ls_unique_services
df_physicians = pd.DataFrame(ls_rows_physicians, columns = columns)
df_physicians.set_index('id_physician', inplace= True)

print u'\nPhysician dataframe'
print df_physicians.info() #seems displays column count only if index set

# CLEAN DF TO IMPROVE DISPLAY

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

# Add departement
df_physicians['dpt'] = df_physicians['zip_city'].str.slice(stop=2)

# DISPLAY

ls_disp_base_1 = ['gender','name', 'surname', 'street', 'zip_city',
                  'convention', 'carte_vitale', 'status']
ls_disp_base_2 = ['gender','name', 'surname', 'zip_city',
                  'convention', 'carte_vitale', 'status']
ls_disp_services = ['consultation', 'avis', 'fond', 'imagerie', 'chirurgie_cat']
print df_physicians[ls_disp_base_1].to_string()
# print df_physicians[ls_disp_base_2 + ls_disp_services[:3]].to_string()

# pprint.pprint(dict_physicians['B7c1mzE3MTOx'])
# pbm with Chirurgie: truncated?

# DEAL WITH DUPLICATES I.E. PHYSICIANS WITH SEVERAL LOCATIONS
# locations to be kept.. ok for several line but identify (propagate tarifs?)

## STORE
#
#df_physicians.reset_index(inplace = True)
#ls_ls_physicians = [list(x) for x in df_physicians.values]
#enc_json(ls_ls_physicians, os.path.join(path_dir_built_json, '%s.json' %file_extension))
## todo: set id_physician back as index?

# PRELIMINARY STATS DES

df_physicians_a = df_physicians[df_physicians['status'] != u'Hopital L'].copy()

# old way => used pd
print u'\nNb of Physicians, nb sect 1, nb sect 2, mean and median visit price by dpt'
print u'-'*30
ls_title_print = [u'Dpt', u'#Phys', u'#Phys1', u'#Phys2', u'Mean', u'Med']
print u'{0:12}{1:>10}{2:>10}{3:>10}{4:>10}{5:>10}'.format(*ls_title_print)
for dpt in df_physicians_a['dpt'].unique():
  nb_physicians = len(df_physicians_a[df_physicians_a['dpt'] == dpt])
  nb_physicians_1 = len(df_physicians_a[(df_physicians_a['dpt'] == dpt) &\
                                        (df_physicians_a['convention'] == '1')]) 
  nb_physicians_2 = len(df_physicians_a[(df_physicians_a['dpt'] == dpt) &\
                                        (df_physicians_a['convention'] == '2')]) 
  mean_consultation = df_physicians_a['consultation'][df_physicians_a['dpt'] == dpt].mean()
  med_consultation = df_physicians_a['consultation'][df_physicians_a['dpt'] == dpt].median()
  print u'{0:12}{1:10d}{2:10d}{3:10d}{4:10.2f}{5:10.2f}'.format(dpt,
                                                                nb_physicians,
                                                                nb_physicians_1,
                                                                nb_physicians_2,
                                                                mean_consultation,
                                                                med_consultation)

## FIX ADDRESSES FOR GEOCODING (ZIP CODE CEDEX)
#df_physicians['zip_city'][df_physicians['zip_city'].str.contains('CEDEX')]
# todo: check also bis (e.g. "27B") and ter (same pattern)

### SYNTAX ELEMENTS
###df_physicians[['zip_city', 'consultation']].groupby('convention').agg([len, np.mean])
##gb_zip_city = df_physicians[['zip_city'] + ls_disp_services].groupby('zip_city')
##df_ardt_count = gb_zip_city.count()
##df_ardt_mean = gb_zip_city.mean()
##df_ardt_med = gb_zip_city.median()
### print gb_zip_city.describe().to_string()
#
### todo: stats des by ardt with groupby
##df_physicians[['zip_city', 'consultation']].groupby('zip_city').aggregate([len, np.mean])
#
## TODO: GEOCODING (?), LOAD INSEE DATA + INTEGRATE WITH OTHER PHYSICIAN DATA
## TODO: PUT FOLLOWING IN ANOTHER SCRIPT (AND LOAD DF PHYSICIANS)
