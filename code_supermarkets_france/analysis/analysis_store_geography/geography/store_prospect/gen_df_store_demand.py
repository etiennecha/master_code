#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_maps import *
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
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

df_lsa = df_lsa[(~df_lsa['latitude'].isnull()) &\
                (~df_lsa['longitude'].isnull())].copy()

df_com_insee = pd.read_csv(os.path.join(path_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'utf-8')
# Has both districts and aggregate for Paris/Marseille/Lyon (e.g. DEP == '75')

df_com_insee.set_index('CODGEO', inplace = True)

# LOAD GEO FRANCE (Keep Corse)
geo_france = GeoFrance(path_dpt = path_geo_dpt,
                       path_com = path_geo_com,
                       corse = True)
df_com = geo_france.df_com
# Has only districts for Paris/Marseille/Lyon (e.g. departement == 'PARIS')

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

lsd0 = [u'enseigne',
        u'adresse1',
        u'c_postal',
        u'ville'] #, u'Latitude', u'Longitude']

## Check correspondence between INSEE and IGN
#df_com_insee_fm = df_com_insee[~df_com_insee['DEP'].isin(['2A', '2B', '97'])].copy()
#print df_com[~df_com['c_insee'].isin(df_com_insee_fm.index)].to_string()

# Add population to IGN data
df_com.set_index('c_insee', inplace = True)
df_com['pop'] = df_com_insee['P10_POP']

# PARAMETERS FOR DEMAND PROXIES
# - no weighting (ac stands for competition authority): 10, 20, 25 km
# - weighting with different discount factors
ls_ac_dist = [10, 20, 25]
ls_cont_disct = [8, 10, 12]

ls_demand_cols = ['pop_ac_{:d}km'.format(ac_dist) for ac_dist in ls_ac_dist] +\
                 ['pop_cont_{:d}'.format(cont_disct) for cont_disct in ls_cont_disct]

df_lsa_hs = df_lsa[df_lsa['type_alt'].isin(['H', 'S'])]
ls_rows_demand = []
for row_ind, row in df_lsa_hs.iterrows():
  ## could actually keep reference store since using groupe surface only
  #df_lsa_sub_temp = df_lsa_sub[df_lsa_sub.index != row_ind].copy()
  df_com_temp = df_com.copy()
  df_com_temp['lat_store'] = row['latitude']
  df_com_temp['lng_store'] = row['longitude']
  df_com_temp['dist'] = compute_distance_ar(df_com_temp['lat_store'],
                                            df_com_temp['lng_store'],
                                            df_com_temp['lat_cl'],
                                            df_com_temp['lng_cl'])
  # Population within radius (no weighting)
  ls_ac_demand = [df_com_temp['pop'][df_com_temp['dist'] <= ac_dist].sum()\
                    for dist in ls_ac_dist]
  
  # Discounted population (all France)
  ls_cont_demand = []
  for cont_disct in ls_cont_disct:
    df_com_temp['wgtd_pop'] = np.exp(-df_com_temp['dist']/ cont_disct) *\
                                          df_com_temp['pop']
    ls_cont_demand.append(df_com_temp['wgtd_pop'].sum())

  ls_rows_demand.append([row['id_lsa'], row['type_alt']] +\
                        ls_ac_demand +\
                        ls_cont_demand)

df_demand = pd.DataFrame(ls_rows_demand,
                         columns = ['id_lsa', 'type_alt'] + ls_demand_cols)

df_demand['pop_ac_1025km'] = df_demand['pop_ac_10km']
df_demand.loc[df_demand['type_alt'] == 'H',
              'pop_ac_1025km'] = df_demand['pop_ac_25km']
df_demand.drop(['type_alt'], axis = 1, inplace = True)

# CHECK RESULTS
df_lsa_hs_demand = pd.merge(df_lsa_hs,
                            df_demand[['id_lsa'] + ls_demand_cols],
                            how = 'left',
                            left_on = 'id_lsa',
                            right_on = 'id_lsa')

df_lsa_hs_demand.sort(['pop_ac_10km'], ascending = False, inplace = True)
lsd_lsa_demand = ['id_lsa'] + lsd0 + ls_demand_cols

print ''
print df_lsa_hs_demand[lsd_lsa_demand][0:10].to_string()

print ''
print df_lsa_hs_demand[lsd_lsa_demand][-10:].to_string()


# OUTPUT
df_demand.to_csv(os.path.join(path_built_csv,
                              '201407_competition',
                              'df_store_prospect_demand.csv'),
                 float_format ='%.3f',
                 index = False,
                 encoding = 'utf-8')
