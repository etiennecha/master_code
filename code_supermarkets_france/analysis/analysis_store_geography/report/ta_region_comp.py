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

path_insee = os.path.join(path_data, 'data_insee')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

# Default float format: no digit after decimal point
pd.set_option('float_format', '{:10.0f}'.format)
# Float print functions for display
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ####################
# LOAD DATA
# ####################

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

# #######################################
# RETAIL GROUPS AND REGIONS : NB STORES
# #######################################

df_reg = pd.DataFrame(columns = df_lsa['region'].unique()).T
for groupe in df_lsa['groupe_alt'].unique():
  se_reg_vc = df_lsa['region'][(df_lsa['groupe_alt'] == groupe) &
                                (df_lsa['type_alt'] != 'DRIN') &\
                                (df_lsa['type_alt'] != 'DRIVE')].value_counts()
  df_reg[groupe] = se_reg_vc
df_reg.fillna(0, inplace = True)
df_reg['TOT.'] = df_reg.sum(axis = 1)
df_reg.sort('TOT.', ascending = False, inplace = True)
df_reg.rename(columns = {'CARREFOUR' : 'CARR.',
                         'LECLERC' : 'LECL.',
                         'AUCHAN' : 'AUCH.',
                         'CASINO' : 'CASI.',
                         'MOUSQUETAIRES': 'MOUS.',
                         'SYSTEME U': 'SYS.U',
                         'LOUIS DELHAIZE': 'L.D.',
                         'COLRUYT' : 'COLR.',
                         'DIAPAR' : 'DIAP.',
                         'AUTRE' : 'OTH.'}, inplace = True)
ls_reg_disp = ['CARR.', 'CASI.', 'MOUS.', 'LIDL', 'SYS.U', 'ALDI',
               'LECL.', 'AUCH.', 'L.D.', 'DIAP.', 'COLR.', 'OTH.', 'TOT.']

df_reg_2 = df_reg.copy()

# GROUP MARKET SHARE (NB STORES) BY REGION
df_reg.loc['TOT.'] = df_reg.sum(axis = 0)
for groupe in ls_reg_disp:
  df_reg[groupe] = df_reg[groupe] / df_reg['TOT.'] * 100
df_reg.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
print df_reg[ls_reg_disp].to_latex()
#print 'TOTAL &', ' & '.join(map(lambda x: '{:4.0f}'.format(x),
#                            df_reg[ls_reg_disp].sum(axis = 0).values)), '\\\\'

# SHARE OF STORES WITHIN EACH REGION BY GROUP
df_reg_2 = df_reg_2.T
df_reg_2['TOT.'] = df_reg_2.sum(axis = 1)
for region in list(df_lsa['region'].unique()) + ['TOT.']:
  df_reg_2[region] = df_reg_2[region] / df_reg_2['TOT.'] * 100
df_reg_2 = df_reg_2.T
df_reg_2.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
print df_reg_2[ls_reg_disp].to_latex()

# #######################################
# RETAIL GROUPS AND REGIONS : CUM SURFACE
# #######################################

df_reg_surf = pd.DataFrame(index = df_lsa['region'].unique())
for groupe in df_lsa['groupe_alt'].unique():
  df_groupe = df_lsa[df_lsa['groupe_alt'] == groupe] 
  df_groupe_rs = df_groupe[['region', 'surface']].\
                   groupby('region', as_index = False).sum()
  df_groupe_rs.set_index('region', inplace = True)
  df_reg_surf[groupe] = df_groupe_rs['surface']

df_reg_surf.fillna(0, inplace = True)
df_reg_surf['TOT.'] = df_reg_surf.sum(axis = 1)
df_reg_surf.sort('TOT.', ascending = False, inplace = True)
df_reg_surf.rename(columns = {'CARREFOUR' : 'CARR.',
                         'LECLERC' : 'LECL.',
                         'AUCHAN' : 'AUCH.',
                         'CASINO' : 'CASI.',
                         'MOUSQUETAIRES': 'MOUS.',
                         'SYSTEME U': 'SYS.U',
                         'LOUIS DELHAIZE': 'L.D.',
                         'COLRUYT' : 'COLR.',
                         'DIAPAR' : 'DIAP.',
                         'AUTRE' : 'OTH.'}, inplace = True)
ls_reg_disp = ['CARR.', 'CASI.', 'MOUS.', 'LIDL', 'SYS.U', 'ALDI',
               'LECL.', 'AUCH.', 'L.D.', 'DIAP.', 'COLR.', 'OTH.', 'TOT.']

df_reg_surf_2 = df_reg_surf.copy()

# GROUP MARKET (SURFACE) SHARE BY REGION
df_reg_surf.loc['TOT.'] = df_reg_surf.sum(axis = 0)
for groupe in ls_reg_disp:
  df_reg_surf[groupe] = df_reg_surf[groupe] / df_reg_surf['TOT.'] * 100
df_reg_surf.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
print df_reg_surf[ls_reg_disp].to_latex()
#print 'TOTAL &', ' & '.join(map(lambda x: '{:4.0f}'.format(x),
#                            df_reg_surf[ls_reg_disp].sum(axis = 0).values)), '\\\\'

# SHARE OF SURFACE WITHIN EACH REGION BY GROUP
df_reg_surf_2 = df_reg_surf_2.T
df_reg_surf_2['TOT.'] = df_reg_surf_2.sum(axis = 1)
for region in list(df_lsa['region'].unique()) + ['TOT.']:
  df_reg_surf_2[region] = df_reg_surf_2[region] / df_reg_surf_2['TOT.'] * 100
df_reg_surf_2 = df_reg_surf_2.T
df_reg_surf_2.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
print df_reg_surf_2[ls_reg_disp].to_latex()

# ################
# GROUP HHI AND CR
# ################

# TODO: fix HHI and CR computations
# Use Groupe instead of groupe_alt

def compute_cr(s, num):
  tmp = s.order(ascending=False)[:num]
  return tmp.sum()

def hhi(s):
  tmp = (s / 100.0)**2
  return tmp.sum()

se_cr1_n = df_reg[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 1), axis = 1)
se_cr2_n = df_reg[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 2), axis = 1)
se_cr3_n = df_reg[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 3), axis = 1)
se_cr4_n = df_reg[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 4), axis = 1)

se_cr1_s = df_reg_surf[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 1), axis = 1)
se_cr2_s = df_reg_surf[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 2), axis = 1)
se_cr3_s = df_reg_surf[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 3), axis = 1)
se_cr4_s = df_reg_surf[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 4), axis = 1)

se_hhi_n = df_reg[ls_reg_disp[:-2]].apply(lambda x: hhi(x), axis = 1)
se_hhi_s = df_reg_surf[ls_reg_disp[:-2]].apply(lambda x: hhi(x), axis = 1)

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
