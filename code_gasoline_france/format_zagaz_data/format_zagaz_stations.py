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

def format_zagaz_station(block_station):
  href_string = BeautifulSoup(block_station[0][0])\
                  .find('a', {'href' : re.compile('station.php\?id_s*')})['href']
  id_station = re.search('station.php\?id_s=([0-9]*)', href_string).group(1)
  highway =  BeautifulSoup(block_station[0][0])\
                  .find('a', {'href' : re.compile('autoroute.php\?id_a*')})
  if highway:
    highway = highway['title']
  brand_and_name_station = BeautifulSoup(block_station[0][0])('strong')[0].string
  # check if other ('strong') with highway?
  brand_station = brand_and_name_station.split('&nbsp;-&nbsp;')[0]
  name_station = brand_and_name_station.split('&nbsp;-&nbsp;')[1]
  street_station = str_correct_html(BeautifulSoup(block_station[0][1])('p')[0].string)
  zip_station = BeautifulSoup(block_station[0][2])('p')[0].contents[0].strip()
  city_station = str_correct_html(BeautifulSoup(block_station[0][2])\
                  .find('a', {'href' : re.compile('prix-carburant.php*')}).string)
  if block_station[1]:
    comment_station = BeautifulSoup(block_station[1][0]).find('div',
                                                              {'class' : 'station_comm'}).string
  else:
    comment_station = None
  latitude = re.search('Latitude: ([0-9.]*)', block_station[2][0])
  longitude = re.search('longitude: (-?[0-9.]*)', block_station[2][0])
  if latitude and longitude:
    gps_station = (latitude.group(1), longitude.group(1), block_station[2][1])
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
  return ls_zagaz_station

def format_zagaz_station_2013(block_station):
  href_string = BeautifulSoup(block_station[0][0])\
                  .find('a', {'href' : re.compile('station.php\?id_s*')})['href']
  id_station = re.search('station.php\?id_s=([0-9]*)', href_string).group(1)
  highway =  BeautifulSoup(block_station[0][0])\
                  .find('a', {'href' : re.compile('autoroute.php\?id_a*')})
  if highway:
    highway = highway['title']
  brand_and_name_station = BeautifulSoup(block_station[0][0])('strong')[0].string
  brand_station = brand_and_name_station.split('&nbsp;-&nbsp;')[0]
  name_station = brand_and_name_station.split('&nbsp;-&nbsp;')[1]
  street_station = BeautifulSoup(block_station[0][1]).findAll(text=True)
  street_station = [str_correct_html(elt).strip() for elt in street_station\
                      if str_correct_html(elt).strip()]
  zip_station, city_station = None, None
  if len(block_station[0]) > 2:
    zip_station = BeautifulSoup(block_station[0][2]).p.find(text=True).strip() # maybe fragile
    city_station =  str_correct_html(BeautifulSoup(block_station[0][2])\
                      .find('a', {'href' : re.compile('prix-carburant.php*')}).string)
  if block_station[1]:
    comment_station = BeautifulSoup(block_station[1][0]).find('div', {'class' : 'station_comm'}).string
  else:
    comment_station = None
  latitude = re.search('Latitude: ([0-9.]*)', block_station[2][0])
  longitude = re.search('longitude: (-?[0-9.]*)', block_station[2][0])
  if latitude and longitude:
    gps_station = (latitude.group(1), longitude.group(1), block_station[2][1])
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
  return ls_zagaz_station

path_dir_zagaz = os.path.join(path_data, 'data_gasoline', 'data_source', 'data_zagaz')
path_dir_zagaz_raw = os.path.join(path_dir_zagaz, 'data_zagaz_raw')
path_dir_zagaz_json = os.path.join(path_dir_zagaz, 'data_zagaz_json')

# 2012: Oldest data: (check 2012?)
ls_blocks_zagaz_stations = dec_json(os.path.join(path_dir_zagaz_raw,
                                                 '2012_zagaz_info_and_gps.json'))

dict_zagaz_stations = {}
for block_station in ls_blocks_zagaz_stations:
  ls_zagaz_station = format_zagaz_station(block_station)
  dict_zagaz_stations[ls_zagaz_station[0]] = ls_zagaz_station

#enc_json(dict_zagaz_stations,
#         os.path.join(path_dir_zagaz_json,
#                      '2012_dict_zagaz_stations.json'))

# 2013 data (2013/11/15)

# Observation: len(ls_zagaz_station[4]) > 1) => highway gas station
# Globally ok (could apply html corr to highway field but avoid error)

path_json_zagaz_20131115_1 = os.path.join(path_dir_zagaz_raw,
                                          '20131115_zagzag_info_and_gps_p_1_60.json')
path_json_zagaz_20131115_2 = os.path.join(path_dir_zagaz_raw,
                                          '20131115_zagzag_info_and_gps_p_60_end.json')

dict_zagaz_stations_2013 = {}
for path_zagaz_file in [path_json_zagaz_20131115_1, path_json_zagaz_20131115_2]:
  ls_blocks_zagaz_stations = dec_json(path_zagaz_file)
  for block_station in ls_blocks_zagaz_stations:
    ls_zagaz_station = format_zagaz_station_2013(block_station)
    if ls_zagaz_station[5]:
      dict_zagaz_stations_2013[ls_zagaz_station[0]] = ls_zagaz_station
    else:
      print u'Not recorded', u'{:>5s}'.format(ls_zagaz_station[0]), ls_zagaz_station[4]

#enc_json(dict_zagaz_stations_2013,
#         os.path.join(path_dir_zagaz_source,
#                      '2013_dict_zagaz_stations.json'))
