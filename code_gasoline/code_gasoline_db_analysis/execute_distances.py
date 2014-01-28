#!/usr/bin/python
# -*- coding: utf-8 -*-

import json
import os, sys, codecs
import re
import math
from generic_master_info import *
from functions_geocoding import * # TODO: reorganize (put into functions_geocoding)

def compute_distance(coordinates_A, coordinates_B):
  d_lat = math.radians(float(coordinates_B[0]) - float(coordinates_A[0]))
  d_lon = math.radians(float(coordinates_B[1]) - float(coordinates_A[1]))
  lat_1 = math.radians(float(coordinates_A[0]))
  lat_2 = math.radians(float(coordinates_B[0]))
  a = math.sin(d_lat/2.0) * math.sin(d_lat/2.0) + \
        math.sin(d_lon/2.0) * math.sin(d_lon/2.0) * math.cos(lat_1) * math.cos(lat_2)
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  distance = 6371 * c
  return round(distance, 2)

def get_list_list_cross_distances(dict_lists_ids_gps):
  """ dict_lists_ids_gps has keys 'ids' : list_ids and 'gps' : list_gps_coordinates or np.nan"""
  list_list_cross_distances = [[np.nan for gps in dict_lists_ids_gps['gps']] for gps in dict_lists_ids_gps['gps']]
  for i, gps_i in enumerate(dict_lists_ids_gps['gps']):
    for j, gps_j in enumerate(dict_lists_ids_gps['gps']):
      if gps_i and gps_j and i != j:
        list_list_cross_distances[i][j] = compute_distance(gps_i, gps_j)
  return [dict_lists_ids_gps, list_list_cross_distances]

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
    path_code = r'W:\Bureau\Etienne_work\Code'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
    path_code = r'C:\Users\etna\Dropbox\Code\Etienne_repos'
  
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  folder_source_brands = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_source_gps_coordinates_std = r'\data_gasoline\data_source\data_stations\data_gouv_gps\std'
  
  master_info = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_info_diesel')
  master_price = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')
  dict_brands = dec_json(path_data + folder_source_brands + r'\dict_brands')
  
  # 1/ Load All GPS information
  # 2/ Compute distances and build competition data (in relation if needed with master price)
  
  # Load gps collected from prix-carburant.gouv.fr
  list_gps_gouv_files = [r'\20130117_list_coordinates_essence',
                         r'\20130117_list_coordinates_diesel',
                         r'\20130724_list_coordinates_essence',
                         r'\20130724_list_coordinates_diesel'] 
  master_gps_gouv_files = [dec_json(path_data + folder_source_gps_coordinates_std + gps_file)\
                            for gps_file in list_gps_gouv_files]
  master_gps_gouv = master_gps_gouv_files[0]
  ls_gps_gouv_but_no_price = []
  for i in range(1, len(master_gps_gouv_files)):
    master_gps_gouv.update(master_gps_gouv_files[i])
  for indiv_id, gps_coord in master_gps_gouv.iteritems():
    if indiv_id in master_info.keys():
      master_info[indiv_id]['gps'][4] = gps_coord
    else:
      ls_gps_gouv_but_no_price.append(indiv_id)
  print len(ls_gps_gouv_but_no_price), 'ids not in master_price but we have gps coord: recent stations (?)'
  
  # Load gps provided by Ronan (from prix-carburant.gouv.fr but older)
  master_rls = open(path_data + r'\data_gasoline\data_source\data_stations\data_rls\raw\data_rls.csv', 'r')
  master_rls = master_rls.read().split('\n')[1:-1]
  master_rls = [row.split(',') for row in master_rls]
  master_gps_rls = {}
  for row in master_rls:
    if row[25] and row[27] and float(row[25]) != 0 and float(row[27]) != 0:
      master_gps_rls[row[0]] = [float(row[25]), float(row[27])]
  
  # Load gps from geocoding
  master_geocoding = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_geocoding')
  # ls_geocoding_best = [get_best_geocoding_info(indiv_info[1]) \
                        # if indiv_info[1] else None for indiv_id, indiv_info in master_geocoding.iteritems()]
  master_geocoding_best = {}
  for indiv_id, indiv_info in master_geocoding.iteritems():
    if indiv_info[1]:
      master_geocoding_best[indiv_id] = get_best_geocoding_info(indiv_info[1])
  
  # Gather gps coordinates from various sources in ls_ls_indiv_gps
  ls_ls_indiv_gps = []
  ls_ids_no_gps = []
  for indiv_id in master_price['ids']:
    ls_indiv_gps = [None, None, None]
    if indiv_id in master_info and master_info[indiv_id]['gps'][4]:
      ls_indiv_gps[0] = master_info[indiv_id]['gps'][4]
    if indiv_id in master_gps_rls:
      ls_indiv_gps[1] = master_gps_rls[indiv_id]
    if indiv_id in master_geocoding_best and master_geocoding_best[indiv_id]:
      ls_indiv_gps[2] = [master_geocoding_best[indiv_id]['results'][0]['geometry']['location']['lat'],
                         master_geocoding_best[indiv_id]['results'][0]['geometry']['location']['lng'],
                         master_geocoding_best[indiv_id]['results'][0]['geometry']['location_type']]
    ls_ls_indiv_gps.append(ls_indiv_gps)
    if not [x for x in ls_indiv_gps]:
      ls_ids_no_gps.append(indiv_id)
  
  # Check consistency of station gps coordinates from various sources
  # a/ raise alarm if (too) inconsistent
  # b/ raise alarm if ROOFTOP status and still distance is not very small
  ls_ls_indiv_distances = []
  for indiv_ind, indiv_gps_info in enumerate(ls_ls_indiv_gps):
    ls_indiv_distances = [None, None, None]
    if indiv_gps_info[0] and indiv_gps_info[1]:
      ls_indiv_distances[0] = compute_distance(indiv_gps_info[0][0:2], indiv_gps_info[1][0:2])
    if indiv_gps_info[0] and indiv_gps_info[2]:
      ls_indiv_distances[1] = compute_distance(indiv_gps_info[0][0:2], indiv_gps_info[2][0:2])
    if indiv_gps_info[1] and indiv_gps_info[2]:
      ls_indiv_distances[2] = compute_distance(indiv_gps_info[1][0:2], indiv_gps_info[2][0:2])
    ls_ls_indiv_distances.append(ls_indiv_distances)
  # Globally... geocoding may fail badly (only lowest quality geocoding?)
  # Conclusion... should really try to match gouv data with zagaz data
  
  # TODO: reconcile gouv data with zagaz data to improve gps info quality
  
  # 1/ BUILD MASTER GEO (FINAL)
  # TODO: add previous geocoding data? (just in case)
  
  master_geo = {}
  for indiv_id, gps_rls_info in master_gps_rls.iteritems():
    if indiv_id in master_info.keys():
      master_geo[indiv_id] = gps_rls_info
  master_geo.update(master_gps_gouv)
  del(master_geo['33830004']) # gps is [0,0]
  del(master_geo['31170006']) # gps is [0,0]
  list_distance_alert = []
  list_geocoding_alert = []
  for indiv_id, geo_info in master_geocoding.iteritems():
    geocoding_info = get_best_geocoding_info(geo_info[1])
    # COULD CHECK COMMUNE CONSISTENCY
    if (geocoding_info) and\
       (geocoding_info['status'] == u'OK') and\
       (u'France' in geocoding_info['results'][0]['formatted_address']):
      lat = geocoding_info['results'][0]['geometry']['location']['lat']
      lng = geocoding_info['results'][0]['geometry']['location']['lng']
      gps_geocoding = (lat, lng)
      if indiv_id in master_geo.keys():
        distance = compute_distance(master_geo[indiv_id], gps_geocoding)
        if distance > 10:
          list_distance_alert.append((indiv_id, distance, master_geo[indiv_id], gps_geocoding))
      else:
        master_geo[indiv_id] = gps_geocoding
        list_geocoding_alert.append((indiv_id, gps_geocoding))
  
  for indiv_id, gps_geocoding in master_geo.iteritems():
    if master_info.get(indiv_id):
      master_info[indiv_id]['gps'][5] = gps_geocoding
    else:
      print indiv_id, 'not in master info (gps not recorded)' # check why... it is bad?
  
  # enc_json(master_info, path_data + folder_built_master_json + r'\master_diesel\master_info_diesel_for_output')
  
  # # 2/ GET CROSS DISTANCES
  
  # # order of pref 4 (website) then 3 (best geocoding info)
  # list_ids = master_price['ids']
  # list_gps = []
  # for id in list_ids:
    # if id in master_info and master_info[id]['highway'][3] != 1:
      # if master_info[id]['gps'][4]:
        # list_gps.append(master_info[id]['gps'][4][0:2])
      # elif master_info[id]['gps'][3]:
        # list_gps.append(master_info[id]['gps'][3][0:2])
      # else:
        # list_gps.append(None)
    # else:
      # list_gps.append(None)
  # dict_best_gps = {'ids': master_price['ids'],
                   # 'gps': list_gps}
  
  # # Execution time: c. 15-20 minutes
  # dict_ids_gps_cross_distances, list_list_cross_distances = get_list_list_cross_distances(dict_best_gps)
  # np_arrays_cross_distances = np.array(list_list_cross_distances, dtype = np.float32)
  # # np_arrays_cross_distances_ma = np.ma.masked_array(np_arrays_cross_distances, np.isnan(np_arrays_cross_distances))
  # np.save(path_data + folder_built_master_json + r'\np_arrays_cross_distances.npy', np_arrays_cross_distances)
  # enc_json(dict_ids_gps_cross_distances, path_data + folder_built_master_json + r'\dict_ids_gps_cross_distances')
  
  # # dict_ids_gps_cross_distances = dec_json(path_data + folder_built_master_json + r'\dict_ids_gps_cross_distances')
  # # np_arrays_cross_distances = np.load(path_data + folder_built_master_json + r'\np_arrays_cross_distances.npy')
  
  # # Numpy array: None were converted to np.nan (if dtype = np.float32) which are preserved by tolist()
  # # np.nan comparison (<, > etc.) always false but if np.nan is True (different from None)
  # list_list_cross_distances = np_arrays_cross_distances.tolist()
  
  # # 3/ IDENTIFYING UNACCEPTABLE DISTANCES (SAME LOCATION => UPDATE GPS?)
  
  # list_same_location = []
  # set_problematic_stations = set()
  # for i, list_distances_i in enumerate(list_list_cross_distances):
    # for j, distance_i_j in enumerate(list_list_cross_distances[i][i+1:], start = i+1):
      # if distance_i_j < np.float32(0.01):
        # list_same_location.append((i,j))
        # set_problematic_stations.add(i)
        # set_problematic_stations.add(j)
        # print dict_ids_gps_cross_distances['ids'][i],\
          # dict_ids_gps_cross_distances['ids'][j],\
          # master_info[dict_ids_gps_cross_distances['ids'][i]]['address'][4],\
          # master_info[dict_ids_gps_cross_distances['ids'][j]]['address'][4]
  # print 'length of list replace or drop', len(set_problematic_stations)
  
  # # TODO: Replace gps from gouv by gps geocoding (or zagaz?)
  
  # list_use_geocoding_info = []
  # list_drop = []
  # for i in list(set_problematic_stations):
    # id = dict_ids_gps_cross_distances['ids'][i]
    # geocoding_info = get_best_geocoding_info(master_geocoding[id][1])
    # if (geocoding_info) and\
       # (geocoding_info['status'] == u'OK') and\
       # (u'France' in geocoding_info['results'][0]['formatted_address']):
      # list_use_geocoding_info.append(id)
      # print geocoding_info['results'][0]['geometry']['location_type'], id,\
            # master_addresses[id], geocoding_info['results'][0]['formatted_address']
    # else:
      # list_drop.append(i)
  
  # # TODO: Visual check
  
  # for id in list_use_geocoding_info:
    # ind = master_price['ids'].index(id)
    # dict_ids_gps_cross_distances['gps'][id] = get_best_geocoding_info(master_geocoding[id][1])
  
  # # TODO: COMPUTE CROSS DISTANCES AND FINISH...
  
  # # 4/ GETTING LISTS OF COMPETITORS (LISTS OF TUPLES ID DISTANCE)
  
  # max_competitor_distance = 10
  
  # list_list_competitors = []
  # for i, list_distances_i in enumerate(list_list_cross_distances):
    # if i not in list_drop:
      # list_competitors = []
      # for j, distance_i_j in enumerate(list_list_cross_distances[i]):
        # if distance_i_j < np.float32(max_competitor_distance) and j not in list_drop:
          # list_competitors.append((dict_ids_gps_cross_distances['ids'][j], distance_i_j))
    # else:
      # list_competitors = None
    # list_list_competitors.append(list_competitors)
  
  # # enc_json(list_list_competitors, path_data + folder_built_master_json + r'\list_list_competitors')
  
  # # 5/ GETTING A LIST OF COMPETITOR PAIRS (A LIST OF TUPLES EACH INCLUDING AN ID PAIR TUPLE AND DISTANCE)
  
  # list_tuple_competitors = []
  # for i, list_distances_i in enumerate(list_list_cross_distances):
    # if i not in list_drop:
      # for j, distance_i_j in enumerate(list_list_cross_distances[i][i+1:], start = i+1):
        # if distance_i_j < np.float32(max_competitor_distance) and j not in list_drop:
          # list_tuple_competitors.append(\
            # ((dict_ids_gps_cross_distances['ids'][i], dict_ids_gps_cross_distances['ids'][j]), float(distance_i_j)))
  
  # enc_json(list_tuple_competitors, path_data + folder_built_master_json + r'\list_tuple_competitors')
  
  # list_list_competitors = dec_json(path_data + folder_built_master_json + r'\list_list_competitors')
  # list_tuple_competitors = dec_json(path_data + folder_built_master_json + r'\list_tuple_competitors')
  
  
  # DEPRECATED (too slow)
  # enc_json(list_list_cross_distances, path_data + folder_built_master_json + r'\list_list_cross_distances') 
  # list_list_cross_distances = dec_json(path_data + folder_built_master_json + r'\list_list_cross_distances')