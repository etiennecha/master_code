#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_maps import *
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from descartes import PolygonPatch

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                        'data_csv')

path_insee = os.path.join(path_data, 'data_insee')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

path_maps = os.path.join(path_data,
                         'data_maps')
path_geo_dpt = os.path.join(path_maps, 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_geo_com = os.path.join(path_maps, 'GEOFLA_COM_WGS84', 'COMMUNE')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DATA
# ##############

# LOAD LSA STORE DATA
df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa_active_hsx.csv'),
                     dtype = {u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

df_lsa = df_lsa[(~pd.isnull(df_lsa['latitude'])) &\
                (~pd.isnull(df_lsa['longitude']))].copy()

# LOAD INSEE MUNICIPALITY DATA
df_com_insee = pd.read_csv(os.path.join(path_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'utf-8')

df_com_insee.set_index('CODGEO', inplace = True)

# LOAD GEO FRANCE
geo_france = GeoFrance(path_dpt = path_geo_dpt,
                       path_com = path_geo_com)
df_com = geo_france.df_com

# KEEP ONLY ONE LINE PER MUNICIPALITY (several polygons for some)
df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)
# keep largest area (todo: sum)
df_com.sort(columns = ['c_insee', 'poly_area'],
            ascending = False,
            inplace = True)
df_com.drop_duplicates(['c_insee'], inplace = True, take_last = False)

# GET GPS COORD OF MUNICIPALITY CENTER

# two centers available: centroid of polygon and town hall
print u'\nTest with commune', df_com['commune'].iloc[0]
x_test, y_test = df_com['x_ct'].iloc[0], df_com['y_ct'].iloc[0]
print geo_france.convert_ign_to_gps(x_test, y_test)

df_com[['lng_ct', 'lat_ct']] = df_com[['x_ct', 'y_ct']].apply(\
                                 lambda x: geo_france.convert_ign_to_gps(x['x_ct'],\
                                                                         x['y_ct']),\
                                 axis = 1)

df_com[['lng_cl', 'lat_cl']] = df_com[['x_cl', 'y_cl']].apply(\
                                 lambda x: geo_france.convert_ign_to_gps(x['x_cl'],\
                                                                         x['y_cl']),\
                                 axis = 1)

# Round gps coord
for col in ['lng_ct', 'lat_ct', 'lng_cl', 'lat_cl']:
  df_com[col] = np.round(df_com[col], 3)

df_com_insee = pd.read_csv(os.path.join(path_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'UTF-8')
df_com_insee.set_index('CODGEO', inplace = True)

# Check correspondence between INSEE and IGN
df_com_insee_fm = df_com_insee[~df_com_insee['DEP'].isin(['2A', '2B', '97'])].copy()
print df_com[~df_com['c_insee'].isin(df_com_insee_fm.index)].to_string()

df_com.set_index('c_insee', inplace = True)
## Overwrite IGN pop with INSEE pop (dates?)
#df_com['pop'] = df_com_insee['P10_POP']

ls_rows_hhi = []
for row_ind, row in df_com.iterrows():
  df_lsa_temp = df_lsa.copy()
  df_lsa_temp['lat_com'] = row['lat_cl']
  df_lsa_temp['lng_com'] = row['lng_cl']
  df_lsa_temp['dist'] = compute_distance_ar(df_lsa_temp['latitude'],
                                            df_lsa_temp['longitude'],
                                            df_lsa_temp['lat_com'],
                                            df_lsa_temp['lng_com'])
  # continous method (could add max group share)
  df_lsa_temp['wgtd_surface'] = np.exp(-df_lsa_temp['dist']/10) * df_lsa_temp['surface']
  wgtd_surface = df_lsa_temp['wgtd_surface'].sum()
  df_hhi = df_lsa_temp[['groupe', 'wgtd_surface']].groupby('groupe').agg([sum])['wgtd_surface']
  df_hhi['market_share'] = df_hhi['sum'] / df_hhi['sum'].sum()
  hhi = (df_hhi['market_share']**2).sum()
  # ac method (could add max group share + nb groups)
  df_lsa_ac = df_lsa_temp[((df_lsa_temp['dist'] <= 25) &\
                           (df_lsa_temp['type_alt'] == 'H')) |
                          ((df_lsa_temp['dist'] <= 10) &\
                           (df_lsa_temp['type_alt'].isin(['S', 'X'])))].copy()
  ac_store_surf = df_lsa_ac['surface'].sum()
  ac_nb_groups = len(df_lsa_ac['groupe'].unique())
  df_ac_hhi = df_lsa_ac[['groupe', 'surface']].groupby('groupe').agg([sum])['surface']
  df_ac_hhi['market_share'] = df_ac_hhi['sum'] / df_ac_hhi['sum'].sum()
  ac_hhi = (df_ac_hhi['market_share']**2).sum()
  ac_cr1 = df_ac_hhi['market_share'].max()
  ls_rows_hhi.append((row_ind, wgtd_surface, hhi,
                      ac_nb_groups, ac_cr1, ac_store_surf, ac_hhi))

ls_columns = ['c_insee', 'wgtd_surface', 'hhi',
              'ac_nb_groups', 'ac_cr1', 'ac_store_surf', 'ac_hhi']

df_hhi = pd.DataFrame(ls_rows_hhi, columns = ls_columns)
df_hhi.set_index('c_insee', inplace = True)

#df_com = pd.merge(df_com,
#                  df_hhi,
#                  how = 'left',
#                  right_index = True,
#                  left_index = True)
#
#df_com['hhi'] = df_com['hhi'] * 10000
#df_com['ac_hhi'] = df_com['ac_hhi'] * 10000
#
## Add DEP and REG... five are not in insee data: nouvelles communes...
#df_com['reg'] = df_com_insee['REG'].astype(str)
#df_com['dpt'] = df_com_insee['DEP'].astype(str)
#for code_insee in  ['52465', '52278', '52266', '52124', '52033']:
#  df_com.loc[code_insee, ['reg', 'dpt']] = ['21', '52']
#
#ls_keep_com = ['commune', 'pop', 'com_surf', 'reg', 'dpt'] + ls_columns[1:]
#
#print df_com[ls_keep_com][0:10].to_string()

#df_com[ls_keep_com].to_csv(os.path.join(path_dir_built_csv,
#                                        'df_municipality_hhi.csv'),
#                           encoding = 'latin-1',
#                           float_format = '%.3f',
#                           date_format = '%Y%m%d',
#                           index_label = 'code_insee')

# Check ability to output HHi quantiles weighted by pop (compare with STATA output)

# Duplicates in df_hhi... dunno why given code used to generate
# Drop them and check they do not appear in new code
