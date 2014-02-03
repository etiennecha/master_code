#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json
import itertools
from lxml import etree
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
from generic_master_info import *
# import fiona
from pysal.esda.mapclassify import Natural_Breaks as nb

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline\master_diesel'
  folder_source_brands = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_source_gps_coordinates_std = r'\data_gasoline\data_source\data_stations\data_gouv_gps\std'
  
  folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'
  folder_dpts_regions = r'\data_insee\Regions_departements'
  
  master_price = dec_json(path_data + folder_built_master_json + r'\master_price_diesel')
  master_info = dec_json(path_data + folder_built_master_json + r'\master_info_diesel_for_output')
  list_list_competitors = dec_json(path_data + folder_built_master_json + r'\list_list_competitors')
  list_tuple_competitors = dec_json(path_data + folder_built_master_json + r'\list_tuple_competitors')
  dict_dpts_regions = dec_json(path_data + folder_dpts_regions + r'\dict_dpts_regions')
  dict_brands = dec_json(path_data + folder_source_brands + r'\dict_brands')
  # TODO: Update with new master info
  master_info_temp = dec_json(path_data + folder_built_master_json + r'\master_info_diesel_for_output')
  
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

  # #################
  # MAP FRAMEWORK (1)
  # #################

  x1 = -5.
  x2 = 9.
  y1 = 42.
  y2 = 52.
  
  # Lambert conformal for France (as suggested by IGN... check WGS84 though?)
  m_route = Basemap(resolution='i',
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
  
   # GAS STATION DATA
  
  ls_ids = []
  ls_gps = []
  ls_chges = []
  for indiv_id, gas_station in master_info_temp.items():
    if indiv_id in master_price['dict_info']:
      indiv_info = master_price['dict_info'][indiv_id]
      ls_brands = [x[0] for x in itertools.groupby([get_str_no_accent_up(brand[0]) for brand in indiv_info['brand']])]
      if 'TOTAL ACCESS' in ls_brands and 'ELF' in ls_brands:
        gps = gas_station['gps'][-1]
        if gps:
          ls_gps.append(gps)
          ls_chges.append('elf_access')
          ls_ids.append(indiv_id)
      elif 'TOTAL ACCESS' in ls_brands and len(ls_brands) > 1:
        gps = gas_station['gps'][-1]
        if gps:
          ls_gps.append(gps)
          ls_chges.append('other_access')
          ls_ids.append(indiv_id)
      elif 'TOTAL' in ls_brands or 'ELF' in ls_brands:
        gps = gas_station['gps'][-1]
        if gps:
          ls_gps.append(gps)
          ls_chges.append('no')
          ls_ids.append(indiv_id)
  
  df_gas_stations = pd.DataFrame({'point': [Point(m_route(gps[1], gps[0])) for gps in ls_gps],
                                  'chge' : ls_chges,
                                  'id' : ls_ids})
  dev = m_route.scatter([station.x for station in df_gas_stations[df_gas_stations['chge']=='no']['point']],
                        [station.y for station in df_gas_stations[df_gas_stations['chge']=='no']['point']],
                        3, marker = 'o', lw=0, facecolor = '#339966', edgecolor = 'w', alpha = 0.5,
                        antialiased = True, zorder = 2)
  dev = m_route.scatter([station.x for station in df_gas_stations[df_gas_stations['chge']=='other_access']['point']],
                        [station.y for station in df_gas_stations[df_gas_stations['chge']=='other_access']['point']],
                        3, marker = 'D', lw=0, facecolor = '#3366CC', edgecolor = 'w', alpha = 0.6,
                        antialiased = True, zorder = 3)
  dev = m_route.scatter([station.x for station in df_gas_stations[df_gas_stations['chge']=='elf_access']['point']],
                        [station.y for station in df_gas_stations[df_gas_stations['chge']=='elf_access']['point']],
                        3, marker = 'D', lw=0, facecolor = '#CC0000', edgecolor = 'w', alpha = 0.6,
                        antialiased = True, zorder = 3)
  
  m_route.drawcountries()
  m_route.drawcoastlines()
  # plt.savefig(path_data + r'\data_maps\graphs\test_total_access.png', bbox_inches='tight', dpi=300)
  plt.savefig(path_data + r'\data_gasoline\data_built\data_graphs\total_access\maps\total.png',
              bbox_inches='tight',
              dpi=700)

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
