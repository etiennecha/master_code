#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
from functions_geocoding import *
import matplotlib.pyplot as plt
import urllib2

path_data_ubuntu = '/home/etna/Etienne/sf_Data'
if not os.path.exists(path_data):
  # to be run with ubuntu (local osrm server)
  path_data = path_data_ubuntu

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built, u'data_json')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_api_keys = os.path.join(path_data, 'api_keys')
with open(os.path.join(path_api_keys, 'key_google_api.txt'), 'r') as f:
  key_google_api = f.read()

# ###########
# LOAD DATA
# ###########

# DF INFO
df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str})
df_info.set_index('id_station', inplace = True)

## DF STATION STATS
#df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
#                                            'df_station_stats.csv'),
#                               encoding = 'utf-8',
#                               dtype = {'id_station' : str})
#df_station_stats.set_index('id_station', inplace = True)
#
## DF MARGIN CHGE
#df_margin_chge = pd.read_csv(os.path.join(path_dir_built_csv,
#                                          'df_margin_chge.csv'),
#                               encoding = 'utf-8',
#                               dtype = {'id_station' : str})
#df_margin_chge.set_index('id_station', inplace = True)


# CLOSE PAIRS
ls_close_pairs = dec_json(os.path.join(path_dir_built_json,
                                       'ls_close_pairs.json'))

# DF CLOSE PAIRS
df_close_pairs = pd.DataFrame(ls_close_pairs,
                              columns = ['id_1', 'id_2', 'dist'])

for i in range(1, 3):
  df_close_pairs = pd.merge(df_close_pairs,
                            df_info[['lat', 'lng']],
                            left_on = 'id_{:d}'.format(i),
                            right_index = True)
  df_close_pairs.rename(columns =  {x : u'{:s}_{:d}'.format(x, i)\
                                        for x in ['lat', 'lng']},
                        inplace = True)

ls_osrm_res = dec_json(os.path.join(path_dir_built_json,
                                    'ls_close_pairs_osrm.json'))

ls_osrm_dist = [[x[0], x[1], x[2]['total_distance'], x[2]['total_time']]\
                  for x in ls_osrm_res]

df_osrm = pd.DataFrame(ls_osrm_dist, columns = ['id_1',
                                                'id_2',
                                                'osrm_dist',
                                                'osrm_time'])

df_pairs = pd.merge(df_close_pairs,
                    df_osrm,
                    on = ['id_1', 'id_2'],
                    how = 'left')

df_pairs['osrm_time'] = df_pairs['osrm_time'] / 60.0 # sec to minutes
df_pairs['osrm_dist'] = df_pairs['osrm_dist'] / 1000.0 # m to km

print()
print(df_pairs[~df_pairs['osrm_dist'].isnull()]\
              [['dist', 'osrm_dist', 'osrm_time']].describe())

print()
print(df_pairs[['dist', 'osrm_dist', 'osrm_time']].describe())

# INSPECT POINTS FOR WHICH ROUTING ALWAYS FAILS

print()
for x, y in df_pairs[df_pairs['osrm_dist'].isnull()]['id_1'].value_counts()[0:10].iteritems():
  print(u"{:s} {:3d} ".format(x, y) +\
        u"{:3.3f} {:6.3f}".format(*df_info.ix[x][['lat', 'lng']].values))

## very large osrm_dist/time... vs short dist (ok: mountain, water...)
#print(len(df_pairs[(df_pairs['osrm_time'] >= 20)]))
#print(df_pairs[(df_pairs['osrm_time'] >= 20) &\
#               (df_pairs['dist'] <= 4)].to_string())

# SUPPLEMENT WITH GOOGLE DISTANCES

## one pass is enough
#ls_gg_res = []
#for row_i, row in df_pairs[df_pairs['osrm_dist'].isnull()].iterrows():
#  try:
#    origin = ' '.join([str(x) for x in row[['lat_1', 'lng_1']].values])
#    destination = ' '.join([str(x) for x in row[['lat_2', 'lng_2']].values])
#    gg = get_google_direction(key_google_api,
#                              origin,
#                              destination)
#  except:
#    gg = None
#    print(u'Pbm with', row)
#  # over write list while looping: bof bof
#  ls_gg_res.append([row['id_1'], row['id_2'], gg])
#
#enc_json(ls_gg_res,
#         os.path.join(path_dir_built_json,
#                      'ls_close_pairs_gg.json'))

ls_gg_res = dec_json(os.path.join(path_dir_built_json,
                                  'ls_close_pairs_gg.json'))

ls_gg_dist = []
for id_1, id_2, gg_res in ls_gg_res:
  if gg_res and gg_res.get('routes'):
    dict_direction = gg_res['routes'][0]['legs'][0]
    ls_gg_dist.append([id_1,
                       id_2,
                       dict_direction['distance']['value'] / 1000.0,
                       dict_direction['duration']['value'] /60.0])

df_gg = pd.DataFrame(ls_gg_dist,
                     columns = ['id_1', 'id_2', 'gg_dist', 'gg_time'])

df_dist = pd.merge(df_pairs,
                   df_gg,
                   on = ['id_1', 'id_2'],
                   how = 'left')

# overwrite osrm_dist and osrm_time

for var_dist in ['dist', 'time']:
  df_dist.loc[df_dist['osrm_{:s}'.format(var_dist)].isnull(),
              'osrm_{:s}'.format(var_dist)] = df_dist['gg_{:s}'.format(var_dist)]

print(df_dist.describe().to_string())

df_dist.drop(['gg_dist', 'gg_time'], axis = 1, inplace = True)

# #########
# OUTPUT
# #########

df_dist.to_csv(os.path.join(path_dir_built_csv,
                            'df_pair_distance.csv'),
               encoding = 'utf-8',
               float_format = '%.3f',
               index = False)
