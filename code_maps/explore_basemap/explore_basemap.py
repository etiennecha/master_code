#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json
# from lxml import etree
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
# import fiona
# import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

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
  
  # #######
  # LONDON
  # #######
  
  # tree = etree.parse(path_data + r'\data_maps\london_plaques_20130119.xml')
  # root = tree.getroot()
  # output = dict()
  # output['raw'] = []
  # output['crs'] = []
  # output['lon'] = []
  # output['lat'] = []
  # for each in root.xpath('/openplaques/plaque/geo'):
    # # check what we got back
    # output['crs'].append(each.get('reference_system'))
    # output['lon'].append(each.get('longitude'))
    # output['lat'].append(each.get('latitude'))
    # # now go back up to plaque
    # r = each.getparent().xpath('inscription/raw')[0]
    # if isinstance(r.text, str):
      # output['raw'].append(r.text.lstrip().rstrip())
    # else:
      # output['raw'].append(None)
  # df = pd.DataFrame(output)
  # df = df.replace({'raw': 0}, None)
  # df = df.dropna()
  # df[['lon', 'lat']] = df[['lon', 'lat']].astype(float)
  
  # path_london = r'\data_maps\london'
  # sf_london = shapefile.Reader(path_data + path_london + r'\london_wards.shp')
  # shapes_london = sf_london.shapes()
  
  # # Europe
  # x1 = -20.
  # x2 = 40.
  # y1 = 32.
  # y2 = 64.
  
  # # tmerc requires lon_0, lat_0, merc probably does not (?)
  # m = Basemap(resolution='i',
              # projection='tmerc',
              # lon_0 = -2.,
              # lat_0 = 49.,
              # ellps = 'WGS84',
              # llcrnrlat=y1,
              # urcrnrlat=y2,
              # llcrnrlon=x1,
              # urcrnrlon=x2,
              # lat_ts=(x1+x2)/2,
              # suppress_ticks = True)
  
  # m.readshapefile(path_data + path_london + '\london_wards',
                  # 'london',
                  # color = 'none',
                  # zorder = 2)        
  
  # # set up a map dataframe
  # df_map = pd.DataFrame({'poly': [Polygon(xy) for xy in m.london],
                         # 'ward_name': [w['NAME'] for w in m.london_info],})
  # df_map['area_m'] = df_map['poly'].map(lambda x: x.area)
  # df_map['area_km'] = df_map['area_m'] / 100000
  
  # # Create Point objects in map coordinates from dataframe lon and lat values
  # map_points = pd.Series([Point(m(mapped_x, mapped_y)) for mapped_x, mapped_y in zip(df['lon'], df['lat'])])
  # plaque_points = MultiPoint(list(map_points.values))
  # wards_polygon = prep(MultiPolygon(list(df_map['poly'].values)))
  # # calculate points that fall within the London boundary
  # ldn_points = filter(wards_polygon.contains, plaque_points)
  
  # ######
  # ROUTES
  # ######
  
  path_route_120 = r'\data_maps\ROUTE120_WGS84'
  path_route_500 = r'\data_maps\ROUTE500_WGS84'
  path_dpt =  r'\data_maps\GEOFLA_DPT_WGS84'
  path_commune = r'\data_maps\GEOFLA_COM_WGS84'
  
  # # Example of shp file reading using shapefile (works also with IGN lambert 93 files)
  # sf_route = shapefile.Reader(path_data + path_route_120 + r'\TRONCON_ROUTE.SHP')
  # fields_route = sf_route.fields
  # records_route = sf_route.records()
  # shapes_route = sf_route.shapes()
  # shapes_route[0].bbox
  # shapes_route[0].parts
  # shapes_route[0].points
  # shapes_route[0].shapeType
  
  # # IGN Lambert 93 files can be read directly
  # path_route_500_l = r'\data_maps\ROUTE500_1-1_SHP_LAMB93_000_2012-11-23\ROUTE500'+\
                     # r'\1_DONNEES_LIVRAISON_2012-11-00093\R500_1-1_SHP_LAMB93_FR-ED121\RESEAU_ROUTIER'
  # shp_route_500_l = shapefile.Reader(path_data + path_route_500_l + r'\TRONCON_ROUTE.SHP')
  # shapes_route_500 = shp_route_500_l.shapes()
  # records_route_500 = shp_route_500_l.records()
  # print shapes_route_500[0].points
  
  # TODO: test fiona at home
  # shp_route_500_l = fiona.open(path_data + path_route_500_l + r'\TRONCON_ROUTE.SHP')
  
  # France
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
  
  # m_route.readshapefile(path_data + path_route_120 + '\TRONCON_ROUTE', 'routes_fr', color = 'none', zorder=2)
  # m_route.readshapefile(path_data + path_route_120 + '\COMMUNE', 'communes_fr', color = 'none', zorder=2)
  m_route.readshapefile(path_data + path_route_500 + '\TRONCON_ROUTE', 'routes_fr', color = 'none', zorder=2)
  m_route.readshapefile(path_data + path_route_500 + '\TRONCON_ROUTE', 'routes_fr', color = 'none', zorder=2)
  m_route.readshapefile(path_data + path_dpt + '\DEPARTEMENT', 'departements_fr', color = 'none', zorder=2)
  
  
  # # Test of accuracy : distance measure
  # [u'1500007', u'1500001'], 1.2799999713897705] <= [45.97268, 5.33747], [45.96952, 5.35345]
  # [[u'1500007', u'1150001'], 7.909999847412109] <= [45.97268, 5.33747], [45.9018, 5.34553]
  # print Point(m_route(5.33747, 45.97268)).distance(Point(m_route(5.35345, 45.96952)))
  # print Point(m_route(5.33747, 45.97268)).distance(Point(m_route(5.34553, 45.9018 )))
  
  # # Test of accuracy : comparison vs. original insee data
  # print shapes_route_500[0].points
  # print m_route.routes_fr_500[0]
  
  # In order to get back to IGN LAMBERT 93 initial coordinates due to
  # 1/ Basemap always sets (0,0) for lower left corner (offset middle)
  # 2/ IGN standard, false easting 700 000, false northing 6 600 000
  # x_l_93_ign = x + 700000 - m_route(3, 46.5)[0]
  # y_l_93_ign = y + 6600000 - m_route(3, 46.5)[1]
  
  # TODO: replicate for COMMUNE (essentially the same process)
  df_dpt = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_route.departements_fr],
                         'dpt_name' : [d['NOM_DEPT'] for d in m_route.departements_fr_info],
                         'dpt_code' : [d['CODE_DEPT'] for d in m_route.departements_fr_info],
                         'region_name' : [d['NOM_REGION'] for d in m_route.departements_fr_info],
                         'region_code' : [d['CODE_REG'] for d in m_route.departements_fr_info]})
  # print df_dpt[['code_dpt', 'dpt_name','code_region', 'region_name']].to_string()
  # Some regions must be broken in mult polygons: appear mult times (138 items, all France Metr)
  region_multipolygon = MultiPolygon(list(df_dpt[df_dpt['region_name'] == "NORD-PAS-DE-CALAIS"]['poly'].values))
  region_multipolygon_prep = prep(region_multipolygon)
  region_bounds = region_multipolygon.bounds
  
  # ############
  # LOCAL GRAPHS
  # ############
  
  # # 1/ ROADS (OK SO FAR)
  # # TODO: improve efficiency: db once and for all with dummies per region/dpt (?)
  for shape_dict, shape in zip(m_route.routes_fr_info, m_route.routes_fr):
    if not region_multipolygon.disjoint(MultiPoint(shape)):
      xx, yy = zip(*shape)
      if shape_dict['CLASS_ADM'] == 'Autoroute':
        temp = m_route.plot(xx, yy, linewidth = 0.6, color = 'b')
      elif shape_dict['CLASS_ADM'] == 'Nationale':
        temp = m_route.plot(xx, yy, linewidth = 0.5, color = 'r')
      elif shape_dict['CLASS_ADM'] == 'D\xe9partementale':
        temp = m_route.plot(xx, yy, linewidth = 0.2, color = 'c')
      else:
        temp = m_route.plot(xx, yy, linewidth = 0.1, color = 'k')
  # m_route.drawcountries()
  # m_route.drawcoastlines()
  # plt.xlim((region_bounds[0], region_bounds[2]))
  # plt.ylim((region_bounds[1], region_bounds[3]))
  # plt.savefig(path_data + r'\data_maps\graphs\test.png' , dpi=700)
  # # plt.show()
  
  # 2/ GAS STATIONS
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline\master_diesel'
  folder_source_brand = r'\data_gasoline\data_source\data_stations\data_brands'
  master_price = dec_json(path_data + folder_built_master_json + r'\master_price')
  master_info_temp = dec_json(path_data + folder_built_master_json + r'\master_info_for_output')
  dict_brands = dec_json(path_data + folder_source_brand + r'\dict_brands')
  list_gps = []
  list_names = []
  list_brands = []
  list_types = []
  for indiv_id, gas_station in master_info_temp.iteritems():
    gps = gas_station['gps'][-1]
    name, brand, type_br = None, None, None
    if master_price['dict_info'].get(indiv_id, None):
      name = master_price['dict_info'][indiv_id]['name']
      brand = dict_brands[get_str_no_accent_up(master_price['dict_info'][indiv_id]['brand'][0][0])][0]
      type_br = dict_brands[get_str_no_accent_up(master_price['dict_info'][indiv_id]['brand'][0][0])][2]
    if gps:
      list_gps.append(gps)
      list_names.append(name)
      list_brands.append(brand)
      list_types.append(type_br)
  df_gas_stations = pd.DataFrame({'point': [Point(m_route(gps[1], gps[0])) for gps in list_gps],
                                  'name' : list_names,
                                  'brand': list_brands,
                                  'type': list_types})
  # TODO: distinguish types by color
  # http://stackoverflow.com/questions/12965075/matplotlib-scatter-plot-colour-as-function-of-third-variable
  # woulbe be for continuous.. e.g. price
  df_gas_stations['type'] = df_gas_stations['type'].map(lambda x: x if x else 'NA')
  dev = m_route.scatter([station.x for station in df_gas_stations[df_gas_stations['type']=='OIL']['point']],
                        [station.y for station in df_gas_stations[df_gas_stations['type']=='OIL']['point']],
                        3, marker = 'D', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
                        antialiased = True, zorder = 3)
  dev = m_route.scatter([station.x for station in df_gas_stations[df_gas_stations['type']=='SUP']['point']],
                        [station.y for station in df_gas_stations[df_gas_stations['type']=='SUP']['point']],
                        3, marker = 'o', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
                        antialiased = True, zorder = 3)
  dev = m_route.scatter([station.x for station in df_gas_stations[df_gas_stations['type']=='IND']['point']],
                        [station.y for station in df_gas_stations[df_gas_stations['type']=='IND']['point']],
                        3, marker = 'v', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
                        antialiased = True, zorder = 3)
  dev = m_route.scatter([station.x for station in df_gas_stations[df_gas_stations['type']=='NA']['point']],
                        [station.y for station in df_gas_stations[df_gas_stations['type']=='NA']['point']],
                        3, marker = '+', lw=0.25, facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
                        antialiased = True, zorder = 3)
  m_route.drawcountries()
  m_route.drawcoastlines()
  plt.xlim((region_bounds[0], region_bounds[2]))
  plt.ylim((region_bounds[1], region_bounds[3]))
  plt.savefig(path_data + r'\data_maps\graphs\test.png' , dpi=700)
  
  # #############
  # GLOBAL GRAPHS
  # #############
  
  # TODO: aggregate (heatmap etc)
  
  # QUERIES
  # #######
  
  # TODO: All
  # TODO: global/local (?): neighbour to big road/many roads
  
  # ######
  # OSM
  # ######
  
  # path_osm_geofabrik_fr  = r'\data_maps\OSM_France'
  
  # # France
  # x1 = -5.
  # x2 = 9.
  # y1 = 42.
  # y2 = 52.
  
  # # Lambert conformal for France (as suggested by IGN... check WGS84 though?)
  # m_osm_geo_fr =  Basemap(resolution='i',
                      # projection='lcc',
                      # ellps = 'WGS84',
                      # lat_1 = 44.,
                      # lat_2 = 49.,
                      # lat_0 = 46.5,
                      # lon_0 = 3,
                      # llcrnrlat=y1,
                      # urcrnrlat=y2,
                      # llcrnrlon=x1,
                      # urcrnrlon=x2)
  
  # path_osm_fr_region = path_data + path_osm_geofabrik_fr + r'\Nord_Pas_de_Calais'
  # m_osm_fr.readshapefile(path_osm_fr_region + r'\places', 'places', color = 'none', zorder=2)
  # m_osm_fr.readshapefile(path_osm_fr_region + r'\landuse', 'landuse', color = 'none', zorder=2)
  # m_osm_fr.readshapefile(path_osm_fr_region + r'\roads', 'roads', color = 'none', zorder=2)
  # m_osm_fr.readshapefile(path_osm_fr_region + r'\natural', 'natural', color = 'none', zorder=2)
  
  # df_landuse = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_osm_fr.landuse],
                             # 'type' : [elt['type'] for elt in m_osm_fr.landuse_info],
                             # 'name' : [elt['name'] for elt in m_osm_fr.landuse_info]})
  # # print np.unique(df_landuse['type'].values)
  # df_landuse['patches'] = df_landuse['poly'].map(lambda x: PolygonPatch(x,
                                                                        # fc='#555555',
                                                                        # ec='#787878',
                                                                        # lw=.25,
                                                                        # alpha=.9,
                                                                        # zorder=4))
  # fig, ax = plt.subplots()
  # m_osm_fr.drawcountries()
  # m_osm_fr.drawcoastlines()
  # ax.add_collection(PatchCollection(df_landuse['patches'].values, match_original=True))
  # plt.show()
  
  # osmread parsing test => use imposm at home (need to compile)
  # path_osm_pbf = path_data + r'\data_maps\nord-pas-de-calais-latest.osm.pbf'
