#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import datetime as datetime
import pandas as pd
import matplotlib.pyplot as plt
import pprint

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_built_graphs = os.path.join(path_built,
                                 'data_graphs')

path_insee_extracts = os.path.join(path_data,
                                   'data_insee',
                                   'data_extracts')

path_geo_dpt = os.path.join(path_data, 'data_maps', 'GEOFLA_DPT_WGS84', 'DEPARTEMENT')
path_geo_com = os.path.join(path_data, 'data_maps', 'GEOFLA_COM_WGS84', 'COMMUNE')

# ##########
# LOAD DATA
# ##########

# LSA Data
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

# LSA Comp (file with closest comp and closest same group)
df_lsa_comp = pd.read_csv(os.path.join(path_built_csv,
                                       '201407_competition',
                                       'df_store_prospect_comp_HS_v_all_1025km.csv'),
                          encoding = 'utf-8')
df_lsa = pd.merge(df_lsa,
                  df_lsa_comp[['id_lsa', 'dist_cl_comp', 'dist_cl_groupe']],
                  how = 'left',
                  on = 'id_lsa')

# INSEE DATA

# Mapping of municipality codes to insee areas codes
df_insee_areas = pd.read_csv(os.path.join(path_insee_extracts,
                                          u'df_insee_areas.csv'),
                             encoding = 'UTF-8')

df_au_agg = pd.read_csv(os.path.join(path_insee_extracts,
                                     u'df_au_agg_final.csv'),
                        encoding = 'UTF-8')

df_uu_agg = pd.read_csv(os.path.join(path_insee_extracts,
                                     u'df_uu_agg_final.csv'),
                        encoding = 'UTF-8')

#df_bv_agg = pd.read_csv(os.path.join(path_insee_extracts,
#                                     u'df_bv_agg_final.csv'),
#                        encoding = 'UTF-8')

# Socio demographic data on insee areas
df_com = pd.read_csv(os.path.join(path_insee_extracts,
                                  'data_insee_extract.csv'),
                     encoding = 'UTF-8',
                     dtype = {u'DEP': str,
                              u'CODGEO' : str,
                              u'UU2010' : str,
                              u'AU2010' : str})
# Paris/Lyon/Marseille: one line each here

# GET RID OF DOMTOM & FORMAT MUNICIPALITY CODE
df_insee_areas =\
  df_insee_areas[df_insee_areas['CODGEO'].str.slice(stop = -3) != '97']
df_com = df_com[~(df_com['DEP'].isin(['971', '972', '973', '974']))]
# Exact same list of municipalities in both files
# Can use df_insee_areas to avoid codes which do no correspond to geo areas
df_lsa = pd.merge(df_lsa,
                  df_insee_areas,
                  left_on = 'c_insee',
                  right_on = 'CODGEO',
                  how = 'left')

pd.set_option('float_format', '{:10,.0f}'.format)

format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##################
# PREPARE INSEE DATA
# ##################

# COM

# Drop AU and UU labels to avoid conflicts with AU and UU files
df_com.drop(['LIBAU2010', 'LIBUU2010'], axis = 1, inplace = True)

# AU

# Get rid of non geo areas
df_au_agg = df_au_agg[~df_au_agg['AU2010'].isin(['000', '997', '998'])]
# Get rid of DOM TOM
df_au_agg = df_au_agg[~df_au_agg['AU2010'].str.slice(0, -1).isin(['9A', '9B', '9C',
                                                                  '9D', '9E', '9F'])]
# Rename some AUs
dict_rename_libau = {u'Marseille - Aix-en-Provence' : u'Marseille - Aix',
                     u'(partie française)' : u'(fr)',
                     u'Clermont-Ferrand' : u'Clermont-Fer.'}
def rename_field(some_str, dict_rename):
  for k,v in dict_rename.items():
    some_str = some_str.replace(k,v).strip()
  return some_str
df_au_agg['LIBAU2010'] = df_au_agg['LIBAU2010'].apply(\
                           lambda x: rename_field(x, dict_rename_libau))

# UU

# Get rid of non geo areas
df_uu_agg = df_uu_agg[~df_uu_agg['LIBUU2010'].str.contains(u'Communes rurales')]
# Get rid of DOM TOM
df_uu_agg = df_uu_agg[~df_uu_agg['UU2010'].str.slice(0, -3).isin(['9A', '9B', '9C',
                                                                  '9D', '9E', '9F'])]
# Rename some UUs
df_uu_agg['LIBUU2010'] = df_uu_agg['LIBUU2010'].apply(\
                           lambda x: rename_field(x, dict_rename_libau))



# Loop (make sure no conflicts)
# df_com    : CODGEO
# df_au_agg : AU2010
# df_uu_agg : UU2010

dict_df_areas = {}

for title_area, code_area, df_area in [['CO', 'CODGEO', df_com],
                                       ['UU',  'UU2010', df_uu_agg],
                                       ['AU',  'AU2010', df_au_agg]]:

  df_area.rename(columns = {'P10_POP' : 'area_pop',
                           'SUPERF' : 'area_surface',
                           'QUAR1UC10': 'area_quar1_rev',
                           'QUAR2UC10': 'area_med_rev',
                           'QUAR3UC10': 'area_quar3_rev',
                           'P10_MEN' :  'area_nb_hh', # nb households
                           'P10_RP_VOIT1P' : 'area_nb_mot_hh', # nb households with one car+
                           'LIBGEO':   'area_label',
                           'LIBAU2010' : 'area_label',
                           'LIBUU2010' : 'area_label'},
                inplace = True)
  
  ls_drop_cols = ['MENFIS10', 'PMENFIS10', 'MENIMP10',
                  'RDUC10', 'PTSA10', 'PBEN10', 'PPEN10', 'PAUT10'
                  'P10_LOG', 'P10_PMEN',
                  'P10_RP_VOIT1', 'P10_RP_VOIT2P', 'POPDENSITY10']
  df_area.drop([x for x in ls_drop_cols if x in df_area.columns],
               axis = 1,
               inplace = True)

  df_area['area_pop_density'] = df_area['area_pop'] / df_area['area_surface'].astype(float)
  
  # Nb stores in area
  se_area_vc = df_lsa[code_area].value_counts()
  df_area.set_index(code_area, inplace = True)
  df_area['area_nb_stores'] = se_area_vc
  
  # Pop by store nb
  df_area['area_pop_by_store_nb'] = df_area['area_pop'] / df_area['area_nb_stores']
  
  # Pop by store surface (nb inhab by squared meter)
  df_area['area_store_surface'] = df_lsa[[code_area, 'surface']].\
                                   groupby(code_area)['surface'].sum()
  df_area['area_pop_by_store_surface'] = df_area['area_pop'] / df_area['area_store_surface']
  
  # Replace nan by 0 for nb stores (now only to avoid inf in area_pop_by_store_nb)
  df_area['area_nb_stores'].fillna(0, inplace = True)
  
  # Avg dist to closest competitor
  df_area['area_cl_comp_m'] = df_lsa[[code_area, 'dist_cl_comp']].\
                                groupby(code_area)['dist_cl_comp'].mean()
  df_area['area_cl_comp_s'] = df_lsa[[code_area, 'dist_cl_comp']].\
                                groupby(code_area)['dist_cl_comp'].std()

  # HHI
  df_surfaces = pd.pivot_table(df_lsa,
                               index = code_area,
                               columns = 'groupe',
                               values = 'surface',
                               aggfunc = 'sum')
  df_ms = df_surfaces.apply(lambda x: x/df_surfaces.sum(1))
  se_hhi = df_ms.apply(lambda x: (x**2).sum(), axis = 1)
  df_area['area_hhi'] = se_hhi * 10000
  df_area['area_cr_1'] = df_surfaces.max(1) / df_surfaces.sum(1) * 100
  df_area['area_gr_1'] = df_surfaces.T.idxmax()
  df_area['area_nb_gr_1'] = df_surfaces.apply(lambda row: len(row[row == row.max()]),
                                              axis = 1)
  
  df_area.sort('area_pop', ascending = False, inplace = True)
  dict_df_areas[title_area] = df_area

# ##################
# STATS DES
# ##################

dict_formatters = {'area_pop_by_store_surface' : format_float_float,
                   'area_cl_comp_m' : format_float_float,
                   'area_cl_comp_s' : format_float_float,
                   'area_hhi' : format_float_float}

lsd = ['area_label', 'area_pop', 'area_surface',
       'area_med_rev', 'area_pop_density',
       'area_nb_stores', 'area_pop_by_store_nb',
       'area_pop_by_store_surface',
       'area_cl_comp_m', 'area_cl_comp_s', 'area_hhi']

ls_sub_cols = ['label',
               'med_rev',
               'pop',
               'nb_stores',
               'store_surface',
               'nb_hh',
               'nb_mot_hh',
               'hhi',
               'cr_1',
               'gr_1',
               'nb_gr_1']

df_all = df_insee_areas.copy()
df_all.drop(['POP_MUN_2007'], axis = 1, inplace = True)

for title_area, code_area in [['CO', 'CODGEO'],
                              ['AU', 'AU2010'],
                              ['UU', 'UU2010']]:
  print()
  print(title_area)
  df_area = dict_df_areas[title_area]
  print('Total pop in areas: {:.0f}'.format(df_area['area_pop'].sum()))
  print('Total pop in areas w/o store: {:.0f}'.format(\
           df_area['area_pop'][df_area['area_nb_stores'] == 0].sum()))

  print()
  print('Display largest areas:')
  print(df_area[0:20][lsd].to_string(formatters = dict_formatters))
 
  print()
  print('Overview of areas:')
  print(df_area[['area_surface', 'area_nb_stores'] + lsd]\
          .describe().to_string(formatters = dict_formatters))
  
  # OUTPUT AREA FILE
  df_area.to_csv(os.path.join(path_built_csv,
                              '201407_competition',
                              'df_area_{:s}.csv'.format(title_area)),
                 encoding = 'utf-8',
                 float_format ='%.3f')

  # PREPARE FOR MERGER IN ONE FILE
  df_area.columns = [x.replace('area', title_area) for x in df_area.columns]
  df_area.reset_index(inplace = True, drop = False)
  
  ls_sub_cols_area = ['{:s}_{:s}'.format(title_area, x)\
                        for x in ls_sub_cols]
  df_all = pd.merge(df_all,
                    df_area[[code_area] + ls_sub_cols_area],
                    on = code_area,
                    how = 'left')

# OUTPUT FILE WITH ALL INSEE MARKETS
df_all.to_csv(os.path.join(path_built_csv,
                           '201407_competition',
                           'df_insee_markets.csv'),
              encoding = 'utf-8',
              float_format ='%.3f',
              index = False)

#df_co = dict_df_areas['CO']
#df_uu = dict_df_areas['UU']
#df_au = dict_df_areas['AU']
