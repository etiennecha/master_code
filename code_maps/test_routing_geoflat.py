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

path_dir_120 = os.path.join(path_data, 'data_maps', 'ROUTE120_WGS84')
path_120_rte = os.path.join(path_dir_120, 'TRONCON_ROUTE')
path_120_nod = os.path.join(path_dir_120, 'NOEUD_ROUTIER')

m_fra.readshapefile(path_120_rte, 'routes_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_120_nod, 'noeuds_fr', color = 'none', zorder=2)

# http://professionnels.ign.fr/sites/default/files/DC_ROUTE120-1-1.pdf

## Nod is "ponctuel" and Rte "lineaire" acoording to official doc
## Check it though...
#dict_nod_rte = {}
#for i, ls_nod_coord in enumerate(m_fra.noeuds_fr):
#  for j, ls_ls_rte_coord in enumerate(m_fra.routes_fr):
#    if ls_nod_coord in ls_ls_rte_coord:
#      dict_nod_rte.setdefault(i, []).append(j)
#enc_json(dict_nod_rte, os.path.join(path_built, 'dict_nod_rte.json'))

dict_nod_rte = dec_json(os.path.join(path_built, 'dict_nod_rte.json'))

dict_rte_nod = {}
for nod, ls_rtes in dict_nod_rte.items():
  for rte in ls_rtes:
    dict_rte_nod.setdefault(rte, []).append(nod)

# check nb of nodes per road... hopefully one or two
dict_nb_nod = {}
for rte, ls_nods in dict_rte_nod.items():
  dict_nb_nod.setdefault(len(ls_nods), []).append(rte)
# 1 node : 7 (check?), 2 nodes: 41948 (normal)
# 4 nodes: 1 road, 3 nodes: 73 roads... see what to do

# temp fix: real weight for extremities... ortherwise somewhat random
# would be good to visualize them

# todo: dict of dict: node to node with weight (double sens?)
# http://code.activestate.com/recipes/119466-dijkstras-algorithm-for-shortest-paths/
