#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
from matching_insee import *
from functions_string import *
import os, sys
import re
import json
import pandas as pd
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PatchCollection
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_qlmc_scraped = os.path.join(path_data,
                                 'data_supermarkets',
                                 'data_source',
                                 'data_qlmc_2015',
                                 'data_scraped_201503')

path_csv = os.path.join(path_data,
                        'data_supermarkets',
                        'data_built',
                        'data_qlmc_2015',
                        'data_csv_201503')

path_dir_match_insee = os.path.join(path_data,
                                    u'data_insee',
                                    u'match_insee_codes')

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'df_stores.csv'),
                        encoding = 'utf-8')

# Fix some problematic store locations (found through competitor pair analysis)
ls_fix_gps = [['intermarche-super-le-portel',      (50.7093, 1.5789)], # too far
              ['casino-l-ile-rousse',              (42.6327, 8.9383)],
              ['centre-e-leclerc-lassigny',        (49.5898, 2.8531)],
              ['carrefour-market-chateau-gontier', (47.8236, -0.7064)],
              ['casino-san-nicolao',               (42.3742, 9.5299)], # too close
              ['centre-e-leclerc-san-giuliano',    (42.2625, 9.5480)]]
for store_id, (store_lat, store_lng) in ls_fix_gps:
  df_stores.loc[df_stores['store_id'] == store_id,
                ['store_lat', 'store_lng']] = [store_lat, store_lng]

# GOAL: match df_stores with df_lsa (in on stores such as surface etc.)
# STEP: find store municipality code to match on this code + chain name
# (CHECK: distance in the end with gps coord, not very reliable though)

# Load communes and dpt shp
# Check in which "departement" polygon each store is
# Check in wich "commune" polygon each store is
# Can perform preliminary LSA matching
# Possible to find store "commune" based on "departement" code + "commune" name

# LOAD COMMUNES

# todo: Use basemap: either IGN Geo or Routes (?)
# todo: Beware to display all stores when several in a town!

# France
x1, x2, y1, y2 = -5.0, 9.0, 42.0, 52.0

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

path_dir_geofla = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84')
m_fra.readshapefile(os.path.join(path_dir_geofla, 'COMMUNE'), u'communes_fr',
                    color = 'none', zorder=2)

df_com = pd.DataFrame({'poly'     : [Polygon(xy) for xy in m_fra.communes_fr],
                       'com_name' : [d['NOM_COMM'] for d in m_fra.communes_fr_info],
                       'com_code' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.communes_fr_info],
                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.communes_fr_info],
                       'reg_name' : [d['NOM_REGION'] for d in m_fra.communes_fr_info],
                       'reg_code' : [d['CODE_REG'] for d in m_fra.communes_fr_info]})

def gps_to_locality(lat, lon, basemap_obj, df_polygons, field_int, poly='poly'):
  poi = Point(basemap_obj(lon, lat))
  for i, x in enumerate(df_polygons[poly]):
    if poi.within(x):
      # returns first match
      return df_polygons.iloc[i][field_int]
  return None

# NB: can be two rows with same com_code: communes in several parts (but same commune etc)
df_stores['ic'] = df_stores.apply(\
                    lambda row: gps_to_locality(row['store_lat'],
                                                row['store_lng'],
                                                m_fra,
                                                df_com,
                                                'com_code'),
                                                axis = 1)
df_stores['ic_city'] = df_stores['ic'].apply(\
                         lambda x: df_com[df_com['com_code'] == x].iloc[0]['com_name']\
                                     if x else None)

# check matching (need to get rid of accents else a lot of false positive)
df_stores['city_match'] = df_stores.apply(lambda row: 1 if str_low_noacc(row['ic_city']) in\
                                                             str_low_noacc(row['store_name'])\
                                                        else 0,
                                          axis = 1)
print len(df_stores[~df_stores['city_match']])
print df_stores[df_stores['city_match'] == 0].to_string()

# Match city name with insee code 
# uses insee code already found to have dpt (should not be too wrong!)
path_df_corr = os.path.join(path_dir_match_insee, 'df_corr_gas.csv')
matching_insee = MatchingINSEE(path_df_corr)

ls_matched = [matching_insee.match_city('PARIS', '75', '75006')]

def apply_insee_matching(store_city, dpt_id):
  dpt_id = dpt_id.replace('2A', '20').replace('2B', '20')
  ls_res = matching_insee.match_city(store_city, dpt_id)
  if ls_res and ls_res[0]:
    return ls_res[0][0][2], ls_res[0][0][0]
  else:
    return None, None

# Not way to fill two columns with one apply?
df_stores.loc[df_stores['city_match'] == 0, 'insee_matching'] =\
  df_stores[df_stores['city_match'] == 0].apply(\
     lambda row: apply_insee_matching(row['store_city'],
                                      row['ic'][0:2]),
     axis = 1)
df_stores['ic_alt'], df_stores['ic_city_alt'] = None, None
df_stores['ic_alt'] = df_stores[~pd.isnull(df_stores['insee_matching'])].apply(\
                        lambda row: row['insee_matching'][0], axis = 1)
df_stores['ic_city_alt'] = df_stores[~pd.isnull(df_stores['insee_matching'])].apply(\
                             lambda row: row['insee_matching'][1], axis = 1)

print df_stores[df_stores['city_match'] == 0]\
        [['store_city', 'ic_city', 'ic_city_alt', 'ic', 'ic_alt']].to_string()

df_stores.loc[(~pd.isnull(df_stores['ic_alt'])) &\
              (~df_stores['ic_city_alt'].isin(['paris', 'marseille', 'lyon'])),
              'ic'] = df_stores['ic_alt']

df_stores.loc[(~pd.isnull(df_stores['ic_alt'])) &\
              (~df_stores['ic_city_alt'].isin(['paris', 'marseille', 'lyon'])),
              'ic_city'] = df_stores['ic_city_alt']

df_stores.drop(['insee_matching', 'ic_alt', 'ic_city_alt'],
               axis = 1,
               inplace = 1)

df_stores.to_csv(os.path.join(path_csv,
                              'df_stores_final.csv'),
                 encoding = 'utf-8',
                 float_format='%.4f',
                 index = False)
