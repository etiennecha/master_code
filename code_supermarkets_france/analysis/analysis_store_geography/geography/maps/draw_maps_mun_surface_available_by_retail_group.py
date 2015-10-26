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
import time

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built, 'data_csv')

path_insee = os.path.join(path_data, 'data_insee')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

path_maps = os.path.join(path_data,
                         'data_maps')
path_geo_dpt = os.path.join(path_maps, 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_geo_com = os.path.join(path_maps, 'GEOFLA_COM_WGS84', 'COMMUNE')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# READ CSV FILES
# ##############

ls_rgs = [u'CARREFOUR',
          u'MOUSQUETAIRES',
          u'CASINO',
          u'LIDL',
          u'SYSTEME U',
          u'ALDI',
          u'LECLERC',
          u'AUCHAN', 
          u'LOUIS DELHAIZE',
          u'DIAPAR',
          u'COLRUYT']

df_com_rgs = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_mun_prospect_surface_available_by_group.csv'),
                         dtype = {'code_insee' : str},
                         encoding = 'utf-8')
df_com_rgs.set_index('c_insee', inplace = True)

#df_com_insee = pd.read_csv(os.path.join(path_insee_extracts,
#                                        'df_communes.csv'),
#                           dtype = {'DEP': str,
#                                    'CODGEO' : str},
#                           encoding = 'UTF-8')
#df_com_insee.set_index('CODGEO', inplace = True)


# #############
# MERGE DFS
# #############

df_com.set_index('c_insee', inplace = True)

df_com = pd.merge(df_com_rgs,
                  df_com,
                  left_index = True,
                  right_index = True,
                  how = 'right')
# not fully satisfactory... loss of polygons

ls_disp_com_rg = ['available_surface_%s' %rg for rg in ls_rgs] +\
                 ['surface_%s' %rg for rg in ls_rgs]

# ###################
# DRAW AVAIL SURFACE
# ###################

for retail_group in ls_rgs:
  field = 'available_surface_%s' %retail_group
  
  breaks = nb(df_com[df_com[field].notnull()][field].values,
              initial=20,
              k=5)
  
  # zero excluded from natural breaks... specific class with val -1 (added later)
  df_com.replace(to_replace={'surface_%s' %retail_group: {0: np.nan}}, inplace=True)
  
  # the notnull method lets us match indices when joining
  jb = pd.DataFrame({'jenks_bins': breaks.yb}, index=df_com[df_com[field].notnull()].index)
  # need to drop duplicate index in jb
  jb = jb.reset_index().drop_duplicates(subset=['index'],
                                        take_last=True).set_index('index')
  # propagated to all rows in df_com with same index
  df_com['jenks_bins'] = jb['jenks_bins']
  df_com.jenks_bins.fillna(-1, inplace=True)
  
  jenks_labels = ["<= {:,.0f} avail surf. ({:d} mun.)".format(b, c)\
                    for b, c in zip(breaks.bins, breaks.counts)]
  
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
  plt.title('Available surface by municipality: %s' %retail_group)
  plt.tight_layout()
  # fig.set_size_inches(7.22, 5.25) # set the image width to 722px
  plt.savefig(os.path.join(path_data,
                           'data_maps',
                           'data_built',
                           'graphs',
                           'lsa',
                           'available_surface',
                           '%s.png' %retail_group.replace(' ', '')),
              dpi=100,
              alpha=True)
  plt.close()

  # need to drop jenk_bins for next map
  df_com.drop('jenks_bins', axis = 1, inplace = True)

# ###################
# DRAW SURFACE
# ###################

for retail_group in ls_rgs:
  field = 'surface_%s' %retail_group
  
  breaks = nb(df_com[df_com[field].notnull()][field].values,
              initial=20,
              k=5)
  
  # zero excluded from natural breaks... specific class with val -1 (added later)
  df_com.replace(to_replace={'surface_%s' %retail_group: {0: np.nan}}, inplace=True)
  
  # the notnull method lets us match indices when joining
  jb = pd.DataFrame({'jenks_bins': breaks.yb}, index=df_com[df_com[field].notnull()].index)
  # need to drop duplicate index in jb
  jb = jb.reset_index().drop_duplicates(subset=['index'],
                                        take_last=True).set_index('index')
  # propagated to all rows in df_com with same index
  df_com['jenks_bins'] = jb['jenks_bins']
  df_com.jenks_bins.fillna(-1, inplace=True)
  
  jenks_labels = ["<= {:,.0f} sq. m. ({:d} mun.)".format(b, c)\
                    for b, c in zip(breaks.bins, breaks.counts)]
  
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
  plt.title('Surface by municipality: %s' %retail_group)
  plt.tight_layout()
  # fig.set_size_inches(7.22, 5.25) # set the image width to 722px
  plt.savefig(os.path.join(path_data,
                           'data_maps',
                           'data_built',
                           'graphs',
                           'lsa',
                           'surface',
                           '%s.png' %retail_group.replace(' ', '')),
              dpi=100,
              alpha=True)
  plt.close()
  
  # need to drop jenk_bins for next map
  df_com.drop('jenks_bins', axis = 1, inplace = True)
