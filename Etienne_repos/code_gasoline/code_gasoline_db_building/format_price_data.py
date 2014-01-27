#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import itertools
from datetime import date, timedelta
import datetime
import time
import re

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:/Bureau/Etienne_work/Data'):
  path_data = r'W:/Bureau/Etienne_work/Data'
else:
  path_data = r'C:/Users/etna/Desktop/Etienne_work/Data'
# structure of the data folder should be the same
folder_source_prices = r'/data_gasoline/data_source/data_json_prices'

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def loop_and_format(format_function, folder_source, folder_ouput, files_extension_output):
  # TODO: add overwrite option to allow not to overwrite file if it exists in output folder
  for file_name in os.listdir(folder_source):
    if re.match('[0-9]{8}[^0-9]', file_name):
      formatted_file = format_function(folder_source + r'/' + file_name)
      enc_stock_json(formatted_file, folder_ouput + r'/%s' %file_name[:8] + files_extension_output)

# ###############################
# DIESEL (LEADED IS NOT PROPER)
# ###############################

def format_price_201109_201205_diesel(path_file, output_list = True):
  # Difficulty dealt with: txt files were generated as CSV but some fields can contain commas
  list_keys = ['id_station', 'commune', 'nom_station','marque', 'prix', 'date']
  input_file = codecs.open(path_file, 'rb', 'utf-8')
  data = input_file.read()
  list_rows = [row for row in data.split('\r\n') if row]
  list_ids = []
  list_stations = []
  for row in list_rows:
    re_1 = re.search(ur",\s[0-9],[0-9]{2,3}|,\s--", row)
    if re_1 is not None:
      split_point = re_1.start()
      # gas station information part
      gas_station_info = row[:split_point].split(',')
      id = gas_station_info[0]
      city_station = gas_station_info[1]
      name_station = u' '.join(gas_station_info[2:-1])
      brand_station = gas_station_info[-1]
      # gas station price date part
      price_and_date = re.findall(ur",\s([0-9],[0-9]{2,3}|--|[0-9]{2}/[0-9]{2}/[0-9]{2})", row)
      if len(price_and_date) == 2:
        price = price_and_date[0]
        date = price_and_date[1]
        station = (id.lstrip(u'pdv'), city_station, name_station, brand_station, price, date)
        if station[0] not in list_ids:
          if output_list:
            list_stations.append(station)
          else:
            list_stations.append(dict(zip(list_keys, station)))
          list_ids.append(station[0])
        """
        else:
          print 'duplicate', row
        """
      else:
        print 'pbm with regex 2', row
    else:
      print 'pbm with regex 1', row
  return list_stations

def format_price_201205_201205_diesel(path_file, output_list = True):
  # dict of dicts => list of tuples (or dicts)
  # diesel and gas are contained in same dict.. hence not all stations have diesel
  # same format/function over 201209_201212
  list_keys = ['id_station', 'commune', 'nom_station','marque', 'prix', 'date']
  data = dec_json(path_file)
  list_observations = []
  list_id_observations = []
  for id_observation, observation in data.iteritems():
    if id_observation not in list_id_observations and 'diesel_price_station' in observation.keys():
      station = ( id_observation.lstrip(u'pdv'),\
                  observation['city_station'],\
                  observation['name_station'],\
                  observation['brand_station'],\
                  observation['diesel_price_station'],\
                  observation['diesel_date_station'] )
      if output_list:
        list_observations.append(station)
      else:
        list_observations.append(dict(zip(list_keys, station)))
      list_id_observations.append(id_observation)
  return list_observations

def format_price_201301_201306_diesel(path_file, output_list = True):
  # does essentially nothing (list of lists => list of tuples (or dicts))
  list_keys = ['id_station', 'commune', 'nom_station', 'marque', 'prix', 'date']
  data = dec_json(path_file)
  list_observations = []
  list_id_observations = []
  for index_observation, observation in enumerate(data):
    if observation[0] not in list_id_observations:
      station = [observation[0].lstrip(u'pdv')] + observation[1:]
      if output_list:
        list_observations.append(tuple(station))
      else:
        list_observations.append(dict(zip(list_keys, station)))
      list_id_observations.append(observation[0])
  return list_observations

list_functions_diesel = [format_price_201109_201205_diesel,
                         format_price_201205_201205_diesel,
                         format_price_201205_201205_diesel,
                         format_price_201301_201306_diesel]
  
folders_source_period_prices_diesel = [r'/20110904_20120514_lea',
                                       r'/20120515_20120521_two',
                                       r'/20120522_20121203_two',
                                       r'/20130121_20130604_lea']

files_source_day_prices_diesel = [r'/20110904ga.txt',
                                  r'/20120515_gas_prices',
                                  r'/20120522_gas_prices',
                                  r'/20130122_diesel_gas_prices']

list_paths_folder_prices_diesel = list(itertools.product([path_data + folder_source_prices],
                                                         folders_source_period_prices_diesel))
list_paths_folder_prices_diesel = [''.join(path) for path in list_paths_folder_prices_diesel]

list_path_files_prices_diesel = zip(list_paths_folder_prices_diesel, files_source_day_prices_diesel)
list_path_files_prices_diesel = [''.join(path) for path in list_path_files_prices_diesel]

#test of each format function
list_to_iterate_diesel_files = zip(list_functions_diesel, list_path_files_prices_diesel)
master_test_diesel_files = []
for (function_format, path_file) in list_to_iterate_diesel_files:
  master_test_diesel_files.append(function_format(path_file))

# execution

folders_clean_period_prices_diesel = r'/clean_prices_diesel'
folder_ouput_diesel = path_data + folder_source_prices + r'/diesel_standardized_tuple_lists'

list_to_iterate_diesel_folders = zip(list_functions_diesel, list_paths_folder_prices_diesel)
for (function_format, path_folder) in list_to_iterate_diesel_folders:
  loop_and_format(function_format, path_folder, folder_ouput_diesel, '_diesel')

  
# DEPRECATED ?
# loop_and_format(format_price_201109_201205_diesel, path_diesel_201109_201205, folder_ouput_diesel, '_diesel')
# loop_and_format(format_price_201205_201205_diesel, path_diesel_201205_201205, folder_ouput_diesel, '_diesel')
# loop_and_format(format_price_201205_201205_diesel, path_diesel_201205_201212, folder_ouput_diesel, '_diesel')
# loop_and_format(format_price_201301_201306_diesel, path_diesel_201301_201306, folder_ouput_diesel, '_diesel')

# ###########################
# GAS (LEADED IS NOT PRECISE)
# ###########################

def format_price_201109_201205_gas(path_file, output_list = True):
  # Difficulty dealt with: txt files were generated as CSV but some fields can contain commas
  # function switches sp95 and e10 price/date positions to ensure forward consistency
  list_keys = ['id_station', 'commune', 'nom_station', 'marque',\
                'prix_sp95', 'date_sp95', 'prix_e10', 'date_e10',]
  input_file = codecs.open(path_file, 'rb', 'utf-8')
  data = input_file.read()
  list_rows = [row for row in data.split('\r\n') if row]
  list_ids = []
  list_stations = []
  for row in list_rows:
    re_1 = re.search(ur",\s[0-9],[0-9]{2,3}|,\s--", row)
    if re_1 is not None:
      split_point = re_1.start()
      # gas station information part
      gas_station_info = row[:split_point].split(',')
      id = gas_station_info[0]
      city_station = gas_station_info[1]
      name_station = u' '.join(gas_station_info[2:-1])
      brand_station = gas_station_info[-1]
      # gas station price date part
      price_and_date = re.findall(ur",\s([0-9],[0-9]{2,3}|--|[0-9]{2}/[0-9]{2}/[0-9]{2})", row)
      if len(price_and_date) == 4:
        price_1 = price_and_date[0]
        date_1 = price_and_date[1]
        price_2 = price_and_date[2]
        date_2 = price_and_date[3]
        station = (id.lstrip(u'pdv'),\
                   city_station,\
                   name_station,\
                   brand_station,\
                    price_2,\
                    date_2,\
                    price_1,\
                    date_1)
        if station[0] not in list_ids:
          if output_list:
            list_stations.append(station)
          else:
            list_stations.append(dict(zip(list_keys, station)))
          list_ids.append(station[0])
        """
        else:
          print 'duplicate', row
        """
      else:
        print 'pbm with regex 2', row
    else:
      print 'pbm with regex 1', row
  return list_stations

def format_price_201205_201205_gas(path_file, output_list = True):
  # dict of dicts => list of tuples (or dicts)
  # diesel and gas are contained in same dict.. hence not all stations have diesel
  list_keys = ['id_station', 'commune', 'nom_station','marque',\
               'prix_sp95', 'date_sp95', 'prix_e10', 'date_e10']
  data = dec_json(path_file)
  list_observations = []
  list_id_observations = []
  for id_observation, observation in data.iteritems():
    if id_observation not in list_id_observations and 'e10_price_station' in observation.keys():
      station = ( id_observation.lstrip(u'pdv'),\
                  observation['city_station'],\
                  observation['name_station'],\
                  observation['brand_station'],\
                  observation['sp95_price_station'],\
                  observation['sp95_date_station'],\
                  observation['e10_price_station'],\
                  observation['e10_date_station'] )
      if output_list:
        list_observations.append(station)
      else:
        list_observations.append(dict(zip(list_keys, station)))
      list_id_observations.append(id_observation)
  return list_observations

def format_price_201205_201212_gas(path_file, output_list = True):
  # dict of dicts => list of tuples (or dicts)
  # diesel and gas are contained in same dict.. hence not all stations have diesel
  # CAUTION: e10 and sp95 were switched => function switches back
  list_keys = ['id_station', 'commune', 'nom_station','marque',\
               'prix_sp95', 'date_sp95', 'prix_e10', 'date_e10']
  data = dec_json(path_file)
  list_observations = []
  list_id_observations = []
  for id_observation, observation in data.iteritems():
    if id_observation not in list_id_observations and 'e10_price_station' in observation.keys():
      station = ( id_observation.lstrip(u'pdv'),\
                  observation['city_station'],\
                  observation['name_station'],\
                  observation['brand_station'],\
                  observation['e10_price_station'],\
                  observation['e10_date_station'],\
                  observation['sp95_price_station'],\
                  observation['sp95_date_station'] )
      if output_list:
        list_observations.append(station)
      else:
        list_observations.append(dict(zip(list_keys, station)))
      list_id_observations.append(id_observation)
  return list_observations

def format_price_201301_201306_gas(path_file, output_list = True):
  # does essentially nothing (list of lists => list of tuples (or dicts))
  list_keys = ['id_station', 'commune', 'nom_station','marque',\
               'prix_sp95', 'date_sp95', 'prix_e10', 'date_e10']
  data = dec_json(path_file)
  list_observations = []
  list_id_observations = []
  for index_observation, observation in enumerate(data):
    if observation[0] not in list_id_observations:
      station = [observation[0].lstrip(u'pdv')] + observation[1:]
      if output_list:
        list_observations.append(tuple(station))
      else:
        list_observations.append(dict(zip(list_keys, station)))
      list_id_observations.append(observation[0])
  return list_observations

list_functions_gas = [format_price_201109_201205_gas,
                      format_price_201205_201205_gas,
                      format_price_201205_201212_gas,
                      format_price_201301_201306_gas]

folders_source_period_prices_gas = [r'/20110903_20120514_unl',
                                    r'/20120515_20120521_two',
                                    r'/20120522_20121203_two',
                                    r'/20130121_20130604_unl']

files_source_day_prices_gas = [r'/20110904sp.txt',
                               r'/20120515_gas_prices',
                               r'/20120522_gas_prices',
                               r'/20130121_essence_gas_prices']

list_paths_folder_prices_gas = list(itertools.product([path_data + folder_source_prices],
                                                       folders_source_period_prices_gas))
list_paths_folder_prices_gas = [''.join(path) for path in list_paths_folder_prices_gas]

list_path_files_prices_gas = zip(list_paths_folder_prices_gas, files_source_day_prices_gas)
list_path_files_prices_gas = [''.join(path) for path in list_path_files_prices_gas]

#test of each format function
list_to_iterate_gas_files = zip(list_functions_gas, list_path_files_prices_gas)
master_test_gas_files = []
for (function_format, path_file) in list_to_iterate_gas_files:
  master_test_gas_files.append(function_format(path_file))

# execution

folders_clean_period_prices_gas = r'/clean_prices_gas'
folder_ouput_gas = path_data + folder_source_prices + r'/gas_standardized_tuple_lists'

list_to_iterate_gas_folders = zip(list_functions_gas, list_paths_folder_prices_gas)
for (function_format, path_folder) in list_to_iterate_gas_folders:
  loop_and_format(function_format, path_folder, folder_ouput_gas, '_gas')

# DEPRECATED ?
# loop_and_format(format_price_201109_201205_gas, path_gas_201109_201205, folder_ouput_gas, '_gas')
# loop_and_format(format_price_201205_201205_gas, path_gas_201205_201205, folder_ouput_gas, '_gas')
# loop_and_format(format_price_201205_201212_gas, path_gas_201205_201212, folder_ouput_gas, '_gas')
# loop_and_format(format_price_201301_201306_gas, path_gas_201301_201306, folder_ouput_gas, '_gas')

"""
# POSITIONS OF E10 AND SP95 IN LISTS? (DEALT WITH)

def count_gas_prices(list_indivs):
  # to make sure to righly attribute prices to sp95 / e10
  # works with list of dics
  count_e10 = 0
  count_sp95 = 0
  for index_indiv, tuple_indiv in enumerate(list_indivs):
    if tuple_indiv[4] != '--' and tuple_indiv[4] != ' --':
      count_sp95 += 1
    if tuple_indiv[6] != '--' and tuple_indiv[6] != ' --':
      count_e10 += 1
  return {'nb_prices_sp95' : count_sp95, 'nb_prices_e10' : count_e10}

def temp_gas_loop_and_format(format_function, folder_source, folder_ouput, files_extension_output):
  for file_name in os.listdir(folder_source):
    if re.match('[0-9]{8}[^0-9]', file_name):
      formatted_file = format_function(folder_source + r'/' + file_name)
      print file_name[:8], count_gas_prices(formatted_file)

temp_gas_loop_and_format(format_price_201109_201205_gas, path_gas_201109_201205, folder_ouput_gas, '_gas')
temp_gas_loop_and_format(format_price_201205_201205_gas, path_gas_201205_201205, folder_ouput_gas, '_gas')
temp_gas_loop_and_format(format_price_201205_201212_gas, path_gas_201205_201212, folder_ouput_gas, '_gas')
temp_gas_loop_and_format(format_price_201301_201306_gas, path_gas_201301_201306, folder_ouput_gas, '_gas')
"""