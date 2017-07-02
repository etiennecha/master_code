#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import *
from functions_generic_qlmc import *
from functions_geocoding import *
import os, sys
import json
import re
import pandas as pd

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2015')
path_built_csv = os.path.join(path_built, 'data_csv_201503')
path_built_json = os.path.join(path_built, 'data_json')

path_lsa_csv = os.path.join(path_data,
                            'data_supermarkets',
                            'data_built',
                            'data_lsa',
                            'data_csv')

path_api_keys = os.path.join(path_data, 'api_keys')
with open(os.path.join(path_api_keys, 'key_google_api.txt'), 'r') as f:
  key_google_api = f.read()

# ##########
# LOAD DATA
# ##########

# Need to have build df_qlmc_competitors already
# Need to have df_stores including lsa_id (best gps coordinates)

df_qlmc_competitors = pd.read_csv(os.path.join(path_built_csv,
                                               'df_qlmc_competitors.csv'),
                                  encoding = 'utf-8')

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                    'df_stores_final.csv'),
                        dtype = {'id_lsa' : str},
                        encoding = 'utf-8')

df_lsa = pd.read_csv(os.path.join(path_lsa_csv,
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

df_stores = pd.merge(df_stores,
                     df_lsa[['id_lsa', 'longitude', 'latitude', 'region']],
                     on = ['id_lsa'],
                     how = 'left')

# Choose preferred gps
# Default to LSA (best quality)
df_stores['lat'] = df_stores['latitude']
df_stores['lng'] = df_stores['longitude']
# If no data from LSA: QLMC
df_stores.loc[df_stores['lat'].isnull(), 'lat'] = df_stores['store_lat']
df_stores.loc[df_stores['lng'].isnull(), 'lng'] = df_stores['store_lng']
# Ad hoc changes
ls_final_gps = [['casino-prunelli-di-fiumorbo', 'qlmc'], # 4 and bad
                ['carrefour-market-beaumont-le-roger', 'lsa'],
                ['carrefour-market-anse', (45.9380, 4.7201)], # 2 and bad
                ['super-u-saint-brevin-les-pins', 'lsa'],
                ['centre-e-leclerc-oletta', 'lsa'],
                ['leclerc-express-borgo', 'lsa'],
                ['casino-rivieres', (45.7463, 0.3830)], # 3 and bad
                ['u-express-bagnoles-de-l-orne', 'qlmc'], # 4 and bad
                ['casino-estancarbon', 'lsa'],
                ['intermarche-super-surgeres', 'lsa'],
                ['centre-e-leclerc-joue-les-tours', 'lsa'],
                ['carrefour-market-aussonne', 'lsa'], # check (resumed activity?)
                ['carrefour-market-vauvert', 'qlmc']] # 3 and bad
for store_id, gps_option in ls_final_gps:
  if gps_option == 'qlmc':
    for coord, source_coord in [['lat', 'store_lat'],
                                ['lng', 'store_lng']]:
      df_stores.loc[df_stores['store_id'] == store_id, coord] = (
        df_stores.loc[df_stores['store_id'] == store_id, source_coord])
  elif isinstance(gps_option, tuple):
    df_stores.loc[df_stores['store_id'] == store_id, 'lat'] = gps_option[0]
    df_stores.loc[df_stores['store_id'] == store_id, 'lng'] = gps_option[1]

# Add gps in df_qlmc_competitors
for prefix in ['lec', 'comp']:
  df_qlmc_competitors = pd.merge(df_qlmc_competitors,
                                 df_stores[['store_id', 'lat', 'lng']],
                                 left_on = ['{:s}_id'.format(prefix)],
                                 right_on = ['store_id'],
                                 how = 'left')
  df_qlmc_competitors['{:s}_lat'.format(prefix)] = df_qlmc_competitors['lat']
  df_qlmc_competitors['{:s}_lng'.format(prefix)] = df_qlmc_competitors['lng']
  df_qlmc_competitors.drop(['store_id', 'lat', 'lng'], axis = 1, inplace = True)

# #############################
# RECOMPUTE DIST WITH FIXED GPS
# #############################

df_qlmc_competitors['dist'] = compute_distance_ar(df_qlmc_competitors['lec_lat'].values,
                                                  df_qlmc_competitors['lec_lng'].values,
                                                  df_qlmc_competitors['comp_lat'].values,
                                                  df_qlmc_competitors['comp_lng'].values)

## Suspicious dist (looks ok: only one which is actually very small)
#print df_qlmc_competitors[df_qlmc_competitors['dist'] < 0.1].T

### Overview
#df_lec_dist = df_qlmc_competitors[['lec_id', 'dist']].groupby('lec_id')\
#                                                     .describe()['dist'].unstack()
#print(df_lec_dist.describe())
#print(df_lec_dist[df_lec_dist['min'] > 19])

# ###############################
# USE GOOGLE DIRECTION
# ###############################

# todo: add previously done to df_qlmc_competitors
# and loop only on those not done yet

path_res = os.path.join(path_built_json, 'ls_qlmc_competitors_directions.json')
if os.path.exists(path_res):
  ls_res = dec_json(path_res)
else:
  ls_res = []
  for row_i, row in df_qlmc_competitors.iterrows():
    ls_res.append(row[['lec_id',
                       'comp_id',
                       'lec_lat',
                       'lec_lng',
                       'comp_lat',
                       'comp_lng']].values.tolist() + [None])

## Query Google Direction for dist and duration
#for i, res in enumerate(ls_res):
#  if (not res) or (res[6]['status'] == 'OVER_QUERY_LIMIT'):
#    try:
#      origin = ' '.join([str(x) for x in res[2:4]])
#      destination = ' '.join([str(x) for x in res[4:6]])
#      gg = get_google_direction(key_google_api,
#                                origin,
#                                destination)
#    except:
#      gg = None
#      print(u'Pbm with', ls_res[0:6])
#    # over write list while looping: bof bof
#    ls_res[i][6] = gg
#enc_json(ls_res,
#         os.path.join(path_built_json,
#                      'ls_qlmc_competitors_directions.json'))

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

df_direction = pd.DataFrame(ls_rows_direction,
                            columns = ['lec_id',
                                       'comp_id',
                                       'gg_dist_txt',
                                       'gg_dist_val',
                                       'gg_dur_txt',
                                       'gg_dur_val'])

df_qlmc_competitors = pd.merge(df_qlmc_competitors,
                               df_direction,
                               on = ['lec_id', 'comp_id'],
                               how = 'left')

df_qlmc_competitors['gg_dist_val'] = df_qlmc_competitors['gg_dist_val'] / 1000
df_qlmc_competitors['gg_dur_val'] = df_qlmc_competitors['gg_dur_val'] / 60

df_qlmc_competitors.to_csv(os.path.join(path_built_csv,
                                        'df_qlmc_competitors_final.csv'),
                           encoding = 'UTF-8',
                           float_format='%.3f',
                           index = False)

# ##########
# STATS DES
# ##########

# Add region in df_qlmc_competitors
df_qlmc_competitors = pd.merge(df_qlmc_competitors,
                               df_stores[['store_id', 'region']],
                               left_on = ['lec_id'],
                               right_on = ['store_id'],
                               how = 'left')
df_qlmc_competitors.drop(['store_id'], axis = 1, inplace = True)

for var in ['dist', 'gg_dist_val', 'gg_dur_val']:
  df_lec_dist = (df_qlmc_competitors[['region', 'lec_id', var]]
                                    .groupby(['region', 'lec_id'])
                                    .describe()[var].unstack())
  df_lec_dist.reset_index(inplace = True, drop = False)
  df_lec_reg = df_lec_dist.groupby('region').agg('mean')
  df_lec_reg['nb_lec'] = df_lec_dist.groupby('region').agg(len)['lec_id']
  print()
  print('Avg dist distribution (by store) for', var)
  print(df_lec_reg.to_string())
  
  # Distribution of max distances
  se_lec_dist_max = (df_qlmc_competitors[['region', 'lec_id', var]]
                                        .groupby(['region', 'lec_id'])
                                        .agg(max)[var])
  df_lec_dist_max = se_lec_dist_max.to_frame()
  df_lec_dist_max.reset_index(drop = False, inplace = True)
  df_lec_reg_max = (df_lec_dist_max[['region', var]].groupby('region')
                                                    .describe()[var].unstack())
  print()
  print('Avg max dist distribution (by store) for', var)
  print(df_lec_reg_max.to_string())
