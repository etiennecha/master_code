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
#from mpl_toolkits.basemap import Basemap

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')

path_dir_source_lsa = os.path.join(path_dir_qlmc, 'data_source', 'data_lsa_xls')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

# #############
# READ CSV FILE
# #############

df_lsa_int = pd.read_csv(os.path.join(path_dir_built_csv, 'df_lsa_int.csv'),
                         encoding = 'UTF-8')
# Todo: fix in a better way?
df_lsa_int['Code INSEE'] = df_lsa_int['Code INSEE'].apply(\
                         lambda x: "{:05d}".format(x)\
                           if (type(x) == np.int64 or type(x) == long) else x)

# change name?
df_lsa_gps = df_lsa_int[(df_lsa_int['Type_alt'] != 'DRIN') &\
                        (df_lsa_int['Type_alt'] != 'DRIVE')]
# todo: get ARDT for big cities thx to gps

# ################
# LOAD INSEE DATA
# ################

# todo: fix pbms with num vs. string (CODEGEO in particular)

df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_insee_areas.csv'),
                             encoding = 'UTF-8')
df_au_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_au_agg_final.csv'),
                        encoding = 'UTF-8')
df_uu_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_uu_agg_final.csv'),
                        encoding = 'UTF-8')
df_com = pd.read_csv(os.path.join(path_dir_insee_extracts, 'data_insee_extract.csv'),
                     encoding = 'UTF-8', dtype = {'DEP': str, 'CODGEO' : str})

# GET RID OF DOMTOM AND CORSICA
df_com = df_com[~(df_com['DEP'].isin(['2A', '2B', '971', '972', '973', '974']))]

df_com['CODGEO'] = df_com['CODGEO'].apply(\
                         lambda x: "{:05d}".format(x)\
                           if (type(x) == np.int64 or type(x) == long) else x)

# ADD INSEE AREA CODES TO df_lsa_gps

df_lsa = pd.merge(df_insee_areas,
                  df_lsa_gps,
                  left_on = 'CODGEO',
                  right_on = 'Code INSEE',
                  how = 'right')

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

se_com_vc = df_lsa['Code INSEE'].value_counts()
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
df_com['Surf'] = df_lsa[['Code INSEE', 'Surf Vente']].\
                    groupby('Code INSEE')['Surf Vente'].sum()
df_com['Surf'] = df_com['Surf'] / 1000.0

df_com['Pop by surf'] = df_com['P10_POP'] / df_com['Surf']

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
               'Nb GS', 'Pop by GS', 'Surf', 'Pop by surf']
print df_com[ls_disp_com]\
        [~pd.isnull(df_com['Pop'])][0:20].to_latex(index = False,
                                                   index_names = False,
                                                   formatters = dict_formatters)

# ##########################
# ANALYSIS AT AU LEVEL
# ##########################

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
df_au_agg['Surf'] = df_lsa[['AU2010', 'Surf Vente']].\
                    groupby('AU2010')['Surf Vente'].sum()
df_au_agg['Surf'] = df_au_agg['Surf'] / 1000.0

df_au_agg['Pop by surf'] = df_au_agg['P10_POP'] / df_au_agg['Surf']

df_au_agg['QUAR2UC10'] = df_au_agg['QUAR2UC10'] / 1000

df_au_agg.rename(columns = {'P10_POP' : 'Pop',
                            'LIBAU2010': 'Area',
                            'SUPERF' : 'Size',
                            'POPDENSITY10': 'Pop density',
                            'QUAR2UC10' : 'Med rev'}, inplace = True)

ls_disp_au = ['Area', 'Pop', 'Size', 'Pop density', 'Med rev',
              'Nb GS', 'Pop by GS', 'Surf', 'Pop by surf']

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

# Same except: 'AU2010' / 'UU2010', 'LIBAU2010' / 'LIBUU2010'
# Also need to sort and drop nan
df_uu_agg.sort('P10_POP', ascending = False, inplace = True)
df_uu_agg = df_uu_agg[~pd.isnull(df_uu_agg['P10_POP'])]

# NB STORES BY UU IN A GIVEN PERIOD
df_uu_agg.set_index('UU2010', inplace = True)
se_au_vc = df_lsa['UU2010'].value_counts()
df_uu_agg['Nb GS'] = se_au_vc

# RENAME AU2010 FOR OUTPUT
df_uu_agg['LIBUU2010'] = df_uu_agg['LIBUU2010'].apply(\
                           lambda x: rename_field(x, dict_rename_libau))

# Pop and Pop by Grocery Store
df_uu_agg['P10_POP'] = df_uu_agg['P10_POP'] / 1000.0
df_uu_agg['Pop by GS'] = df_uu_agg['P10_POP'] / df_uu_agg['Nb GS']

# Surface and Pop by m2
df_uu_agg['Surf'] = df_lsa[['UU2010', 'Surf Vente']].\
                    groupby('UU2010')['Surf Vente'].sum()
df_uu_agg['Surf'] = df_uu_agg['Surf'] / 1000.0

df_uu_agg['Pop by surf'] = df_uu_agg['P10_POP'] / df_uu_agg['Surf']

df_uu_agg['QUAR2UC10'] = df_uu_agg['QUAR2UC10'] / 1000

df_uu_agg.rename(columns = {'P10_POP' : 'Pop',
                            'LIBUU2010': 'Area',
                            'SUPERF' : 'Size',
                            'POPDENSITY10': 'Pop density',
                            'QUAR2UC10' : 'Med rev'}, inplace = True)

ls_disp_au = ['Area', 'Pop', 'Size', 'Pop density', 'Med rev',
              'Nb GS', 'Pop by GS', 'Surf', 'Pop by surf']

dict_formatters.update({'Med rev' : format_float_float})

print u'\nTop 20 Aires Urbaines in terms of inhabitants'
print df_uu_agg[ls_disp_au][0:20].to_latex(index = False,
                                           index_names = False,
                                           formatters = dict_formatters)

## Nb stores vs. population (# stores by head decreasing in population density?)
## exclude paris (+ todo: check with exclusion of au internationales)
#plt.scatter(df_uu_agg['P10_POP'][df_uu_agg['AU2010']!='001'],
#            df_uu_agg['nb_stores'][df_uu_agg['AU2010']!='001'])
#plt.show()
#
## Store density vs. pop density (# stores by head decreasing in population density?)
#plt.scatter(df_uu_agg['POPDENSITY10'][df_uu_agg['AU2010']!='001'],
#            df_uu_agg['pop_by_store'][df_uu_agg['AU2010']!='001'])
#plt.show()