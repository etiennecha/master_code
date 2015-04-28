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
from matplotlib.text import TextPath

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_png = os.path.join(path_dir_qlmc, 'data_built' , 'data_png')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

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
# LOAD SUBSET LSA
# ###############

df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_example_comp.csv'),
                      dtype = {u'Code INSEE' : str,
                               u'Code INSEE ardt' : str,
                               u'N°Siren' : str,
                               u'N°Siret' : str},
                      parse_dates = [u'DATE ouv', u'DATE ferm', u'DATE réouv',
                                     u'DATE chg enseigne', u'DATE chgt surf'],
                      encoding = 'latin-1')

# #####################
# LOAD SUBSET COMMUNES
# #####################

df_mun = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_example_mun.csv'),
                     dtype = {'code_insee' : str},
                     encoding = 'latin-1')

# ####################
# COMPETITION LIMITS
# ####################

print u'\nOverview:'
print df_comp[['dist', 'dist_osrm', 'time_osrm']].describe()

# MAP

# subsets of stores
df_lsa_ot = df_lsa[df_lsa['Ident'] != 49]
df_lsa_ot_H = df_lsa_ot[df_lsa_ot['Type'] == 'H']
df_lsa_ot_nH = df_lsa_ot[df_lsa_ot['Type'] != 'H']

df_lsa_ot_H_sg = df_lsa_ot[(df_lsa_ot['Type_alt'] == 'H') & (df_lsa_ot['Groupe'] == 'CARREFOUR')]
df_lsa_ot_X_sg = df_lsa_ot[(df_lsa['Type_alt'] == 'X') & (df_lsa_ot['Groupe'] == 'CARREFOUR')]
df_lsa_ot_S_sg = df_lsa_ot[(df_lsa['Type_alt'] == 'S') & (df_lsa_ot['Groupe'] == 'CARREFOUR')]

df_lsa_ot_H_og = df_lsa_ot[(df_lsa_ot['Type_alt'] == 'H') & (df_lsa_ot['Groupe'] != 'CARREFOUR')]
df_lsa_ot_X_og = df_lsa_ot[(df_lsa_ot['Type_alt'] == 'X') & (df_lsa_ot['Groupe'] != 'CARREFOUR')]
df_lsa_ot_S_og = df_lsa_ot[(df_lsa_ot['Type_alt'] == 'S') & (df_lsa_ot['Groupe'] != 'CARREFOUR')]

# http://www.autoritedelaconcurrence.fr/doc/fiche1_concentration_dec10.pdf
# hyper: 30 mins by car
print u'\nNb comp within 30 mn:', len(df_comp[df_comp['time_osrm'] <= 30])
print df_comp[['dist', 'dist_osrm', 'time_osrm']][df_comp['time_osrm'] <= 30].describe()

lat_ref = df_lsa[df_lsa['Ident'] == 49]['Latitude'].values[0]
lng_ref = df_lsa[df_lsa['Ident'] == 49]['Longitude'].values[0]

df_comp_close = df_comp[df_comp['time_osrm'] <= 30].copy()
delta_lat = max(np.abs(df_comp['Latitude'].max() - lat_ref),
                np.abs(df_comp['Latitude'].min() - lat_ref))
delta_lng = max(np.abs(df_comp['Longitude'].max() - lng_ref),
                np.abs(df_comp['Longitude'].min() - lng_ref))

zoom = 10

delta = 0.4

a, bbox = getImageCluster(lat_ref - delta, # need 1/2 delta_lat
                          lng_ref - delta, # need 1/2 delta_lng
                          delta * 2,
                          delta * 2,
                          zoom)

fig = plt.figure(figsize=(10, 10))
ax = plt.subplot(111)
m = Basemap(
    llcrnrlon=bbox[0], llcrnrlat=bbox[1],
    urcrnrlon=bbox[2], urcrnrlat=bbox[3],
    projection='merc', ax=ax
)

#m = Basemap(
#    lat_0 = lat_ref, lon_0 =  lng_ref,
#    llcrnrlon=bbox[0], llcrnrlat=bbox[1],
#    urcrnrlon=bbox[2], urcrnrlat=bbox[3],
#    projection='tmerc', ax=ax
#)

# display image composed of OSM times
m.imshow(a, interpolation='lanczos', origin='upper')

# display ref stor
xy_ref = m(lng_ref, lat_ref)
ax.scatter([xy_ref[0]], [xy_ref[1]],
           alpha = 1, zorder = 10, color = 'b', s = 50,
           marker = TextPath((0,0), 'H', color = 'b', size = 10))

## display stores (does not include reference store?)
#ls_points = [m(row['Longitude'], row['Latitude']) for row_ind, row\
#               in df_lsa[df_lsa['Ident'] != 49].iterrows()]
#ax.scatter([point[0] for point in ls_points],
#           [point[1] for point in ls_points],
#           alpha = 0.5, s = 10)

# display hypermarkets same group
ls_groups = [[df_lsa_ot_H_sg, 'b', 'H'], 
             [df_lsa_ot_X_sg, 'b', 'X'],
             [df_lsa_ot_S_sg, 'b', 'S'],
             [df_lsa_ot_H_og, 'r', 'H'],
             [df_lsa_ot_X_og, 'r', 'X'],
             [df_lsa_ot_S_og, 'r', 'S']]

from matplotlib.font_manager import FontProperties

for df_temp, marker_c, marker_l in ls_groups:
  ls_points = [m(row['Longitude'], row['Latitude']) for row_ind, row\
                 in df_temp.iterrows()]
  ax.scatter([point[0] for point in ls_points],
             [point[1] for point in ls_points],
             alpha = 0.8, s = 50, color = marker_c, zorder = 9,
             marker = TextPath((0,0), marker_l, color = marker_c, size = 7))

# display circle
def radius_for_tissot(dist_km):
    return np.rad2deg(dist_km/6367.)
m.tissot(lng_ref, lat_ref, radius_for_tissot(30), 256, facecolor='b', alpha=0.1, zorder = 8)

# print ax.get_xlim()
# print ax.get_ylim()

xmin, xmax = 10000, 156367 
ymin, ymax = 50000, 150000
ax.set_xlim((xmin, xmax))
ax.set_ylim((ymin, ymax))

xmin_deg, ymin_deg = m(xmin, ymin, inverse = True)
xmax_deg, ymax_deg = m(xmax, ymax, inverse = True)

## mapscale has a bug with merc projection (use tmerc if needed)
#m.drawmapscale(lon = xmin_deg + 0.1,
#               lat = ymin_deg + 0.05,
#               lon0 = lng_ref, #m.llcrnrlon,
#               lat0 = lat_ref, #m.llcrnrlat,
#               barstyle = 'fancy',
#               labelstyle = 'simple',
#               length = 10,
#               format = '%d')

## add mapscale manually
#x_r_ms = m(xmin_deg + radius_for_tissot(10), ymin)


plt.tight_layout()
plt.show()