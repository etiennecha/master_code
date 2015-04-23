#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys # codecs
import json
from datetime import date, timedelta
import datetime
import time
import copy
import itertools
import numpy as np

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def date_range(start_date, end_date):
  """Creates a list of dates (string %Y%m%d)"""
  list_dates = []
  for n in range((end_date + timedelta(1) - start_date).days):
    temp_date = start_date + timedelta(n)
    list_dates.append(temp_date.strftime('%Y%m%d'))
  return list_dates

def build_master(start_date, end_date, path_in, extension_in, dict_var_types):
  # todo: make constant and varying optional
  """
  The function aggregates files i.e. lists of tuples to build a master
  ----
  Arguments description:
  - path_in: location of standardized lists of tuples
  - path_out : location where master files are written
  - dict_variable_types: key 'id' points to location of id in tuple
                         other keys (var types) point to ls of (location_in_tuple, var_name)
                         possible types:  tuple id (unique to each individual)
                                          constant (does not vary over time)
                                          series (varies signifcantly over time)
                                          varying (varies scarcely over time)
  """
  master = {}
  master['ids'] = []
  master['dates'] = date_range(start_date, end_date)
  master['missing_dates'] = []
  master['dict_info'] = {}
  for (tuple_index, var_name) in dict_var_types['series']:
    master.setdefault(var_name, [])
  list_file_paths = [path_in + r'/' + date + extension_in for date in master['dates']]
  for day_index, file_path in enumerate(list_file_paths):
    if os.path.exists(file_path):
      list_obs_tuples = dec_json(file_path)
      for obs_tuple in list_obs_tuples:
        obs_tuple = [elt.strip() for elt in obs_tuple]
        obs_id = obs_tuple[dict_var_types['id']]
        if obs_id in master['ids']:
          indiv_index = master['ids'].index(obs_id)
          # constant (does not vary over time)
          for (tuple_index, var_name) in dict_var_types['constant']:
            if obs_tuple[tuple_index] != master['dict_info'][obs_id][var_name]:
              print 'Replacing', master['dict_info'][obs_id][var_name],\
                    'by', obs_tuple[tuple_index], '(unexpected variation for %s)' %obs_id
              master['dict_info'][obs_id][var_name] = obs_tuple[tuple_index]                   
          # varying (varies scarcely over time)
          for (tuple_index, var_name) in dict_var_types['varying']:
            if obs_tuple[tuple_index] != master['dict_info'][obs_id][var_name][-1][0]:
              master['dict_info'][obs_id][var_name].append((obs_tuple[tuple_index], day_index))
        else:
          master['ids'].append(obs_id)
          indiv_index = master['ids'].index(obs_id)
          master['dict_info'][obs_id] = {'rank': indiv_index}
          # constant (does not vary over time)
          for (tuple_index, var_name) in dict_var_types['constant']:
            master['dict_info'][obs_id][var_name] = obs_tuple[tuple_index]
          # varying (varies scarcely over time)
          for (tuple_index, var_name) in dict_var_types['varying']:
            master['dict_info'][obs_id][var_name] = [(obs_tuple[tuple_index], day_index)]
          # series
          for (tuple_index, var_name) in dict_var_types['series']:
            master[var_name].append([])
        # series: add None (missing dates or individuals) before appending
        for (tuple_index, var_name) in dict_var_types['series']:
          while len(master[var_name][indiv_index]) < day_index:
            master[var_name][indiv_index].append(None)
          master[var_name][indiv_index].append(obs_tuple[tuple_index])
    else:
      master['missing_dates'].append(master['dates'][day_index])
  # series: add None to series shorter than nb of days
  nb_periods = len(list_file_paths)
  for (tuple_index, var_name) in dict_var_types['series']:
    for series in master[var_name]:
      while len(series)  < nb_periods:
        series.append(None)
  return master

path_dir_source_prices = os.path.join(path_data,
                                      'data_gasoline',
                                      'data_source',
                                      'data_prices')

path_dir_built_json = os.path.join(path_data,
                                   'data_gasoline',
                                   'data_built',
                                   'data_paper_dispersion',
                                   'data_json')

#DIESEL MASTER 2011-2013
#Current master: (2011,9,4) to (2012,5,14) (Can do : (2011,9,4) to (2013,6,4))
start_date = date(2011,9,4)
end_date = date(2013,6,4)
path_in = os.path.join(path_dir_source_prices, 'diesel_standardized_tuple_lists')
extension_in = r'_diesel'
dict_var_types = {'id' : 0,
                  'constant': [(1, 'city'),
                               (2, 'name')],
                  'varying': [(3, 'brand')],
                  'series' : [(4,'diesel_price'),
                              (5,'diesel_date')]}
master = build_master(start_date, end_date, path_in, extension_in, dict_var_types)
enc_json(master, os.path.join(path_dir_built_json,
                              'master_price_diesel_raw.json'))

# GAS MASTER 2011-2013
start_date = date(2011,9,4)
end_date = date(2013,6,4)
path_in = os.path.join(path_dir_source_prices, 'gas_standardized_tuple_lists')
extension_in = r'_gas'
dict_var_types = {'id' : 0,
                  'constant': [(1, 'city'),
                               (2, 'name')],
                  'varying': [(3, 'brand')],
                  'series' : [(4,'sp95_price'),
                              (5,'sp95_date'),
                              (6,'e10_price'),
                              (7,'e10_date')]}
master = build_master(start_date, end_date, path_in, extension_in, dict_var_types)
enc_json(master, os.path.join(path_dir_built_json,
                              'master_price_gas_raw.json'))
