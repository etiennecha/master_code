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

df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_lsa_active_fm_hsx.csv'),
                     dtype = {'Code INSEE' : str,
                              'Code INSEE ardt' : str},
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

path_dir_120 = os.path.join(path_data, 'data_maps', 'ROUTE120_WGS84')
path_120_rte = os.path.join(path_dir_120, 'TRONCON_ROUTE')
path_120_nod = os.path.join(path_dir_120, 'NOEUD_ROUTIER')

m_fra.readshapefile(path_120_rte, 'routes_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_120_nod, 'noeuds_fr', color = 'none', zorder=2)

df_com = pd.DataFrame({'poly' :       [Polygon(xy) for xy in m_fra.communes_fr],
                       'x_center' :   [d['X_CENTROID'] for d in m_fra.communes_fr_info],
                       'y_center' :   [d['Y_CENTROID'] for d in m_fra.communes_fr_info],
                       'x_cl' :       [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl' :       [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'code_insee' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'commune' :    [d['NOM_COMM'] for d in m_fra.communes_fr_info]})
# keep only one line per commune (several polygons for some)
df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)
df_com.sort(columns = ['code_insee', 'poly_area'],
            ascending = False,
            inplace = True)

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

#print u'\nTest with commune', df_com['commune'].iloc[0]
#x_test, y_test = df_com['x_center'].iloc[0], df_com['y_center'].iloc[0]
#print convert_from_ign(x_test, y_test)

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

# ##########
# EXECUTION
# ##########

# SURFACE AVAIL TO EACH COMMUNE BY BRAND

df_com.set_index('code_insee', inplace = True)

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

ls_rows_res = []
start = time.time()
for i, row in df_com[0:100].iterrows():
  df_lsa['lat_com'] = row['lat_cl']
  df_lsa['lng_com'] = row['lng_cl']
  df_lsa['dist'] = compute_distance_ar(df_lsa['Latitude'],
                                          df_lsa['Longitude'],
                                          df_lsa['lat_com'],
                                          df_lsa['lng_com'])
  df_lsa['wgt_surf'] = np.exp(-df_lsa['dist']/10) * df_lsa['Surf Vente']
  df_rgps = df_lsa[['Groupe_alt', 'wgt_surf']].groupby('Groupe_alt').agg([sum])['wgt_surf']
  df_rgps['market_share'] = df_rgps['sum'] / df_rgps['sum'].sum()
  ls_rows_res.append([i] +\
                     list(df_rgps.ix[ls_rgs]['market_share'].values))

print time.time() - start

df_com_ms = pd.DataFrame(ls_rows_res, columns = ['code_insee'] + ls_rgs)
df_com_ms.set_index('code_insee', inplace = True)

df_com = pd.merge(df_com, df_com_ms,
                  left_index = True, right_index = True, how = 'left')

# ADD NB HOUSEHOLD AND REVENUE BY MUNICIPALITY
df_com['PMENFIS10'] = df_com_insee['PMENFIS10']
df_com['QUAR2UC10'] = df_com_insee['QUAR2UC10']

for rgs in ls_rgs:
  df_com['rev_%s' %rgs] = df_com[rgs] * df_com['PMENFIS10'] * df_com['QUAR2UC10']

se_th_rev = df_com[['rev_%s' %rgs for rgs in ls_rgs]].sum()
se_nat_ms = se_th_rev / (df_com['PMENFIS10'] * df_com['QUAR2UC10']).sum()
se_nat_ms.sort(ascending = False)

df_temp = pd.DataFrame(se_nat_ms)
df_temp.index = [x.lstrip('rev_') for x in df_temp.index]
