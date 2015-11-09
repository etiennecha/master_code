#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
import time

path_built = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_lsa')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_built_json = os.path.join(path_built,
                                    'data_json')

path_built_comp_csv = os.path.join(path_built_csv,
                                   '201407_competition')

path_built_comp_json = os.path.join(path_built_json,
                                    '201407_competition')

# ######################
# LOAD DATA
# ######################

df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa_active.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'UTF-8')

df_lsa = df_lsa[(~df_lsa['latitude'].isnull()) &
                (~df_lsa['longitude'].isnull())]

df_lsa.rename(columns = {'latitude' : 'lat',
                         'longitude' : 'lng'},
              inplace = True)

df_lsa.set_index('id_lsa', inplace = True)

dict_df_lsa = {}
dict_df_lsa['hsx'] = df_lsa.copy()
dict_df_lsa['hs'] = df_lsa[df_lsa['type_alt'].isin(['H', 'S'])].copy()

# ######################
# GET CROSS DISTANCES
# ######################

for lsa_types, df_lsa in  dict_df_lsa.items():
  
  print u'\nGet distances for stores:', lsa_types
  ls_ids, ls_gps = [], []
  for id_lsa, row in df_lsa.iterrows():
    if not pd.isnull(row['lat']) and not pd.isnull(row['lng']):
      ls_ids.append(id_lsa)
      ls_gps.append((row['lat'], row['lng']))
  
  # Too slow to add each series to dataframe
  start = time.time()
  ls_se_distances = []
  for i, (id_lsa, gps_station) in enumerate(zip(ls_ids, ls_gps)[:-1]):
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
  df_distances.ix[ls_ids[0]] = np.nan
  df_distances[ls_ids[-1]] = np.nan
  print u'\nLength of computation:', time.time() - start
  
  ## Check results
  ## print df_distances.ix[ls_ids][0:10]
  # print compute_distance(ls_gps[1], ls_gps[10])
  # print df_distances.loc[ls_ids[10], ls_ids[1]]
  
  # ###########################
  # IDENTIFY SUSPECT DISTANCES 
  # ###########################
  
  # Same location => update gps?
  ls_pbm_tup_ids = []
  for id_lsa in df_distances.columns:
    ls_pbm_ids = list(df_distances.index[df_distances[id_lsa] < 0.01])
    for id_lsa_alt in ls_pbm_ids:
      ls_pbm_tup_ids.append((id_lsa, id_lsa_alt))
  
  ## Inspect very short distance pairs
  ## df_lsa.drop(['poly'], axis = 1, inplace = True)
  #lsd0 = ['enseigne', 'adresse1', 'ville']
  #for tup_ids in ls_pbm_tup_ids[0:10]:
  #  print '\n', df_lsa.ix[list(tup_ids)][lsd0].to_string()
  
  # #######
  # OUPUT
  # #######
  
  comp_radius = 25
  ls_close_pairs = [] # ls of tup with two ids and distance inbetween
  dict_ls_close = {}  # dict of ls of comp id and distance for each station
  for id_lsa in df_distances.columns:
    ls_comp_ids = list(df_distances.index[df_distances[id_lsa] <= comp_radius])
    for id_lsa_alt in ls_comp_ids:
      dist = df_distances.loc[id_lsa_alt, id_lsa]
      ls_close_pairs.append((id_lsa, id_lsa_alt, dist))
      dict_ls_close.setdefault(id_lsa, []).append((id_lsa_alt, dist))
      dict_ls_close.setdefault(id_lsa_alt, []).append((id_lsa, dist))
  
  # Sort each ls_comp on distance
  dict_ls_close = {k: sorted(v, key=lambda tup: tup[1]) for k,v in dict_ls_close.items()}
  
  # takes more time to store (load?) than to build (cur. 353Mo)
  df_distances.to_csv(os.path.join(path_built_comp_csv,
                                   'df_distances_{:s}.csv'.format(lsa_types)),
                      index_label = 'id_lsa',
                      float_format= '%.2f',
                      encoding = 'utf-8')
  
  enc_json(ls_close_pairs, os.path.join(path_built_comp_json,
                                        'ls_close_pairs_{:s}.json'.format(lsa_types)))
  
  enc_json(dict_ls_close, os.path.join(path_built_comp_json,
                                       'dict_ls_close_{:s}.json'.format(lsa_types)))
  
  print u'\nFound and saved {:d} close pairs'.format(len(ls_close_pairs))
  print u'\nFound and saved neighbours for {:d} stations'.format(len(dict_ls_close))
