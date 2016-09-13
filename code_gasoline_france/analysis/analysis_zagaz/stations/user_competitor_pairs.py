#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import collections

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

# COMP

dict_comp_dtype = {'id_ta_{:d}'.format(i) : str for i in range(23)}
dict_comp_dtype['id_station'] = str
df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_comp.csv'),
                      dtype = dict_comp_dtype,
                      encoding = 'utf-8')
df_comp.set_index('id_station', inplace = True)

dict_close = dec_json(os.path.join(path_dir_built_json,
                                   'dict_ls_close.json'))

ls_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                          'ls_robust_stable_markets.json'))

# PRICE STATS DES

df_price_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_station_stats.csv'),
                               dtype = {'id_station' : str},
                               encoding = 'utf-8')
df_price_stats.set_index('id_station', inplace = True)

# MATCHING ZAGAZ

df_matching_zagaz = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                             'df_zagaz_matching_final.csv'),
                                dtype = {'id_station' : str,
                                         'zag_id' : str},
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
## temp for gps coord (todo: move)
#df_zagaz_info = df_zagaz_info[df_zagaz_info['lat'] != 'INDEPENDANT']
#df_zagaz_info['lat'] = df_zagaz_info['lat'].str.replace('-', '').astype(float)
#df_zagaz_info['lng'] = df_zagaz_info['lng'].str.replace('-', '').astype(float)

dict_types = {'SUP' : ['MOUSQUETAIRES',
                       'CARREFOUR',
                       'SYSTEME U',
                       'LECLERC', 
                       'AUCHAN',
                       'CASINO',
                       'CORA',
                       'COLRUYT'],
              'OIL': ['TOTAL',
                      'ESSO',
                      'BP',
                      'AGIP',
                      'SHELL'],
              'IND' : ['AVIA',
                       'DYNEFF']}

# df_zagaz_info[df_zagaz_info['group_2012'].isnull()]['brand_std_2012'].value_counts()
# df_zagaz_info[df_zagaz_info['group_2013'].isnull()]['brand_std_2013'].value_counts()
# todo: add IND and DIS (not all TA in 2013 but do the best...)

# todo: add type & investigate if pairs have same type (support segmentation?)
# todo: check by user: many reporting only SUP & DIS?
# pbm with TOTAL ACCESS... would require to check over time (but got ESSO EXPRESS?)

# ZAGAZ USER DATA

df_zagaz_users = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                          'df_zagaz_users_201404.csv'),
                             encoding = 'utf-8')

df_zagaz_reports = pd.read_csv(os.path.join(path_dir_built_zagaz_csv,
                                            'df_zagaz_price_reports_201404.csv'),
                               dtype = {'station' : str},
                               encoding = 'utf-8')

# ADD ZAGAZ INFO TO GOV INFO

df_matching_zagaz = pd.merge(df_matching_zagaz,
                             df_zagaz_info[['street',
                                            'municipality',
                                            'brand_std_2012',
                                            'brand_std_2013',
                                            'lat', 'lng']],
                             left_on = 'zag_id',
                             right_index = True,
                             how = 'left')

df_matching_zagaz.rename(columns = {'street' : 'zag_street',
                                    'municipality': 'zag_municipality',
                                    'brand_std_2012' : 'zag_brand_2012',
                                    'brand_std_2013' : 'zag_brand_2013',
                                    'lat' : 'zag_lat',
                                    'lng' : 'zag_lng'}, inplace = True)

lsdzm = ['id_station', 'zag_id',
         'zag_street', 'zag_municipality',
         'zag_brand_2012', 'zag_brand_2013',
         'zag_lat', 'zag_lng']

df_info = pd.merge(df_info,
                   df_matching_zagaz[lsdzm],
                   left_index = True,
                   right_on = 'id_station',
                   how = 'left')

df_info = df_info[df_info['highway'] != 1]

# #####################################
# GET STATION PAIRS FROM USER REPORTS
# ####################################

# Build dict: key = id_zagaz, content = list of stations w/ which station associated
# Frequency of reports per user not taken into account
# But id_zagaz appears as many times as users contribute to both stations
dict_station_relations = {}
for user, df_user_reports in df_zagaz_reports.groupby('user'):
  # consider each station reported by user (no control for frequency)
  ls_zagaz_ids = list(set(df_user_reports['station'].values))
  for i, zagaz_id in enumerate(ls_zagaz_ids):
    for zagaz_id_2 in ls_zagaz_ids[i+1:]:
      dict_station_relations.setdefault(zagaz_id, []).append(zagaz_id_2)
      dict_station_relations.setdefault(zagaz_id_2, []).append(zagaz_id)

# Count nb of users who contributed to both stations
dict_station_relations = {k : dict(Counter(v))\
                              for k,v in dict_station_relations.items()}

# Build dict pairs based on user contributions
temp_set_covered = set()
dict_pairs = {}
for zagaz_id, dict_relations in dict_station_relations.items():
  for zagaz_id_2, nb_users in dict_relations.items():
    if zagaz_id_2 not in temp_set_covered:
      dict_pairs.setdefault(nb_users, []).append((zagaz_id, zagaz_id_2))
  temp_set_covered.add(zagaz_id)

# #################
# BUILD DF PAIRS
# #################

# todo: distance? same brand? in gov data (some are highways)
#print df_zagaz_info.ix[['13372', '7255']].T.to_string()
#print df_matching_zagaz[df_matching_zagaz['zag_id'].isin(['13372', '7255'])].T.to_string()

# todo: loop and check those which involve a Total Access
# stats on price? would be better to use pre-existing pair stats
# those should take into account total access (in gen_dispersion?)

# Overview of pairs
ls_rows_pairs = []
for k, ls_pairs in dict_pairs.items():
  if k >= 2:
    for id_zagaz_1, id_zagaz_2 in ls_pairs:
      ls_rows_pairs.append((id_zagaz_1, id_zagaz_2, k))

df_pairs = pd.DataFrame(ls_rows_pairs,
                        columns = ['id_zag_1',
                                   'id_zag_2',
                                   'nb_users'])

ls_temp_cols = ['group_2012', 'group_2013',
                'street', 'municipality', 'ci',
                'lat', 'lng', 'highway']
for extension in [1, 2]:
  df_temp = df_zagaz_info[ls_temp_cols].copy()
  df_temp.columns = ['{:s}_{:d}'.format(x, extension) for x in df_temp.columns]
  df_pairs = pd.merge(df_pairs,
                      df_temp,
                      left_on = 'id_zag_{:d}'.format(extension),
                      right_index = True,
                      how = 'left')

# get rid of pairs involving highway
df_pairs = df_pairs[(df_pairs['highway_1'].isnull()) &\
                    (df_pairs['highway_2'].isnull())]
df_pairs.drop(['highway_1', 'highway_2'], axis = 1, inplace = True)

df_pairs['dist'] = compute_distance_ar(df_pairs['lat_1'],
                                       df_pairs['lng_1'],
                                       df_pairs['lat_2'],
                                       df_pairs['lng_2'])


print()
print(u'Overview pair distances:')
print(df_pairs['dist'].describe())

print()
print(u'Overview nb_users when dist > 30')
print(df_pairs[df_pairs['dist'] > 30]['nb_users'].value_counts())
#print()
#print(df_pairs[(df_pairs['dist'] > 30) &  (df_pairs['nb_users'] >= 10)].to_string())

# comp if not comp in 2012 nor in 2013
df_comp = df_pairs[~((df_pairs['group_2012_1'] == df_pairs['group_2012_2']) |
                     (df_pairs['group_2013_1'] == df_pairs['group_2013_2']))].copy()
# same if same group in 2012 and 2013
df_same = df_pairs[(df_pairs['group_2012_1'] == df_pairs['group_2012_2']) &
                   (df_pairs['group_2013_1'] == df_pairs['group_2013_2'])].copy()
# rest (check?)
df_rest = df_pairs[((df_pairs['group_2012_1'] == df_pairs['group_2012_2']) |
                    (df_pairs['group_2013_1'] == df_pairs['group_2013_2'])) &
                   (~((df_pairs['group_2012_1'] == df_pairs['group_2012_2']) &
                     (df_pairs['group_2013_1'] == df_pairs['group_2013_2'])))].copy()
                   
# ##############     
# STATS DES
# ##############

print()
print(u'Overview of pair distances:')

for nb_users in range(5, 11):
  print()
  print('Nb users required for comp:', nb_users)
  df_comp_temp = df_comp[df_comp['nb_users'] >= nb_users]
  print('Nb pairs:', len(df_comp_temp))
  
  min_dist, max_dist = 3, 5
  print('Less than {:d}: {:.0f}%'.format(\
           min_dist,
           len(df_comp_temp[df_comp_temp['dist'] <= min_dist]) /\
           float(len(df_comp_temp)) * 100))
  
  print('Between {:d} and {:d}: {:.0f}%'.format(\
           min_dist,
           max_dist,
           len(df_comp_temp[(df_comp_temp['dist'] > min_dist) &\
                            (df_comp_temp['dist'] <= max_dist)]) /\
           float(len(df_comp_temp))* 100))
  
  print('Above {:d}: {:.0f}%'.format(\
           max_dist,
           len(df_comp_temp[df_comp_temp['dist'] > max_dist]) /\
           float(len(df_comp_temp)) * 100))

## Play with networkx
#import networkx as nx
#g = nx.Graph()
#g.add_edges_from(df_comp[['id_zag_1', 'id_zag_2']].values.tolist())
## find (connected) subgraphs
#d = nx.connected_component_subgraphs(g)
#for sg in d[0:10]:
#  print(len(sg.nodes()))
