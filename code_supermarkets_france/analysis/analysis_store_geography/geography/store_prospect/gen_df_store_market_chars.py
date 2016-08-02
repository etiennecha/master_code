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
                              u'c_siret' : str,
                              u'id_lsa' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

# COMP: STORE CENTERED
ls_comp_files = [['10km', 'df_store_prospect_comp_HS_v_all_10km.csv'],
                 ['20km', 'df_store_prospect_comp_HS_v_all_20km.csv'],
                 ['1025km', 'df_store_prospect_comp_HS_v_all_1025km.csv']]

ls_sub_comp_cols = ['ac_nb_comp',
                    'ac_group_share',
                    'group_share',
                    'ac_hhi',
                    'hhi']

dict_df_comp = {}
for comp_title, comp_file_name in ls_comp_files:
  df_comp = pd.read_csv(os.path.join(path_built_csv,
                                     '201407_competition',
                                     comp_file_name),
                        dtype = {'id_lsa' : str},
                        encoding = 'utf-8')
  ls_sub_comp_cols_2 = ['{:s}_{:s}'.format(x, comp_title) for x in ls_sub_comp_cols]
  dict_repl = dict(zip(ls_sub_comp_cols,
                       ls_sub_comp_cols_2))
  df_comp.rename(columns = dict_repl,
                 inplace = True)
  if comp_title == '1025km':
    dict_df_comp[comp_title] = df_comp[['id_lsa', 'dist_cl_comp', 'dist_cl_groupe'] +\
                                       ls_sub_comp_cols_2]
  else:
    dict_df_comp[comp_title] = df_comp[['id_lsa'] + ls_sub_comp_cols_2]

df_comp = dict_df_comp['1025km']
df_comp = pd.merge(df_comp,
                   dict_df_comp['10km'],
                   on = 'id_lsa',
                   how = 'left')
df_comp = pd.merge(df_comp,
                   dict_df_comp['20km'],
                   on = 'id_lsa',
                   how = 'left')

# DEMAND: STORE CENTERED
df_demand = pd.read_csv(os.path.join(path_built_csv,
                                     '201407_competition',
                                     'df_store_prospect_demand.csv'),
                        dtype = {'id_lsa' : str},
                        encoding = 'utf-8')

## temp?
#df_demand.rename(columns = {'pop_ac_10km'   : '10km_ac_pop',
#                            'pop_ac_20km'   : '20km_ac_pop',  
#                            'pop_ac_25km'   : '25km_ac_pop',
#                            'pop_ac_1025km' : '1025km_ac_pop',
#                            'pop_cont_8'    : '8_pop',
#                            'pop_cont_10'   : '10_pop',
#                            'pop_cont_12'   : '12_pop'},
#                 inplace = True)

# MARKETS: INSEE AREAS
df_insee_markets = pd.read_csv(os.path.join(path_built_csv,
                                            '201407_competition',
                                            'df_insee_markets.csv'),
                               dtype = {'CODGEO': str,
                                        'AU2010' : str,
                                        'UU2010' : str,
                                        'BV' : str,
                                        'AU2010_O' : str,
                                        'UU2010_O' : str},
                               encoding = 'utf-8')

# ##############
# MERGE DATA
# ##############

# Got Info only for H & S... other null for now
df_mc = pd.merge(df_lsa[['id_lsa', 'c_insee']],
                 df_comp,
                 on = 'id_lsa',
                 how = 'left')

df_mc = pd.merge(df_mc,
                 df_demand,
                 on = 'id_lsa',
                 how = 'left')

df_mc.rename(columns = {'c_insee' : 'CODGEO'},
             inplace = True)

df_mc = pd.merge(df_mc,
                 df_insee_markets,
                 on = 'CODGEO',
                 how = 'left')

df_mc.to_csv(os.path.join(path_built_csv,
                          '201407_competition',
                          'df_store_market_chars.csv'),
             encoding = 'utf-8',
             float_format ='%.3f',
             index = False)
