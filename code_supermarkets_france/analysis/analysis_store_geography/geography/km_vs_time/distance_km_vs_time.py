#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
import matplotlib.pyplot as plt
import urllib2

# Run with ubuntu hence path fixed
path_data = '/home/etna/Etienne/sf_Data'

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                              'data_csv')
path_built_json = os.path.join(path_built,
                               'data_json')
path_built_graphs = os.path.join(path_built,
                                 'data_graphs')

path_insee = os.path.join(path_data, 'data_insee')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

def convert_to_ign(x, y):
  x_l_93_ign = (m_fra(x, y)[0] + 700000 - m_fra(3, 46.5)[0])/100.0
  y_l_93_ign = (m_fra(x, y)[1] + 6600000 - m_fra(3, 46.5)[1])/100.0
  return x_l_93_ign, y_l_93_ign

def convert_from_ign(x_l_93_ign, y_l_93_ign):
  x = x_l_93_ign * 100 - 700000 + m_fra(3, 46.5)[0] 
  y = y_l_93_ign * 100 - 6600000 + m_fra(3, 46.5)[1]
  x, y = m_fra(x, y, inverse = True)
  return x, y

# ##############
# LOAD LSA data
# ##############

df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa_active.csv'),
                     dtype = {u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'UTF-8')

df_lsa = df_lsa[(~pd.isnull(df_lsa['latitude'])) &\
                (~pd.isnull(df_lsa['longitude']))].copy()

lsd0 = [u'enseigne',
        u'adresse1',
        u'c_postal',
        u'ville'] #, u'Latitude', u'Longitude']

# ###############
# LOAD COMMUNES
# ###############

df_com_insee = pd.read_csv(os.path.join(path_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'UTF-8')
df_com_insee.set_index('CODGEO', inplace = True)

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

path_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')

m_fra.readshapefile(path_dpt, 'departements_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_com, 'communes_fr', color = 'none', zorder=2)

df_com = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.communes_fr],
                       'x_center' : [d['X_CENTROID'] for d in m_fra.communes_fr_info],
                       'y_center' : [d['Y_CENTROID'] for d in m_fra.communes_fr_info],
                       'x_cl' : [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl' : [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'code_insee' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'commune' : [d['NOM_COMM'] for d in m_fra.communes_fr_info],
                       'com_surf' : [d['SUPERFICIE'] for d in m_fra.communes_fr_info],
                       'pop' : [d['POPULATION'] for d in m_fra.communes_fr_info]})

# Drop Corsica (make sure dropped in LSA as well?)
df_com['dpt'] = df_com['code_insee'].str.slice(stop=-3)
df_com = df_com[~df_com['dpt'].isin(['2A', '2B'])]

# Keep only one line per commune (several polygons for some)
df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)
df_com.sort(columns = ['code_insee', 'poly_area'],
            ascending = False,
            inplace = True)

df_com.drop_duplicates(subset = 'code_insee', inplace = True)

#print u'\nTest with commune', df_com['commune'].iloc[0]
#x_test, y_test = df_com['x_center'].iloc[0], df_com['y_center'].iloc[0]
#print convert_from_ign(x_test, y_test)

df_com[['lng_ct', 'lat_ct']] = df_com[['x_center', 'y_center']].apply(\
                                 lambda x: convert_from_ign(x['x_center'],\
                                                            x['y_center']),\
                                 axis = 1)

df_com[['lng_cl', 'lat_cl']] = df_com[['x_cl', 'y_cl']].apply(\
                                 lambda x: convert_from_ign(x['x_cl'],\
                                                            x['y_cl']),\
                                 axis = 1)

# Round gps coord
for col in ['lng_ct', 'lat_ct', 'lng_cl', 'lat_cl']:
  df_com[col] = np.round(df_com[col], 3)

# Check correspondence between INSEE and IGN
df_com_insee_fm = df_com_insee[~df_com_insee['DEP'].isin(['2A', '2B', '97'])].copy()
print df_com[['code_insee', 'commune']]\
        [~df_com['code_insee'].isin(df_com_insee_fm.index)].to_string()

df_com.set_index('code_insee', inplace = True)
## Overwrite IGN pop with INSEE pop (dates?)
#df_com['pop'] = df_com_insee['P10_POP']

# #############
# CASE STUDY
# #############

# todo: find competitors of a store based on radius
# todo: refine by querying dist/travel time from osrm server

# Municipalities around a given store
df_com['lat_store'] = df_lsa.loc[df_lsa['id_lsa'] == 49, 'latitude'].iloc[0]
df_com['lng_store'] = df_lsa.loc[df_lsa['id_lsa'] == 49, 'longitude'].iloc[0]
# print df_com[['lat_store', 'lng_store']][0:10].to_string()
df_com['dist'] = compute_distance_ar(df_com['lat_store'].values,
                                     df_com['lng_store'].values,
                                     df_com['lat_cl'].values,
                                     df_com['lng_cl'].values)
print u'\nMunicipalities within 30km {:d}'.format(\
        len(df_com[df_com['dist'] < 30]))

# row = df_com[df_com['dist'] < 30].iloc[0]
dict_res = {}
for row_i, row in df_com[df_com['dist'] <= 30].iterrows():
  ls_gps = list(row[['lat_store', 'lng_store', 'lat_cl', 'lng_cl']].values)
  query = 'http://localhost:5000/viaroute?'+\
          'loc={:f},{:f}&loc={:f},{:f}'.format(*ls_gps)
  try:
    # print query
    response = urllib2.urlopen(query)
    content = response.read()
    osrm_resp = json.loads(content)
    # pprint.pprint(osrm_resp)
    # print osrm_resp['route_summary']
    dict_res[row_i] = osrm_resp['route_summary']
  except:
    print 'Query failed:', query

# Check results
ls_rows_res = []
for k,v in dict_res.items():
  ls_rows_res.append([k, v['total_distance'], v['total_time']])
df_res = pd.DataFrame(ls_rows_res, columns = ['ind_com', 'dist_osrm', 'time_osrm'])
#print df_res[['dist_osrm', 'time_osrm']].describe()
df_res.set_index('ind_com', inplace = True)

# Merge back
df_com_sub = df_com[df_com['dist'] <= 30].copy()
df_com_sub = pd.merge(df_com_sub[['com_surf', 'commune', 'pop', 'dist']],
                      df_res,
                      left_index = True,
                      right_index = True,
                      how = 'left')
df_com_sub.sort('dist', inplace = True)
df_com_sub['time_osrm'] = df_com_sub['time_osrm'] / 60.0 # sec to minutes
df_com_sub['dist_osrm'] = df_com_sub['dist_osrm'] / 1000.0 # m to km
#print df_com_sub[0:20].to_string()
print df_com_sub[['dist', 'dist_osrm', 'time_osrm']].describe()

df_com_sub.to_csv(os.path.join(path_built_csv,
                               '201407_competition',
                               'df_km_vs_time_mun_ex.csv'),
                  encoding = 'utf-8',
                  float_format = '%.3f',
                  index_label = 'code_insee')

#plt.scatter(df_com_sub['dist'].values, df_com_sub['dist_osrm'].values)
#plt.show()
#plt.scatter(df_com_sub['dist'].values, df_com_sub['time_osrm'].values)
#plt.show()

# Stores around a given store
df_lsa['lat_store'] = df_lsa.loc[df_lsa['id_lsa'] == 49, 'latitude'].iloc[0]
df_lsa['lng_store'] = df_lsa.loc[df_lsa['id_lsa'] == 49, 'longitude'].iloc[0]
# print df_com[['lat_store', 'lng_store']][0:10].to_string()
df_lsa['dist'] = compute_distance_ar(df_lsa['lat_store'].values,
                                     df_lsa['lng_store'].values,
                                     df_lsa['latitude'].values,
                                     df_lsa['longitude'].values)
print u'\nStores within 30km {:d}'.format(\
        len(df_lsa[(df_lsa['dist'] < 30) & (df_lsa['id_lsa'] != 49)]))

# row = df_com[df_com['dist'] < 30].iloc[0]
df_lsa_sub = df_lsa[(df_lsa['dist'] < 30) & (df_lsa['id_lsa'] != 49)].copy()
dict_res = {}
for row_i, row in df_lsa_sub.iterrows():
  ls_gps = list(row[['lat_store', 'lng_store', 'latitude', 'longitude']].values)
  query = 'http://localhost:5000/viaroute?'+\
          'loc={:f},{:f}&loc={:f},{:f}'.format(*ls_gps)
  try:
    # print query
    response = urllib2.urlopen(query)
    content = response.read()
    osrm_resp = json.loads(content)
    # pprint.pprint(osrm_resp)
    # print osrm_resp['route_summary']
    dict_res[row_i] = osrm_resp['route_summary']
  except:
    print 'Query failed:', query

# Check results
ls_rows_res = []
for k,v in dict_res.items():
  ls_rows_res.append([k, v['total_distance'], v['total_time']])
df_res = pd.DataFrame(ls_rows_res, columns = ['ind_com', 'dist_osrm', 'time_osrm'])
#print df_res[['dist_osrm', 'time_osrm']].describe()
df_res.set_index('ind_com', inplace = True)

# Merge back
df_lsa_sub = pd.merge(df_lsa_sub,
                      df_res,
                      left_index = True,
                      right_index = True,
                      how = 'left')
df_lsa_sub.sort('dist', inplace = True)
df_lsa_sub['time_osrm'] = df_lsa_sub['time_osrm'] / 60.0 # sec to minutes
df_lsa_sub['dist_osrm'] = df_lsa_sub['dist_osrm'] / 1000.0 # m to km
#print df_com_sub[0:20].to_string()
print df_lsa_sub[['dist', 'dist_osrm', 'time_osrm']].describe()

print df_lsa_sub.iloc[-1].to_string()

df_lsa_sub.to_csv(os.path.join(path_built_csv,
                               '201407_competition',
                               'df_km_vs_time_comp_ex.csv'),
                  encoding = 'utf-8',
                  float_format = '%.3f',
                  index_label = 'code_insee')

#import httplib2
#h = httplib2.Http(".cache")
#resp, content = h.request(query, 'GET')
#print content
