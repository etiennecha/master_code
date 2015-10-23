#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
from functions_maps import *
import os, sys
import re
import numpy as np
import datetime as datetime
import pandas as pd
import matplotlib.pyplot as plt
import pprint
import matplotlib.cm as cm
from matplotlib.colors import Normalize
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
from pysal.esda.mapclassify import Natural_Breaks as nb
from matplotlib import colors

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_built_graphs = os.path.join(path_built,
                                 'data_graphs')

path_insee_extracts = os.path.join(path_data,
                                   'data_insee',
                                   'data_extracts')

path_geo_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_geo_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')

# ########################
# LOAD DATA AND GEO FRANCE
# ########################

# LSA Data

df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa.csv'),
                     dtype = {u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

geo_france = GeoFrance(path_dpt = path_geo_dpt,
                       path_com = path_geo_com)
df_dpt = geo_france.df_dpt
df_com = geo_france.df_com

df_lsa['point'] = df_lsa[['longitude', 'latitude']].apply(\
                   lambda x: Point(geo_france.m_fra(x[0], x[1])), axis = 1)

# #########################
# MAPS: COMPETITION
# #########################

# Load competition at municipality level
df_comp = pd.read_csv(os.path.join(path_built_csv,
                                   '201407_competition',
                                   'df_mun_prospect_comp.csv'),
                      dtype = {'c_insee' : str},
                      encoding = 'UTF-8')
# temp: should be useless (final final should have one line per c_insee)
df_comp.drop_duplicates('c_insee', inplace = True)

# caution: can be several polygons by com
df_comp = pd.merge(df_com[['c_insee', 'poly']],
                   df_comp,
                   on = 'c_insee',
                   how = 'left')
df_comp.set_index('c_insee', inplace = True)

# Pbm: 0 is replaced by nan to generate map
# Get rid of 0 in Closest store or find a more general fix
df_comp.loc[df_comp['dist_any'] == 0, 'dist_any'] = 0.01

df_comp.rename(columns = {'hhi' : 'HHI',
                         'dist_any' : 'Closest store',
                         'available_surface': 'Available surface',
                         'nb_stores' : 'Nb stores',
                         'cr1' : 'CR1',
                         'cr2' : 'CR2',
                         'cr3' : 'CR3'}, inplace = True)

# todo: format legend
for field in ['CR1', 'CR2', 'CR3', 'HHI',
              'Nb stores', 'Closest store', 'Available surface']:
  
  # zero excluded from natural breaks... specific class with val -1 (added later)
  df_comp.replace(to_replace={field: {0: np.nan}}, inplace=True)
  
  # generate natural breaks (slight bias due to multiplicity of polygons per municipality)
  breaks = nb(df_comp[df_comp[field].notnull()][field].values,
              initial=20,
              k=5)
  
  # the notnull method lets us match indices when joining
  jb = pd.DataFrame({'jenks_bins': breaks.yb},
                    index = df_comp[df_comp[field].notnull()].index.values)
  
  # need to drop duplicate index in jb
  jb = jb.reset_index().drop_duplicates(subset=['index'],
                                        take_last=True).set_index('index')
  # propagated to all rows in df_comp with same index
  df_comp['jenks_bins'] = jb['jenks_bins']
  df_comp.jenks_bins.fillna(-1, inplace=True)
  
  jenks_labels = ["<= {:0.2f} {:s} ({:d} mun.)".format(b, field, c) for b, c in zip(
                    breaks.bins, breaks.counts)]
  
  # if there are 0
  if len(df_comp[df_comp[field].isnull()]) != 0:
    jenks_labels.insert(0, 'Null ({:5d} mun.)'.format(len(df_comp[df_comp[field].isnull()])))
  
  plt.clf()
  fig = plt.figure()
  ax = fig.add_subplot(111, axisbg='w', frame_on=False)
  
  # use a blue colour ramp - we'll be converting it to a map using cmap()
  cmap = plt.get_cmap('Blues')
  # draw wards with grey outlines
  df_comp['patches'] = df_comp['poly'].map(lambda x:\
                        PolygonPatch(x, ec='#555555', lw=.03, alpha=1., zorder=4))
  pc = PatchCollection(df_comp['patches'], match_original=True)
  # impose our colour map onto the patch collection
  norm = Normalize()
  pc.set_facecolor(cmap(norm(df_comp['jenks_bins'].values)))
  ax.add_collection(pc)
  
  df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                        PolygonPatch(x, fc = 'none', ec='#000000', lw=.2, alpha=1., zorder=1))
  pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
  ax.add_collection(pc_2)
  
  # Add a colour bar
  cb = colorbar_index(ncolors=len(jenks_labels), cmap=cmap, shrink=0.5, labels=jenks_labels)
  cb.ax.tick_params(labelsize=6)
  
  # Add scale
  geo_france.m_fra.drawmapscale(-3.,
                                43.,
                                3.,
                                46.5,
                                100.,
                                barstyle='fancy', labelstyle='simple',
                                fillcolor1='w', fillcolor2='#555555',
                                fontcolor='#555555',
                                zorder=5)
  
  #ax.autoscale_view(True, True, True)
  #plt.axis('off')
  plt.title('%s by municipality' %field)
  plt.tight_layout()
  # fig.set_size_inches(7.22, 5.25) # set the image width to 722px
  plt.savefig(os.path.join(path_built_graphs,
                           'overview',
                           'competition',
                           '%s.png' %field),
              dpi=300,
              alpha=True)
  plt.close()

# ###############
# BACKUP MAP CODE
# ###############

# HEATMAPS (PBM TO RESPECT DIMENSIONS?)

# http://bagrow.com/dsv/heatmap_basemap.html

# use dpt path as background
df_dpt['patches'] = df_dpt['poly'].map(\
                      lambda x: PolygonPatch(x,
                                             facecolor='#FFFFFF', # '#555555'
                                             edgecolor='#787878', # '#787878'
                                             lw=.2, alpha=.3, zorder=1))

import scipy.ndimage as ndi
x1 = -5. # todo: get it from geo_france.m_fra
x2 = 9.
y1 = 42.
y2 = 51.5
ll_corner = geo_france.m_fra(x1, y1)
ur_corner = geo_france.m_fra(x2, y2)
w2 = ur_corner[0] - ll_corner[0]
h2 = ur_corner[1] - ll_corner[1]

for retail_group in df_lsa['groupe_alt'].unique():
  c = 0
  img = np.zeros((h2/1000, w2/1000))
  for station in df_lsa['point'][df_lsa['groupe'] == retail_group]:
    yn = (station.y - ll_corner[1]) / 1000
    xn = (station.x - ll_corner[0]) / 1000
    try:
      img[yn, xn] += 1
    except:
      c=+1
  img = ndi.gaussian_filter(img, (100,100))

  plt.clf()
  fig = plt.figure()
  ax = fig.add_subplot(111, aspect='equal', frame_on = False)
  plt.imshow(img,
             origin = 'lower',
             zorder = 0,
             extent = [ll_corner[0],
                       ur_corner[0],
                       ll_corner[1],
                       ur_corner[1]])
  plt.axis('off')
  ##plt.imshow(img, origin = 'lower', zorder = 0,  extent = [0, ur_corner[0], 0, ur_corner[1]]) 
  ax.add_collection(PatchCollection(df_dpt['patches'].values,
                                    match_original = True))

  # plt.tight_layout()
  # plt.show()
  #ax.set_axes(plt.Axes(fig, [0., 0., 1., 1.])) # work on this line to get rid of black
  ax.set_axis_off()
  #ax.autoscale(False)
  ax.autoscale_view(True, True, True)
  extent = ax.get_window_extent().transformed(plt.gcf().dpi_scale_trans.inverted())
  plt.savefig(os.path.join(path_built_graphs,
                           'overview',
                           'group_locations',
                           '{:s}.png'.format(retail_group)),
              transparent = True,
              bbox_inches = extent)
  plt.close()

# todo: by commune / dpt / region / au / uu maps (with clear scale)

# DISPLAY FRA MUNICIPALITY PATCHES (TEST: MOVE?)

df_com['patches'] = df_com['poly'].map(\
                      lambda x: PolygonPatch(x,
                                             facecolor='#FFFFFF', # '#555555'
                                             edgecolor='#787878', # '#787878'
                                             lw=.1, alpha=.3, zorder=2))

fig = plt.figure()
ax = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
p = PatchCollection(df_com['patches'].values, match_original = True)
ax.add_collection(p)
#geo_france.m_fra.drawcountries()
#geo_france.m_fra.drawcoastlines()
ax.autoscale_view(True, True, True)
ax.axis('off')
plt.tight_layout()
# plt.show()
plt.savefig(os.path.join(path_built_graphs,
                         'overview',
                         'test',
                         'test_fra_com_patches.png'),
            transparent = True,
            dpi=700)

# TEST FRA MUNICIPALITY PATCHES (TEST: MOVE?)

df_dpt['patches'] = df_dpt['poly'].map(\
                      lambda x: PolygonPatch(x,
                                             facecolor='#FFFFFF', # '#555555'
                                             edgecolor='#787878', # '#787878'
                                             lw=.2, alpha=.3, zorder=1))
fig = plt.figure()
ax = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
p = PatchCollection(df_dpt['patches'].values, match_original = True)
ax.add_collection(p)
#geo_france.m_fra.drawcountries()
#geo_france.m_fra.drawcoastlines()
ax.autoscale_view(True, True, True)
ax.axis('off')
plt.tight_layout()
# plt.show()
plt.savefig(os.path.join(path_built_graphs,
                         'overview',
                         'test',
                         'test_fra_dpt_patches.png'),
            transparent = True,
            dpi=700)
