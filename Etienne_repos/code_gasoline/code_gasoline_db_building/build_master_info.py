#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
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

if __name__=="__main__":
  # path_data: data folder at different locations at CREST vs. HOME
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  # structure of the data folder should be the same
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  
  folder_source_gouv_stations_std = r'\data_gasoline\data_source\data_stations\data_gouv_stations\std'
  files_source_data = [r'\20111121_gouv_stations',
                       r'\20120000_gouv_stations',
                       r'\20120314_gouv_stations',
                       r'\20120902_gouv_stations',
                       r'\20130220_gouv_stations',
                       r'\20130707_gouv_stations']
  
  list_paths_std = [path_data + folder_source_gouv_stations_std + file for file in files_source_data]
  master_files_info = [dec_json(path_file_std) for path_file_std in list_paths_std]
  
  list_info_keys = ['name',
                    'address', 
                    'services', 
                    'hours', 
                    'closed_days', 
                    'highway', 
                    'gps', 
                    'gas_types']
  
  master_info = build_master_info(master_files_info, list_info_keys)
  
  # enc_json(master_info, path_data + folder_built_master_json + r'\master_diesel\master_info_diesel_raw')
  enc_json(master_info, path_data + folder_built_master_json + r'\master_gas\master_info_gas_raw')