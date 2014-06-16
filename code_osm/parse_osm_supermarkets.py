#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import pandas as pd
import xml.etree.ElementTree as ET
import re

path = os.path.abspath(os.path.dirname(sys.argv[0]))
# tree = ET.parse(os.path.join(path, 'haute-normandie-latest.osm'))
tree = ET.parse(os.path.join(path, 'france_supermarkets.osm'))
root = tree.getroot()

## Check first 50 elements
#for i in range(50):
#  print '\n', root[i].tag, root[i].attrib
#  for elt in root[i]:
#    print elt.tag, elt.attrib # elt.tag always tag?

# need to check way too apparently (can be way + node for same station?)
ls_entities = []
for i, row in enumerate(root):
  if row.tag == 'node' or row.tag == 'way': 
  # or row.tag=='relation': # relations have no gps coord... => recursion?
    for row_elt in row:
      if row_elt.attrib == {'k': 'shop', 'v': 'supermarket'}:
        ls_entities.append(i)
        break

# extract info in list of dict (add distinction way/node?)
ls_dict_entities = []
for i in ls_entities:
  dict_entity = root[i].attrib
  if root[i].tag == 'node':
    for row_elt in root[i]:
      dict_entity[row_elt.attrib['k']] = row_elt.attrib['v']
  else:
    for row_elt in root[i]:
      if 'k' in row_elt.attrib:
        dict_entity[row_elt.attrib['k']] = row_elt.attrib['v']
  ls_dict_entities.append(dict_entity)

# todo: check what happens with relations?

# todo:
# do with france or dl each region and loop (extract osm?)

# todo: 
# with geofla: check in which commune and get insee code
# with gps: look for nearest stations (with zagaz? gouv?)

import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch

# France
x1 = -5.
x2 = 9.
y1 = 42.
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

# path_dir_geofla_com = 'C:\Users\etna\Desktop\Etienne_work\Data\data_maps\GEOFLA_COM_WGS84\COMMUNE'
path_dir_geofla_com = '\\ulysse\users\echamayou\Bureau\Etienne_work\Data\data_maps\GEOFLA_COM_WGS84\COMMUNE'

m_fra.readshapefile(path_dir_geofla_com, 'communes_fr', color = 'none', zorder=2)

df_com = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.communes_fr],
                       'com_name' : [d['NOM_COMM'] for d in m_fra.communes_fr_info],
                       'com_code' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.communes_fr_info],
                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.communes_fr_info],
                       'reg_name' : [d['NOM_REGION'] for d in m_fra.communes_fr_info],
                       'reg_code' : [d['CODE_REG'] for d in m_fra.communes_fr_info]})

# caution: inverse x and y
# todo: run on all stores... see quality of results

# OSM Supermarkets: operator and name
dict_describe = {}
for field in ['operator', 'name']:
  dict_describe[field] = set()
  for entity in ls_dict_entities:
    dict_describe[field].add(entity.get(field))

# OSM Supermarkets: Intermarche / Les Mousquetaires
ls_mousquetaires = []
for entity in ls_dict_entities:
  if entity.get('operator') == 'Groupement des Mousquetaires':
    ls_mousquetaires.append(entity)

ls_itm = []
for entity in ls_dict_entities:
  if re.search(u'inter(-|\s)?march(e|é)', entity.get('name', u''), re.IGNORECASE):
    ls_itm.append(entity)

ls_diff_1 =  [entity for entity in ls_itm if entity not in ls_mousquetaires] # len88, legit ?
ls_diff_2 = [entity for entity in ls_mousquetaires if entity not in ls_itm]
# a priori: ls_itm is ok, 
# can add elt from ls_diff_2 which have no name (check)

ls_itm_final = []
for entity in ls_dict_entities:
  if (re.search(u'inter(-|\s)?march(e|é)', entity.get('name', u''), re.IGNORECASE)) or\
     (entity.get('operator') == 'Groupement des Mousquetaires' and not entity.get('name')):
    ls_itm_final.append(entity)

# OSM Supermarkets: Leclerc
ls_leclerc_all = []
for entity in ls_dict_entities:
  if (re.search(u'leclerc', entity.get('name', u''), re.IGNORECASE)) or\
     (re.search(u'leclerc', entity.get('operator', u''), re.IGNORECASE)):
    ls_leclerc_all.append(entity)

# 711 including drives
ls_leclerc_drive = [entity for entity in ls_leclerc_all\
                     if 'drive' in entity.get('name', '').lower()]

# Leclerc stores (might need to exclude a few more)
ls_leclerc_final = [entity for entity in ls_leclerc_all\
                     if entity not in ls_leclerc_drive]

# OSM Supermarkets: Find commune of supermarket (NB: need to inverse coordinates)
for i, x in enumerate(df_com['poly']):
	if Point(m_fra(3.13161, 50.7757)).within(x):
		print i
		break

ls_match = []
for entity in ls_leclerc_final:
  if entity.get('lon') and entity['lon']:
    store_point = Point(m_fra(float(entity['lon']), float(entity['lat'])))
    for i, x in enumerate(df_com['poly']):
      if store_point.within(x):
        ls_match.append((i, entity))
# seems to work but a lot have no gps coordinates... work on osmosis extraction
