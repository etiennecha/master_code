import json
import math
import urllib
import numpy as np

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

machine_path = r'C:\Users\etna\Desktop\Code\Gasoline'
info_folder = r'data_stations\data_info_stations_prix_carb'
price_folder = r'data_prices'
geocoding_folder = r'geolocalisation\geocoding'

master_info_gas_stations = dec_json(machine_path + r'\\' + info_folder + r'\\current_master_info')
master_price_gas_stations = dec_json(machine_path + r'\\' + price_folder + r'\\current_master_price')

def get_id(rank, master):
  return master[3][rank]

def get_ranks(id, master):
  return master[2][id]['rank']

def unique(items):
  """
  keep only unique elements in a list
  """
  found = set()
  keep = []
  for item in items:
    if item not in found:
      found.add(item)
      keep.append(item)
  return keep
  
def print_list_of_lists(list_of_lists, nb_columns):
  list_of_list_groups = [list_of_lists[i:i+nb_columns] for i in range(0, len(list_of_lists), nb_columns)]
  for list_items in list_of_list_groups:
    tuple_lists = zip(*list_items)
    col_width = max(len(item) for row in tuple_lists for item in row if item is not None) + 2
    for row in tuple_lists:
      row = tuple('.' if x is None else x for x in row)
      print "".join(item.ljust(col_width) for item in row)
    print '-'*100

def print_list_of_lists_from_ranks(list_of_ranks, master_price, nb_columns):
  list_of_id_groups = [list_of_ranks[i:i + nb_columns] for i in range(0, len(list_of_ranks), nb_columns)]
  list_of_lists = [master_price['list_indiv_prices'][i] for i in list_of_ranks]
  list_of_list_groups = [list_of_lists[i:i + nb_columns] for i in range(0, len(list_of_lists), nb_columns)]
  for k in range(0,len(list_of_list_groups)):
    id_list = list_of_id_groups[k]
    col_width_1 = max(len(str(id)) for id in id_list) + 2
    tuple_lists = zip(*list_of_list_groups[k])
    col_width_2 = max(len(str(item)) for row in tuple_lists for item in row if item is not None) + 2
    col_width = max(col_width_1, col_width_2)
    print "".join(str(item).rjust(col_width) for item in id_list)
    for row in tuple_lists:
      row = tuple('.' if x is None else x for x in row)
      print "".join(str(item).rjust(col_width) for item in row)
    print '-'*100

def compute_distance(coordinates_A, coordinates_B):
  d_lat = math.radians(float(coordinates_B[0])-float(coordinates_A[0]))
  d_lon = math.radians(float(coordinates_B[1])-float(coordinates_A[1]))
  lat_1 = math.radians(float(coordinates_A[0]))
  lat_2 = math.radians(float(coordinates_B[0]))
  a = math.sin(d_lat/2.0) * math.sin(d_lat/2.0) + math.sin(d_lon/2.0) * math.sin(d_lon/2.0) * math.cos(lat_1) * math.cos(lat_2);
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a));
  distance = 6371 * c
  return round(distance, 2)

def print_dict_stat_des(dict_stat_des):
  for key, content in dict_stat_des.iteritems():
    print key, len(content)
  
def get_ids_stat_des_geocoding(list_ids, master_info, period):
  score_stats =  {'ROOFTOP' : [],
                  'RANGE_INTERPOLATED' : [],
                  'GEOMETRIC_CENTER' : [],
                  'APPROXIMATE' : [],
                  'NONE' : []}
  for id in list_ids:
    if master_info[id]['gps'][period] is not None and master_info[id]['highway'][3] != 1:
      score_stats[master_info[id]['gps'][period][2]].append(id)
    else:
      score_stats['NONE'].append(id)
  print_dict_stat_des(score_stats)
  return score_stats

def get_stat_des_price_vs_info(master_price, master_info):
  """
  Compare individuals present in price vs. info masters
  Particular interest for gas statations whose price is given at last period
  Also the coordinates from site are considered most valuable
  """
  list_ids_last_period = []
  list_ids_in_price_not_in_info = []
  list_ids_last_period_not_in_info = []
  list_ids_last_period_with_gps_from_site = []
  for id, info in master_price['dict_general_info'].iteritems():
    if master_price['list_indiv_prices'][info['rank']][len(master_price['list_dates'])-1] is not None:
      list_ids_last_period.append(id)
    if master_info.get(id) is not None:
      if master_price['list_indiv_prices'][info['rank']][len(master_price['list_dates'])-1] is not None and master_info[id]['gps'][4] is not None:
        list_ids_last_period_with_gps_from_site.append(id)
    else:
      list_ids_in_price_not_in_info.append(id)
      # print id, info
      if master_price_gas_stations['list_indiv_prices'][info['rank']][len(master_price['list_dates'])-1]is not None:
        list_ids_last_period_not_in_info.append(id)
  dict_results = {'list_ids_last_period' : list_ids_last_period,
                  'list_ids_in_price_not_in_info' : list_ids_in_price_not_in_info,
                  'list_ids_last_period_not_in_info': list_ids_last_period_not_in_info,
                  'list_ids_last_period_with_gps_from_site' : list_ids_last_period_with_gps_from_site}
  print_dict_stat_des(dict_results)
  return dict_results

def confront_geocoding_vs_website(master_info, gps_geocoding_index, gps_website_index):
  list_distances = []
  for id, info in master_info.iteritems():
    if info['gps'][gps_geocoding_index] is not None and info['gps'][gps_website_index] is not None:
      list_distances.append((id, compute_distance(info['gps'][gps_geocoding_index][0:2], info['gps'][gps_website_index][0:2])))
    else:
      list_distances.append((id, None))
  print len([elt for elt in list_distances if elt[1] is not None]), 'cross distances could be computed (both not none)'
  print len([elt for elt in list_distances if elt[1] is not None and elt[1] > 5]), 'cross distances computed > 5 km'
  list_ids_problematic_gps = []
  for id_distance in list_distances:
    if id_distance[1] is None or id_distance[1] > 5:
      list_ids_problematic_gps.append(id_distance[0])
  dict_results = {'list_distances' : list_distances,
                  'list_ids_problematic_gps' : list_ids_problematic_gps}
  print_dict_stat_des(dict_results)
  return dict_results

def compute_cross_distances(master_best_gps):
  distance_matrix = np.matrix([[None for elt in master_best_gps['list_gps']] for elt in master_best_gps['list_gps']], dtype = np.float32)
  for ind_1 in range(0,len(master_best_gps['list_gps'])):
    for ind_2 in range(0, len(master_best_gps['list_gps'])):
      if master_best_gps['list_gps'][ind_1] is not None and master_best_gps['list_gps'][ind_2] is not None and ind_1!= ind_2:
        distance_matrix[ind_1, ind_2] = compute_distance(master_best_gps['list_gps'][ind_1], master_best_gps['list_gps'][ind_2])
  return [master_best_gps, distance_matrix]

# FIRST STEP: IMPROVING GPS INFORMATION

print '\n Stats des: ids in master price vs. ids in master info and gps coordinates'
stat_des_price_vs_info = get_stat_des_price_vs_info(master_price_gas_stations, master_info_gas_stations)
print '\n Stats des: scores from [0]th geocoding'
stat_des_geocoding_1 = get_ids_stat_des_geocoding(master_info_gas_stations.keys(), master_info_gas_stations, 0)
print '\n Stats des: scores from [1]st geocoding'
stat_des_geocoding_2 = get_ids_stat_des_geocoding(master_info_gas_stations.keys(), master_info_gas_stations, 1)

print '\n Stats des: comparison from [1]st geocoding (the best) vs. website gps coordinates'
stat_des_geocoding_vs_website_1 = confront_geocoding_vs_website(master_info_gas_stations, 1, 4)

"""
# One-off: encode and use the geolocalisation script:
dico_ids_bad_gps = {}
for id in stat_des_geocoding_vs_website_1['list_ids_problematic_gps']:
  if master_info_gas_stations[id]['address'][4] is not None:
    dico_ids_bad_gps[id] = {'address' : master_info_gas_stations[id]['address'][4]}
  else:
    print id
enc_stock_json(dico_ids_bad_gps, machine_path + r'\\' + geocoding_folder + r'\\current_master_geocoding')
"""

# Reintegrate gps coordinates obtained from geocoding in master
# We will store in ['gps'][3] the final coordinates to be used
dico_ids_newly_geocoded = dec_json (machine_path + r'\\' + geocoding_folder + r'\\current_master_geocoding')
list_na_reasons = []
for id, info in dico_ids_newly_geocoded.iteritems():
  if info['gps_geocoding']['status'] == u'OK':
    lat = info['gps_geocoding']['results'][0]['geometry']['location']['lat']
    lng = info['gps_geocoding']['results'][0]['geometry']['location']['lng']
    score = info['gps_geocoding']['results'][0]['geometry']['location_type']
    master_info_gas_stations[id]['gps'][2] = [lat, lng, score]
  else:
    list_na_reasons.append((id, info['gps_geocoding']['status']))
for id, info in master_info_gas_stations.iteritems():
  if info['gps'][2] is None:
    info['gps'][3] = info['gps'][1]
  else:
    info['gps'][3] = info['gps'][2]

print '\n Stats des: scores from [3]rd geocoding'
stat_des_geocoding_1 = get_ids_stat_des_geocoding(master_info_gas_stations.keys(), master_info_gas_stations, 3)
print '\n Stats des: comparison from [3]rd geocoding (the new best) vs. website gps coordinates'
stat_des_geocoding_vs_website_1 = confront_geocoding_vs_website(master_info_gas_stations, 3, 4)

# SECOND STEP: GETTING CROSS DISTANCES

list_ids = master_price_gas_stations['list_ids']
list_gps = []
for id in list_ids:
  if id in master_info_gas_stations and master_info_gas_stations[id]['highway'][3] != 1:
    if master_info_gas_stations[id]['gps'][4] is not None:
      list_gps.append(master_info_gas_stations[id]['gps'][4][0:2])
    elif master_info_gas_stations[id]['gps'][3] is not None:
      list_gps.append(master_info_gas_stations[id]['gps'][3][0:2])
    else:
      list_gps.append(None)
  else:
    list_gps.append(None)
dict_best_gps = {'list_ids': master_price_gas_stations['list_ids'],
                 'list_gps': list_gps}

"""
Execution time: c. 15 minutes
cross_distances = compute_cross_distances(dict_best_gps)
np.save(machine_path + r'\\' + info_folder + r'\\cross_distances_matrix.npy', cross_distances[1])
enc_stock_json(cross_distances[0], machine_path + r'\\' + info_folder + r'\\cross_distances_dict')
"""

cross_distances_dict = dec_json(machine_path + r'\\' + info_folder + r'\\cross_distances_dict')
cross_distances_matrix = np.load(machine_path + r'\\' + info_folder + r'\\cross_distances_matrix.npy')

# THIRD STEP: IDENTIFYING UNACCEPTABLE DISTANCES (SAME LOCATION... pbms)
# must be uncommented for 2 following points to be (re)doable

"""
list_same_location = []
for i in range(0, len(cross_distances_matrix[:,0])):
  for j in range(i, len(cross_distances_matrix[0,:])):
    if not np.isnan(cross_distances_matrix[i,j]) and cross_distances_matrix[i,j] < np.float32(0.01):
      list_same_location.append((i,j))
list_drop = []
for (i,j) in list_same_location:
  list_drop.append(i)
  list_drop.append(j)
  try:
    print master_info_gas_stations[master_price_gas_stations['list_ids'][i]]['address'][4], master_info_gas_stations[master_price_gas_stations['list_ids'][j]]['address'][4]
  except:
    print i,j
list_drop = unique(list_drop)
"""

# FOURTH STEP: GETTING LISTS OF COMPETITORS (LISTS OF TUPLES ID DISTANCE)

"""
list_competitor_lists = []
for i in range(0, len(cross_distances_matrix[:,0])):
  if i not in list_drop:
    competitor_list = []
    for j in range(0, len(cross_distances_matrix[0,:])):
      if not np.isnan(cross_distances_matrix[i,j]) and cross_distances_matrix[i,j] < np.float32(10) and j not in list_drop:
        competitor_list.append((cross_distances_dict['list_ids'][j], float(cross_distances_matrix[i,j])))
  else:
    competitor_list = None
  list_competitor_lists.append(competitor_list)
enc_stock_json(list_competitor_lists, machine_path + r'\\' + info_folder + r'\\list_competitor_lists')
"""

list_competitor_lists = dec_json(machine_path + r'\\' + info_folder + r'\\list_competitor_lists')

# FIFTH STEP: GETTING A LIST OF COMPETITOR PAIRS (A LIST OF TUPLES EACH INCLUDING AN ID PAIR TUPLE AND DISTANCE)

"""
list_competitor_pairs = []
for i in range(0, len(cross_distances_matrix[:,0])):
  if i not in list_drop:
    for j in range(i, len(cross_distances_matrix[0,:])):
      if not np.isnan(cross_distances_matrix[i,j]) and cross_distances_matrix[i,j] < np.float32(10) and j not in list_drop:
        list_competitor_pairs.append(((cross_distances_dict['list_ids'][i],cross_distances_dict['list_ids'][j]), float(cross_distances_matrix[i,j])))
enc_stock_json(list_competitor_pairs, machine_path + r'\\' + info_folder + r'\\list_competitor_pairs')      
"""

list_competitor_pairs = dec_json(machine_path + r'\\' + info_folder + r'\\list_competitor_pairs')

# TO DO:
# Check for each group (small distance) if a disappearance + an appearance occurs (print some info on both then)
# Use address to check we have the same station
# Check for highway gas stations... info used so far for this may be a bit outdated