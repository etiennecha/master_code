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

df_lsa = df_lsa[(~df_lsa['latitude'].isnull()) &\
                (~df_lsa['longitude'].isnull())].copy()

df_com_insee = pd.read_csv(os.path.join(path_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'utf-8')
# Has both districts and aggregate for Paris/Marseille/Lyon (e.g. DEP == '75')

df_com_insee.set_index('CODGEO', inplace = True)

# LOAD GEO FRANCE (Keep Corse)
geo_france = GeoFrance(path_dpt = path_geo_dpt,
                       path_com = path_geo_com,
                       corse = True)
df_com = geo_france.df_com
# Has only districts for Paris/Marseille/Lyon (e.g. departement == 'PARIS')

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

## Check correspondence between INSEE and IGN
#df_com_insee_fm = df_com_insee[~df_com_insee['DEP'].isin(['2A', '2B', '97'])].copy()
#print df_com[~df_com['c_insee'].isin(df_com_insee_fm.index)].to_string()

# Add population to IGN data
df_com.set_index('c_insee', inplace = True)
df_com['pop'] = df_com_insee['P10_POP']

# ####################
# COMPUTE STORE DEMAND
# ####################

# Each city population shared across:
# - all stores (continuous) - several factors?
# - nearby stores (discrete) - several distances?

# Then sum for each store demand from each municipality:
# => gives an index of store potential market

# todo: check by group vs. group market shares? (+ large hypers?)
# could adjust demand depending on groups to match it (price effect etc.)

ls_rows_demand_cont = []
ls_rows_demand_disc = []
for row_ind, row in df_com.iterrows():
  df_lsa_temp = df_lsa.copy()
  df_lsa_temp['lat_com'] = row['lat_cl']
  df_lsa_temp['lng_com'] = row['lng_cl']
  df_lsa_temp['pop'] = row['pop']
  df_lsa_temp['dist'] = compute_distance_ar(df_lsa_temp['latitude'],
                                            df_lsa_temp['longitude'],
                                            df_lsa_temp['lat_com'],
                                            df_lsa_temp['lng_com'])
  # continous method (could add max group share)
  df_lsa_temp['wgtd_surface'] = np.exp(-df_lsa_temp['dist']/10) * df_lsa_temp['surface']
  df_lsa_temp['wgtd_market_share'] = df_lsa_temp['wgtd_surface'] / df_lsa_temp['wgtd_surface'].sum()
  df_lsa_temp['wgtd_pop'] = df_lsa_temp['wgtd_market_share'] * df_lsa_temp['pop']
  ls_rows_demand_cont.append(df_lsa_temp['wgtd_pop'])

  # discrete method (could add max group share)
  df_lsa_temp_sub = df_lsa_temp[df_lsa_temp['dist'] <= 10].copy()
  df_lsa_temp_sub['wgtd_market_share'] = df_lsa_temp_sub['surface'] /\
                                           df_lsa_temp['surface'].sum()
  df_lsa_temp_sub['wgtd_pop'] = df_lsa_temp_sub['wgtd_market_share'] * df_lsa_temp_sub['pop']
  ls_rows_demand_disc.append(df_lsa_temp_sub['wgtd_pop'])

df_demand_cont = pd.concat(ls_rows_demand_cont, axis = 1)
se_store_demand_cont = df_demand_cont.sum(1)

df_demand_disc = pd.concat(ls_rows_demand_disc, axis = 1)
se_store_demand_disc = df_demand_disc.sum(1)
