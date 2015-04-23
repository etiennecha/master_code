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

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# READ CSV FILES
# ##############

df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_lsa_active_fm_hsx.csv'),
                     dtype = {'Code INSEE' : str},
                     encoding = 'UTF-8')
df_lsa = df_lsa[(~pd.isnull(df_lsa['Latitude'])) &\
                (~pd.isnull(df_lsa['Longitude']))].copy()

df_com_insee = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'UTF-8')
df_com_insee.set_index('CODGEO', inplace = True)

# #############
# FRANCE MAP
# #############

# excludes Corsica
x1 = -5.
x2 = 9.
y1 = 42
y2 = 52.

#w = x2 - x1
#h = y2 - y1
#extra = 0.025

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
#                llcrnrlat=y1 - extra * h,
#                urcrnrlat=y2 + extra * h,
#                llcrnrlon=x1 - extra * w,
#                urcrnrlon=x2 + extra * w)

path_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')

m_fra.readshapefile(path_dpt, 'departements_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_com, 'communes_fr', color = 'none', zorder=2)

path_dir_120 = os.path.join(path_data, 'data_maps', 'ROUTE120_WGS84')
path_120_rte = os.path.join(path_dir_120, 'TRONCON_ROUTE')
path_120_nod = os.path.join(path_dir_120, 'NOEUD_ROUTIER')

m_fra.readshapefile(path_120_rte, 'routes_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_120_nod, 'noeuds_fr', color = 'none', zorder=2)

#df_dpt = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.departements_fr],
#                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.departements_fr_info],
#                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.departements_fr_info],
#                       'region_name' : [d['NOM_REGION'] for d in m_fra.departements_fr_info],
#                       'region_code' : [d['CODE_REG'] for d in m_fra.departements_fr_info]})

#df_dpt['patches'] = df_dpt['poly'].map(lambda x: PolygonPatch(x,
#                                                              facecolor='#FFFFFF', # '#555555'
#                                                              edgecolor='#555555', # '#787878'
#                                                              lw=.25, alpha=.3, zorder=1))

df_com = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.communes_fr],
                       'x_center' : [d['X_CENTROID'] for d in m_fra.communes_fr_info],
                       'y_center' : [d['Y_CENTROID'] for d in m_fra.communes_fr_info],
                       'x_cl' : [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl' : [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'code_insee' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'commune' : [d['NOM_COMM'] for d in m_fra.communes_fr_info]})
# keep only one line per commune (several polygons for some)
df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)
df_com.sort(columns = ['code_insee', 'poly_area'],
            ascending = False,
            inplace = True)

if pd.__version__ in ['0.13.0', '0.13.1']:
  df_com.drop_duplicates(cols = ['code_insee'], inplace = True)
else:
  df_com.drop_duplicates(subset = 'code_insee', inplace = True)

#df_lsa['point'] = df_lsa[['Longitude', 'Latitude']].apply(\
#                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)

def convert_to_ign(x, y):
  x_l_93_ign = (m_fra(x, y)[0] + 700000 - m_fra(3, 46.5)[0])/100.0
  y_l_93_ign = (m_fra(x, y)[1] + 6600000 - m_fra(3, 46.5)[1])/100.0
  return x_l_93_ign, y_l_93_ign

def convert_from_ign(x_l_93_ign, y_l_93_ign):
  x = x_l_93_ign * 100 - 700000 + m_fra(3, 46.5)[0] 
  y = y_l_93_ign * 100 - 6600000 + m_fra(3, 46.5)[1]
  x, y = m_fra(x, y, inverse = True)
  return x, y

print u'\nTest with commune', df_com['commune'].iloc[0]
x_test, y_test = df_com['x_center'].iloc[0], df_com['y_center'].iloc[0]
print convert_from_ign(x_test, y_test)

df_com[['lng_ct', 'lat_ct']] = df_com[['x_center', 'y_center']].apply(\
                                 lambda x: convert_from_ign(x['x_center'],\
                                                            x['y_center']),\
                                 axis = 1)

df_com[['lng_cl', 'lat_cl']] = df_com[['x_cl', 'y_cl']].apply(\
                                 lambda x: convert_from_ign(x['x_cl'],\
                                                            x['y_cl']),\
                                 axis = 1)

df_com['dpt'] = df_com['code_insee'].str.slice(stop=-3)
df_com = df_com[~df_com['dpt'].isin(['2A', '2B'])]

# Round gps coord
for col in ['lng_ct', 'lat_ct', 'lng_cl', 'lat_cl']:
  df_com[col] = np.round(df_com[col], 3)

# #####
# TESTS
# #####

## DISTANCE OF STORE TO ALL COMMUNES
#df_com['lat_store'] = df_lsa['Latitude'].iloc[0]
#df_com['lng_store'] = df_lsa['Longitude'].iloc[0]
#df_com['dist'] = compute_distance_ar(df_com['lat_store'],
#                                     df_com['lng_store'],
#                                     df_com['lng_ct'],
#                                     df_com['lat_ct'])

# SURFACE AVAILABLE TO COMMUNE
df_lsa['lat_com'] = df_com['lat_cl'].iloc[0] #.iloc[0]
df_lsa['lng_com'] = df_com['lng_cl'].iloc[0] #.iloc[0]
df_lsa['dist'] = compute_distance_ar(df_lsa['Latitude'],
                                     df_lsa['Longitude'],
                                     df_lsa['lat_com'],
                                     df_lsa['lng_com'])
ls_disp_a = ['Enseigne', 'ADRESSE1', 'Ville',
                'Latitude', 'Longitude', 'dist']
ls_disp_b = ls_disp_a + ['Surf Vente' , 'wgt_surf']
print df_lsa[ls_disp_a][df_lsa['dist'] < 10].to_string()
# Compute surface weighted by distance
df_lsa['wgt_surf'] = np.exp(-df_lsa['dist']/10) * df_lsa['Surf Vente']
print df_lsa[ls_disp_b][df_lsa['dist'] < 10].to_string()
store_avail_surface = df_lsa['wgt_surf'].sum()

# AVAILABLE MARKET SHARE OF STORE
df_rgps = df_lsa[['Groupe', 'wgt_surf']].groupby('Groupe').agg([sum])['wgt_surf']
df_rgps['market_share'] = df_rgps['sum'] / df_rgps['sum'].sum()
hhi = (df_rgps['market_share']**2).sum()

# COMMUNE CENTERED: DISTANCE TO ALL STORES AND AVAIL. SURFACE

# ##########
# EXECUTION
# ##########

## SURFACE AVAILABLE TO EACH COMMUNE
#
#df_com['avail_surf'] = np.nan
#df_com['hhi'] = np.nan
#df_com['CR1'] = np.nan
#df_com['CR2'] = np.nan
#df_com['CR3'] = np.nan
#for store_type in ['H', 'X', 'S']:
#  df_com['%s_ens' %store_type] = None
#  df_com['%s_dist' %store_type] = np.nan
#
#for i, row in df_com.iterrows():
#  df_lsa['lat_com'] = row['lat_cl']
#  df_lsa['lng_com'] = row['lng_cl']
#  df_lsa['dist'] = compute_distance_ar(df_lsa['Latitude'],
#                                       df_lsa['Longitude'],
#                                       df_lsa['lat_com'],
#                                       df_lsa['lng_com'])
#  df_lsa['wgt_surf'] = np.exp(-df_lsa['dist']/10) * df_lsa['Surf Vente']
#  df_com['avail_surf'].ix[i] = df_lsa['wgt_surf'].sum()
#
#  df_rgps = df_lsa[['Groupe', 'wgt_surf']].groupby('Groupe').agg([sum])['wgt_surf']
#  df_rgps['market_share'] = df_rgps['sum'] / df_rgps['sum'].sum()
#  df_com['hhi'].ix[i] = (df_rgps['market_share']**2).sum()
#  
#  df_rgps.sort('sum', ascending = False, inplace = True)
#  df_com['CR1'].ix[i] = df_rgps['sum'][0:1].sum() / df_rgps['sum'].sum()
#  df_com['CR2'].ix[i] = df_rgps['sum'][0:2].sum() / df_rgps['sum'].sum()
#  df_com['CR3'].ix[i] = df_rgps['sum'][0:3].sum() / df_rgps['sum'].sum()
#
#  for store_type in ['H', 'X', 'S']:
#    store_ind = df_lsa['dist'][df_lsa['Type_alt'] == '%s' %store_type].argmin()
#    df_com['%s_ens' %store_type].ix[i] = df_lsa['Enseigne'].loc[store_ind]
#    df_com['%s_dist' %store_type].ix[i] = df_lsa['dist'].loc[store_ind]
#
#df_com['All_dist'] = df_com[['H_dist', 'S_dist', 'X_dist']].min(axis = 1)
#
### output
#ls_disp_com_comp = ['code_insee', 'avail_surf',
#                    'hhi', 'CR1', 'CR2', 'CR3',
#                    'All_dist', 'H_dist', 'S_dist', 'X_dist',
#                    'H_ens', 'S_ens', 'X_ens']
#df_com[ls_disp_com_comp].to_csv(os.path.join(path_dir_built_csv,
#                                             'df_com_comp.csv'),
#                                 index = False,
#                                 encoding = 'utf-8',
#                                 float_format='%.3f')

# READ STORED df_com_comp and MERGE BACK
df_com_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                             'df_com_comp.csv'))
df_com_comp['code_insee'] = df_com_comp['code_insee'].apply(\
                              lambda x: "{:05d}".format(x)\
                                if (type(x) == np.int64 or type(x) == long) else x)
df_com = pd.merge(df_com, df_com_comp,
                  left_on = 'code_insee', right_on = 'code_insee')

# Add nb of stores and surf. by municipality

se_nb_stores = df_lsa['Code INSEE'].value_counts()
se_surf_stores = df_lsa[['Surf Vente', 'Code INSEE']].groupby('Code INSEE').agg(sum)['Surf Vente']

df_com.set_index('code_insee', inplace = True)
df_com['nb_stores'] = se_nb_stores
df_com['surf'] = se_surf_stores
df_com['nb_stores'].fillna(0, inplace = True) #necessary?
df_com['surf'].fillna(0, inplace = True) #necessary?

# Avail surf by pop
df_com['nb_households'] = df_com_insee['P10_MEN']
df_com[df_com['nb_households'] == 0] = np.nan
df_com['avail_surf_by_h'] = df_com['avail_surf'] / df_com['nb_households']
df_com['nb_h_by_stores'] = df_com['nb_households'] / df_com['nb_stores']
df_com['surf_by_h'] = df_com['surf'] / df_com['nb_households']
df_com.replace([np.inf, -np.inf], np.nan, inplace = True)

# Summary Table (include Gini?)
dict_formatters = {'hhi' : format_float_float,
                   'avail_surf' : format_float_int}
ls_percentiles = [0.25, 0.75]
# percentiles option only available in newest python

if pd.__version__ in ['0.13.0', '0.13.1']:
  print df_com[['nb_stores', 'surf', 'avail_surf', 'hhi', 'CR1', 'CR2', 'CR3',
                'All_dist', 'H_dist', 'S_dist', 'X_dist']].describe().\
          T.to_string(formatters=dict_formatters)
else:
  print df_com[['nb_stores', 'surf', 'avail_surf', 'avail_surf_by_h',
                'hhi', 'CR1', 'CR2', 'CR3',
                'All_dist', 'H_dist', 'S_dist', 'X_dist']].describe(\
        percentiles=ls_percentiles).T.to_string(formatters=dict_formatters)

# Entropy
for field in ['nb_stores', 'surf', 'avail_surf', 'avail_surf_by_h']:
  df_com['norm_%s' %field] = df_com[field]/df_com[field].mean()
  ent = (df_com['norm_%s' %field]*np.log(df_com['norm_%s' %field])).sum()
  print u'Entropy of field %s: ' %field, ent

# Entropy decomposition

# add region to df_com (5 com left out)
#df_com.set_index('code_insee', inplace = True)
df_com['reg'] = df_com_insee['REG']
df_com.reset_index()

df_com = df_com[~pd.isnull(df_com['reg']) &\
                ~pd.isnull(df_com['avail_surf'])]

# get s_k
df_reg_s = df_com[['reg', 'avail_surf']].groupby('reg').agg([len,
                                                           np.mean])['avail_surf']
df_reg_s['s_k'] = (df_reg_s['len'] * df_reg_s['mean']) /\
                  (len(df_com) * df_com['avail_surf'].mean())

# get T1_k
def get_T1_k(se_inc):
  se_norm_inc = se_inc / se_inc.mean()
  return (se_norm_inc * np.log(se_norm_inc)).sum() / len(se_inc)
df_reg_t = df_com[['reg', 'avail_surf']].groupby('reg').agg([len,
                                                       get_T1_k])['avail_surf']
df_reg_t['T1_k'] = df_reg_t['get_T1_k']

# merge and final
df_reg = df_reg_s[['mean', 's_k']].copy()
df_reg['T1_k'] = df_reg_t['T1_k']

T1 = (df_reg['s_k'] * df_reg['T1_k']).sum()  +\
     (df_reg['s_k'] * np.log(df_reg['mean'] / df_com['avail_surf'].mean())).sum()

T1_simple = (df_com['norm_avail_surf'] * np.log(df_com['norm_avail_surf'])).sum() /\
            len(df_com)
# Close enough! (Same as get_T1)

# Gini (draw normalized empirical distrib?)

def get_Gini(df_interest, field):
  df_gini = df_interest.copy()
  df_gini.sort(field, ascending = True, inplace = True)
  df_gini.reset_index(drop = True, inplace = True)
  df_gini['i'] = df_gini.index + 1
  G = 2*(df_gini[field]*df_gini['i']).sum()/\
      (df_gini['i'].max()*df_gini[field].sum()) -\
      (df_gini['i'].max() + 1)/float(df_gini['i'].max())
  return np.round(G, 2), df_gini

for field in ['avail_surf', 'hhi', 'CR1', 'CR2', 'CR3']:
  G, df_gini = get_Gini(df_com, field)
  print field, G

df_com.sort('avail_surf', ascending = True, inplace = True)
df_com.reset_index(inplace = True)
df_com['i'] = df_com.index + 1
G = 2*(df_com['avail_surf']*df_com['i']).sum()/\
    (df_com['i'].max()*df_com['avail_surf'].sum()) -\
    (df_com['i'].max() + 1)/float(df_com['i'].max())


# POP AVAIL TO EACH STORE

#df_com = pd.merge(df_com_insee, df_com, how='right', left_on = 'CODGEO', right_on = 'code_insee')
##df_com[['code_insee', 'commune']][pd.isnull(df_com['P10_POP'])]
#
#df_lsa['avail_pop'] = np.nan
#for i, row in df_lsa.iterrows():
#  df_com['Latitude'] = row['Latitude']
#  df_com['Longitude'] = row['Longitude']
#  df_com['dist'] = compute_distance_ar(df_com['Latitude'],
#                                       df_com['Longitude'],
#                                       df_com['lat_cl'],
#                                       df_com['lng_cl'])
#  df_com['wgt_pop'] = np.exp(-df_com['dist']/10) * df_com['P10_POP']
#  df_lsa['avail_pop'].ix[i] = df_com['wgt_pop'].sum()
