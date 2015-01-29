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
                       'commune' : [d['NOM_COMM'] for d in m_fra.communes_fr_info],
                       'com_surf' : [d['SUPERFICIE'] for d in m_fra.communes_fr_info],
                       'pop' : [d['POPULATION'] for d in m_fra.communes_fr_info]})

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

df_com.set_index('code_insee', inplace = True)
## Overwrite IGN pop with INSEE pop (dates?)
#df_com['pop'] = df_com_insee['P10_POP']

ls_rows_hhi = []
for row_ind, row in df_com.iterrows():
  df_lsa_temp = df_lsa.copy()
  df_lsa_temp['lat_com'] = row['lat_cl']
  df_lsa_temp['lng_com'] = row['lng_cl']
  df_lsa_temp['dist'] = compute_distance_ar(df_lsa_temp['Latitude'],
                                            df_lsa_temp['Longitude'],
                                            df_lsa_temp['lat_com'],
                                            df_lsa_temp['lng_com'])
  # continous method (could add max group share)
  df_lsa_temp['wgt_store_surf'] = np.exp(-df_lsa_temp['dist']/10) * df_lsa_temp['Surf Vente']
  wgt_store_surf = df_lsa_temp['wgt_store_surf'].sum()
  df_hhi = df_lsa_temp[['Groupe', 'wgt_store_surf']].groupby('Groupe').agg([sum])['wgt_store_surf']
  df_hhi['market_share'] = df_hhi['sum'] / df_hhi['sum'].sum()
  hhi = (df_hhi['market_share']**2).sum()
  # ac method (could add max group share + nb groups)
  df_lsa_ac = df_lsa_temp[((df_lsa_temp['dist'] <= 25) &\
                           (df_lsa_temp['Type_alt'] == 'H')) |
                          ((df_lsa_temp['dist'] <= 10) &\
                           (df_lsa_temp['Type_alt'].isin(['S', 'X'])))].copy()
  ac_store_surf = df_lsa_ac['Surf Vente'].sum()
  ac_nb_groups = len(df_lsa_ac['Groupe'].unique())
  df_ac_hhi = df_lsa_ac[['Groupe', 'Surf Vente']].groupby('Groupe').agg([sum])['Surf Vente']
  df_ac_hhi['market_share'] = df_ac_hhi['sum'] / df_ac_hhi['sum'].sum()
  ac_hhi = (df_ac_hhi['market_share']**2).sum()
  ac_cr1 = df_ac_hhi['market_share'].max()
  ls_rows_hhi.append((row_ind, wgt_store_surf, hhi,
                      ac_nb_groups, ac_cr1, ac_store_surf, ac_hhi))

  #ls_rows_hhi.append((row_ind, wgt_store_surf, hhi))

print df_lsa_ac[ls_disp_lsa + ['Type_alt', 'dist']].to_string()

ls_columns = ['index', 'wgt_store_surf', 'hhi',
              'ac_nb_groups', 'ac_cr1', 'ac_store_surf', 'ac_hhi']
# ls_columns = ['index', 'wgt_store_surf', 'hhi']

df_hhi = pd.DataFrame(ls_rows_hhi, columns = ls_columns)
df_hhi.set_index('index', inplace = True)

df_com = pd.merge(df_com,
                  df_hhi,
                  how = 'left',
                  right_index = True,
                  left_index = True)

df_com['hhi'] = df_com['hhi'] * 10000
df_com['ac_hhi'] = df_com['ac_hhi'] * 10000

# Add DEP and REG... five are not in insee data: nouvelles communes...
df_com['reg'] = df_com_insee['REG'].astype(str)
df_com['dpt'] = df_com_insee['DEP'].astype(str)
for code_insee in  ['52465', '52278', '52266', '52124', '52033']:
  df_com.loc[code_insee, ['reg', 'dpt']] = ['21', '52']

ls_keep_com = ['commune', 'pop', 'com_surf'] + ls_columns[1:]

print df_com[ls_keep_com][0:10].to_string()

df_com[ls_keep_com].to_csv(os.path.join(path_dir_built_csv,
                                        'df_municipality_hhi.csv'),
                           encoding = 'latin-1',
                           float_format = '%.3f',
                           date_format = '%Y%m%d',
                           index_label = 'code_insee')

# Check ability to output HHi quantiles weighted by pop (compare with STATA output)

# Duplicates in df_hhi... dunno why given code used to generate
# Drop them and check they do not appear in new code
