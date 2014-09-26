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
path_120_com = os.path.join(path_dir_120, 'COMMUNE')
path_120_rat = os.path.join(path_dir_120, 'RATTACHEMENT_COMMUNE')

m_fra.readshapefile(path_120_rte, 'routes_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_120_nod, 'noeuds_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_120_com, 'communes_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_120_rat, 'rat_communes_fr', color = 'none', zorder=2)

# http://professionnels.ign.fr/sites/default/files/DC_ROUTE120-1-1.pdf

## Nod is "ponctuel" and Rte "lineaire" acoording to official doc
## Check it though...
#dict_nod_rte = {}
#for i, ls_nod_coord in enumerate(m_fra.noeuds_fr):
#  for j, ls_ls_rte_coord in enumerate(m_fra.routes_fr):
#    if ls_nod_coord in ls_ls_rte_coord:
#      dict_nod_rte.setdefault(i, []).append(j)
#enc_json(dict_120_nod_rte, os.path.join(path_built, 'dict_nod_rte.json'))

dict_nod_rte = dec_json(os.path.join(path_built, 'dict_120_nod_rte.json'))

# JSON stores keys as string

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

# for now: only if two nodes
dict_graph = {}
for rte, ls_nods in dict_rte_nod.items():
  # Weight by type of road: time?
  dist = m_fra.routes_fr_info[rte]['LONGUEUR']
  if len(ls_nods) == 2:
    # Sens unique?
    dict_graph.setdefault(ls_nods[0], {}).update({ls_nods[1] : dist})
    dict_graph.setdefault(ls_nods[1], {}).update({ls_nods[0] : dist})

# Try to visualize a dpt or region with reasonable nb of communes

from shortest_path import *
print shortestPath(dict_graph, '0', '1000')

# still need to compute distance
# pbm: shortest path to all nodes?
# interesting: compare results with simple distance
# todo: visualize result (how to display road? just segments?)

# http://en.wikipedia.org/wiki/Shortest_path_problem
# all pairs: http://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm
# http://en.wikipedia.org/wiki/NetworkX

import networkx as nx

# Caution: with simple dict_graph, weight not taken into account
dict_graph_nx = {}
for k,dict_v in dict_graph.items():
  for l, u in dict_v.items():
    dict_graph_nx.setdefault(k, {})[l] = {'weight' : u}

G = nx.Graph(dict_graph_nx)
print nx.dijkstra_path(G,'0','1000')

## might want to use a directed graph
## networkx reference doc: p316
#test_all_len = nx.all_pairs_dijkstra_path_length(G)
## took roughly half a day
## need to add communes to graph
## compute shortest path between communes (only those nodes to consider)

# No offset/scale pbm in L93 coordinates
print '\n', m_fra.communes_fr_info[0]
lng, lat = m_fra(*m_fra.communes_fr[0], inverse = True)
print lat, lng

# Rattachement des communes au reseau
dict_rat_com = {}
for rat_com in m_fra.rat_communes_fr_info:
  dict_rat_com.setdefault(rat_com['ID_RTE120'],
                          {})[rat_com['ID_ND_RTE']] = rat_com['DISTANCE']

# todo:
# dict_rat_com[1] => {22256: 5.4, 22222: 5.3, 21950: 5.6}
# Commune d'identifiant 1 doit dc etre attachee a 3 noeuds ac les poids renseignes
# Question: what do coordinates in rat_com mean? (vs. those of node?)

# Match stores with closest node or project store on nearest road?
