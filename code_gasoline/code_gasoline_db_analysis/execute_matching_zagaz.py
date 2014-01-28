#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json
from functions_string import *

def enc_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())
    
if __name__=="__main__":
  # path_data: data folder at different locations at CREST vs. HOME
  # could do the same for path_code if necessary (import etc).
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
    path_code = r'W:\Bureau\Etienne_work\Code'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  
  folder_source_zagaz_std = r'\data_gasoline\data_source\data_stations\data_zagaz\std'  
  folder_source_zagaz = r'\data_gasoline\data_source\data_json_prices\zagaz'
    
  folder_source_brand = r'\data_gasoline\data_source\data_stations\data_brands'
  dict_brands = dec_json(path_data + folder_source_brand + r'\dict_brands')
  
  ls_ls_zagaz_gps = dec_json(path_data + folder_source_zagaz_std + r'\2012_zagzag_gps')
  dict_zagaz_all = dec_json(path_data + folder_source_zagaz + r'\20140124_zagzag_stations')
  dict_zagaz_prices = dec_json(path_data + folder_source_zagaz + r'\20140127_zagzag_dict_ext_prices')
  
  # TODO: include in format file and drop
  dict_zagaz_gps = {}
  for ls_zagaz_gps in ls_ls_zagaz_gps:
    dict_zagaz_gps[ls_zagaz_gps[0]] = ls_zagaz_gps[1:]
    
  # Check matching between (old) zagaz gps file and (recent) info/price files
  ls_missing_gps_zagaz = [indiv_id for indiv_id in dict_zagaz_all if indiv_id not in dict_zagaz_gps]
  print len(ls_missing_gps_zagaz), 'gps coordinates are to be collected'
  # TODO: pbm: need to have all insee codes if those are used for matching