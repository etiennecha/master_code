#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import numpy as np
import pandas as pd
import numpy as np
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
import simplekml

# France
x1 = -5.
x2 = 9.
y1 = 42.
y2 = 52.

m_france = Basemap(resolution='i',
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


path_dir_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')
m_france.readshapefile(path_dir_com, 'communes_fr', color = 'none', zorder=2)

ls_com = []
for com_poly, com_info in zip(m_france.communes_fr, m_france.communes_fr_info):
  com_info['poly'] = Polygon(com_poly)
  ls_com.append(com_info)
df_com = pd.DataFrame(ls_com)
ls_ign_codegeo = [unicode(codegeo) for codegeo in df_com['INSEE_COM'].values]

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_csv_insee_extract = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')
df_insee = pd.read_csv(path_csv_insee_extract, encoding = 'utf-8', dtype = str)

ls_insee_codegeo = df_insee[u'Département - Commune CODGEO'].values

ls_pbms_1 = [codegeo for codegeo in ls_insee_codegeo if codegeo not in ls_ign_codegeo]
# [u'69123', u'13055', u'76095', u'28042', u'75056'] + DOM TOM in INSEE but not in IGN
ls_pbms_2 = [codegeo for codegeo in ls_ign_codegeo if codegeo not in ls_insee_codegeo]
# Paris / Marseille / Lyon ardts not in INSEE + [u'52124', u'52266', u'52465', u'52033']

## KML COMMUNES

#kml = simplekml.Kml()
#
#for com_ind, com_row in df_com.iterrows():
#  shapely_polygon = com_row['poly']
#  outerboundary = [m_france(*point_coord, inverse = 'True')\
#                     for point_coord in list(shapely_polygon.exterior.coords)]
#  innerboundary = [m_france(*point_coord, inverse = 'True')\
#                     for point_coord in list(shapely_polygon.interiors)]
#  name = '%s (%s)' %(com_row['NOM_COMM'], com_row['INSEE_COM'])
#  pol = kml.newpolygon(name = name,
#                       outerboundaryis = outerboundary,
#                       innerboundaryis = innerboundary)
#
#kml.save(os.path.join(os.path.dirname(sys.argv[0]), 'communes.kml'))

# UNION OF POLYGONS?

pol1 = df_com['poly'][df_com['INSEE_COM'] == '92050'].values[0]  # nanterre
pol2 = df_com['poly'][df_com['INSEE_COM'] == '92063'].values[0]  # rueil
pol3 = pol1.union(pol2)

pol4 = df_com['poly'][df_com['INSEE_COM'] == '78646'].values[0]  # versailles
pol5 = pol3.union(pol4)

pol6 = df_com['poly'][df_com['INSEE_COM'] == '92076'].values[0]  # vaucresson (should connect)
pol7 = pol5.union(pol6) # seems to worl => Polygon, not MultiPolygon !

# KML UNITES URBAINES

ls_codes_uu2010 = np.unique(df_insee[u"Code géographique de l'unité urbaine UU2010"].values).tolist()
# exclude rural areas (end with '000')
ls_codes_uu2010 = [code_uu2010 for code_uu2010 in ls_codes_uu2010 if code_uu2010[-3:] != '000']

## '00851' => Paris
#code_uu2010 = '00851'
#ls_uu_codegeos = df_insee[u'Département - Commune CODGEO']\
#                   [df_insee[u"Code géographique de l'unité urbaine UU2010"] == code_uu2010].values.tolist()
#polygon_uu = df_com['poly'][df_com['INSEE_COM'] == ls_uu_codegeos[1]].values[0]
#for uu_codegeo in ls_uu_codegeos[2:]:
#  try:
#    polygon_uu = polygon_uu.union(df_com['poly'][df_com['INSEE_COM'] == uu_codegeo].values[0])
#  except:
#    print uu_cdeogeo, 'not found in df_com'
#
#kml = simplekml.Kml()
#shapely_polygon = polygon_uu
#outerboundary = [m_france(*point_coord, inverse = 'True')\
#                   for point_coord in list(shapely_polygon.exterior.coords)]
#innerboundary = [m_france(*point_coord, inverse = 'True')\
#                   for point_coord in list(shapely_polygon.interiors)]
#name = 'Paris UU'
#pol = kml.newpolygon(name = name,
#                     outerboundaryis = outerboundary,
#                     innerboundaryis = [])
#kml.save(os.path.join(os.path.dirname(sys.argv[0]), 'unites_urbaines.kml'))

kml = simplekml.Kml()
ls_uu_pbms = []
for code_uu2010 in ls_codes_uu2010:
  ls_uu_codegeos = df_insee[u'Département - Commune CODGEO']\
                     [df_insee[u"Code géographique de l'unité urbaine UU2010"] == code_uu2010].values.tolist()
  ls_uu_codegeos = [codegeo for codegeo in ls_uu_codegeos if codegeo in ls_ign_codegeo]
  if ls_uu_codegeos: 
    polygon_uu = df_com['poly'][df_com['INSEE_COM'] == ls_uu_codegeos[0]].values[0]
    for uu_codegeo in ls_uu_codegeos:
      for row_ind, row_info in df_com[df_com['INSEE_COM'] == uu_codegeo].iterrows():
        polygon_uu = polygon_uu.union(row_info['poly'])
    try: 
      shapely_polygon = polygon_uu
      name = df_insee[u"Libellé de l'unité urbaine LIBUU2010"]\
               [df_insee[u'Département - Commune CODGEO'] == uu_codegeo].values[0]
      outerboundary = [m_france(*point_coord, inverse = 'True')\
                         for point_coord in list(shapely_polygon.exterior.coords)]
      ## innerboundary: can't keep since several polygons 
      #innerboundary = [m_france(*point_coord, inverse = 'True')\
      #                   for point_coord in list(shapely_polygon.interiors)]
      pol = kml.newpolygon(name = name,
                           outerboundaryis = outerboundary,
                           innerboundaryis = [])
    except:
      ls_uu_pbms.append(code_uu2010)
kml.save(os.path.join(os.path.dirname(sys.argv[0]), 'unites_urbaines.kml'))

## List of problematic code_uu2010
#for uu_codegeo in ls_uu_pbms:
#	print df_insee[u"Libellé de l'unité urbaine LIBUU2010"]\
#          [df_insee[u"Code géographique de l'unité urbaine UU2010"] == uu_codegeo].values[0]
#df_insee[u"Libellé de la commune LIBGEO"]\
# [df_insee[u"Code géographique de l'unité urbaine UU2010"] == '27501']

# KML AIRES URBAINES

ls_codes_au2010 = np.unique(df_insee[u'Code AU2010'].values).tolist()
# '000' => those which do not belong to any AU
# '001' => Paris appears to be very very broad...

code_au2010 = ls_codes_au2010[0]
ls_au_codegeos = df_insee[u'Département - Commune CODGEO']\
                   [df_insee['Code AU2010'] == code_au2010].values.tolist()

