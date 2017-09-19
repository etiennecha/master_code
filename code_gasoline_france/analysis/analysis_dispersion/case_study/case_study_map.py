#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_maps import *
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
from matplotlib.text import TextPath

path_dir_built = os.path.join(path_data,
                              'data_gasoline',
                              'data_built',
                              'data_scraped_2011_2014')
path_dir_built_json = os.path.join(path_dir_built, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_insee_extracts = os.path.join(path_data,
                                       'data_insee',
                                       'data_extracts')


# ###############
# LOAD DATA
# ###############

# LOAD DF INFO AND PRICES

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
# Get rid of highway (gps too unreliable so far + require diff treatment)
df_info = df_info[df_info['highway'] != 1]

# LOAD PRICES (only for stats des...)
df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                            parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# LOAD JSON CLOSE

dict_ls_close = dec_json(os.path.join(path_dir_built_json,
                                      'dict_ls_close.json'))
ls_close_pairs = dec_json(os.path.join(path_dir_built_json,
                                      'ls_close_pairs.json'))

# COMPETITORS
ls_comp_pairs = dec_json(os.path.join(path_dir_built_json,
                                      'ls_comp_pairs.json'))

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# NB BASED ON INSEE AREAS
df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                          'df_insee_areas.csv'),
                             dtype = {'CODGEO' : str,
                                      'AU2010': str,
                                      'UU2010': str,
                                      'BV' : str},
                             encoding = 'utf-8')

df_info = df_info.reset_index().merge(df_insee_areas[['CODGEO', 'AU2010', 'UU2010', 'BV']],
                                      left_on = 'ci_1', right_on = 'CODGEO',
                                      how = 'left').set_index('id_station')

ls_areas = ['ci_1', 'AU2010', 'UU2010', 'BV']
df_area_nb = df_info[ls_areas].copy()
df_area_nb.reset_index(inplace = True) # index used to add data by area
for area in ls_areas:
  se_area = df_info[area].value_counts()
  df_area_nb.set_index(area, inplace = True)
  df_area_nb['nb_%s' %area] = se_area
df_area_nb.set_index('id_station', inplace = True)

# NB SAME GROUP IN INSEE AREAS
ls_areas = ['ci_1', 'AU2010', 'UU2010', 'BV']
df_area_same = df_info[['group'] + ls_areas].copy()
ls_groups = df_info['group'][~(df_info['group'].isnull())].unique()
for group_name in ls_groups:
  df_group = df_info[df_info['group'] == group_name]
  for area in ls_areas:
    se_group_area = df_group[area].value_counts()
    df_area_same.reset_index(inplace = True)
    df_area_same.set_index(area, inplace = True)
    df_area_same.loc[df_area_same['group'] == group_name,
                     'nb_s_%s' %area] = se_group_area
df_area_same.set_index('id_station', inplace = True)
df_area_same = df_area_same[['nb_s_%s' %area for area in ls_areas]]

# MARKETS ON THEIR OWN
ls_dict_markets = dec_json(os.path.join(path_dir_built_json,
                                        'ls_dict_stable_markets.json'))

ls_robust_markets = dec_json(os.path.join(path_dir_built_json,
                                          'ls_robust_stable_markets.json'))

# ####
# MAPS
# ####

dict_robust_markets = {}
for x in ls_robust_markets:
  dict_robust_markets.setdefault(len(x), []).append(x)

def draw_market_map(ls_market_ids, directory, zoom = 12, delta_lng = 0.18, delta_lat = 0.10):
  ls_close_ids = [x[0] for market_id in ls_market_ids for x in dict_ls_close[market_id]]
  ls_outside_ids = list(set(ls_close_ids).difference(set(ls_market_ids)))
  
  ls_market_coordinates = [df_info.ix[x][['lat', 'lng']].tolist() for x in ls_market_ids]
  lat_ref = (np.max([x[0] for x in ls_market_coordinates]) +\
               np.min([x[0] for x in ls_market_coordinates])) / 2
  lng_ref = (np.max([x[1] for x in ls_market_coordinates]) +\
               np.min([x[1] for x in ls_market_coordinates])) / 2
  
  ls_outside_coordinates = [df_info.ix[x][['lat', 'lng']].tolist() for x in ls_outside_ids]
  
  ## todo: see how to get dist of X km?
  #zoom = 12 # defines how many tiles are collected (precision)
  #delta_lat = 0.10 # height 0.10
  #delta_lng = 0.18 # width 0.18
  
  adj_lng_c = 0 # -0.01
  
  a, bbox = getImageCluster(lat_ref - delta_lat, # need 1/2 delta_lat
                            lng_ref - delta_lng + adj_lng_c, # need 1/2 delta_lng
                            delta_lat * 2,
                            delta_lng * 2,
                            zoom)
  
  fig = plt.figure(figsize=(10, 10))
  ax = plt.subplot(111)
  m = Basemap(
      llcrnrlon=bbox[0], llcrnrlat=bbox[1],
      urcrnrlon=bbox[2], urcrnrlat=bbox[3],
      projection='merc', ax=ax)
  
  # display image composed of OSM times
  m.imshow(a, interpolation='lanczos', origin='upper')
  
  # convert coord (caution: inversion)
  for ls_gps_points, marker_c, marker in [[ls_market_coordinates, 'b', 'o'],
                                          [ls_outside_coordinates, 'r', 's']]:
    ls_points = [m(x[1], x[0]) for x in ls_gps_points]
    ax.scatter([point[0] for point in ls_points],
               [point[1] for point in ls_points],
               alpha = 0.8, s = 30, color = marker_c, marker = marker, zorder = 9)
  
  # add circles
  def radius_for_tissot(dist_km):
      return np.rad2deg(dist_km/6367.)
  
  for ls_gps_points, marker_c, radius in [[ls_market_coordinates, 'b', 3],
                                          [ls_outside_coordinates, 'r', 5]]:
    for lat_x, lng_x in ls_gps_points:
      m.tissot(lng_x,
               lat_x,
               radius_for_tissot(radius),
               256, facecolor=marker_c, alpha=0.1, zorder = 8)
  
  # need to cut again (otherwise get whole loaded tiles displayed)
  xmin, ymin = m(lng_ref - delta_lng + adj_lng_c, lat_ref - delta_lat)
  xmax, ymax = m(lng_ref + delta_lng + adj_lng_c, lat_ref + delta_lat)
  
  ax.set_xlim((xmin, xmax))
  ax.set_ylim((ymin, ymax))
  
  plt.tight_layout()
  #plt.show()
  
  # add correct map scale (or try using tmerc?)
  xmin_deg, ymin_deg = m(xmin, ymin, inverse = True)
  xmax_deg, ymax_deg = m(xmax, ymax, inverse = True)
  dref = 3.0
  lat0 = ymin_deg + 0.005 #0.012
  distance=dref/np.cos(lat0*np.pi/180.)
  scale = m.drawmapscale(lon = xmin_deg + 0.02,
                         lat = ymin_deg + 0.005,  #0.012,
                         lon0 = lng_ref, #m.llcrnrlon,
                         lat0 = lat_ref, #m.llcrnrlat,
                         barstyle = 'fancy',
                         labelstyle = 'simple',
                         length = distance,
                         yoffset = 0.01*(m.ymax-m.ymin),
                         format = '%.1f')
  scale[12].set_text(dref/2.0)
  scale[13].set_text(dref)
  
  nb_ids = len(ls_market_ids)
  subdir = 'maps_market_6_plus'
  if nb_ids < 6:
    subdir = 'maps_market_{:d}'.format(nb_ids)
  plt.savefig(os.path.join(path_dir_built_graphs,
                           directory,
                           '{:d}_{:s}_map.png'.format(nb_ids, ls_market_ids[0])),
              dpi=90,
              alpha=True,
              bbox_inches = 'tight')
  plt.close()

# Look for a market with 4 gas stations and 2 supermarkets / 2 traditional
dict_candidates = {}
for ls_market_ids in dict_robust_markets[4]:
  df_info_m = df_info.ix[ls_market_ids]
  if ((len(df_info_m[df_info_m['group_type'].isin(['SUP', 'DIS'])]) >= 2) and
      (len(df_info_m[df_info_m['group_type'].isin(['OIL', 'IND'])]) >= 2)):
    #print(df_info_m[['name', 'brand_0', 'commune']].to_string())
    #draw_market_map(ls_market_ids, 'case_study')
    #df_prices_m = df_prices_ttc[ls_market_ids]
    #df_prices_m.plot(grid = True, figsize = (18, 8))
    #plt.savefig(os.path.join(path_dir_built_graphs,
    #                             'case_study',
    #                             '{:d}_{:s}_prices.png'.format(len(ls_market_ids), ls_market_ids[0])),
    #            dpi = 200,
    #            bbox_inches = 'tight')
    #plt.close()
    dict_candidates[ls_market_ids[0]] = ls_market_ids
  if len(dict_candidates) >= 10:
    break

#draw_market_map(dict_candidates['48100001'], 'case_study', 13, delta_lat = 0.04, delta_lng = 0.05)
