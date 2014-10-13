#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
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

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

path_built = os.path.join(path_data, 'data_maps', 'data_built')

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

# Union of ardt polygons for Paris
ls_codegeos = df_com[u'insee_code'][df_com['dpt_name'] == 'PARIS'].values.tolist()
my_poly = df_com['poly'][df_com['insee_code'] == ls_codegeos[0]].values[0]
for codegeo in ls_codegeos:
  for row_ind, row_info in df_com[df_com['insee_code'] == codegeo].iterrows():
    my_poly = my_poly.union(row_info['poly'])
    my_poly_buffer = my_poly.buffer(1000)
try:
  patch = PolygonPatch(my_poly, color='r') # check if connected (really?)
  patch_buffer = PolygonPatch(my_poly_buffer, color='b')
  shapely_polygon = my_poly
except:
  shapely_polygon = my_poly.convex_hull # if not connected, enveloppe?

# Check result
fig = plt.figure()
ax = fig.add_subplot(111, aspect = 'equal')
ax.add_patch(patch_buffer)
ax.add_patch(patch)
ax.autoscale_view(True, True, True)
plt.tight_layout()
plt.show()

# Get list of coordinates (neglect interior if any for now)
paris_poly = zip(shapely_polygon.exterior.coords.xy[0].tolist(),
                 shapely_polygon.exterior.coords.xy[1].tolist())

# Prepare string in format poly
# http://wiki.openstreetmap.org/wiki/Osmosis/Polygon_Filter_File_Format
# Might prefer scientific notations
paris_poly_gps = [' '.join(map(lambda x: "{:.4f}".format(x),\
    m_fra(x, y, inverse = True))) for x,y in paris_poly]
# no need to inverse via [::-1]

paris_poly_str = u'paris\n1\n' +\
                    u''.join([u'    %s\n' %x for x in paris_poly_gps])+\
                    u'END\nEND'

f = open(os.path.join(path_built, 'paris.poly'), 'w')
f.write(paris_poly_str)
f.close()

# With buffer
paris_poly_buffer = zip(my_poly_buffer.exterior.coords.xy[0].tolist(),
                        my_poly_buffer.exterior.coords.xy[1].tolist())
paris_poly_buffer_gps = [' '.join(map(lambda x: "{:.4f}".format(x),\
    m_fra(x, y, inverse = True))) for x,y in paris_poly_buffer]
paris_poly_buffer_str = u'paris\n1\n' +\
                        u''.join([u'    %s\n' %x for x in paris_poly_buffer_gps])+\
                        u'END\nEND'
f = open(os.path.join(path_built, 'paris_buffer.poly'), 'w')
f.write(paris_poly_buffer_str)
f.close()
