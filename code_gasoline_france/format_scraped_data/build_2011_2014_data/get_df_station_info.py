#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
from matching_insee import *
import pprint
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape

path_dir_built = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_scraped_2011_2014')

path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')

# #################
# LOAD ALL INFO DFS
# #################

df_chars = pd.read_csv(os.path.join(path_dir_built_csv,
                                    'df_chars.csv'),
                       encoding = 'utf-8',
                       dtype = {'id_station' : str,
                                'adr_zip' : str,
                                'adr_dpt' : str})
# could read whole as str and then destr a few columns
df_chars.set_index('id_station', inplace = True)

df_geocoding = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_geocoding.csv'),
                           encoding = 'utf-8',
                           dtype = {'id_station' : str})
df_geocoding.set_index('id_station', inplace = True)

df_ci = pd.read_csv(os.path.join(path_dir_built_csv,
                                 'df_ci.csv'),
                           encoding = 'utf-8',
                           dtype = str)
df_ci.set_index('id_station', inplace = True)

df_brand_activity = pd.read_csv(os.path.join(path_dir_built_csv,
                                             'df_brand_activity.csv'),
                           encoding = 'utf-8',
                           dtype = {'id_station' : str,
                                    'dilettante' : int})
df_brand_activity.set_index('id_station', inplace = True)

# #######
# MERGE
# #######

df_station_info = pd.merge(df_chars,
                           df_brand_activity,
                           left_index = True,
                           right_index = True,
                           how = 'outer')

for df_temp in [df_ci, df_geocoding]:
  df_station_info = pd.merge(df_station_info,
                             df_temp,
                             left_index = True, 
                             right_index = True,
                             how = 'outer')

# #########################
# CHECK GPS AND KEEP BEST
# #########################

# LOAD MUNICIPALITY GEOGRAPHY

# excludes Corsica
x1 = -5.
x2 = 9.
y1 = 42
y2 = 52.

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

path_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')
m_fra.readshapefile(path_com, 'communes_fr', color = 'none', zorder=2)
df_com = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.communes_fr],
                       'x_center' : [d['X_CENTROID'] for d in m_fra.communes_fr_info],
                       'y_center' : [d['Y_CENTROID'] for d in m_fra.communes_fr_info],
                       'x_cl' : [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl' : [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'code_insee' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'commune' : [d['NOM_COMM'] for d in m_fra.communes_fr_info]})

def convert_from_ign(x_l_93_ign, y_l_93_ign):
  x = x_l_93_ign * 100 - 700000 + m_fra(3, 46.5)[0] 
  y = y_l_93_ign * 100 - 6600000 + m_fra(3, 46.5)[1]
  x, y = m_fra(x, y, inverse = True)
  return x, y

df_com[['lng_ct', 'lat_ct']] = df_com[['x_center', 'y_center']].apply(\
                                 lambda x: convert_from_ign(x['x_center'],\
                                                            x['y_center']),\
                                 axis = 1)

df_com[['lng_cl', 'lat_cl']] = df_com[['x_cl', 'y_cl']].apply(\
                                 lambda x: convert_from_ign(x['x_cl'],\
                                                            x['y_cl']),\
                                 axis = 1)

# PICK MOST RECENT GPS

df_station_info['id_station'] = df_station_info.index
df_com.drop_duplicates(subset = 'code_insee', inplace = True)
df_station_info = pd.merge(df_station_info,
                           df_com,
                           left_on = 'ci_ardt_1',
                           right_on = 'code_insee',
                           how = 'left')
df_station_info.set_index('id_station', inplace = True)


# Update those for which more recent info (fixes existing issues?)
for i in [1,2]:
  df_station_info.loc[~pd.isnull(df_station_info['lng_gov_%s' %i]),
              'lng_gov_0'] = df_station_info['lng_gov_%s' %i]
  df_station_info.loc[~pd.isnull(df_station_info['lat_gov_%s' %i]),
              'lat_gov_0'] = df_station_info['lat_gov_%s' %i]

# Use rls (old gov info) if no info
df_station_info.loc[pd.isnull(df_station_info['lng_gov_0']),
                    'lng_gov_0'] = df_station_info['lng_rls']
df_station_info.loc[pd.isnull(df_station_info['lat_gov_0']),
                    'lat_gov_0'] = df_station_info['lat_rls']

# Use geocoding if no info
df_station_info.loc[pd.isnull(df_station_info['lng_gov_0']),
                    'lng_gov_0'] = df_station_info['lng_gc']
df_station_info.loc[pd.isnull(df_station_info['lat_gov_0']),
                    'lat_gov_0'] = df_station_info['lat_gc']

# Fix issue detected: inversion of lat and lng
#len(df_station_info_ta[df_station_info_ta['lng_gov_0'] > df_station_info_ta['lat_gov_0']])
df_station_info['lng_best'] = df_station_info['lng_gov_0']
df_station_info['lat_best'] = df_station_info['lat_gov_0']
df_station_info.loc[df_station_info['lng_gov_0'] > df_station_info['lat_gov_0'],
            'lng_best'] = df_station_info['lat_gov_0']
df_station_info.loc[df_station_info['lng_gov_0'] > df_station_info['lat_gov_0'],
            'lat_best'] = df_station_info['lng_gov_0']

# Get rid of highway gps (too unreliable so far)
df_station_info.loc[df_station_info['highway'] == 1,
                    ['lat_best', 'lng_best']] = np.nan, np.nan

# COMPUTE DISTANCE TO MUNICIPALITY CENTER TO DETECT ERRORS

df_station_info['dist_cl'] = compute_distance_ar(df_station_info['lat_best'],
                                                 df_station_info['lng_best'],
                                                 df_station_info['lat_ct'],
                                                 df_station_info['lng_ct'])

# Threshold picked: 20 km... if more, try with gps from geocoding
print u'\nNb of wrong gov coordinates (dist to municipality center too high):',\
      len(df_station_info[df_station_info['dist_cl'] > 20])

df_station_info.loc[df_station_info['dist_cl'] > 20,
                    'lat_best'] = df_station_info['lat_gc']
df_station_info.loc[df_station_info['dist_cl'] > 20,
                    'lng_best'] = df_station_info['lng_gc']

df_station_info['dist_cl'] = compute_distance_ar(df_station_info['lat_best'],
                                                 df_station_info['lng_best'],
                                                 df_station_info['lat_ct'],
                                                 df_station_info['lng_ct'])

df_station_info['dist_gc'] = compute_distance_ar(df_station_info['lat_best'],
                                                 df_station_info['lng_best'],
                                                 df_station_info['lat_gc'],
                                                 df_station_info['lng_gc'])

ls_disp_info = ['name', 'adr_street', 'commune',
                'lat_best', 'lng_best',
                'dist_cl', 'dist_gc', 'quality']

df_too_far = df_station_info[(df_station_info['dist_cl'] > 20)]
print '\nNb stations too far to commune center:', len(df_too_far)
print '\n', df_too_far[ls_disp_info].to_string()

df_too_close = df_station_info[ls_disp_info][(df_station_info['dist_cl'] < 0.10)]
print '\nNb stations too close to commune center:', len(df_too_close)
print '\n', df_too_close[ls_disp_info].to_string()

# If too close with gov but got ROOFTOP OR RANGE_INTERPOLATED: prefer geocoding
df_station_info.loc[(df_station_info['dist_cl'] < 0.1) &\
                    (df_station_info['quality'].isin(['ROOFTOP',
                                                      'RANGE_INTERPOLATED'])),
                    'lat_best'] = df_station_info['lat_gc']

df_station_info.loc[(df_station_info['dist_cl'] < 0.1) &\
                    (df_station_info['quality'].isin(['ROOFTOP',
                                                      'RANGE_INTERPOLATED'])),
                    'lng_best'] = df_station_info['lng_gc']

df_still_too_close =\
  df_station_info[(df_station_info['dist_cl'] < 0.10) &\
                  (~df_station_info['quality'].isin(['ROOFTOP',
                                                     'RANGE_INTERPOLATED']))]

print '\nNb stations still close to commune center:', len(df_still_too_close)
print '\n', df_still_too_close[ls_disp_info].to_string(index=False)

# Adhox fixes (dist was too high even with geocoding)
ls_gps_adhoc_fix = [['13115001', [43.686, 5.713]],
                    ['19350001', [45.316, 1.341]],
                    ['5350001',  [44.763, 6.820]],
                    ['84140005', [43.940, 4.600]],
                    ['33410003', [44.964, -0.378]],
                    ['83000002', [43.115, 5.945]],
                    ['6210008',  [43.546, 6.938]],
                    ['59148002', [50.429, 3.180]],
                    ['84570001', [44.058, 5.232]]]
for id_station, gps in ls_gps_adhoc_fix:
  if id_station in df_station_info.index:
    df_station_info.loc[id_station, ['lat_best', 'lng_best']] = gps

df_station_info.drop(['lat_gov_0', 'lng_gov_0',
                      'lat_gov_1', 'lng_gov_1',
                      'lat_gov_2', 'lng_gov_2',
                      'lat_rls', 'lng_rls',
                      'lat_gc', 'lng_gc', 'quality', 'google_adr',
                      'x_center', 'y_center', 'x_cl', 'y_cl', 'poly',
                      'lat_ct', 'lng_ct', 'lat_cl', 'lng_cl',
                      'dist_cl', 'dist_gc'],
                     axis = 1,
                     inplace = True)

df_station_info.rename(columns = {'lat_best': 'lat',
                                  'lng_best': 'lng'},
                       inplace = True)

# Make sure no gps for highway gas stations (so far)
df_station_info.loc[df_station_info['highway'] == 1,
                    ['lat', 'lng']] = np.nan, np.nan

# ######
# OUTPUT
# ######

# CSV
df_station_info.to_csv(os.path.join(path_dir_built_csv,
                                    'df_station_info.csv'),
                       index_label = 'id_station',
                       float_format= '%.3f',
                       encoding = 'utf-8')

# XLS (?)
