#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
import numpy as np
import pandas as pd
from functions_generic_qlmc import *
from functions_geocoding import *
import matplotlib.pyplot as plt

def enc_json(data, path_file):
  with open(path_file, 'w') as f:
    json.dump(data, f)

def dec_json(path_file):
  with open(path_file, 'r') as f:
    return json.loads(f.read())

path_built_2015 = os.path.join(path_data,
                               'data_supermarkets',
                               'data_built',
                               'data_qlmc_2015')
path_built_201415_csv = os.path.join(path_built_2015,
                                     'data_csv_2014-2015')
path_built_201415_json = os.path.join(path_built_2015,
                                     'data_json_2014-2015')

path_built_lsa = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_lsa')

path_built_lsa_csv = os.path.join(path_built_lsa,
                                  'data_csv')

path_api_keys = os.path.join(path_data, 'api_keys')
with open(os.path.join(path_api_keys, 'key_google_api.txt'), 'r') as f:
  key_google_api = f.read()

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##########
# LOAD DATA
# ##########

# Need to have build df_qlmc_competitors already
# Need to have df_stores including lsa_id (best gps coordinates)

df_comp_pairs = pd.read_csv(os.path.join(path_built_201415_csv,
                                         'df_comp_store_pairs.csv'),
                            dtype = {'id_lsa_0' : str,
                                     'id_lsa_1' : str},
                            encoding = 'utf-8')

df_lsa = pd.read_csv(os.path.join(path_built_lsa_csv,
                                  'df_lsa_active.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

df_stores = df_lsa[['id_lsa', 'latitude', 'longitude', 'region']].copy()
df_stores['lat'] = df_stores['latitude']
df_stores['lng'] = df_stores['longitude']

### Choose preferred gps
### Default to LSA (best quality)
##df_stores['lat'] = df_stores['latitude']
##df_stores['lng'] = df_stores['longitude']
### If no data from LSA: QLMC
##df_stores.loc[df_stores['lat'].isnull(), 'lat'] = df_stores['store_lat']
##df_stores.loc[df_stores['lng'].isnull(), 'lng'] = df_stores['store_lng']
### Ad hoc changes
##ls_final_gps = [['casino-prunelli-di-fiumorbo', 'qlmc'], # 4 and bad
##                ['carrefour-market-beaumont-le-roger', 'lsa'],
##                ['carrefour-market-anse', (45.9380, 4.7201)], # 2 and bad
##                ['super-u-saint-brevin-les-pins', 'lsa'],
##                ['centre-e-leclerc-oletta', 'lsa'],
##                ['leclerc-express-borgo', 'lsa'],
##                ['casino-rivieres', (45.7463, 0.3830)], # 3 and bad
##                ['u-express-bagnoles-de-l-orne', 'qlmc'], # 4 and bad
##                ['casino-estancarbon', 'lsa'],
##                ['intermarche-super-surgeres', 'lsa'],
##                ['centre-e-leclerc-joue-les-tours', 'lsa'],
##                ['carrefour-market-aussonne', 'lsa'], # check (resumed activity?)
##                ['carrefour-market-vauvert', 'qlmc']] # 3 and bad
##for store_id, gps_option in ls_final_gps:
##  if gps_option == 'qlmc':
##    for coord, source_coord in [['lat', 'store_lat'],
##                                ['lng', 'store_lng']]:
##      df_stores.loc[df_stores['store_id'] == store_id, coord] =\
##        df_stores.loc[df_stores['store_id'] == store_id, source_coord]
##  elif isinstance(gps_option, tuple):
##    df_stores.loc[df_stores['store_id'] == store_id, 'lat'] = gps_option[0]
##    df_stores.loc[df_stores['store_id'] == store_id, 'lng'] = gps_option[1]

# Add gps in df_comp_pairs
for suffix in ['0', '1']:
  df_comp_pairs = pd.merge(df_comp_pairs,
                           df_stores[['id_lsa', 'lat', 'lng']],
                           left_on = ['id_lsa_{:s}'.format(suffix)],
                           right_on = ['id_lsa'],
                           how = 'left')
  df_comp_pairs['lat_{:s}'.format(suffix)] = df_comp_pairs['lat']
  df_comp_pairs['lng_{:s}'.format(suffix)] = df_comp_pairs['lng']
  df_comp_pairs.drop(['id_lsa', 'lat', 'lng'], axis = 1, inplace = True)

# #############################
# RECOMPUTE DIST WITH FIXED GPS
# #############################

## already done
#df_comp_pairs['dist'] = compute_distance_ar(df_comp_pairs['lec_lat'].values,
#                                            df_comp_pairs['lec_lng'].values,
#                                            df_comp_pairs['comp_lat'].values,
#                                            df_comp_pairs['comp_lng'].values)

## Suspicious dist (looks ok: only one which is actually very small)
#print(df_comp_pairs[df_comp_pairs['dist'] < 0.1].T)

# ###############################
# USE GOOGLE DIRECTION
# ###############################

# ls_res done once => no check if consistent with df_comp_pairs
path_res = os.path.join(path_built_201415_json,
                        'ls_comp_201415_directions.json')
if os.path.exists(path_res):
  ls_res = dec_json(path_res)
else:
  ls_res = []
  for row_i, row in df_comp_pairs.iterrows():
    ls_res.append(row[['id_lsa_0',
                       'id_lsa_1',
                       'lat_0',
                       'lng_0',
                       'lat_1',
                       'lng_1']].values.tolist() +\
                  [None])

# Query Google Direction for dist and duration
for i, res in enumerate(ls_res[0:2200]):
  if (not res[6]) or (res[6]['status'] == 'OVER_QUERY_LIMIT'):
    try:
      origin = ' '.join([str(x) for x in res[2:4]])
      destination = ' '.join([str(x) for x in res[4:6]])
      gg = get_google_direction(key_google_api,
                                origin,
                                destination)
    except:
      gg = None
      print u'Pbm with', ls_res[0:6]
    # over write list while looping: bof bof
    ls_res[i][6] = gg
enc_json(ls_res,
         os.path.join(path_built_201415_json,
                      'ls_comp_201415_directions.json'))

ls_rows_direction = []
for res in ls_res:
  if res[6] and res[6].get('routes'):
    dict_direction = res[6]['routes'][0]['legs'][0]
    ls_rows_direction.append((res[0],
                              res[1],
                              dict_direction['distance']['text'],
                              dict_direction['distance']['value'],
                              dict_direction['duration']['text'],
                              dict_direction['duration']['value']))

# Avoid bug upon df creation if ls_rows_direction is empty
if not ls_rows_direction:
  ls_rows_direction = None

df_direction = pd.DataFrame(ls_rows_direction,
                            columns = ['id_lsa_0',
                                       'id_lsa_1',
                                       'gg_dist_txt',
                                       'gg_dist_val',
                                       'gg_dur_txt',
                                       'gg_dur_val'])

df_comp_pairs = pd.merge(df_comp_pairs,
                         df_direction,
                         on = ['id_lsa_0', 'id_lsa_1'],
                         how = 'left')

df_comp_pairs['gg_dist_val'] = df_comp_pairs['gg_dist_val'] / 1000
df_comp_pairs['gg_dur_val'] = df_comp_pairs['gg_dur_val'] / 60

df_comp_pairs.to_csv(os.path.join(path_built_201415_csv,
                                  'df_comp_store_pairs_final.csv'),
                           encoding = 'UTF-8',
                           float_format='%.3f',
                           index = False)

# ##########
# STATS DES
# ##########

df_sub = df_comp_pairs[~df_comp_pairs['gg_dur_val'].isnull()]

print('Nb non null dur gg info', len(df_sub))

print('Stats des distance')
print(df_sub[['dist', 'gg_dist_val', 'gg_dur_val']].describe())

print('Corr distance proxies')
print(df_sub[['dist', 'gg_dist_val', 'gg_dur_val']].describe())

df_sub.plot(kind = 'scatter', x = 'dist', y = 'gg_dist_val')
plt.show()
