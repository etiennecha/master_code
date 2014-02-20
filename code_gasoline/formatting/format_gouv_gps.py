#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def format_gps_coordinates(gps_lea):
  master_gps_coordinates = {}
  for i in range(0,len(gps_lea)):
    if len(gps_lea[i].split('||')) == 3:
      master_gps_coordinates[gps_lea[i].split('||')[0]] =\
        [float(gps_lea[i].split('||')[2])/100000, float(gps_lea[i].split('||')[1])/100000]
  return master_gps_coordinates

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  
  folder_source_gps_coordinates_std = r'\data_gasoline\data_source\data_stations\data_gouv_gps\std'
  folder_source_gps_coordinates_raw = r'\data_gasoline\data_source\data_stations\data_gouv_gps\raw'
  
  list_gps_files = [r'\20130117_list_coordinates_essence',
                    r'\20130117_list_coordinates_diesel',
                    r'\20130724_list_coordinates_essence',
                    r'\20130724_list_coordinates_diesel'] 
  
  master_files = []
  for gps_file in list_gps_files:
    file = dec_json(path_data + folder_source_gps_coordinates_raw + gps_file)
    file = format_gps_coordinates(file)
    master_files.append(file)
    enc_json(file, path_data + folder_source_gps_coordinates_std + gps_file)