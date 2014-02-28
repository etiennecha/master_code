#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json
import itertools
import math
import copy
import random
import pprint
import numpy as np
import scipy
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import patsy
import xlrd
from generic_master_price import *

if __name__=="__main__":
  # path_data: data folder at different locations at CREST vs. HOME
  # could do the same for path_code if necessary (import etc).
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  # structure of the data folder should be the same
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline\master_diesel'
  folder_source_brand = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'
  folder_dpts_regions = r'\data_insee\Regions_departements'
  
  master_price = dec_json(path_data + folder_built_master_json + r'\master_price_diesel')
  master_info = dec_json(path_data + folder_built_master_json + r'\master_info_diesel_for_output') # CAUTION
  
  list_list_competitors = dec_json(path_data + folder_built_master_json + r'\list_list_competitors')
  list_tuple_competitors = dec_json(path_data + folder_built_master_json + r'\list_tuple_competitors')
  
  dict_brands = dec_json(path_data + folder_source_brand + r'\dict_brands')
  
  # ################
  # INSEE & MARKETS
  # ################
  
  # import csv data as pd.df and check correspondence
  # TODO: have a look at master_price: some stations have no insee code
  
  # INSEE DATA DESCRIPTION
  
  # UNITES URBAINES (rural alone - general classification)
  # u'Code géographique de l'unité urbaine UU2010' : id de l'uu
  # u'Nombre de communes NB_COM' : nb de communes ds l'uu
  # u'Population municipale 2007 POP_MUN_2007_UU' : pop ds l'uu
  # u'Taille de l'unité urbaine TAILLE' : taille de l'uu (comme pop mais discret)
  # u'Type d'unité urbaine TYPE': équivalent au type de commune: rural etc (6 catégories)
  
  # AIRES URBAINES (rural regrouped in 000 - focus on cities)
  # u'Code AU2010': id de l'au
  # u'Tranche d'aire urbaine 2010 TAU2010' : taille (catégories de pop) de l'au
  # u'Catégorie de la commune dans le zonage en aires urbaines 2010 CATAEU2010': (rural, petit/moyen/grand pole etc.)
  
  # COMMUNES
  # u'Type de commune TYPE_2010' : Rural/Urbain
  # u'Statut de la commune STATUT_2010': R/C/I/B (Type en plus précis)
  # u'Population municipale 2007 POP_MUN_2007' Pop commune
  
  pd_df_insee = pd.read_csv(path_data + folder_built_csv + r'/master_insee_output.csv',
                            encoding = 'utf-8',
                            dtype = str)
  pd_df_insee['id_code_geo'] = pd_df_insee[u'Département - Commune CODGEO']
  pd_df_insee = pd_df_insee.set_index('id_code_geo')
  dict_markets_insee = {}
  dict_markets_au = {}
  dict_markets_uu = {}
  # some stations don't have code_geo (short spells which are not in master_info)
  for id_station, info_station in master_price['dict_info'].iteritems():
    if 'code_geo' in info_station:
      dict_markets_insee.setdefault(info_station['code_geo'], []).append(id_station)
      station_uu = pd_df_insee.ix[info_station['code_geo']][u"Code géographique de l'unité urbaine UU2010"]
      dict_markets_uu.setdefault(station_uu, []).append(station_id)
      station_au = pd_df_insee.ix[info_station['code_geo']][u'Code AU2010']
      dict_markets_au.setdefault(station_au, []).append(station_id)
  
  # #######################################################
  # REDUCE MULTIPLE BRAND CHANGES (for INFO and PRICE FILE)
  # ########################################################
   
  ls_brand_adjs = [('10130004', 0, 1),
                   ('31700002', 1, 2),
                   ('68490001', 1, 2),
                   ('60230003', 1, 2),
                   ('78150001', 1, 4),
                   ('84700001', 1, 2),
                   ('93420006', 1, 2),
                   ('91590008', 1, 2),
                   ('33640003', 1, 2)]
  for indiv_id, ind_brand_1, ind_brand_2 in ls_brand_adjs:
    master_price['dict_info'][indiv_id]['brand'][ind_brand_2][1] =\
      master_price['dict_info'][indiv_id]['brand'][ind_brand_1][1]
    del(master_price['dict_info'][indiv_id]['brand'][ind_brand_1:ind_brand_2])
  
  # All Carrefour Market => Coop => Systeme U
  for id_station, info_station in master_price['dict_info'].items():
    if len(info_station['brand']) > 2 and info_station['brand'][1][0] == u'Coop':
      master_price['dict_info'][id_station]['brand'][2][1] = master_price['dict_info'][id_station]['brand'][1][1]
      del(master_price['dict_info'][id_station]['brand'][1])
  
  # Check stations with more than two brand changes
  for id_station, info_station in master_price['dict_info'].items():
    if len(info_station['brand']) > 2:
      print id_station, info_station['brand']
  
  # ########################################
  # BRAND: CHANGE TREATMENT (for INFO FILE)
  # ########################################
  
  # TODO: put it after brand fixing for consistency (if needed ???)
  dict_comp_total_access = {}
  dict_comp_total_access_short = {}
  for i, id in enumerate(master_price['ids']):
    station_info = master_price['dict_info'][id]
    if station_info['brand']:
      # generalize to all (single) brand changes ?
      if 'TOTAL_ACCESS' in [dict_brands[get_str_no_accent_up(brand)][0] \
                              for (brand, day_ind) in station_info['brand']]:
        if list_list_competitors[i]:
          for (indiv_id, indiv_distance) in list_list_competitors[i]:
            dict_comp_total_access.setdefault(indiv_id, []).append((id, indiv_distance))
  for id, list_stations in dict_comp_total_access.iteritems():
    dict_comp_total_access[id] = sorted(list_stations, key = lambda x: x[1])
    dict_comp_total_access_short[id] = dict_comp_total_access[id][0:2]
  
  # #########################
  # SERVICES (for INFO FILE)
  # #########################
  
  set_services = set()
  for id, station in master_info.iteritems():
    if station['services'][-1]:
      for service in station['services'][-1]:
        set_services.add(service)
  list_services = list(set_services)
  for id, station in master_info.iteritems():
    if station['services'][-1] is not None:
      list_station_services = [0 for i in range(len(list_services))]
      for service in station['services'][-1]:
        service_ind = list_services.index(service)
        list_station_services[service_ind] = 1
    else:
      list_station_services = [None for i in range(len(list_services))]
    master_info[id]['list_service_dummies'] = list_station_services
  
  # #################################
  # OUTPUT CSV: PRICE AND INFO FILES
  # #################################
  
  # PRICE FILE
  series = 'diesel' 
  ls_all_prices = [price for ls_prices in master_price[series] for price in ls_prices]
  ls_all_ids = [id_indiv for id_indiv in master_price['ids'] for x in range(len(master_price['dates']))]
  ls_all_dates = [date for id_indiv in master_price['ids'] for date in master_price['dates']]
  
  # TODO: correct brand beginning dates based on price observations
  # TODO: loop + check if robust to None as brand
  ls_ls_all_brands = []
  for i in range(3):
    ls_ls_brands =  [[[dict_brands[get_str_no_accent_up(brand)][i], period]\
                          for brand, period in master_price['dict_info'][id_indiv]['brand']]\
                            for id_indiv in master_price['ids']]
    ls_ls_brands = [get_expanded_list(ls_brands, len(master_price['dates'])) for ls_brands in ls_ls_brands]
    ls_ls_all_brands.append([brand for ls_expanded_brands in ls_ls_brands for brand in ls_expanded_brands])
  
  index = pd.MultiIndex.from_tuples(zip(ls_all_ids, ls_all_dates))
  columns = ['price', 'brand_1', 'brand_2', 'brand_type']
  pd_mi_prices = pd.DataFrame(zip(*[ls_all_prices] + ls_ls_all_brands), index = index, columns = columns)
  # Get rid of periods with low number of observations (missing periods filled ex post...)
  # TODO: try to do following correction directly with multiindex (avoid double conversion)
  pd_pd_prices = pd_mi_prices.to_panel()
  for date in pd_pd_prices.minor_axis:
    if pd_pd_prices['price'][date].count() < 8000:
      pd_pd_prices['price'][date] = np.nan
  pd_mi_prices_for_output = pd_pd_prices.to_frame(filter_observations=False)
  
  pd_mi_prices_for_output['price'] = pd_mi_prices_for_output['price'].astype(np.float32)  
  
  # pd_mi_prices_for_output.to_csv(path_data + folder_built_csv + r'/master_price_output.csv', float_format='%.3f')
  
  # pd_df_test_1 = pd.read_csv(path_data + folder_built_csv + r'/master_price_output.csv', dtype = str)
  
  # # Convert dates to datetime format
  # pd_pd_prices.minor_axis = pd.to_datetime(pd_pd_prices.minor_axis)
  
  # INFO FILE (right now based on master_ids since can't do much w/o prices)
  
  # TODO: complete location, services, hours
  # TODO: add insee data (separate table?)
  # TODO: add brand changes, price rigidity (censored etc), competition (+closed/opening?)
  # TODO: check those in master_price not in master_info (reconciliate or drop?)
  
  list_rows = []
  for indiv_ind, id in enumerate(master_price['ids']):
    city = master_price['dict_info'][id]['city']
    if city:
      city = city.replace(',',' ')
    code_geo = master_price['dict_info'][id].get('code_geo')
    code_geo_ardts = master_price['dict_info'][id].get('code_geo_ardts')
    location_x, location_y, hours, highway = None, None, None, None
    list_service_dummies = [None for i in range(len(list_services))]
    if master_info.get(id):
      if master_info[id]['gps'][-1]:
        location_x = master_info[id]['gps'][-1][0]
        location_y = master_info[id]['gps'][-1][1]
      if master_info[id]['hours'][-1]:
        hours = master_info[id]['hours'][-1].replace(',', ' ')
      highway = master_info[id]['highway'][3]
      list_service_dummies = master_info[id]['list_service_dummies']
      ta_id_1, ta_dist_1, ta_id_2, ta_dist_2 = None, None, None, None
      if id in dict_comp_total_access and len(dict_comp_total_access[id]) >= 1:
        ta_id_1 = dict_comp_total_access[id][0][0]
        ta_dist_1 = dict_comp_total_access[id][0][1]
      if id in dict_comp_total_access and len(dict_comp_total_access[id]) == 2:
        ta_id_2 = dict_comp_total_access[id][1][0]
        ta_dist_2 = dict_comp_total_access[id][1][1]
    row = [id, city, code_geo, code_geo_ardts, location_x, location_y, highway, hours] +\
          list_service_dummies +\
          [ta_id_1, ta_dist_1, ta_id_2, ta_dist_2]+\
          [np_ar_diffs_argmaxs[indiv_ind] + window_limit,\
           round(np_ar_mean_diffs[indiv_ind, np_ar_diffs_argmaxs[indiv_ind]], 4)]
    list_rows.append(row)
  header = ['id', 'city', 'code_geo', 'code_geo_ardts', 'location_x', 'location_y', 'highway', 'hours'] +\
           list_services +\
           ['ta_id_1', 'ta_dist_1', 'ta_id_2', 'ta_dist_2'] +\
           ['arg_max_diff', 'max_diff']
  pd_df_master_info = pd.DataFrame([list(i) for i in zip(*list_rows)], header).T
  # pd_df_master_info[['arg_max_diff','max_diff']].head(n=10)
  
  # pd_df_master_info.to_csv(path_data + folder_built_csv + r'/master_info_output.csv', float_format='%.4f', encoding='utf-8', index=False)
  
  # pd_df_test_2 = pd.read_csv(path_data + folder_built_csv + r'/master_info_output.csv')
  
  # ############
  # DEPRECATED
  # ############
  
  # DEPRECATED (PRICE FILE)
  
  # dict_panel_data_master_price = {}
  # for i, id in enumerate(master_price['ids']):
    # list_station_prices = master_price['diesel_price'][i]
    # # TODO (permanent: complete price series based on brand series (corresponds to filled missing periods)
    # if [x for x in list_station_prices if x] and not list_station_prices[0]:
      # first_valid_price = 0
      # while not list_station_prices[first_valid_price]:
        # first_valid_price += 1
      # if master_price['dict_info'][id]['brand'][0][1] != first_valid_price:
        # master_price['dict_info'][id]['brand'][0][1] = first_valid_price
        # print 'Corrected starting brand day index for:', id
    # list_station_brands_0 = [dict_brands[get_str_no_accent_up(brand)][0] if brand else brand\
                            # for brand in get_field_as_list(id, 'brand', master_price)]
    # list_station_brands_1 = [dict_brands[get_str_no_accent_up(brand)][1] if brand else brand\
                              # for brand in get_field_as_list(id, 'brand', master_price)]
    # list_station_brands_2 = [dict_brands[get_str_no_accent_up(brand)][2] if brand else brand\
                              # for brand in get_field_as_list(id, 'brand', master_price)]
    # dict_station = {'price' : np.array(list_station_prices, dtype = np.float32),
                    # 'brand_0' : np.array(list_station_brands_0),
                    # 'brand_1' : np.array(list_station_brands_1),
                    # 'brand_type' : np.array(list_station_brands_2)}
    # dict_panel_data_master_price[id] = pd.DataFrame(dict_station, index = master_price['dates'])
  # pd_pd_master_price = pd.Panel(dict_panel_data_master_price)
  # pd_pd_master_price = pd_pd_master_price.transpose('minor', 'items', 'major')
  
  # for elt in pd_pd_master_price.minor_axis:
	  # if pd_pd_master_price['price'][elt].count() < 8000:
      # pd_pd_master_price['price'][elt] = np.nan
  
  # pd_mi_master_price = pd_pd_master_price.to_frame(filter_observations=False)
  # pd_mi_master_price['price'] = pd_mi_master_price['price'].astype(np.float32)
  
  # DEPRECATED (BRAND CHANGES)
  
  # master_nearby_brand_chge = []
  # for distance_max in (0.5, 1, 2, 3, 4, 5):
    # ls_ls_nearby_brand_chge = [[0 for i in range(len(master_price['dates']))]\
                                # for j in range(len(master_price['ids']))]
    # for i, id in enumerate(master_price['ids']):
      # station_info = master_price['dict_info'][id]
      # if station_info['brand']:
        # if 'TOTAL_ACCESS' in [dict_brands[get_str_no_accent_up(brand)][0] \
                                # for (brand, day_ind) in station_info['brand']]:
          # ls_station_brands_0 = [dict_brands[get_str_no_accent_up(brand)][0] if brand else brand\
                                  # for brand in get_field_as_list(id, 'brand', master_price)]
          # ls_station_brands_d = [1 if x == 'TOTAL_ACCESS' else 0 for x in ls_station_brands_0]
          # if list_list_competitors[i]:
            # for (indiv_id, indiv_distance) in list_list_competitors[i]:
              # if indiv_distance < distance_max:
                # if sum(ls_station_brands_d) > sum(ls_ls_nearby_brand_chge[master_price['ids'].index(indiv_id)]):
                  # ls_ls_nearby_brand_chge[master_price['ids'].index(indiv_id)] = ls_station_brands_d
    # master_nearby_brand_chge.append(ls_ls_nearby_brand_chge)
