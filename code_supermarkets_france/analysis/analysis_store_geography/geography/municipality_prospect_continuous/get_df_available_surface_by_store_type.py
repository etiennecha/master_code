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
import time

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                        'data_csv')

path_insee = os.path.join(path_data, 'data_insee')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# READ CSV FILES
# ##############

df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa_active.csv'),
                     dtype = {u'C_INSEE' : str,
                              u'C_INSEE_Ardt' : str,
                              u'C_Postal' : str,
                              u'SIREN' : str,
                              u'NIC' : str,
                              u'SIRET' : str},
                     parse_dates = [u'Date_Ouv', u'Date_Fer', u'Date_Reouv',
                                    u'Date_Chg_Enseigne', u'Date_Chg_Surface'],
                     encoding = 'UTF-8')

df_lsa = df_lsa[(~pd.isnull(df_lsa['Latitude'])) &\
                (~pd.isnull(df_lsa['Longitude']))].copy()

df_com_insee = pd.read_csv(os.path.join(path_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'UTF-8')

df_com_insee.set_index('CODGEO', inplace = True)

# #############
# FRANCE MAP
# #############

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

#path_dir_120 = os.path.join(path_data, 'data_maps', 'ROUTE120_WGS84')
#path_120_rte = os.path.join(path_dir_120, 'TRONCON_ROUTE')
#path_120_nod = os.path.join(path_dir_120, 'NOEUD_ROUTIER')
#m_fra.readshapefile(path_120_rte, 'routes_fr', color = 'none', zorder=2)
#m_fra.readshapefile(path_120_nod, 'noeuds_fr', color = 'none', zorder=2)

df_com = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.communes_fr],
                       'x_center' : [d['X_CENTROID'] for d in m_fra.communes_fr_info],
                       'y_center' : [d['Y_CENTROID'] for d in m_fra.communes_fr_info],
                       'x_cl' : [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl' : [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'code_insee' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'commune' : [d['NOM_COMM'] for d in m_fra.communes_fr_info]})
# keep only one line per commune (several polygons for some)
df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)
df_com.sort(columns = ['code_insee', 'poly_area'],
            ascending = False,
            inplace = True)

df_com.drop_duplicates(subset = 'code_insee', inplace = True)

#df_lsa['point'] = df_lsa[['Longitude', 'Latitude']].apply(\
#                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)

def convert_to_ign(x, y):
  x_l_93_ign = (m_fra(x, y)[0] + 700000 - m_fra(3, 46.5)[0])/100.0
  y_l_93_ign = (m_fra(x, y)[1] + 6600000 - m_fra(3, 46.5)[1])/100.0
  return x_l_93_ign, y_l_93_ign

def convert_from_ign(x_l_93_ign, y_l_93_ign):
  x = x_l_93_ign * 100 - 700000 + m_fra(3, 46.5)[0] 
  y = y_l_93_ign * 100 - 6600000 + m_fra(3, 46.5)[1]
  x, y = m_fra(x, y, inverse = True)
  return x, y

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

df_com['dpt'] = df_com['code_insee'].str.slice(stop=-3)
df_com = df_com[~df_com['dpt'].isin(['2A', '2B'])]

# Round gps coord
for col in ['lng_ct', 'lat_ct', 'lng_cl', 'lat_cl']:
  df_com[col] = np.round(df_com[col], 3)

# ##########
# EXECUTION
# ##########

df_com.set_index('code_insee', inplace = True)

# SURFACE AVAIL TO EACH COMMUNE

ls_rows_res = []
for i, row in df_com.iterrows():
  df_lsa['lat_com'] = row['lat_cl']
  df_lsa['lng_com'] = row['lng_cl']
  df_lsa['dist'] = compute_distance_ar(df_lsa['Latitude'],
                                       df_lsa['Longitude'],
                                       df_lsa['lat_com'],
                                       df_lsa['lng_com'])
  df_lsa['wgt_surf'] = np.exp(-df_lsa['dist']/10) * df_lsa['Surf Vente']
  row_res = [i, df_lsa['wgt_surf'].sum()]
  ls_rows_res.append(row_res)

df_com_all = pd.DataFrame(ls_rows_res, columns = ['code_insee', 'avail_surf'])
df_com_all.set_index('code_insee', inplace = True)
df_com['avail_surf'] = df_com_all['avail_surf']

# SURFACE AVAIL TO EACH COMMUNE BY STORE TYPE

ls_st = ['S', 'X', 'H']

for store_type in ls_st:
  
  #df_com['avail_surf' ] = np.nan
  #for store_type in ['H', 'X', 'S']:
  #  df_com['%s_dist' %store_type] = np.nan
  
  df_lsa_type = df_lsa[df_lsa['Type_alt'] == store_type].copy()
  
  ls_rows_res = []
  start = time.time()
  for i, row in df_com.iterrows():
    df_lsa_type['lat_com'] = row['lat_cl']
    df_lsa_type['lng_com'] = row['lng_cl']
    df_lsa_type['dist'] = compute_distance_ar(df_lsa_type['Latitude'],
                                              df_lsa_type['Longitude'],
                                              df_lsa_type['lat_com'],
                                              df_lsa_type['lng_com'])
    df_lsa_type['wgt_surf'] = np.exp(-df_lsa_type['dist']/10) * df_lsa_type['Surface']
    row_res = [i, df_lsa_type['wgt_surf'].sum()]
    # df_com.loc[i, 'avail_surf'] = df_lsa_type['wgt_surf'].sum()
    
    #for store_type in ['H', 'X', 'S']:
    #  min_dist = df_lsa_type['dist'][df_lsa_type['Type_alt'] == '%s' %store_type].min()
    #  # df_com.loc[i, '%s_dist' %store_type] = min_dist
    #  row_res.append(min_dist)
    
    ls_rows_res.append(row_res)
  
  print store_type, time.time() - start
  
  # df_com['All_dist'] = df_com[['H_dist', 'S_dist', 'X_dist']].min(axis = 1)
  
  df_com_type = pd.DataFrame(ls_rows_res, columns = ['code_insee', 'avail_surf'])
  df_com_type.set_index('code_insee', inplace = True)
  df_com['avail_surf_%s' %store_type] = df_com_type['avail_surf']

# SURFACE IN EACH COMMUNE
se_com_surf = df_lsa[['C_INSEE_Ardt', 'Surface']]\
                .groupby('C_INSEE_Ardt').agg(np.sum)['Surface']
df_com['surf'] = se_com_surf

# SURFACE IN EACH COMMUNE BY TYPE
for store_type in ls_st:
  df_lsa_type = df_lsa[df_lsa['Type_alt'] == store_type].copy()
  se_type_com_surf = df_lsa_type[['C_INSEE_Ardt', 'Surface']]\
                     .groupby('C_INSEE_Ardt').agg(np.sum)['Surface']
  df_com['surf_%s' %store_type] = se_type_com_surf

# add surface 
ls_disp_com_st = ['avail_surf', 'surf'] +\
                 ['avail_surf_%s' %st for st in ls_st] +\
                 ['surf_%s' %st for st in ls_st]

# OUTPUT TO CSV
df_com[ls_disp_com_st].to_csv(os.path.join(path_dir_built_csv,
                                           '201407_competition',
                                          'df_com_avail_surf_type.csv'),
                              index_label = 'code_insee',
                              encoding = 'utf-8',
                              float_format='%.3f')
