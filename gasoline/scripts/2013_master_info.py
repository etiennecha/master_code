# -*- coding: cp1252 -*-

import json
import os, sys, codecs

machine_path = r'C:\Users\etna\Desktop\Code\Gasoline'
raw_data_folder = r'data_stations\data_info_stations_prix_carb'
gps_coordinates_folder = r'data_stations\data_stations_coordinates'

raw_data_files = [r'20111121_db_chars',
                  r'20120000_jsondb_competition',
                  r'20120314_master_adr_servs',
                  r'20120902_master_adr_servs',
                  r'20130220_diesel_info_stations']

list_services = [u'Automate CB',
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

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def format_info_stations_1(master_list_stations):
  master_final_dict_stations = {}
  for dict_station in master_list_stations:
    dict_station['ser19'] = dict_station['ser 19']
    list_station_services = []
    for i in range(1,21):
      if dict_station['ser%s' %i] == '1':
        list_station_services.append(list_services[i-1])
    # Standardize gps info
    if dict_station['lat'] != u'na':
      gps = [dict_station['lat'], dict_station['long'], dict_station['score']]
    else:
      gps = None
    new_dict_stations = {'name' : dict_station['nom'],
                         'address' : {'street': dict_station['rue'],
                                      'city' : dict_station['commune']},
                         'highway' : dict_station['autoroute'],
                         'services' : list_station_services,
                         'gps' : gps}
    master_final_dict_stations[dict_station['id_station']] = new_dict_stations
  return master_final_dict_stations

def format_info_stations_2(master_list_stations):
  master_final_dict_stations = {}
  for dict_station in master_list_stations:
    list_station_services = []
    for i in range(1,21):
      if dict_station['ser%s' %i] == '1':
        list_station_services.append(list_services[i-1])
    # Standardize gps info (left away most google result info... that could be useful)
    try:
      gps = [dict_station['geolocalisation']['results'][0]['geometry']['location']['lat'],
             dict_station['geolocalisation']['results'][0]['geometry']['location']['lng'],
             dict_station['geolocalisation']['results'][0]['geometry']['location_type']]
    except:
      gps = None
    new_dict_stations = {'name' : dict_station['nom'],
                         'address' : {'street': dict_station['rue'],
                                      'city' : dict_station['commune']},
                         'highway' : dict_station['autoroute'],
                         'services' : list_station_services,
                         'gps' : gps}
    master_final_dict_stations[dict_station['id_station']] = new_dict_stations
  return master_final_dict_stations

def format_info_stations_3(master_dict_stations):
  # Third file: address in one string so can't be exploited (includes station name)
  master_final_dict_stations = {}
  for id, dict_station in master_dict_stations.iteritems():
    # Reformat list of services (always same order)
    list_station_services = []
    for i in range(0,20):
      if dict_station['services'][i] == 1:
        list_station_services.append(list_services[i])
    # Distinguish opening hours and closed days
    separation_string = 'Jour(s) de Fermeture :'
    separation = dict_station['horaire'].find(separation_string)
    if separation > - 1:
      hours = dict_station['horaire'][:separation].strip()
      closed_days = dict_station['horaire'][separation + len(separation_string):].strip()
    else:
      hours = dict_station['horaire'].strip()
      closed_days = None
    new_dict_stations = {'address' : dict_station['adresse'],
                         'services' : list_station_services,
                         'hours' : hours,
                         'closed_days': closed_days}
    master_final_dict_stations[id] = new_dict_stations
  return master_final_dict_stations

def format_info_stations_4(master_dict_stations):
  # Fourth file: a priori order of adresse is correct so that 3 is street and 4 is city (check that)
  master_final_dict_stations = {}
  for id, dict_station in master_dict_stations.iteritems():
    # Reformat list of services (always same order)
    list_station_services = []
    for i in range(0,20):
      if dict_station['services'][i] == 1:
        list_station_services.append(list_services[i])
    # Distinguish opening hours and closed days
    separation_string = 'Jour(s) de Fermeture :'
    separation = dict_station['horaire'].find(separation_string)
    if separation > - 1:
      hours = dict_station['horaire'][:separation].strip()
      closed_days = dict_station['horaire'][separation + len(separation_string):].strip()
    else:
      hours = dict_station['horaire'].strip()
      closed_days = None
    new_dict_stations = {'address' : dict_station['adresse'],
                         'services' : list_station_services,
                         'highway' : dict_station['autoroute'],
                         'hours' : hours,
                         'closed_days': closed_days,
                         'gas_types' : dict_station['carburants']}
    master_final_dict_stations[id] = new_dict_stations
  return master_final_dict_stations

def format_info_stations_5(master_dict_stations):
  # Looks like name[1] is brand (and thus useless)
  master_final_dict_stations = {}
  for id, dict_station in master_dict_stations.iteritems():
    if dict_station['hours'] is not None:
      dict_station['hours'] = dict_station['hours'][1]
    if dict_station['closed_days'] is not None:
      dict_station['closed_days'] = dict_station['closed_days'][1]
    new_dict_stations = {'name' : dict_station['name'],
                         'address' : dict_station['address'],
                         'closed_days' : dict_station['closed_days'],
                         'services': dict_station['services'],
                         'hours' : dict_station['hours']}
    master_final_dict_stations[id] = new_dict_stations
  return master_final_dict_stations

def unique(items):
  """
  keep only unique elements in a list
  """
  found = set()
  keep = []
  for item in items:
    if item not in found:
      found.add(item)
      keep.append(item)
  return keep

def build_master_by_id(master_by_period, list_field_keys):
  """
  Build a dict (key = id) of dicts (keys = fields/information content)
  In a field: list with info per period, None if no info (position=period)
  """
  list_ids = []
  for period_dict in master_by_period:
    list_ids +=  period_dict.keys()
  list_ids = unique(list_ids)
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

def get_occurences_by_period(master_dicts, field):
  """
  Lists all possible occurences by period for a given field
  assumes that each field period list has the same length (None if nuffin)
  """
  period_occurences_lists = [{} for i in range(0,len(master_dicts[master_dicts.keys()[0]][field]))]
  period_none_list = [0 for i in range(0,len(master_dicts[master_dicts.keys()[0]][field]))]
  for id, info in master_dicts.iteritems():
    for i in range(0,len(info[field])):
      if info[field][i] is not None:
        if ''.join(info[field][i]) not in period_occurences_lists[i]:
          period_occurences_lists[i][''.join(info[field][i])] = 1
        else:
          period_occurences_lists[i][''.join(info[field][i])] += 1
      else:
        period_none_list[i] += 1
  print 'None number at each period', period_none_list, 'for', field
  return period_occurences_lists

def sum_dict(some_dict):
  sum = 0
  for k,v in some_dict.iteritems():
    sum += v
  return sum

def get_differences_in_length_by_period(master_dicts, field, period_i, period_j):
  """
  Checks differences (in length, by period) in info reported by stations for a given field:
  """
  nb_differences = 0
  for id, info in master_dicts.iteritems():
    if info[field][period_i] is not None and info[field][period_j] is not None:
      if (info[field][period_i] is not None and info[field][period_j] is None) or \
         (info[field][period_i] is None and info[field][period_j] is None) or \
         (set(info[field][period_i]) != set(info['services'][period_j])):
        nb_differences += 1
  print i,j, nb_differences

def format_gps_coordinates(gps_lea):
  master_gps_coordinates = {}
  for i in range(0,len(gps_lea)):
    if len(gps_lea[i].split('||')) == 3:
      master_gps_coordinates[gps_lea[i].split('||')[0]] = [float(gps_lea[i].split('||')[2])/100000, float(gps_lea[i].split('||')[1])/100000]
  return master_gps_coordinates

raw_data_info = []
for file in raw_data_files:
  raw_data_info.append(dec_json('%s\%s\%s' %(machine_path, raw_data_folder, file)))
master_info_1 = format_info_stations_1(raw_data_info[0])
master_info_2 = format_info_stations_2(raw_data_info[1])
master_info_3 = format_info_stations_3(raw_data_info[2])
master_info_4 = format_info_stations_4(raw_data_info[3])
master_info_5 = format_info_stations_5(raw_data_info[4])
master_dicts_stations = [master_info_1, master_info_2, master_info_3, master_info_4, master_info_5]
list_station_keys = ['name', 'address', 'services', 'hours', 'closed_days', 'highway', 'gps', 'gas_types']
master_gas_stations = build_master_by_id(master_dicts_stations, list_station_keys)

for i in range(0, 4):
  for j in range(i+1, 5):
    get_differences_in_length_by_period(master_gas_stations, 'services', i ,j)

hours = get_occurences_by_period(master_gas_stations, 'hours')
closed_days = get_occurences_by_period(master_gas_stations, 'closed_days')
services = get_occurences_by_period(master_gas_stations, 'services')

gps_lea = dec_json(machine_path + r'\\' + gps_coordinates_folder + r'\\20130117_list_coordinates_diesel')
gps_master = format_gps_coordinates(gps_lea)
gps_unl = dec_json(machine_path + r'\\' + gps_coordinates_folder + r'\\20130117_list_coordinates_essence')
gps_unl = format_gps_coordinates(gps_unl)
gps_master.update(gps_unl)

for id, gps_coord in gps_master.iteritems():
  try:
    master_gas_stations[id]['gps'][4] = gps_coord
  except:
    print id, 'not in master (but we have gps coord)'

# enc_stock_json(master_gas_stations, machine_path + r'\\' + raw_data_folder + r'\\current_master_info')
# could drop unncessary info collected from google geocoding or at least reduce size