#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import datetime as datetime
import pandas as pd
import matplotlib.pyplot as plt
import pprint
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

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_png = os.path.join(path_dir_qlmc, 'data_built' , 'data_png')

path_dir_source_lsa = os.path.join(path_dir_qlmc, 'data_source', 'data_lsa_xls')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

# #############
# LOAD DATA
# #############

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

# Departments
path_dir_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
m_fra.readshapefile(path_dir_dpt, 'dpt', color = 'none', zorder=2)

df_dpt = pd.DataFrame({'poly'     : [Polygon(xy) for xy in m_fra.dpt],
                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.dpt_info],
                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.dpt_info],
                       'reg_name' : [d['NOM_REGION'] for d in m_fra.dpt_info],
                       'reg_code' : [d['CODE_REG'] for d in m_fra.dpt_info]})

df_dpt = df_dpt[df_dpt['reg_name'] != 'CORSE']

# Communes
path_dir_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')
m_fra.readshapefile(path_dir_dpt, 'com', color = 'none', zorder=2)

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


# LSA Data
df_lsa_int = pd.read_csv(os.path.join(path_dir_built_csv, 'df_lsa_int.csv'),
                         encoding = 'UTF-8')
df_lsa_gps = df_lsa_int[(df_lsa_int['Type_alt'] != 'DRIN') &\
                        (df_lsa_int['Type_alt'] != 'DRIVE')]

df_lsa_gps['point'] = df_lsa_gps[['Longitude', 'Latitude']].apply(\
                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)

# #########################
# MAPS
# #########################

# MAPS BY COMMUNES

## FRA
#
#df_com['patches'] = df_com['poly'].map(\
#                      lambda x: PolygonPatch(x,
#                                             facecolor='#FFFFFF', # '#555555'
#                                             edgecolor='#787878', # '#787878'
#                                             lw=.1, alpha=.3, zorder=2))
#
#fig = plt.figure()
#ax = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
#p = PatchCollection(df_com['patches'].values, match_original = True)
#ax.add_collection(p)
##m_fra.drawcountries()
##m_fra.drawcoastlines()
#ax.autoscale_view(True, True, True)
#ax.axis('off')
#plt.tight_layout()
## plt.show()
#plt.savefig(os.path.join(path_data, 'data_maps', 'data_built',
#                         'graphs', 'lsa', 'fra_com.png'),
#            transparent = True,
#            dpi=700)


#MAPS BY DPT

## FRA
#
#df_dpt['patches'] = df_dpt['poly'].map(\
#                      lambda x: PolygonPatch(x,
#                                             facecolor='#FFFFFF', # '#555555'
#                                             edgecolor='#787878', # '#787878'
#                                             lw=.2, alpha=.3, zorder=1))
#fig = plt.figure()
#ax = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
#p = PatchCollection(df_dpt['patches'].values, match_original = True)
#ax.add_collection(p)
##m_fra.drawcountries()
##m_fra.drawcoastlines()
#ax.autoscale_view(True, True, True)
#ax.axis('off')
#plt.tight_layout()
## plt.show()
#plt.savefig(os.path.join(path_data, 'data_maps', 'data_built',
#                         'graphs', 'lsa', 'fra_dpt.png'),
#            transparent = True,
#            dpi=700)


# HEATMAPS

path_dir_heatmaps = os.path.join(path_data, 'data_maps', 'data_built',
                                 'graphs', 'lsa', 'heatmaps')

# use dpt path as background
df_dpt['patches'] = df_dpt['poly'].map(\
                      lambda x: PolygonPatch(x,
                                             facecolor='#FFFFFF', # '#555555'
                                             edgecolor='#787878', # '#787878'
                                             lw=.2, alpha=.3, zorder=1))

import scipy.ndimage as ndi
ll_corner = m_fra(x1, y1)
ur_corner = m_fra(x2, y2)
w2 = ur_corner[0] - ll_corner[0]
h2 = ur_corner[1] - ll_corner[1]

for retail_group in df_lsa_gps['Groupe'].unique():
  c = 0
  img = np.zeros((h2/1000, w2/1000))
  for station in df_lsa_gps['point'][df_lsa_gps['Groupe'] == retail_group]:
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
  plt.savefig(os.path.join(path_dir_heatmaps, '%s.png' % retail_group),
              transparent = True,
              bbox_inches = extent)

# todo: by commune / dpt / region / au / uu maps (with clear scale)
