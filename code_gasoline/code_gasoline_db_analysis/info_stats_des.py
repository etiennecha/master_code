#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import os, sys, codecs
import re
import copy
import itertools
import numpy as np
import pandas as pd
import statsmodels.api as sm
from decimal import *
from collections import Counter
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
# import fiona
import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
from pysal.esda.mapclassify import Natural_Breaks as nb

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

# GENERIC

def get_field_as_list(id, field, master_price):
  """
  Returns a list with field info per period: [info_per_1, info_per_2, info_per_3...]
  Reminder: Field info is a list of lists: [(info, period),(info, period)...]
  Starts with None if no info at beginning
  """
  field_index = 0
  if not master_price['dict_info'][id][field]:
    # fill with None if no info at all for the field
    list_result = [None for i in range(len(master_price['dates']))]
  else:
    period_index = master_price['dict_info'][id][field][field_index][1]
    # initiate list_result, fill with None if no info at beginning
    if period_index == 0:
      list_result = []
    else:
      list_result = [None for i in range(period_index)]
    # fill list_results with relevant field info
    while period_index < len(master_price['dates']):
      if field_index < len(master_price['dict_info'][id][field]) - 1:
        # before the last change: compare periods
        if period_index < master_price['dict_info'][id][field][field_index + 1][1]:
          list_result.append(master_price['dict_info'][id][field][field_index][0])
        else:
          field_index += 1
          list_result.append(master_price['dict_info'][id][field][field_index][0])
      else:
        # after the last change: fill with last info given
        list_result.append(master_price['dict_info'][id][field][-1][0])
      period_index += 1
  return list_result

def get_latest_info(id, field, master_info):
  # TODO: enrich for categorical variables ?
  list_info = [elt for elt in master_info[id][field]]
  if list_info:
    return list_info[-1]
  else:
    return None

def get_str_no_accent_up(line):
  """Suppresses some accents/weird chars from a unicode str"""
  if line:
    accents = {u'a': [u'à', u'ã', u'á', u'â', u'\xc2'],
               u'c': [u'ç', u'\xe7'],
               u'e': [u'é', u'è', u'ê', u'ë', u'É', u'\xca', u'\xc8', u'\xe8', u'\xe9', u'\xc9'],
               u'i': [u'î', u'ï', u'\xcf', u'\xce'],
               u'o': [u'ô', u'ö'],
               u'u': [u'ù', u'ü', u'û'],
               u' ': [u'\xb0'] }
    for (char, accented_chars) in accents.iteritems():
      for accented_char in accented_chars:
        line = line.replace(accented_char, char) #line.encode('latin-1').replace(accented_char, char)
    line = line.replace('&#039;',' ').rstrip().lstrip().upper()
  return line

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
  
  master_price = dec_json(path_data + folder_built_master_json + r'\master_price')
  master_info = dec_json(path_data + folder_built_master_json + r'\master_info_for_output')
  list_list_competitors = dec_json(path_data + folder_built_master_json + r'\list_list_competitors')
  list_tuple_competitors = dec_json(path_data + folder_built_master_json + r'\list_tuple_competitors')
  dict_dpts_regions = dec_json(path_data + folder_dpts_regions + r'\dict_dpts_regions')
  
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
  
  # #####################
  # IMPORT INSEE DATA
  # #####################
  
  pd_df_insee = pd.read_csv(path_data + folder_built_csv + r'/master_insee_output.csv',\
                              encoding = 'utf-8', dtype= str)
  ls_no_match = []
  pd_df_insee[u'Département - Commune CODGEO'] = pd_df_insee[u'Département - Commune CODGEO'].astype(str)
  ls_insee_data_codes_geo = list(pd_df_insee[u'Département - Commune CODGEO'])
  for station_id, station_info in master_price['dict_info'].iteritems():
    if 'code_geo' in station_info.keys():
      if (station_info['code_geo'] not in ls_insee_data_codes_geo) and\
         (station_info['code_geo_ardts'] not in ls_insee_data_codes_geo):
			  ls_no_match.append((station_id, station_info['code_geo']))
  # exclude dom tom
  pd_df_insee = pd_df_insee[~pd_df_insee[u'Département - Commune CODGEO'].str.contains('^97')]
  pd_df_insee['Population municipale 2007 POP_MUN_2007'] =\
    pd_df_insee['Population municipale 2007 POP_MUN_2007'].astype(float)
  
  # #####################
  # MARKET DEFINITIONS
  # #####################
  
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
  
  # #####################
  # BRAND CHANGES
  # #####################
  
  dict_brands = dec_json(path_data + folder_source_brand + r'\dict_brands')
  # Check that all brands are in dict_brands
  for id, station in master_price['dict_info'].iteritems():
    for brand in station['brand']:
      if get_str_no_accent_up(brand[0]) not in dict_brands:
        print 'Not in dict_brands:', get_str_no_accent_up(brand[0])
  # enc_stock_json(dict_brands, path_data + folder_source_brand + r'\dict_brands')
  
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
  
  # #########
  # SERVICES 
  # #########
  
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
  
  # #####################
  # INFO DATAFRAME
  # #####################
  
  list_rows = []
  for i, id in enumerate(master_price['ids']):
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
      highway = master_info[id]['highway'][-1]
      list_service_dummies = master_info[id]['list_service_dummies']
      ta_id_1, ta_dist_1, ta_id_2, ta_dist_2 = None, None, None, None
      if id in dict_comp_total_access and len(dict_comp_total_access[id]) >= 1:
        ta_id_1 = dict_comp_total_access[id][0][0]
        ta_dist_1 = dict_comp_total_access[id][0][1]
      if id in dict_comp_total_access and len(dict_comp_total_access[id]) == 2:
        ta_id_2 = dict_comp_total_access[id][1][0]
        ta_dist_2 = dict_comp_total_access[id][1][1]   
    row = [id, city, code_geo, code_geo_ardts, location_x, location_y, highway, hours] +\
          list_service_dummies + [ta_id_1, ta_dist_1, ta_id_2, ta_dist_2]
    list_rows.append(row)
  header = ['id', 'city', 'code_geo', 'code_geo_ardts', 'location_x', 'location_y', 'highway', 'hours'] +\
           list_services + ['ta_id_1', 'ta_dist_1', 'ta_id_2', 'ta_dist_2']
  pd_df_master_info = pd.DataFrame([list(i) for i in zip(*list_rows)], header).T
  
  pd_df_master_info['dpt'] = pd_df_master_info['code_geo'].map(lambda x: x[:2] if x else None)
  # http://pandas.pydata.org/pandas-docs/dev/groupby.html
  # http://stackoverflow.com/questions/17926273/how-to-count-distinct-values-in-a-column-of-a-pandas-group-by-object
  # Corsica as 2A/2B here
  
  # #####################
  # MAPS
  # #####################
  
  # TODO: beware with highway / corsica
  # TODO: build price stats to allow static display on maps
  # TODO: always do map + tables in pandas (by region maybe instead of dpt)
  # TODO: compare with zagaz data when possible (i.e. no price)
  
  # TODO: heatmap population (by dpt)
  # TODO: heatmap nb gas stations (by dpt)
  # TODO: heatmap price level (by dpt... try to include corsica?)
  # TODO: heatmap price dispersion (?)
  # TODO: heatmap supermarket penetration
  # TODO: heatmap concentration i.e. average distance between stations or such a stat
  # TODO: heatmap concentration i.e. nb of monopolies / duopolies (distinguish supermarkets vs. not)
    
  # TODO: scatter scatter gas stations
  # TODO: scatter brand changes
  # TODO: scatter bad reporting / stations disappearing reappearing
  # TODO: scatter promotions
  
  # France
  x1 = -5.
  x2 = 9.
  y1 = 42.
  y2 = 52.
  
  # Lambert conformal for France (as suggested by IGN... check WGS84 though?)
  m_france =  Basemap(resolution='i',
                      projection='lcc',
                      ellps = 'WGS84',
                      lat_1 = 44.,
                      lat_2 = 49.,
                      lat_0 = 46.5,
                      lon_0 = 3,
                      llcrnrlat=y1,
                      urcrnrlat=y2,
                      llcrnrlon=x1,
                      urcrnrlon=x2)
  
  path_commune = r'\data_maps\GEOFLA_COM_WGS84'
  # m_france.readshapefile(path_data + path_commune + '\COMMUNE', 'communes_fr', color = 'none', zorder=2)
  # m_france.communes_fr_info[0]
  # m_france.communes_fr[0]
  # ls_map_codes_geo = [commune['INSEE_COM'] for commune in m_france.communes_fr_info]
  # ms_map_insee_pbm = [code_geo for code_geo in ls_insee_data_codes_geo if code_geo not in ls_map_codes_geo]
  # # no issue: essentially Paris/Lyon/Marseille and DOM/TOM
  
  path_dpt = r'\data_maps\GEOFLA_DPT_WGS84'
  m_france.readshapefile(path_data + path_dpt + '\DEPARTEMENT', 'dpts_fr', color = 'none', zorder = 2)
  # Can be several polygons per dpt...
  
  # TODO: create dataframe with info by dpt
  # TODO: create categories and labels
  # TODO: plot with colour bar
  
  dict_all_dpt_info = {}
  for i, dict_dpt_info in enumerate(m_france.dpts_fr_info):
    if (dict_dpt_info['CODE_DEPT'] in dict_all_dpt_info) and \
       (Polygon(m_france.dpts_fr[i]).area < dict_all_dpt_info[dict_dpt_info['CODE_DEPT']]['poly'].area):
      pass
    else:
      dict_all_dpt_info[dict_dpt_info['CODE_DEPT']] = dict_dpt_info
      dict_all_dpt_info[dict_dpt_info['CODE_DEPT']]['poly'] = Polygon(m_france.dpts_fr[i])
  
  pd_df_dpts = pd.DataFrame(dict_all_dpt_info).T                                                        
  # areas computed from biggest polygon (for density computation)
  pd_df_dpts['area'] = pd_df_dpts['poly'].map(lambda x: x.area)
  # population computed from cities (for density computation)
  pd_df_pop = pd_df_insee[[u'Département DEP', 'Population municipale 2007 POP_MUN_2007']].\
                            groupby([u'Département DEP'], sort = True).sum()
  pd_df_dpts = pd_df_dpts.join(pd_df_pop)          
  
  # could take merge approach  + test with zagaz
  pd_df_dpts['dpt_nb_stations'] = np.nan
  grouped_dpt = pd_df_master_info.groupby('dpt')
  for dpt, group in grouped_dpt:
    pd_df_dpts['dpt_nb_stations'].ix[dpt] = len(group)
  
  # density (different definitions)
  pd_df_dpts['density_area'] = pd_df_dpts['dpt_nb_stations'] / pd_df_dpts['area']
  pd_df_dpts['density_pop'] = pd_df_dpts['dpt_nb_stations'] / pd_df_dpts['Population municipale 2007 POP_MUN_2007']
  
  from matplotlib import colors
  
  for density_field in ('density_area', 'density_pop'):
    # Easier to work with NaN values when classifying
    pd_df_dpts.replace(to_replace={density_field: {0: np.nan}}, inplace=True)
    # Calculate Jenks natural breaks for density
    breaks = nb(pd_df_dpts[pd_df_dpts[density_field].notnull()][density_field].values, initial=300, k=5)
    # The notnull method lets us match indices when joining
    jb = pd.DataFrame({'jenks_bins': breaks.yb}, index=pd_df_dpts[pd_df_dpts[density_field].notnull()].index)
    pd_df_dpts = pd_df_dpts.join(jb)
    pd_df_dpts.jenks_bins.fillna(-1, inplace=True)
    
    fig, ax = plt.subplots()
    m_france.drawcountries()
    m_france.drawcoastlines()
    pd_df_dpts['patches'] = pd_df_dpts['poly'].map(lambda x: PolygonPatch(x,
                                                                          fc='#555555',
                                                                          ec='#787878', 
                                                                          lw=.25, 
                                                                          alpha=.9,
                                                                          zorder=4))
    cmap = plt.get_cmap('Blues')
    norm = colors.Normalize()
    pc = PatchCollection(pd_df_dpts['patches'], match_original=True)
    pc.set_facecolor(cmap(norm(pd_df_dpts['jenks_bins'].values)))
    ax.add_collection(pc)
    # ax.add_collection(PatchCollection(pd_df_dpts['patches'].values, match_original=True))
    plt.title(density_field)
    plt.tight_layout()
    # this will set the image width to 722px at 100dpi
    plt.savefig(path_data + r'\data_maps\graphs\gasoline_%s.png' %density_field , dpi=700)
    plt.close()
    plt.clf()
    del(pd_df_dpts['jenks_bins'])