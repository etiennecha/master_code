#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv') 

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

# #####################
# IMPORT INSEE DATA
# #####################

pd_df_insee = pd.read_csv(path_csv_insee_data, encoding = 'utf-8', dtype= str)
# excludes dom tom
pd_df_insee = pd_df_insee[~pd_df_insee[u'Département - Commune CODGEO'].str.contains('^97')]
pd_df_insee['Population municipale 2007 POP_MUN_2007'] = \
  pd_df_insee['Population municipale 2007 POP_MUN_2007'].apply(lambda x: float(x))

# #####################
# MARKET DEFINITIONS
# #####################

pd_df_insee['id_code_geo'] = pd_df_insee[u'Département - Commune CODGEO']
pd_df_insee = pd_df_insee.set_index('id_code_geo')
dict_markets_insee = {}
dict_markets_au = {}
dict_markets_uu = {}
# some stations don't have code_geo (short spells which are not in master_info)
for id_station, info_station in master_price['dict_info'].items():
  if 'code_geo' in info_station:
    dict_markets_insee.setdefault(info_station['code_geo'], []).append(id_station)
    station_uu = pd_df_insee.ix[info_station['code_geo']][u"Code géographique de l'unité urbaine UU2010"]
    dict_markets_uu.setdefault(station_uu, []).append(id_station)
    station_au = pd_df_insee.ix[info_station['code_geo']][u'Code AU2010']
    dict_markets_au.setdefault(station_au, []).append(id_station)

# #####################
# BRAND CHANGES
# #####################

dict_std_brands = {v[0]: v for k, v in dict_brands.items()}
# Builds dict with keys: tuple of brand changes combinations, ctent: list of station ids
dict_brand_chges = {}
for indiv_id, indiv_info in master_price['dict_info'].items():
  if len(indiv_info['brand_std']) > 1:
    tup_indiv_brands = tuple([brand[0] for brand in indiv_info['brand_std']])
    dict_brand_chges.setdefault(tup_indiv_brands, []).append(indiv_id)
# Display significant brand changes
print '\nBrand changes concerning at least 4 stations'
for k, v in dict_brand_chges.items():
  if len(v) >= 5: 
    print k, len(v)
# Print intra SUP changes
print '\nBrand changes between supermarkets'
for k, v in dict_brand_chges.items():
  if all(dict_std_brands[x][2] == 'SUP' for x in k):
    print k, len(v)
# Print intra OIL changes
print '\nBrand changes between oil stations'
for k,v in dict_brand_chges.items():
  if all(dict_std_brands[x][2] == 'OIL' for x in k):
    print k, len(v)

# For Total Access analysis (TODO: generalize? + MOVE)
dict_comp_total_access = {}
dict_comp_total_access_short = {}
for indiv_id, indiv_info in master_price['dict_info'].items():
  indiv_ind = master_price['ids'].index(indiv_ind) 
  if 'TOTAL_ACCESS' in indiv_info['brand_std']:
    if ls_ls_competitors[indiv_ind]:
      for competitor_id, competitor_distance in ls_ls_competitors[indiv_ind]:
        dict_comp_total_access.setdefault(competitor_id, []).append((indiv_id, competitor_distance))
for indiv_id, ls_stations in dict_comp_total_access.items():
  dict_comp_total_access[indiv_id] = sorted(ls_stations, key = lambda x: x[1])
  dict_comp_total_access_short[indiv_id] = dict_comp_total_access[indiv_id][0:2]

# #########
# SERVICES 
# #########

ls_services = [service for indiv_id, indiv_info in master_info.items()\
                 if indiv_info['services'][-1] for service in indiv_info['services'][-1]]
ls_services = list(set(ls_services))
for indiv_id, indiv_info in master_info.items():
  if indiv_info['services'][-1]:
    ls_station_services = [0 for i in ls_services]
    for service in indiv_info['services'][-1]:
      service_ind = ls_services.index(service)
      ls_station_services[service_ind] = 1
  else:
    ls_station_services = [None for i in ls_services]
  master_info[indiv_id]['list_service_dummies'] = ls_station_services

# #############################################
# INFO DATAFRAME (NO TOTAL ACCESS COMP HERE...)
# #############################################

ls_rows = []
for i, id in enumerate(master_price['ids']):
  city = master_price['dict_info'][id]['city']
  if city:
    if ',' in city:
      print i, id, city
    city = city.replace(',',' ')
  code_geo = master_price['dict_info'][id].get('code_geo')
  code_geo_ardts = master_price['dict_info'][id].get('code_geo_ardts')
  location_x, location_y, hours, highway = None, None, None, None
  ls_service_dummies = [None for i in ls_services]
  if master_info.get(id):
    if master_info[id]['gps'][-1]:
      location_x = master_info[id]['gps'][-1][0]
      location_y = master_info[id]['gps'][-1][1]
    if master_info[id]['hours'][-1]:
      hours = master_info[id]['hours'][-1].replace(',', ' ')
    highway = master_info[id]['highway'][-1]
    ls_service_dummies = master_info[id]['list_service_dummies']
    ta_id_1, ta_dist_1, ta_id_2, ta_dist_2 = None, None, None, None
    if id in dict_comp_total_access and len(dict_comp_total_access[id]) >= 1:
      ta_id_1 = dict_comp_total_access[id][0][0]
      ta_dist_1 = dict_comp_total_access[id][0][1]
    if id in dict_comp_total_access and len(dict_comp_total_access[id]) == 2:
      ta_id_2 = dict_comp_total_access[id][1][0]
      ta_dist_2 = dict_comp_total_access[id][1][1]   
  row = [id, city, code_geo, code_geo_ardts, location_x, location_y, highway, hours] +\
        ls_service_dummies + [ta_id_1, ta_dist_1, ta_id_2, ta_dist_2]
  ls_rows.append(row)
header = ['id', 'city', 'code_geo', 'code_geo_ardts', 'location_x', 'location_y', 'highway', 'hours'] +\
         ls_services + ['ta_id_1', 'ta_dist_1', 'ta_id_2', 'ta_dist_2']
pd_df_master_info = pd.DataFrame([list(i) for i in zip(*ls_rows)], header).T
 
pd_df_master_info['dpt'] = pd_df_master_info['code_geo'].map(lambda x: x[:2] if x else None)
# http://pandas.pydata.org/pandas-docs/dev/groupby.html
# http://stackoverflow.com/questions/17926273/how-to-count-distinct-values-in-a-column-of-a-pandas-group-by-object
# Corsica as 2A/2B here

# #################################
# OPENING DAYS, HOURS AND SERVICES
# #################################

# closed_days: not much heterogeneity: correlation with 24/24h?
# roughly c.2,000 stations are closed at least one day, c. 1600 on Sunday (only)
# 72 are supposed to be closed everyday (4th per) => no price... what happens?
# maybe sometimes opening days were mistaken for closed days
# TODO: check closed Sunday and closed every day (or so)
# hours: roughly half 24/24h... otherwise large number of occurences, not much interest
# TODO: check open 24/24h (equivalent to ATM?)

# High heterogeneity in set of services offered
# Services: pbm, can't know if it really changes or info is improved/corrected...
# Date of change unknown so kinda impossible to check an effect... (rather would come from price)
# TODO: check most standard service patterns... scarce services ... brand specificities...

