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
# READ CSV FILE
# #############
df_lsa_int = pd.read_csv(os.path.join(path_dir_built_csv, 'df_lsa_int.csv'),
                         encoding = 'UTF-8')
# change name?
df_lsa_gps = df_lsa_int[(df_lsa_int['Type_alt'] != 'DRIN') &\
                        (df_lsa_int['Type_alt'] != 'DRIVE')]

# #############
# FRANCE MAP
# #############

# excludes Corsica
x1 = -4.8
x2 = 9.
y1 = 41.8
y2 = 51.

w = x2 - x1
h = y2 - y1
extra = 0.025

# Lambert conformal for France (as suggested by IGN... check WGS84 though?)
m_fra = Basemap(resolution='i',
                projection='lcc',
                ellps = 'WGS84',
                lat_1 = 44.,
                lat_2 = 49.,
                lat_0 = 46.5,
                lon_0 = 3,
                llcrnrlat=y1 - extra * h,
                urcrnrlat=y2 + extra * h,
                llcrnrlon=x1 - extra * w,
                urcrnrlon=x2 + extra * w)

path_dir_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
m_fra.readshapefile(path_dir_dpt, 'departements_fr', color = 'none', zorder=2)
df_dpt = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.departements_fr],
                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.departements_fr_info],
                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.departements_fr_info],
                       'region_name' : [d['NOM_REGION'] for d in m_fra.departements_fr_info],
                       'region_code' : [d['CODE_REG'] for d in m_fra.departements_fr_info]})
df_dpt['patches'] = df_dpt['poly'].map(lambda x: PolygonPatch(x,
                                                              facecolor='#FFFFFF', # '#555555'
                                                              edgecolor='#555555', # '#787878'
                                                              lw=.25, alpha=.3, zorder=1))

df_lsa_gps['point'] = df_lsa_gps[['Longitude', 'Latitude']].apply(\
                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)

# TODO: improve design and loop to generate group maps
# TODO: by commune / dpt / region / au / uu maps (with clear scale)

import scipy.ndimage as ndi
#ll_corner = m_fra(x1 - extra *w, y1 - extra *1)
#ur_corner = m_fra(x2 + extra *w, y2 + extra * h)
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
  ax = fig.add_subplot(111, axisbg = 'w', frame_on = False)
  plt.imshow(img,
             origin = 'lower',
             zorder = 0,
             extent = [ll_corner[0],
                       ur_corner[0],
                       ll_corner[1],
                       ur_corner[1]])
  #plt.imshow(img, origin = 'lower', zorder = 0,  extent = [0, ur_corner[0], 0, ur_corner[1]]) 
  ax.add_collection(PatchCollection(df_dpt['patches'].values,
                                    match_original = True))
  # plt.show()
  plt.axis('off')
  plt.savefig(os.path.join(path_dir_built_png, '%s.png' % retail_group),
              bbox_inches = 'tight')
