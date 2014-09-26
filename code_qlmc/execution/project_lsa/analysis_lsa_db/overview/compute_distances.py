#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import datetime as datetime
import pandas as pd
import matplotlib.pyplot as plt
import pprint
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
#import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
#from pysal.esda.mapclassify import Natural_Breaks as nb
from matplotlib import colors

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_png = os.path.join(path_dir_qlmc, 'data_built' , 'data_png')

path_dir_source_lsa = os.path.join(path_dir_qlmc, 'data_source', 'data_lsa_xls')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

# #############
# READ CSV FILE
# #############

df_lsa_int = pd.read_csv(os.path.join(path_dir_built_csv, 'df_lsa_int.csv'),
                         encoding = 'UTF-8')

# change name?
df_lsa_gps = df_lsa_int[(df_lsa_int['Type_alt'] != 'DRIN') &\
                        (df_lsa_int['Type_alt'] != 'DRIVE')]

# #############
# FRANCE MAP
# #############

# excludes Corsica
x1 = -5.
x2 = 9.
y1 = 42
y2 = 52.

#w = x2 - x1
#h = y2 - y1
#extra = 0.025

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
#                llcrnrlat=y1 - extra * h,
#                urcrnrlat=y2 + extra * h,
#                llcrnrlon=x1 - extra * w,
#                urcrnrlon=x2 + extra * w)

path_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')

m_fra.readshapefile(path_dpt, 'departements_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_com, 'communes_fr', color = 'none', zorder=2)

path_dir_120 = os.path.join(path_data, 'data_maps', 'ROUTE120_WGS84')
path_120_rte = os.path.join(path_dir_120, 'TRONCON_ROUTE')
path_120_nod = os.path.join(path_dir_120, 'NOEUD_ROUTIER')

m_fra.readshapefile(path_120_rte, 'routes_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_120_nod, 'noeuds_fr', color = 'none', zorder=2)

#df_dpt = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.departements_fr],
#                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.departements_fr_info],
#                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.departements_fr_info],
#                       'region_name' : [d['NOM_REGION'] for d in m_fra.departements_fr_info],
#                       'region_code' : [d['CODE_REG'] for d in m_fra.departements_fr_info]})

#df_dpt['patches'] = df_dpt['poly'].map(lambda x: PolygonPatch(x,
#                                                              facecolor='#FFFFFF', # '#555555'
#                                                              edgecolor='#555555', # '#787878'
#                                                              lw=.25, alpha=.3, zorder=1))

df_com = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.communes_fr],
                       'x_center' : [d['X_CENTROID'] for d in m_fra.communes_fr_info],
                       'y_center' : [d['Y_CENTROID'] for d in m_fra.communes_fr_info],
                       'x_cl' : [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl' : [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'code_insee' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'commune' : [d['NOM_COMM'] for d in m_fra.communes_fr_info]})

df_lsa_gps['point'] = df_lsa_gps[['Longitude', 'Latitude']].apply(\
                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)

def convert_to_ign(x, y):
  x_l_93_ign = (m_fra(x, y)[0] + 700000 - m_fra(3, 46.5)[0])/100.0
  y_l_93_ign = (m_fra(x, y)[1] + 6600000 - m_fra(3, 46.5)[1])/100.0
  return x_l_93_ign, y_l_93_ign

def convert_from_ign(x_l_93_ign, y_l_93_ign):
  x = x_l_93_ign * 100 - 700000 + m_fra(3, 46.5)[0] 
  y = y_l_93_ign * 100 - 6600000 + m_fra(3, 46.5)[1]
  x, y = m_fra(x, y, inverse = True)
  return x, y

print u'\nTest with commune', df_com['commune'].iloc[0]
x_test, y_test = df_com['x_center'].iloc[0], df_com['y_center'].iloc[0]
print convert_from_ign(x_test, y_test)

df_com[['lng_ct', 'lat_ct']] = df_com[['x_center', 'y_center']].apply(\
                                 lambda x: convert_from_ign(x['x_center'],\
                                                            x['y_center']),\
                                 axis = 1)

df_com[['lng_cl', 'lat_cl']] = df_com[['x_cl', 'y_cl']].apply(\
                                 lambda x: convert_from_ign(x['x_cl'],\
                                                            x['y_cl']),\
                                 axis = 1)

df_com['dpt'] = df_com['code_insee'].str.slice(stop=-3)
df_com = df_com[~df_com['dpt'].isin(['2A', '2B'])]

# Store centered: distance to all communes
#df_com['lat_store'] = df_lsa_gps['Latitude'].iloc[0]
#df_com['lng_store'] = df_lsa_gps['Longitude'].iloc[0]
#df_com['dist'] = compute_distance_ar(df_com['lat_store'],
#                                     df_com['lng_store'],
#                                     df_com['lng_ct'],
#                                     df_com['lat_ct'])
## todo: finish coding and iterate over communes (or stores)

# COMMUNE CENTERED: DISTANCE TO ALL STORES AND AVAIL. SURFACE
df_lsa_gps['lat_com'] = df_com['lat_cl'].iloc[0]
df_lsa_gps['lng_com'] = df_com['lng_cl'].iloc[0]
df_lsa_gps['dist'] = compute_distance_ar(df_lsa_gps['Latitude'],
                                         df_lsa_gps['Longitude'],
                                         df_lsa_gps['lat_com'],
                                         df_lsa_gps['lng_com'])
ls_disp_a = ['Enseigne', 'ADRESSE1', 'Ville',
                'Latitude', 'Longitude', 'dist']
ls_disp_b = ls_disp_a + ['Surf Vente' , 'wgt_surf']
print df_lsa_gps[ls_disp_a][df_lsa_gps['dist'] < 10].to_string()
# Compute surface weighted by distance
df_lsa_gps['wgt_surf'] = np.exp(-df_lsa_gps['dist']/10) * df_lsa_gps['Surf Vente']
print df_lsa_gps[ls_disp_b][df_lsa_gps['dist'] < 10].to_string()
store_avail_surface = df_lsa_gps['wgt_surf'].sum()

# ITERATION OVER COMMUNES
df_com['avail_surf'] = np.nan
for store_type in ['H', 'X', 'S']:
  df_com['%s_ens' %store_type] = None
  df_com['%s_dist' %store_type] = np.nan

for i, row in df_com.iterrows():
  df_lsa_gps['lat_com'] = row['lat_cl']
  df_lsa_gps['lng_com'] = row['lng_cl']
  df_lsa_gps['dist'] = compute_distance_ar(df_lsa_gps['Latitude'],
                                           df_lsa_gps['Longitude'],
                                           df_lsa_gps['lat_com'],
                                           df_lsa_gps['lng_com'])
  df_lsa_gps['wgt_surf'] = np.exp(-df_lsa_gps['dist']/10) * df_lsa_gps['Surf Vente']
  df_com['avail_surf'].ix[i] = df_lsa_gps['wgt_surf'].sum()
  # writing may be costly => put in list, and merge dfs?
  for store_type in ['H', 'X', 'S']:
    store_ind = df_lsa_gps['dist'][df_lsa_gps['Type_alt'] == '%s' %store_type].argmin()
    df_com['%s_ens' %store_type].ix[i] = df_lsa_gps['Enseigne'].loc[store_ind]
    df_com['%s_dist' %store_type].ix[i] = df_lsa_gps['dist'].loc[store_ind]

#df_com.drop('poly', axis = 1 ,inplace = True)
#ls_disp_c = ['code_insee', 'commune', 'avail_surf',
#             'H_ens', 'H_dist', 'S_ens', 'S_dist', 'X_ens', 'X_dist']
#print df_com[ls_disp_c][df_com['code_insee'].str.slice(stop=-3) == '92'].to_string()
#print df_com[ls_disp_c][df_com['code_insee'].str.slice(stop=-3) == '75'].to_string()

# todo: output and perform stats descs

# ITERATION OVER ALL STORES
