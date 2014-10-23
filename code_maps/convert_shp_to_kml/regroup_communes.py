#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
# import fiona
# import shapefile
# import simplekml

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

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

# LOAD INSEE AREAS

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')
df_insee_a = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_insee_areas.csv'),
                         encoding = 'UTF-8')

# Add big city ardts
ls_insee_ardts = [['75056', ['{:5d}'.format(i) for i in range(75101, 75121)]],
                  ['69123', ['{:5d}'.format(i) for i in range(69381, 69390)]],
                  ['13055', ['{:5d}'.format(i) for i in range(13201, 13217)]]]
for ic_main, ls_ic_ardts in ls_insee_ardts:
  df_temp = df_insee_a[df_insee_a['CODGEO'] == ic_main].copy()
  for ic_ardt in ls_ic_ardts:
    df_temp['CODGEO'] = ic_ardt
    df_insee_a = pd.concat([df_insee_a, df_temp])

# Get rid of Corsica and DOMTOM
df_insee_a = df_insee_a[~(df_insee_a['CODGEO'].str.slice(stop = -3).isin(['2A', '2B', '97']))]

# check match between geofla insee codes and insee data
set_geofla_ic = set(df_com['insee_code'].values)
set_insee_ic = set(df_insee_a['CODGEO'].values)
set_pbms_1 = set_geofla_ic.difference(set_insee_ic)
# Missing in insee areas: ['52266', '52124', '52033', '52465', '52278']
set_pbms_2 = set_insee_ic.difference(set_geofla_ic)
# Missing in geofla : [u'69123', u'28042', u'75056', u'76095', u'13055']

## UNION OF POLYGONS
#pol1 = df_com['poly'][df_com['insee_code'] == '92050'].values[0]  # nanterre
#pol2 = df_com['poly'][df_com['insee_code'] == '92063'].values[0]  # rueil
#pol3 = pol1.union(pol2)
#pol4 = df_com['poly'][df_com['insee_code'] == '78646'].values[0]  # versailles
#pol5 = pol3.union(pol4) 
## error with path=PolygonPatch(pol5) since not connected
#pol6 = df_com['poly'][df_com['insee_code'] == '92076'].values[0]  # vaucresson
#pol7 = pol5.union(pol6) 
#patch = PolygonPatch(pol7)
## works since this one is connected
##fig = plt.figure()
##ax = fig.add_subplot(111)
##ax.add_patch(patch)
##ax.autoscale_view(True, True, True)
##plt.show()

# build dict of area coords
area = 'AU2010'
dict_uu_polygons = {}
ls_uu_polygons, ls_uu_pbms = [], []
for uu2010 in df_insee_a[area].unique():
  ls_uu_codegeos = df_insee_a[u'CODGEO'][df_insee_a[area] == uu2010].values.tolist()
  ls_uu_codegeos = list(set(ls_uu_codegeos).intersection(set_insee_ic))
  if ls_uu_codegeos: 
    polygon_uu = df_com['poly'][df_com['insee_code'] == ls_uu_codegeos[0]].values[0]
    for uu_codegeo in ls_uu_codegeos:
      for row_ind, row_info in df_com[df_com['insee_code'] == uu_codegeo].iterrows():
        polygon_uu = polygon_uu.union(row_info['poly'])
    try:
      patch = PolygonPatch(polygon_uu) # check if connected (really?)
      shapely_polygon = polygon_uu
    except:
      ls_uu_pbms.append(uu2010)
      shapely_polygon = polygon_uu.convex_hull # if not connected
    ls_uu_polygons.append(shapely_polygon)
    # neglect interior if any
    dict_uu_polygons[uu2010] = zip(shapely_polygon.exterior.coords.xy[0].tolist(),
                                   shapely_polygon.exterior.coords.xy[1].tolist())

enc_json(dict_uu_polygons, os.path.join(path_dir_insee,
                                        'insee_areas',
                                        'dict_%s_l93_coords.json' %area))

# try to improve on convex_hull: keep several polygons
