#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import itertools
from datetime import date, timedelta
import datetime
import time
import re

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def loop_and_format(format_function, path_input_dir, path_output_dir, extension_out):
  # todo: add option to allow not to overwrite file if it exists in output folder
  for file_name in os.listdir(path_input_dir):
    if re.match('[0-9]{8}[^0-9]', file_name):
      formatted_file = format_function(os.path.join(path_input_dir, file_name))
      enc_json(formatted_file, os.path.join(path_output_dir,
                                            file_name[:8] + extension_out))

# DIESEL

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
    if (id_observation not in list_id_observations) and\
       ('diesel_price_station' in observation.keys()):
      station = (id_observation.lstrip(u'pdv'),
                 observation['city_station'],
                 observation['name_station'],
                 observation['brand_station'],
                 observation['diesel_price_station'],
                 observation['diesel_date_station'])
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

# GAS

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


if __name__=="__main__":
  
  # path_data: default to CREST location, else try home location
  path_data = os.path.join(u'W:\\', u'Bureau', u'Etienne_work', u'Data')
  if not os.path.exists(path_data):
    path_data = os.path.join(u'C:\\', u'Users', u'etna', u'Desktop',
                             u'Etienne_work', u'Data')
  
  path_raw_prices = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_raw',
                                 u'data_prices')
  
  
  # actually source is the destination (raw is the origin)
  path_source_prices = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_source',
                                    u'data_prices')
  
  # #######
  # DIESEL
  # #######

  ls_diesel_functions = [format_price_201109_201205_diesel,
                         format_price_201205_201205_diesel,
                         format_price_201205_201205_diesel,
                         format_price_201301_201306_diesel]
  
  ls_raw_diesel_dirs = [u'20110904_20120514_lea',
                        u'20120515_20120521_two',
                        u'20120522_20121203_two',
                        u'20130121_20130604_lea']
  
  # Test each format function with one file of each type
  ls_raw_diesel_files = [u'20110904ga.txt',
                         u'20120515_gas_prices',
                         u'20120522_gas_prices',
                         u'20130122_diesel_gas_prices']
  ls_raw_diesel_file_paths = [os.path.join(path_raw_prices, raw_diesel_dir, raw_diesel_file)\
                                for (raw_diesel_dir, raw_diesel_file)
                                  in zip(ls_raw_diesel_dirs, ls_raw_diesel_files)]
  ls_diesel_records = []
  for (function_format, path_file) in zip(ls_diesel_functions, ls_raw_diesel_file_paths):
    ls_diesel_records.append(function_format(path_file))
  
  ## Execute
  #ls_raw_diesel_dir_paths = [os.path.join(path_raw_prices, dir_raw_prices)\
  #                             for dir_raw_prices in ls_raw_diesel_dirs]
  #path_diesel_output_dir = os.path.join(path_source_prices, 'diesel_standardized_tuple_lists')
  #for (function_format, path_input_dir) in zip(ls_diesel_functions, ls_raw_diesel_dir_paths):
  #  loop_and_format(function_format, path_input_dir, path_diesel_output_dir, '_diesel')
  
  # ####
  # GAS
  # ####

  ls_gas_functions = [format_price_201109_201205_gas,
                      format_price_201205_201205_gas,
                      format_price_201205_201212_gas,
                      format_price_201301_201306_gas]
  
  ls_raw_gas_dirs = [u'20110903_20120514_unl',
                     u'20120515_20120521_two',
                     u'20120522_20121203_two',
                     u'20130121_20130604_unl']
  
  # Test each format function with one file of each type
  ls_raw_gas_files = [u'20110904sp.txt',
                      u'20120515_gas_prices',
                      u'20120522_gas_prices',
                      u'20130121_essence_gas_prices']
  ls_raw_gas_file_paths = [os.path.join(path_raw_prices, raw_gas_dir, raw_gas_file)\
                             for (raw_gas_dir, raw_gas_file)
                               in zip(ls_raw_gas_dirs, ls_raw_gas_files)]
  ls_gas_records = []
  for (function_format, path_file) in zip(ls_gas_functions, ls_raw_gas_file_paths):
    ls_gas_records.append(function_format(path_file))
  
  ## Execute
  #ls_raw_gas_dir_paths = [os.path.join(path_raw_prices, dir_raw_prices)\
  #                          for dir_raw_prices in ls_raw_gas_dirs]
  #path_gas_output_dir = os.path.join(path_source_prices, 'gas_standardized_tuple_lists')
  #for (function_format, path_input_dir) in zip(ls_gas_functions, ls_raw_gas_dir_paths):
  #  loop_and_format(function_format, path_input_dir, path_gas_output_dir, '_gas')
  
  
  ## POSITIONS OF E10 AND SP95 IN LISTS (USE NB AVAIL PRICES. DONE)
  #
  #def count_gas_prices(list_indivs):
  #  # to make sure to righly attribute prices to sp95 / e10
  #  # works with list of dics
  #  count_e10 = 0
  #  count_sp95 = 0
  #  for index_indiv, tuple_indiv in enumerate(list_indivs):
  #    if tuple_indiv[4] != '--' and tuple_indiv[4] != ' --':
  #      count_sp95 += 1
  #    if tuple_indiv[6] != '--' and tuple_indiv[6] != ' --':
  #      count_e10 += 1
  #  return {'nb_prices_sp95' : count_sp95, 'nb_prices_e10' : count_e10}
  #
  #def loop_format_and_count(format_function, path_input_dir):
  #  for file_name in os.listdir(path_input_dir):
  #    if re.match('[0-9]{8}[^0-9]', file_name):
  #      formatted_file = format_function(os.path.join(path_input_dir, file_name))
  #      print file_name[:8], count_gas_prices(formatted_file)
  #
  #ls_raw_gas_dir_paths = [os.path.join(path_raw_prices, dir_raw_prices)\
  #                          for dir_raw_prices in ls_raw_gas_dirs]
  #for (function_format, path_input_dir) in zip(ls_gas_functions, ls_raw_gas_dir_paths)[0:1]:
  #  loop_format_and_count(function_format, path_input_dir)
