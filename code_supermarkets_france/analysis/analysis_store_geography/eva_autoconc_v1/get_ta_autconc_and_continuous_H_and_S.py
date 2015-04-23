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

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_png = os.path.join(path_dir_qlmc, 'data_built' , 'data_png')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###################
# LOAD DF HYPER COMP
# ###################

# Hyper vs. hyper only
df_hvh = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_eval_comp_H_v_H.csv'),
                     dtype = {u'Code INSEE' : str,
                              u'Code INSEE ardt' : str,
                              u'N°Siren' : str,
                              u'N°Siret' : str},
                     parse_dates = [u'DATE ouv', u'DATE ferm', u'DATE réouv',
                                    u'DATE chg enseigne', u'DATE chgt surf'],
                     encoding = 'latin-1')

# Hyper vs hyper, super and discounters
df_hva = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_eval_comp_H_v_all.csv'),
                     dtype = {u'Code INSEE' : str,
                              u'Code INSEE ardt' : str,
                              u'N°Siren' : str,
                              u'N°Siret' : str},
                     parse_dates = [u'DATE ouv', u'DATE ferm', u'DATE réouv',
                                    u'DATE chg enseigne', u'DATE chgt surf'],
                     encoding = 'latin-1')

# Proxies for hyper demand: population around
df_demand_h = pd.read_csv(os.path.join(path_dir_built_csv,
                                       'df_store_demand_H.csv'),
                          dtype = {u'Code INSEE' : str,
                                   u'Code INSEE ardt' : str,
                                   u'N°Siren' : str,
                                   u'N°Siret' : str},
                          parse_dates = [u'DATE ouv', u'DATE ferm', u'DATE réouv',
                                         u'DATE chg enseigne', u'DATE chgt surf'],
                          encoding = 'latin-1')

# Preliminary display
ls_disp_lsa = [u'Enseigne',
               u'ADRESSE1',
               u'Code postal',
               u'Ville'] # u'Latitude', u'Longitude']

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

df_hvh.set_index('Ident', inplace = True)
df_hva.set_index('Ident', inplace = True)

df_hvh = pd.merge(df_hvh,
                  df_hva[['hva_ac_nb_groups',
                          'hva_ac_group_share',
                          'hva_group_share',
                          'ac_nb_stores']],
                  how = 'left',
                  right_index = True,
                  left_index = True)

df_demand_h.set_index('Ident', inplace = True)

df_hvh = pd.merge(df_hvh,
                  df_demand_h[['pop', 'ac_pop']],
                  how = 'left',
                  right_index = True,
                  left_index = True)

df_hvh['ac_hypers_by_pop_ac'] = df_hvh['ac_nb_hypers'] / df_hvh['ac_pop'] * 100000
df_hvh['ac_hypers_by_pop'] = df_hvh['ac_nb_hypers'] / df_hvh['pop'] * 100000
df_hvh['ac_stores_by_pop_ac'] = df_hvh['ac_nb_stores'] / df_hvh['ac_pop'] * 1000000
df_hvh['ac_stores_by_pop'] = df_hvh['ac_nb_stores'] / df_hvh['pop'] * 100000

# #########################
# LOAD DF MUNICIPALITY HHI
# #########################

df_hhi = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_municipality_hhi.csv'),
                     dtype = {'code_insee' : str,
                                           'dpt' : str},
                     encoding = 'latin-1')
df_hhi.set_index('code_insee', inplace = True)

# #####################
# STATS DES COMPETITION
# #####################

# Examine nb competitors
print u'\nAll figures by pop are by 100,000 inhabitants'

print u'\n', df_hvh[['ac_nb_hypers', 'ac_hypers_by_pop_ac', 'ac_hypers_by_pop']].describe()
print u'\n', df_hvh[['ac_nb_stores', 'ac_stores_by_pop_ac', 'ac_stores_by_pop']].describe()

# Display dpt largest quartiles

print u'\nRegions of stores in highest quartile in terms of nb stores in market'
print df_hvh['Reg'][df_hvh['ac_nb_stores'] >= df_hvh['ac_nb_stores']\
        .quantile(q = 0.75)].value_counts()

print u'\nRegions of stores in highest quartile in terms of nb stores by pop'
print df_hvh['Reg'][df_hvh['ac_stores_by_pop'] >= df_hvh['ac_stores_by_pop']\
        .quantile(q = 0.75)].value_counts()

print u'\nRegions of stores in lowest quartile in terms of nb stores in market'
print df_hvh['Reg'][df_hvh['ac_nb_stores'] <= df_hvh['ac_nb_stores']\
        .quantile(q = 0.25)].value_counts()

print u'\nRegions of stores in lowest quartile in terms of nb stores in market'
print df_hvh['Reg'][df_hvh['ac_stores_by_pop'] <= df_hvh['ac_stores_by_pop']\
        .quantile(q = 0.25)].value_counts()

print u'\nRegions of stores with st. less than 3 groups in market'
print df_hvh['Reg'][df_hvh['hvh_ac_nb_groups'] < 4].value_counts()

print u'\nRegions of stores with st. less than 3 H groups and above 50% H market share (AC):'
print df_hvh['Reg'][(df_hvh['hvh_ac_nb_groups'] < 4) &\
                    (df_hvh['hvh_ac_group_share'] > 0.5)].value_counts()

print u'\nRegions of stores with st. less than 3 groups and above 50% market share (AC):'
print df_hvh['Reg'][(df_hvh['hva_ac_nb_groups'] < 4) &\
                    (df_hvh['hva_ac_group_share'] > 0.5)].value_counts()

print u'\nRegions of stores with st. less than 3 groups and above 50% H market share (cont):'
print df_hvh['Reg'][(df_hvh['hvh_ac_nb_groups'] < 4) &\
                    (df_hvh['hvh_group_share'] > 0.5)].value_counts()

print u'\nRegions of stores with st. less than 3 groups and above 50% market share (cont):'
print df_hvh['Reg'][(df_hvh['hva_ac_nb_groups'] < 4) &\
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
        [ls_disp_lsa + ['Surf Vente', 'Reg']].to_string()

df_hvh.to_csv(os.path.join(path_dir_built_csv,
                           'df_hyper_competition.csv'),
              encoding = 'latin-1',
              float_format ='%.3f',
              date_format='%Y%m%d',
              index = False)

# ############################
# MAP OF LOW COMPETITION AREAS
# ############################

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

# DPTS
df_dpt = pd.DataFrame({'poly' : [Polygon(xy) for xy in m_fra.departements_fr],
                       'dpt_name' : [d['NOM_DEPT'] for d in m_fra.departements_fr_info],
                       'dpt_code' : [d['CODE_DEPT'] for d in m_fra.departements_fr_info],
                       'reg_name' : [d['NOM_REGION'] for d in m_fra.departements_fr_info],
                       'reg_code' : [d['CODE_REG'] for d in m_fra.departements_fr_info]})

df_dpt = df_dpt[df_dpt['reg_name'] != 'CORSE']

# MUNICIPALITIES
df_com = pd.DataFrame({'poly'       : [Polygon(xy) for xy in m_fra.communes_fr],
                       'insee_code' : [d['INSEE_COM'] for d in m_fra.communes_fr_info],
                       'com_name'   : [d['NOM_COMM'] for d in m_fra.communes_fr_info],
                       'dpt_name'   : [d['NOM_DEPT'] for d in m_fra.communes_fr_info],
                       'reg_name'   : [d['NOM_REGION'] for d in m_fra.communes_fr_info],
                       'pop'        : [d['POPULATION'] for d in m_fra.communes_fr_info],
                       'surf'       : [d['SUPERFICIE'] for d in m_fra.communes_fr_info],
                       'x_cl'       : [d['X_CHF_LIEU'] for d in m_fra.communes_fr_info],
                       'y_cl'       : [d['Y_CHF_LIEU'] for d in m_fra.communes_fr_info]})
df_com['poly_area'] = df_com['poly'].apply(lambda x: x.area)

df_com.sort(columns = ['insee_code', 'poly_area'],
            ascending = False,
            inplace = True)

# ADD HHI
df_com.set_index('insee_code', inplace = True)
df_com = pd.merge(df_com,
                  df_hhi[['wgt_store_surf', 'hhi']],
                  how = 'left',
                  left_index = True,
                  right_index = True)


# PREPARE GPS POINTS
df_hvh['point'] = df_hvh[['Longitude', 'Latitude']].apply(\
                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)

plt.clf()
fig = plt.figure()
ax1 = fig.add_subplot(111, aspect = 'equal') #, frame_on = False)

le_1 = ax1.scatter([store.x for store in df_hvh['point'].ix[ls_hyper_low_comp]],
                   [store.y for store in df_hvh['point'].ix[ls_hyper_low_comp]],
                   s = 20, marker = 'o', lw=0, facecolor = '#FE2E2E', edgecolor = 'w', alpha = 0.8,
                   antialiased = True, zorder = 3)

# dpt borders
df_dpt['patches'] = df_dpt['poly'].map(lambda x:\
                      PolygonPatch(x, fc = 'w', ec='#000000', lw=0.6, alpha=1, zorder=1))
pc_2 = PatchCollection(df_dpt['patches'], match_original=True)
le_2 = ax1.add_collection(pc_2)

# communes with low comp
df_com['patches'] = df_com['poly'].map(lambda x:\
                      PolygonPatch(x, fc = 'b', ec= 'w', lw=0.1, alpha=0.6, zorder=2))
pc_3 = PatchCollection(df_com['patches'][df_com['hhi'] > 2500], match_original=True)
le_3 = ax1.add_collection(pc_3)

# fake object for legend
from matplotlib.lines import Line2D
le_4 = Line2D([0], [0], linestyle="none", marker="o", alpha=0.6, markersize=10, markerfacecolor="b")

ax1.autoscale_view(True, True, True)
ax1.axis('off')
#ax1.set_title('Hypermarkets with low competition', loc = 'left')
# plt.subplots_adjust(left=.1, right=0.95, bottom=0.1, top=0.95, wspace=0, hspace=0)
plt.tight_layout()
plt.legend((le_1, le_4),
           ('Hypers w/ low competition', 'Municipalities with HHI > 2500'),
            scatterpoints = 1, numpoints = 1, loc = 'best')
fig.set_size_inches(10, 15) # set the image width to 722px
#plt.savefig(os.path.join(path_dir_built_graphs,
#                         'maps',
#                         'total_access.png'),
#            dpi=300,
#            alpha=True,
#            bbox_inches = 'tight')
plt.show()

# drop communes duplicates (several polygons: can not draw map as well after that!)
df_com.reset_index(inplace = True) # index name lost?
df_com.drop_duplicates('index', inplace = True)
df_com.set_index('index', inplace = True)

ls_percentiles = [0.1, 0.25, 0.5, 0.75, 0.9]
print df_hhi['hhi'].describe(percentiles = ls_percentiles)

# requires package wquantiles
import weighted
for quantile in ls_percentiles:
  print weighted.quantile(df_hhi['hhi'], df_hhi['pop'], quantile)

# todo: code weighted mean and std (count, min, max, unchanged) + check vs. STATA

df_com.sort('hhi', ascending = False, inplace = True)
print df_com[['com_name', 'dpt_name', 'reg_name', 'pop', 'wgt_store_surf', 'hhi']][0:20].to_string()

print 'u\nPop living in municipalies with hhi above 2500:'
print df_com['pop'][df_com['hhi'] > 2500].sum()
