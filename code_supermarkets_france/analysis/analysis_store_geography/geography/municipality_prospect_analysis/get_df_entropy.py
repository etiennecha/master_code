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
import time

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built, 'data_csv')
path_built_csv_comp = os.path.join(path_built_csv, '201407_competition')

path_insee = os.path.join(path_data, 'data_insee')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

pd.set_option('float_format', '{:10,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# READ CSV FILES
# ##############

# LOAD LSA STORE DATA
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

df_lsa = df_lsa[(~pd.isnull(df_lsa['latitude'])) &\
                (~pd.isnull(df_lsa['longitude']))].copy()

# LOAD INSEE MUNICIPALITY DATA
df_com_insee = pd.read_csv(os.path.join(path_insee_extracts,
                                        'df_communes.csv'),
                           dtype = {'DEP': str,
                                    'CODGEO' : str},
                           encoding = 'UTF-8')
df_com_insee.set_index('CODGEO', inplace = True)

# SURFACE AVAIL TO EACH COMMUNE BY TYPE
df_com_surf_type = pd.read_csv(os.path.join(path_built_csv_comp,
                                          'df_mun_prospect_surface_avail_by_type.csv'),
                               dtype = {'c_insee' : str},
                               encoding = 'utf-8')
df_com_surf_type.set_index('c_insee', inplace = True)

# Columns to be filled and worked on
ls_st = ['H', 'S', 'X']
ls_disp_com_st = ['available_surface', 'surface'] +\
                 ['available_surface_%s' %st for st in ls_st] +\
                 ['surface_%s' %st for st in ls_st]

# MERGE TO BUILD DF COM
df_com = pd.merge(df_com_insee, df_com_surf_type,
                  left_index = True, right_index = True, how = 'right')

# Check all communes have some avail surf
len(df_com[pd.isnull(df_com['available_surface'])])
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

# get t1_k
def get_t1_k(se_inc):
  se_norm_inc = se_inc / se_inc.mean()
  return (se_norm_inc * np.log(se_norm_inc)).sum() / len(se_inc)
df_reg_t = df_com[[decomp, field]].groupby(decomp).agg([len,
                                                      get_t1_k])[field]
df_reg_t['t1_k'] = df_reg_t['get_t1_k']

# merge and final
df_reg = df_reg_s[['mean', 's_k']].copy()
df_reg['t1_k'] = df_reg_t['t1_k']

t1 = (df_reg['s_k'] * df_reg['t1_k']).sum()  +\
     (df_reg['s_k'] * np.log(df_reg['mean'] / df_com[field].mean())).sum()

df_com['norm_%s' %field] = df_com[field] / df_com[field].mean()
t1_simple = (df_com['norm_%s' %field] * np.log(df_com['norm_%s' %field])).sum() /\
            len(df_com)

df_reg.index = ['{:.0f}'.format(x) for x in df_reg.index]
df_reg.index = [dict_regions[x]for x in df_reg.index]
df_reg.ix['France'] = [df_com[field].mean(), np.nan, t1]

print df_reg.to_string(formatters = {'mean' : format_float_int})
print 'Within regions:', (df_reg['s_k'] * df_reg['t1_k']).sum()
print 'Inter regions:', (df_reg['s_k'] * np.log(df_reg['mean'] / df_com[field].mean())).sum()

# ################################
# ENTROPY: TABLE W/ ALL VARIABLES
# ################################

ls_entropy = []
ls_df_entropy_decomp = []
ls_se_entropy = []

decomp = 'REG'
for field in ls_disp_com_st:

  
  # get s_k
  df_reg_s = df_com[[decomp, field]].groupby(decomp).agg([len,
                                                         np.mean])[field]
  df_reg_s['s_k'] = (df_reg_s['len'] * df_reg_s['mean']) /\
                    (len(df_com) * df_com[field].mean())
  
  # get t1_k
  def get_t1_k(se_inc):
    se_norm_inc = se_inc / se_inc.mean()
    return (se_norm_inc * np.log(se_norm_inc)).sum() / len(se_inc)
  df_reg_t = df_com[[decomp, field]].groupby(decomp).agg([len,
                                                        get_t1_k])[field]
  df_reg_t['t1_k'] = df_reg_t['get_t1_k']
  
  # merge and final
  df_reg = df_reg_s[['mean', 's_k']].copy()
  df_reg['t1_k'] = df_reg_t['t1_k']
  
  t1 = (df_reg['s_k'] * df_reg['t1_k']).sum()  +\
       (df_reg['s_k'] * np.log(df_reg['mean'] / df_com[field].mean())).sum()
  
  df_com['norm_%s' %field] = df_com[field] / df_com[field].mean()
  t1_simple = (df_com['norm_%s' %field] * np.log(df_com['norm_%s' %field])).sum() /\
              len(df_com)
  # Close enough! (Same as get_t1)
  
  # Get table (todo: compare between types of stores)
  df_reg.index = ['{:.0f}'.format(x) for x in df_reg.index]
  df_reg.index = [dict_regions[x]for x in df_reg.index]
  #df_reg.sort(columns = 's_k', ascending = False, inplace = True)
  #print df_reg[['s_k', 't1_k']].to_string()
  
  ls_entropy.append((t1_simple,
                     t1,
                     (df_reg['s_k'] * df_reg['t1_k']).sum(),
                     (df_reg['s_k'] * np.log(df_reg['mean'] / df_com[field].mean())).sum()))
  ls_df_entropy_decomp.append(df_reg)
   
  df_temp = df_reg.copy()
  df_temp.loc['All', 't1_k'] = t1
  df_temp.loc['W/ Reg'] = (df_reg['s_k'] * df_reg['t1_k']).sum()
  df_temp.loc['B/ Reg'] = (df_reg['s_k'] * np.log(df_reg['mean'] / df_com[field].mean())).sum()
  ls_se_entropy.append(df_temp['t1_k'])

df_entropy = pd.concat(ls_se_entropy, axis = 1, keys = ls_disp_com_st)
print df_entropy[['available_surface'] +\
                 ['available_surface_%s' %x for x in ['H', 'S', 'X']]+\
                 ['surface']+\
                 ['surface_%s' %x for x in ['H', 'S', 'X']]].to_string()
