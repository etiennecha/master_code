#!/usr/bin/python
# -*- coding: utf-8 -*-

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

# INSEE DATA

# Mapping of municipality codes to insee areas codes
df_insee_areas = pd.read_csv(os.path.join(path_insee_extracts,
                                          u'df_insee_areas.csv'),
                             encoding = 'UTF-8')

df_au_agg = pd.read_csv(os.path.join(path_insee_extracts,
                                     u'df_au_agg_final.csv'),
                        encoding = 'UTF-8')
# AU2010 read as str (some contains letters)

df_uu_agg = pd.read_csv(os.path.join(path_insee_extracts,
                                     u'df_uu_agg_final.csv'),
                        encoding = 'UTF-8')
# UU2010 read as str (some contains letters)

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

# ##########################
# ANALYSIS AT COMMUNE LEVEL
# ##########################

pd.set_option('float_format', '{:10,.0f}'.format)

# Why not here ? Right superf?
df_com['POPDENSITY10'] = df_com['P10_POP'] / df_com['SUPERF'].astype(float)
# No data on revenue... generate proper commune file

# COMMUNES WITH NO STORE
print u"\nNb of communes in Metro France: " +\
      u"{:5d}".format(len(df_com))
print u"\nPop in Metro France (2010): " +\
      u"{:12,.0f}".format(df_com['P10_POP'].sum())

se_com_vc = df_lsa['c_insee'].value_counts()
df_com.set_index('CODGEO', inplace = True)
df_com['Nb GS'] = se_com_vc
print u"\nNb of communes with a store: " +\
      u"{:5d}".format(len(df_com[~pd.isnull(df_com['Nb GS'])]))

pop_tot = df_com['P10_POP'].sum()
pop_nostore = df_com['P10_POP'][pd.isnull(df_com['Nb GS'])].sum()
print u'\nPercentage of French citizens (2010) with no store on "Commune": ' +\
      u"{:2.2f}".format(pop_nostore / pop_tot * 100)

df_com.sort('P10_POP', ascending=False, inplace=True)

format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# Pop and Pop by Grocery Store
df_com['P10_POP'] = df_com['P10_POP'] / 1000.0
df_com['Pop by GS'] = df_com['P10_POP'] / df_com['Nb GS']

# Surface and Pop by m2
df_com['Surface'] = df_lsa[['c_insee', 'surface']].\
                      groupby('c_insee')['surface'].sum()
df_com['Surface'] = df_com['Surface'] / 1000.0

df_com['Pop by surf'] = df_com['P10_POP'] / df_com['Surface']

df_com.rename(columns = {'P10_POP' : 'Pop',
                         'LIBGEO':   'Area',
                         'SUPERF' : 'Size',
                         'POPDENSITY10' : 'Pop density'},
              inplace = True)

dict_formatters = {'Pop' : format_float_int,
                   'Pop by GS' : format_float_float,
                   'Surf' : format_float_int,
                   'Pop by surf' : format_float_float}

print u'\nTop 20 Communes in terms of inhabitants'

ls_disp_com = ['Area', 'Pop', 'Size', 'Pop density',
               'Nb GS', 'Pop by GS', 'Surface', 'Pop by surf']
print df_com[ls_disp_com]\
        [~pd.isnull(df_com['Pop'])][0:20].to_latex(index = False,
                                                   index_names = False,
                                                   formatters = dict_formatters)

# ##########################
# ANALYSIS AT AU LEVEL
# ##########################

# Get rid of non geo areas
df_au_agg = df_au_agg[~df_au_agg['AU2010'].isin(['000', '997', '998'])]

dict_rename_libau = {u'Marseille - Aix-en-Provence' : u'Marseille - Aix',
                     u'(partie française)' : u'(fr)',
                     u'Clermont-Ferrand' : u'Clermont-Fer.'}

def rename_field(some_str, dict_rename):
  for k,v in dict_rename.items():
    some_str = some_str.replace(k,v).strip()
  return some_str


# NB STORES BY AU IN A GIVEN PERIOD
df_au_agg.set_index('AU2010', inplace = True)
se_au_vc = df_lsa['AU2010'].value_counts()
df_au_agg['Nb GS'] = se_au_vc

# RENAME AU2010 FOR OUTPUT
df_au_agg['LIBAU2010'] = df_au_agg['LIBAU2010'].apply(\
                           lambda x: rename_field(x, dict_rename_libau))

# Pop and Pop by Grocery Store
df_au_agg['P10_POP'] = df_au_agg['P10_POP'] / 1000.0
df_au_agg['Pop by GS'] = df_au_agg['P10_POP'] / df_au_agg['Nb GS']

# Surface and Pop by m2
df_au_agg['Surface'] = df_lsa[['AU2010', 'surface']].\
                         groupby('AU2010')['surface'].sum()
df_au_agg['Surface'] = df_au_agg['Surface'] / 1000.0

df_au_agg['Pop by surf'] = df_au_agg['P10_POP'] / df_au_agg['Surface']

df_au_agg['QUAR2UC10'] = df_au_agg['QUAR2UC10'] / 1000

df_au_agg.rename(columns = {'P10_POP' : 'Pop',
                            'LIBAU2010': 'Area',
                            'SUPERF' : 'Size',
                            'POPDENSITY10': 'Pop density',
                            'QUAR2UC10' : 'Med rev'}, inplace = True)

ls_disp_au = ['Area', 'Pop', 'Size', 'Pop density', 'Med rev',
              'Nb GS', 'Pop by GS', 'Surface', 'Pop by surf']

dict_formatters.update({'Med rev' : format_float_float})

print u'\nTop 20 Aires Urbaines in terms of inhabitants'
print df_au_agg[ls_disp_au][0:20].to_latex(index = False,
                                           index_names = False,
                                           formatters = dict_formatters)

## Nb stores vs. population (# stores by head decreasing in population density?)
## exclude paris (+ todo: check with exclusion of au internationales)
#plt.scatter(df_au_agg['P10_POP'][df_au_agg['AU2010']!='001'],
#            df_au_agg['nb_stores'][df_au_agg['AU2010']!='001'])
#plt.show()

## Store density vs. pop density (# stores by head decreasing in population density?)
#plt.scatter(df_au_agg['POPDENSITY10'][df_au_agg['AU2010']!='001'],
#            df_au_agg['pop_by_store'][df_au_agg['AU2010']!='001'])
#plt.show()

# ##########################
# ANALYSIS AT UU LEVEL
# ##########################

# Get rid of non geo areas
df_uu_agg = df_uu_agg[~df_uu_agg['LIBUU2010'].str.contains(u'Communes rurales')]

# Same except: 'AU2010' / 'UU2010', 'LIBAU2010' / 'LIBUU2010'
# Also need to sort and drop nan
df_uu_agg.sort('P10_POP', ascending = False, inplace = True)
df_uu_agg = df_uu_agg[~pd.isnull(df_uu_agg['P10_POP'])]

# NB STORES BY UU IN A GIVEN PERIOD
df_uu_agg.set_index('UU2010', inplace = True)
se_uu_vc = df_lsa['UU2010'].value_counts()
df_uu_agg['Nb GS'] = se_uu_vc

# RENAME AU2010 FOR OUTPUT
df_uu_agg['LIBUU2010'] = df_uu_agg['LIBUU2010'].apply(\
                           lambda x: rename_field(x, dict_rename_libau))

# Pop and Pop by Grocery Store
df_uu_agg['P10_POP'] = df_uu_agg['P10_POP'] / 1000.0
df_uu_agg['Pop by GS'] = df_uu_agg['P10_POP'] / df_uu_agg['Nb GS']

# Surface and Pop by m2
df_uu_agg['Surface'] = df_lsa[['UU2010', 'surface']].\
                    groupby('UU2010')['surface'].sum()
df_uu_agg['Surface'] = df_uu_agg['Surface'] / 1000.0

df_uu_agg['Pop by surf'] = df_uu_agg['P10_POP'] / df_uu_agg['Surface']

df_uu_agg['QUAR2UC10'] = df_uu_agg['QUAR2UC10'] / 1000

df_uu_agg.rename(columns = {'P10_POP' : 'Pop',
                            'LIBUU2010': 'Area',
                            'SUPERF' : 'Size',
                            'POPDENSITY10': 'Pop density',
                            'QUAR2UC10' : 'Med rev'}, inplace = True)

ls_disp_uu = ['Area', 'Pop', 'Size', 'Pop density', 'Med rev',
              'Nb GS', 'Pop by GS', 'Surface', 'Pop by surf']

dict_formatters.update({'Med rev' : format_float_float})

print u'\nTop 20 Unites Urbaines in terms of inhabitants'
print df_uu_agg[ls_disp_uu][0:20].to_latex(index = False,
                                           index_names = False,
                                           formatters = dict_formatters)

# Nb stores vs. population (# stores by head decreasing in population density?)
# exclude paris (+ todo: check with exclusion of au internationales)
df_uu_disp = df_uu_agg[(~df_uu_agg.index.isin(['00851'])) &\
                       (df_uu_agg['Nb GS'] > 0)]
plt.scatter(df_uu_disp['Pop'], df_uu_disp['Nb GS'])
plt.show()

# Store density vs. pop density (# stores by head decreasing in population density?)
df_au_disp = df_au_agg[(~df_au_agg.index.isin(['001'])) &\
                       (df_au_agg['Nb GS'] > 0)]
plt.scatter(df_au_disp['Pop'], df_au_disp['Nb GS'])
plt.show()
