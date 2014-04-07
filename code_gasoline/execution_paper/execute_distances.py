#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_geocoding import *
from generic_competition import *

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_info_output = os.path.join(path_dir_built_json, 'master_info_diesel_for_output.json')
path_geocoding = os.path.join(path_dir_built_json, 'master_geocoding.json')
path_ar_cross_distances = os.path.join(path_dir_built_json, 'ar_cross_distances.npy')
path_dict_ls_ids_gps = os.path.join(path_dir_built_json, 'dict_ls_ids_gps.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_rls = os.path.join(path_dir_source, 'data_other', 'data_rls.csv')
path_dir_gps_coordinates = os.path.join(path_dir_source, 'data_stations', 'data_gouv_gps')
ls_gps_gouv_files = [r'20130117_ls_coordinates_essence.json',
                     r'20130117_ls_coordinates_diesel.json',
                     r'20130724_ls_coordinates_essence.json',
                     r'20130724_ls_coordinates_diesel.json'] 

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
dict_brands = dec_json(path_dict_brands)
  
# 1/ Load All GPS information
# 2/ Compute distances and build competition data (in relation if needed with master price)

# Load gps collected from prix-carburant.gouv.fr
master_gps_gouv_files = [dec_json(os.path.join(path_dir_gps_coordinates, gps_file))\
                           for gps_file in ls_gps_gouv_files]
master_gps_gouv = master_gps_gouv_files[0]
for gps_gouv_file in master_gps_gouv_files[1:]:
  master_gps_gouv.update(gps_gouv_file)
# Fill master_info with available gps coordinates
ls_gps_gouv_but_no_price = []
for indiv_id, gps_coord in master_gps_gouv.items():
  if indiv_id in master_info.keys():
    master_info[indiv_id]['gps'][4] = gps_coord
  else:
    ls_gps_gouv_but_no_price.append(indiv_id)
print len(ls_gps_gouv_but_no_price), 'ids not in master_price but we have gps coord: recent/duplicates (?)'

# Load gps provided by Ronan (from prix-carburant.gouv.fr but older)
master_rls = open(path_csv_rls, 'r')
master_rls = master_rls.read().split('\n')[1:-1]
master_rls = [row.split(',') for row in master_rls]
master_gps_rls = {}
for row in master_rls:
  if row[25] and row[27] and float(row[25]) != 0 and float(row[27]) != 0:
    master_gps_rls[row[0]] = [float(row[25]), float(row[27])]

# Load gps from geocoding
master_geocoding = dec_json(path_geocoding)
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

# Eliminate [0,0]
del(master_geo['33830004']) # gps is [0,0]
del(master_geo['31170006']) # gps is [0,0]

ls_distance_alert = []
ls_geocoding_alert = []
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
        ls_distance_alert.append((indiv_id, distance, master_geo[indiv_id], gps_geocoding))
    else:
      master_geo[indiv_id] = gps_geocoding
      ls_geocoding_alert.append((indiv_id, gps_geocoding))

ls_gps_not_recorded_info = []
for indiv_id, gps_geocoding in master_geo.iteritems():
  if master_info.get(indiv_id):
    master_info[indiv_id]['gps'][5] = gps_geocoding
  else:
    ls_gps_not_recorded_info.append(indiv_id)
# TODO: Check why... duplicates or?

enc_json(master_info, path_info_output)

# 2/ GET CROSS DISTANCES

## order of pref 4 (website) then 3 (best geocoding info)
#ls_gps = []
#for indiv_id in master_price['ids']:
#  indiv_gps = None
#  if indiv_id in master_info and master_info[indiv_id]['highway'][3] != 1:
#    if master_info[indiv_id]['gps'][4]:
#      indiv_gps = master_info[indiv_id]['gps'][4][0:2]
#    elif master_info[indiv_id]['gps'][3]:
#      indiv_gpsmaster_info[indiv_id]['gps'][3][0:2]
#  ls_gps.append(indiv_gps)
#dict_ls_ids_gps = {'ids': master_price['ids'],
#                  'gps': ls_gps}

## Execution time : c. 13 mn
#ls_ls_cross_distances = get_ls_ls_cross_distances(dict_ls_ids_gps['gps'])
#ar_cross_distances = np.array(ls_ls_cross_distances, dtype = np.float32)
#
##dict_ls_ids_gps = dec_json(path_dict_ls_ids_gps)
##np_arrays_cross_distances = np.load(path_ar_cross_distances)
#
### Comments
### Numpy array: None were converted to np.nan (if dtype = np.float32) which are preserved by tolist()
### np.nan comparison (<, > etc.) always false but if np.nan is True (different from None)
### ls_ls_cross_distances = np_arrays_cross_distances.tolist()
### np_arrays_cross_distances_ma = np.ma.masked_array(np_arrays_cross_distances, np.isnan(np_arrays_cross_distances))
#
## 3/ IDENTIFYING UNACCEPTABLE DISTANCES (SAME LOCATION => UPDATE GPS?)
#
#ls_tup_same_location = []
#for i, list_distances_i in enumerate(ls_ls_cross_distances):
#  for j, distance_i_j in enumerate(ls_ls_cross_distances[i][i+1:], start = i+1):
#    if distance_i_j < np.float32(0.01):
#      ls_tup_same_location.append((i,j))
##      # printing takes a lot of time (?)
##      print dict_ls_ids_gps['ids'][i],\
##        dict_ls_ids_gps['ids'][j],\
##        master_info[dict_ls_ids_gps['ids'][i]]['address'][4],\
##        master_info[dict_ls_ids_gps['ids'][j]]['address'][4]
#print 'Length of tuples same location', len(ls_tup_same_location)
#ls_same_location = list(set([ind for tup_ind in ls_tup_same_location for ind in tup_ind]))

## Replace gps from gouv by gps geocoding if same location and...
#
#ls_use_geocoding_info = []
#ls_no_geocoding_info = []
#for indiv_ind in ls_same_location:
#  indiv_id = dict_ls_ids_gps['ids'][indiv_ind]
#  geocoding_info = get_best_geocoding_info(master_geocoding[indiv_id][1])
#  if (geocoding_info) and\
#     (geocoding_info['status'] == u'OK') and\
#     (u'France' in geocoding_info['results'][0]['formatted_address']):
#    ls_use_geocoding_info.append(indiv_id)
#    print geocoding_info['results'][0]['geometry']['location_type'], indiv_id,\
#          master_info[indiv_id]['address'][-1], geocoding_info['results'][0]['formatted_address']
#  else:
#    ls_no_geocoding_info.append(indiv_ind)
#
#for indiv_id in ls_use_geocoding_info:
#  ind = master_price['ids'].index(indiv_id)
#  dict_ls_ids_gps['gps'][indiv_ind] = get_best_geocoding_info(master_geocoding[indiv_id][1])

# TODO: Check if worth recomputing cross distances?

## 4/ GETTING LISTS OF COMPETITORS (LISTS OF TUPLES ID DISTANCE)
#
#max_competitor_distance = 10
#
#ls_ls_competitors = []
#for i, list_distances_i in enumerate(ls_ls_cross_distances):
#  ls_competitors = []
#  for j, distance_i_j in enumerate(ls_ls_cross_distances[i]):
#    if distance_i_j < np.float32(max_competitor_distance):
#      ls_competitors.append((dict_ls_ids_gps['ids'][j], distance_i_j))
#  ls_ls_competitors.append(ls_competitors)
#
## 5/ GETTING A LIST OF COMPETITOR PAIRS (A LIST OF TUPLES EACH INCLUDING AN ID PAIR TUPLE AND DISTANCE)
#
#ls_tuple_competitors = []
#for i, ls_distances_i in enumerate(ls_ls_cross_distances):
#  for j, distance_i_j in enumerate(ls_ls_cross_distances[i][i+1:], start = i+1):
#    if distance_i_j < np.float32(max_competitor_distance):
#      ls_tuple_competitors.append(\
#        ((dict_ls_ids_gps['ids'][i], dict_ls_ids_gps['ids'][j]), float(distance_i_j)))

# 6/ STORE RESULTS

#np.save(path_ar_cross_distances, ar_cross_distances)
#enc_json(dict_ls_ids_gps, path_dict_ls_ids_gps) 
#
#enc_json(ls_ls_competitors, path_ls_ls_competitors)
#enc_json(ls_tuple_competitors, path_ls_tuple_competitors) 


#ls_ls_competitors = dec_json(path_ls_ls_competitors)
#ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
