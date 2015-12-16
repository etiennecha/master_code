#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built, u'data_json')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_built_zagaz = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_zagaz')
path_dir_built_zagaz_csv = os.path.join(path_dir_built_zagaz, 'data_csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DATA
# ##############

# INFO

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
                               'dpt' : str},
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

# MATCHING ZAGAZ

df_matching_0 = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                         'df_zagaz_stations_match_0.csv'),
                            dtype = {'zag_id' : str,
                                     'gov_id' : str,
                                     'ci' : str},
                            encoding = 'utf-8')

df_matching_1 = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                         'df_zagaz_stations_match_1.csv'),
                            dtype = {'zag_id' : str,
                                     'gov_id' : str,
                                     'ci' : str},
                            encoding = 'utf-8')

# ZAGAZ INFO

df_zagaz_info = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                         'df_zagaz_stations.csv'),
                            encoding='utf-8',
                            dtype = {'id_zagaz' : str,
                                     'zip' : str,
                                     'ci_1' : str,
                                     'ci_ardt_1' : str})
df_zagaz_info.set_index('id_zagaz', inplace = True)

# #################
# DF HIGHWAY GOV
# #################

df_hw_gov = df_info[df_info['highway'] == 1].copy()

lsdhwgov = ['name', 'adr_street', 'adr_city', 'ci_1', 'brand_0', 'brand_1']

print()
print(u'Overview of gov highway stations')
print(df_hw_gov[lsdhwgov][0:20].to_string())

print()
print(u'Overview of gov A1 stations')
print(df_hw_gov[df_hw_gov['adr_street'].str.contains('A\s?1(?:\s|$)')]\
               [lsdhwgov].to_string())

# #################
# DF HIGHWAY ZAGAZ
# #################

df_hw_zag = df_zagaz_info[~df_zagaz_info['highway'].isnull()].copy()

# Extract highway info
def format_highway(highway):
  res = re.search('Autoroute (.*?) - (.*?) \(km (.*?)\)', highway)
  return res.group(1), res.group(2), int(res.group(3))

df_hw_zag['hw_id'], df_hw_zag['hw_dir'], df_hw_zag['hw_km'] =\
    zip(*df_hw_zag['highway'].apply(lambda x: format_highway(x)))

lsdhw = ['hw_id', 'hw_dir', 'hw_km', 'name', 'municipality', 'ci',
         'zag_id', 'gov_id', 'brand_2013', 'gov_br_0', 'gov_br_1']

# Match zagaz w/ gov id (can result in duplicates: inspect and fix)
df_hw_zag = pd.merge(df_hw_zag,
                      df_matching_1[['zag_id', 'gov_id',
                                     'gov_street', 'gov_city',
                                     'gov_br_0', 'gov_br_1']],
                      left_index = True,
                      right_on = 'zag_id',
                      how = 'left')

print()
print(u'Inspect duplicates')
df_hw_zag['dup'] = df_hw_zag.groupby('zag_id')['zag_id'].transform(len)
print(df_hw_zag[df_hw_zag['dup'] > 1][lsdhw].to_string())

# Check highways
df_hw_zag.sort(['hw_id', 'hw_dir', 'hw_km'], ascending = True, inplace = True)
print()
print(u'Inspect highways')
print(df_hw_zag[df_hw_zag['hw_id'] == 'A1'][lsdhw].to_string())
