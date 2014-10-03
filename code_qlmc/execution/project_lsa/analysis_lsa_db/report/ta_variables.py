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

# Default float format: no digit after decimal point
pd.set_option('float_format', '{:10.0f}'.format)
# Float print functions for display
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
# Stores active in Metropolitan France, includes  H/S/X and Drive
# (only this file, others include only H/S/X so far)
df_lsa = pd.read_csv(os.path.join(path_dir_built_csv, 'df_lsa_active_fm.csv'),
                     encoding = 'UTF-8')

def pdmin(x):
  return x.min(skipna = True)

def pdmax(x):
  return x.max(skipna = True)

def quant_05(x):
  return x.quantile(0.05)

def quant_95(x):
  return x.quantile(0.95)

dict_type_out = {'S' : 'Supermarkets',
                 'H' : 'Hypermarkets',
                 'DRIN' : 'Drive in',
                 'X' : 'Hard discount',
                 'DRIVE' : 'Drive'}

str_total, str_avail = u'#Total', u'#Avail.' # need '\#' if old pandas?

dict_rename_columns =  {'len' : str_total,
                        'mean': u'Avg',
                        'median': u'Med',
                        'pdmin': u'Min',
                        'pdmax': u'Max',
                        'quant_05': u'Q05',
                        'quant_95': u'Q95',
                        'sum' : u'Cum'}

ls_surf_disp = [str_total, str_avail,
                u'Min', u'Q05', u'Med',
                u'Avg', u'Q95', u'Max', u'Cum']

ls_loc_hsx = ['Hypermarkets', 'Supermarkets', 'Hard discount']
ls_loc_drive = ['Drive in', 'Drive']

for field in ['Surf Vente', 'Nbr emp', 'Nbr de caisses', 'Nbr parking', 'Pompes']:
  print u'\n', u'-'*30
  print field
  gbt = df_lsa[['Type_alt', field]].groupby('Type_alt',
                                                      as_index = False)
  df_surf = gbt.agg([len, np.mean, pdmin, quant_05,
                     np.median, quant_95, pdmax, np.sum])[field]
  df_surf.sort('len', ascending = False, inplace = True)
  se_null_vc = df_lsa['Type_alt'][~pd.isnull(df_lsa[field])].value_counts()
  df_surf[str_avail] = se_null_vc.apply(lambda x: float(x)) # float format...
  df_surf.rename(columns = dict_rename_columns, inplace = True)
  df_surf.reset_index(inplace = True)
  df_surf['Type_alt'] = df_surf['Type_alt'].apply(lambda x: dict_type_out[x])
  df_surf.set_index('Type_alt', inplace = True)
  # Bottom line to be improved (fake groupy for now...)
  for ls_loc_disp, ls_store_types in zip([ls_loc_hsx, ls_loc_drive],
                                         [['H', 'X', 'S'], ['DRIVE', 'DRIN']]):
    df_surf_hxs = df_lsa[df_lsa['Type_alt'].isin(ls_store_types)]\
                    [['Statut', field]].groupby('Statut', as_index = False).\
                      agg([len, pdmin, quant_05, np.median,
                           np.mean, quant_95, pdmax, np.sum])[field]
    df_surf_hxs[str_avail] = len(df_lsa[(df_lsa['Type_alt'].isin(ls_store_types)) &\
                                             (~pd.isnull(df_lsa[field]))])
    df_surf_hxs.rename(columns = dict_rename_columns,
                       index = {'M' : 'All'},
                       inplace = True)
    # Fix for drive
    df_surf_final = pd.concat([df_surf.loc[ls_loc_disp], df_surf_hxs])
    print '\n', df_surf_final[ls_surf_disp].loc[ls_loc_disp + ['All']].\
                  to_latex(index_names = False)
