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

# #############
# LOAD FILES
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

path_dir_500 = os.path.join(path_data, 'data_maps', 'ROUTE500_WGS84')

ls_files_500 = [('TRONCON_ROUTE', 'routes'),
                ('NOEUD_ROUTIER', 'noeuds'),
                ('NOEUD_COMMUNE', 'communes')]

for file_500_orig, file_500_dest in ls_files_500:
  m_fra.readshapefile(os.path.join(path_dir_500, file_500_orig),
                      file_500_dest,
                      color = 'none',
                      zorder = 2)

# Load administrative limits
path_dir_dpts = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84')
m_fra.readshapefile(os.path.join(path_dir_dpts, 'DEPARTEMENT'),
                    'dpt',
                    color = 'none',
                    zorder = 2)

df_dpt = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.dpt],
                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.dpt_info],
                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.dpt_info],
                       'region_name' : [d['NOM_REGION'] for d in m_fra.dpt_info],
                       'region_code' : [d['CODE_REG'] for d in m_fra.dpt_info]})
#print df_dpt[['code_dpt', 'dpt_name','code_region', 'region_name']].to_string()
# Some regions broken in multi polygons: appear mult times (138 items, all France Metr)

# ############
# DRAW MAPS
# ############

## FRANCE
#
#for shape_dict, shape in zip(m_fra.routes_info, m_fra.routes):
#  xx, yy = zip(*shape)
#  if shape_dict['CLASS_ADM'].decode('latin-1') == u'Autoroute':
#    temp = m_fra.plot(xx, yy, linewidth = 1.2, color = 'r')
#    temp = m_fra.plot(xx, yy, linewidth = 0.8, color = '#ffff00')
#  elif shape_dict['CLASS_ADM'].decode('latin-1') == u'Nationale':
#    temp = m_fra.plot(xx, yy, linewidth = 0.8, color = 'k')
#    temp = m_fra.plot(xx, yy, linewidth = 0.6, color = 'r')
#  elif shape_dict['CLASS_ADM'].decode('latin-1') == u'Départementale':
#    temp = m_fra.plot(xx, yy, linewidth = 0.7, color = 'k')
#    temp = m_fra.plot(xx, yy, linewidth = 0.5, color = '#ffff00')
#  else:
#    temp = m_fra.plot(xx, yy, linewidth = 0.5, color = 'k')
#    temp = m_fra.plot(xx, yy, linewidth = 0.3, color = 'w')
#m_fra.drawcountries()
#m_fra.drawcoastlines()
#plt.tight_layout()
##plt.show()
#plt.savefig(os.path.join(path_data, 'data_maps', 'data_built',
#                         'graphs', 'roads', 'fra_500.png'),
#            dpi=700)

# ANY AREA

# todo: improve efficiency: db once and for all with dummies per region/dpt (?)
# todo: improve road display

region ="NORD-PAS-DE-CALAIS"
region_multipolygon = MultiPolygon(list(df_dpt[df_dpt['region_name'] ==\
                                          region]['poly'].values))
region_multipolygon_prep = prep(region_multipolygon)
region_bounds = region_multipolygon.bounds

for shape_dict, shape in zip(m_fra.routes_info, m_fra.routes):
  if not region_multipolygon.disjoint(MultiPoint(shape)):
    xx, yy = zip(*shape)
    if shape_dict['CLASS_ADM'].decode('latin-1') == u'Autoroute':
      temp = m_fra.plot(xx, yy, linewidth = 3., color = 'r')
      temp = m_fra.plot(xx, yy, linewidth = 2., color = '#ffff00')
    elif shape_dict['CLASS_ADM'].decode('latin-1') == u'Nationale':
      temp = m_fra.plot(xx, yy, linewidth = 2.5, color = 'k')
      temp = m_fra.plot(xx, yy, linewidth = 2., color = 'r')
    elif shape_dict['CLASS_ADM'].decode('latin-1') == u'Départementale':
      temp = m_fra.plot(xx, yy, linewidth = 1.5, color = 'k')
      temp = m_fra.plot(xx, yy, linewidth = 1.0, color = '#ffff00')
    else:
      temp = m_fra.plot(xx, yy, linewidth = 1.2, color = 'k')
      temp = m_fra.plot(xx, yy, linewidth = 0.8, color = 'w')
m_fra.drawcountries()
m_fra.drawcoastlines()
plt.xlim((region_bounds[0], region_bounds[2]))
plt.ylim((region_bounds[1], region_bounds[3]))
plt.tight_layout()
plt.savefig(os.path.join(path_data, 'data_maps', 'data_built',
                         'graphs', 'roads', '%s_500.png' %region),
            dpi=700)
#plt.show()
