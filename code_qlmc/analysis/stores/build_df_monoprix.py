#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import *
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PatchCollection
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
import pprint

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_source_json = os.path.join(path_dir_qlmc, 'data_source', 'data_json_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_source_chains = os.path.join(path_dir_qlmc, 'data_source', 'data_chain_websites')
path_dir_source_kml = os.path.join(path_dir_qlmc, 'data_source', 'data_kml')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')

# LOAD COMMUNES

# todo: Use basemap: either IGN Geo or Routes (?)
# todo: Beware to display all stores when several in a town!

# France
x1, x2, y1, y2 = -5.0, 9.0, 42.0, 52.0

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

path_dir_geofla = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84')
m_fra.readshapefile(os.path.join(path_dir_geofla, 'COMMUNE'), u'communes_fr',
                    color = 'none', zorder=2)

df_com = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.communes_fr],
                       'com_name' : [d['NOM_COMM'] for d in m_fra.communes_fr_info],
                       'com_code' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.communes_fr_info],
                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.communes_fr_info],
                       'reg_name' : [d['NOM_REGION'] for d in m_fra.communes_fr_info],
                       'reg_code' : [d['CODE_REG'] for d in m_fra.communes_fr_info]})

# READ INTERMARCHE DATA

ls_monoprix_general_info = dec_json(os.path.join(path_dir_source_chains,
                                                u'list_monoprix_general_info'))
ls_monoprix_kml = parse_kml(open(os.path.join(path_dir_source_kml,
                                                u'monoprix.kml'), 'r').read())

# build df monoprix
ls_columns = ['type', 'name', 'gps', 'street', 'zip', 'city']
ls_rows_monoprix = []
for ls_store in ls_monoprix_general_info:
  ls_rows_monoprix.append([ls_store[0],
                           ls_store[1],
                           '',
                           ls_store[3][2],
                           ls_store[3][1],
                           ls_store[3][0]])
df_monoprix = pd.DataFrame(ls_rows_monoprix, columns = ls_columns)


# build df kml

ls_monoprix_kml_types = [u'SUPER MONOPRIX',
                         u'MONOPRIX',
                         u'BEAUTY MONOP',
                         u"MONOP'",
                         u'INNO']

df_monoprix_kml = pd.DataFrame(ls_monoprix_kml,
                               columns = ['name', 'gps'])
df_monoprix_kml['name_2'] = df_monoprix_kml['name'].apply(lambda x: standardize_intermarche(\
                                                            str_low_noacc(x.decode('latin-1'))))
df_monoprix_kml['gps'] = df_monoprix_kml['gps'].apply(lambda y: ' '.join(\
                                              map(lambda x: u'{:2.4f}'.format(float(x)), y)))
# print df_monoprix_kml.to_string()

# todo: only for unique names (disregard type, hope won't be a pbm else???)
# match on names... geocode remaining (check address)
