#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import json
import os, sys #codecs
import re

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

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
    dict_id = dict(zip(list_field_keys, [[] for i in range(len(list_field_keys))]))
    for period_dict in master_by_period:
      for field_key in list_field_keys:
        if period_dict.get(id) is not None:
          dict_id[field_key].append(period_dict[id].get(field_key))
        else:
          dict_id[field_key].append(None)
    master_by_id[id] = dict_id
  return master_by_id

path_dir_gouv_stations = os.path.join(path_data,
                                      'data_gasoline',
                                      'data_source',
                                      'data_stations',
                                      'data_gouv_stations')

ls_file_names = ['20111121_gouv_stations.json',
                 '20120000_gouv_stations.json',
                 '20120314_gouv_stations.json',
                 '20120902_gouv_stations.json',
                 '20130220_gouv_stations.json',
                 '20130707_gouv_stations.json']

list_info_keys = ['name',
                  'address', 
                  'services', 
                  'hours', 
                  'closed_days', 
                  'highway', 
                  'gps', 
                  'gas_types']

path_dir_built_json = os.path.join(path_data,
                                   'data_gasoline',
                                   'data_built',
                                   'data_paper',
                                   'data_json')

ls_file_paths = []
master_files_info = [dec_json(os.path.join(path_dir_gouv_stations, file_name))\
                        for file_name in ls_file_names]

# Obvious error of unknown original (CAHORS => AULNAY SOUS BOIS...)
master_files_info[5]['46000011']['address'] = master_files_info[4]['46000011']['address']

master_info = build_master_info(master_files_info, list_info_keys)


# OUTPUT TO CSV

enc_json(master_info, os.path.join(path_dir_built_json,
                                   'master_info_raw.json'))

# No preliminary fix deemed necessary at this stage... could add (e.g. brands)
enc_json(master_info, os.path.join(path_dir_built_json,
                                   'master_info_fixed.json'))
