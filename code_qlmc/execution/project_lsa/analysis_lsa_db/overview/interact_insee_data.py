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

# #################################
# INTEGRATE INSEE DATA FOR ANALYSIS
# #################################

df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_insee_areas.csv'),
                             encoding = 'UTF-8')
df_au_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_au_agg_final.csv'),
                        encoding = 'UTF-8')
df_uu_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_uu_agg_final.csv'),
                        encoding = 'UTF-8')
df_com = pd.read_csv(os.path.join(path_dir_insee_extracts, 'data_insee_extract.csv'),
                     encoding = 'UTF-8', dtype = {'DEP': str, 'CODGEO' : str})
df_com = df_com[~(df_com['DEP'].isin(['2A', '2B', '971', '972', '973', '974']))]
# Todo: fix in a better way?
df_com['CODGEO'] = df_com['CODGEO'].apply(\
                         lambda x: "{:05d}".format(x)\
                           if (type(x) == np.int64 or type(x) == long) else x)

# Add insee area codes to df_fra_stores
df_lsa = pd.merge(df_insee_areas,
                  df_lsa_gps,
                  left_on = 'CODGEO',
                  right_on = 'Code INSEE',
                  how = 'right')

# COMMUNES WITH NO STORE
se_com_vc = df_lsa['Code INSEE'].value_counts()
df_com.index = df_com['CODGEO']
df_com['nb_stores'] = se_com_vc
len(df_com[~pd.isnull(df_com['nb_stores'])])

pop_tot = df_com['POP_MUN_2007_COM'].sum()
pop_nostore = df_com['POP_MUN_2007_COM'][pd.isnull(df_com['nb_stores'])].sum()
print u"{:2.2f}".format(pop_nostore / pop_tot * 100),\
      u'% of French citizens in 2007 with no store on "Commune"'

# NB STORES BY AU IN A GIVEN PERIOD
df_au_agg.index = df_au_agg['AU2010']
ls_disp_au = ['AU2010', 'LIBAU2010', 'P10_POP', 'SUPERF', 'POPDENSITY10', 'QUAR2UC10',
              'nb_stores', 'pop_by_store']
se_au_vc = df_lsa['AU2010'].value_counts()
df_au_agg['nb_stores'] = se_au_vc
df_au_agg['pop_by_store'] = df_au_agg['P10_POP'] / df_au_agg['nb_stores']

print df_au_agg[ls_disp_au][0:10].to_string()

# Nb stores vs. population (# stores by head decreasing in population density?)
# exclude paris (+ todo: check with exclusion of au internationales)
plt.scatter(df_au_agg['P10_POP'][df_au_agg['AU2010']!='001'],
            df_au_agg['nb_stores'][df_au_agg['AU2010']!='001'])
plt.show()

## Store density vs. pop density (# stores by head decreasing in population density?)
#plt.scatter(df_au_agg['POPDENSITY10'][df_au_agg['AU2010']!='001'],
#            df_au_agg['pop_by_store'][df_au_agg['AU2010']!='001'])
#plt.show()

# STORE SURFACE BY AU (todo: take period into account)
df_au_agg['surf_vente_cum'] = df_lsa[['AU2010', 'Surf Vente']].groupby('AU2010')['Surf Vente'].sum()
df_au_agg['pop_by_surf_vente'] = df_au_agg['P10_POP'] / df_au_agg['surf_vente_cum']
print df_au_agg[ls_disp_au + ['surf_vente_cum', 'pop_by_surf_vente']][0:10].to_string()

# NB STORES BY UU
df_uu_agg.index = df_uu_agg['UU2010']
ls_disp_uu = ['UU2010', 'LIBUU2010', 'P10_POP', 'SUPERF', 'POPDENSITY10', 'QUAR2UC10',
              'nb_stores', 'pop_by_store']

se_au_vc = df_lsa['UU2010'].value_counts()
df_uu_agg['nb_stores'] = se_au_vc
df_uu_agg['pop_by_store'] = df_uu_agg['P10_POP'] / df_uu_agg['nb_stores']

df_uu_agg.sort('P10_POP', ascending=False, inplace=True)
print df_uu_agg[ls_disp_uu][df_uu_agg['nb_stores'] >= 1][0:10].to_string()

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
