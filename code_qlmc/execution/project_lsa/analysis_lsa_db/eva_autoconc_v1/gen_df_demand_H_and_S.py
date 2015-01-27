#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_png = os.path.join(path_dir_qlmc, 'data_built' , 'data_png')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

def convert_to_ign(x, y):
  x_l_93_ign = (m_fra(x, y)[0] + 700000 - m_fra(3, 46.5)[0])/100.0
  y_l_93_ign = (m_fra(x, y)[1] + 6600000 - m_fra(3, 46.5)[1])/100.0
  return x_l_93_ign, y_l_93_ign

def convert_from_ign(x_l_93_ign, y_l_93_ign):
  x = x_l_93_ign * 100 - 700000 + m_fra(3, 46.5)[0] 
  y = y_l_93_ign * 100 - 6600000 + m_fra(3, 46.5)[1]
  x, y = m_fra(x, y, inverse = True)
  return x, y

# ##############
# LOAD LSA data
# ##############

df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_lsa_active_fm_hsx.csv'),
                     dtype = {u'Code INSEE' : str,
                              u'Code INSEE ardt' : str,
                              u'N°Siren' : str,
                              u'N°Siret' : str},
                     parse_dates = [u'DATE ouv', u'DATE ferm', u'DATE réouv',
                                    u'DATE chg enseigne', u'DATE chgt surf'],
                     encoding = 'UTF-8')
df_lsa = df_lsa[(~pd.isnull(df_lsa['Latitude'])) &\
                (~pd.isnull(df_lsa['Longitude']))].copy()

ls_disp_lsa = [u'Enseigne',
               u'ADRESSE1',
               u'Code postal',
               u'Ville'] # u'Latitude', u'Longitude']

# ###############
# LOAD COMMUNES
# ###############

df_com_insee = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'UTF-8')
df_com_insee.set_index('CODGEO', inplace = True)

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

path_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')

m_fra.readshapefile(path_dpt, 'departements_fr', color = 'none', zorder=2)
m_fra.readshapefile(path_com, 'communes_fr', color = 'none', zorder=2)

df_com = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.communes_fr],
                       'x_center' : [d['X_CENTROID'] for d in m_fra.communes_fr_info],
                       'y_center' : [d['Y_CENTROID'] for d in m_fra.communes_fr_info],
                       'x_cl' : [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl' : [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'code_insee' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'commune' : [d['NOM_COMM'] for d in m_fra.communes_fr_info]})


# Drop Corsica (make sure dropped in LSA as well?)
df_com['dpt'] = df_com['code_insee'].str.slice(stop=-3)
df_com = df_com[~df_com['dpt'].isin(['2A', '2B'])]

# Keep only one line per commune (several polygons for some)
df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)
df_com.sort(columns = ['code_insee', 'poly_area'],
            ascending = False,
            inplace = True)

df_com.drop_duplicates(subset = 'code_insee', inplace = True)

#print u'\nTest with commune', df_com['commune'].iloc[0]
#x_test, y_test = df_com['x_center'].iloc[0], df_com['y_center'].iloc[0]
#print convert_from_ign(x_test, y_test)

df_com[['lng_ct', 'lat_ct']] = df_com[['x_center', 'y_center']].apply(\
                                 lambda x: convert_from_ign(x['x_center'],\
                                                            x['y_center']),\
                                 axis = 1)

df_com[['lng_cl', 'lat_cl']] = df_com[['x_cl', 'y_cl']].apply(\
                                 lambda x: convert_from_ign(x['x_cl'],\
                                                            x['y_cl']),\
                                 axis = 1)

# Round gps coord
for col in ['lng_ct', 'lat_ct', 'lng_cl', 'lat_cl']:
  df_com[col] = np.round(df_com[col], 3)

# Check correspondence between INSEE and IGN
df_com_insee_fm = df_com_insee[~df_com_insee['DEP'].isin(['2A', '2B', '97'])].copy()
print df_com[~df_com['code_insee'].isin(df_com_insee_fm.index)].to_string()

# Add population to IGN data
df_com.set_index('code_insee', inplace = True)
df_com['pop'] = df_com_insee['P10_POP']

# Type restriction
ls_h_and_s_demand = [['H', 25],
                     ['S', 10]]

for type_store, dist_demand in ls_h_and_s_demand:
  df_lsa_type = df_lsa[df_lsa['Type_alt'] == type_store].copy()
  
  # Population available for one store
  
  ls_rows_demand = []
  for row_ind, row in df_lsa_type.iterrows():
    ## could actually keep reference store since using groupe surface only
    #df_lsa_sub_temp = df_lsa_sub[df_lsa_sub.index != row_ind].copy()
    df_com_temp = df_com.copy()
    df_com_temp['lat_store'] = row['Latitude']
    df_com_temp['lng_store'] = row['Longitude']
    df_com_temp['dist'] = compute_distance_ar(df_com_temp['lat_store'],
                                              df_com_temp['lng_store'],
                                              df_com_temp['lat_cl'],
                                              df_com_temp['lng_cl'])
    # AC
    ac_pop = df_com_temp['pop'][df_com_temp['dist'] <= dist_demand].sum()
    
    # CONTINUOUS
    df_com_temp['Wgt pop'] = np.exp(-df_com_temp['dist']/10) *\
                                          df_com_temp['pop']
    pop = df_com_temp['Wgt pop'].sum()

    ls_rows_demand.append((row_ind, ac_pop, pop))

  df_des_demand = pd.DataFrame(ls_rows_demand,
                               columns = ['index', 'ac_pop', 'pop'])
  df_des_demand.set_index('index', inplace = True)
  
  df_lsa_type = pd.merge(df_lsa_type,
                         df_des_demand,
                         how = 'left',
                         left_index = True,
                         right_index = True)
  
  df_lsa_type.sort(['Code INSEE ardt', 'Enseigne'], inplace = True)
  
  ls_disp_lsa_comp = ls_disp_lsa + ['ac_pop', 'pop']

  print u'\n', type_store
  print df_lsa_type[ls_disp_lsa_comp][0:10].to_string()
  
  # temp: avoid error with dates before 1900 and strftime (when outputing to csv)
  df_lsa_type.loc[df_lsa_type[u'DATE ouv'] <= '1900', 'DATE ouv'] =\
     pd.to_datetime('1900/01/01', format = '%Y/%m/%d')

  df_lsa_type.to_csv(os.path.join(path_dir_built_csv,
                                  'df_store_demand_%s.csv' %type_store),
                     encoding = 'latin-1',
                     float_format ='%.3f',
                     date_format='%Y%m%d',
                     index = False)

## Test GroupBy with None => Caution, None ignored in groupby
## Hence need to fill with unique entries if None to get it working properly
#df_mkt = pd.DataFrame([['Carrouf', 100],
#                       ['Leclerc',  50],
#                       [None     ,  11],
#                       [None     ,   3]], columns = ['Groupe', 'Surf Vente'])
#df_hhi_test = df_mkt[['Groupe', 'Surf Vente']].groupby('Groupe').agg([sum])['Surf Vente']
#df_hhi_test['market_share'] = df_hhi_test['sum'] / df_hhi_test['sum'].sum()
#print df_hhi_test.to_string()
