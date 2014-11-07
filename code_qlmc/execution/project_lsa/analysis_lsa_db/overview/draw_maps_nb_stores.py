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
df_lsa = pd.read_csv(os.path.join(path_dir_built_csv, 'df_lsa_active_fm_hsx.csv'),
                     encoding = 'UTF-8',
                     dtype = {'Code INSEE' : str,
                              'Code INSEE ardt' : str,
                              'Code postal' : str})

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

# LOAD DF AREAS
ls_areas = [['df_au_agg_final.csv', 'dict_AU2010_l93_coords.json', 'AU2010'],
            ['df_uu_agg_final.csv', 'dict_UU2010_l93_coords.json', 'UU2010'],
            ['df_bv_agg_final.csv', 'dict_BV_l93_coords.json', 'BV']]

dict_df_areas = {}
for df_area_file, dict_area_coords_file, area in ls_areas:
  df_area = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                     df_area_file),
                    encoding = 'UTF-8')
  dict_area_coords = dec_json(os.path.join(path_dir_insee,
                                         'insee_areas',
                                         dict_area_coords_file))
  
  # nb stores
  se_area_vc = df_lsa[area].value_counts()
  df_area.set_index(area, inplace = True)
  df_area['nb_stores'] = se_area_vc
  
  # cum store surface
  df_area['store_surface'] =\
     df_lsa[[area, 'Surf Vente']].groupby(area).agg(np.sum)['Surf Vente']
  
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

dict_df_areas['insee_code'] = df_com

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
    
    # need to drop duplicate index in jb, TODO: check why need area here (MI?)
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
    plt.title(u'{:s} by {:s}'.format(dict_titles[field], area))
    plt.tight_layout()
    # fig.set_size_inches(7.22, 5.25) # set the image width to 722px
    plt.savefig(os.path.join(path_data,
                             'data_maps',
                             'data_built',
                             'graphs',
                             'lsa',
                             'insee_areas',
                             '%s_%s.png' %(area, field)),
                dpi=300,
                alpha=True)
