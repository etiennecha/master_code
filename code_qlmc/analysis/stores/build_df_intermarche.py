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

ls_intermarche_info_old = dec_json(os.path.join(path_dir_source_chains,
                                                u'list_intermarche_general_info_alt'))
ls_intermarche_info_new = dec_json(os.path.join(path_dir_source_chains,
                                                u'list_intermarche_general_info_new'))
ls_intermarche_kml = parse_kml(open(os.path.join(path_dir_source_kml,
                                                u'intermarche.kml'), 'r').read())

ls_columns = ['type', 'name', 'gps', 'street', 'zip', 'city']


# INTERMARCHE: OLD DATA + POI/KML FILE

ls_itm = ls_intermarche_info_old
ls_itm_kml = ls_intermarche_kml
ls_itm_kml_names = [x[0].decode('latin-1').lower() for x in ls_itm_kml]
ls_itm_matched_q = [x[0] for x in ls_itm if x[0].lower() in ls_itm_kml_names]
ls_itm_no_q = [x[0] for x in ls_itm if x[0].lower() not in ls_itm_kml_names]

# built df intermarche old website data
ls_itm_rows = []
for ls_store in ls_intermarche_info_old:
  street = ls_store[1].split('=')[0].rstrip(u'"').lstrip(u'"')
  street = re.split(u'[0-9]{5}', street)[0].replace(u'" ', u"'").strip()
  ls_itm_rows.append([u'Intermarché',
                     ls_store[0],
                     '',
                     street,
                     ls_store[2][0],
                     ls_store[2][1]])
df_itm = pd.DataFrame(ls_itm_rows, columns=ls_columns)
df_itm['name_2'] = df_itm['name'].apply(lambda x: standardize_intermarche(str_low_noacc(x)))
se_itm_vc = df_itm['name_2'].value_counts()
se_itm_unique = se_itm_vc[se_itm_vc == 1]
str_itm_unique = u'|'.join(se_itm_unique.index)
ls_re_replace = [[u'(', u'\('],
                 [u')', u'\)'],
                 [u'.', u'\.']]
for old, new in ls_re_replace:
  str_itm_unique = str_itm_unique.replace(old, new)
df_itm = df_itm[df_itm['name_2'].str.contains(str_itm_unique)]

# build df intermarche kml data
df_itm_kml = pd.DataFrame(ls_intermarche_kml,
                          columns = ['name', 'gps'])
df_itm_kml['name_2'] = df_itm_kml['name'].apply(lambda x: standardize_intermarche(\
                                                            str_low_noacc(x.decode('latin-1'))))
df_itm_kml['gps'] = df_itm_kml['gps'].apply(lambda y: ' '.join(\
                                              map(lambda x: u'{:2.4f}'.format(float(x)), y)))

se_itm_kml_vc = df_itm_kml['name_2'].value_counts()
se_itm_kml_unique = se_itm_kml_vc[se_itm_kml_vc == 1]
str_kml_unique = u'|'.join(se_itm_kml_unique.index)
ls_re_replace = [[u'(', u'\('],
                 [u')', u'\)'],
                 [u'.', u'\.']]
for old, new in ls_re_replace:
  str_kml_unique = str_kml_unique.replace(old, new)
df_itm_kml = df_itm_kml[df_itm_kml['name_2'].str.contains(str_kml_unique)]

# match: old intermarche website (including entity names) vs. kml
ls_itm_matched = [x for x in df_itm['name_2'].values if x in  df_itm_kml['name_2'].values]
ls_itm_no = [x for x in df_itm['name_2'].values if x not in df_itm_kml['name_2'].values]

# match 1
df_itm.index = df_itm['name_2']
df_itm_kml.index = df_itm_kml['name_2']
df_itm_all = df_itm.join(df_itm_kml, rsuffix='_kml')
#df_itm_all_o = df_itm.join(df_itm_kml, rsuffix='_kml', how='outer')
df_itm_all['gps'] = df_itm_all['gps_kml']
del(df_itm_all['gps_kml'])
# print df_itm_all[['name', 'gps', 'street', 'zip', 'city']].to_string()

# add city to df kml
def extract_gps(str_gps):
  ls_gps = re.split(u'\s+', str_gps)
  lat, lon = map(lambda x: float(x), ls_gps)
  return lat, lon

def get_locality_from_gps(lat, lon, basemap_obj, df_polygons, field_int, poly='poly'):
  poi = Point(basemap_obj(lon, lat))
  for i, x in enumerate(df_polygons['poly']):
    if poi.within(x):
      return df_polygons.iloc[i][field_int]
  return None

def gps_to_locality(str_gps, basemap_obj, df_polygons, field_int, poly='poly'):
  try:
    lat, lon = extract_gps(str_gps)
    res = get_locality_from_gps(lat, lon, basemap_obj, df_polygons, field_int, poly)
    return res
  except:
    print 'Pbm with', str_gps
    return None

# NB: can be two rows with same com_code: communes in several parts (but same commune etc)
df_itm_kml['insee_code'] = df_itm_kml['gps'].apply(\
                             lambda x: gps_to_locality(x, m_fra, df_com, 'com_code'))
df_itm_kml['city'] = df_itm_kml['insee_code'].apply(\
                       lambda x: df_com[df_com['com_code'] == x].iloc[0]['com_name'])

# match 2
# Check if more pairs can be found with city

df_itm_all = df_itm.join(df_itm_kml, rsuffix='_kml', how='outer')
# some harmonization: enough?
df_itm_all['city_noacc'] = df_itm_all['city'].apply(\
                             lambda x: str_low_noacc(x, basic_std=False)\
                               if isinstance(x, unicode) else x)

# todo: add check that city is unique
for city in df_itm_all['city_kml'][pd.isnull(df_itm_all['name'])].values:
  df_city_kml_match = df_itm_all[(pd.isnull(df_itm_all['name'])) &\
                                 (df_itm_all['city_kml'] == city)]
  df_city_match = df_itm_all[(pd.isnull(df_itm_all['city_kml'])) &\
                             (df_itm_all['city_noacc'] == city.lower())]
  if len(df_city_kml_match) == 1 and len(df_city_match) == 1:
    print '\n', city
    print df_city_kml_match.to_string(index=False, header=False)
    print df_city_match.to_string(index=False, header=False)
    # modify df kml to get better matching
    df_itm_kml['name_2'][df_itm_kml['name_2'] == df_city_kml_match['name_2_kml'].values[0]]\
       = df_city_match.index[0]

df_itm_kml.index = df_itm_kml['name_2']
df_itm_all = df_itm.join(df_itm_kml, rsuffix='_kml')
#df_itm_all_o = df_itm.join(df_itm_kml, rsuffix='_kml', how='outer')
df_itm_all['gps'] = df_itm_all['gps_kml']
del(df_itm_all['gps_kml'])

ls_disp_kml = ['name', 'name_kml', 'city', 'city_kml', 'street', 'zip', 'insee_code']
print df_itm_all[ls_disp_kml][0:10].to_string(index=False)
print len(df_itm_all[~pd.isnull(df_itm_all['gps'])])

# INTERMARCHE LATEST DATA (No gps, no entity name)

def get_itm_type(word):
  dict_itm_types = {u'logo_intermarche_Express.png' : u'Intermarché Express',
                    u'logo_intermarche_Hyper.png'   : u'Intermarché Hyper',
                    u'logo_intermarche.png'         : u'Intermarché',
                    u'logo_intermarche_Super.png'   : u'Intermarché Super',
                    u'logo_intermarche_Contact.png' : u'Intermarché Contact'}
  for itm_logo, itm_type in dict_itm_types.items():
    if itm_logo in word:
      return itm_type
  return None

ls_rows_intermarche = []
for ls_store in ls_intermarche_info_new:
  store_type = get_itm_type(ls_store[1])
  address =  [elt.replace(u'\n', u'').replace(u'\t', u'').strip() for elt in ls_store[2]\
                if elt.replace(u'\n', u'').replace(u'\t', u'').strip()]
  re_zip = re.search(u'\(([0-9]{5})\)', address[0])
  ls_rows_intermarche.append([store_type,
                              ' '.join([store_type, address[0][:re_zip.start()]]),
                              '',
                              ' '.join(address[1:]),
                              re_zip.group(1),
                              address[0][:re_zip.start()]])
df_intermarche = pd.DataFrame(ls_rows_intermarche, columns = ls_columns)
# todo: get gps for following at least...
# print df_intermarche[df_intermarche['type'] == u'Intermarché Hyper'].to_string()

# match 2: old website with kml vs. new website (including type of supermarket)

# clean street in itm
def clean_itm_street(word):
  ls_replace = [[u'\n', u''],
                [u'\t', u''],
                [u"'",  u' '],
                [u'"',  u' ']]
  for old, new in ls_replace:
    word = word.replace(old, new)
  word = u' '.join([x for x in word.split(u' ') if x])
  return word

df_itm_all['street'] = df_itm_all['street'].apply(lambda x: clean_itm_street(x).lower())
df_intermarche['street'] = df_intermarche['street'].apply(lambda x: clean_itm_street(x).lower())

df_intermarche['street_zip'] = df_intermarche['street'] + u' ' + df_intermarche['zip']
df_itm_all['street_zip'] = df_itm_all['street'] + u' ' + df_itm_all['zip']
ls_itm_matched_2 = [x for x in df_intermarche['street_zip'].values\
                      if x in df_itm_all['street_zip'].values]
ls_itm_no_2 = [x for x in df_intermarche['street_zip'].values\
                 if x not in df_itm_all['street_zip'].values]

df_itm_all.set_index('street_zip', inplace = True)
df_intermarche.set_index('street_zip', inplace = True)
df_intermarche_all = df_intermarche.join(df_itm_all[['name', 'gps', 'city']],
                                         rsuffix='_o',
                                         how = 'outer')
df_intermarche_all.reset_index(drop = True, inplace = True)

pd.set_option('display.max_colwidth', 30)
ls_disp_itm = ['name', 'street', 'zip', 'city', 'name_o', 'gps', 'city_o']
# print df_intermarche_all[ls_disp_itm][0:100].to_string()

# df_intermarche_all.drop(['name_o', 'city_o', 'gps'], 1, inplace = True)
df_intermarche_all.drop(['gps'], 1, inplace = True)
df_intermarche_all.rename(columns = {'gps_o' : 'gps'}, inplace = True)

# Result for first matching
print 'First matching'
print len(df_intermarche_all[(~pd.isnull(df_intermarche_all['name_o'])) &\
                             (~pd.isnull(df_intermarche_all['gps']))])

# Result for full matching
print 'Full matching'
len(df_intermarche_all[(~pd.isnull(df_intermarche_all['type'])) &\
                        (~pd.isnull(df_intermarche_all['gps']))])

### CONTROLS
##df_itm_all.reset_index(drop = True, inplace = True)
##df_itm_all[df_itm_all['city'] == 'volgelsheim']
#print df_intermarche_all[ls_disp_itm][(pd.isnull(df_intermarche_all['type'])) &\
#                                      (~pd.isnull(df_intermarche_all['gps']))].to_string()

# can check a posteriori with reverse geocoding
