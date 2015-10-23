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

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_built_graphs = os.path.join(path_built,
                                 'data_graphs')

path_insee = os.path.join(path_data, 'data_insee')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

path_geo_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_geo_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')

# ######################
# LOAD DATA & GEO FRANCE
# ######################

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

# ##############
# DATA TREATMENT
# ##############

# MATCH LSA INSEE CODES WITH GEO FLA COM INSEE CODES
df_com.set_index('c_insee', inplace = True)

#df_lsa['Code INSEE ardt'] = df_lsa['Code INSEE ardt'].apply(lambda x : u'{:05d}'.format(x))
#df_lsa['Code INSEE'] = df_lsa['Code INSEE ardt'].apply(lambda x : u'{:05d}'.format(x))
#df_lsa['Code postal'] = df_lsa['Code postal'].apply(lambda x : u'{:05d}'.format(x))

se_ci_vc = df_lsa['c_insee_ardt'].value_counts()
ls_pbms = [insee_code for insee_code in df_lsa['c_insee_ardt'].unique()\
             if insee_code not in df_com.index]

# NB STORES BY COMMUNE
df_com['nb_stores'] = se_ci_vc

# SURFACE BY COMMUNE
df_com['store_surface'] =\
   df_lsa[['c_insee_ardt', 'surface']].groupby('c_insee_ardt').agg(np.sum)['surface']

# INSEE AREAS (todo: check if necessary here: move?)
df_insee_a = pd.read_csv(os.path.join(path_insee_extracts,
                                      'df_insee_areas.csv'),
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
                  right_on = 'c_insee_ardt',
                  how = 'right')

# LOAD DF AREAS
ls_areas = [['df_au_agg_final.csv', 'dict_AU2010_l93_coords.json', 'AU2010'],
            ['df_uu_agg_final.csv', 'dict_UU2010_l93_coords.json', 'UU2010'],
            ['df_bv_agg_final.csv', 'dict_BV_l93_coords.json', 'BV']]

dict_df_areas = {}
for df_area_file, dict_area_coords_file, area in ls_areas:
  df_area = pd.read_csv(os.path.join(path_insee_extracts,
                                     df_area_file),
                    encoding = 'UTF-8')
  dict_area_coords = dec_json(os.path.join(path_insee,
                                           'insee_areas',
                                           dict_area_coords_file))
  
  # nb stores
  se_area_vc = df_lsa[area].value_counts()
  df_area.set_index(area, inplace = True)
  df_area['nb_stores'] = se_area_vc
  
  # cum store surface
  df_area['store_surface'] =\
     df_lsa[[area, 'surface']].groupby(area).agg(np.sum)['surface']
  
  df_area_coords = pd.DataFrame([(k, Polygon(v)) for k,v in dict_area_coords.items()],
                                 columns = [area, 'poly'])
  df_area_coords.set_index(area, inplace = True)
  df_area['poly'] = df_area_coords['poly']
  # Nb stores out of any area
  print '\nNb stores out of {:s} {:4d}'.format(area,
                                               len(df_lsa[pd.isnull(df_lsa[area])]))
  dict_df_areas[area] = df_area

# #########################
# MAPS
# #########################

dict_df_areas['c_insee'] = df_com

dict_titles = {'nb_stores' : 'Nb of stores',
               'store_surface' : 'Cumulated store surface'}

# todo: generalize nb of stores and store surface (or other loop?)
for area, df_area in dict_df_areas.items():
  df_area_temp = df_area[~pd.isnull(df_area['poly'])].copy()
  for field in ['nb_stores', 'store_surface']:
    # Calculate Jenks natural breaks for density
    breaks = nb(df_area_temp[df_area_temp[field].notnull()][field].values,
                initial=300,
                k=5)
    
    # zero excluded from natural breaks... specific class with val -1 (added later)
    df_area_temp.replace(to_replace={field: {0: np.nan}}, inplace=True)
    
    # the notnull method lets us match indices when joining
    jb = pd.DataFrame({'jenks_bins': breaks.yb},
                      index=df_area_temp[df_area_temp[field].notnull()].index)
    
    # need to drop duplicate index in jb, todo: check why need area here (MI?)
    jb = jb.reset_index().drop_duplicates(subset=[area],
                                          take_last=True).set_index(area)
    # propagated to all rows in df_com with same index
    df_area_temp['jenks_bins'] = jb['jenks_bins']
    df_area_temp.jenks_bins.fillna(-1, inplace=True)
    
    jenks_labels = ["<= {:,.0f} {:s} ({:d} ar.)".format(b, field, c)\
                      for b, c in zip(breaks.bins, breaks.counts)]
    
    # if there are 0
    if len(df_area_temp[df_area_temp[field].isnull()]) != 0:
      jenks_labels.insert(0, 'Null ({:5d} mun.)'.\
           format(len(df_area_temp[df_area_temp[field].isnull()])))
    
    plt.clf()
    fig = plt.figure()
    ax = fig.add_subplot(111, axisbg='w', frame_on=False)
    
    # use a blue colour ramp - we'll be converting it to a map using cmap()
    cmap = plt.get_cmap('Blues')
    # draw wards with grey outlines
    df_area_temp['patches'] = df_area_temp['poly'].map(lambda x:\
                          PolygonPatch(x, ec='#555555', lw=.03, alpha=1., zorder=4))
    pc = PatchCollection(df_area_temp['patches'], match_original=True)
    # impose our colour map onto the patch collection
    norm = Normalize()
    pc.set_facecolor(cmap(norm(df_area_temp['jenks_bins'].values)))
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
    plt.title(u'{:s} by {:s}'.format(dict_titles[field], area))
    plt.tight_layout()
    # fig.set_size_inches(7.22, 5.25) # set the image width to 722px
    plt.savefig(os.path.join(path_built_graphs,
                             'overview',
                             'nb_stores',
                             '{:s}_{:s}.png'.format(area, field)),
                dpi=300,
                alpha=True)
