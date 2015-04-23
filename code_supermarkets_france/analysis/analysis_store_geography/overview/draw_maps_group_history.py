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

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

# #############
# LOAD DATA
# #############

x1 = -4.8
x2 = 8.3
y1 = 42.4
y2 = 51.2

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
df_lsa = pd.read_csv(os.path.join(path_dir_built_csv, 'df_lsa_active_fm_hsx.csv'),
                     encoding = 'UTF-8',
                     dtype = {'Code INSEE' : str,
                              'Code INSEE ardt' : str,
                              'Code postal' : str},
                     parse_dates = [u'DATE ouv', u'DATE ferm', u'DATE réouv'])

df_lsa['point'] = df_lsa[['Longitude', 'Latitude']].apply(\
                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)

# ##############
# DATA TREATMENT
# ##############

# MATCH LSA INSEE CODES WITH GEO FLA COM INSEE CODES
df_com.set_index('insee_code', inplace = True)

#df_lsa['Code INSEE ardt'] = df_lsa['Code INSEE ardt'].apply(lambda x : u'{:05d}'.format(x))
#df_lsa['Code INSEE'] = df_lsa['Code INSEE ardt'].apply(lambda x : u'{:05d}'.format(x))
#df_lsa['Code postal'] = df_lsa['Code postal'].apply(lambda x : u'{:05d}'.format(x))

se_ci_vc = df_lsa['Code INSEE ardt'].value_counts()
ls_pbms = [insee_code for insee_code in df_lsa['Code INSEE ardt'].unique()\
             if insee_code not in df_com.index]

# NB STORES BY COMMUNE
df_com['nb_stores'] = se_ci_vc

# SURFACE BY COMMUNE
df_com['store_surface'] =\
   df_lsa[['Code INSEE ardt', 'Surf Vente']].groupby('Code INSEE ardt').agg(np.sum)['Surf Vente']

# INSEE AREAS (TODO: check if necessary here: move?)
df_insee_a = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_insee_areas.csv'),
                         encoding = 'UTF-8')
# Get rid of Corsica and DOMTOM
df_insee_a = df_insee_a[~(df_insee_a['CODGEO'].str.slice(stop = -3).isin(['2A', '2B', '97']))]
# Add big city ardts
ls_insee_ardts = [['75056', ['{:5d}'.format(i) for i in range(75101, 75121)]],
                  ['69123', ['{:5d}'.format(i) for i in range(69381, 69390)]],
                  ['13055', ['{:5d}'.format(i) for i in range(13201, 13217)]]]
for ic_main, ls_ic_ardts in ls_insee_ardts:
  df_temp = df_insee_a[df_insee_a['CODGEO'] == ic_main].copy()
  for ic_ardt in ls_ic_ardts:
    df_temp['CODGEO'] = ic_ardt
    df_insee_a = pd.concat([df_insee_a, df_temp])

df_lsa = pd.merge(df_insee_a,
                  df_lsa,
                  left_on = 'CODGEO',
                  right_on = 'Code INSEE',
                  how = 'right')

# #########################
# ADD DECADE
# #########################

df_lsa['DEC ouv'] = np.nan
ls_decades = [(1890, 1950)] + [(1900+i, 1910+i) for i in range(50, 120, 10)]
for date_a, date_b in ls_decades:
  df_lsa.loc[(df_lsa['DATE ouv'] > u"{:d}".format(date_a)) &\
             (df_lsa['DATE ouv'] <= u"{:d}".format(date_b)), 'DEC ouv'] = date_a
# All
df_lsa_dec_ouv = df_lsa[['DEC ouv', 'Groupe_alt']].groupby('DEC ouv').agg([len])

# By retail group
ls_se_decade = []
for rg in df_lsa['Groupe_alt'].unique():
  df_rg_dec_ouv = df_lsa[['DEC ouv', 'Groupe_alt']][df_lsa['Groupe_alt'] == rg]\
                    .groupby('DEC ouv').agg([len])
  ls_se_decade.append(df_rg_dec_ouv['Groupe_alt']['len'])
df_rgs = pd.concat(ls_se_decade, axis = 1, keys = df_lsa['Groupe_alt'].unique())


# #########################
# MAPS
# #########################

#gs1 = matplotlib.gridspec.GridSpec(2, 2)
#gs1.update(wspace=0.0, hspace=0.0)

#ax = fig.add_subplot(111, axisbg='w', frame_on=False)

ls_hd_dates = ['1992', '1995', '2000', '2005', '2010', '2015']
dict_maps  = {'LIDL' : ls_hd_dates,
              'ALDI' : ls_hd_dates}

for rg, ls_dates in dict_maps.items():
  
  plt.clf()
  fig = plt.figure()
  
  # UPPER LEFT
  ax1 = fig.add_subplot(321, aspect = 'equal') #, frame_on = False)
  se1 = df_lsa[(df_lsa['Groupe_alt'] == rg) &\
               (df_lsa['DATE ouv'] <= ls_dates[0])]['point']
  ax1.scatter([store.x for store in se1],
              [store.y for store in se1],
              3, marker = 'o', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                        PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
  pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
  ax1.add_collection(pc_2)
  ax1.autoscale_view(True, True, True)
  ax1.axis('off')
  ax1.set_title(ls_dates[0], loc = 'left')
  
  # UPPER RIGHT
  ax2 = fig.add_subplot(322, aspect = 'equal') #, frame_on = False)
  se_b = df_lsa[(df_lsa['Groupe_alt']== rg) &\
                (df_lsa['DATE ouv'] <= ls_dates[0])]['point']
  se_a = df_lsa[(df_lsa['Groupe_alt']== rg) &\
                (df_lsa['DATE ouv'] > ls_dates[0]) &\
                (df_lsa['DATE ouv'] <= ls_dates[1])]['point']
  ax2.scatter([store.x for store in se_b],
              [store.y for store in se_b],
              3, marker = 'o', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  ax2.scatter([store.x for store in se_a],
              [store.y for store in se_a],
              3, marker = 'o', lw=0.25, facecolor = '#C80000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                        PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
  pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
  ax2.add_collection(pc_2)
  ax2.autoscale_view(True, True, True)
  ax2.axis('off')
  ax2.set_title(ls_dates[1], loc = 'left')
  
  # MID LEFT
  ax3 = fig.add_subplot(323, aspect = 'equal') #, frame_on = False)
  se_b = df_lsa[(df_lsa['Groupe_alt']== rg) &\
                (df_lsa['DATE ouv'] <= ls_dates[1])]['point']
  se_a = df_lsa[(df_lsa['Groupe_alt']== rg) &\
                (df_lsa['DATE ouv'] > ls_dates[1]) &\
                (df_lsa['DATE ouv'] <= ls_dates[2])]['point']
  ax3.scatter([store.x for store in se_b],
              [store.y for store in se_b],
              3, marker = 'o', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  ax3.scatter([store.x for store in se_a],
              [store.y for store in se_a],
              3, marker = 'o', lw=0.25, facecolor = '#C80000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                        PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
  pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
  ax3.add_collection(pc_2)
  ax3.autoscale_view(True, True, True)
  ax3.axis('off')
  ax3.set_title(ls_dates[2], loc = 'left')
  
  # MID RIGHT
  ax4 = fig.add_subplot(324, aspect = 'equal') #, frame_on = False)
  se_b = df_lsa[(df_lsa['Groupe_alt']== rg) &\
                (df_lsa['DATE ouv'] <= ls_dates[2])]['point']
  se_a = df_lsa[(df_lsa['Groupe_alt']== rg) &\
                (df_lsa['DATE ouv'] > ls_dates[2]) &\
                (df_lsa['DATE ouv'] <= ls_dates[3])]['point']
  ax4.scatter([store.x for store in se_b],
              [store.y for store in se_b],
              3, marker = 'o', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  ax4.scatter([store.x for store in se_a],
              [store.y for store in se_a],
              3, marker = 'o', lw=0.25, facecolor = '#C80000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                        PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
  pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
  ax4.add_collection(pc_2)
  ax4.autoscale_view(True, True, True)
  ax4.axis('off')
  ax4.set_title(ls_dates[3], loc = 'left')
  
  # LOW LEFT
  ax5 = fig.add_subplot(325, aspect = 'equal') #, frame_on = False)
  se_b = df_lsa[(df_lsa['Groupe_alt']== rg) &\
                (df_lsa['DATE ouv'] <= ls_dates[3])]['point']
  se_a = df_lsa[(df_lsa['Groupe_alt']== rg) &\
                (df_lsa['DATE ouv'] > ls_dates[3]) &\
                (df_lsa['DATE ouv'] <= ls_dates[4])]['point']
  ax5.scatter([store.x for store in se_b],
              [store.y for store in se_b],
              3, marker = 'o', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  ax5.scatter([store.x for store in se_a],
              [store.y for store in se_a],
              3, marker = 'o', lw=0.25, facecolor = '#C80000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                        PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
  pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
  ax5.add_collection(pc_2)
  ax5.autoscale_view(True, True, True)
  ax5.axis('off')
  ax5.set_title(ls_dates[4], loc = 'left')
  
  # LOW RIGHT
  ax6 = fig.add_subplot(326, aspect = 'equal') #, frame_on = False)
  se_b = df_lsa[(df_lsa['Groupe_alt']== rg) &\
                (df_lsa['DATE ouv'] <= ls_dates[4])]['point']
  se_a = df_lsa[(df_lsa['Groupe_alt']== rg) &\
                (df_lsa['DATE ouv'] > ls_dates[4]) &\
                (df_lsa['DATE ouv'] <= ls_dates[5])]['point']
  ax6.scatter([store.x for store in se_b],
              [store.y for store in se_b],
              3, marker = 'o', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  ax6.scatter([store.x for store in se_a],
              [store.y for store in se_a],
              3, marker = 'o', lw=0.25, facecolor = '#C80000', edgecolor = 'w', alpha = 0.9,
              antialiased = True, zorder = 3)
  df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                        PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
  pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
  ax6.add_collection(pc_2)
  ax6.autoscale_view(True, True, True)
  ax6.axis('off')
  ax6.set_title(ls_dates[5], loc = 'left')
  
  plt.subplots_adjust(left=.1, right=0.95, bottom=0.1, top=0.95, wspace=0, hspace=0)
  plt.tight_layout()
  fig.set_size_inches(10, 15) # set the image width to 722px
  
  #plt.show()
  
  plt.savefig(os.path.join(path_data,
                           'data_maps',
                           'data_built',
                           'graphs',
                           'lsa',
                           'history',
                           '%s.png' %rg),
              dpi=300,
              alpha=True,
              bbox_inches = 'tight')
