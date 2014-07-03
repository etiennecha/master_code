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
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

fra_stores = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'fra_stores.h5'))

## BUILD DF FRA STORES
#print fra_stores.keys()
## print fra_stores.keys()
#ls_df_chain_names = ['/df_auchan',
#                     '/df_carrefour',
#                     '/df_casino',
#                     '/df_cora',
#                     '/df_franprix',
#                     '/df_intermarche',
#                     '/df_leclerc',
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
#df_fra_stores['insee_code'] = df_fra_stores['gps'].apply(\
#                                lambda x: gps_to_locality(x, m_fra, df_com, 'com_code'))
#
#fra_stores['df_fra_stores'] = df_fra_stores # necessary

# INSPECT ZIP CODE & CITY

df_fra_stores = fra_stores['df_fra_stores']

for i, row in df_fra_stores.iterrows():
	if not re.match(u'^[0-9]{5}$', row['zip']):
		print i, row['zip'], row['city']

def clean_zip_code(zip_code):
  zip_code = zip_code.replace(u' ', u'').replace(u"'", u'')
  if re.search(u'^[0-9]{4}$', zip_code):
    zip_code  = u'0%s' %zip_code
  if not re.match(u'[0-9]{5}$', zip_code):
    print zip_code
  return zip_code

df_fra_stores['zip'] = df_fra_stores['zip'].apply(lambda x: clean_zip_code(x))

for i, row in df_fra_stores.iterrows():
	if re.search(u'CEDEX', row['city'], re.IGNORECASE):
		print i, row['zip'], row['city']
  #elif re.search(u'[0-9]', row['city']):
  #  print i, row['zip'], row['city']

#ls_big_cities = [u'PARIS', u'MARSEILLE', u'LYON', u'TOULOUSE', u'LILLE', u'NANTES',
#                 u'STRASBOURG', u'MONTPELLIER', u'BORDEAUX', u'RENNES', 'LE HAVRE',
#                 u'REIMS', u'LILLE']
#for i, row in df_fra_stores.iterrows():
#  for big_city in ls_big_cities:
#    if re.search(big_city, row['city'], re.IGNORECASE):
#      print i, row['zip'], row['city']
#      break

def clean_city(city):
  # does not solve pbm allone: CEDEX => specific zip code
  re_cedex = re.search(u'CEDEX', city, flags=re.IGNORECASE)
  if re_cedex:
    city = city[:re_cedex.start()].strip()
  return city

df_fra_stores['city'] = df_fra_stores['city'].apply(lambda x: clean_city(x))

fra_stores['df_fra_stores'] = df_fra_stores

# Serious pbms: 1220, 6895

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

# Generate dict of non unique cities by dpt
ls_corr_insee_columns = ['city', 'zip_code', 'dpt', 'insee_code']
df_corr_insee = pd.DataFrame(correspondence, columns = ls_corr_insee_columns)
df_corr_insee = df_corr_insee[df_corr_insee['city']!='Commune'] # CHECK ISSUE
df_corr_insee.reset_index(drop=True, inplace=True)
df_corr_insee['dpt_code'] = df_corr_insee['zip_code'].str.slice(stop=2)

dict_dpt_ls_ambiguous = {}

# Seems most have same insee code... could keep them
for dpt_code in df_corr_insee['dpt_code'].unique():
  df_dpt_corr_insee = df_corr_insee[df_corr_insee['dpt_code'] == dpt_code]
  se_dpt_city_vc = df_dpt_corr_insee['city'].value_counts()
  df_dpt_corr_insee.index = df_dpt_corr_insee['city']
  df_dpt_corr_insee['nb_city'] = se_dpt_city_vc
  dict_dpt_ls_ambiguous[dpt_code] = []
  for i, row in df_dpt_corr_insee[df_dpt_corr_insee['nb_city'] > 1].iterrows():
    if len(df_dpt_corr_insee['insee_code']\
            [df_dpt_corr_insee['city'] == row['city']].unique()) > 1:
      dict_dpt_ls_ambiguous[dpt_code].append(row['city'])
# keep only city once in each list
dict_dpt_ls_ambiguous = {k: list(set(v)) for k,v in dict_dpt_ls_ambiguous.items()}

ls_tup_big_cities = [[u'PARIS', u'75'],
                     [u'MARSEILLE', u'13'],
                     [u'LYON', u'69'],
                     [u'TOULOUSE', u'31'],
                     [u'NICE', '06'],
                     [u'NANTES', u'44'],
                     [u'STRASBOURG', u'67'],
                     [u'MONTPELLIER', u'34'],
                     [u'BORDEAUX', u'33'],
                     [u'RENNES', u'35'],
                     ['LE HAVRE', u'76'],
                     [u'REIMS', u'51'],
                     [u'LILLE', u'59']]

# matching
print u'\nMatching Zip/City vs. INSEE codes'
ls_matching = []
ls_no_zip_match = []
ls_no_city_match = []
for i, row in df_fra_stores.iterrows():
  found_indicator = False
	# print row['zip'], row['city']
  zip_code, city = row['zip'], row['city']
  try:
    for city_insee, zip_insee, dpt_insee, code_insee in dict_corr_zip_insee[zip_code]:
      if str_insee_harmonization(str_low_noacc(city)) == str_insee_harmonization(city_insee):
        ls_matching.append((i, zip_code, code_insee))
        found_indicator = True
        break
    if not found_indicator:
      for city_insee, zip_insee, dpt_insee, code_insee in dict_corr_zip_insee[zip_code]:
        if str_insee_harmonization(str_low_noacc(city)) in str_insee_harmonization(city_insee):
          ls_matching.append((i, zip_code, code_insee))
          print 'Matched', city, city_insee, zip_insee, '(', i, ')'
          found_indicator = True
          break
    if not found_indicator:
      for big_city, big_city_dpt in ls_tup_big_cities:
        if re.match(big_city, city_insee, flags=re.IGNORECASE) and zip_code[:2] == big_city_dpt:
          for city_insee, zip_insee, dpt_insee, code_insee in dict_corr_dpt_insee[big_city_dpt]:
            if re.match(big_city, city_insee, flags=re.IGNORECASE) and zip_code == zip_insee:
              ls_matching.append((i, zip_code, code_insee))
              print 'Matched', city, city_insee, zip_insee, '(', i, ')'
              found_indicator = True
              break
    if not found_indicator:
      for city_insee, zip_insee, dpt_insee, code_insee in dict_corr_dpt_insee[zip_code[:2]]:
          if (city_insee not in dict_dpt_ls_ambiguous[zip_code[:2]]) and\
             (str_insee_harmonization(str_low_noacc(city)) == str_insee_harmonization(city_insee)):
            ls_matching.append((i, zip_code, code_insee))
            print 'Matched (zip=>dpt)', city, city_insee, zip_insee, '(', i, ')'
            found_indicator = True
            break
    if not found_indicator:
      ls_no_city_match.append([i, zip_insee, city])
  except:
    try:
      for city_insee, zip_insee, dpt_insee, code_insee in dict_corr_dpt_insee[zip_code[:2]]:
          if (city_insee not in dict_dpt_ls_ambiguous[zip_code[:2]]) and\
             (str_insee_harmonization(str_low_noacc(city)) == str_insee_harmonization(city_insee)):
            ls_matching.append((i, zip_code, code_insee))
            print 'Matched (dpt)', city, city_insee, zip_insee, '(', i, ')'
            found_indicator = True
            break
      # Pbm: Cedex: no ardt for big cities...
      if not found_indicator:
        for big_city, big_city_dpt in ls_tup_big_cities:
          if re.match(big_city, city_insee, flags=re.IGNORECASE) and zip_code[:2] == big_city_dpt:
            for city_insee, zip_insee, dpt_insee, code_insee in dict_corr_dpt_insee[big_city_dpt]:
              if re.match(big_city, city_insee, flags=re.IGNORECASE):
                ls_matching.append((i, zip_code, code_insee))
                print 'Matched (dpt-big city)', city, city_insee, zip_insee, '(', i, ')'
                found_indicator = True
                break
      if not found_indicator:
         ls_no_zip_match.append([i, zip_code, city])
    except:
      print 'WHAAAT', zip_code, city

se_matching = pd.Series([x[2] for x in ls_matching], index = [x[0] for x in ls_matching])
df_fra_stores['insee_code_2'] = se_matching

pd.set_option('display.max_colwidth', 30)

# Can add to correspondence (could be useful later...)
ls_city_replace = [[u'Decines', u'Decines Charpieu'],
                   [u'Saint-Maries de la Mer', u'Stes Maries de la Mer'],
                   [u'Waldighoffen', u'Waldighofen'],
                   [u'Chateauneuf de Grasse', u'Chateauneuf Grasse'],
                   [u'Vorey-sur-Arzon', u'Vorey'],
                   [u'Terrasson', u'Terrasson Lavilledieu'],
                   [u"Briec de l'Odet", u'Briec'],
                   [u'Saint-Amand de Boixe', u'Saint-Amant-de-Boixe'], # fix store city?
                   [u'Nîmes Vacquerolles', u'Nîmes'],
                   [u'Ile de Groix', u'Groix'],
                   [u'Lambres-lez-Aire', u'Lambres'],
                   [u'Seynes les Alpes', u'Seyne'],
                   [u'LE PERREUX/M', u'Le Perreux sur Marne']] # fix store city?

# Stores with no insee code at all
print df_fra_stores[(pd.isnull(df_fra_stores['insee_code'])) &\
                    (pd.isnull(df_fra_stores['insee_code_2']))].to_string()

# Stores with two different insee codes
print df_fra_stores[(~pd.isnull(df_fra_stores['insee_code'])) &\
                    (~pd.isnull(df_fra_stores['insee_code_2'])) &\
                    (df_fra_stores['insee_code'] != df_fra_stores['insee_code_2'])].to_string()

# load insee data extract
df_insee = pd.read_csv(os.path.join(path_dir_insee_extracts, 'data_insee_extract.csv'),
                       encoding = 'utf-8',
                       dtype= str)
## excludes dom tom
#df_insee = df_insee[~df_insee[u'CODGEO'].str.contains('^97')]
df_insee['POP_MUN_2007_COM'] = \
  df_insee['POP_MUN_2007_COM'].apply(lambda x: float(x))
#ls_mic_1 = [x for x in df_fra_stores['insee_code'].unique() if x not in df_insee['CODGEO'].values]
#ls_mic_2 = [x for x in df_fra_stores['insee_code_2'].unique() if x not in df_insee['CODGEO'].values]

df_fra_stores['insee_code_final'] = df_fra_stores['insee_code']
df_fra_stores['insee_code_final'][pd.isnull(df_fra_stores['insee_code_final'])] =\
   df_fra_stores['insee_code_2']

# Check that no ambiguity in corsica
ls_corsica_icA = list(df_insee['CODGEO'][df_insee['CODGEO'].str.slice(stop=2) == '2A'].values)
ls_corsica_icA0 = [x.replace('A', '0') for x in ls_corsica_icA]
ls_corsica_icB = list(df_insee['CODGEO'][df_insee['CODGEO'].str.slice(stop=2) == '2B'].values)
ls_corsica_icB0 = [x.replace('B', '0') for x in ls_corsica_icB]
ls_corsica_amb = [x for x in ls_corsica_icA0 if x in ls_corsica_icB0]
dict_corsica_ic = {x.replace(u'A', u'0').replace(u'B', '0'): x\
                     for x in ls_corsica_icA + ls_corsica_icB}
# need to be sure all codes have 5 figures
df_fra_stores['insee_code_final'] = df_fra_stores['insee_code_final'].apply(\
                                      lambda x: dict_corsica_ic[x] if (not pd.isnull(x)) and\
                                                                      (x[:2] == '20') else x)

ls_mic = [x for x in df_fra_stores['insee_code_final'].unique() if x not in df_insee['CODGEO'].values]
ls_mic.sort()
print ls_mic
# pbms apart for 3 cities with ardts:
ls_update_ic = [['66910', '66008'],
                ['79017', '79195']]
for old, new in ls_update_ic:
  df_fra_stores['insee_code_final'][df_fra_stores['insee_code_final'] == old] = new

# for now: drops a bit too many stores
df_fra_stores = df_fra_stores[(~pd.isnull(df_fra_stores['insee_code_final'])) &\
                              (df_fra_stores['insee_code_final'].str.slice(stop=2) != '96') &\
                              (df_fra_stores['insee_code_final'].str.slice(stop=2) != '97') &\
                              (df_fra_stores['insee_code_final'].str.slice(stop=2) != '98') &\
                              (df_fra_stores['insee_code_final'].str.slice(stop=2) != '99')]

# No gps
print 'No gps:', len(df_fra_stores[(pd.isnull(df_fra_stores['gps'])) |\
                                  (df_fra_stores['gps'] == '')])
#print df_fra_stores[(pd.isnull(df_fra_stores['gps'])) |\
#                                  (df_fra_stores['gps'] == '')].to_string()

# Example: Clermont Ferrand
print df_fra_stores[df_fra_stores['insee_code_final'] == '63113'].to_string()

#fra_stores['df_fra_stores'] = df_fra_stores
#fra_stores.close()

# todo: match with BV, AU, UU
# todo: build BV, AU, UU datasets (AND COMMUNE)
