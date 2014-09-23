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

# ###################
# READ LSA EXCEL FILE
# ###################

# Need to work with _no1900 at CREST for now (older versions of numpy/pandas/xlrd...?)
df_lsa_all = pd.read_excel(os.path.join(path_dir_source_lsa,
                                               '2014-07-30-export_CNRS_no1900.xlsx'),
                           sheetname = 'Feuil1')
df_lsa = df_lsa_all

# ############
# FORMAT DATES
# ############

# Convert dates to pandas friendly format
# Can not use np.datetime64() as missing value
for field in [u'DATE ouv', u'DATE ferm', u'DATE réouv',
              u'DATE chg enseigne', u'DATE chgt surf']:
  df_lsa[field] = df_lsa[field].apply(lambda x: x.replace(hour=0, minute=0,
                                                          second=0, microsecond=0)\
                                        if (type(x) is datetime.datetime) or\
                                           (type(x) is pd.Timestamp)
                                        else pd.tslib.NaT)

print u'Stores in data (active or not): {0:5d}'.format 

# ############################
# CREATE DPT AND REG VARIABLES
# ############################

dict_dpts_regions = dec_json(os.path.join(path_dir_insee,
                                          'dpts_regions',
                                          'dict_dpts_regions.json'))
df_lsa['Dpt'] = df_lsa['Code INSEE'].str.slice(stop=-3)
df_lsa['Reg'] = df_lsa['Dpt'].apply(\
                  lambda x: dict_dpts_regions.get(x, 'DOMTOM'))

# ###############################
# CREATE RETAIL GROUP VARIABLE
# ###############################

#print df_lsa['Enseigne'].value_counts().to_string()
#print df_lsa['Ex enseigne'].value_counts().to_string()

dict_groupes = {'MOUSQUETAIRES'      : ['INTERMARCHE SUPER',
                                        'NETTO',
                                        'LE DRIVE INTERMARCHE',
                                        'INTERMARCHE CONTACT',
                                        'INTERMARCHE',
                                        'INTERMARCHE HYPER',
                                        'ECOMARCHE',
                                        'INTERMARCHE EXPRESS',
                                        'RELAIS DES MOUSQUETAIRES'],
                'SYSTEME U'          : ['SUPER U',
                                        'COURSES U',
                                        'U EXPRESS',
                                        'HYPER U',
                                        'MARCHE U',
                                        'UTILE'],
                'CARREFOUR'          : ['CARREFOUR MARKET',
                                        'CARREFOUR CONTACT',
                                        'DIA %',
                                        'CARREFOUR',
                                        'CARREFOUR MARKET DRIVE',
                                        'ED',
                                        'CARREFOUR DRIVE',
                                        'CARREFOUR CITY',
                                        'MARKET', # check MARKET
                                        'SHOPI',
                                        'CHAMPION',
                                        'MARKET DRIVE', # check MARKET DRIVE
                                        'CARREFOUR EXPRESS',
                                        'PROXI',
                                        '8 A HUIT',
                                        'PROXI SUPER',
                                        'MARCHE PLUS',
                                        'CARREFOUR MONTAGNE',
                                        'CHAMPION',
                                        'HYPER CHAMPION'], 
                'CASINO'             : ['LEADER PRICE',
                                        'FRANPRIX',
                                        'CASINO',
                                        'MONOPRIX',
                                        'SPAR',
                                        'CASINO DRIVE',
                                        'LEADER DRIVE',
                                        'GEANT CASINO',
                                        "MONOP'",
                                        'HYPER CASINO',
                                        'SPAR SUPERMARCHE',
                                        'SCORE', # check SCORE
                                        'MONOPRIX DRIVE',
                                        'CASINO SHOPPING',
                                        'LEADER EXPRESS',
                                        'JUMBO SCORE', # check JUMBO SCORE
                                        'PETIT CASINO',
                                        'LEADER MARKET',
                                        'GEANT',
                                        'CASINO EXPRESS',
                                        'INNO',
                                        'DISCOUNT CASINO',
                                        "DAILYMONOP'",
                                        'SUPER MONOPRIX'],  
                'LECLERC'            : ['CENTRE E.LECLERC',
                                        'E.LECLERC DRIVE',
                                        'LECLERC EXPRESS'],
                'AUCHAN'             : ['SIMPLY MARKET',
                                        'AUCHAN',
                                        'AUCHAN DRIVE',
                                        'ATAC',
                                        'CHRONODRIVE', # check CHRONODRIVE
                                        'MAXIMARCHE', # check MAXIMARCHE
                                        "LES HALLES D'AUCHAN",
                                        'A2PAS',
                                        'SIMPLY DRIVE',
                                        'EASY MARCHE',
                                        'AUCHAN CITY',
                                        'MAXIMARCHE'], 
                'LOUIS DELHAIZE'     : ['SUPERMARCHE MATCH',
                                        'CORA',
                                        'CORADRIVE',
                                        'SUPERMARCHE MATCH DRIVE'],
                'DIAPAR'             : ['G 20',
                                        'DIAGONAL',
                                        'SITIS'],
                'COLRUYT'            : ['COLRUYT',
                                        'COCCINELLE',
                                        'COCCINELLE SUPERMARCHE',
                                        'COCCINELLE EXPRESS',
                                        'COCCIMARKET',
                                        'COCCINELLE MARCHE'],
                'ALDI'                : ['ALDI'],
                'LIDL'                : ['LIDL']}

# MUTANT EXPRESS, CDM, AU MARCHE VRAC...

dict_enseigne_groupe = {x: k for k,v in dict_groupes.items() for x in v}
df_lsa['Groupe'] = df_lsa['Enseigne'].apply(\
                     lambda x: dict_enseigne_groupe.get(x, 'AUTRE') if not pd.isnull(x)\
                                                       else None)
df_lsa['Ex groupe'] = df_lsa['Ex enseigne'].apply(\
                     lambda x: dict_enseigne_groupe.get(x, 'AUTRE') if not pd.isnull(x)\
                                                       else None)

# ###############################
# REFINE ENSEIGNE VARIABLES
# ###############################

dict_alt_enseignes = {'ED' : 'DIA %', # CARREFOUR
                      'CHAMPION' : 'CARREFOUR MARKET',
                      'HYPER CHAMPION' : 'MARKET',
                      '8 A HUIT': 'CARREFOUR OTHER',
                      'PROXI SUPER': 'CARREFOUR OTHER',
                      'PROXI' : 'CARREFOUR OTHER',
                      'LEADER EXPRESS' : 'LEADER PRICE', # CASINO
                      'LEADER MARKET' : 'LEADER PRICE',
                      'CASINO SHOPPING' : 'CASINO AUTRE',
                      'PETIT CASINO' : 'CASINO AUTRE',
                      'RELAIS DES MOUSQUETAIRES' : 'INTERMARCHE AUTRE',
                      'ECOMARCHE' : 'INTERMARCHE AUTRE',
                      'EASY MARCHE' : 'ATAC', # AUCHAN
                      'MAXIMARCHE' : 'AUTRE AUCHAN',
                      'A2PAS' : 'AUTRE AUCHAN',
                      'DIAGONAL' : 'AUTRE DIAPAR', # DIAPAR
                      'SITIS' : 'AUTRE DIAPART',
                      'COCCINELLE SUPERMARCHE' : 'COCCINELLE', # COLRUYT
                      'COCCINELLE EXPRESS' : 'COCCINELLE',
                      'COCCIMARKET' : 'COCCINELLE',
                      'COCCINELLE MARCHE' : 'COCCINELLE'}

df_lsa['Enseigne_alt'] = df_lsa['Enseigne']
df_lsa['Enseigne_alt'] = df_lsa['Enseigne_alt'].apply(\
                           lambda x: dict_alt_enseignes[x] if x in dict_alt_enseignes\
                                                           else x)

# ###############################
# GET RID OF MAGASINS POPULAIRES
# ###############################

# Drop if surface below 400m2, else either Supermarket or Hypermarket
df_lsa = df_lsa[~((df_lsa['Type'] == 'MP') & (df_lsa['Surf Vente'] < 400))].copy()
df_lsa['Type_alt'] = None
df_lsa['Type_alt'][df_lsa['Type'] != 'MP'] = df_lsa['Type']
df_lsa['Type_alt'][(df_lsa['Type'] == 'MP') & (df_lsa['Surf Vente'] < 2500)] == 'S'
df_lsa['Type_alt'][(df_lsa['Type'] == 'MP') & (df_lsa['Surf Vente'] >= 2500)] == 'H'

# ##############################
# DINSTIGUISH OPERATING STORES
# ##############################

# Stores no more operating
df_lsa_inactive = df_lsa[(~pd.isnull(df_lsa[u'DATE ferm'])) &\
                         (pd.isnull(df_lsa[u'DATE réouv']))].copy()
print u'Stores no more operating: {0:5d}'.format(len(df_lsa_inactive))

# Stores still operating (add for any date e.g. 01/01/2014)
df_lsa_active = df_lsa[(pd.isnull(df_lsa[u'DATE ferm'])) |\
                       ((~pd.isnull(df_lsa[u'DATE ferm'])) &\
                        (~pd.isnull(df_lsa[u'DATE réouv'])))].copy()
print u'Stores still operating: {0:5d}'.format(len(df_lsa_active))

# Stores active and located in Metropolitan France
df_lsa_active_fm = df_lsa_active[(df_lsa_active['Reg'] != 'DOMTOM') &\
                                 (df_lsa_active['Reg'] != 'Corse')]

# Choose dataframe to describe
df_lsa_int = df_lsa_active_fm
print u'Stores of interest: {0:5d}'.format(len(df_lsa_int))

# Describe variables of operating stores
for field in ['Statut', 'Type_alt', 'Enseigne_alt', 'Ex enseigne', 'Groupe']:
  print u'\nValue counts for:', field
  print u'-'*20
  print df_lsa_int[field].value_counts()

# ###################### 
# STATS BY TYPE OF STORE 
# ######################

df_lsa['Pompes'][pd.isnull(df_lsa['Pompes'])] = np.nan
# solve pbm: why min and max on grouby return nan...

def quant_05(x):
  return x.quantile(0.05)

def quant_95(x):
  return x.quantile(0.95)

pd.set_option('float_format', '{:10,.0f}'.format)
pd.set_option('float_format', '{:10,.0f}'.format)

dict_type_out = {'S' : 'Supermarkets',
                 'H' : 'Hypermarkets',
                 'DRIN' : 'Drive in',
                 'X' : 'Hard discount',
                 'DRIVE' : 'Drive'}

ls_loc_hsx = ['Hypermarkets', 'Supermarkets', 'Hard discount']
ls_loc_drive = ['Drive in', 'Drive']

for field in ['Surf Vente', 'Nbr emp', 'Nbr de caisses', 'Nbr parking', 'Pompes']:
  print u'\n', u'-'*30
  print field
  gbt = df_lsa_int[['Type_alt', field]].groupby('Type_alt',
                                                      as_index = False)
  df_surf = gbt.agg([len, np.mean, min, quant_05,
                     np.median, quant_95, max, np.sum])[field]
  df_surf.sort('len', ascending = False, inplace = True)
  se_null_vc = df_lsa_int['Type_alt'][~pd.isnull(df_lsa_int[field])].value_counts()
  df_surf[u'\#Avail.'] = se_null_vc.apply(lambda x: float(x)) # float format...
  df_surf.rename(columns = {'len' : u'\#Total',
                            'mean': u'Avg',
                            'median': u'Med',
                            'min': u'Min',
                            'max': u'Max',
                            'quant_05': u'Q05',
                            'quant_95': u'Q95',
                            'sum': u'Cum'}, inplace = True)
  ls_surf_disp = [u'\#Total', u'\#Avail.',
                  u'Min', u'Q05', u'Med',
                  u'Avg', u'Q95', u'Max', u'Cum']
  df_surf.reset_index(inplace = True)
  df_surf['Type_alt'] = df_surf['Type_alt'].apply(lambda x: dict_type_out[x])
  df_surf.set_index('Type_alt', inplace = True)
  
  # pbm: bottom line? (fake groupby?)
  print '\n', df_surf[ls_surf_disp].loc[ls_loc_hsx].to_latex(index_names = False)
  print df_lsa_int[df_lsa_int['Type_alt'].isin(['H', 'X', 'S'])]\
          [['Surf Vente', 'Statut']].groupby('Statut', as_index = False).\
            agg([len, min, quant_05, np.median, np.mean, quant_95, max, np.sum]).to_string()

  print '\n', df_surf[ls_surf_disp].loc[ls_loc_drive].to_latex(index_names = False)
  print df_lsa_int[df_lsa_int['Type_alt'].isin(['DRIVE', 'DRIN'])]\
          [['Surf Vente', 'Statut']].groupby('Statut', as_index = False).\
            agg([len, min, quant_05, np.median, np.mean, quant_95, max, np.sum]).to_string()

# ###################################
# INSPECT SUSPECT VALUES AND FIX DATA
# ###################################

# todo: inspect suspect values
pd.set_option('display.max_columns', 50)
#print df_lsa_int[df_lsa_int['Nbr de caisses'] > 100]
#print df_lsa_int[(df_lsa_int['Type_alt'] == 'X') &\
#                    (df_lsa_int['Nbr de caisses'] > 20)]
#print df_lsa_int[(df_lsa_int['Type_alt'] == 'DRIVE') &\
#                    (df_lsa_int['Nbr de caisses'] > 20)]
#df_lsa_int[df_lsa_int['Nbr parking']<10]

# ##########################################################
# STATS ON NB OF STORES AND SURFACE BY RETAIL GROUPS/CHAINS
# ##########################################################

# Stats desc by retail group
print '\nStats des per retail group'
df_lsa_gps = df_lsa_int[(df_lsa_int['Type_alt'] != 'DRIN') &\
                           (df_lsa_int['Type_alt'] != 'DRIVE')]
gbg = df_lsa_gps[['Groupe', 'Surf Vente']].groupby('Groupe',
                                                   as_index = False)
df_surf_rg = gbg.agg([len, np.mean, np.median, min, max, np.sum])['Surf Vente']
df_surf_rg.sort('len', ascending = False, inplace = True)
# print df_surf.to_string()
df_types = pd.DataFrame(columns = ['H', 'S', 'X']).T
for groupe in df_lsa_gps['Groupe'].unique():
  se_types_vc = df_lsa_gps['Type_alt'][df_lsa_gps['Groupe'] == groupe].value_counts()
  df_types[groupe] = se_types_vc
df_types.fillna(0, inplace = True)
df_types = df_types.T
# print df_types.to_string()
df_rgps = pd.merge(df_types, df_surf_rg, left_index = True, right_index = True)
df_rgps.sort('len', ascending = False, inplace = True)
df_rgps.rename(columns = {'len' : '#Tot',
                          'mean': 'Avg S.',
                          'median': 'Med S.',
                          'min': 'Min S.',
                          'max': 'Max S.',
                          'sum': 'Cum S.',
                          'H' : '#Hyp',
                          'S' : '#Sup',
                          'X' : '#Dis'}, inplace = True)
ls_rgps_disp = ['#Tot', '#Hyp', '#Sup', '#Dis',
                'Avg S.', 'Med S.', 'Min S.', 'Max S.', 'Cum S.']
print df_rgps[ls_rgps_disp].to_latex()

# Stats desc by enseigne (and by group)
print '\nStats des per retail group'
for retail_group in dict_groupes.keys():
  print '\n', retail_group
  df_lsa_rgp = df_lsa_int[(df_lsa_int['Groupe'] == retail_group) &\
                             (df_lsa_int['Type_alt'] != 'DRIN') &\
                             (df_lsa_int['Type_alt'] != 'DRIVE')]
  gbg = df_lsa_rgp[['Enseigne', 'Surf Vente']].groupby('Enseigne',
                                                       as_index = False)
  df_surf_rg = gbg.agg([len, np.mean, np.median, min, max, np.sum])['Surf Vente']
  df_surf_rg.sort('len', ascending = False, inplace = True)
  # print df_surf.to_string()
  df_types = pd.DataFrame(columns = ['H', 'S', 'X']).T
  for enseigne in df_lsa_rgp['Enseigne'].unique():
    se_types_vc = df_lsa_rgp['Type_alt'][df_lsa_rgp['Enseigne'] == enseigne].value_counts()
    df_types[enseigne] = se_types_vc
  df_types.fillna(0, inplace = True)
  df_types = df_types.T
  # print df_types.to_string()
  df_rgp = pd.merge(df_types, df_surf_rg, left_index = True, right_index = True)
  df_rgp.sort('len', ascending = False, inplace = True)
  df_rgp.rename(columns = {'len' : '#Tot',
                           'mean': 'Avg S.',
                           'median': 'Med S.',
                           'min': 'Min S.',
                           'max': 'Max S.',
                           'sum': 'Cum S.',
                           'H' : '#Hyp',
                           'S' : '#Sup',
                           'X' : '#Dis'}, inplace = True)
  ls_rgp_disp = ['#Tot', '#Hyp', '#Sup', '#Dis',
                 'Avg S.', 'Med S.', 'Min S.', 'Max S.', 'Cum S.']
  print df_rgp[ls_rgp_disp].to_latex()

#print u'\nNb stores (dead or alive) with valid gps:'
#print len(df_lsa[(~pd.isnull(df_lsa['Longitude'])) &\
#                 (~pd.isnull(df_lsa['Latitude']))])
#

# #########################################
# STATS ON NB OF STORES BY GROUP AND REGION
# #########################################

df_reg = pd.DataFrame(columns = df_lsa_int['Reg'].unique()).T
for groupe in df_lsa_int['Groupe'].unique():
  se_reg_vc = df_lsa_int['Reg'][(df_lsa_int['Groupe'] == groupe) &
                                   (df_lsa_int['Type_alt'] != 'DRIN') &\
                                   (df_lsa_int['Type_alt'] != 'DRIVE')].value_counts()
  df_reg[groupe] = se_reg_vc
df_reg.fillna(0, inplace = True)
df_reg['TOT.'] = df_reg.sum(axis = 1)
df_reg.sort('TOT.', ascending = False, inplace = True)
df_reg.rename(columns = {'CARREFOUR' : 'CARR.',
                         'LECLERC' : 'LECL.',
                         'AUCHAN' : 'AUCH.',
                         'CASINO' : 'CASI.',
                         'MOUSQUETAIRES': 'MOUSQ.',
                         'SYSTEME U': 'SYS.U',
                         'LOUIS DELHAIZE': 'L.D.',
                         'COLRUYT' : 'COLR.',
                         'DIAPAR' : 'DIAP.',
                         'AUTRE' : 'OTH.'}, inplace = True)
ls_reg_disp = ['CARR.', 'CASI.', 'MOUSQ.', 'LIDL', 'SYS.U', 'ALDI',
               'LECL.', 'AUCH.', 'L.D.', 'DIAP.', 'COLR.', 'OTH.', 'TOT.']
print df_reg[ls_reg_disp].to_latex()
# row: TOT
print 'TOTAL &', ' & '.join(map(lambda x: '{:4.0f}'.format(x),
                            df_reg[ls_reg_disp].sum(axis = 0).values)), '\\\\'

## #######################
## OUTPUT FOR MAP CREATION
## #######################

#df_lsa_int.to_csv(os.path.join(path_dir_built_csv, 'df_lsa_int.csv'),
#                     encoding = 'UTF-8', float_format='%.3f')
