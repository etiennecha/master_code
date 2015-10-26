#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
from matplotlib.collections import PatchCollection

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built, 'data_csv')
path_built_csv_comp = os.path.join(path_built_csv, '201407_competition')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###################
# LOAD DF HYPER COMP
# ###################

# Hyper vs. hyper only
df_hvh = pd.read_csv(os.path.join(path_built_csv_comp,
                                  'df_store_prospect_comp_H_v_H.csv'),
                     encoding = 'utf-8')

# Hyper vs hyper, super and discounters
df_hva = pd.read_csv(os.path.join(path_built_csv_comp,
                                  'df_store_prospect_comp_H_v_all.csv'),
                     encoding = 'utf-8')

# Proxies for hyper demand: population around
df_demand_h = pd.read_csv(os.path.join(path_built_csv_comp,
                                       'df_store_prospect_demand_H.csv'),
                          encoding = 'utf-8')

# Municipality HHI
df_hhi = pd.read_csv(os.path.join(path_built_csv_comp,
                                  'df_municipality_hhi.csv'),
                     dtype = {'c_insee' : str},
                     encoding = 'utf-8')
df_hhi.set_index('c_insee', inplace = True)

# Preliminary display
ls_disp_lsa = [u'enseigne',
               u'adresse1',
               u'c_postal',
               u'ville']

ls_disp_lsa_comp = ls_disp_lsa + ['ac_nb_stores', 'ac_nb_chains', 'ac_nb_comp',
                                  'ac_store_share', 'store_share',
                                  'ac_group_share', 'group_share',
                                  'ac_hhi', 'hhi']

print u'HvH'
print u'\n', df_hvh['ac_nb_chains'].describe()
print u'\n', df_hvh['ac_group_share'].describe()

print u'\nNb with st. less than 4 chains and group share about 0.5:',\
        len(df_hvh[(df_hvh['ac_nb_chains'] < 4) &\
                 (df_hvh['ac_group_share'] > 0.5)])

# ###################
# BUILD FINAL DF
# ###################

# Variables in file:
# - hvh_ac_nb_groups: nb hypermarket groups present within market with AC method
# - hva_ac_nb_groups: nb hyper, super, discounter groups present within market with AC method
# - hvh_ac_group_share_hvh : share of the hypermarket group vs. hyper with AC method
# - hva_ac_group_share : share of the hypermarket group vs. hyper, super, discounters with AC method
# - hvh_group_share : share of the hypermarket group vs. hyper with weighting by distance
# - hva_group_share : share of the hypermarket group vs. hyper, super, discounters with weighting by distance
# - ac_pop: pop available to hypermarket with AC method
# - pop : pop available to hypermarket with weighting by distance
# - ac_nb_hypers : nb hyper within market with AC method
# - ac_nb_stores : nb hyper, super, discounters within market with AC method
# - ac_hypers_by_pop_ac: nb hyper (AC) divided by pop available with AC method
# - ac_hypers_by_pop: nb hyper (AC) divided by pop available with weighting by distance
# - ac_stores_by_pop_ac: nb stores (AC) divided by pop available with AC method
# - ac_stores_by_pop: nb stores (AC) divided by pop available with weighting by distance

# Could also check surface available divided by pop

df_hvh.rename(columns = {'ac_nb_chains' : 'hvh_ac_nb_groups',
                         'ac_group_share' : 'hvh_ac_group_share',
                         'group_share' : 'hvh_group_share',
                         'ac_nb_stores' : 'ac_nb_hypers'}, inplace = True)

df_hva.rename(columns = {'ac_nb_chains' : 'hva_ac_nb_groups',
                         'ac_group_share' : 'hva_ac_group_share',
                         'group_share' : 'hva_group_share',
                         'ac_nb_stores' : 'ac_nb_stores'}, inplace = True)

df_hvh.set_index('id_lsa', inplace = True)
df_hva.set_index('id_lsa', inplace = True)

df_hvh = pd.merge(df_hvh,
                  df_hva[['hva_ac_nb_groups',
                          'hva_ac_group_share',
                          'hva_group_share',
                          'ac_nb_stores']],
                  how = 'left',
                  right_index = True,
                  left_index = True)

df_demand_h.set_index('id_lsa', inplace = True)

df_hvh = pd.merge(df_hvh,
                  df_demand_h[['pop', 'ac_pop']],
                  how = 'left',
                  right_index = True,
                  left_index = True)

df_hvh['ac_hypers_by_pop_ac'] = df_hvh['ac_nb_hypers'] / df_hvh['ac_pop'] * 100000
df_hvh['ac_hypers_by_pop'] = df_hvh['ac_nb_hypers'] / df_hvh['pop'] * 100000
df_hvh['ac_stores_by_pop_ac'] = df_hvh['ac_nb_stores'] / df_hvh['ac_pop'] * 1000000
df_hvh['ac_stores_by_pop'] = df_hvh['ac_nb_stores'] / df_hvh['pop'] * 100000

# #####################
# STATS DES COMPETITION
# #####################

# Examine nb competitors
print u'\nAll figures by pop are by 100,000 inhabitants'

print u'\n', df_hvh[['ac_nb_hypers', 'ac_hypers_by_pop_ac', 'ac_hypers_by_pop']].describe()
print u'\n', df_hvh[['ac_nb_stores', 'ac_stores_by_pop_ac', 'ac_stores_by_pop']].describe()

# Display dpt largest quartiles

print u'\nRegions of stores in highest quartile in terms of nb stores in market'
print df_hvh['region'][df_hvh['ac_nb_stores'] >= df_hvh['ac_nb_stores']\
        .quantile(q = 0.75)].value_counts()

print u'\nRegions of stores in highest quartile in terms of nb stores by pop'
print df_hvh['region'][df_hvh['ac_stores_by_pop'] >= df_hvh['ac_stores_by_pop']\
        .quantile(q = 0.75)].value_counts()

print u'\nRegions of stores in lowest quartile in terms of nb stores in market'
print df_hvh['region'][df_hvh['ac_nb_stores'] <= df_hvh['ac_nb_stores']\
        .quantile(q = 0.25)].value_counts()

print u'\nRegions of stores in lowest quartile in terms of nb stores in market'
print df_hvh['region'][df_hvh['ac_stores_by_pop'] <= df_hvh['ac_stores_by_pop']\
        .quantile(q = 0.25)].value_counts()

print u'\nRegions of stores with st. less than 3 groups in market'
print df_hvh['region'][df_hvh['hvh_ac_nb_groups'] < 4].value_counts()

print u'\nRegions of stores with st. less than 3 H groups and above 50% H market share (AC):'
print df_hvh['region'][(df_hvh['hvh_ac_nb_groups'] < 4) &\
                    (df_hvh['hvh_ac_group_share'] > 0.5)].value_counts()

print u'\nRegions of stores with st. less than 3 groups and above 50% market share (AC):'
print df_hvh['region'][(df_hvh['hva_ac_nb_groups'] < 4) &\
                    (df_hvh['hva_ac_group_share'] > 0.5)].value_counts()

print u'\nRegions of stores with st. less than 3 groups and above 50% H market share (cont):'
print df_hvh['region'][(df_hvh['hvh_ac_nb_groups'] < 4) &\
                    (df_hvh['hvh_group_share'] > 0.5)].value_counts()

print u'\nRegions of stores with st. less than 3 groups and above 50% market share (cont):'
print df_hvh['region'][(df_hvh['hva_ac_nb_groups'] < 4) &\
                    (df_hvh['hva_group_share'] > 0.5)].value_counts()

print u'\nStudy of hypermarkets with low hypermarket competition:'
ls_hyper_low_comp = df_hvh.index[(df_hvh['hvh_ac_nb_groups'] < 4) &\
                                 (df_hvh['hvh_ac_group_share'] > 0.5)]

print u'\nTaking H/S/X into account:'
print df_hvh[['hva_group_share', 'hva_ac_group_share', 'hva_ac_nb_groups']].\
        ix[ls_hyper_low_comp].describe()

print u'\nAll hypermarkets:'
print df_hvh[['ac_hypers_by_pop_ac', 'ac_hypers_by_pop']].describe()

print u'\nLow comp hypermarkets:'
print df_hvh.ix[ls_hyper_low_comp][['ac_hypers_by_pop_ac', 'ac_hypers_by_pop']].describe()

print u'\nLow comp but high nb of hypers by pop'
print df_hvh.ix[ls_hyper_low_comp][df_hvh['ac_hypers_by_pop'].ix[ls_hyper_low_comp] > 10]\
        [ls_disp_lsa + ['surface', 'region']].to_string()

# ########
# OUTPUT
# ########

#df_hvh.to_csv(os.path.join(path_built_csv_comp,
#                           'df_hyper_competition.csv'),
#              encoding = 'utf-8',
#              float_format ='%.3f',
#              date_format='%Y%m%d',
#              index = False)


## ############################
## MAP OF LOW COMPETITION AREAS
## ############################
#
# todo: move (not tested)
#
#path_maps = os.path.join(path_data, 'data_maps')
#path_geo_dpt = os.path.join(path_maps, 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
#path_geo_com = os.path.join(path_maps, 'GEOFLA_COM_WGS84', 'COMMUNE')
#
## LOAD GEO FRANCE
#geo_france = GeoFrance(path_dpt = path_geo_dpt,
#                       path_com = path_geo_com)
#df_com = geo_france.df_com
#df_dpt = geo_france.df_dpt
#
## KEEP ONLY ONE LINE PER MUNICIPALITY (several polygons for some)
#df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)
## keep largest area (todo: sum)
#df_com.sort(columns = ['c_insee', 'poly_area'],
#            ascending = False,
#            inplace = True)
#df_com.drop_duplicates(['c_insee'], inplace = True, take_last = False)
#
## GET GPS COORD OF MUNICIPALITY CENTER
#
## two centers available: centroid of polygon and town hall
#print u'\nTest with commune', df_com['commune'].iloc[0]
#x_test, y_test = df_com['x_ct'].iloc[0], df_com['y_ct'].iloc[0]
#print geo_france.convert_ign_to_gps(x_test, y_test)
#
#df_com[['lng_ct', 'lat_ct']] = df_com[['x_ct', 'y_ct']].apply(\
#                                 lambda x: geo_france.convert_ign_to_gps(x['x_ct'],\
#                                                                         x['y_ct']),\
#                                 axis = 1)
#
#df_com[['lng_cl', 'lat_cl']] = df_com[['x_cl', 'y_cl']].apply(\
#                                 lambda x: geo_france.convert_ign_to_gps(x['x_cl'],\
#                                                                         x['y_cl']),\
#                                 axis = 1)
#
## Round gps coord
#for col in ['lng_ct', 'lat_ct', 'lng_cl', 'lat_cl']:
#  df_com[col] = np.round(df_com[col], 3)
#
## ADD HHI
#df_com.set_index('c_insee', inplace = True)
#df_com = pd.merge(df_com,
#                  df_hhi[['wgtd_surface', 'hhi']],
#                  how = 'left',
#                  left_index = True,
#                  right_index = True)
#
#
## PREPARE GPS POINTS
#df_hvh['point'] = df_hvh[['longitude', 'latitude']].apply(\
#                        lambda x: Point(geo_france.m_fra(x[0], x[1])), axis = 1)
#
#plt.clf()
#fig = plt.figure()
#ax1 = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
#
#le_1 = ax1.scatter([store.x for store in df_hvh['point'].ix[ls_hyper_low_comp]],
#                   [store.y for store in df_hvh['point'].ix[ls_hyper_low_comp]],
#                   s = 20, marker = 'o', lw=0, facecolor = '#FE2E2E', edgecolor = 'w', alpha = 0.8,
#                   antialiased = True, zorder = 3)
#
## dpt borders
#df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
#                      PolygonPatch(x, fc = 'w', ec='#000000', lw=0.6, alpha=1, zorder=1))
#pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
#le_2 = ax1.add_collection(pc_2)
#
## communes with low comp
#df_com['patches'] = df_com['poly'].map(lambda x:\
#                      PolygonPatch(x, fc = 'b', ec= 'w', lw=0.1, alpha=0.6, zorder=2))
#pc_3 = PatchCollection(df_com['patches'][df_com['hhi'] > 2500], match_original=True)
#le_3 = ax1.add_collection(pc_3)
#
## fake object for legend
#from matplotlib.lines import Line2D
#le_4 = Line2D([0], [0], linestyle="none", marker="o", alpha=0.6, markersize=10, markerfacecolor="b")
#
#ax1.autoscale_view(True, True, True)
#ax1.axis('off')
##ax1.set_title('Hypermarkets with low competition', loc = 'left')
## plt.subplots_adjust(left=.1, right=0.95, bottom=0.1, top=0.95, wspace=0, hspace=0)
#plt.tight_layout()
#plt.legend((le_1, le_4),
#           ('Hypers w/ low competition', 'Municipalities with HHI > 2500'),
#            scatterpoints = 1, numpoints = 1, loc = 'best')
#fig.set_size_inches(10, 15) # set the image width to 722px
##plt.savefig(os.path.join(path_dir_built_graphs,
##                         'maps',
##                         'total_access.png'),
##            dpi=300,
##            alpha=True,
##            bbox_inches = 'tight')
#plt.show()
#
## drop communes duplicates (several polygons: can not draw map as well after that!)
#df_com.reset_index(inplace = True) # index name lost?
#df_com.drop_duplicates('index', inplace = True)
#df_com.set_index('index', inplace = True)
#
#ls_percentiles = [0.1, 0.25, 0.5, 0.75, 0.9]
#print df_hhi['hhi'].describe(percentiles = ls_percentiles)
#
### requires package wquantiles
##import weighted
##for quantile in ls_percentiles:
##  print weighted.quantile(df_hhi['hhi'], df_hhi['pop'], quantile)
#
## todo: code weighted mean and std (count, min, max, unchanged) + check vs. STATA
#
#df_com.sort('hhi', ascending = False, inplace = True)
#print df_com[['commune', 'departement', 'region', 'pop', 'wgtd_surface', 'hhi']][0:20].to_string()
#
#print 'u\nPop living in municipalies with hhi above 2500:'
#print df_com['pop'][df_com['hhi'] > 2500].sum()
