#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re
import json
import time
from collections import Counter
import pprint
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def ls_to_clean(ls_to_clean):
  ls_to_clean = map(lambda x: x.replace(u'&gt;', u'').replace(u'&nbsp;',u'').strip(), ls_to_clean)
  return [x for x in ls_to_clean if x]

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

path_physicians = r'\\ulysse\users\echamayou\Bureau\Etienne_work\Data\data_ameli'
# path_physicians = r'C:\Users\etna\Desktop\Etienne_work\Data\data_ameli'

ls_ls_physicians = dec_json(path_physicians + r'\ls_ls_physicians')
dict_physicians = dec_json(path_physicians + r'\dict_physicians')

# [ls_address_name, ls_places, ls_infos, ls_actes]

# Explore components by length (all are lists, None are not counted)
ls_dict_counters = [{} for i in dict_physicians[dict_physicians.keys()[0]]]
for id_physician, ls_physician in dict_physicians.items():
  for i, field in enumerate(ls_physician):
    if field:
      ls_dict_counters[i].setdefault(len(field), []).append(id_physician)
for i, dict_counters in enumerate(ls_dict_counters):
  print 'field', i, ':', [(k, len(v)) for k,v in dict_counters.items()]

# Clean (0) name-address-phone component and (2) info component (checked always 3 same items)
ls_formatted = []
for id_physician, ls_physician in dict_physicians.items():
  ind_name = ls_physician[0].index(u'Médecin ophtalmologiste')
  ls_name = ls_physician[0][:ind_name]
  ls_address_phone = ls_physician[0][ind_name + 1:]
  if re.match(u'0[0-9]{9}$', ls_address_phone[-1]):
    phone = ls_address_phone[-1]
    ls_address = ls_address_phone[:-1]
  else:
    ls_address = ls_address_phone
    phone = None
  if not re.match(u'75[0-9]{3}.*', ls_address[-1]):
    print 'Problem end of address, no zip:', ls_address
  # TODO: further improve (not ok for geocoding now)
  if not re.match(u'[0-9]+', ls_address[-2]):
    print 'Want to keep more than last two items?', ls_address
    ls_address = ls_address [-3:]
  else:
    ls_address = ls_address[-2:]
  dict_physicians[id_physician][0] = [ls_name, phone, ls_address]
  dict_physicians[id_physician][2] = [x for ls_x in ls_physician[2] for x in ls_x]

# Clean (1) multiple location component (TODO)

# Clean (3) services/prices component (TODO)
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
        ls_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][0][1])
      else:
        ls_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][1][1])
      ls_consultations_prices.append(ls_prices)
      avg_price = np.mean(map(lambda x: float(x.rstrip(u'\u20ac')), ls_prices))
ls_consultations_prices_avg = [np.mean(map(lambda x: float(x.rstrip(u'\u20ac')), ls_prices))\
                            for ls_prices in ls_consultations_prices] 
print np.mean(ls_consultations_prices_avg)
bins = range(20, 220, 20)
n, bins, patches = plt.hist(ls_consultations_prices_avg, bins)
plt.show()
#bins = range(20, 220, 10)
#n, bins, patches = plt.hist(ls_consultations_prices_avg, bins, histtype='step', normed = 1, cumulative = True)
#plt.ylim(0,1.05)
#plt.show()
## TODO: improve design and make cut-offs clear: pby need to change bins)

# Create pandas df (generalize... create function)
ls_ls_physicians_temp = []
for id_physician, ls_physician in dict_physicians.items():
  ls_physician_temp_info = [id_physician] + ls_physician[0][0] + ls_physician[0][2][-1:] + ls_physician[2]
  # prices
  ls_physician_temp = [None for i in ls_unique_services]
  for service in ls_physician[3]:
    service_ind = ls_unique_services.index(service[0])
    if service[2]:
      if len(service[2]) == 1:
        ls_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][0][1])
      else:
        ls_prices = re.findall(u'[0-9]{2,3}\u20ac', service[2][1][1])
      avg_price = np.mean(map(lambda x: float(x.rstrip(u'\u20ac')), ls_prices))
      ls_physician_temp[service_ind] = avg_price
  ls_ls_physicians_temp.append(ls_physician_temp_info + ls_physician_temp)

columns = ['id_physician', 'gender', 'name', 'surname' , 
           'zip_city', 'convention', 'carte_vitale', 'status'] + ls_unique_services

pd_df_physicians = pd.DataFrame(ls_ls_physicians_temp, columns = columns)
pd_df_physicians.set_index('id_physician', inplace= True)
print pd_df_physicians.info() #seems displays column count only if index set
print pd_df_physicians['zip_city'].value_counts()
pd_df_physicians[pd_df_physicians[u'convention'] == u'Conventionné secteur 1']

ls_stats_ardt = []
for i in range(1,21):
  ls_stats_ardt.append(pd_df_physicians['Consultation']\
                        [pd_df_physicians['zip_city'].str.contains('750%02d'%i)].describe())
pd_df_stats_ard = pd.DataFrame(ls_stats_ardt, index=['%02d'%i for i in range(1,21)])
print pd_df_stats_ard[['mean','25%', '50%', '75%', 'count']].corr()
# Scatter: TODO add label nb of ardt + fit line
#plt.scatter(pd_df_stats_ard['count'], pd_df_stats_ard['mean'])
#plt.scatter(pd_df_stats_ard['count'], pd_df_stats_ard['50%'])

#TODO: represent homogeneity within ardts

# CHECK OSM ROUTE SERVICE : http://wiki.openstreetmap.org/wiki/OpenRouteService
