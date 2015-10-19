#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
from geocoding import *
import numpy as np
import pandas as pd
import pprint
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
#import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
from pysal.esda.mapclassify import Natural_Breaks as nb
from matplotlib import colors

path_built = os.path.join(path_data,
                          u'data_ameli',
                          u'data_built')
path_built_csv = os.path.join(path_built, 'data_csv')
path_built_json = os.path.join(path_built, u'data_json')

path_dir_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')

# DF OPHTALMO 75

file_extension = u'ophtalmologiste_75_2014'
ls_ls_physicians = dec_json(os.path.join(path_built_json,
                                         '%s.json' %file_extension))
dict_gps_physicians = dec_json(os.path.join(path_built_json,
                                            'dict_gps_%s.json' %file_extension))
for i, ls_physician in enumerate(ls_ls_physicians):
  best_geo = get_best_google_geocoding_info(dict_gps_physicians[ls_physician[0]][1])
  if best_geo:
    lat = best_geo['results'][0]['geometry']['location']['lat']
    lng = best_geo['results'][0]['geometry']['location']['lng']
  else:
    lat, lng = np.nan, np.nan
  ls_ls_physicians[i] += [lat, lng]

ls_columns = ['id_physician', 'gender', 'name', 'surname',
              'street', 'zip_city', 'convention', 'carte_vitale', 'status',
              'injection_med', 'examen_mot', 'imagerie', 'traitement_las',
              'fond', 'examen_vis', 'chirurgie_cat', 'consultation', 'avis']
df_physicians = pd.DataFrame(ls_ls_physicians, columns = ls_columns + ['x', 'y', 'z', 'lat', 'lng'])
df_physicians.index = df_physicians['id_physician']
# do the following after geocoding?
df_physicians.to_csv(os.path.join(path_built_csv,
                                  '%s.csv' %file_extension),
                     float_format = '%.3f',
                     index = False)

# MAP OF PARIS

# Rendering not to nice: would like to see Seine, Periph, railway etc...
# Ok for aggregate info (e.g. density / dpt)
# Else rather use GFT or Leaflet

# Paris (limits of suburb?)
x1 = 2.2294
x2 = 2.4688
y1 = 48.8148
y2 = 48.9047

w = x2 - x1
h = y2 - y1
extra = 0.025

# Lambert conformal for France (as suggested by IGN... check WGS84 though?)
m_fra = Basemap(resolution='i',
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


m_fra.readshapefile(path_dir_com, 'communes_fr', color = 'none', zorder=2)

# DF COM
ls_com = []
for com_poly, com_info in zip(m_fra.communes_fr, m_fra.communes_fr_info):
  com_info['poly'] = Polygon(com_poly)
  ls_com.append(com_info)
df_com = pd.DataFrame(ls_com)
df_com['patches'] = df_com['poly'].map(lambda x: PolygonPatch(x,
                                                              facecolor='#FFFFFF', # '#555555'
                                                              edgecolor='#555555', # '#787878'
                                                              lw=.25, alpha=.3, zorder=1))

# DF PHYSICIANS: CREATE POINTS
df_physicians['point'] = df_physicians[['lng', 'lat']].apply(\
                           lambda x: Point(m_fra(x[0], x[1])),
                                           axis = 1)

plt.clf()
fig = plt.figure()
ax = fig.add_subplot(111, axisbg = 'w', frame_on = False)

dev = m_fra.scatter([phys.x for phys in df_physicians['point']],
                    [phys.y for phys in df_physicians['point']],
                    8, marker = 'D', lw=0.25,
                    facecolor = '#000000', edgecolor = 'w', alpha = 0.9,
                    antialiased = True, zorder = 3)

ax.add_collection(
      PatchCollection(\
        df_com[df_com['INSEE_COM'].str.slice(stop=2) == '75']['patches'].values,
        match_original = True))

ax.add_collection(PatchCollection(df_com[df_com['NOM_DEPT'] == "PARIS"]['patches'].values,
                                  match_original = True))

m_fra.drawcountries() # necessary to have map displayed if only add_collection (dunno why?)
plt.show()
