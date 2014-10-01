#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
# import fiona
import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
import simplekml

# France
x1 = -5.
x2 = 9.
y1 = 42.
y2 = 52.

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

# LOAD GEOFLA COMMUNES

path_dir_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')
m_fra.readshapefile(path_dir_com, 'com', color = 'none', zorder=2)

df_com = pd.DataFrame({'poly'       : [Polygon(xy) for xy in m_fra.com],
                       'insee_code' : [d['INSEE_COM'] for d in m_fra.com_info],
                       'com_name'   : [d['NOM_COMM'] for d in m_fra.com_info],
                       'dpt_name'   : [d['NOM_DEPT'] for d in m_fra.com_info],
                       'reg_name'   : [d['NOM_REGION'] for d in m_fra.com_info],
                       'pop'        : [d['POPULATION'] for d in m_fra.com_info],
                       'surf'       : [d['SUPERFICIE'] for d in m_fra.com_info],
                       'x_cl'       : [d['X_CHF_LIEU'] for d in m_fra.com_info],
                       'y_cl'       : [d['Y_CHF_LIEU'] for d in m_fra.com_info]})

df_com = df_com[df_com['reg_name'] != 'CORSE']

# LOAD INSEE REGROUPMENTS

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')
df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_insee_areas.csv'),
                             encoding = 'UTF-8')

df_insee_areas = [df_insee_areas['CODGEO'].str.slice(stop = -3) == '2A' |

# check match between geofla insee codes and insee data
ls_geofla_ic = list(df_com['insee_code'].values)
ls_insee_ic = list(df_insee_areas['CODGEO'].values)
#ls_pbms_1 = [ic for ic in ls_geofla_ic if ic not in ls_insee_ic] # easy fix: enrich insee areas
ls_pbms_2 = [ic for ic in ls_insee_ic if ic not in ls_geofla_ic]

## KML COMMUNES

#kml = simplekml.Kml()
#
#for com_ind, com_row in df_com.iterrows():
#  shapely_polygon = com_row['poly']
#  outerboundary = [m_france(*point_coord, inverse = 'True')\
#                     for point_coord in list(shapely_polygon.exterior.coords)]
#  innerboundary = [m_france(*point_coord, inverse = 'True')\
#                     for point_coord in list(shapely_polygon.interiors)]
#  name = '%s (%s)' %(com_row['NOM_COMM'], com_row['INSEE_COM'])
#  pol = kml.newpolygon(name = name,
#                       outerboundaryis = outerboundary,
#                       innerboundaryis = innerboundary)
#
#kml.save(os.path.join(path_data, 'data_maps', 'kml_files', 'communes.kml'))

## UNION OF POLYGONS
#
#pol1 = df_com['poly'][df_com['INSEE_COM'] == '92050'].values[0]  # nanterre
#pol2 = df_com['poly'][df_com['INSEE_COM'] == '92063'].values[0]  # rueil
#pol3 = pol1.union(pol2)
#
#pol4 = df_com['poly'][df_com['INSEE_COM'] == '78646'].values[0]  # versailles
#pol5 = pol3.union(pol4)
#
#pol6 = df_com['poly'][df_com['INSEE_COM'] == '92076'].values[0]  # vaucresson (should connect)
#pol7 = pol5.union(pol6) # seems to worl => Polygon, not MultiPolygon !

#kml = simplekml.Kml()
#ls_uu_pbms = []
#for code_uu2010 in ls_codes_uu2010:
#  ls_uu_codegeos = df_insee[u'Département - Commune CODGEO']\
#                     [df_insee[u"Code géographique de l'unité urbaine UU2010"] == code_uu2010].values.tolist()
#  ls_uu_codegeos = [codegeo for codegeo in ls_uu_codegeos if codegeo in ls_ign_codegeo]
#  if ls_uu_codegeos: 
#    polygon_uu = df_com['poly'][df_com['INSEE_COM'] == ls_uu_codegeos[0]].values[0]
#    for uu_codegeo in ls_uu_codegeos:
#      for row_ind, row_info in df_com[df_com['INSEE_COM'] == uu_codegeo].iterrows():
#        polygon_uu = polygon_uu.union(row_info['poly'])
#    try: 
#      shapely_polygon = polygon_uu
#      name = df_insee[u"Libellé de l'unité urbaine LIBUU2010"]\
#               [df_insee[u'Département - Commune CODGEO'] == uu_codegeo].values[0]
#      outerboundary = [m_france(*point_coord, inverse = 'True')\
#                         for point_coord in list(shapely_polygon.exterior.coords)]
#      ## innerboundary: can't keep since several polygons 
#      #innerboundary = [m_france(*point_coord, inverse = 'True')\
#      #                   for point_coord in list(shapely_polygon.interiors)]
#      pol = kml.newpolygon(name = name,
#                           outerboundaryis = outerboundary,
#                           innerboundaryis = [])
#    except:
#      ls_uu_pbms.append(code_uu2010)
