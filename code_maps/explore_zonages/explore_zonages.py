#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
#import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
#from pysal.esda.mapclassify import Natural_Breaks as nb
from matplotlib import colors

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

# LAMBERT ETENDU (OLD?)

def convert_to_lambert(x, y):
  # returns coordinates in meters
  x_l = (m_fra(x, y)[0] + 600000 - m_fra(2.34, 46.8)[0])
  y_l = (m_fra(x, y)[1] + 2200000 - m_fra(2.34, 46.8)[1])
  return x_l, y_l

def convert_from_lambert(x_l, y_l):
  # takes coordinates in meters
  x = x_l - 600000 + m_fra(2.34, 46.8)[0] 
  y = y_l - 2200000 + m_fra(2.34, 46.8)[1]
  x, y = m_fra(x, y, inverse = True)
  return x, y

path_dir_zonages = os.path.join(path_data,
                                'data_maps',
                                'France_zonages_2008')

# #############
# LOAD FRANCE
# #############

# excludes Corsica
x1 = -5.
x2 = 9.
y1 = 42
y2 = 52.

# Lambert conformal for France (as suggested by IGN... check WGS84 though?)
# http://geodesie.ign.fr/contenu/fichiers/documentation/pedagogiques/TransformationsCoordonneesGeodesiques.pdf

# Lamber (old ?)
m_fra = Basemap(resolution='i',
                projection='lcc',
                ellps = 'WGS84',
                lat_1 = 45.9,
                lat_2 = 47.7,
                lat_0 = 46.8,
                lon_0 = 2.34,
                llcrnrlat=y1,
                urcrnrlat=y2,
                llcrnrlon=x1,
                urcrnrlon=x2)

## need to preprocess... or use shapefile
#m_fra.readshapefile(os.path.join(path_dir_zonages, 'zus'),
#                    'zus',
#                    color = 'none',
#                    zorder = 2)


file_name = 'zus' #'perimetre_massif'

import shapefile
sf = shapefile.Reader(os.path.join(path_dir_zonages, file_name))
shapes = sf.shapes()

print sf.fields
print len(sf.records())
print sf.record(0)
print sf.shape(0).points

#lng, lat = m_fra(*sf.shape(0).points[0], inverse = True)
lng, lat = convert_from_lambert(*sf.shape(0).points[0])
print lat, lng

ls_rows = []
for i in range(len(sf.records())):
  coord_gps = convert_from_lambert(*sf.shape(i).points[0])
  coord_bm  = m_fra(*coord_gps)
  zus_info = map(lambda x: x.decode('latin-1'), sf.record(i))
  ls_rows.append([coord_gps, coord_bm] + zus_info)
df_zus = pd.DataFrame(ls_rows, columns = ['ct_gps', 'ct_bm', 'insee_code', 'zus_city'])

# hehe.. seems not lambert etendu.. lambert with all zones and corsica is a pbm?
df_zus_mainland = df_zus[~df_zus['insee_code'].str.startswith('97')].copy()
m_fra.scatter([row['ct_bm'][0] for row_ind, row in df_zus_mainland.iterrows()],
              [row['ct_bm'][1] for row_ind, row in df_zus_mainland.iterrows()],
              color = 'b', lw=0.8, alpha = 0.3)

m_fra.drawcountries()
m_fra.drawcoastlines()
plt.show()

print df_zus_mainland[['zus_city', 'insee_code', 'ct_gps']].to_string()

def conv_gps_to_str(gps):
  return ' '.join(map(lambda x: u'{:.3f}'.format(x), gps[::-1]))

df_zus_mainland['ct_gps'] = df_zus_mainland['ct_gps'].apply(lambda x: conv_gps_to_str(x))
df_zus_mainland[['zus_city', 'insee_code', 'ct_gps']].to_csv('W:\Bureau\zus_test.csv',
                                                             float_format= '%.3f',
                                                             encoding = 'utf-8')

# gaps appear.. might be due to imprecision in computations or use of each lambert area
# can see with http://sig.ville.gouv.fr/Atlas/ZUS/
