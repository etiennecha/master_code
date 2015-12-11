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

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')

path_dir_built_ta = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_total_access')
path_dir_built_ta_json = os.path.join(path_dir_built_ta, 'data_json')
path_dir_built_ta_csv = os.path.join(path_dir_built_ta, 'data_csv')
path_dir_built_ta_graphs = os.path.join(path_dir_built_ta, 'data_graphs')

path_dir_insee_extracts = os.path.join(path_data,
                                       'data_insee',
                                       'data_extracts')

# #########
# LOAD DATA
# #########

# DF INFO

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
df_info = df_info[df_info['highway'] != 1]

# DF TOTAL ACCESS

#str_ta_ext = '_3km_dist_order'
str_ta_ext = '_5km'

df_ta = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                 'df_total_access{:s}.csv'.format(str_ta_ext)),
                              dtype = {'id_station' : str,
                                       'id_total_ta' : str},
                              encoding = 'utf-8',
                              parse_dates = ['start', 'end',
                                             'ta_date_beg',
                                             'ta_date_end',
                                             'date_min_total_ta',
                                             'date_max_total_ta',
                                             'date_min_elf_ta',
                                             'date_max_elf_ta'])
df_ta.set_index('id_station', inplace = True)

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

df_ta['point'] = df_ta[['lng', 'lat']].apply(\
                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)
df_ta_converted = df_ta[df_ta['brand_last'] == 'TOTAL_ACCESS']

# ###########################################################
# ALL TOTAL ACCESS: ELF + TOTAL AT THE END OF PERIOD STUDIED
# ##########################################################

# background: departments
# todo: add legend + other (previous brand unknown or outside total)

plt.clf()
fig = plt.figure()
ax1 = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)
l1 = ax1.scatter([store.x for store in df_ta_converted['point'][df_ta_converted['brand_0'] == 'TOTAL']],
                 [store.y for store in df_ta_converted['point'][df_ta_converted['brand_0'] == 'TOTAL']],
                 s = 20, marker = 'o', lw=1, facecolor = '#FE2E2E', edgecolor = 'w', alpha = 0.4,
                 antialiased = True, zorder = 3)
l2 = ax1.scatter([store.x for store in df_ta_converted['point'][df_ta_converted['brand_0'] == 'ELF']],
                 [store.y for store in df_ta_converted['point'][df_ta_converted['brand_0'] == 'ELF']],
                 s = 20, marker = 'o', lw=1, facecolor = '#2E64FE', edgecolor = 'w', alpha = 0.4,
                 antialiased = True, zorder = 3)
df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                      PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
pc_2 = PatchCollection(df_dpt['patches'], match_original=True)

ax1.legend((l1, l2),
           ('Ex-Total', 'Ex-Elf'),
           loc='lower right',
           scatterpoints=1,
           ncol = 2)
ax1.add_collection(pc_2)
ax1.autoscale_view(True, True, True)
ax1.axis('off')
#ax1.set_title('Total Access as of 2014', loc = 'left')
# plt.subplots_adjust(left=.1, right=0.95, bottom=0.1, top=0.95, wspace=0, hspace=0)
plt.tight_layout()
fig.set_size_inches(10, 15) # set the image width to 722px
plt.savefig(os.path.join(path_dir_built_ta_graphs,
                         'maps',
                         'total_access.png'),
            dpi=300,
            alpha=True,
            bbox_inches = 'tight')

# todo: backgroup: top 10/100 (whatever) AU/UU/BV (how many inside/outside => what makes sense?)
# idea: how many market touched? urban only phenomenon?

# ###########################################################
# ALL TOTAL ACCESS: ELF + TOTAL HISTORY (6 SMALL MAPS)
# ##########################################################

df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                      PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))

ls_dates = ['2012-01', '2012-06', '2013-01', '2013-06', '2014-01', '2014-06']
 
plt.clf()
fig = plt.figure()

for i, date in enumerate(ls_dates, start = 1):
  df_temp = df_ta_converted[df_ta_converted['ta_date_end'] <= date]

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
plt.savefig(os.path.join(path_dir_built_ta_graphs,
                         'maps',
                         'history_elf_total_access.png'),
            dpi=300,
            alpha=True,
            bbox_inches = 'tight')

## ###########################################################
## ALL TOTAL ACCESS: ELF + TOTAL HISTORY (6 SMALL MAPS 2 BY 2)
## ##########################################################
#
#df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
#                      PolygonPatch(x, fc = '#FFFFFF', ec='#000000', lw=.2, alpha=1., zorder=1))
#
#ls_dates = ['2011-12-31', '2012-06-30', '2012-12-31', '2013-06-30', '2013-12-31', '2014-06-30']
# 
#ls_loop = [[0, 2, '2012'],
#           [2, 4, '2013'],
#           [4, 6, '2014']]
#
#for start, end, str_title in ls_loop:
#  plt.clf()
#  fig = plt.figure()
#  fig.set_size_inches(12, 10) # set the image width to 722px
#  for i, date in enumerate(ls_dates[start:end], start = 1):
#    df_temp = df_ta_converted[df_ta_converted['ta_date_end'] <= date]
#  
#    ax1 = fig.add_subplot(120 + i, aspect = 'equal') #, frame_on = False)
#    l1 = ax1.scatter([store.x for store in df_temp['point'][df_temp['brand_0'] == 'TOTAL']],
#                     [store.y for store in df_temp['point'][df_temp['brand_0'] == 'TOTAL']],
#                     s = 15, marker = 'o', lw=0, facecolor = '#FE2E2E', edgecolor = 'w', alpha = 0.3,
#                     antialiased = True, zorder = 3)
#    l2 = ax1.scatter([store.x for store in df_temp['point'][df_temp['brand_0'] == 'ELF']],
#                     [store.y for store in df_temp['point'][df_temp['brand_0'] == 'ELF']],
#                     s = 15, marker = 'o', lw=0, facecolor = '#2E64FE', edgecolor = 'w', alpha = 0.3,
#                     antialiased = True, zorder = 3)
#    pc_1 = PatchCollection(df_dpt['patches'], match_original=True)
#    ax1.add_collection(pc_1)
#    ax1.autoscale_view(True, True, True)
#    ax1.axis('off')
#    ax1.set_title(date, loc = 'left')
#  
#  ax1.legend((l1, l2),
#             ('Total', 'Elf'),
#             bbox_to_anchor=(-0.08, -0.05),
#             loc='lower center',
#             scatterpoints=1,
#             ncol = 2)
#  # leg.get_frame().set_linewidth(0.0)
#  plt.subplots_adjust(left=.1, right=0.95, bottom=0.1, top=0.95, wspace=0, hspace=0)
#  plt.tight_layout()
#  #plt.show()
#  plt.savefig(os.path.join(path_dir_built_ta_graphs,
#                           'maps',
#                           'map_network_%s.png' %str_title),
#              dpi=300,
#              alpha=True,
#              bbox_inches = 'tight')
