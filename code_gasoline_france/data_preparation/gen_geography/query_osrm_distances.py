#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
#from generic_master_info import *
#from generic_competition import *
#from functions_generic_qlmc import *
#from functions_geocoding import *
import os, sys
import pandas as pd
import matplotlib.pyplot as plt
import urllib2

# REQUIRES LOCAL OSRM SERVER

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

# ################
# RUN OSRM QUERIES
# ################

ls_res = []
for row_i, row in df_close_pairs.iterrows():
  ls_gps = list(row[['lat_1', 'lng_1', 'lat_2', 'lng_2']].values)
  query = 'http://localhost:5000/viaroute?'+\
          'loc={:f},{:f}&loc={:f},{:f}'.format(*ls_gps)
  try:
    # print query
    response = urllib2.urlopen(query)
    content = response.read()
    osrm_resp = json.loads(content)
    # pprint.pprint(osrm_resp)
    # print osrm_resp['route_summary']
    ls_res.append([row['id_1'], row['id_2'], osrm_resp['route_summary']])
  except:
    print('Query failed:', query)

# ######
# OUTPUT
# ######

#enc_json(ls_res,
#         os.path.join(path_dir_built_json,
#                      'ls_close_pairs_osrm.json'))
