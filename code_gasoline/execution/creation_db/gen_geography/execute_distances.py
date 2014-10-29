#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_geocoding import *
from generic_competition import *
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
import time

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

path_ar_cross_distances = os.path.join(path_dir_built_json, 'ar_cross_distances.npy')
path_dict_ls_ids_gps = os.path.join(path_dir_built_json, 'dict_ls_ids_gps.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')

# ######################
# LOAD DF INFO STATIONS
# ######################

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info.csv'),
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

print len(df_info)

df_info = df_info[(df_info['highway'] != 1) &
                  (~pd.isnull(df_info['start']))]

# ######################
# LOAD DF GEOFLA COM
# ######################

# excludes Corsica
x1 = -5.
x2 = 9.
y1 = 42
y2 = 52.

# Lambert conformal for France (as suggested by IGN... check WGS84 though?)
m_fra = Basemap(resolution='i',
                projection='lcc',
                ellps = 'WGS84',
                lat_1 = 44.,
                lat_2 = 49.,
                lat_0 = 46.5,
                lon_0 = 3,
                llcrnrlat=y1,
                urcrnrlat=y2,
                llcrnrlon=x1,
                urcrnrlon=x2)

path_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')
m_fra.readshapefile(path_com, 'communes_fr', color = 'none', zorder=2)
df_com = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.communes_fr],
                       'x_center' : [d['X_CENTROID'] for d in m_fra.communes_fr_info],
                       'y_center' : [d['Y_CENTROID'] for d in m_fra.communes_fr_info],
                       'x_cl' : [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl' : [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'code_insee' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'commune' : [d['NOM_COMM'] for d in m_fra.communes_fr_info]})

def convert_from_ign(x_l_93_ign, y_l_93_ign):
  x = x_l_93_ign * 100 - 700000 + m_fra(3, 46.5)[0] 
  y = y_l_93_ign * 100 - 6600000 + m_fra(3, 46.5)[1]
  x, y = m_fra(x, y, inverse = True)
  return x, y

df_com[['lng_ct', 'lat_ct']] = df_com[['x_center', 'y_center']].apply(\
                                 lambda x: convert_from_ign(x['x_center'],\
                                                            x['y_center']),\
                                 axis = 1)

df_com[['lng_cl', 'lat_cl']] = df_com[['x_cl', 'y_cl']].apply(\
                                 lambda x: convert_from_ign(x['x_cl'],\
                                                            x['y_cl']),\
                                 axis = 1)

# #############################
# GET CROSS DISTANCES AND COMP
# #############################

# 1/ PICK BEST GPS

df_info['id_station']= df_info.index
df_com.drop_duplicates(subset = 'code_insee', inplace = True)
df_info = pd.merge(df_info,
                   df_com,
                   left_on = 'ci_ardt_1',
                   right_on = 'code_insee',
                   how = 'left')

df_info['lat_best'] = df_info['lat_gov_1']
df_info['lng_best'] = df_info['lng_gov_1']
df_info.loc[pd.isnull(df_info['lat_best']), 'lat_best'] = df_info['lat_gov_0']
df_info.loc[pd.isnull(df_info['lng_best']), 'lng_best'] = df_info['lng_gov_0']
df_info.loc[pd.isnull(df_info['lat_best']), 'lat_best'] = df_info['lat_rls']
df_info.loc[pd.isnull(df_info['lng_best']), 'lng_best'] = df_info['lng_rls']

df_info['dist_cl'] = compute_distance_ar(df_info['lat_best'],
                                         df_info['lng_best'],
                                         df_info['lat_ct'],
                                         df_info['lng_ct'])

# If dist > 20, wrong coordinates... try geocoding coordinates
df_info.loc[df_info['dist_cl'] > 20, 'lat_best'] = df_info['lat_gc']
df_info.loc[df_info['dist_cl'] > 20, 'lng_best'] = df_info['lng_gc']

df_info['dist_cl'] = compute_distance_ar(df_info['lat_best'],
                                         df_info['lng_best'],
                                         df_info['lat_ct'],
                                         df_info['lng_ct'])

df_info['dist_gc'] = compute_distance_ar(df_info['lat_best'],
                                         df_info['lng_best'],
                                         df_info['lat_gc'],
                                         df_info['lng_gc'])

ls_disp_info = ['id_station', 'name', 'adr_street', 'commune',
                'lat_best', 'lng_best',
                'dist_cl', 'dist_gc', 'quality']

#print '\nNb stations too far to commune center:', len(df_info[(df_info['dist_cl'] > 20)])
#print '\n', df_info[ls_disp_info][(df_info['dist_cl'] > 20)].to_string(index=False)

#print '\nNb stations close to commune center:', len(df_info[(df_info['dist_cl'] < 0.10)])
#print '\n', df_info[ls_disp_info][(df_info['dist_cl'] < 0.10)].to_string(index=False)

# If too close but got ROOFTOP OR RANGE_INTERPOLATED : SWITCH TO GC
df_info.loc[(df_info['dist_cl'] < 0.1) &\
            (df_info['quality'].isin(['ROOFTOP',
                                      'RANGE_INTERPOLATED'])), 'lat_best'] = df_info['lat_gc']
df_info.loc[(df_info['dist_cl'] < 0.1) &\
            ((df_info['quality'] == 'ROOFTOP') |\
             (df_info['quality'] == 'RANGE_INTERPOLATED')), 'lng_best'] = df_info['lng_gc']

#print '\nNb stations still close to commune center:', len(df_info[(df_info['dist_cl'] < 0.10)])
#print '\n', df_info[ls_disp_info][(df_info['dist_cl'] < 0.10) &\
#                                  (df_info['quality'] != 'ROOFTOP') &\
#                                  (df_info['quality'] != 'RANGE_INTERPOLATED')].\
#                                        to_string(index=False)
## Try to use Zagaz coordinates for those (see if matched!)

# 2/ GET CROSS DISTANCES

df_info.set_index('id_station', inplace = True)
ls_ids, ls_gps = [], []
for id_station, row in df_info.iterrows():
  if not pd.isnull(row['lat_best']) and not pd.isnull(row['lng_best']):
    ls_ids.append(id_station)
    ls_gps.append((row['lat_best'], row['lng_best']))

# Too slow to add each series to dataframe
start = time.time()
ls_se_distances = []
for i, (id_station, gps_station) in enumerate(zip(ls_ids, ls_gps)[:-1]):
  df_temp = pd.DataFrame(ls_gps[i+1:], columns = ['lat_1', 'lng_1'], index = ls_ids[i+1:])
  df_temp['lat_0'] = gps_station[0]
  df_temp['lng_0'] = gps_station[1]
  df_temp['dist'] = compute_distance_ar(df_temp['lat_0'],
                                        df_temp['lng_0'],
                                        df_temp['lat_1'],
                                        df_temp['lng_1'])
  ls_se_distances.append(df_temp['dist'])
df_distances = pd.concat(ls_se_distances, axis = 1, keys = ls_ids)
print time.time() - start

## Check results
## print df_distances.ix[ls_ids][0:10]
# print compute_distance(ls_gps[1], ls_gps[10])
# print df_distances.loc[ls_ids[10], ls_ids[1]]

## STORE df_distances (dataframe, numpy array?)
#dict_ls_ids_gps = dec_json(path_dict_ls_ids_gps)
#np_arrays_cross_distances = np.load(path_ar_cross_distances)

# 3/ IDENTIFYING UNACCEPTABLE DISTANCES (SAME LOCATION => UPDATE GPS?)

ls_pbm_tup_ids = []
for id_station in df_distances.columns:
  ls_pbm_ids = list(df_distances.index[df_distances[id_station] < 0.01])
  for id_station_alt in ls_pbm_ids:
    ls_pbm_tup_ids.append((id_station, id_station_alt))

# 4/ GET COMPETITION FILES

comp_radius = 10
ls_comp_pairs = [] # ls of tup with two ids and distance inbetween
dict_ls_comp = {}  # dict of ls of comp id and distance for each station
for id_station in df_distances.columns:
  ls_comp_ids = list(df_distances.index[df_distances[id_station] < comp_radius])
  for id_station_alt in ls_comp_ids:
    dist = df_distances.loc[id_station_alt, id_station]
    ls_comp_pairs.append((id_station, id_station_alt, dist))
    dict_ls_comp.setdefault(id_station, []).append((id_station_alt, dist))
    dict_ls_comp.setdefault(id_station_alt, []).append((id_station, dist))

# 5/ STORE FILES

# takes more time to store (load?) than to build (cur. 353Mo)
df_distances.to_csv(os.path.join(path_dir_built_csv, 'df_distances.csv'),
                    index_label = 'id_station',
                    float_format= '%.2f',
                    encoding = 'utf-8')

enc_json(ls_comp_pairs, os.path.join(path_dir_built_json,
                                     'ls_comp_pairs.json'))

enc_json(dict_ls_comp, os.path.join(path_dir_built_json,
                                    'dict_ls_comp.json'))

## DEPRECATED ?
#np.save(path_ar_cross_distances, ar_cross_distances)
#enc_json(dict_ls_ids_gps, path_dict_ls_ids_gps) 
#enc_json(ls_ls_competitors, path_ls_ls_competitors)
#enc_json(ls_tuple_competitors, path_ls_tuple_competitors) 
#ls_ls_competitors = dec_json(path_ls_ls_competitors)
#ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
