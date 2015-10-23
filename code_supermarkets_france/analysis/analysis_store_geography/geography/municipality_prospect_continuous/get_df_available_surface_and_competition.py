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
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
#import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
#from pysal.esda.mapclassify import Natural_Breaks as nb
from matplotlib import colors

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                        'data_csv')

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
# LOAD DATA
# ##############

# LOAD LSA STORE DATA
df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa_active_hsx.csv'),
                     dtype = {u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'UTF-8')

df_lsa = df_lsa[(~pd.isnull(df_lsa['latitude'])) &\
                (~pd.isnull(df_lsa['longitude']))].copy()

# LOAD INSEE MUNICIPALITY DATA
df_com_insee = pd.read_csv(os.path.join(path_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'UTF-8')

df_com_insee.set_index('CODGEO', inplace = True)

# LOAD GEO FRANCE
geo_france = GeoFrance(path_dpt = path_geo_dpt,
                       path_com = path_geo_com)
df_com = geo_france.df_com

# KEEP ONLY ONE LINE PER MUNICIPALITY (several polygons for some)
df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)
# keep largest area (todo: sum)
df_com.sort(columns = ['c_insee', 'poly_area'],
            ascending = False,
            inplace = True)
df_com.drop_duplicates(['c_insee'], inplace = True, take_last = False)

# GET GPS COORD OF MUNICIPALITY CENTER

# two centers available: centroid of polygon and town hall
print u'\nTest with commune', df_com['commune'].iloc[0]
x_test, y_test = df_com['x_ct'].iloc[0], df_com['y_ct'].iloc[0]
print geo_france.convert_ign_to_gps(x_test, y_test)

df_com[['lng_ct', 'lat_ct']] = df_com[['x_ct', 'y_ct']].apply(\
                                 lambda x: geo_france.convert_ign_to_gps(x['x_ct'],\
                                                                         x['y_ct']),\
                                 axis = 1)

df_com[['lng_cl', 'lat_cl']] = df_com[['x_cl', 'y_cl']].apply(\
                                 lambda x: geo_france.convert_ign_to_gps(x['x_cl'],\
                                                                         x['y_cl']),\
                                 axis = 1)

# Round gps coord
for col in ['lng_ct', 'lat_ct', 'lng_cl', 'lat_cl']:
  df_com[col] = np.round(df_com[col], 3)

# #######################################
# GET COMP VARIABLES OF ONE MUNICIPALITY
# #######################################

df_lsa['lat_com'] = df_com['lat_cl'].iloc[0]
df_lsa['lng_com'] = df_com['lng_cl'].iloc[0]
df_lsa['dist'] = compute_distance_ar(df_lsa['latitude'],
                                     df_lsa['longitude'],
                                     df_lsa['lat_com'],
                                     df_lsa['lng_com'])
lsd_ex = ['enseigne', 'adresse1', 'ville',
          'latitude', 'longitude', 'dist',
          'surface' , 'wgtd_surface']

print u'\nCompetition vars for one municipality (test):'
# Compute surface weighted by distance and sum to get available surface
df_lsa['wgtd_surface'] = np.exp(-df_lsa['dist']/10) * df_lsa['surface']
print df_lsa[lsd_ex][df_lsa['dist'] <= 10].to_string()
available_surface = df_lsa['wgtd_surface'].sum()
# Market share of each group and hhi
df_rgps = df_lsa[['groupe', 'wgtd_surface']].groupby('groupe').agg([sum])['wgtd_surface']
df_rgps['market_share'] = df_rgps['sum'] / df_rgps['sum'].sum()
hhi = (df_rgps['market_share']**2).sum()

# ##########
# EXECUTION
# ##########

ls_rows_comp = []
for row_i, row in df_com.iterrows():
  df_lsa['lat_com'] = row['lat_cl']
  df_lsa['lng_com'] = row['lng_cl']
  df_lsa['dist'] = compute_distance_ar(df_lsa['latitude'],
                                       df_lsa['longitude'],
                                       df_lsa['lat_com'],
                                       df_lsa['lng_com'])
  df_lsa['wgtd_surface'] = np.exp(-df_lsa['dist']/10) * df_lsa['surface']

  df_rgps = df_lsa[['groupe', 'wgtd_surface']].groupby('groupe').agg([sum])['wgtd_surface']
  df_rgps['market_share'] = df_rgps['sum'] / df_rgps['sum'].sum()
  
  df_rgps.sort('sum', ascending = False, inplace = True)
  ls_temp_ens, ls_temp_dist = [], []
  for store_type in ['H', 'S', 'X']:
    store_ind = df_lsa['dist'][df_lsa['type_alt'] == '%s' %store_type].argmin()
    ls_temp_ens.append(df_lsa['enseigne'].ix[store_ind])
    ls_temp_dist.append(df_lsa['dist'].ix[store_ind])

  ls_rows_comp.append([row['c_insee'],
                       df_lsa['wgtd_surface'].sum(),
                       (df_rgps['market_share']**2).sum(),
                       df_rgps['sum'][0:1].sum() / df_rgps['sum'].sum(),
                       df_rgps['sum'][0:2].sum() / df_rgps['sum'].sum(),
                       df_rgps['sum'][0:3].sum() / df_rgps['sum'].sum()] +\
                       ls_temp_dist + ls_temp_ens)

ls_comp_cols = ['c_insee', 'available_surface', 'hhi',
                'cr1', 'cr2', 'cr3',
                'dist_h', 'dist_s', 'dist_x',
                'ens_h', 'ens_s', 'ens_x']

df_comp = pd.DataFrame(ls_rows_comp, columns = ls_comp_cols)
df_comp['dist_any'] = df_comp[['dist_h', 'dist_s', 'dist_x']].min(axis = 1)

# Add nb of stores and surf. by municipality
se_nb_stores = df_lsa['c_insee'].value_counts()
se_surf_stores = df_lsa[['surface', 'c_insee']].groupby('c_insee').agg(sum)['surface']

df_comp.set_index('c_insee', inplace = True)
df_comp['nb_stores'] = se_nb_stores
df_comp['surface'] = se_surf_stores
df_comp['nb_stores'].fillna(0, inplace = True) #necessary?
df_comp['surface'].fillna(0, inplace = True) #necessary?

# Avail surf by pop
df_comp['nb_households'] = df_com_insee['P10_MEN']
df_comp[df_comp['nb_households'] == 0] = np.nan
df_comp['available_surface_by_h'] = df_comp['available_surface'] / df_comp['nb_households']
df_comp['nb_h_by_stores'] = df_comp['nb_households'] / df_comp['nb_stores']
df_comp['surf_by_h'] = df_comp['surface'] / df_comp['nb_households']
df_comp.replace([np.inf, -np.inf], np.nan, inplace = True)

print u'\nOverview competition:'
dict_formatters = {'hhi' : format_float_float,
                   'available_surface' : format_float_int}
ls_percentiles = [0.25, 0.75]
print df_comp[ls_comp_cols[1:]].describe(percentiles=ls_percentiles)\
                               .T.to_string(formatters=dict_formatters)

# ########
# OUTPUT
# ########

df_comp.to_csv(os.path.join(path_built_csv,
                            '201407_competition',
                            'df_mun_prospect_comp.csv'),
                    index_label = 'c_insee',
                    encoding = 'utf-8',
                    float_format='%.3f')

## ######################
## ENTROPY DECOMPOSITION
## ######################
#
## Move to analysis?
#
## ENTROPY
#
#print u'\nEntropy analysis:'
#for field in ['nb_stores', 'surface', 'available_surface', 'available_surface_by_h']:
#  df_comp['norm_%s' %field] = df_comp[field]/df_comp[field].mean()
#  ent = (df_comp['norm_%s' %field]*np.log(df_comp['norm_%s' %field])).sum()
#  print u'Entropy of field %s: ' %field, ent
#
## ENTROPY DECOMPOSITION FOR AVAIL. SURFACE
#
## add region to df_comp (5 com left out)
#df_comp['region'] = df_com_insee['REG']
## df_comp.reset_index()
#
#df_comp = df_comp[~pd.isnull(df_comp['region']) &\
#                  ~pd.isnull(df_comp['available_surface'])]
#
## get s_k
#df_reg_s = df_comp[['region', 'available_surface']]\
#             .groupby('region').agg([len,
#                                     np.mean])['available_surface']
#df_reg_s['s_k'] = (df_reg_s['len'] * df_reg_s['mean']) /\
#                  (len(df_comp) * df_comp['available_surface'].mean())
#
## get t1_k
#def get_t1_k(se_inc):
#  se_norm_inc = se_inc / se_inc.mean()
#  return (se_norm_inc * np.log(se_norm_inc)).sum() / len(se_inc)
#df_reg_t = df_comp[['region', 'available_surface']]\
#             .groupby('region').agg([len,
#                                     get_t1_k])['available_surface']
#df_reg_t['t1_k'] = df_reg_t['get_t1_k']
#
## merge and final
#df_reg = df_reg_s[['mean', 's_k']].copy()
#df_reg['t1_k'] = df_reg_t['t1_k']
#
#T1 = (df_reg['s_k'] * df_reg['t1_k']).sum()  +\
#     (df_reg['s_k'] * np.log(df_reg['mean'] / df_comp['available_surface'].mean())).sum()
#
#T1_simple = (df_comp['norm_available_surface'] *\
#               np.log(df_comp['norm_available_surface'])).sum() /\
#            len(df_comp)
## Close enough! (Same as get_T1)
#
## Gini (draw normalized empirical distrib?)
#
#def get_Gini(df_interest, field):
#  df_gini = df_interest.copy()
#  df_gini.sort(field, ascending = True, inplace = True)
#  df_gini.reset_index(drop = True, inplace = True)
#  df_gini['i'] = df_gini.index + 1
#  G = 2*(df_gini[field]*df_gini['i']).sum()/\
#      (df_gini['i'].max()*df_gini[field].sum()) -\
#      (df_gini['i'].max() + 1)/float(df_gini['i'].max())
#  return np.round(G, 2), df_gini
#
#print u'\nGini coefficients:'
#for field in ['available_surface', 'hhi', 'cr1', 'cr2', 'cr3']:
#  G, df_gini = get_Gini(df_comp, field)
#  print field, G
#
#df_comp.sort('available_surface', ascending = True, inplace = True)
#df_comp.reset_index(inplace = True)
#df_comp['i'] = df_comp.index + 1
#G = 2*(df_comp['available_surface']*df_comp['i']).sum()/\
#    (df_comp['i'].max()*df_comp['available_surface'].sum()) -\
#    (df_comp['i'].max() + 1)/float(df_comp['i'].max())
