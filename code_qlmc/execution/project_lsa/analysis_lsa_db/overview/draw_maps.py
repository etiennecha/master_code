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
#import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
from pysal.esda.mapclassify import Natural_Breaks as nb
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
y1 = 42.
y2 = 51.5

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

df_com = df_com[df_com['reg_name'] != 'CORSE']


# LSA Data
df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_lsa_active_fm_hsx.csv'),
                     dtype = {'Code INSEE' : str,
                              'Code INSEE ardt' : str},
                     encoding = 'UTF-8')

df_lsa['point'] = df_lsa[['Longitude', 'Latitude']].apply(\
                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)

# ##############
# DATA TREATMENT
# ##############

# Nb stores by commune
se_ci_vc = df_lsa['Code INSEE ardt'].value_counts()
df_com.set_index('insee_code', inplace = True)
df_com['nb_stores'] = se_ci_vc

# Read df_com_comp
df_com_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                       'df_com_comp.csv'),
                          dtype = {'code_insee' : str},
                          encoding = 'UTF-8')
df_com_comp.set_index('code_insee', inplace = True)

df_com = pd.merge(df_com, df_com_comp,
                  left_index = True, right_index = True)

# #########################
# MAPS: COMPETITION
# #########################

# Pbm: 0 is replaced by nan to generate map
# Get rid of 0 in Closest store or find a more general fix
df_com.loc[df_com['All_dist'] == 0, 'All_dist'] = 0.01

df_com.rename(columns = {'hhi' : 'HHI',
                         'All_dist' : 'Closest store',
                         'avail_surf': 'Available surface',
                         'nb_stores' : 'Nb stores'}, inplace = True)

# TODO: format legend
for field in ['CR1', 'CR2', 'CR3', 'HHI',
              'Nb stores', 'Closest store', 'Available surface']:
  
  # zero excluded from natural breaks... specific class with val -1 (added later)
  df_com.replace(to_replace={field: {0: np.nan}}, inplace=True)
  
  # generate natural breaks
  breaks = nb(df_com[df_com[field].notnull()][field].values,
              initial=20,
              k=5)
  
  # the notnull method lets us match indices when joining
  jb = pd.DataFrame({'jenks_bins': breaks.yb},
                    index=df_com[df_com[field].notnull()].index)
  
  # need to drop duplicate index in jb
  jb = jb.reset_index().drop_duplicates(subset=['index'],
                                        take_last=True).set_index('index')
  # propagated to all rows in df_com with same index
  df_com['jenks_bins'] = jb['jenks_bins']
  df_com.jenks_bins.fillna(-1, inplace=True)
  
  jenks_labels = ["<= {:0.2f} {:s} ({:d} mun.)".format(b, field, c) for b, c in zip(
                    breaks.bins, breaks.counts)]
  
  # if there are 0
  if len(df_com[df_com[field].isnull()]) != 0:
    jenks_labels.insert(0, 'Null ({:5d} mun.)'.format(len(df_com[df_com[field].isnull()])))
  
  plt.clf()
  fig = plt.figure()
  ax = fig.add_subplot(111, axisbg='w', frame_on=False)
  
  # use a blue colour ramp - we'll be converting it to a map using cmap()
  cmap = plt.get_cmap('Blues')
  # draw wards with grey outlines
  df_com['patches'] = df_com['poly'].map(lambda x:\
                        PolygonPatch(x, ec='#555555', lw=.03, alpha=1., zorder=4))
  pc = PatchCollection(df_com['patches'], match_original=True)
  # impose our colour map onto the patch collection
  norm = Normalize()
  pc.set_facecolor(cmap(norm(df_com['jenks_bins'].values)))
  ax.add_collection(pc)
  
  df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                        PolygonPatch(x, fc = 'none', ec='#000000', lw=.2, alpha=1., zorder=1))
  pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
  ax.add_collection(pc_2)
  
  # Add a colour bar
  cb = colorbar_index(ncolors=len(jenks_labels), cmap=cmap, shrink=0.5, labels=jenks_labels)
  cb.ax.tick_params(labelsize=6)
  
  # Add scale
  m_fra.drawmapscale(-3.,
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
  plt.savefig(os.path.join(path_data,
                           'data_maps',
                           'data_built',
                           'graphs',
                           'lsa',
                           'competition',
                           '%s.png' %field),
              dpi=300,
              alpha=True)
  plt.close()

# ###############
# BACKUP MAP CODE
# ###############

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

## HEATMAPS (PBM TO RESPECT DIMENSIONS?)
#
## http://bagrow.com/dsv/heatmap_basemap.html
#
#path_dir_heatmaps = os.path.join(path_data, 'data_maps', 'data_built',
#                                 'graphs', 'lsa', 'heatmaps')
#
## use dpt path as background
#df_dpt['patches'] = df_dpt['poly'].map(\
#                      lambda x: PolygonPatch(x,
#                                             facecolor='#FFFFFF', # '#555555'
#                                             edgecolor='#787878', # '#787878'
#                                             lw=.2, alpha=.3, zorder=1))
#
#import scipy.ndimage as ndi
#ll_corner = m_fra(x1, y1)
#ur_corner = m_fra(x2, y2)
#w2 = ur_corner[0] - ll_corner[0]
#h2 = ur_corner[1] - ll_corner[1]
#
#for retail_group in df_lsa['Groupe'].unique():
#  c = 0
#  img = np.zeros((h2/1000, w2/1000))
#  for station in df_lsa['point'][df_lsa['Groupe'] == retail_group]:
#    yn = (station.y - ll_corner[1]) / 1000
#    xn = (station.x - ll_corner[0]) / 1000
#    try:
#      img[yn, xn] += 1
#    except:
#      c=+1
#  img = ndi.gaussian_filter(img, (100,100))
#
#  plt.clf()
#  fig = plt.figure()
#  ax = fig.add_subplot(111, aspect='equal', frame_on = False)
#  plt.imshow(img,
#             origin = 'lower',
#             zorder = 0,
#             extent = [ll_corner[0],
#                       ur_corner[0],
#                       ll_corner[1],
#                       ur_corner[1]])
#  plt.axis('off')
#  ##plt.imshow(img, origin = 'lower', zorder = 0,  extent = [0, ur_corner[0], 0, ur_corner[1]]) 
#  ax.add_collection(PatchCollection(df_dpt['patches'].values,
#                                    match_original = True))
#
#  # plt.tight_layout()
#  # plt.show()
#  #ax.set_axes(plt.Axes(fig, [0., 0., 1., 1.])) # work on this line to get rid of black
#  ax.set_axis_off()
#  #ax.autoscale(False)
#  ax.autoscale_view(True, True, True)
#  extent = ax.get_window_extent().transformed(plt.gcf().dpi_scale_trans.inverted())
#  plt.savefig(os.path.join(path_dir_heatmaps, '%s.png' % retail_group),
#              transparent = True,
#              bbox_inches = extent)
#
## todo: by commune / dpt / region / au / uu maps (with clear scale)


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
