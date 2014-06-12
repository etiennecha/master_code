#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import json
import numpy as np
import re
import ast
import pprint
from functions_geocoding import *
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
# import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def parse_kml(kml_str):
  ls_kml_data = []
  ls_placemarks = re.findall('<Placemark>(.*?)<\\/Placemark>',kml_str)
  for placemark in ls_placemarks:
    name = re.search('<name>(.*?)<\\/name>', placemark).group(1)
    coordinates = re.search('<coordinates>(.*?)<\\/coordinates>', placemark).group(1)
    coordinates = map(lambda x: float(x), coordinates.split(',')[0:2][::-1])
    ls_kml_data.append((name, coordinates))
  return ls_kml_data

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_source_json = os.path.join(path_dir_qlmc, 'data_source', 'data_json_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_source_chains = os.path.join(path_dir_qlmc, 'data_source', 'data_chain_websites')
path_dir_source_kml = os.path.join(path_dir_qlmc, 'data_source', 'data_kml')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')

ls_chain_general = ['list_auchan_general_info',
                    'list_carrefour_general_info',
                    'list_leclerc_general_info',
                    'list_geant_casino_general_info',
                    'list_u_general_info', # contains gps
                    'list_cora_general_info', # contains gps
                    'list_franprix_general_info', # contains gps (small stores though?)
                    'list_super_casino_general_info', # contains gps...
                    'list_monoprix_general_info', # gps in kml (for now)
                    'list_intermarche_general_info'] # gps in kml (for now)

ls_chain_full = [ 'list_auchan_full_info',
                  'list_carrefour_full_info',
                  'list_leclerc_full_info',
                  'list_geant_casino_full_info']
                    
ls_kml = ['monoprix.kml',
          'intermarche.kml']

ls_ls_tuple_stores = dec_json(os.path.join(path_dir_built_json, 'ls_ls_tuple_stores'))

# ##############################################
# MATCH STORE'S CITY WITH CITY (INSEE CORRES.)
# ##############################################

# Load Correspondence File (Improvements for gas stations kept)
file_correspondence = open(os.path.join(path_dir_insee_match, 'corr_cinsee_cpostal'),'r')
correspondence = file_correspondence.read().split('\n')[1:-1]
file_correspondence_update = open(os.path.join(path_dir_insee_match, 'corr_cinsee_cpostal_update'),'r')
correspondence_update = file_correspondence_update.read().split('\n')[1:]
correspondence += correspondence_update
file_correspondence_gas_path = open(os.path.join(path_dir_insee_match, 'corr_cinsee_cpostal_gas_patch'),'r')
correspondence_gas_patch = file_correspondence_gas_path.read().split('\n')
correspondence += correspondence_gas_patch
correspondence = [row.split(';') for row in correspondence]
# Harmonize: 5 chars code_insee (beg 0) and Corsica: A and B (no mistake possible in principle)
for i, (commune, zip_code, department, insee_code) in enumerate(correspondence):
  if len(insee_code) == 4:
    insee_code = '0%s' %insee_code
    correspondence[i] = (commune, zip_code, department, insee_code)
# Dict not of much help in this case a priori
dict_insee_zip = {}
for (city, zip_code, dpt, cinsee) in correspondence:
  dict_insee_zip.setdefault(zip_code, []).append((city, zip_code, dpt, cinsee))
dict_insee_dpt = {}
for (city, zip_code, dpt, cinsee) in correspondence:
  dict_insee_dpt.setdefault(zip_code[:-3], []).append((city, zip_code, dpt, cinsee))
dict_insee_city = {}
for (city, zip_code, dpt, cinsee) in correspondence:
  dict_insee_city.setdefault(city, []).append((city, zip_code, dpt, cinsee))

# Match store's city vs. all city names in correspondence (position 0)
# NB: City names can be ambiguous (several cities with same name...)
nb_periods = 6
ls_ls_ls_store_insee = []
for ls_tuple_stores in ls_ls_tuple_stores[:nb_periods]:
  ls_ls_store_insee_temp = []
  for (brand, city) in ls_tuple_stores:
    ls_store_insee = []
    for row in correspondence:
      if city == row[0]:
        ls_store_insee.append(row)
    ls_ls_store_insee_temp.append(ls_store_insee)
  ls_ls_ls_store_insee.append(ls_ls_store_insee_temp)  

# Check problems and, aside, manually establish a list of corrections
ls_city_match = dec_json(os.path.join(path_dir_built_json, 'ls_city_match'))
# todo: check if corrections made at previous perdiods...
ls_ls_pbms = []
for period_ind, ls_results in enumerate(ls_ls_ls_store_insee):
  c = 0
  ls_pbms = []
  for ind_store, results in enumerate(ls_results):
    if len(results) == 1:
      c+=1
    elif (len(results) > 1) and (all(result[3] == results[0][3] for result in results)):
      ls_ls_ls_store_insee[period_ind][ind_store] = results[0]
      c+=1
    else:
      pb_bool = True
      for store, row_insee in ls_city_match:
        if ls_ls_tuple_stores[period_ind][ind_store] == store:
          ls_ls_ls_store_insee[period_ind][ind_store] = row_insee
          pb_bool = False
          break
      if pb_bool == False:
        c+=1
      else:
        ls_pbms.append((ls_ls_tuple_stores[period_ind][ind_store], results))
  ls_ls_pbms.append(ls_pbms)
  print 'Period', period_ind, 'Got', c, 'out of', len(ls_results)

# todo: drop store if empty result though correction already done (city could not be identified for sure)

# ####################################################
# MATCH STORE'S CITY WITH ADDRESS / GPS (IN PROGRESS)
# ####################################################

# todo: Use brands' list of stores with addresses and gps coordinates

ls_chain_general_info = []
for file_general_info in ls_chain_general:
  ls_chain_general_info.append(dec_json(os.path.join(path_dir_source_chains, file_general_info)))

ls_chain_full_info = []
for file_full_info in ls_chain_full:
  ls_chain_full_info.append(dec_json(os.path.join(path_dir_source_chains, file_full_info)))

ls_chain_kml = []
for file_kml in ls_kml:
  ls_chain_kml.append(parse_kml(open(os.path.join(path_dir_source_kml, file_kml), 'r').read()))

# reconcile:
# [x[1].upper() for x in master_3[0]]
# [x[0] for x in ls_chain_kml[0]]

# for elt in ls_chain_kml[1]:
	# if elt[0].upper() not in [x[0].upper() for x in master_3[-1]]:
		# c+=1

# Full has all info for: Auchan, Carrefour, Leclerc (no need for general info)
# Also full info for Geant but these are also in Super casino (check)
# General has all info for: U, Cora, Franprix

master_1 = ls_chain_full_info[:4]
master_2 = ls_chain_general_info[4:8]
master_3 = ls_chain_general_info[8:] # reconcile gps (not needed a priori for qlmc)

# todo: areas of stores... use the few xls files found + try with OSM (area of building polygons...)

# ####################
# PLOT STORES' MAPS
# ####################

# todo: Use basemap: either IGN Geo or Routes (?)
# todo: Beware to display all stores when several in a town!

# France
x1 = -5.
x2 = 9.
y1 = 42.
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

path_commune = r'\data_maps\GEOFLA_COM_WGS84'
m_fra.readshapefile(path_data + path_commune + '\COMMUNE', 'communes_fr', color = 'none', zorder=2)

# todo: see if commune file is recent enough (matching of INSEE codes with current INSEE data)
# todo: if recent enough: do matching vs commune rather than my creepy correspondence file...

# todo: fix matching problems: Corsica ? DOM-TOM (or just forget about this creepy file?)
ls_shp_insee = [row['INSEE_COM'] for row in m_fra.communes_fr_info]
ls_unmatched_general = [row for row in correspondence if row[3] not in ls_shp_insee]
# enc_json(list_unmatched_general, path_data + r'/temp_file_obs_and_drop')

for i in range(nb_periods):
  ls_ls_ls_store_insee[i] = [elt[0] if len(elt)==1 else elt for elt in ls_ls_ls_store_insee[i]]
# Specify Ardts for Paris/Marseille/Lyon + fix two cities
# Got to be cautious not to write to correspondence (essentially ls_ls... points to corresp)
ls_ls_ls_store_insee[0][55]  = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13210'] # 13010
ls_ls_ls_store_insee[0][106] = ['PARIS', '75000', 'PARIS', u'75116'] # 75016
ls_ls_ls_store_insee[0][119] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13209'] # 13009
ls_ls_ls_store_insee[0][159] = ['LYON', '69000', 'RHONE', u'69387'] # 69007
ls_ls_ls_store_insee[0][177] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13208'] # 13008
ls_ls_ls_store_insee[0][184] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13212'] # 13012
ls_ls_ls_store_insee[0][339] = ['PARIS', '75000', 'PARIS', u'75113'] # 75013

ls_ls_ls_store_insee[1][60]  = ['LYON', '69000', 'RHONE', u'69383'] # 69003
ls_ls_ls_store_insee[1][86]  = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13207'] # 13007
ls_ls_ls_store_insee[1][160] = ['PLAN DE CAMPAGNE', '13170', 'BOUCHES DU RHONE', u'13071'] # 13170
ls_ls_ls_store_insee[1][249] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13211'] # 13011

ls_ls_ls_store_insee[2][77]  = ['PARIS', '75000', 'PARIS', u'75113'] # 75013
ls_ls_ls_store_insee[2][157] = ['BIHOREL', '76420', 'SEINE MARITIME', u'76108'] # 76230

ls_ls_unmatched_store_cities = [[] for i in range(nb_periods)]
for i in range(nb_periods):
  ls_ls_ls_store_insee[i] = [elt[0] if len(elt)==1 else elt for elt in ls_ls_ls_store_insee[i]]
  ls_ls_unmatched_store_cities[i] = [(indiv_ind, row, ls_ls_tuple_stores[i][indiv_ind]) \
                                          for indiv_ind, row in enumerate(ls_ls_ls_store_insee[i]) \
                                          if row and row[3] not in ls_shp_insee]

ls_ls_store_insee = ls_ls_ls_store_insee
#enc_stock_json(ls_ls_store_insee, os.path.join(folder_built_qlmc_json, 'ls_ls_store_insee'))
                                          
# Build dict_city_polygon (some have same insee code ?)
# TODO if too long to build: only those which are needed
ls_required_insee_codes = [store[3] for ls_stores in ls_ls_ls_store_insee\
                             for store in ls_stores if store]
dict_city_polygons = {}
for city_info, city_gps in zip(m_fra.communes_fr_info, m_fra.communes_fr):
  if city_info['INSEE_COM'] in ls_required_insee_codes:
    dict_city_polygons[city_info['INSEE_COM']] = Polygon(city_gps)

ls_ls_store_gps_b = []
for ls_stores in ls_ls_ls_store_insee:
  ls_store_gps_b = []
  for store in ls_stores:
    repr_point = []
    if store:
      try:
        repr_point = dict_city_polygons[store[3]].representative_point()
        repr_point = [repr_point.x, repr_point.y]
      except:
        print store, ': check insee code'
    ls_store_gps_b.append(repr_point)
  ls_ls_store_gps_b.append(ls_store_gps_b)

ls_gps_b_draw = [gps_b for ls_store_gps_b in ls_ls_store_gps_b\
                   for gps_b in ls_store_gps_b if gps_b]

dev = m_fra.scatter([gps_b[0] for gps_b in ls_gps_b_draw],
                    [gps_b[1] for gps_b in ls_gps_b_draw],
                     3, marker = 'o', lw=0.25,
                     facecolor = '#1E90FF', edgecolor = 'w',
                     alpha = 0.5, antialiased = True, zorder = 3)

m_fra.drawcountries()
m_fra.drawcoastlines()  
#plt.savefig(path_data + r'\data_maps\graphs\test_supermarches.png' , dpi=700)

#TODO: match vs chain lists... going to be difficult though

# ##################################################################################
# DEPRECATED (TEST OF geocode_via_google VS. geocode_via_google_textsearch (best))
# ##################################################################################

# shop = ls_ls_tuple_stores[0][0]
# location = ', '.join(shop)

# # geocode_via_google is based uniquely on address
# test_geocoding = geocode_via_google(location)
# pprint.pprint(test_geocoding)

# test_textsearch = geocode_via_google_textsearch(location)
# pprint.pprint(test_textsearch)
# # => provides essentially formatted address + gps
# # TODO: see if can be more precise... else pick right one in the list of result if it's there...

# ###############################################################
# DEPRECATED (GEOCODING WITH geocode_via_google_textsearch)
# ###############################################################

# TODO: Some brands have changed since then e.g. CHAMPION => CARREFOUR MARKET etc.
# TODO: optimize vs. strong usage limitation (nb of queries...)
# => may want to restrict type 
# => may want to restrain to one request / location

# path_dict_location_google_places = path_data + folder_built_qlmc_json + r'/dict_location_google_places'
# if os.path.exists(path_dict_location_google_places):
  # dict_location_google_places = dec_json(path_dict_location_google_places)
  # print 'dict_location_google_places loaded: len %s' %len(dict_location_google_places)
# else:
  # dict_location_google_places = {}
  # print 'dict_location_google_places created: len 0'

# # PERIOD 0 ONLY SO FAR
# for chain, city in ls_ls_tuple_stores[0]:
  # location = chain + ', ' + city
  # if location not in dict_location_google_places.keys():
    # try:
      # status, result_textsearch = geocode_via_google_textsearch(location)
      # if status not in ['OVER_QUERY_LIMIT', 'REQUEST_DENIED', 'INVALID_REQUEST']:
        # dict_location_google_places[location] = result_textsearch
      # else:
        # print status, location
        # break
    # except Exception, e:
      # print e, location
      # break

# print 'dict_location_google_places updated: len %s' %len(dict_location_google_places)
# # enc_json(dict_location_google_places, path_dict_location_google_places)

# TODO: within results, scan fields 'name'/'formatted_address'/'types'(?) to check match
# TODO: distinguish: no match, one match, several matches => choose manually
