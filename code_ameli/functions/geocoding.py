#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re
import json
import urllib2
import time

def dec_json(path_file):
  with open(path_file, 'r') as f:
    return json.loads(f.read())

def enc_json(json_obj, path_file):
  with open(path_file, 'w') as f:
    json.dump(json_obj, f)

def get_google_direction(key_api, origin, destination):
  origin = urllib2.quote(origin.encode('utf-8'))
  destination = urllib2.quote(destination.encode('utf-8'))
  url = 'https://maps.googleapis.com/maps/api/directions/json?'+\
        'origin={:s}&destination={:s}&key={:s}'.format(origin,
                                                       destination,
                                                       key_api)
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


def geocode_via_google_textsearch(key_api, location, all_pages = False):
  """
  Tight quota hence best practice: 
  - first result page only (if helps?) 
  - restrict type
  """
  results = []
  location = urllib2.quote(location.encode('utf-8'))
  url = u'https://maps.googleapis.com/maps/api/place/textsearch/json?' +\
        u'key=%s&sensor=false&query=%s' %(key_api, location)
  geocoding_response = urllib2.urlopen(url)
  json_response = json.loads(geocoding_response.read())
  status = json_response['status']
  results = json_response['results']
  if all_pages:
    while 'next_page_token' in json_response.keys():
      time.sleep(2)
      url = u'https://maps.googleapis.com/maps/api/place/textsearch/json?' +\
            u'pagetoken=%s&sensor=false&key=%s' %(json_response['next_page_token'], key)
      geocoding_response = urllib2.urlopen(url)
      json_response = json.loads(geocoding_response.read())
      status = json_response['status']
      results += json_response['results']
  return status, results

def geocode_via_mapquest(location):
  """
  Check guidelines: systematic queries forbidden?
  """
  location = urllib2.quote(location.encode('utf-8'))
  url = u'http://open.mapquestapi.com/nominatim/v1/search?q=%s&' %location +\
        u'format=json&polygon=1&addressdetails=1&'+\
        u'countrycodes=fr&viewbox=-5.133333,51.0833,9.55,41.333333'
  geocoding_response = urllib2.urlopen(url)
  json_response = json.loads(geocoding_response.read())
  return json_response

def get_best_google_geocoding_info(geocoding_info):
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

def get_google_geocoding_stats(dict_geocoding):
  """ 
  Provide descriptive stats on Google geocoding results
  Supports no address and geocoding not yet done
  #ls_location_type = ['ROOFTOP',
  #                    'RANGE_INTERPOLATED',
  #                    'GEOMETRIC_CENTER',
  #                    'APPROXIMATE']
  #ls_bad_status = ['INVALID_REQUEST',
  #                 'ZERO_RESULTS']
  """
  dict_score_stats = {'TO_DO' : []}
  for indiv_id, indiv_geo in dict_geocoding.items():
    best_indiv_geo = get_best_google_geocoding_info(indiv_geo[1])
    if best_indiv_geo:
      dict_score_stats.setdefault(\
        best_indiv_geo['results'][0]['geometry']['location_type'], []).append(indiv_id)
    else:
      if [x for x in indiv_geo[1] if x]:
          dict_score_stats.setdefault(\
            indiv_geo[1][0]['status'], []).append(indiv_id)
      else:
        dict_score_stats['TO_DO'].append(indiv_id)
  return dict_score_stats

if __name__=="__main__":
  
  # Need to have a google api key
  path_data_0 = u'W:\Bureau\Etienne_work\Data'
  path_data_1 = u'C:\Bureau\Etienne_work\Data'
  if not os.path.exists(path_data_0):
    path_data_0 = path_data_1
  path_dir_api_keys = os.path.join(path_data_0, 'api_keys')
  with open(os.path.join(path_dir_api_keys, 'key_google_api.txt'), 'r') as f:
    key_google_api = f.read()
  
  location = u'9 rue des Grandes Allées, 02600 Villers-Cotterêts'
  test_google_geocoding =  geocode_via_google(key_google_api,
                                              location)
  test_mapquest_geocoding = geocode_via_mapquest(location)

  origin = u'7 rue Marie Bonaparte, Saint Cloud, France'
  destination = u'15 Boulevard Gabriel Péri, Malakoff, France'
  test_google_direction = get_google_direction(key_google_api,
                                               origin,
                                               destination)
  
  #http://open.mapquestapi.com/nominatim/v1/search?
  #q=14%20rue%20martignon,%20rueil%20malmaison
  #&format=json&polygon=1&addressdetails=1
  #&countrycodes=fr&viewbox=-5.133333,51.0833,9.55,41.333333
  
  #France box incl. Corsica
  #51.0833, -5.133333 North West
  #41.333333, 9.55 South East
  
  #Google bounds example : bounds=34.172684,-118.604794|34.236144,-118.500938
  #France: bounds=41.333333,-5.133333|51.0833,9.55
  #addr_1 = 14%20%rue%20martignon,%2092500%20rueil%20malmaison
  #addr_2 = r.n%207,84430%20mondragon
  #http://maps.googleapis.com/maps/api/geocode/json?address=r.n%207,84430%20mondragon
  #&region=FR&sensor=false&bounds=41.333333,-5.133333|51.0833,9.55
  
  #Mapquest viewbox: viewbox=left,top,right,bottom
  #France: -5.133333,51.0833,9.55,41.333333
