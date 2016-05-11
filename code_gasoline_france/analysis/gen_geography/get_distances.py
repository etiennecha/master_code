#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_geocoding import *
from generic_competition import *
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
import time

path_dir_built = os.path.join(path_data,
                              'data_gasoline',
                              'data_built',
                              'data_scraped_2011_2014')
path_dir_built_json = os.path.join(path_dir_built, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')

# ######################
# LOAD DF INFO STATIONS
# ######################

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str})
df_info.set_index('id_station', inplace = True)

print(len(df_info))

df_info = df_info[(df_info['highway'] != 1) &
                  (~pd.isnull(df_info['start']))]

# ######################
# GET CROSS DISTANCES
# ######################

ls_ids, ls_gps = [], []
for id_station, row in df_info.iterrows():
  if not pd.isnull(row['lat']) and not pd.isnull(row['lng']):
    ls_ids.append(id_station)
    ls_gps.append((row['lat'], row['lng']))

# Too slow to add each series to dataframe
start = time.time()
ls_se_distances = []
for i, (id_station, gps_station) in enumerate(zip(ls_ids, ls_gps)[:-1]):
  df_temp = pd.DataFrame(ls_gps[i+1:],
                         columns = ['lat_1', 'lng_1'],
                         index = ls_ids[i+1:])
  df_temp['lat_0'] = gps_station[0]
  df_temp['lng_0'] = gps_station[1]
  df_temp['dist'] = compute_distance_ar(df_temp['lat_0'],
                                        df_temp['lng_0'],
                                        df_temp['lat_1'],
                                        df_temp['lng_1'])
  ls_se_distances.append(df_temp['dist'])
df_distances = pd.concat(ls_se_distances, axis = 1, keys = ls_ids)
# need to add first and last to complete index/columns
# df_distances is then an upper triangular matrix w/ a null diagonal
# except for the fact that the first column in in last position
df_distances.ix[ls_ids[0]] = np.nan
df_distances[ls_ids[-1]] = np.nan
print(u'Length of computation:', time.time() - start)

## Check results
## print(df_distances.ix[ls_ids][0:10])
# print(compute_distance(ls_gps[1], ls_gps[10]))
# print(df_distances.loc[ls_ids[10], ls_ids[1]])

# ###########################
# IDENTIFY SUSPECT DISTANCES 
# ###########################

# Same location => update gps?
ls_pbm_tup_ids = []
for id_station in df_distances.columns:
  ls_pbm_ids = list(df_distances.index[df_distances[id_station] < 0.01])
  for id_station_alt in ls_pbm_ids:
    ls_pbm_tup_ids.append((id_station, id_station_alt))

## Inspect very short distance pairs
## df_info.drop(['poly'], axis = 1, inplace = True)
#lsd0 = ['name', 'adr_street', 'adr_zip', 'adr_city',
#        'brand_0', 'brand_1', 'start', 'end', 'lat', 'lng']
#for tup_ids in ls_pbm_tup_ids[0:10]:
#  print()
#  print(df_info.ix[list(tup_ids)][lsd0].to_string())
## One potential duplicated detected: 86000018, 86000021

# #######
# OUPUT
# #######

comp_radius = 10
ls_close_pairs = [] # ls of tup with two ids and distance inbetween
dict_ls_close = {}  # dict of ls of comp id and distance for each station
for id_station in df_distances.columns:
  ls_comp_ids = list(df_distances.index[df_distances[id_station] <= comp_radius])
  for id_station_alt in ls_comp_ids:
    dist = df_distances.loc[id_station_alt, id_station]
    ls_close_pairs.append((id_station, id_station_alt, dist))
    dict_ls_close.setdefault(id_station, []).append((id_station_alt, dist))
    dict_ls_close.setdefault(id_station_alt, []).append((id_station, dist))

# Add those with no competitors within 10km
for id_station in ls_ids:
  dict_ls_close.setdefault(id_station, [])

# Sort each ls_comp on distance
dict_ls_close = {k: sorted(v, key=lambda tup: tup[1]) for k,v in dict_ls_close.items()}

# takes more time to store (load?) than to build (cur. 353Mo)
df_distances.to_csv(os.path.join(path_dir_built_csv, 'df_distances.csv'),
                    index_label = 'id_station',
                    float_format= '%.2f',
                    encoding = 'utf-8')

enc_json(ls_close_pairs, os.path.join(path_dir_built_json,
                                      'ls_close_pairs.json'))

enc_json(dict_ls_close, os.path.join(path_dir_built_json,
                                     'dict_ls_close.json'))

print(u'Found and saved {:d} close pairs'.format(len(ls_close_pairs)))
print(u'Found and saved neighbours for {:d} stations'.format(len(dict_ls_close)))
