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

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                              'data_csv')

path_insee_extracts = os.path.join(path_data,
                                   'data_insee',
                                   'data_extracts')

# ################
# LOAD DATA
# ################

# Active stores only
# (could be stores at any period)

df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa.csv'),
                     dtype = {u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

# ###################### 
# STATS BY TYPE OF STORE 
# ######################

format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

#df_lsa['Pompes'][pd.isnull(df_lsa['Pompes'])] = np.nan
# solve pbm: why min and max on grouby return nan...

def pdmin(x):
  return x.min(skipna = True)

def pdmax(x):
  return x.max(skipna = True)

def quant_05(x):
  return x.quantile(0.05)

def quant_95(x):
  return x.quantile(0.95)

pd.set_option('float_format', '{:10,.0f}'.format)

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

for field in ['surface', 'nb_emplois', 'nb_caisses', 'nb_parking', 'nb_pompes']:
  print u'\n', u'-'*80
  print field
  gbt = df_lsa[['type_alt', field]].groupby('type_alt',
                                                      as_index = False)
  df_surf = gbt.agg([len, np.mean, pdmin, quant_05,
                     np.median, quant_95, pdmax, np.sum])[field]
  df_surf.sort('len', ascending = False, inplace = True)
  se_null_vc = df_lsa['type_alt'][~pd.isnull(df_lsa[field])].value_counts()
  df_surf[str_avail] = se_null_vc.apply(lambda x: float(x)) # float format...
  df_surf.rename(columns = dict_rename_columns, inplace = True)
  df_surf.reset_index(inplace = True)
  df_surf['type_alt'] = df_surf['type_alt'].apply(lambda x: dict_type_out[x])
  df_surf.set_index('type_alt', inplace = True)
  # Bottom line to be improved (fake groupy for now...)
  for ls_loc_disp, ls_store_types in zip([ls_loc_hsx, ls_loc_drive],
                                         [['H', 'X', 'S'], ['DRIVE', 'DRIN']]):
    df_surf_hxs = df_lsa[df_lsa['type_alt'].isin(ls_store_types)]\
                    [['statut', field]].groupby('statut', as_index = False).\
                      agg([len, pdmin, quant_05, np.median,
                           np.mean, quant_95, pdmax, np.sum])[field]
    df_surf_hxs[str_avail] = len(df_lsa[(df_lsa['type_alt']\
                                                     .isin(ls_store_types)) &\
                                                  (~pd.isnull(df_lsa[field]))])
    df_surf_hxs.rename(columns = dict_rename_columns,
                       index = {'M' : 'All'},
                       inplace = True)
    # Fix for drive
    df_surf_final = pd.concat([df_surf.loc[ls_loc_disp], df_surf_hxs])
    print '\n', df_surf_final[ls_surf_disp].loc[ls_loc_disp + ['All']].\
                  to_string(index_names = False)

# ###################################
# INSPECT SUSPECT VALUES AND FIX DATA
# ###################################

# todo: inspect suspect values
pd.set_option('display.max_columns', 50)
#print df_lsa[df_lsa['Nbr de caisses'] > 100]
#print df_lsa[(df_lsa['type_alt'] == 'X') &\
#                    (df_lsa['Nbr de caisses'] > 20)]
#print df_lsa[(df_lsa['type_alt'] == 'DRIVE') &\
#                    (df_lsa['Nbr de caisses'] > 20)]
#df_lsa[df_lsa['Nbr parking']<10]

# ####################
# RETAIL GROUP STORES
# ####################

print u'\n', u'-'*120
print '\nStats des per retail group\n'

gbg = df_lsa[['groupe_alt', 'surface']].groupby('groupe_alt',
                                                   as_index = False)
df_surf_rgs = gbg.agg([len, np.mean, np.median, min, max, np.sum])['surface']
df_surf_rgs.sort('len', ascending = False, inplace = True)
# Bottom line
df_surf_rgs_b = df_lsa[df_lsa['type_alt'].isin(['H', 'S', 'X'])]\
                  [['statut', 'surface']].groupby('statut', as_index = False).\
                    agg([len, np.mean, np.median, min, max, np.sum])['surface']
df_surf_rgs = pd.concat([df_surf_rgs, df_surf_rgs_b])
df_surf_rgs.rename(index = {'M' : 'ALL'}, inplace = True)
# print df_surf_rgs.to_string()
df_types_rgs = pd.DataFrame(columns = ['H', 'S', 'X']).T
for groupe in df_lsa['groupe_alt'].unique():
  se_types_vc = df_lsa['type_alt'][df_lsa['groupe_alt'] ==\
                                            groupe].value_counts()
  df_types_rgs[groupe] = se_types_vc
df_types_rgs.fillna(0, inplace = True)
df_types_rgs = df_types_rgs.T
# Bottom line
df_types_rgs.loc['ALL'] = df_types_rgs.sum()
# print df_types_rg.to_string()
df_rgs = pd.merge(df_types_rgs, df_surf_rgs, left_index = True, right_index = True)
df_rgs.sort('len', ascending = False, inplace = True)
df_rgs.rename(columns = {'len' : '#Tot',
                         'mean': 'Avg S.',
                         'median': 'Med S.',
                         'min': 'Min S.',
                         'max': 'Max S.',
                         'sum': 'Cum S.',
                         'H' : '#Hyp',
                         'S' : '#Sup',
                         'X' : '#Dis'},
              inplace = True)
ls_rgs_disp = ['#Tot', '#Hyp', '#Sup', '#Dis',
                'Avg S.', 'Med S.', 'Min S.', 'Max S.', 'Cum S.']
ls_ind_disp = list(df_rgs.index[1:])
ls_ind_disp.remove('AUTRE')
print df_rgs[ls_rgs_disp].loc[ls_ind_disp + ['AUTRE', 'ALL']].to_string()

# ###########################
# RETAIL GROUP CHAIN STORES
# ###########################

print u'\n', u'-'*120
print '\nStats des per retail group chain\n'

dict_rename_rg = {'len' : '#Tot',
                  'mean': 'Avg S.',
                  'median': 'Med S.',
                  'min': 'Min S.',
                  'max': 'Max S.',
                  'sum': 'Cum S.',
                  'H' : '#Hyp',
                  'S' : '#Sup',
                  'X' : '#Dis'}

ls_rg_disp = ['#Tot', '#Hyp', '#Sup', '#Dis',
               'Avg S.', 'Med S.', 'Min S.', 'Max S.', 'Cum S.']

dict_formatters = {'Cum S.' : format_float_float}

ls_main_retail_groups = ['MOUSQUETAIRES',
                         'SYSTEME U',
                         'CARREFOUR',
                         'CASINO',
                         'LECLERC',
                         'AUCHAN',
                         'LOUIS DELHAIZE',
                         'DIAPAR',
                         'COLRUYT',
                         'ALDI',
                         'LIDL']

for retail_group in ls_main_retail_groups:

  print '\n', u'-'*20
  print '\n', retail_group
  
  # All group stores
  df_lsa_rg = df_lsa[df_lsa['groupe_alt'] == retail_group]
  gbg = df_lsa_rg[['enseigne_alt', 'surface']].groupby('enseigne_alt',
                                                       as_index = False)
  df_surf_rg = gbg.agg([len, np.mean, np.median, min, max, np.sum])['surface']
  df_surf_rg.sort('len', ascending = False, inplace = True)
  # print df_surf_rg.to_string()
  df_types_rg = pd.DataFrame(columns = ['H', 'S', 'X']).T
  for Enseigne in df_lsa_rg['enseigne_alt'].unique():
    se_types_vc = df_lsa_rg['type_alt'][df_lsa_rg['enseigne_alt'] ==\
                                          Enseigne].value_counts()
    df_types_rg[Enseigne] = se_types_vc
  df_types_rg.fillna(0, inplace = True)
  df_types_rg = df_types_rg.T
  # print df_types_rg.to_string()
  df_rg = pd.merge(df_types_rg, df_surf_rg,
                   left_index = True, right_index = True)
  df_rg.sort('len', ascending = False, inplace = True)
  df_rg.rename(columns = dict_rename_rg, inplace = True)
  df_rg['Cum S.'] = df_rg['Cum S.'] / 1000000
  print df_rg[ls_rg_disp].to_string(formatters = dict_formatters)
  
  # Independent stores
  df_lsa_rg_ind = df_lsa[(df_lsa['groupe_alt'] == retail_group) &
                             (df_lsa[u'int_ind'] == 'independant')]
  if len(df_lsa_rg_ind) != 0:
    gbg = df_lsa_rg_ind[['enseigne_alt', 'surface']].groupby('enseigne_alt',
                                                             as_index = False)
    df_surf_rg_ind = gbg.agg([len, np.mean, np.median, min, max, np.sum])['surface']
    df_surf_rg_ind.sort('len', ascending = False, inplace = True)
    # print df_surf_rg_ind.to_string()
    df_types_rg_ind = pd.DataFrame(columns = ['H', 'S', 'X']).T
    for Enseigne in df_lsa_rg_ind['enseigne_alt'].unique():
      se_types_vc = df_lsa_rg_ind['type_alt'][df_lsa_rg_ind['enseigne_alt'] ==\
                                                Enseigne].value_counts()
      df_types_rg_ind[Enseigne] = se_types_vc
    df_types_rg_ind.fillna(0, inplace = True)
    df_types_rg_ind = df_types_rg_ind.T
    # print df_types.to_string()
    df_rg_ind = pd.merge(df_types_rg_ind, df_surf_rg_ind,
                         left_index = True, right_index = True)
    df_rg_ind.sort('len', ascending = False, inplace = True)
    df_rg_ind.rename(columns = dict_rename_rg, inplace = True)
    df_rg_ind['Cum S.'] = df_rg_ind['Cum S.'] / 1000000
    print '\n', df_rg_ind[ls_rg_disp].to_string(formatters = dict_formatters)
  else:
    print '\nNo indpt store'

# #########################################
# STATS ON NB OF STORES BY GROUP AND REGION
# #########################################

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

# Share of each group by region
df_reg.loc['TOT.'] = df_reg.sum(axis = 0)
for groupe in ls_reg_disp:
  df_reg[groupe] = df_reg[groupe] / df_reg['TOT.'] * 100
df_reg.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
print df_reg[ls_reg_disp].to_latex()
#print 'TOTAL &', ' & '.join(map(lambda x: '{:4.0f}'.format(x),
#                            df_reg[ls_reg_disp].sum(axis = 0).values)), '\\\\'

# Share of each region by group
df_reg_2 = df_reg_2.T
df_reg_2['TOT.'] = df_reg_2.sum(axis = 1)
for region in list(df_lsa['region'].unique()) + ['TOT.']:
  df_reg_2[region] = df_reg_2[region] / df_reg_2['TOT.'] * 100
df_reg_2 = df_reg_2.T
df_reg_2.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
print df_reg_2[ls_reg_disp].to_latex()

# #########################################
# SURFACE BY GROUP AND REGION
# #########################################

df_lsa_gps = df_lsa[~pd.isnull(df_lsa['latitude'])]

df_reg_surf = pd.DataFrame(index = df_lsa_gps['region'].unique())
for groupe in df_lsa_gps['groupe_alt'].unique():
  df_groupe = df_lsa_gps[df_lsa_gps['groupe_alt'] == groupe] 
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

# Share of each group by region
df_reg_surf.loc['TOT.'] = df_reg_surf.sum(axis = 0)
for groupe in ls_reg_disp:
  df_reg_surf[groupe] = df_reg_surf[groupe] / df_reg_surf['TOT.'] * 100
df_reg_surf.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
print df_reg_surf[ls_reg_disp].to_latex()
#print 'TOTAL &', ' & '.join(map(lambda x: '{:4.0f}'.format(x),
#                            df_reg_surf[ls_reg_disp].sum(axis = 0).values)), '\\\\'

# Share of each region by group
df_reg_surf_2 = df_reg_surf_2.T
df_reg_surf_2['TOT.'] = df_reg_surf_2.sum(axis = 1)
for region in list(df_lsa_gps['region'].unique()) + ['TOT.']:
  df_reg_surf_2[region] = df_reg_surf_2[region] / df_reg_surf_2['TOT.'] * 100
df_reg_surf_2 = df_reg_surf_2.T
df_reg_surf_2.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
print df_reg_surf_2[ls_reg_disp].to_latex()

# CR2 table

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
