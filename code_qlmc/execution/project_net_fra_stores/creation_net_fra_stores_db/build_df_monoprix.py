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

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

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

# BUILD DF MONOPRIX
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
df_monoprix['name_2'] = df_monoprix.apply(\
                           lambda x: x['name'][len(x['type'])+1:]\
                                       if re.match(x['type'], x['name']) else None, axis = 1)
df_monoprix['name_2'] = df_monoprix['name_2'].apply(\
                          lambda x: x.encode('raw_unicode_escape').decode('utf-8').upper())

## Représentation unicode ds chaine unicode...
# v = u'Monoprix ASNIERES MARCH\xc3\xa9'.encode('raw_unicode_escape')
# v.decode('utf-8')

# BUILD DF MONOPRIX KML
ls_monoprix_kml_types = [u'SUPER MONOPRIX',
                         u'MONOPRIX',
                         u'BEAUTY MONOP',
                         u"MONOP'",
                         u'INNO']

ls_monoprix_kml_clean = []
for monoprix_kml in ls_monoprix_kml:
  for kml_type in ls_monoprix_kml_types:
    monoprix_kml_2 = [monoprix_kml[0].decode('latin-1'), monoprix_kml[1]]
    if re.match(kml_type, monoprix_kml_2[0]):
      store_type, store_city = kml_type, monoprix_kml_2[0][len(kml_type)+1:].strip()
  ls_monoprix_kml_clean.append([store_type, store_city,  monoprix_kml_2[1]])

df_monoprix_kml = pd.DataFrame(ls_monoprix_kml_clean,
                               columns = ['type', 'name', 'gps'])

df_monoprix_kml['gps'] = df_monoprix_kml['gps'].apply(lambda y: ' '.join(\
                                              map(lambda x: u'{:2.4f}'.format(float(x)), y)))
#df_monoprix_kml['city'] = df_monoprix_kml['city'].apply(lambda x: standardize_intermarche(\
#                                                            str_low_noacc(x.decode('latin-1'))))
## print df_monoprix_kml.to_string()

# todo: corre following
ls_replace_name_kml = [[u'ANNECY Courrier', 'ANNECY Courier']]

# MATCHING MONOPRIX VS. MONOPRIX KML
df_monoprix_kml.sort('name', inplace = True)
df_monoprix.sort('name_2', inplace = True)

se_monoprix_vc = df_monoprix['name_2'].value_counts()
se_monoprix_unique = se_monoprix_vc[se_monoprix_vc == 1]
str_monoprix_unique = u'|'.join(se_monoprix_unique.index)
ls_re_replace = [[u'(', u'\('],
                 [u')', u'\)'],
                 [u'.', u'\.']]
for old, new in ls_re_replace:
  str_monoprix_unique = str_monoprix_unique.replace(old, new)
df_monoprix_unique = df_monoprix[df_monoprix['name_2'].str.contains(str_monoprix_unique)]

se_monoprix_kml_vc = df_monoprix_kml['name'].value_counts()
se_monoprix_kml_unique = se_monoprix_kml_vc[se_monoprix_kml_vc == 1]
str_monoprix_kml_unique = u'|'.join(se_monoprix_kml_unique.index)
ls_re_replace = [[u'(', u'\('],
                 [u')', u'\)'],
                 [u'.', u'\.']]
for old, new in ls_re_replace:
  str_monoprix_kml_unique = str_monoprix_kml_unique.replace(old, new)
df_monoprix_kml_unique =\
  df_monoprix_kml[df_monoprix_kml['name'].str.contains(str_monoprix_kml_unique)]

df_monoprix_unique.index = df_monoprix_unique['name_2']
df_monoprix_kml_unique.index = df_monoprix_kml_unique['name'].str.upper()
df_monoprix_all = df_monoprix_unique.join(df_monoprix_kml_unique,
                                          rsuffix = u'_kml',
                                          how='outer')
df_monoprix_all['gps'] = df_monoprix_all['gps_kml']
del(df_monoprix_all['gps_kml'])

pd.set_option('display.max_colwidth', 30)
ls_disp_all = ['type', 'name_2', 'street', 'zip', 'city', 'type_kml', 'name_kml', 'gps']
print df_monoprix_all[ls_disp_all].to_string(index=False)

# Check loss: 246 gps matched out of 283 available from kml... ok
print len(df_monoprix_kml)
print len(df_monoprix_all[(~pd.isnull(df_monoprix_all['type'])) &\
                          (~pd.isnull(df_monoprix_all['gps']))])

# Match with original df_monoprix on name_2 (since no duplicates in df_monoprix_all)
df_monoprix_all = df_monoprix_all[~pd.isnull(df_monoprix_all['type'])]
del(df_monoprix['gps'])
df_monoprix.index = df_monoprix['name_2']
df_monoprix_final = df_monoprix.join(df_monoprix_all[['gps']])

# todo: only for unique names (disregard type, hope won't be a pbm else???)
# match on names... geocode remaining (check address)

df_monoprix_final.drop(['name_2'], axis = 1, inplace=True)

fra_stores = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'fra_stores.h5'))
fra_stores['df_monoprix'] = df_monoprix_final
fra_stores.close()
