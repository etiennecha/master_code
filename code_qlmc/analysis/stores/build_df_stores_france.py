#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import *
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PatchCollection
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
import pprint

def extract_gps(str_gps):
  ls_gps = re.split(u'\s+', str_gps)
  lat, lon = map(lambda x: float(x), ls_gps)
  return lat, lon

def get_locality_from_gps(lat, lon, basemap_obj, df_polygons, field_int, poly='poly'):
  poi = Point(basemap_obj(lon, lat))
  for i, x in enumerate(df_polygons['poly']):
    if poi.within(x):
      return df_polygons.iloc[i][field_int]
  return None

def gps_to_locality(str_gps, basemap_obj, df_polygons, field_int, poly='poly'):
  try:
    lat, lon = extract_gps(str_gps)
    res = get_locality_from_gps(lat, lon, basemap_obj, df_polygons, field_int, poly)
    return res
  except:
    print 'Pbm with', str_gps
    return None

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_source_json = os.path.join(path_dir_qlmc, 'data_source', 'data_json_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_source_chains = os.path.join(path_dir_qlmc, 'data_source', 'data_chain_websites')
path_dir_source_kml = os.path.join(path_dir_qlmc, 'data_source', 'data_kml')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

fra_stores = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'fra_stores.h5'))

## BUILD DF FRA STORES
#
## print fra_stores.keys()
#ls_df_chain_names = ['/df_auchan',
#                     '/df_carrefour',
#                     '/df_casino',
#                     '/df_cora',
#                     '/df_franprix',
#                     '/df_intermarche',
#                     '/df_monoprix',
#                     '/df_u']
#ls_df_chains = [fra_stores[df_chain_name] for df_chain_name in ls_df_chain_names]
#df_fra_stores = pd.concat(ls_df_chains)
#df_fra_stores.reset_index(drop=True, inplace=True)
#fra_stores['df_fra_stores'] = df_fra_stores
#
#ls_columns = ['type', 'name', 'gps', 'street', 'zip', 'city']
#pd.set_option('display.max_colwidth', 30)
#print fra_stores['df_fra_stores'][ls_columns].to_string()
#
## LOAD COMMUNES & GET INSEE CODES VIA GPS
#
## todo: Use basemap: either IGN Geo or Routes (?)
## todo: Beware to display all stores when several in a town!
#
## France
#x1, x2, y1, y2 = -5.0, 9.0, 42.0, 52.0
#
## Lambert conformal for France (as suggested by IGN... check WGS84 though?)
#m_fra = Basemap(resolution='i',
#                projection='lcc',
#                ellps = 'WGS84',
#                lat_1 = 44.,
#                lat_2 = 49.,
#                lat_0 = 46.5,
#                lon_0 = 3,
#                llcrnrlat=y1,
#                urcrnrlat=y2,
#                llcrnrlon=x1,
#                urcrnrlon=x2)
#
#path_dir_geofla = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84')
#m_fra.readshapefile(os.path.join(path_dir_geofla, 'COMMUNE'), u'communes_fr',
#                    color = 'none', zorder=2)
#
#df_com = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.communes_fr],
#                       'com_name' : [d['NOM_COMM'] for d in m_fra.communes_fr_info],
#                       'com_code' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
#                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.communes_fr_info],
#                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.communes_fr_info],
#                       'reg_name' : [d['NOM_REGION'] for d in m_fra.communes_fr_info],
#                       'reg_code' : [d['CODE_REG'] for d in m_fra.communes_fr_info]})
#
#df_fra_stores = fra_stores['df_fra_stores']
## takes a bit of time
#df_fra_stores['insee_code'] = df_fra_stores['gps'].apply(\
#                                lambda x: gps_to_locality(x, m_fra, df_com, 'com_code'))
#
#fra_stores['df_fra_stores'] = df_fra_stores # necessary
#fra_stores.close()

# LOAD CORRESP INSEE & GET INSEE CODES VIA CITY NAME

df_fra_stores = fra_stores['df_fra_stores']

# Load zip code - insee code correspondence file
file_correspondence = open(os.path.join(path_dir_insee_match,
                                        'corr_cinsee_cpostal'),'r')
correspondence = file_correspondence.read().split('\n')[1:-1]
# Update changes in city codes (correspondence is a bit old)
file_correspondence_update = open(os.path.join(path_dir_insee_match,
                                               'corr_cinsee_cpostal_update'),'r')
correspondence_update = file_correspondence_update.read().split('\n')[1:]
correspondence += correspondence_update
# Patch ad hoc for gas station cedexes
file_correspondence_gas_path = open(os.path.join(path_dir_insee_match,
                                                 'corr_cinsee_cpostal_gas_patch'),'r')
correspondence_gas_patch = file_correspondence_gas_path.read().split('\n')
correspondence += correspondence_gas_patch
correspondence = [row.split(';') for row in correspondence]

# Corrections: standardize insee codes to 5 chars (zip assumed to be ok)
correspondence = [(commune, zip_code, department, insee_code.rjust(5, '0'))\
                    for(commune, zip_code, department, insee_code) in correspondence]
# Generate dict (key: zip code) with correspondence file
dict_corr_zip_insee = {}
for (city, zip_code, department, insee_code) in correspondence:
  dict_corr_zip_insee.setdefault(zip_code, []).append((city, zip_code, department, insee_code))
# Generate dict (key: dpt code) with correspondence file
dict_corr_dpt_insee = {}
for (city, zip_code, department, insee_code)  in correspondence:
  dict_corr_dpt_insee.setdefault(zip_code[:-3], []).append((city, zip_code, department, insee_code))

# matching
ls_matching = []
ls_no_matching = []
for i, row in df_fra_stores[0:100].iterrows():
	# print row['zip'], row['city']
  try:
    zip_code, city = row['zip'], row['city']
    found_indicator = False
    for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
      if str_insee_harmonization(str_low_noacc(city)) == str_insee_harmonization(city_insee):
        ls_matching.append((i, zip_code, code_insee))
        found_indicator = True
        break
    if not found_indicator:
      for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
        if str_insee_harmonization(str_low_noacc(city)) in str_insee_harmonization(city_insee):
          ls_matching.append((i, zip_code, code_insee))
          print 'Matched', city, city_insee, zip_insee, '(', i, ')'
          found_indicator = True
          break
    if not found_indicator:
        print i, zip_insee, city, 'not matched'
  except:
    ls_no_matching.append((i, zip_code, city))

## Check best matching based on zip: first if same city name then if contained
#ls_matching = []
#for indiv_id, ls_addresses in master_addresses.iteritems():
#  if ls_addresses:
#    for address in ls_addresses:
#      zip_and_city = re.match('([0-9]{5,5}) (.*)', address[1])
#      zip_code = zip_and_city.group(1)
#      city = zip_and_city.group(2)
#      found_indicator = False
#      for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
#        if str_insee_harmonization(str_low_noacc(city)) == str_insee_harmonization(city_insee):
#          ls_matching.append((indiv_id, zip_code, code_insee))
#          found_indicator = True
#          break
#      if not found_indicator:
#        for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
#          if str_insee_harmonization(str_low_noacc(city)) in str_insee_harmonization(city_insee):
#            ls_matching.append((indiv_id, zip_code, code_insee))
#            print 'Matched', city, city_insee, zip_insee, '(', indiv_id, ')'
#            found_indicator = True
#            break
#      if found_indicator:
#        break
#    if not found_indicator:
#      print indiv_id, zip_insee, city, dict_corr_zip_insee[zip_code]
#      print 'Could not match', str_insee_harmonization(str_low_noacc(city))
