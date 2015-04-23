#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
from matching_insee import *
import os, sys
import re
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
import pprint

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')

path_dir_match_insee = os.path.join(path_data, u'data_insee', u'match_insee_codes')

# LOAD DATA STORES
ls_ls_stores = dec_json(os.path.join(path_dir_built_json, 'ls_ls_stores.json'))
# qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))

# MATCH STORES WITH INSEE COMMUNE
df_corr = pd.read_csv(os.path.join(path_dir_match_insee, 'df_corr_gas.csv'),
                      dtype = str)
ls_corr = [list(x) for x in df_corr.to_records(index = False)]
ls_corr = format_correspondence(ls_corr)

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
    ## todo: refactor standardization
    #city_standardized = re.sub(u'^SAINT(E\s|\s)', u'ST\\1', city.replace(u'-', u' '))
    #for old, new in ls_str_insee_replace:
    #  city_standardized = format_str_city_insee(city_standardized.replace(old, new))
    city_standardized = format_str_city_insee(city.replace(u"''", u" "))
    for corr_row in ls_corr:
      if city_standardized == corr_row[0]:
        row[3].append(corr_row)
    ls_rows.append(row)

# Check problems and, aside, manually establish a list of corrections
ls_city_match = dec_json(os.path.join(path_dir_built_json, 'ls_city_match.json'))
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
ls_unmatched_general = [row for row in ls_corr if row[3] not in ls_shp_insee]
# enc_json(ls_unmatched_general, os.path.join(path_data, u'temp_file_obs_and_drop'))

# Specify Ardts for Paris/Marseille/Lyon + fix two cities
# Got to be cautious not to write to correspondence (essentially ls_ls... points to corresp)

# TODO: fix in a more robust way (avoid repetition also)

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


# LOAD QLMC STORE INFO

df_stores['Magasin'] = df_stores['Enseigne'] + ' ' + df_stores['Commune']
ls_ls_qlmc_store_info = dec_json(os.path.join(path_dir_built_json,
                                              'ls_ls_qlmc_store_info.json'))
# Store names in qlmc price files
ls_ls_store_names = [list(df_stores['Magasin'][df_stores['P'] == i].values)\
                       for i in range(13)]

# Store names in info files
ls_ls_store_info_names = [[x[0] for x in row] for row in ls_ls_qlmc_store_info]

for i, ls_store_info_names in enumerate(ls_ls_store_info_names):
  print u'\nSize of info file {:d}: {:d}'.format(i, len(ls_store_info_names))
  print u'Matching vs each period price records:'
  for j in range(13):
    set_isct = set(ls_store_info_names).intersection(set(ls_ls_store_names[j]))
    print j, len(set_isct)

# 0th file => Little wit 0-3... check 4-5?
# 1st file => Period 6 (100%)
# 2d  file => Period 7 (100%)
# 3d  file => Period 9 (100% match in price file but got more info: why?)
# 4th file => Period 11 (100% match in price file but got more info: why?)
# 5th file => Check that really not Period 12?

# Global matching
set_store_info_names = set([store for ls_stores in ls_ls_store_info_names for store in ls_stores])
set_store_names = set([store for ls_stores in ls_ls_store_names for store in ls_stores])
# elements in info not in price files : 878
set_uselessinfo = set_store_info_names.difference(set_store_names)
# elements in price file not in info at all (any period)
print u'\nMatching of each price file name vs. all info'
for i, ls_store_names in enumerate(ls_ls_store_names):
  set_isct = set(ls_store_names).intersection(set_store_info_names)
  print i, len(set_isct)

# Check those in info not in price files of periods 9 and 11
set_nomatch_9 = set(ls_ls_store_info_names[3]).difference(set(ls_ls_store_names[9]))
# pprint.pprint(list(set_nomatch_9))
set_nomatch_11 = set(ls_ls_store_info_names[4]).difference(set(ls_ls_store_names[11]))
# pprint.pprint(list(set_nomatch_11))
# For both: essentially hard discount: probably not enough products

# todo: check those missing in price files of period 8, 10 (and 12)
set_nomatch_8 = set(ls_ls_store_names[8]).difference(set_store_info_names)
# pprint.pprint(list(set_nomatch_8))
set_nomatch_10 = set(ls_ls_store_names[10]).difference(set_store_info_names)

# todo: make sure never two stores with same name within info files
ls_rows_qlmc_store_info  = [[i] + store for i, ls_store in enumerate(ls_ls_qlmc_store_info)\
                              for store in ls_store]
df_qlmc_store_info = pd.DataFrame(ls_rows_qlmc_store_info,
                                  columns = ['P_info', 'Magasin', 'QLMC_Dpt', 'QLMC_Surface'])
# print df_qlmc_stores.to_string()

# todo: make sure never two stores with same name / diff dpt or surface across info files
se_qsi_vc = df_qlmc_store_info['Magasin'].value_counts()
#for x in se_qsi_vc[se_qsi_vc > 1].index:
#  print df_qlmc_store_info[df_qlmc_store_info['Magasin'] == x]
## presen of variations in surfaces (maybe precision issue sometimes but also chges)

# Merge store_info with df_stores conservatively i.e. by period
df_qlmc_store_info = df_qlmc_store_info[(df_qlmc_store_info['P_info'] != 0) &\
                                        (df_qlmc_store_info['P_info'] != 5)]

ls_replace_periods = [(1,6),
                      (2,7),
                      (3,9),
                      (4,11)]
for store_info_per, qlmc_per in ls_replace_periods:
  df_qlmc_store_info.loc[df_qlmc_store_info['P_info'] == store_info_per,
                         'P_info'] = qlmc_per
df_qlmc_store_info.rename(columns = {'P_info' : 'P'}, inplace = True)

# Delete duplicate in period 9
df_qlmc_store_info.drop_duplicates(subset = ['P', 'Magasin'], inplace = True)

df_stores_all = pd.merge(df_qlmc_store_info, df_stores, how = 'right', on = ['P', 'Magasin'])
df_stores_all['QLMC_Dpt'] = df_stores_all['QLMC_Dpt'].apply(lambda x: x.rjust(2,'0')\
                                                              if not pd.isnull(x) else x)
# any use?
df_stores_all['P'] = df_stores_all['P'].apply(lambda x: int(x))

# STORE DF STORES

# HDF (abandon?)
path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')
qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))
qlmc_data['df_qlmc_stores'] = df_stores_all
qlmc_data.close()

# CSV
df_stores_all.to_csv(os.path.join(path_dir_built_csv,
                                  'df_qlmc_stores_raw.csv'),
                     index = False,
                     encoding = 'UTF-8')
