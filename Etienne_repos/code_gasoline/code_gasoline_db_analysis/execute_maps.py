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

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
    path_code = r'W:\Bureau\Etienne_work\Code'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
    path_code = r'C:\Users\etna\Dropbox\Code\Etienne_repos'
  
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  folder_source_brands = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_source_gps_coordinates_std = r'\data_gasoline\data_source\data_stations\data_gouv_gps\std'
  
  # TODO: Update with new master info
  master_info_temp = dec_json(path_data + folder_built_master_json + r'\master_diesel_bu\master_info_for_output')
  
  master_price = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')
  dict_brands = dec_json(path_data + folder_source_brands + r'\dict_brands')
  
  # MAP FRAMEWORK
  
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