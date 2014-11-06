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

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_png = os.path.join(path_dir_qlmc, 'data_built' , 'data_png')

path_dir_source_lsa = os.path.join(path_dir_qlmc, 'data_source', 'data_lsa_xls')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

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
                                     'df_com_avail_surf_rgs.csv'),
                         dtype = {'code_insee' : str},
                         encoding = 'utf-8')
df_com_rgs.set_index('code_insee', inplace = True)

#df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
#                                  'df_lsa_active_fm_hsx.csv'),
#                     dtype = {'Code INSEE' : str},
#                     encoding = 'UTF-8')
#df_lsa = df_lsa[(~pd.isnull(df_lsa['Latitude'])) &\
#                (~pd.isnull(df_lsa['Longitude']))].copy()
#
#df_com_insee = pd.read_csv(os.path.join(path_dir_insee_extracts,
#                                        'df_communes.csv'),
#                           dtype = {'DEP': str,
#                                    'CODGEO' : str},
#                           encoding = 'UTF-8')
#df_com_insee.set_index('CODGEO', inplace = True)

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

path_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')

m_fra.readshapefile(path_dpt, 'departements_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_com, 'communes_fr', color = 'none', zorder=2)

df_dpt = pd.DataFrame({'poly'     : [Polygon(xy) for xy in m_fra.departements_fr],
                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.departements_fr_info],
                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.departements_fr_info],
                       'reg_name' : [d['NOM_REGION'] for d in m_fra.departements_fr_info],
                       'reg_code' : [d['CODE_REG'] for d in m_fra.departements_fr_info]})

df_dpt = df_dpt[df_dpt['reg_name'] != 'CORSE']

df_com = pd.DataFrame({'poly'       : [Polygon(xy) for xy in m_fra.communes_fr],
                       'insee_code' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'com_name'   : [d['NOM_COMM'] for d in m_fra.communes_fr_info],
                       'dpt_name'   : [d['NOM_DEPT'] for d in m_fra.communes_fr_info],
                       'reg_name'   : [d['NOM_REGION'] for d in m_fra.communes_fr_info],
                       'pop'        : [d['POPULATION'] for d in m_fra.communes_fr_info],
                       'surf'       : [d['SUPERFICIE'] for d in m_fra.communes_fr_info],
                       'x_cl'       : [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl'       : [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info]})

df_com = df_com[df_com['reg_name'] != 'CORSE']

df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)

## keep only one line per commune (several polygons for some)
#df_com.sort(columns = ['insee_code', 'poly_area'],
#            ascending = False,
#            inplace = True)
#df_com.drop_duplicates(subset = 'code_insee', inplace = True)

# #############
# MERGE DFS
# #############

df_com.set_index('insee_code', inplace = True)

df_com = pd.merge(df_com_rgs, df_com,
                       left_index = True, right_index = True, how = 'right')
# not fully satisfactory... loss of polygons

ls_disp_com_rg = ['avail_surf_%s' %rg for rg in ls_rgs] +\
                 ['surf_%s' %rg for rg in ls_rgs]

# ###################
# DRAW AVAIL SURFACE
# ###################

for retail_group in ls_rgs:
  field = 'avail_surf_%s' %retail_group
  
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
                        PolygonPatch(x, ec='#555555', lw=.05, alpha=1., zorder=4))
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
                           '%s.png' %field),
              dpi=200, alpha=True)
  plt.close()

  # need to drop jenk_bins for next map
  df_com.drop('jenks_bins', axis = 1, inplace = True)

# ###################
# DRAW SURFACE
# ###################

for retail_group in ls_rgs:
  field = 'surf_%s' %retail_group
  
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
                        PolygonPatch(x, ec='#555555', lw=.05, alpha=1., zorder=4))
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
                           '%s.png' %field),
              dpi=200, alpha=True)
  plt.close()
  
  # need to drop jenk_bins for next map
  df_com.drop('jenks_bins', axis = 1, inplace = True)
