#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import re
from generic_master_info import *
from functions_geocoding import *

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
    # path_code = r'W:\Bureau\Etienne_work\Code'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
    # path_code = r'C:\Users\etna\Dropbox\Code\Etienne_repos'
  
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  folder_source_brands = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_source_gps_coordinates_std = r'\data_gasoline\data_source\data_stations\data_gouv_gps\std'
  
  master_info = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_info_diesel')
  master_price = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')
  dict_brands = dec_json(path_data + folder_source_brands + r'\dict_brands')
  
  #  Build master_addresses (addresses corrected for html pbms and somewhat stdized)
  dict_addresses = {}
  for id, station in master_info.iteritems():
    dict_addresses[id] = [station['address'][i] for i in (5, 3, 4, 0) if station['address'][i]]
  master_addresses = build_master_addresses(dict_addresses)
  master_addresses['15400003'] = [(u'zone industrielle du sedour', u'15400 riom-\xc8s-montagnes')]
  master_addresses['76170004'] = [(u'autoroute a 29', u'76210 bolleville')]
  
  # Update master_geocoding with (and update id needed)
  master_geocoding = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_geocoding')
  ls_ids_not_in_master_geocoding = []
  ls_ids_missing_addresses = []
  for indiv_id, list_addresses in master_addresses.iteritems():
    if list_addresses:
      if indiv_id not in master_geocoding.keys():
        ls_ids_not_in_master_geocoding.append(indiv_id)
        master_geocoding[id] = [list_addresses, [None for i in range(len(list_addresses))]]
      else:
        for address in list_addresses:
          if list(address) not in master_geocoding[indiv_id][0]: # json does not support tuples
            ls_ids_missing_addresses.append(indiv_id)
            # master_geocoding[id][0].append(list(address))
            # master_geocoding[id][1].append(None)
    else:
      print indiv_id, 'has no address hence can not be included in master_geocoding...'
  ls_ids_missing_addresses = list(set(ls_ids_missing_addresses))
  print len(ls_ids_not_in_master_geocoding), 'ids not included in master_geocoding'
  print len(ls_ids_missing_addresses), 'ids have not all addresses in master_geocoding'
  
  # TODO: may want to use standardized string comparison e.g. master_addresses['58640003']
  
  # # Geocode master_geocoding
  # over_query = False
  # c = 0
  # for id, geo_info in master_geocoding.iteritems():
    # for i, address in enumerate(geo_info[0]):
      # if not geo_info[1][i]:
        # info_geocoding = geocode_via_google(','.join(address))
        # c += 1
        # if info_geocoding['status'] == u'OVER_QUERY_LIMIT':
          # over_query = True
          # print 'Query quota used'
          # break
        # else:
          # master_geocoding[id][1][i] = info_geocoding
          # time.sleep(0.15)
    # if over_query:
      # break
  # print c, 'queries performed (should be < 2500)'
  
  # enc_json(master_geocoding, path_data + folder_built_master_json + r'\master_diesel\master_geocoding')
  
  # Check results in master_geocoding
  dict_results_geocoding, ls_geocoded_but_weird, ls_not_geocoded = get_stats_geocoding(master_geocoding)
  print '\nStations not geocoded yet', len(ls_not_geocoded)
  print 'Stations geocoded but result can not be read', len(ls_geocoded_but_weird)
  for quality, ls_quality_results in dict_results_geocoding.iteritems():
    print quality, len(ls_quality_results)
  
  for indiv_id in dict_results_geocoding['ROOFTOP'][-20:]:
    if indiv_id in master_addresses:
      gps = get_best_geocoding_info(master_geocoding[indiv_id][1])['results'][0]['geometry']['location']
      print '\n', indiv_id, gps
      print master_addresses[indiv_id]
  
  for indiv_id in dict_results_geocoding['ZERO_RESULTS']:
    if indiv_id in master_addresses:
      print '\n', indiv_id, master_addresses[indiv_id]