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

def format_gps_coordinates(ls_gps):
  dict_gps = {}
  for row_gps in ls_gps:
    # old format
    if ((isinstance(row_gps, str)) or\
        (isinstance(row_gps, unicode))) and\
       (len(row_gps.split('||')) == 3):
      ls_station_gps = row_gps.split('||')
      dict_gps[ls_station_gps[0]]=\
          [u'{:.6f}'.format(float(ls_station_gps[2])/100000),
           u'{:.6f}'.format(float(ls_station_gps[1])/100000)]
    # new format (2014, maybe end 2013?)
    elif (isinstance(row_gps, list)) and\
         (len(row_gps) == 3):
      dict_gps[row_gps[0]] =\
          [u'{:.6f}'.format(float(row_gps[2])),
           u'{:.6f}'.format(float(row_gps[1]))]
    else:
      if row_gps:
        print 'Unexpected row_gps', row_gps
  return dict_gps

if __name__=="__main__":
  # path_data: default to CREST location, else try home location
  path_data = os.path.join(u'W:\\', u'Bureau', u'Etienne_work', u'Data')
  if not os.path.exists(path_data):
    path_data = os.path.join(u'C:\\', u'Users', u'etna', u'Desktop',
                             u'Etienne_work', u'Data')

  path_dir_raw_gps = os.path.join(path_data,
                                  u'data_gasoline',
                                  u'data_raw',
                                  u'data_stations',
                                  u'data_gouv_gps')

  path_dir_source_gps = os.path.join(path_data,
                                     u'data_gasoline',
                                     u'data_source',
                                     u'data_stations',
                                     u'data_gouv_gps')
  
  ls_gps_file_names = [u'20130117_ls_gps_essence.json',
                       u'20130117_ls_gps_diesel.json',
                       u'20130724_ls_gps_essence.json',
                       u'20130724_ls_gps_diesel.json',
                       u'20131115_ls_gps_essence.json',
                       u'20131115_ls_gps_diesel.json',
                       u'20141206_ls_gps_essence.json',
                       u'20141206_ls_gps_diesel.json']
  
  ls_dict_gps = []
  for gps_file_name in ls_gps_file_names:
    gps_file = dec_json(os.path.join(path_dir_raw_gps,
                                     gps_file_name))
    gps_file = format_gps_coordinates(gps_file)
    ls_dict_gps.append(gps_file)
    enc_json(gps_file, os.path.join(path_dir_source_gps,
                                    gps_file_name.replace(u'_ls_', '_dict_')))
