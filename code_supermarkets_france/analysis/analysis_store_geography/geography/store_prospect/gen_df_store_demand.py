#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_maps import *
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                        'data_csv')

path_insee = os.path.join(path_data, 'data_insee')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

path_maps = os.path.join(path_data,
                         'data_maps')
path_geo_dpt = os.path.join(path_maps, 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_geo_com = os.path.join(path_maps, 'GEOFLA_COM_WGS84', 'COMMUNE')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DATA
# ##############

# LOAD LSA STORE DATA
df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa_active_hsx.csv'),
                     dtype = {u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

df_lsa = df_lsa[(~pd.isnull(df_lsa['latitude'])) &\
                (~pd.isnull(df_lsa['longitude']))].copy()

df_com_insee = pd.read_csv(os.path.join(path_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'utf-8')

df_com_insee.set_index('CODGEO', inplace = True)

# LOAD GEO FRANCE
geo_france = GeoFrance(path_dpt = path_geo_dpt,
                       path_com = path_geo_com)
df_com = geo_france.df_com

# KEEP ONLY ONE LINE PER MUNICIPALITY (several polygons for some)
df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)
# keep largest area (todo: sum)
df_com.sort(columns = ['c_insee', 'poly_area'],
            ascending = False,
            inplace = True)
df_com.drop_duplicates(['c_insee'], inplace = True, take_last = False)

# GET GPS COORD OF MUNICIPALITY CENTER

# two centers available: centroid of polygon and town hall
print u'\nTest with commune', df_com['commune'].iloc[0]
x_test, y_test = df_com['x_ct'].iloc[0], df_com['y_ct'].iloc[0]
print geo_france.convert_ign_to_gps(x_test, y_test)

df_com[['lng_ct', 'lat_ct']] = df_com[['x_ct', 'y_ct']].apply(\
                                 lambda x: geo_france.convert_ign_to_gps(x['x_ct'],\
                                                                         x['y_ct']),\
                                 axis = 1)

df_com[['lng_cl', 'lat_cl']] = df_com[['x_cl', 'y_cl']].apply(\
                                 lambda x: geo_france.convert_ign_to_gps(x['x_cl'],\
                                                                         x['y_cl']),\
                                 axis = 1)

# Round gps coord
for col in ['lng_ct', 'lat_ct', 'lng_cl', 'lat_cl']:
  df_com[col] = np.round(df_com[col], 3)

lsd0 = [u'enseigne',
        u'adresse1',
        u'c_postal',
        u'ville'] #, u'Latitude', u'Longitude']

# Check correspondence between INSEE and IGN
df_com_insee_fm = df_com_insee[~df_com_insee['DEP'].isin(['2A', '2B', '97'])].copy()
print df_com[~df_com['c_insee'].isin(df_com_insee_fm.index)].to_string()

# Add population to IGN data
df_com.set_index('c_insee', inplace = True)
df_com['pop'] = df_com_insee['P10_POP']

# Type restriction
ls_h_and_s_demand = [['H', 25],
                     ['S', 10]]

for type_store, dist_demand in ls_h_and_s_demand:
  df_lsa_type = df_lsa[df_lsa['type_alt'] == type_store].copy()
  
  # Population available for one store
  
  ls_rows_demand = []
  for row_ind, row in df_lsa_type.iterrows():
    ## could actually keep reference store since using groupe surface only
    #df_lsa_sub_temp = df_lsa_sub[df_lsa_sub.index != row_ind].copy()
    df_com_temp = df_com.copy()
    df_com_temp['lat_store'] = row['latitude']
    df_com_temp['lng_store'] = row['longitude']
    df_com_temp['dist'] = compute_distance_ar(df_com_temp['lat_store'],
                                              df_com_temp['lng_store'],
                                              df_com_temp['lat_cl'],
                                              df_com_temp['lng_cl'])
    # AC
    ac_pop = df_com_temp['pop'][df_com_temp['dist'] <= dist_demand].sum()
    
    # CONTINUOUS
    df_com_temp['wgtd_pop'] = np.exp(-df_com_temp['dist']/10) *\
                                          df_com_temp['pop']
    pop = df_com_temp['wgtd_pop'].sum()

    ls_rows_demand.append((row_ind, ac_pop, pop))

  df_des_demand = pd.DataFrame(ls_rows_demand,
                               columns = ['index', 'ac_pop', 'pop'])
  df_des_demand.set_index('index', inplace = True)
  
  df_lsa_type = pd.merge(df_lsa_type,
                         df_des_demand,
                         how = 'left',
                         left_index = True,
                         right_index = True)
  
  df_lsa_type.sort(['c_insee_ardt', 'enseigne'], inplace = True)
  
  ls_disp_lsa_comp = lsd0 + ['ac_pop', 'pop']

  print u'\n', type_store
  print df_lsa_type[ls_disp_lsa_comp][0:10].to_string()
  
  ## temp: avoid error with dates before 1900 and strftime (when outputing to csv)
  #df_lsa_type.loc[df_lsa_type[u'Date_Ouv'] <= '1900', 'Date_Ouv'] =\
  #   pd.to_datetime('1900/01/01', format = '%Y/%m/%d')

  df_lsa_type.to_csv(os.path.join(path_built_csv,
                                  '201407_competition',
                                  'df_store_prospect_demand_%s.csv' %type_store),
                     float_format ='%.3f',
                     index = False,
                     encoding = 'utf-8')
