#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re
import json
import urllib2
import time

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def geocode_via_mapquest(location):
  # systematic queries forbidden...
  location = urllib2.quote(location.encode('utf-8'))
  url = u'http://open.mapquestapi.com/nominatim/v1/search?q=%s&' %location +\
        u'format=json&polygon=1&addressdetails=1&countrycodes=fr&viewbox=-5.133333,51.0833,9.55,41.333333'
  geocoding_response = urllib2.urlopen(url)
  json_response = json.loads(geocoding_response.read())
  return json_response

def geocode_via_google(key_api, location):
  location += ', France'
  location = urllib2.quote(location.encode('utf-8'))
  url = u'https://maps.googleapis.com/maps/api/geocode/json?' +\
        u'address=%s&region=FR&sensor=false&key=%s' %(location, key_api)
  geocoding_response = urllib2.urlopen(url)
  json_response = json.loads(geocoding_response.read())
  return json_response

def get_best_geocoding_info(geocoding_info):
  """
  Find best quality geocoding result in a list of standard Google geocoding results
  Supports lists of None (geocoding not yet done)
  """
  dict_score_stats = {'ROOFTOP' : 3,
                      'RANGE_INTERPOLATED' : 2,
                      'GEOMETRIC_CENTER' : 1,
                      'APPROXIMATE' : 0}
  score = -1
  best_geocoding_info = None
  for info in geocoding_info:
    if (info) and\
       (info['status'] == u'OK') and\
       (dict_score_stats[info['results'][0]['geometry']['location_type']]) > score:
      best_geocoding_info = info
      score = dict_score_stats[info['results'][0]['geometry']['location_type']]
  return best_geocoding_info

def get_stats_geocoding(master_geocoding):
  """ 
  Provide descriptive stats on Google geocoding results
  Supports no address and geocoding not yet done
  """
  score_stats =  {'ROOFTOP' : [],
                  'RANGE_INTERPOLATED' : [],
                  'GEOMETRIC_CENTER' : [],
                  'APPROXIMATE' : [],
                  'ZERO_RESULTS' : [],
                  'INVALID_REQUEST' : []}
  ls_geocoded_but_weird = []
  ls_not_geocoded = []
  for indiv_id, geo_info in master_geocoding.iteritems():
    if geo_info[1]:
      best_geocoding_info = get_best_geocoding_info(geo_info[1])
      if best_geocoding_info:
        score_stats[best_geocoding_info['results'][0]['geometry']['location_type']].append(indiv_id)
      elif 'INVALID_REQUEST' in [dict_info['status'] for dict_info in geo_info[1] if dict_info]:
        score_stats['INVALID_REQUEST'].append(indiv_id)
      elif 'ZERO_RESULTS' in [dict_info['status'] for dict_info in geo_info[1] if dict_info]:
        score_stats['ZERO_RESULTS'].append(indiv_id)
      else:
        ls_geocoded_but_weird.append(indiv_id)
    else:
      ls_not_geocoded.append(indiv_id)
  return score_stats, ls_geocoded_but_weird, ls_not_geocoded

# path_data: data folder at different locations at CREST vs. HOME
if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
geocoding_folder = r'\data_gasoline\data_source\geolocalisation\geocoding'

if __name__=="__main__":
  
  test_google =  geocode_via_google(u'r.n 7,84430 mondragon')
  test_mapquest = geocode_via_mapquest(u'9 rue des Grandes Allées, 02600 Villers-Cotterêts')
  
  # TODO: update following
  
  # dict_ids_bad_gps = dec_json(path_data + geocoding_folder + r'\current_master_geocoding')
  # for id, info in dict_ids_bad_gps.iteritems():
    # if 'gps_geocoding' not in info or info['gps_geocoding']['status'] == u'OVER_QUERY_LIMIT':
      # try:
        # address = ', '.join(info['address'])
        # info['gps_geocoding'] = geocode_via_google(address.encode('utf-8'))
        # time.sleep(0.15)
      # except Exception, e:
        # print id, e
        # info['gps_geocoding'] = None
  # # enc_stock_json(dict_ids_bad_gps, machine_path + r'\\' + geocoding_folder + r'\\current_master_geocoding')
  
  # http://open.mapquestapi.com/nominatim/v1/search?q=14%20rue%20martignon,%20rueil%20malmaison&format=json&polygon=1&addressdetails=1&countrycodes=fr&viewbox=-5.133333,51.0833,9.55,41.333333
  
  # France box incl. Corsica
  # 51.0833, -5.133333 North West
  # 41.333333, 9.55 South East
  
  # Google bounds example : bounds=34.172684,-118.604794|34.236144,-118.500938
  # France: bounds=41.333333,-5.133333|51.0833,9.55
  # addr_1 = 14%20%rue%20martignon,%2092500%20rueil%20malmaison
  # addr_2 = r.n%207,84430%20mondragon
  # http://maps.googleapis.com/maps/api/geocode/json?address=r.n%207,84430%20mondragon&region=FR&sensor=false&bounds=41.333333,-5.133333|51.0833,9.55
  
  # Mapquest viewbox: viewbox=left,top,right,bottom
  # France: -5.133333,51.0833,9.55,41.333333 
  
