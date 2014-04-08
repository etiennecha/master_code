#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import json
import re
from functions_string import *
from BeautifulSoup import BeautifulSoup

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

path_dir_raw = os.path.join(path_data, 'data_gasoline', 'data_raw')
path_dir_zagaz_raw = os.path.join(path_dir_raw, 'data_stations', 'data_zagaz')
path_json_zagaz_raw = os.path.join(path_dir_zagaz_raw, 'zagaz_info_and_gps.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dir_zagaz_source = os.path.join(path_dir_source, 'data_stations', 'data_zagaz')

ls_zagaz_info_stations_raw = dec_json(path_json_zagaz_raw)

# #####################
# CLEANING ZAGAZ DATA
# #####################

ls_ls_zagaz_stations = []
dict_zagaz = {}
for i, station in enumerate(ls_zagaz_info_stations_raw):
  href_string = BeautifulSoup(station[0][0])\
                  .find('a', {'href' : re.compile('station.php\?id_s*')})['href']
  id_station = re.search('station.php\?id_s=([0-9]*)', href_string).group(1)
  highway =  BeautifulSoup(station[0][0])\
                  .find('a', {'href' : re.compile('autoroute.php\?id_a*')})
  if highway:
    highway = highway['title']
  brand_and_name_station = BeautifulSoup(station[0][0])('strong')[0].string
  # check if other ('strong') with highway?
  brand_station = brand_and_name_station.split('&nbsp;-&nbsp;')[0]
  name_station = brand_and_name_station.split('&nbsp;-&nbsp;')[1]
  street_station = str_correct_html(BeautifulSoup(station[0][1])('p')[0].string)
  zip_station = BeautifulSoup(station[0][2])('p')[0].contents[0].strip()
  city_station = str_correct_html(BeautifulSoup(station[0][2])\
                  .find('a', {'href' : re.compile('prix-carburant.php*')}).string)
  if station[1]:
    comment_station = BeautifulSoup(station[1][0]).find('div', {'class' : 'station_comm'}).string
  else:
    comment_station = None
  latitude = re.search('Latitude: ([0-9.]*)', station[2][0])
  longitude = re.search('longitude: (-?[0-9.]*)', station[2][0])
  if latitude and longitude:
    gps_station = (latitude.group(1), longitude.group(1), station[2][1])
  else:
    gps_station = (None, None, None)
  ls_zagaz_station = [id_station,
                      brand_station,
                      name_station,
                      comment_station,
                      street_station,
                      zip_station,
                      city_station,
                      gps_station,
                      highway]
  ls_ls_zagaz_stations.append(ls_zagaz_station)
  dict_zagaz[id_station] = ls_zagaz_station

enc_json(dict_zagaz, os.path.join(path_dir_zagaz_source, '2012_zagaz_info_gps.json'))
