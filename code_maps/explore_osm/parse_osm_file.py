#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import xml.etree.ElementTree as ET
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

path_data_osm = os.path.join(path_data, 'data_osm')
tree = ET.parse(os.path.join(path_data_osm, 'paris_buffer_residential.osm'))
root = tree.getroot()

dict_nodes, dict_ways_pre, dict_relations_pre = {}, {}, {}
for i, row in enumerate(root):
  if row.tag == 'node':
    dict_nodes[root[i].attrib['id']] = [i,
                                        [], # add info?
                                        [root[i].attrib['lat'],
                                         root[i].attrib['lon']]]
  elif row.tag == 'way':
    ls_ref, ls_info = [], []
    for x in root[i]:
      if 'ref' in x.attrib:
        ls_ref.append(x.attrib['ref'])
        # sufficient a priori?
      else:
        ls_info.append(x.attrib)
    dict_ways_pre[root[i].attrib['id']] = [i,
                                           ls_info,
                                           ls_ref]
  elif row.tag == 'relation':
    ls_ref, ls_info = [], []
    for x in root[i]:
      if 'ref' in x.attrib:
        ls_ref.append(x.attrib)
        # need to know inner, outer etc
      else:
        ls_info.append(x.attrib)
    dict_relations_pre[root[i].attrib['id']] = [i,
                                                ls_info,
                                                ls_ref]

# todo: dict_ways, dict_relations directly with gps (from dict_nodes)
# should exclude inner polygons in relations or smth like that

dict_ways = {}
for k,v in dict_ways_pre.items():
  ls_way_gps = [dict_nodes.get(x, [[], [], []])[2] for x in v[2]]
  dict_ways[k] = v[0:2] + [[x for x in ls_way_gps if x]]

# ##############
# MAP OF PARIS
# ##############

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
# print df_dpt[['code_dpt', 'dpt_name','code_region', 'region_name']].to_string()
# Some regions broken in multi polygons: appear mult times (138 items, all France Metr)
region_multipolygon = MultiPolygon(list(df_dpt[df_dpt['dpt_name'] ==\
                                          "PARIS"]['poly'].values))
region_multipolygon_prep = prep(region_multipolygon)
region_bounds = region_multipolygon.bounds

## Display one polygon
#ls_poly_wgs84 = dict_ways[dict_ways.keys()[0]][2]
#ls_gps_l93 = [m_fra(*map(lambda x: float(x), gps[::-1])) for gps\
#               in ls_poly_wgs84]
#my_poly = Polygon(ls_gps_l93)
#patch = PolygonPatch(my_poly)
#fig = plt.figure()
#ax = fig.add_subplot(111)
#ax.add_patch(patch)
#plt.xlim((region_bounds[0], region_bounds[2]))
#plt.ylim((region_bounds[1], region_bounds[3]))
## to savefig (else it crashes)
#plt.savefig(os.path.join(path_data_osm, 'paris_test_1.png'),
#            dpi = 700)
#plt.close()

# Display several/all polygons
ls_polygon_patches = []
ls_pbms = []
for k,v in dict_ways.items():
  try:
    ls_gps_l93 = [m_fra(*map(lambda x: float(x), gps[::-1])) for gps in v[2]]
    my_poly = Polygon(ls_gps_l93)
    patch = PolygonPatch(my_poly)
    ls_polygon_patches.append(patch)
  except:
    ls_pbms.append(k)
fig = plt.figure()
ax = fig.add_subplot(111)
m_fra.drawcountries()
ax.add_collection(PatchCollection(ls_polygon_patches))
plt.xlim((region_bounds[0], region_bounds[2]))
plt.ylim((region_bounds[1], region_bounds[3]))
# to savefig (else it crashes)
plt.savefig(os.path.join(path_data_osm, 'paris_test_2.png'),
            dpi = 700)
plt.close()
