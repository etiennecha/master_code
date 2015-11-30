#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
import os, sys
import json
import re
from functions_string import *
import pprint

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

# Records 0, 1, 2 and 3 (up to 2012 included) use (kind of) list with the following order:
list_services =  [u'Automate CB',
                  u'Laverie',
                  u'Toilettes publiques',
                  u'Boutique alimentaire',
                  u'Boutique non alimentaire',
                  u'Restauration à emporter',
                  u'Restauration sur place',
                  u'Relais colis',
                  u'Vente de gaz domestique',
                  u'Vente de fioul domestique',
                  u'Vente de pétrole lampant',
                  u'Carburant qualité supérieure',
                  u'GPL',
                  u'Station de gonflage',
                  u'Station de lavage',
                  u'Lavage multi-programmes',
                  u'Lavage haute-pression',
                  u'Baie de service auto',
                  u'Piste poids lourds',
                  u'Location de véhicule']

def format_gouv_stations_201111(list_dict_stations):
  dict_dict_stations = {}
  for dict_station in list_dict_stations:
    # Std list of services
    dict_station['ser19'] = dict_station['ser 19']
    list_station_services = []
    for i in range(1, 21):
      if dict_station['ser%s' %i] == '1':
        list_station_services.append(list_services[i-1])
    # Std gps
    tuple_gps = ()
    if dict_station['lat'] != u'na':
      tuple_gps = (dict_station['lat'], dict_station['long'], dict_station['score'])
    # Std address
    tuple_address = ()
    if dict_station['rue'] and dict_station['commune']:
      tuple_address = (dict_station['rue'], dict_station['commune'])
    dict_station_std = {'name' : dict_station['nom'],
                        'highway' : dict_station['autoroute'],
                        'services' : list_station_services,
                        'gps' : tuple_gps,
                        'address' : tuple_address}
    dict_dict_stations[dict_station['id_station']] = dict_station_std
  return dict_dict_stations

def format_gouv_stations_201200(list_dict_stations):
  dict_dict_stations = {}
  for dict_station in list_dict_stations:
    # Std list of services
    list_station_services = []
    for i in range(1, 21):
      if dict_station['ser%s' %i] == '1':
        list_station_services.append(list_services[i-1])
    # Std gps (leaves away most google result info... that could be useful)
    try:
      tuple_gps =  (dict_station['geolocalisation']['results'][0]['geometry']['location']['lat'],
                    dict_station['geolocalisation']['results'][0]['geometry']['location']['lng'],
                    dict_station['geolocalisation']['results'][0]['geometry']['location_type'])
    except:
      tuple_gps = ()
    # Std address
    tuple_address = ()
    if dict_station['rue'] and dict_station['commune']:
      tuple_address = (dict_station['rue'], dict_station['commune'])
    dict_station_std = {'name' : dict_station['nom'],
                         'highway' : dict_station['autoroute'],
                         'services' : list_station_services,
                         'gps' : tuple_gps,
                         'address' : tuple_address}
    dict_dict_stations[dict_station['id_station']] = dict_station_std
  return dict_dict_stations

def format_gouv_stations_201203(dict_dict_stations_raw):
  """ 
  address in one string incl. station name so can't be exploited 
  highway not included
  gps not included
  """
  dict_dict_stations_std = {}
  for id, dict_station in dict_dict_stations_raw.iteritems():
    # Std list of services
    list_station_services = []
    for i in range(20):
      if dict_station['services'][i] == 1:
        list_station_services.append(list_services[i])
    # Std opening hours and closed days
    separation_string = 'Jour(s) de Fermeture :'
    separation = dict_station['horaire'].find(separation_string)
    if separation > - 1:
      hours = dict_station['horaire'][:separation].strip()
      closed_days = dict_station['horaire'][separation + len(separation_string):].strip()
    else:
      hours = dict_station['horaire'].strip()
      closed_days = None
    # Std address: can't be exploited due to station name in string (or use other files...)
    tuple_address = ()
    dict_station_std = {'services' : list_station_services,
                        'hours' : hours,
                        'closed_days': closed_days,
                        'address' : tuple_address}
    dict_dict_stations_std[id] = dict_station_std
  return dict_dict_stations_std

def format_gouv_stations_201209(dict_dict_stations_raw):
  """
  address: 2nd component is street, 3d is zip and city name
  highway not included
  gps not included
  """
  dict_dict_stations_std = {}
  for id, dict_station in dict_dict_stations_raw.iteritems():
    # Std list of services
    list_station_services = []
    for i in range(20):
      if dict_station['services'][i] == 1:
        list_station_services.append(list_services[i])
    # Std opening hours and closed days
    separation_string = 'Jour(s) de Fermeture :'
    separation = dict_station['horaire'].find(separation_string)
    if separation > - 1:
      hours = dict_station['horaire'][:separation].strip()
      closed_days = dict_station['horaire'][separation + len(separation_string):].strip()
    else:
      hours = dict_station['horaire'].strip()
      closed_days = None
    # Std address
    tuple_address = ()
    if dict_station['adresse']:
      tuple_address = (dict_station['adresse'][2], dict_station['adresse'][3])
    dict_station_std = {'gas_types' : dict_station['carburants'],
                        'highway' : dict_station['autoroute'],
                        'services' : list_station_services,
                        'hours' : hours,
                        'closed_days': closed_days,
                        'address' : tuple_address}
    dict_dict_stations_std[id] = dict_station_std
  return dict_dict_stations_std

def format_gouv_stations_201300(dict_dict_stations_raw):
  """
  address: 2nd component is street, 3d is zip and city name
  highway not included
  gps not included
  """
  dict_dict_stations_std = {}
  for id_gouv, dict_station in dict_dict_stations_raw.iteritems():
    # Std opening hours and closed days
    hours = None
    if dict_station['hours']:
      hours = dict_station['hours'][1]
    closed_days = None
    if dict_station['closed_days']:
      if len(dict_station['closed_days']) == 2:
        closed_days = dict_station['closed_days'][1]
      else:
        print id_gouv, dict_station['closed_days']
    # Std address
    tuple_address = ()
    if dict_station['address']:
      if len(dict_station['address']) == 2:
        tuple_address = (dict_station['address'][0], dict_station['address'][1])
      elif len(dict_station['address']) == 1:
        if re.match(u'[0-9]{4,5}', dict_station['address'][0]):
          tuple_address = (u'', dict_station['address'][0])
        else:
          tuple_address = None
        print u'Len address 1:', id_gouv, dict_station['address'], tuple_address
      else:
        tuple_address = None
        print u'Len address > 2:', id_gouv, dict_station['address']
    dict_station_std = {'name' : dict_station['name'],
                        'services': dict_station['services'],
                        'hours' : hours,
                        'closed_days' : closed_days,
                        'address' : tuple_address}
    dict_dict_stations_std[id_gouv] = dict_station_std
  return dict_dict_stations_std

def build_master_info(master_by_period, list_field_keys):
  """
  Build a dict (key = id) of dicts (keys = fields/information content)
  In a field: list with info per period, None if no info (position=period)
  """
  list_ids = []
  for period_dict in master_by_period:
    list_ids +=  period_dict.keys()
  list_ids = list(set(list_ids))
  master_by_id = {}
  for id in list_ids:
    dict_id = dict(zip(list_field_keys, [[] for i in range(0,len(list_field_keys))]))
    for period_dict in master_by_period:
      for field_key in list_field_keys:
        if period_dict.get(id) is not None:
          dict_id[field_key].append(period_dict[id].get(field_key))
        else:
          dict_id[field_key].append(None)
    master_by_id[id] = dict_id
  return master_by_id

def get_dict_stat(list_items):
  dict_stats = {}
  for item in list_items:
    if item in dict_stats.keys():
      dict_stats[item] += 1
    else:
      dict_stats[item] = 1
  return dict_stats

if __name__=="__main__":
  
  # path_data: default to CREST location, else try home location
  path_data = os.path.join(u'W:\\', u'Bureau', u'Etienne_work', u'Data')
  if not os.path.exists(path_data):
    path_data = os.path.join(u'C:\\', u'Users', u'etna', u'Desktop',
                             u'Etienne_work', u'Data')

  path_dir_raw_gouv_stations = os.path.join(path_data,
                                            'data_gasoline',
                                            'data_raw',
                                            'data_stations',
                                            'data_gouv_stations')

  path_dir_source_gouv_stations = os.path.join(path_data,
                                               'data_gasoline',
                                               'data_source',
                                               'data_stations',
                                               'data_gouv_stations')

  ls_format_functions = [format_gouv_stations_201111,
                         format_gouv_stations_201200,
                         format_gouv_stations_201203,
                         format_gouv_stations_201209,
                         format_gouv_stations_201300,
                         format_gouv_stations_201300,
                         format_gouv_stations_201300,
                         format_gouv_stations_201300,
                         format_gouv_stations_201300]
  
  ls_file_names = [u'20111121_gouv_stations.json',
                   u'20120000_gouv_stations.json',
                   u'20120314_gouv_stations.json',
                   u'20120902_gouv_stations.json',
                   u'20130220_gouv_stations.json',
                   u'20130707_gouv_stations.json',
                   u'20131115_gouv_stations.json',
                   u'20140128_gouv_stations.json',
                   u'20141206_gouv_stations.json']
  
  # TODO: create new formatting function for 20131115 and 20140128
  # T0D0: collect highway data (or check if available...)
  
  ls_path_files_raw = [os.path.join(path_dir_raw_gouv_stations,
                                    file_name) for file_name in ls_file_names]
  ls_path_files_source = [os.path.join(path_dir_source_gouv_stations,
                                       file_name) for file_name in ls_file_names]

  ls_for_loop = zip(ls_path_files_raw, ls_format_functions, ls_path_files_source)
  ls_raw_files, ls_std_files = [], []
  for (path_in, format_function, path_out) in ls_for_loop:
    print 'Reading and formatting:', path_in
    raw_file = dec_json(path_in)
    std_file = format_function(raw_file)
    ls_raw_files.append(raw_file)
    ls_std_files.append(std_file)
    enc_json(std_file, path_out)
  
  # BUILD master_info AND EXPLORE ADDRESSES (FIELDS)
  
  ls_info_keys = ['name',
                  'address', 
                  'services', 
                  'hours', 
                  'closed_days', 
                  'highway', 
                  'gps', 
                  'gas_types']
  
  master_info = build_master_info(ls_std_files, ls_info_keys)
  
  # 3d raw address: starts with station name hence dropped
  # 3d raw address: lower case, structure: Name / Brand(old) / Street / Zip and City
  # 4th raw address: upper case, structure: Street / Zip and City
  
  # Check that taking subset of periods allows to cover (virtually) all stations
  print u'\nStation addresses not covered by chosen subset of periods:'
  ls_period_subset = [0, 3, 4, 5, 6, 7, 8]
  for id, station in master_info.iteritems():
    if all(not station['address'][i] for i in ls_period_subset):
      print id, 'address info', master_info[id]['address']

  # Check that addresses do not change much between periods (with simple corrections)
  ls_multi_streets = []
  ls_multi_cities = []
  for id_gouv, station in master_info.items():
    ls_std_streets = []
    ls_std_cities = []
    for i in ls_period_subset:
      if station['address'][i]:
        std_street = str_corr_low_std_noacc(station['address'][i][0], False)
        if std_street not in ls_std_streets:
          ls_std_streets.append(std_street)
        std_city = str_corr_low_std_noacc(station['address'][i][1], False)
        if std_city not in ls_std_cities:
          ls_std_cities.append(std_city)
    if len(ls_std_streets) > 1:
      ls_multi_streets.append((id_gouv, ls_std_streets))
    if len(ls_std_cities) > 1:
      ls_multi_cities.append((id_gouv, ls_std_cities))

  # Aggregation of corrected addresses (light fix, not standardization)
  dict_cor_addresses_test = {}
  for id_gouv, station in master_info.items():
    ls_addresses = []
    for period_index in ls_period_subset[::-1]:
      if station['address'][period_index]:
        cor_address = tuple(map(str_corr_low_std, station['address'][period_index]))
        if cor_address not in ls_addresses:
          ls_addresses.append(cor_address)
    dict_cor_addresses_test[id_gouv] = ls_addresses

  # Compare standardized and keep the best if duplicated
  # (here: this which needed more standardization)
  # Could check if difference is not merely the presence of street number
  # Coul use levenshtein stat to evaluate interest of keeping several addresses
  dict_addresses = {}
  for id_gouv, ls_addresses in dict_cor_addresses_test.iteritems():
    if len(ls_addresses) > 1:
      ls_unique_addresses = []
      ls_unique_score = []
      ls_positions_to_keep = []
      ls_std_adresses = [map(str_corr_low_std_noacc, address) for address\
                           in ls_addresses]
      ls_std_adresses = [((stre[0], city[0]), stre[1] + city[1]) for stre, city\
                           in ls_std_adresses]
      for ind, (address, score) in enumerate(ls_std_adresses):
        if address[0] not in ls_unique_addresses:
          ls_unique_addresses.append(address[0])
          ls_unique_score.append(score)
          ls_positions_to_keep.append(ind)
        else:
          ind_other = ls_unique_addresses.index(ls_unique_addresses[0])
          score_other = ls_unique_score[ind_other]
          if score > score_other:
            ls_unique_score[ind_other] = score
            ls_positions_to_keep[ind_other] = ind
      ls_addresses_to_keep = [ls_addresses[i] for i in ls_positions_to_keep]
    else:
      ls_addresses_to_keep = ls_addresses
    dict_addresses[id_gouv] = ls_addresses_to_keep

  # Stats des
  dict_adr_stats = {}
  for id_gouv, ls_addresses in dict_addresses.items():
    dict_adr_stats.setdefault(len(ls_addresses), []).append(id_gouv)
  
  print u'\nNb of stations by nb of addresses:'
  for k, v in dict_adr_stats.items():
    print k, len(v)
  
  print '\nInspect: 3 stdized addresses'
  for id_gouv in dict_adr_stats[3]:
    print u'\n', id_gouv
    pprint.pprint(master_info[id_gouv]['address'])
  
  #print '\nInspect: 2 stdized addresses'
  #for id_gouv in dict_adr_stats[2]:
  #  print u'\n', id_gouv
  #  pprint.pprint(master_info[id_gouv]['address'])
  
  # Build dict_zip
  dict_zip_codes = {}
  for id_gouv, ls_addresses in dict_addresses.items():
    if ls_addresses:
      ls_id_streets = [id_gouv]
      for address in ls_addresses:
        zip_and_city = re.match('([0-9]{5,5}) (.*)', address[1])
        zip_code = zip_and_city.group(1)
        ls_id_streets.append(address[0])
      dict_zip_codes.setdefault(zip_code, []).append(ls_id_streets)

  # Build dict_dpt_city
  dict_dpt_codes = {}
  for id_gouv, ls_addresses in dict_addresses.items():
    if ls_addresses:
      ls_id_streets = [id]
      for address in ls_addresses:
        zip_and_city = re.match('([0-9]{5,5}) (.*)', address[1])
        zip_code = zip_and_city.group(1)
        dpt_code = zip_and_city.group(1)[:2]
        city = zip_and_city.group(2)
        ls_id_streets.append((zip_code, city, address[0]))
      dict_dpt_codes.setdefault(dpt_code, []).append(ls_id_streets)
