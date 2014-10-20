#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
import pprint

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

path_dir_match_insee = os.path.join(path_data, u'data_insee', 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_data, u'data_insee', 'data_extracts')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_csv_rls = os.path.join(path_dir_source, 'data_other', 'data_rls.csv')
path_dir_gps_coordinates = os.path.join(path_dir_source, 'data_stations', 'data_gouv_gps')
ls_dict_gouv_gps_file_names = ['20130117_ls_coordinates_essence.json',
                               '20130117_ls_coordinates_diesel.json',
                               '20130724_ls_coordinates_essence.json',
                               '20130724_ls_coordinates_diesel.json'] 

# ######################
# LOAD GAS STATION DATA
# ######################

master_price_raw = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel_raw.json'))
master_price = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel.json'))
master_info_raw = dec_json(os.path.join(path_dir_built_json, 'master_info_diesel_raw.json'))
master_info = dec_json(os.path.join(path_dir_built_json, 'master_info_diesel.json'))

# BUILD master_addresses (addresses corrected for html pbms and somewhat stdized
dict_addresses = {indiv_id: [indiv_info['address'][i]\
                               for i in (5, 3, 4, 0) if indiv_info['address'][i]]\
                    for (indiv_id, indiv_info) in master_info_raw.items()}
master_addresses = build_master_addresses(dict_addresses)
master_addresses['15400003'] = [(u'zone industrielle du sedour', u'15400 riom-\xc8s-montagnes')]
master_addresses['76170004'] = [(u'autoroute a 29', u'76210 bolleville')]

# ########################################
# GAS STATIONS GPS COORDINATES (FROM GOUV)
# ########################################

# Load gps collected from prix-carburant.gouv.fr
ls_dict_gouv_gps = [dec_json(os.path.join(path_dir_gps_coordinates, gps_file))\
                      for gps_file in ls_dict_gouv_gps_file_names]
dict_20130117 = ls_dict_gouv_gps[0]
dict_20130117.update(ls_dict_gouv_gps[1])
dict_20130724 = ls_dict_gouv_gps[2]
dict_20130724.update(ls_dict_gouv_gps[3])
ls_index, ls_rows_gps = [], []
for indiv_id in master_info_raw.keys():
  ls_index.append(indiv_id)
  ls_gps_gouv_0 = dict_20130117.get(indiv_id, [np.nan, np.nan])
  ls_gps_gouv_1 = dict_20130724.get(indiv_id, [np.nan, np.nan])
  ls_rows_gps.append(ls_gps_gouv_0 + ls_gps_gouv_1)
df_gps = pd.DataFrame(ls_rows_gps,
                      index = ls_index,
                      columns = ['gps_lat_gov_0',
                                 'gps_lng_gov_0',
                                 'gps_lat_gov_1',
                                 'gps_lng_gov_1'])

# Load gps provided by Ronan (from prix-carburant.gouv.fr but older)
df_rls = pd.read_csv(path_csv_rls, dtype = {'idpdv' : str})
df_rls.set_index('idpdv', inplace = True)

# Get final df_gps
df_gps = pd.merge(df_gps, df_rls[['latDeg', 'longDeg']],
                       left_index = True, right_index = True, how = 'left')
df_gps.rename(columns = {'latDeg' : 'gps_lat_rls',
                         'longDeg' : 'gps_lng_rls'}, inplace = True)
df_gps = df_gps.apply(lambda x: np.round(x, 3))

# #######################
# GAS STATIONS ON HIGHWAY
# #######################

set_highway_ids = set()
for indiv_id, ls_addresses in master_addresses.items():
  for address in ls_addresses:
    if 'autoroute' in address[0] or\
       re.search('(^|\s|-)a\s?[0-9]{1,3}($|\s|-|,)', address[0]) or\
       master_info_raw[indiv_id]['highway'][3] == 1:
      set_highway_ids.add(indiv_id)
ls_mistakes_highway = ['93130007', '75017016', '56190007', '68127001', '7580002']
ls_highway_indiv_ids = [indiv_id for indiv_id in list(set_highway_ids)\
                          if indiv_id not in ls_mistakes_highway]
# for indiv_id in list(set_highway_ids):
  # if indiv_id in master_price['dict_info'].keys():
    # print indiv_id, master_price['dict_info'][indiv_id]['name'], master_addresses[indiv_id]
# # excluded: 93130007 (address incl. 'chasse a 3'), 75017016 ('6 a 8'),  56190007 (dummy 1), 
# # excluded: 68127001 ('pres sortie...'), 7580002 (dummy 1, RN)
ls_index = master_info_raw.keys()
ls_rows_highway = [1 if indiv_id in ls_highway_indiv_ids else 0\
                     for indiv_id in master_info_raw.keys()]
se_highway = pd.Series(ls_rows_highway, index = ls_index, name = 'highway')

# ######################
# GAS STATIONS AMENITIES
# ######################

# Explore services in each period
ls_ls_period_services = [[service for indiv_id, indiv_info in master_info_raw.items()\
                          if indiv_info['services'][i] for service in indiv_info['services'][i]]\
                            for i in range(len(master_info_raw[master_info.keys()[0]]['services']))]
ls_ls_period_services = [list(set(ls_per_services)) for ls_per_services in ls_ls_period_services]
for i, ls_period_services in enumerate(ls_ls_period_services[1:], start = 1):
  for service in ls_period_services:
    if service not in ls_ls_period_services[i-1]:
      print 'New service in', i, ':', service

# todo: check intra station differences
# put all periods together?

# Keep only last period amenities in df for now
ls_all_services = [service for indiv_id, indiv_info in master_info_raw.items()\
                    if indiv_info['services'][-1] for service in indiv_info['services'][-1]]
ls_unique_services = list(set(ls_all_services))

ls_index, ls_rows_services = [], []
for indiv_id, indiv_info in master_info_raw.items():
  ls_index.append(indiv_id)
  # Caution [] and None are false but different here
  if indiv_info['services'][-1] is not None:
    ls_services = [0 for i in ls_unique_services]
    for service in indiv_info['services'][-1]:
      service_ind = ls_unique_services.index(service)
      ls_services[service_ind] = 1
  else:
    ls_services = [None for i in ls_unique_services]
  ls_rows_services.append(ls_services)

df_services = pd.DataFrame(ls_rows_services,
                           index = ls_index,
                           columns = ls_unique_services)

# #######################
# OPENING DAYS and HOURS
# #######################

# closed_days: not much heterogeneity: correlation with 24/24h?
# roughly c.2,000 stations are closed at least one day, c. 1,600 on Sunday (only)
# 72 are supposed to be closed everyday (4th per) => no price... what happens?
# maybe sometimes opening days were mistaken for closed days
# TODO: check closed Sunday and closed every day (or so)
# hours: roughly half 24/24h... otherwise large number of occurences, not much interest
# TODO: check open 24/24h (equivalent to ATM?)

# High heterogeneity in set of services offered
# Services: pbm, can't know if it really changes or info is improved/corrected...
# Date of change unknown so kinda impossible to check an effect... (rather would come from price)
# TODO: check most standard service patterns... scarce services ... brand specificities...

ls_index, ls_rows_opening = [], []
for indiv_id, indiv_info in master_info_raw.items():
  ls_index.append(indiv_id)
  # Caution [] and None are false but different here
  ls_rows_opening.append([indiv_info['closed_days'][2],
                          indiv_info['hours'][2],
                          indiv_info['closed_days'][5],
                          indiv_info['hours'][5]])

df_opening = pd.DataFrame(ls_rows_opening,
                          index = ls_index,
                          columns = ['closed_days_f',
                                     'hours_f',
                                     'closed_days_l',
                                     'hours_l'])

# Check differences over time

print len(df_opening[df_opening['hours_f'] != df_opening['hours_l']])

# Only 15 have changes (opened all days even before credit cards...)
print len(df_opening[(~pd.isnull(df_opening['closed_days_f'])) &
                     (~pd.isnull(df_opening['closed_days_l'])) &
                     (df_opening['closed_days_f'] != df_opening['closed_days_l'])])

print df_opening[(~pd.isnull(df_opening['closed_days_f'])) &
                 (~pd.isnull(df_opening['closed_days_l'])) &
                 (df_opening['closed_days_f'] != df_opening['closed_days_l'])][0:100].to_string()

# Quite a few changes:
# see earlier opening hours (winter /summer?)
# also move to 24h/24h: check if Total Acces / Esso express (credit cards)

print len(df_opening[(~pd.isnull(df_opening['hours_f'])) &
                     (~pd.isnull(df_opening['hours_l'])) &
                     (df_opening['hours_f'] != df_opening['hours_l'])])

print df_opening[(~pd.isnull(df_opening['hours_f'])) &
                 (~pd.isnull(df_opening['hours_l'])) &
                 (df_opening['hours_f'] != df_opening['hours_l'])][0:100].to_string()

# ####################
# BUILD DF CHARS
# ####################

df_chars = pd.merge(df_gps, df_services, left_index = True, right_index = True)
df_chars = pd.merge(df_chars, df_opening, left_index = True, right_index = True)
df_chars['highway'] = se_highway
