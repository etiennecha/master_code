#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import re
from functions_string import *

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
  for id, dict_station in dict_dict_stations_raw.iteritems():
    # Std opening hours and closed days
    hours = None
    if dict_station['hours']:
      hours = dict_station['hours'][1]
    closed_days = None
    if dict_station['closed_days']:
      closed_days = dict_station['closed_days'][1]
    # Std address
    tuple_address = ()
    if dict_station['address']:
      tuple_address = (dict_station['address'][0], dict_station['address'][1])
    dict_station_std = {'name' : dict_station['name'],
                        'services': dict_station['services'],
                        'hours' : hours,
                        'closed_days' : closed_days,
                        'address' : tuple_address}
    dict_dict_stations_std[id] = dict_station_std
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

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
# structure of the data folder should be the same
folder_built_info_stations = r'\data_gasoline\data_built\data_json_gasoline\master_diesel'
folder_source_brands = r'\data_gasoline\data_source\data_stations\data_brands'

folder_source_gouv_stations_raw = r'\data_gasoline\data_source\data_stations\data_gouv_stations\raw'
folder_source_gouv_stations_std = r'\data_gasoline\data_source\data_stations\data_gouv_stations\std'

list_format_functions = [format_gouv_stations_201111,
                         format_gouv_stations_201200,
                         format_gouv_stations_201203,
                         format_gouv_stations_201209,
                         format_gouv_stations_201300,
                         format_gouv_stations_201300]

files_source_data = [r'\20111121_gouv_stations',
                     r'\20120000_gouv_stations',
                     r'\20120314_gouv_stations',
                     r'\20120902_gouv_stations',
                     r'\20130220_gouv_stations',
                     r'\20130707_gouv_stations']

list_paths_raw = [path_data + folder_source_gouv_stations_raw + file for file in files_source_data]
list_paths_std = [path_data + folder_source_gouv_stations_std + file for file in files_source_data]

list_to_iterate = zip(list_paths_raw, list_format_functions, list_paths_std)

if __name__=="__main__":
  master_raw_files = []
  master_std_files = []
  for (path_in, format_function, path_out) in list_to_iterate:
    raw_file = dec_json(path_in)
    std_file = format_function(raw_file)
    master_raw_files.append(raw_file)
    master_std_files.append(std_file)
    enc_json(std_file, path_out)
  
  # BUILD master_info AND EXPLORE ADDRESSES (FIELDS)
  
  list_info_keys = ['name',
                    'address', 
                    'services', 
                    'hours', 
                    'closed_days', 
                    'highway', 
                    'gps', 
                    'gas_types']
  
  master_info = build_master_info(master_std_files, list_info_keys)
  master_price = dec_json(path_data + folder_built_info_stations +\
                            r'\master_price_diesel')
  
  # 3d raw address: starts with station name hence dropped
  # 3d raw address: lower case, structure: Name / Brand(old) / Street / Zip and City
  # 4th raw address: upper case, structure: Street / Zip and City
  
  # match zip/citylist_zip_codes_4 = []
  """
  zip_and_city = re.match('([0-9]{5,5}) (.*)', station['address'][1])
  if zip_and_city:
    zip_code = zip_and_city.group(1)        
    city = zip_and_city.group(2)
  """

  # Check that taking 0, 3, 4, 5 fields allows to cover (virtually) all stations
  for id, station in master_info.iteritems():
    if all(not station['address'][i] for i in (0,3,4,5)):
      print id, 'address info', master_info[id]['address']

  # Check that addresses do not change much between periods
  list_several_streets = []
  list_several_cities = []
  for id, station in master_info.iteritems():
    list_station_streets_std = []
    list_stations_cities_std = []
    for i in (0, 3, 4, 5):
      if station['address'][i]:
        street_std = str_corr_low_std_noacc(station['address'][i][0], False)
        if street_std not in list_station_streets_std:
          list_station_streets_std.append(street_std)
        city_std = str_corr_low_std_noacc(station['address'][i][1], False)
        if city_std not in list_stations_cities_std:
          list_stations_cities_std.append(city_std)
    if len(list_station_streets_std) > 1:
      list_several_streets.append((id, list_station_streets_std))
    if len(list_stations_cities_std) > 1:
      list_several_cities.append((id, list_stations_cities_std))

  # Aggregation into a new master (here: corrected, not standardized)
  master_address_test = {}
  for id, station in master_info.iteritems():
    list_station_addresses = []
    for period_index in (5, 3, 4, 0):
      if station['address'][period_index]:
        cor_address = tuple(map(str_corr_low_std, station['address'][period_index]))
        if cor_address not in list_station_addresses:
          list_station_addresses.append(cor_address)
    master_address_test[id] = list_station_addresses

  # Compare standardized and keep the best if duplicated
  # (i.e. this which needed more standardization)
  # TODO: Remains to check if difference is not merely the presence of street number
  # (order by length as approx?)
  # TODO: use levenshtein stat to evaluate interest of keeping several addresses...
  temp_multiple_addresses = []
  master_addresses_final = {}
  for id, list_station_addresses in master_address_test.iteritems():
    if len(list_station_addresses) > 1:
      list_unique_addresses = []
      list_unique_score = []
      list_positions_to_keep = []
      list_std_station_adresses = [map(str_corr_low_std_noacc, address) for address\
                                    in list_station_addresses]
      list_std_station_adresses = [((stre[0], city[0]), stre[1] + city[1]) for stre, city\
                                    in list_std_station_adresses]
      for ind, (address, score) in enumerate(list_std_station_adresses):
        if address[0] not in list_unique_addresses:
          list_unique_addresses.append(address[0])
          list_unique_score.append(score)
          list_positions_to_keep.append(ind)
        else:
          ind_other = list_unique_addresses.index(list_unique_addresses[0])
          score_other = list_unique_score[ind_other]
          if score > score_other:
            list_unique_score[ind_other] = score
            list_positions_to_keep[ind_other] = ind
      temp_multiple_addresses.append((id, list_positions_to_keep))
      final_list_station_addresses = [list_station_addresses[i] for i in list_positions_to_keep]
    else:
      final_list_station_addresses = list_station_addresses
    master_addresses_final[id] = final_list_station_addresses
  
  """
  # Control:
  for id_sta, list_indices in temp_multiple_addresses:
    print id_sta, list_indices
    print master_address_test[id_sta], '\n'
  """

  # Build dict_zip
  dict_zip_master = {}
  for id, list_addresses in master_addresses_final.iteritems():
    if list_addresses:
      list_id_streets = [id]
      for address in list_addresses:
        zip_and_city = re.match('([0-9]{5,5}) (.*)', address[1])
        zip = zip_and_city.group(1)
        list_id_streets.append(address[0])
      dict_zip_master.setdefault(zip, []).append(list_id_streets)

  # Build dict_dpt_city
  dict_dpt_master = {}
  for id, list_addresses in master_addresses_final.iteritems():
    if list_addresses:
      list_id_streets = [id]
      for address in list_addresses:
        zip_and_city = re.match('([0-9]{5,5}) (.*)', address[1])
        zip = zip_and_city.group(1)
        dpt = zip_and_city.group(1)[:2]
        city = zip_and_city.group(2)
        list_id_streets.append((zip, city, address[0]))
      dict_dpt_master.setdefault(dpt, []).append(list_id_streets)