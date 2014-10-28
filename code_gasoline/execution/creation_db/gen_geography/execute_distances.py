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

df_info = df_info[df_info['highway'] != 1]

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

# ######################
# LOAD MERGE
# ######################

df_info['id_station']= df_info.index
df_com.drop_duplicates(subset = 'code_insee', inplace = True)
df_info = pd.merge(df_info,
                   df_com,
                   left_on = 'ci_ardt_1',
                   right_on = 'code_insee',
                   how = 'left')

df_info['lat_gov'] = df_info['gps_lat_gov_1']
df_info['lng_gov'] = df_info['gps_lng_gov_1']
df_info.loc[pd.isnull(df_info['lat_gov']), 'lat_gov'] = df_info['gps_lat_gov_0']
df_info.loc[pd.isnull(df_info['lng_gov']), 'lng_gov'] = df_info['gps_lng_gov_0']
df_info.loc[pd.isnull(df_info['lat_gov']), 'lat_gov'] = df_info['gps_lat_rls']
df_info.loc[pd.isnull(df_info['lng_gov']), 'lng_gov'] = df_info['gps_lng_rls']

df_info['dist_cl'] = compute_distance_ar(df_info['lat_gov'],
                                         df_info['lng_gov'],
                                         df_info['lat_ct'],
                                         df_info['lng_ct'])

# If dist > 20, wrong coordinates... try geocoding coordinates
df_info.loc[df_info['dist_cl'] > 20, 'lat_gov'] = df_info['lat']
df_info.loc[df_info['dist_cl'] > 20, 'lng_gov'] = df_info['lng']

df_info['dist_cl'] = compute_distance_ar(df_info['lat_gov'],
                                         df_info['lng_gov'],
                                         df_info['lat_ct'],
                                         df_info['lng_ct'])

df_info['dist_gc'] = compute_distance_ar(df_info['lat_gov'],
                                         df_info['lng_gov'],
                                         df_info['lat'],
                                         df_info['lng'])


ls_disp_columns = ['id_station', 'name', 'adr_street', 'commune',
                   'lat_gov', 'lng_gov',
                   'dist_cl', 'dist_gc', 'quality']

print '\nNb stations too far to commune center:', len(df_info[(df_info['dist_cl'] > 20)])
print '\n', df_info[ls_disp_columns][(df_info['dist_cl'] > 20)].to_string(index=False)

print '\nNb stations close to commune center:', len(df_info[(df_info['dist_cl'] < 0.10)])
print '\n', df_info[ls_disp_columns][(df_info['dist_cl'] < 0.10)].to_string(index=False)

# If too close but got ROOFTOP OR RANGE_INTERPOLATED : SWITCH TO GC
df_info.loc[(df_info['dist_cl'] < 0.1) &\
            (df_info['quality'].isin(['ROOFTOP',
                                      'RANGE_INTERPOLATED'])), 'lat_gov'] = df_info['lat']
df_info.loc[(df_info['dist_cl'] < 0.1) &\
            ((df_info['quality'] == 'ROOFTOP') |\
             (df_info['quality'] == 'RANGE_INTERPOLATED')), 'lng_gov'] = df_info['lng']

print '\nNb stations still close to commune center:', len(df_info[(df_info['dist_cl'] < 0.10)])
print '\n', df_info[ls_disp_columns][(df_info['dist_cl'] < 0.10) &\
                                     (df_info['quality'] != 'ROOFTOP') &\
                                     (df_info['quality'] != 'RANGE_INTERPOLATED')].\
                                        to_string(index=False)
# Try to use Zagaz coordinates for those (see if matched!)



# 2/ GET CROSS DISTANCES

# Check those with missing gps coordinates
df_info.set_index('id_station', inplace = True)

# order of pref 4 (website) then 3 (best geocoding info)
ls_ids, ls_gps = [], []
for id_station, row in df_info.iterrows():
  if not pd.isnull(row['lat_gov']) and not pd.isnull(row['lng_gov']):
    ls_ids.append(id_station)
    ls_gps.append((row['lat_gov'], row['lng_gov']))

### Execution time : c. 13 mn
#ls_ls_cross_distances = get_ls_ls_cross_distances(dict_ls_ids_gps['gps'])
#ar_cross_distances = np.array(ls_ls_cross_distances, dtype = np.float32)
#
##dict_ls_ids_gps = dec_json(path_dict_ls_ids_gps)
##np_arrays_cross_distances = np.load(path_ar_cross_distances)
#
### Numpy array: None were converted to np.nan (if dtype = np.float32) which are preserved by tolist()
### np.nan comparison (<, > etc.) always false but if np.nan is True (different from None)
### ls_ls_cross_distances = np_arrays_cross_distances.tolist()
### np_arrays_cross_distances_ma = np.ma.masked_array(np_arrays_cross_distances,
###                                                   np.isnan(np_arrays_cross_distances))
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
#
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
#
## todo: Check if worth recomputing cross distances?
#
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
#
## 6/ STORE RESULTS
#
##np.save(path_ar_cross_distances, ar_cross_distances)
##enc_json(dict_ls_ids_gps, path_dict_ls_ids_gps) 
##
##enc_json(ls_ls_competitors, path_ls_ls_competitors)
##enc_json(ls_tuple_competitors, path_ls_tuple_competitors) 
#
#
##ls_ls_competitors = dec_json(path_ls_ls_competitors)
##ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
