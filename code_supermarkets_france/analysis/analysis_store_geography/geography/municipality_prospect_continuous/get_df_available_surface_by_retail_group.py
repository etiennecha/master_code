#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
from functions_maps import *
import os, sys
import re
import numpy as np
import datetime as datetime
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from matplotlib.collections import PatchCollection
from descartes import PolygonPatch
import time

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

df_com.set_index('c_insee', inplace = True)

# ##########
# EXECUTION
# ##########

ls_rgs = [u'CARREFOUR',
          u'MOUSQUETAIRES',
          u'CASINO',
          u'LIDL',
          u'SYSTEME U',
          u'ALDI',
          u'LECLERC',
          u'AUCHAN', 
          u'LOUIS DELHAIZE',
          u'DIAPAR',
          u'COLRUYT']

# SURFACE AVAIL TO EACH COMMUNE BY GROUP
for retail_group in ls_rgs:
  df_lsa_rg = df_lsa[df_lsa['groupe'] == retail_group].copy()
  ls_rows_res = []
  start = time.time()
  for i, row in df_com.iterrows():
    df_lsa_rg['lat_com'] = row['lat_cl']
    df_lsa_rg['lng_com'] = row['lng_cl']
    df_lsa_rg['dist'] = compute_distance_ar(df_lsa_rg['latitude'],
                                            df_lsa_rg['longitude'],
                                            df_lsa_rg['lat_com'],
                                            df_lsa_rg['lng_com'])
    df_lsa_rg['wgtd_surface'] = np.exp(-df_lsa_rg['dist']/10) * df_lsa_rg['surface']
    ls_rows_res.append([i, df_lsa_rg['wgtd_surface'].sum()])
  print retail_group, time.time() - start
  df_com_rg = pd.DataFrame(ls_rows_res, columns = ['c_insee', 'available_surface'])
  df_com_rg.set_index('c_insee', inplace = True)
  df_com['available_surface_%s' %retail_group] = df_com_rg['available_surface']

# SURFACE WITHIN EACH COMMUNE BY GROUP
for retail_group in ls_rgs:
  df_lsa_rg = df_lsa[df_lsa['groupe'] == retail_group].copy()
  se_rg_com_surf = df_lsa_rg[['c_insee_ardt', 'surface']]\
                     .groupby('c_insee_ardt').agg(np.sum)['surface']
  df_com['surface_%s' %retail_group] = se_rg_com_surf

ls_disp_com_rg = ['available_surface_%s' %rg for rg in ls_rgs] +\
                 ['surface_%s' %rg for rg in ls_rgs]

## OUTPUT TO CSV
#df_com[ls_disp_com_rg].to_csv(os.path.join(path_dir_built_csv,
#                                           '201407_competition',
#                                          'df_mun_prospect_surface_available_by_group.csv'),
#                              index_label = 'code_insee',
#                              encoding = 'utf-8',
#                              float_format='%.3f')
