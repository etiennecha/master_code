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
import time

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_png = os.path.join(path_dir_qlmc, 'data_built' , 'data_png')

path_dir_source_lsa = os.path.join(path_dir_qlmc, 'data_source', 'data_lsa_xls')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# READ CSV FILES
# ##############

df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_lsa_active_fm_hsx.csv'),
                     dtype = {'Code INSEE' : str,
                              'Code INSEE ardt' : str},
                     encoding = 'UTF-8')
df_lsa = df_lsa[(~pd.isnull(df_lsa['Latitude'])) &\
                (~pd.isnull(df_lsa['Longitude']))].copy()

df_com_insee = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'UTF-8')
df_com_insee.set_index('CODGEO', inplace = True)

# SURFACE AVAIL TO EACH COMMUNE BY TYPE
df_com_surf_type = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_com_avail_surf_type.csv'),
                               dtype = {'code_insee' : str},
                               encoding = 'utf-8')
df_com_surf_type.set_index('code_insee', inplace = True)

# Columns to be filled and worked on
ls_st = ['H', 'S', 'X']
ls_disp_com_st = ['avail_surf', 'surf'] +\
                 ['avail_surf_%s' %st for st in ls_st] +\
                 ['surf_%s' %st for st in ls_st]

# MERGE TO BUILD DF COM
df_com = pd.merge(df_com_insee, df_com_surf_type,
                  left_index = True, right_index = True, how = 'right')

# Check all communes have some avail surf
len(df_com[pd.isnull(df_com['avail_surf'])])
# Replace nan surface by 0 (not sure of proper syntax: flagged inplace = True )
df_com.loc[:, ls_disp_com_st]= df_com.loc[:, ls_disp_com_st].fillna(0)

# Dict regions
dict_regions =  {'Alsace' :'42',
                 'Aquitaine': '72', 
                 'Auvergne' : '83',
                 'Basse-Normandie' : '25',
                 'Bourgogne' : '26',
                 'Bretagne' : '53',
                 'Centre' : '24',
                 'Champagne-Ardenne' : '21',
                 'Corse' : '94',
                 'Franche-Comte' : '43',
                 'Haute-Normandie':'23',
                 'Ile-de-France' : '11',
                 'Languedoc-Roussillon' : '91',
                 'Limousin' : '74',
                 'Lorraine' : '41',
                 'Midi-Pyrenees' : '73',
                 'Nord-Pas-de-Calais': '31',
                 'Pays de la Loire' : '52',
                 'Picardie' : '22',
                 'Poitou-Charentes' : '54',
                 "Provence-Alpes-Cote-d'Azur" : '93',
                 'Rhone-Alpes' : '82'}

dict_regions = {v: k for k,v in dict_regions.items()}

# ##############################
# ENTROPY: AVAIL SURFACE vs. POP
# ##############################

field = 'P10_MEN' # 'avail_surf' # 
decomp = 'REG'

# get s_k
df_reg_s = df_com[[decomp, field]].groupby(decomp).agg([len,
                                                       np.mean])[field]
df_reg_s['s_k'] = (df_reg_s['len'] * df_reg_s['mean']) /\
                  (len(df_com) * df_com[field].mean())

# get T1_k
def get_T1_k(se_inc):
  se_norm_inc = se_inc / se_inc.mean()
  return (se_norm_inc * np.log(se_norm_inc)).sum() / len(se_inc)
df_reg_t = df_com[[decomp, field]].groupby(decomp).agg([len,
                                                      get_T1_k])[field]
df_reg_t['T1_k'] = df_reg_t['get_T1_k']

# merge and final
df_reg = df_reg_s[['mean', 's_k']].copy()
df_reg['T1_k'] = df_reg_t['T1_k']

T1 = (df_reg['s_k'] * df_reg['T1_k']).sum()  +\
     (df_reg['s_k'] * np.log(df_reg['mean'] / df_com[field].mean())).sum()

df_com['norm_%s' %field] = df_com[field] / df_com[field].mean()
T1_simple = (df_com['norm_%s' %field] * np.log(df_com['norm_%s' %field])).sum() /\
            len(df_com)

df_reg.index = ['{:.0f}'.format(x) for x in df_reg.index]
df_reg.index = [dict_regions[x]for x in df_reg.index]
df_reg.ix['France'] = [df_com[field].mean(), np.nan, T1]

print df_reg.to_string(formatters = {'mean' : format_float_int})
print 'Within regions:', (df_reg['s_k'] * df_reg['T1_k']).sum()
print 'Inter regions:', (df_reg['s_k'] * np.log(df_reg['mean'] / df_com[field].mean())).sum()

## ################################
## ENTROPY: TABLE W/ ALL VARIABLES
## ################################
#
#ls_entropy = []
#ls_df_entropy_decomp = []
#ls_se_entropy = []
#
#decomp = 'REG'
#for field in ls_disp_com_st:
#
#  
#  # get s_k
#  df_reg_s = df_com[[decomp, field]].groupby(decomp).agg([len,
#                                                         np.mean])[field]
#  df_reg_s['s_k'] = (df_reg_s['len'] * df_reg_s['mean']) /\
#                    (len(df_com) * df_com[field].mean())
#  
#  # get T1_k
#  def get_T1_k(se_inc):
#    se_norm_inc = se_inc / se_inc.mean()
#    return (se_norm_inc * np.log(se_norm_inc)).sum() / len(se_inc)
#  df_reg_t = df_com[[decomp, field]].groupby(decomp).agg([len,
#                                                        get_T1_k])[field]
#  df_reg_t['T1_k'] = df_reg_t['get_T1_k']
#  
#  # merge and final
#  df_reg = df_reg_s[['mean', 's_k']].copy()
#  df_reg['T1_k'] = df_reg_t['T1_k']
#  
#  T1 = (df_reg['s_k'] * df_reg['T1_k']).sum()  +\
#       (df_reg['s_k'] * np.log(df_reg['mean'] / df_com[field].mean())).sum()
#  
#  df_com['norm_%s' %field] = df_com[field] / df_com[field].mean()
#  T1_simple = (df_com['norm_%s' %field] * np.log(df_com['norm_%s' %field])).sum() /\
#              len(df_com)
#  # Close enough! (Same as get_T1)
#  
#  # Get table (todo: compare between types of stores)
#  df_reg.index = ['{:.0f}'.format(x) for x in df_reg.index]
#  df_reg.index = [dict_regions[x]for x in df_reg.index]
#  #df_reg.sort(columns = 's_k', ascending = False, inplace = True)
#  #print df_reg[['s_k', 'T1_k']].to_string()
#  
#  ls_entropy.append((T1_simple,
#                     T1,
#                     (df_reg['s_k'] * df_reg['T1_k']).sum(),
#                     (df_reg['s_k'] * np.log(df_reg['mean'] / df_com[field].mean())).sum()))
#  ls_df_entropy_decomp.append(df_reg)
#   
#  df_temp = df_reg.copy()
#  df_temp.loc['All', 'T1_k'] = T1
#  df_temp.loc['W/ Reg'] = (df_reg['s_k'] * df_reg['T1_k']).sum()
#  df_temp.loc['B/ Reg'] = (df_reg['s_k'] * np.log(df_reg['mean'] / df_com[field].mean())).sum()
#  ls_se_entropy.append(df_temp['T1_k'])
#
#df_entropy = pd.concat(ls_se_entropy, axis = 1, keys = ls_disp_com_st)
#print df_entropy[['avail_surf'] +\
#                 ['avail_surf_%s' %x for x in ['H', 'S', 'X']]+\
#                 ['surf']+\
#                 ['surf_%s' %x for x in ['H', 'S', 'X']]].to_latex()
