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
# Stores H/S/X active in Metropolitan France
df_lsa = pd.read_csv(os.path.join(path_dir_built_csv, 'df_lsa_active_fm_hsx.csv'),
                     encoding = 'UTF-8')

# #######################################
# RETAIL GROUPS AND REGIONS : NB STORES
# #######################################

df_reg = pd.DataFrame(columns = df_lsa['Reg'].unique()).T
for groupe in df_lsa['Groupe'].unique():
  se_reg_vc = df_lsa['Reg'][(df_lsa['Groupe'] == groupe) &
                                (df_lsa['Type_alt'] != 'DRIN') &\
                                (df_lsa['Type_alt'] != 'DRIVE')].value_counts()
  df_reg[groupe] = se_reg_vc
df_reg.fillna(0, inplace = True)
df_reg['TOT.'] = df_reg.sum(axis = 1)
df_reg.sort('TOT.', ascending = False, inplace = True)

# GROUP MARKET SHARE (NB STORES) BY REGION
df_reg.loc['TOT.'] = df_reg.sum(axis = 0)
for groupe in df_lsa['Groupe'].unique():
  df_reg[groupe] = df_reg[groupe] / df_reg['TOT.'] * 100
df_reg.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
df_reg.drop('TOT.', 1, inplace = True)

# #######################################
# RETAIL GROUPS AND REGIONS : CUM SURFACE
# #######################################

df_reg_surf = pd.DataFrame(index = df_lsa['Reg'].unique())
for groupe in df_lsa['Groupe'].unique():
  df_groupe = df_lsa[df_lsa['Groupe'] == groupe] 
  df_groupe_rs = df_groupe[['Reg', 'Surf Vente']].\
                   groupby('Reg', as_index = False).sum()
  df_groupe_rs.set_index('Reg', inplace = True)
  df_reg_surf[groupe] = df_groupe_rs['Surf Vente']

df_reg_surf.fillna(0, inplace = True)
df_reg_surf['TOT.'] = df_reg_surf.sum(axis = 1)
df_reg_surf.sort('TOT.', ascending = False, inplace = True)

df_reg_surf.loc['TOT.'] = df_reg_surf.sum(axis = 0)
for groupe in df_lsa['Groupe'].unique():
  df_reg_surf[groupe] = df_reg_surf[groupe] / df_reg_surf['TOT.'] * 100
df_reg_surf.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
df_reg_surf.drop('TOT.', 1, inplace = True)

# ################
# GROUP HHI AND CR
# ################

# TODO: fix HHI and CR computations
# Use Groupe instead of Groupe_alt

def compute_cr(s, num):
  tmp = s.order(ascending=False)[:num]
  return tmp.sum()

def hhi(s):
  tmp = (s / 100.0)**2
  return tmp.sum()

se_cr1_n = df_reg.apply(lambda x: compute_cr(x, 1), axis = 1)
se_cr2_n = df_reg.apply(lambda x: compute_cr(x, 2), axis = 1)
se_cr3_n = df_reg.apply(lambda x: compute_cr(x, 3), axis = 1)
se_cr4_n = df_reg.apply(lambda x: compute_cr(x, 4), axis = 1)

se_cr1_s = df_reg_surf.apply(lambda x: compute_cr(x, 1), axis = 1)
se_cr2_s = df_reg_surf.apply(lambda x: compute_cr(x, 2), axis = 1)
se_cr3_s = df_reg_surf.apply(lambda x: compute_cr(x, 3), axis = 1)
se_cr4_s = df_reg_surf.apply(lambda x: compute_cr(x, 4), axis = 1)

se_hhi_n = df_reg.apply(lambda x: hhi(x), axis = 1)
se_hhi_s = df_reg_surf.apply(lambda x: hhi(x), axis = 1)

df_reg_cr = pd.DataFrame({'CR1_n' : se_cr1_n,
                          'CR2_n' : se_cr2_n,
                          'CR3_n' : se_cr3_n,
                          'CR4_n' : se_cr4_n,
                          'CR1_s' : se_cr1_s,
                          'CR2_s' : se_cr2_s,
                          'CR3_s' : se_cr3_s,
                          'CR4_s' : se_cr4_s,
                          'HHI_n' : se_hhi_n,
                          'HHI_s' : se_hhi_s})

ls_disp = ['CR1_n' , 'CR2_n', 'CR3_n', 'CR4_n',
           'CR1_s' , 'CR2_s', 'CR3_s', 'CR4_s',
           'HHI_n', 'HHI_s']

dict_formatters = {'HHI_n' : format_float_float,
                   'HHI_s' : format_float_float}

# pbm: need to precise display for HHI columns + pbms with small brands
print df_reg_cr[ls_disp].to_latex(formatters = dict_formatters)
