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
import pprint

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

ls_ls_stores = dec_json(os.path.join(path_dir_built_json, 'ls_ls_stores'))

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))

# MATCH STORES WITH INSEE COMMUNE

# Load Correspondence File (Improvements for gas stations kept)
file_correspondence = open(os.path.join(path_dir_insee_match,
                                        'corr_cinsee_cpostal'),'r')
correspondence = file_correspondence.read().split('\n')[1:-1]
file_correspondence_update = open(os.path.join(path_dir_insee_match,
                                               'corr_cinsee_cpostal_update'),'r')
correspondence_update = file_correspondence_update.read().split('\n')[1:]
correspondence += correspondence_update
file_correspondence_gas_path = open(os.path.join(path_dir_insee_match,
                                                 'corr_cinsee_cpostal_gas_patch'),'r')
correspondence_gas_patch = file_correspondence_gas_path.read().split('\n')
correspondence += correspondence_gas_patch
correspondence = [row.split(';') for row in correspondence]
# Harmonize: 5 chars code_insee (beg 0) and Corsica: A and B (no mistake possible)
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
ls_str_insee_replace = [[u'\xc9', u'E'],
                        [u'\xc8', u'E'],
                        [u'\xca', u'E'],
                        [u'\xd4', u'O'],
                        [u'\xc2', u'A'],
                        [u'\xce', u'I'],
                        [u"''", u" "],
                        [u"'", u" "]]
ls_rows = []
for i, ls_stores in enumerate(ls_ls_stores):
  for store in ls_stores:
    chain, city = get_split_chain_city(store, ls_chain_brands)
    row = [i, chain, city, []]
    city_standardized = re.sub(u'^SAINT(E\s|\s)', u'ST\\1', city.replace(u'-', u' '))
    for old, new in ls_str_insee_replace:
      city_standardized = city_standardized.replace(old, new)
    # todo: get rid of accents for period 11
    for corr_row in correspondence:
      if city_standardized == corr_row[0]:
        row[3].append(corr_row)
    ls_rows.append(row)

# Check problems and, aside, manually establish a list of corrections
ls_city_match = dec_json(os.path.join(path_dir_built_json, 'ls_city_match'))
c = 0
ls_pbms = []
for row in ls_rows:
  if len(row[3]) == 1:
    c+=1
  elif (len(row[3]) > 1) and\
       (all(res[3] == row[3][0][3] for res in row[3])):
    row[3] = [row[3][0]] # what about city name though?
    c+=1
  else:
    pb_bool = True
    for store, row_insee in ls_city_match:
      if row[1:3] == store:
        row[3] = [row_insee]
        pb_bool = False
        break
    if pb_bool == False:
      c+=1
    else:
      ls_pbms.append(row)
print u'Nb no insee match', len(ls_pbms)

# Normally no pbm left in insee matching hence can attribute the only result
for row in ls_rows:
  if len(row[3]) != 1:
    print u'Need to fix', row
    break
  else:
    row[3] = row[3][0]

# CHECK INSEE CODES VS. GEOFLA

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

path_dir_geofla = os.path.join(path_data, u'data_maps', u'GEOFLA_COM_WGS84')
m_fra.readshapefile(os.path.join(path_dir_geofla, u'COMMUNE'),
                    u'communes_fr',
                    color = u'none',
                    zorder=2)

ls_shp_insee = [row[u'INSEE_COM'] for row in m_fra.communes_fr_info]
ls_unmatched_general = [row for row in correspondence if row[3] not in ls_shp_insee]
# enc_json(ls_unmatched_general, os.path.join(path_data, u'temp_file_obs_and_drop'))

# Specify Ardts for Paris/Marseille/Lyon + fix two cities
# Got to be cautious not to write to correspondence (essentially ls_ls... points to corresp)
# TODO: fix this in a more robust way (avoid repetition also)

#ls_ls_ls_store_insee[0][55]  = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13210'] # 13010
#ls_ls_ls_store_insee[0][106] = ['PARIS', '75000', 'PARIS', u'75116'] # 75016
#ls_ls_ls_store_insee[0][119] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13209'] # 13009
#ls_ls_ls_store_insee[0][159] = ['LYON', '69000', 'RHONE', u'69387'] # 69007
#ls_ls_ls_store_insee[0][177] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13208'] # 13008
#ls_ls_ls_store_insee[0][184] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13212'] # 13012
#ls_ls_ls_store_insee[0][339] = ['PARIS', '75000', 'PARIS', u'75113'] # 75013
#
#ls_ls_ls_store_insee[1][60]  = ['LYON', '69000', 'RHONE', u'69383'] # 69003
#ls_ls_ls_store_insee[1][86]  = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13207'] # 13007
#ls_ls_ls_store_insee[1][160] = ['PLAN DE CAMPAGNE', '13170', 'BOUCHES DU RHONE', u'13071'] # 13170
#ls_ls_ls_store_insee[1][249] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13211'] # 13011
#
#ls_ls_ls_store_insee[2][77]  = ['PARIS', '75000', 'PARIS', u'75113'] # 75013
#ls_ls_ls_store_insee[2][157] = ['BIHOREL', '76420', 'SEINE MARITIME', u'76108'] # 76230
#
#ls_ls_ls_store_insee[7][94] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13210'] # 13010 Auhan
#
#ls_ls_ls_store_insee[9][99] = ['LYON', '69000', 'RHONE', u'69383'] # 69003 Carrefour
#ls_ls_ls_store_insee[9][111] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13210'] # 13010 Auchan
#ls_ls_ls_store_insee[9][297] = ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13209'] # 13009 Leclerc

ls_fix_insee = [[55      , ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13210']], # 13010
                [106     , ['PARIS', '75000', 'PARIS', u'75116']], # 75016
                [119     , ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13209']], # 13009
                [159     , ['LYON', '69000', 'RHONE', u'69387']], # 69007
                [177     , ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13208']], # 13008
                [184     , ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13212']], # 13012
                [339     , ['PARIS', '75000', 'PARIS', u'75113']], # 75013
                [344+60  , ['LYON', '69000', 'RHONE', u'69383']], # 69003
                [344+86  , ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13207']], # 13007
                [344+160 , ['PLAN DE CAMPAGNE', '13170', 'BOUCHES DU RHONE', u'13071']], # 13170
                [344+249 , ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13211']], # 13011
                [679+77  , ['PARIS', '75000', 'PARIS', u'75113']], # 75013
                [679+157 , ['BIHOREL', '76420', 'SEINE MARITIME', u'76108']], # 76230
                [3409+94 , ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13210']], # 13010 Auhan
                [4667+99 , ['LYON', '69000', 'RHONE', u'69383']], # 69003 Carrefour
                [4667+111, ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13210']], # 13010 Auchan
                [4667+297, ['MARSEILLE', '13000', 'BOUCHES DU RHONE', u'13209']]] # 13009 Leclerc

for row_ind, insee_info in ls_fix_insee:
  ls_rows[row_ind][3] = insee_info

# insee code no more in use? => todo: update correspondence
ls_unmatched_store_cities = [row for row in ls_rows\
                               if row[3] and row[3][3] not in ls_shp_insee]
# if not match for store just None (could drop it)
ls_rows = [row[:3] + list(row[3]) if row[3] else row[:3] + [None, None, None, None]\
             for row in ls_rows]
#enc_stock_json(ls_rows, os.path.join(folder_built_qlmc_json, 'ls_ls_store_insee'))

# BUILD STORE DATAFRAME

ls_columns = ['P', 'Enseigne', 'Commune',
              'INSEE_Commune', 'INSEE_ZIP', 'INSEE_Dpt', 'INSEE_Code']
df_stores = pd.DataFrame(ls_rows, columns = ls_columns)

# CHECK SUPERMARKET NAMES

## Stores likely to generate multi matching but with disambig. possibilities
## C.C. CITE2 is SOUVENIR FRANCAIS => for matching
#print df_stores[df_stores['INSEE_ZIP'].str.slice(stop=2) == '75'].to_string()
#print df_stores[(df_stores['Commune'].str.contains('carcassonne', case=False)) |\
#                (df_stores['INSEE_Commune'].str.contains('carcassonne', case=False))]
df_stores.sort(['INSEE_Code', 'P', 'Enseigne'], inplace = True)
se_insee_vc = df_stores['INSEE_Code'].value_counts()
# default: sorted in decreasing order
for insee_code in se_insee_vc[0:20].index:
	print '\n\n', df_stores[df_stores['INSEE_Code'] == insee_code].to_string()

# STORE DF STORES

#qlmc_data['df_qlmc_stores'] = df_stores
#qlmc_data.close()



## LOAD INSEE DATA
#path_data_insee_extract = os.path.join(path_dir_insee_extracts, 'data_insee_extract.csv')
#df_insee = pd.read_csv(path_data_insee_extract, encoding = 'utf-8', dtype= str)
#
#df_stores.index = df_stores['INSEE_Code']
#df_insee.index = df_insee['CODGEO']
#
#df_nu = df_stores.join(df_insee)
#df_nu['CODGEO'] = df_nu.index
#
#ls_disp_uu = ['UU2010', 'P', 'Enseigne', 'Commune', 'LIBUU2010',
#              'POP_MUN_07_UU', 'TAILLE_UU', 'TYPE_UU']
## View UU
#df_nu.sort(['UU2010', 'P', 'Enseigne'], inplace = 1)
#print '\n', df_nu[ls_disp_uu].ix[0:10].to_string()

# print df_stores[df_stores['INSEE_Code'] == '63113'].to_string()
