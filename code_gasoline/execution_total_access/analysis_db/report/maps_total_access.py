#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import matplotlib.cm as cm
from matplotlib.collections import PatchCollection
import matplotlib.font_manager as fm
#import shapefile
from mpl_toolkits.basemap import Basemap
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch
#from pysal.esda.mapclassify import Natural_Breaks as nb
from matplotlib import colors

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_dir_built_json = os.path.join(path_dir_built_paper,
                                   'data_json')

path_dir_built_graphs = os.path.join(path_dir_built_paper,
                                     'data_graphs')

path_dir_insee_extracts = os.path.join(path_data,
                                       'data_insee',
                                       'data_extracts')

# #########################
# LOAD INFO STATIONS
# #########################

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str},
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
df_info.set_index('id_station', inplace = True)

# Exclude highway
df_info = df_info[df_info['highway'] != 1]

# ###########################
# LOAD INFO TA FIXED
# ###########################

df_info_ta = pd.read_csv(os.path.join(path_dir_built_csv,
                                      'df_info_ta_fixed.csv'),
                         encoding = 'utf-8',
                         dtype = {'id_station' : str,
                                  'adr_zip' : str,
                                  'adr_dpt' : str,
                                  'ci_1' : str,
                                  'ci_ardt_1' :str,
                                  'ci_2' : str,
                                  'ci_ardt_2' : str,
                                  'dpt' : str},
                         parse_dates = [u'day_%s' %i for i in range(4)] +\
                                       ['pp_chge_date', 'ta_chge_date'])
df_info_ta.set_index('id_station', inplace = True)

# #############
# FRA BASEMAP
# #############

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

df_dpt = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.departements_fr],
                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.departements_fr_info],
                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.departements_fr_info],
                       'reg_name' : [d['NOM_REGION'] for d in m_fra.departements_fr_info],
                       'reg_code' : [d['CODE_REG'] for d in m_fra.departements_fr_info]})

df_dpt = df_dpt[df_dpt['reg_name'] != 'CORSE']

#df_dpt['patches'] = df_dpt['poly'].map(lambda x: PolygonPatch(x,
#                                                              facecolor='#FFFFFF', # '#555555'
#                                                              edgecolor='#555555', # '#787878'
#                                                              lw=.25, alpha=.3, zorder=1))

df_com = pd.DataFrame({'poly'       : [Polygon(xy) for xy in m_fra.communes_fr],
                       'insee_code' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'com_name'   : [d['NOM_COMM'] for d in m_fra.communes_fr_info],
                       'dpt_name'   : [d['NOM_DEPT'] for d in m_fra.communes_fr_info],
                       'reg_name'   : [d['NOM_REGION'] for d in m_fra.communes_fr_info],
                       'pop'        : [d['POPULATION'] for d in m_fra.communes_fr_info],
                       'surf'       : [d['SUPERFICIE'] for d in m_fra.communes_fr_info],
                       'x_cl'       : [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl'       : [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info]})

df_com = df_com[df_com['reg_name'] != 'CORSE']

df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)

df_com.sort(columns = ['insee_code', 'poly_area'],
            ascending = False,
            inplace = True)

# ####################
# PREPARE STATION GPS
# ####################

# need to improve gps coord (use zagaz info), for now temp fix

## check those with missing info => replace by geocoding, looks ok
#print df_info_ta[['lng_gc', 'lat_gc']][pd.isnull(df_info_ta['lng_gov_0'])].to_string()

# update those for which more recent info (fixes existing issues?)
for i in [1,2]:
  df_info_ta.loc[~pd.isnull(df_info_ta['lng_gov_%s' %i]),
                 'lng_gov_0'] = df_info_ta['lng_gov_%s' %i]
  df_info_ta.loc[~pd.isnull(df_info_ta['lat_gov_%s' %i]),
                 'lat_gov_0'] = df_info_ta['lat_gov_%s' %i]
# use geocoding if no info
df_info_ta.loc[pd.isnull(df_info_ta['lng_gov_0']), 'lng_gov_0'] = df_info_ta['lng_gc']
df_info_ta.loc[pd.isnull(df_info_ta['lat_gov_0']), 'lat_gov_0'] = df_info_ta['lat_gc']
# fix issue detected: inversion of lat and lng...
#len(df_info_ta[df_info_ta['lng_gov_0'] > df_info_ta['lat_gov_0']])
df_info_ta['lng'] = df_info_ta['lng_gov_0']
df_info_ta['lat'] = df_info_ta['lat_gov_0']
df_info_ta.loc[df_info_ta['lng_gov_0'] > df_info_ta['lat_gov_0'], 'lng'] = df_info_ta['lat_gov_0']
df_info_ta.loc[df_info_ta['lng_gov_0'] > df_info_ta['lat_gov_0'], 'lat'] = df_info_ta['lng_gov_0']
df_info_ta['point'] = df_info_ta[['lng', 'lat']].apply(\
                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)

## #############################################
## ALL TOTAL ACCESS AT THE END OF PERIOD STUDIED
## #############################################
#
#plt.clf()
#fig = plt.figure()
#ax1 = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
#ax1.scatter([store.x for store in df_info_ta['point']],
#            [store.y for store in df_info_ta['point']],
#            s = 20, marker = 'o', lw=1, facecolor = '#FE9A2E', edgecolor = 'w', alpha = 0.4,
#            antialiased = True, zorder = 3)
#df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
#                      PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
#pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
#ax1.add_collection(pc_2)
#ax1.autoscale_view(True, True, True)
#ax1.axis('off')
#ax1.set_title('Total Access in 2014' , loc = 'left')
## plt.subplots_adjust(left=.1, right=0.95, bottom=0.1, top=0.95, wspace=0, hspace=0)
#plt.tight_layout()
#fig.set_size_inches(10, 15) # set the image width to 722px
#plt.show()
#
## #####################################################
## ALL EX ELF TOTAL ACCESS AT THE END OF PERIOD STUDIED
## #####################################################
#
## no ELF remaining?
#plt.clf()
#fig = plt.figure()
#ax1 = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
#ax1.scatter([store.x for store in df_info_ta['point'][df_info_ta['brand_0'] == 'ELF']],
#            [store.y for store in df_info_ta['point'][df_info_ta['brand_0'] == 'ELF']],
#            s = 20, marker = 'o', lw=1, facecolor = '#FE9A2E', edgecolor = 'w', alpha = 0.4,
#            antialiased = True, zorder = 3)
#df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
#                      PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
#pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
#ax1.add_collection(pc_2)
#ax1.autoscale_view(True, True, True)
#ax1.axis('off')
#ax1.set_title('Elf rebranded Total Access as of 2014' , loc = 'left')
## plt.subplots_adjust(left=.1, right=0.95, bottom=0.1, top=0.95, wspace=0, hspace=0)
#plt.tight_layout()
#fig.set_size_inches(10, 15) # set the image width to 722px
#plt.show()
#
## #####################################################
## ALL EX ELF TOTAL ACCESS AT THE END OF PERIOD STUDIED
## #####################################################
#
#plt.clf()
#fig = plt.figure()
#ax1 = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
#ax1.scatter([store.x for store in df_info_ta['point'][df_info_ta['brand_0'] == 'TOTAL']],
#            [store.y for store in df_info_ta['point'][df_info_ta['brand_0'] == 'TOTAL']],
#            s = 20, marker = 'o', lw=1, facecolor = '#FE9A2E', edgecolor = 'w', alpha = 0.4,
#            antialiased = True, zorder = 3)
#df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
#                      PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
#pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
#ax1.add_collection(pc_2)
#ax1.autoscale_view(True, True, True)
#ax1.axis('off')
#ax1.set_title('Total rebranded Total Access as of 2014' , loc = 'left')
## plt.subplots_adjust(left=.1, right=0.95, bottom=0.1, top=0.95, wspace=0, hspace=0)
#plt.tight_layout()
#fig.set_size_inches(10, 15) # set the image width to 722px
#plt.show()

# ###########################################################
# ALL TOTAL ACCESS: ELF + TOTAL AT THE END OF PERIOD STUDIED
# ##########################################################

# background: departments
# todo: add legend + other (previous brand unknown or outside total)

plt.clf()
fig = plt.figure()
ax1 = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
ax1.scatter([store.x for store in df_info_ta['point'][df_info_ta['brand_0'] == 'TOTAL']],
            [store.y for store in df_info_ta['point'][df_info_ta['brand_0'] == 'TOTAL']],
            s = 20, marker = 'o', lw=1, facecolor = '#FE2E2E', edgecolor = 'w', alpha = 0.4,
            antialiased = True, zorder = 3)
ax1.scatter([store.x for store in df_info_ta['point'][df_info_ta['brand_0'] == 'ELF']],
            [store.y for store in df_info_ta['point'][df_info_ta['brand_0'] == 'ELF']],
            s = 20, marker = 'o', lw=1, facecolor = '#2E64FE', edgecolor = 'w', alpha = 0.4,
            antialiased = True, zorder = 3)
df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                      PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
ax1.add_collection(pc_2)
ax1.autoscale_view(True, True, True)
ax1.axis('off')
ax1.set_title('Total Access as of 2014', loc = 'left')
# plt.subplots_adjust(left=.1, right=0.95, bottom=0.1, top=0.95, wspace=0, hspace=0)
plt.tight_layout()
fig.set_size_inches(10, 15) # set the image width to 722px
plt.savefig(os.path.join(path_dir_built_graphs,
                         'maps',
                         'total_access.png'),
            dpi=300,
            alpha=True,
            bbox_inches = 'tight')

# todo: backgroup: top 10/100 (whatever) AU/UU/BV (how many inside/outside => what makes sense?)
# idea: how many market touched? urban only phenomenon?

# ###########################################################
# ALL TOTAL ACCESS: ELF + TOTAL HISTORY
# ##########################################################

df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                      PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))

ls_dates = ['2012', '2012-06', '2013', '2013-06', '2014', '2014-06']
 
plt.clf()
fig = plt.figure()

for i, date in enumerate(ls_dates, start = 1):
  df_temp = df_info_ta[df_info_ta['TA_day'] <= date]

  ax1 = fig.add_subplot(320 + i, aspect = 'equal') #, frame_on = False)
  #ax1.scatter([store.x for store in df_temp['point'][df_temp['brand_0'] == 'TOTAL']],
  #            [store.y for store in df_temp['point'][df_temp['brand_0'] == 'TOTAL']],
  #            s = 20, marker = 'o', lw=1, facecolor = '#FE2E2E', edgecolor = 'w', alpha = 0.4,
  #            antialiased = True, zorder = 3)
  ax1.scatter([store.x for store in df_temp['point'][df_temp['brand_0'] == 'ELF']],
              [store.y for store in df_temp['point'][df_temp['brand_0'] == 'ELF']],
              s = 20, marker = 'o', lw=1, facecolor = '#2E64FE', edgecolor = 'w', alpha = 0.4,
              antialiased = True, zorder = 3)
  pc_1 = PatchCollection(df_dpt['patches'], match_original=True)
  ax1.add_collection(pc_1)
  ax1.autoscale_view(True, True, True)
  ax1.axis('off')
  ax1.set_title(date, loc = 'left')

plt.subplots_adjust(left=.1, right=0.95, bottom=0.1, top=0.95, wspace=0, hspace=0)
plt.tight_layout()
fig.set_size_inches(10, 15) # set the image width to 722px
#plt.show()
plt.savefig(os.path.join(path_dir_built_graphs,
                         'maps',
                         'history_elf_total_access.png'),
            dpi=300,
            alpha=True,
            bbox_inches = 'tight')
