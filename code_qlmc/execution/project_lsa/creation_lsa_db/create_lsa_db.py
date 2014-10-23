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
df_lsa = pd.read_excel(os.path.join(path_dir_source_lsa,
                                               '2014-07-30-export_CNRS_no1900.xlsx'),
                           sheetname = 'Feuil1')

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

# ############
# INSEE CODES
# ############

# TODO: read Code INSEE and Code postal as unicode

# Check that INSEE codes are up to date
# fusion de communes
df_lsa['Code INSEE'] = df_lsa['Code INSEE'].apply(\
                         lambda x: str(x).replace('76095', '76108'))

def get_insee_from_zip_ardt(zip_code):
# fix: ['75056', '13055', '69123']
# geofla only has arrondissements
  zip_code = re.sub(u'750([0-9]{2})', u'751\\1', zip_code) # 75116 untouched
  zip_code = re.sub(u'130([0-9]{2})', u'132\\1', zip_code)
  zip_code = re.sub(u'6900([0-9])', u'6938\\1', zip_code)
  return zip_code # actually an ardt insee code

ls_insee_bc = ['75056', '13055', '69123']

df_lsa['Code INSEE ardt'] = df_lsa['Code INSEE']
df_lsa['Code INSEE ardt'].loc[df_lsa['Code INSEE'].isin(ls_insee_bc)] =\
    df_lsa['Code postal'].loc[df_lsa['Code INSEE'].isin(ls_insee_bc)].apply(\
       lambda x: get_insee_from_zip_ardt(unicode(x)))

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
                     lambda x: dict_enseigne_groupe[x] if x in dict_enseigne_groupe
                                                       else x)
df_lsa['Groupe_alt'] = df_lsa['Enseigne'].apply(\
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
                      '8 A HUIT': 'CARREFOUR AUTRE',
                      'PROXI SUPER': 'CARREFOUR AUTRE',
                      'PROXI' : 'CARREFOUR AUTRE',
                      'CARREFOUR MONTAGNE' : 'CARREFOUR AUTRE',
                      'LEADER EXPRESS' : 'LEADER PRICE', # CASINO
                      'LEADER MARKET' : 'LEADER PRICE',
                      'SPAR SUPERMARCHE' : 'SPAR',
                      'CASINO SHOPPING' : 'CASINO AUTRE',
                      'PETIT CASINO' : 'CASINO AUTRE',
                      'RELAIS DES MOUSQUETAIRES' : 'INTERMARCHE AUTRE',
                      'ECOMARCHE' : 'INTERMARCHE AUTRE',
                      'EASY MARCHE' : 'ATAC', # AUCHAN
                      'ATAC' : 'SIMPLY MARKET',
                      'MAXIMARCHE' : 'AUCHAN AUTRE',
                      'A2PAS' : 'AUCHAN AUTRE',
                      'DIAGONAL' : 'DIAPAR AUTRE', # DIAPAR
                      'SITIS' : 'DIAPAR AUTRE',
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
df_lsa['Type_alt'] = df_lsa['Type']
df_lsa['Type_alt'].loc[(df_lsa['Type'] == 'MP') & (df_lsa['Surf Vente'] < 2500)] = 'S'
df_lsa['Type_alt'].loc[(df_lsa['Type'] == 'MP') & (df_lsa['Surf Vente'] >= 2500)] = 'H'

# ####################
# BUILD DATAFRAMES
# ####################

print u'Stores in data (active or not): {0:5d}'.format(len(df_lsa)) 

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
print u'Stores active in Met Fra: {0:5d}'.format(len(df_lsa_active_fm))

# Stores HSX active located in Metropolitan France
df_lsa_a_f_hsx = df_lsa_active[(df_lsa_active['Reg'] != 'DOMTOM') &\
                               (df_lsa_active['Reg'] != 'Corse') &\
                               (df_lsa_active['Type_alt'] != 'DRIN') &\
                               (df_lsa_active['Type_alt'] != 'DRIVE')]
print u'Stores HSX active in Met Fra: {0:5d}'.format(len(df_lsa_a_f_hsx))

# Stores HSX located in Metropolitan France
df_lsa_fm_hsx = df_lsa[(df_lsa['Type_alt'] != 'DRIN') &\
                       (df_lsa['Type_alt'] != 'DRIVE')]

# Describe variables of operating stores
print u'\n', u'-'*120
for field in ['Statut', 'Type_alt', 'Enseigne_alt', 'Ex enseigne', 'Groupe']:
  print u'\nValue counts for:', field
  print df_lsa_active_fm[field].value_counts()
  print u'-'*30

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

for field in ['Surf Vente', 'Nbr emp', 'Nbr de caisses', 'Nbr parking', 'Pompes']:
  print u'\n', u'-'*120
  print field
  gbt = df_lsa_active_fm[['Type_alt', field]].groupby('Type_alt',
                                                      as_index = False)
  df_surf = gbt.agg([len, np.mean, pdmin, quant_05,
                     np.median, quant_95, pdmax, np.sum])[field]
  df_surf.sort('len', ascending = False, inplace = True)
  se_null_vc = df_lsa_active_fm['Type_alt'][~pd.isnull(df_lsa_active_fm[field])].value_counts()
  df_surf[str_avail] = se_null_vc.apply(lambda x: float(x)) # float format...
  df_surf.rename(columns = dict_rename_columns, inplace = True)
  df_surf.reset_index(inplace = True)
  df_surf['Type_alt'] = df_surf['Type_alt'].apply(lambda x: dict_type_out[x])
  df_surf.set_index('Type_alt', inplace = True)
  # Bottom line to be improved (fake groupy for now...)
  for ls_loc_disp, ls_store_types in zip([ls_loc_hsx, ls_loc_drive],
                                         [['H', 'X', 'S'], ['DRIVE', 'DRIN']]):
    df_surf_hxs = df_lsa_active_fm[df_lsa_active_fm['Type_alt'].isin(ls_store_types)]\
                    [['Statut', field]].groupby('Statut', as_index = False).\
                      agg([len, pdmin, quant_05, np.median,
                           np.mean, quant_95, pdmax, np.sum])[field]
    df_surf_hxs[str_avail] = len(df_lsa_active_fm[(df_lsa_active_fm['Type_alt']\
                                                     .isin(ls_store_types)) &\
                                                  (~pd.isnull(df_lsa_active_fm[field]))])
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
#print df_lsa_active_fm[df_lsa_active_fm['Nbr de caisses'] > 100]
#print df_lsa_active_fm[(df_lsa_active_fm['Type_alt'] == 'X') &\
#                    (df_lsa_active_fm['Nbr de caisses'] > 20)]
#print df_lsa_active_fm[(df_lsa_active_fm['Type_alt'] == 'DRIVE') &\
#                    (df_lsa_active_fm['Nbr de caisses'] > 20)]
#df_lsa_active_fm[df_lsa_active_fm['Nbr parking']<10]

# ####################
# RETAIL GROUP STORES
# ####################

print u'\n', u'-'*120
print '\nStats des per retail group\n'

gbg = df_lsa_a_f_hsx[['Groupe_alt', 'Surf Vente']].groupby('Groupe_alt',
                                                           as_index = False)
df_surf_rgs = gbg.agg([len, np.mean, np.median, min, max, np.sum])['Surf Vente']
df_surf_rgs.sort('len', ascending = False, inplace = True)
# Bottom line
df_surf_rgs_b = df_lsa_a_f_hsx[df_lsa_a_f_hsx['Type_alt'].isin(['H', 'S', 'X'])]\
                  [['Statut', 'Surf Vente']].groupby('Statut', as_index = False).\
                    agg([len, np.mean, np.median, min, max, np.sum])['Surf Vente']
df_surf_rgs = pd.concat([df_surf_rgs, df_surf_rgs_b])
df_surf_rgs.rename(index = {'M' : 'ALL'}, inplace = True)
# print df_surf_rgs.to_string()
df_types_rgs = pd.DataFrame(columns = ['H', 'S', 'X']).T
for groupe in df_lsa_a_f_hsx['Groupe_alt'].unique():
  se_types_vc = df_lsa_a_f_hsx['Type_alt'][df_lsa_a_f_hsx['Groupe_alt'] ==\
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

for retail_group in dict_groupes.keys():

  print '\n', u'-'*20
  print '\n', retail_group
  
  # All group stores
  df_lsa_rg = df_lsa_a_f_hsx[df_lsa_a_f_hsx['Groupe_alt'] == retail_group]
  gbg = df_lsa_rg[['Enseigne_alt', 'Surf Vente']].groupby('Enseigne_alt',
                                                       as_index = False)
  df_surf_rg = gbg.agg([len, np.mean, np.median, min, max, np.sum])['Surf Vente']
  df_surf_rg.sort('len', ascending = False, inplace = True)
  # print df_surf_rg.to_string()
  df_types_rg = pd.DataFrame(columns = ['H', 'S', 'X']).T
  for enseigne in df_lsa_rg['Enseigne_alt'].unique():
    se_types_vc = df_lsa_rg['Type_alt'][df_lsa_rg['Enseigne_alt'] ==\
                                          enseigne].value_counts()
    df_types_rg[enseigne] = se_types_vc
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
  df_lsa_rg_ind = df_lsa_a_f_hsx[(df_lsa_a_f_hsx['Groupe_alt'] == retail_group) &
                             (df_lsa_a_f_hsx[u'Intégré / Indépendant'] == 'independant')]
  if len(df_lsa_rg_ind) != 0:
    gbg = df_lsa_rg_ind[['Enseigne_alt', 'Surf Vente']].groupby('Enseigne_alt',
                                                             as_index = False)
    df_surf_rg_ind = gbg.agg([len, np.mean, np.median, min, max, np.sum])['Surf Vente']
    df_surf_rg_ind.sort('len', ascending = False, inplace = True)
    # print df_surf_rg_ind.to_string()
    df_types_rg_ind = pd.DataFrame(columns = ['H', 'S', 'X']).T
    for enseigne in df_lsa_rg_ind['Enseigne_alt'].unique():
      se_types_vc = df_lsa_rg_ind['Type_alt'][df_lsa_rg_ind['Enseigne_alt'] ==\
                                                enseigne].value_counts()
      df_types_rg_ind[enseigne] = se_types_vc
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

## #########################################
## STATS ON NB OF STORES BY GROUP AND REGION
## #########################################
#
#df_reg = pd.DataFrame(columns = df_lsa_int['Reg'].unique()).T
#for groupe in df_lsa_int['Groupe_alt'].unique():
#  se_reg_vc = df_lsa_int['Reg'][(df_lsa_int['Groupe_alt'] == groupe) &
#                                (df_lsa_int['Type_alt'] != 'DRIN') &\
#                                (df_lsa_int['Type_alt'] != 'DRIVE')].value_counts()
#  df_reg[groupe] = se_reg_vc
#df_reg.fillna(0, inplace = True)
#df_reg['TOT.'] = df_reg.sum(axis = 1)
#df_reg.sort('TOT.', ascending = False, inplace = True)
#df_reg.rename(columns = {'CARREFOUR' : 'CARR.',
#                         'LECLERC' : 'LECL.',
#                         'AUCHAN' : 'AUCH.',
#                         'CASINO' : 'CASI.',
#                         'MOUSQUETAIRES': 'MOUS.',
#                         'SYSTEME U': 'SYS.U',
#                         'LOUIS DELHAIZE': 'L.D.',
#                         'COLRUYT' : 'COLR.',
#                         'DIAPAR' : 'DIAP.',
#                         'AUTRE' : 'OTH.'}, inplace = True)
#ls_reg_disp = ['CARR.', 'CASI.', 'MOUS.', 'LIDL', 'SYS.U', 'ALDI',
#               'LECL.', 'AUCH.', 'L.D.', 'DIAP.', 'COLR.', 'OTH.', 'TOT.']
#
#df_reg_2 = df_reg.copy()
#
## Share of each group by region
#df_reg.loc['TOT.'] = df_reg.sum(axis = 0)
#for groupe in ls_reg_disp:
#  df_reg[groupe] = df_reg[groupe] / df_reg['TOT.'] * 100
#df_reg.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
#print df_reg[ls_reg_disp].to_latex()
##print 'TOTAL &', ' & '.join(map(lambda x: '{:4.0f}'.format(x),
##                            df_reg[ls_reg_disp].sum(axis = 0).values)), '\\\\'
#
## Share of each region by group
#df_reg_2 = df_reg_2.T
#df_reg_2['TOT.'] = df_reg_2.sum(axis = 1)
#for region in list(df_lsa_gps['Reg'].unique()) + ['TOT.']:
#  df_reg_2[region] = df_reg_2[region] / df_reg_2['TOT.'] * 100
#df_reg_2 = df_reg_2.T
#df_reg_2.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
#print df_reg_2[ls_reg_disp].to_latex()
#
## #########################################
## SURFACE BY GROUP AND REGION
## #########################################
#
#df_reg_surf = pd.DataFrame(index = df_lsa_gps['Reg'].unique())
#for groupe in df_lsa_gps['Groupe_alt'].unique():
#  df_groupe = df_lsa_gps[df_lsa_gps['Groupe_alt'] == groupe] 
#  df_groupe_rs = df_groupe[['Reg', 'Surf Vente']].\
#                   groupby('Reg', as_index = False).sum()
#  df_groupe_rs.set_index('Reg', inplace = True)
#  df_reg_surf[groupe] = df_groupe_rs['Surf Vente']
#
#df_reg_surf.fillna(0, inplace = True)
#df_reg_surf['TOT.'] = df_reg_surf.sum(axis = 1)
#df_reg_surf.sort('TOT.', ascending = False, inplace = True)
#df_reg_surf.rename(columns = {'CARREFOUR' : 'CARR.',
#                         'LECLERC' : 'LECL.',
#                         'AUCHAN' : 'AUCH.',
#                         'CASINO' : 'CASI.',
#                         'MOUSQUETAIRES': 'MOUS.',
#                         'SYSTEME U': 'SYS.U',
#                         'LOUIS DELHAIZE': 'L.D.',
#                         'COLRUYT' : 'COLR.',
#                         'DIAPAR' : 'DIAP.',
#                         'AUTRE' : 'OTH.'}, inplace = True)
#ls_reg_disp = ['CARR.', 'CASI.', 'MOUS.', 'LIDL', 'SYS.U', 'ALDI',
#               'LECL.', 'AUCH.', 'L.D.', 'DIAP.', 'COLR.', 'OTH.', 'TOT.']
#
#df_reg_surf_2 = df_reg_surf.copy()
#
## Share of each group by region
#df_reg_surf.loc['TOT.'] = df_reg_surf.sum(axis = 0)
#for groupe in ls_reg_disp:
#  df_reg_surf[groupe] = df_reg_surf[groupe] / df_reg_surf['TOT.'] * 100
#df_reg_surf.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
#print df_reg_surf[ls_reg_disp].to_latex()
##print 'TOTAL &', ' & '.join(map(lambda x: '{:4.0f}'.format(x),
##                            df_reg_surf[ls_reg_disp].sum(axis = 0).values)), '\\\\'
#
## Share of each region by group
#df_reg_surf_2 = df_reg_surf_2.T
#df_reg_surf_2['TOT.'] = df_reg_surf_2.sum(axis = 1)
#for region in list(df_lsa_gps['Reg'].unique()) + ['TOT.']:
#  df_reg_surf_2[region] = df_reg_surf_2[region] / df_reg_surf_2['TOT.'] * 100
#df_reg_surf_2 = df_reg_surf_2.T
#df_reg_surf_2.rename(index = {u"Provence-Alpes-Cote-d'Azur" : 'PACA'}, inplace = True)
#print df_reg_surf_2[ls_reg_disp].to_latex()
#
## CR2 table
#
#def compute_cr(s, num):
#  tmp = s.order(ascending=False)[:num]
#  return tmp.sum()
#
#def hhi(s):
#  tmp = (s / 100.0)**2
#  return tmp.sum()
#
#se_cr1_n = df_reg[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 1), axis = 1)
#se_cr2_n = df_reg[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 2), axis = 1)
#se_cr3_n = df_reg[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 3), axis = 1)
#se_cr4_n = df_reg[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 4), axis = 1)
#
#se_cr1_s = df_reg_surf[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 1), axis = 1)
#se_cr2_s = df_reg_surf[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 2), axis = 1)
#se_cr3_s = df_reg_surf[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 3), axis = 1)
#se_cr4_s = df_reg_surf[ls_reg_disp[:-2]].apply(lambda x: compute_cr(x, 4), axis = 1)
#
#se_hhi_n = df_reg[ls_reg_disp[:-2]].apply(lambda x: hhi(x), axis = 1)
#se_hhi_s = df_reg_surf[ls_reg_disp[:-2]].apply(lambda x: hhi(x), axis = 1)
#
#df_reg_cr = pd.DataFrame({'CR1_n' : se_cr1_n,
#                          'CR2_n' : se_cr2_n,
#                          'CR3_n' : se_cr3_n,
#                          'CR4_n' : se_cr4_n,
#                          'CR1_s' : se_cr1_s,
#                          'CR2_s' : se_cr2_s,
#                          'CR3_s' : se_cr3_s,
#                          'CR4_s' : se_cr4_s,
#                          'HHI_n' : se_hhi_n,
#                          'HHI_s' : se_hhi_s})
#
#ls_disp = ['CR1_n' , 'CR2_n', 'CR3_n', 'CR4_n',
#           'CR1_s' , 'CR2_s', 'CR3_s', 'CR4_s',
#           'HHI_n', 'HHI_s']
#
#dict_formatters = {'HHI_n' : format_float_float,
#                   'HHI_s' : format_float_float}
#
## pbm: need to precise display for HHI columns + pbms with small brands
#print df_reg_cr[ls_disp].to_latex(formatters = dict_formatters)

# ###############
# OUTPUT TO CSV
# ###############

# ALL
df_lsa.to_csv(os.path.join(path_dir_built_csv, 'df_lsa.csv'),
              encoding = 'UTF-8', float_format='%.3f')

# ACTIVE STORES IN METROPOLITAN FRANCE
df_lsa_active_fm.to_csv(os.path.join(path_dir_built_csv, 'df_lsa_active_fm.csv'),
                        encoding = 'UTF-8', float_format='%.3f')

# ACTIVE STORES H/S/X IN METROPOLITAN FRANCE
df_lsa_a_f_hsx.to_csv(os.path.join(path_dir_built_csv, 'df_lsa_active_fm_hsx.csv'),
                     encoding = 'UTF-8', float_format='%.3f')

# H/S/X IN METROPOLITAN FRANCE
df_lsa_fm_hsx.to_csv(os.path.join(path_dir_built_csv, 'df_lsa_fm_hsx.csv'),
                     encoding = 'UTF-8', float_format='%.3f')

# ###############
# OUTPUT TO EXCEL
# ###############

## todo check if valid
#for field in [u'DATE ouv', u'DATE ferm', u'DATE réouv',
#              u'DATE chg enseigne', u'DATE chgt surf']:
#  df_lsa[field][df_lsa[field] < '1900'] = pd.tslib.NaT
#  df_lsa[field] = df_lsa[field].apply(lambda x: x.date()\
#                                        if type(x) is pd.tslib.Timestamp\
#                                        else pd.tslib.NaT)
#
#writer = pd.ExcelWriter(os.path.join(path_dir_built_csv, 'LSA_enriched.xlsx'))
#df_lsa.to_excel(writer, index = False)
#writer.close()
