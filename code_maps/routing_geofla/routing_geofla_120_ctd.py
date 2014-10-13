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

ls_files_120 = [('TRONCON_ROUTE', 'routes'),
                ('NOEUD_ROUTIER', 'noeuds'),
                ('COMMUNE', 'communes'),
                ('RATTACHEMENT_COMMUNE', 'rat_com')]

for file_120_orig, file_120_dest in ls_files_120:
  m_fra.readshapefile(os.path.join(path_dir_120, file_120_orig),
                      file_120_dest,
                      color = 'none',
                      zorder = 2)

# http://professionnels.ign.fr/sites/default/files/DC_ROUTE120-1-1.pdf

# Base files for which ID_RTE_2010 is a key
ls_120_main = [('routes', m_fra.routes, m_fra.routes_info),
               ('noeuds', m_fra.noeuds, m_fra.noeuds_info),
               ('communes', m_fra.communes, m_fra.communes_info)]
dict_120_main = {}
for field, ls_field_geo, ls_field_info in ls_120_main:
  dict_120_main[field] = {}
  # position i should not be used... just bu
  for i, (geo, info) in enumerate(zip(ls_field_geo, ls_field_info)):
    dict_120_main[field][info['ID_RTE120']] = [geo, info, i]

# Annex files which refer to base files via ID_RTE_2010 (tgus not nec. unique)
ls_120_sub = [('rat_com', m_fra.rat_com, m_fra.rat_com_info)]
dict_120_sub = {}
for field, ls_field_geo, ls_field_info in ls_120_sub:
  dict_120_sub[field] = {}
  for i, (geo, info) in enumerate(zip(ls_field_geo, ls_field_info)):
    dict_120_sub[field].setdefault(info['ID_RTE120'], []).append([geo, info, i])

## Noeud is "ponctuel" and Route "lineaire" acoording to official doc
## Building graph requires to know connections between nodes
## i.e. check if node coordinates are in roads (takes c. 10 mins this way at CREST)
#dict_120_node_routes, dict_120_route_nodes = {}, {}
#for node_id, node_info in dict_120_main['noeuds'].items():
#  for road_id, road_info in dict_120_main['routes'].items():
#    if node_info[0] in road_info[0]:
#      dict_120_node_routes.setdefault(node_id, []).append(road_id)
#      dict_120_route_nodes.setdefault(road_id, []).append(node_id)
#enc_json(dict_120_node_routes, os.path.join(path_built, 'dict_120_node_routes.json'))
#enc_json(dict_120_route_nodes, os.path.join(path_built, 'dict_120_route_nodes.json'))

dict_120_node_routes = dec_json(os.path.join(path_built, 'dict_120_node_routes.json'))
dict_120_route_nodes = dec_json(os.path.join(path_built, 'dict_120_route_nodes.json'))

# JSON stores keys as string: convert back?
for k,v in dict_120_node_routes.items():
  dict_120_node_routes[int(k)] = v
  del(dict_120_node_routes[k])

for k,v in dict_120_route_nodes.items():
  dict_120_route_nodes[int(k)] = v
  del(dict_120_route_nodes[k])

# Nb of nodes per road
dict_nb_route_nodes = {}
for route_id, ls_node_ids in dict_120_route_nodes.items():
  dict_nb_route_nodes.setdefault(len(ls_node_ids), []).append(route_id)
# 1 node : 7 (check?), 2 nodes: 41948 (normal)
# 4 nodes: 1 road, 3 nodes: 73 roads... see what to do

# todo: take care of cases with more than 2 nodes (build graph + dijkstra)

# Dict node to node with weight (double sens?)

# Types of roads?
dict_desc_roads = {}
for field in ['CLASS_ADM', 'VOCATION']:
  dict_desc_roads[field] = {}
  for route_id, route_info in dict_120_main['routes'].items():
    dict_desc_roads[field].setdefault(route_info[1][field], []).append(route_id)

# todo: take location into account?
# todo: update dict_120_main['routes']
def compute_weight(road_length, road_type):
  dict_speed = {u'Autoroute' : 120.0,
                u'Nationale' : 100.0,
                u'Départementale' : 80.0,
                u'Sans objet': 60.0}
  return np.round(road_length / dict_speed[road_type], 2)

# Only if two nodes (todo: restriction to first and last should be ok)
dict_graph, dict_graph_nx = {}, {}
for route_id, ls_node_ids in dict_120_route_nodes.items():
  ls_node_ids = ls_node_ids[:1] + ls_node_ids[-1:]
  if len(ls_node_ids) == 2:
    dist = compute_weight(dict_120_main['routes'][route_id][1]['LONGUEUR'],
                          dict_120_main['routes'][route_id][1]['CLASS_ADM'].decode('latin-1'))
    dict_graph.setdefault(ls_node_ids[0], {}).update({ls_node_ids[1] : dist})
    dict_graph.setdefault(ls_node_ids[1], {}).update({ls_node_ids[0] : dist})
    dict_graph_nx.setdefault(ls_node_ids[0], {}).\
        update({ls_node_ids[1] : {'weight' : dist}})
    dict_graph_nx.setdefault(ls_node_ids[1], {}).\
        update({ls_node_ids[0] : {'weight' : dist}})

# ARTISANAL:
# http://code.activestate.com/recipes/119466-dijkstras-algorithm-for-shortest-paths/
#from shortest_path import *
#print shortestPath(dict_graph, '0', '1000')

## NETWORKX (PACKAGE)
## http://en.wikipedia.org/wiki/Shortest_path_problem
## all pairs: http://en.wikipedia.org/wiki/Floyd%E2%80%93Warshall_algorithm
## http://en.wikipedia.org/wiki/NetworkX
## networkx reference doc: p316
## might want to use a directed graph
#import networkx as nx
#G = nx.Graph(dict_graph_nx)
#print nx.dijkstra_path(G, 1, 1000)
#test_all_len = nx.all_pairs_dijkstra_path_length(G)
#enc_json(dict_all_len, os.path.join(path_built, 'dict_all_len_hours.json'))

## took roughly half a day

# Each commune attached to a node
# Option 1: compute shortest path between all nodes
# Option 2: compute shortest path only beween nodes associated to a commune
# Then by commune check min dist by adding dist to connection nodes

# Stores: add distance to chef lieu of commune? Neglect it first?
ls_com_nodes = []
for commune_id, commune_rat_info in dict_120_sub['rat_com'].items():
  for rat in commune_rat_info:
    ls_com_nodes.append(rat[1]['ID_ND_RTE'])
ls_com_nodes = list(set(ls_com_nodes))

dict_all_len = dec_json(os.path.join(path_built, 'dict_all_len_hours.json'))

## Nodes connected to municipalities
#ls_com_nodes_str = ['%s' %x for x in ls_com_nodes]
#ls_com_len = [[dict_all_len[i].get(j, np.nan) for j in ls_com_nodes_str]\
#                for i in ls_com_nodes_str]
#ar_com_len = np.array(ls_com_len)
#np.save(os.path.join(path_built, 'ar_com_len_hours.npy'), ar_com_len)
#enc_json(ls_com_nodes_str, os.path.join(path_built, 'ls_com_nodes_str.json'))

## All nodes
#ls_all_nodes_str = dict_all_len.keys()
#ls_all_len = [[dict_all_len[i].get(j, np.nan) for j in ls_all_nodes_str]\
#                for i in ls_all_nodes_str]
#ar_all_len = np.array(ls_all_len)
#np.save(os.path.join(path_built, 'ar_all_len_hours.npy'), ar_all_len)
#enc_json(ls_all_nodes_str, os.path.join(path_built, 'ls_all_nodes_str.json'))
