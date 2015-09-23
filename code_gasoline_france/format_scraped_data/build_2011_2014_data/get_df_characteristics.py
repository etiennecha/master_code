#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
import pprint

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_scraped_2011_2014')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_csv_rls = os.path.join(path_dir_source, 'data_other', 'data_rls.csv')
path_dir_gps_coordinates = os.path.join(path_dir_source, 'data_stations', 'data_gouv_gps')
ls_dict_gouv_gps_file_names = ['20130117_dict_gps_essence.json',
                               '20130117_dict_gps_diesel.json',
                               '20130724_dict_gps_essence.json',
                               '20130724_dict_gps_diesel.json',
                               '20131115_dict_gps_essence.json',
                               '20131115_dict_gps_diesel.json',
                               '20141206_dict_gps_essence.json',
                               '20141206_dict_gps_diesel.json']

# ######################
# LOAD GAS STATION DATA
# ######################

#master_price_raw = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel_raw.json'))
#master_info_raw = dec_json(os.path.join(path_dir_built_json, 'master_info_raw.json'))

master_price = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel_fixed.json'))
master_info = dec_json(os.path.join(path_dir_built_json, 'master_info_fixed.json'))

# BUILD master_addresses (addresses corrected for html pbms and somewhat stdized
dict_addresses = {indiv_id: [indiv_info['address'][i]\
                               for i in (8, 7, 6, 5, 3, 4, 0) if indiv_info['address'][i]]\
                    for (indiv_id, indiv_info) in master_info.items()}
master_addresses = build_master_addresses(dict_addresses)

# ########################################
# GAS STATIONS GPS COORDINATES (FROM GOUV)
# ########################################

# Load gps collected from prix-carburant.gouv.fr
ls_dict_gouv_gps = [dec_json(os.path.join(path_dir_gps_coordinates, gps_file))\
                      for gps_file in ls_dict_gouv_gps_file_names]

dict_gps = {}
for dict_gouv_gps in ls_dict_gouv_gps:
  for id_gouv, gps in dict_gouv_gps.items():
    if gps not in dict_gps.get(id_gouv, []):
      dict_gps.setdefault(id_gouv,[]).append(gps)

dict_gps_len = {}
for id_gouv, ls_gps in dict_gps.items():
	dict_gps_len.setdefault(len(ls_gps), []).append(id_gouv)

ls_columns_gps = []
for i in range(max(dict_gps_len.keys())):
  ls_columns_gps += ['lat_gov_%s' %i, 'lng_gov_%s' %i]

ls_index_gps, ls_rows_gps = [], []
for id_gouv in master_info.keys():
  ls_index_gps.append(id_gouv)
  ls_rows_gps.append([x for ls_x in dict_gps.get(id_gouv, []) for x in ls_x])
df_gps = pd.DataFrame(ls_rows_gps, index = ls_index_gps, columns = ls_columns_gps)
df_gps = df_gps.astype(float)

# Load gps provided by Ronan (from prix-carburant.gouv.fr but older)
df_rls = pd.read_csv(path_csv_rls, dtype = {'idpdv' : str})
df_rls.set_index('idpdv', inplace = True)

# Get final df_gps
df_gps = pd.merge(df_gps, df_rls[['latDeg', 'longDeg']],
                       left_index = True, right_index = True, how = 'left')
df_gps.rename(columns = {'latDeg' : 'lat_rls',
                         'longDeg' : 'lng_rls'}, inplace = True)
df_gps = df_gps.apply(lambda x: np.round(x, 3))

# #######################
# GAS STATIONS ON HIGHWAY
# #######################

ls_gouv_highway_ids = dec_json(os.path.join(path_dir_source,
                                            u'data_stations',
                                            u'data_gouv_highway',
                                            u'20141206_ls_highway_ids.json'))

set_highway_ids = set()
for indiv_id, ls_addresses in master_addresses.items():
  for address in ls_addresses:
    if 'autoroute' in address[0] or\
       re.search('(^|\s|-)a\s?[0-9]{1,3}($|\s|-|,)', address[0]) or\
       any([x == 1 for x in master_info[indiv_id]['highway']]) or\
       indiv_id in ls_gouv_highway_ids:
      set_highway_ids.add(indiv_id)
ls_mistakes_highway = ['93130007', '75017016', '56190007', '68127001', '7580002']
ls_highway_ids = [indiv_id for indiv_id in list(set_highway_ids)\
                          if indiv_id not in ls_mistakes_highway]
# for indiv_id in list(set_highway_ids):
  # if indiv_id in master_price['dict_info'].keys():
    # print indiv_id, master_price['dict_info'][indiv_id]['name'], master_addresses[indiv_id]
# # excluded: 93130007 (address incl. 'chasse a 3'), 75017016 ('6 a 8'),  56190007 (dummy 1), 
# # excluded: 68127001 ('pres sortie...'), 7580002 (dummy 1, RN)
ls_index = master_info.keys()
ls_rows_highway = [1 if indiv_id in ls_highway_ids else 0\
                     for indiv_id in master_info.keys()]
se_highway = pd.Series(ls_rows_highway, index = ls_index, name = 'highway')

# ######################
# GAS STATIONS AMENITIES
# ######################

# Explore services in each period
ls_ls_period_services = [[service for indiv_id, indiv_info in master_info.items()\
                          if indiv_info['services'][i] for service in indiv_info['services'][i]]\
                            for i in range(len(master_info[master_info.keys()[0]]['services']))]
ls_ls_period_services = [list(set(ls_per_services)) for ls_per_services in ls_ls_period_services]
for i, ls_period_services in enumerate(ls_ls_period_services[1:], start = 1):
  for service in ls_period_services:
    if service not in ls_ls_period_services[i-1]:
      print 'New service in', i, ':', service

# todo: check intra station differences
# put all periods together?

# Keep only last period amenities in df for now
ls_all_services = [service for indiv_id, indiv_info in master_info.items()\
                    if indiv_info['services'][-1] for service in indiv_info['services'][-1]]
ls_unique_services = list(set(ls_all_services))

ls_index, ls_rows_services = [], []
for indiv_id, indiv_info in master_info.items():
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
# todo: should set service to None if was not recorded at info period

# #######################
# OPENING DAYS and HOURS
# #######################

# closed_days: not much heterogeneity: correlation with 24/24h?
# roughly c.2,000 stations are closed at least one day, c. 1,600 on Sunday (only)
# 72 are supposed to be closed everyday (4th per) => no price... what happens?
# maybe sometimes opening days were mistaken for closed days
# todo: check closed Sunday and closed every day (or so)
# hours: roughly half 24/24h... otherwise large number of occurences, not much interest
# todo: check open 24/24h (equivalent to ATM?)

# High heterogeneity in set of services offered
# Services: pbm, can't know if it really changes or info is improved/corrected...
# Date of change unknown so kinda impossible to check an effect... (rather would come from price)
# todo: check most standard service patterns... scarce services ... brand specificities...

ls_index, ls_rows_opening = [], []
for indiv_id, indiv_info in master_info.items():
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

print u'\nNb chges in days (all):',\
      len(df_opening[df_opening['closed_days_f'] != df_opening['closed_days_l']])

# Only 15 have changes (opened all days even before credit cards...)
print u'Nb chges in days (non null):',\
      len(df_opening[(~pd.isnull(df_opening['closed_days_f'])) &
                     (~pd.isnull(df_opening['closed_days_l'])) &
                     (df_opening['closed_days_f'] != df_opening['closed_days_l'])])

print u'Extract: chge in days (non null):'
print df_opening[(~pd.isnull(df_opening['closed_days_f'])) &
                 (~pd.isnull(df_opening['closed_days_l'])) &
                 (df_opening['closed_days_f'] != df_opening['closed_days_l'])][0:20].to_string()

# Quite a few changes:
# see earlier opening hours (winter /summer?)
# also move to 24h/24h: check if Total Acces / Esso express (credit cards)

print u'\nNb chges in hours (all):',\
      len(df_opening[df_opening['hours_f'] != df_opening['hours_l']])

print u'Nb chges in hours (non null):',\
      len(df_opening[(~pd.isnull(df_opening['hours_f'])) &
                     (~pd.isnull(df_opening['hours_l'])) &
                     (df_opening['hours_f'] != df_opening['hours_l'])])

print u'Extract: chge in hours (non null):'
print df_opening[(~pd.isnull(df_opening['hours_f'])) &
                 (~pd.isnull(df_opening['hours_l'])) &
                 (df_opening['hours_f'] != df_opening['hours_l'])][0:20].to_string()

# ###########################
# STATION LATEST ADR AND NAME
# ###########################

ls_index, ls_rows_name_adr = [], []
for indiv_id, indiv_info in master_info.items():
  ls_index.append(indiv_id)
  res_name = get_latest_info(indiv_id, 'name', master_info, non_null = True)
  if type(res_name) == list:
    res_name = res_name[0]
  res_adr = get_latest_info(indiv_id, 'address', master_info, non_null = True)
  if (not res_adr) or (len(res_adr) != 2):
    res_adr = [None, None]
  ls_rows_name_adr.append([res_name] + res_adr)

df_name_adr = pd.DataFrame(ls_rows_name_adr,
                          index = ls_index,
                          columns = ['name', 'adr_street', 'zip_city'])

for field in ['name', 'adr_street', 'zip_city']:
  df_name_adr[field] = df_name_adr[field].apply(lambda x: str_correct_html(x) if x else x)

print u'\nNb with no address', len(df_name_adr[pd.isnull(df_name_adr['adr_street']) &\
                                               pd.isnull(df_name_adr['zip_city'])])

# Get zip, dpt, city
pat_zip = u"([0-9]?[0-9AB][0-9]{3})\s"
df_name_adr['adr_zip'] = df_name_adr['zip_city'].apply(\
                          lambda x: re.match(pat_zip, x).group(1) if x else x)

df_name_adr['adr_dpt'] = None
df_name_adr['adr_dpt'][~pd.isnull(df_name_adr['adr_zip'])] =\
   df_name_adr['adr_zip'][~pd.isnull(df_name_adr['adr_zip'])].str.slice(stop = -3)

# normally no need to allow for A or B (code insee only)
pat_city = "[0-9]?[0-9AB][0-9]{3}\s(.*)"
df_name_adr['adr_city'] = df_name_adr['zip_city'].apply(\
                           lambda x: re.match(pat_city, x).group(1).\
                                       replace('CEDEX', '').strip() if x else x)

df_name_adr = df_name_adr[['name', 'adr_street', 'adr_zip', 'adr_city', 'adr_dpt']]

# ####################
# BUILD DF CHARS
# ####################

df_chars = pd.merge(df_name_adr, df_gps, left_index = True, right_index = True)
df_chars = pd.merge(df_chars, df_services, left_index = True, right_index = True)
df_chars = pd.merge(df_chars, df_opening, left_index = True, right_index = True)
df_chars['highway'] = se_highway

# OUTPUT TO CSV
df_chars.to_csv(os.path.join(path_dir_built_csv,
                             'df_chars.csv'),
                         index_label = 'id_station',
                         float_format= '%.3f',
                         encoding = 'utf-8')

# print df_chars[['name', 'adr_street', 'adr_zip', 'adr_city', 'adr_dpt']].to_string()
