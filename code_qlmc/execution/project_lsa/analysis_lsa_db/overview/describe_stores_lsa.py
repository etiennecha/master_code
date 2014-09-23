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

# READ LSA EXCEL FILE
# need to work with _no1900 at CREST for now (older versions of numpy/pandas/xlrd...?)
df_lsa_all = pd.read_excel(os.path.join(path_dir_source_lsa,
                                               '2014-07-30-export_CNRS_no1900.xlsx'),
                           sheetname = 'Feuil1')
df_lsa = df_lsa_all

# Convert dates to pandas friendly format
# Can not use np.datetime64() as missing value
for field in [u'DATE ouv', u'DATE ferm', u'DATE réouv',
              u'DATE chg enseigne', u'DATE chgt surf']:
  df_lsa[field] = df_lsa[field].apply(lambda x: x.replace(hour=0, minute=0,
                                                          second=0, microsecond=0)\
                                        if (type(x) is datetime.datetime) or\
                                           (type(x) is pd.Timestamp)
                                        else pd.tslib.NaT)

print u'Stores in data (active or not): {0:5d}'.format(len(df_lsa))

# Create retail group variable

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

# Stores still operating (add for any date e.g. 01/01/2014)
df_lsa_active = df_lsa[(pd.isnull(df_lsa[u'DATE ferm'])) |\
                       ((~pd.isnull(df_lsa[u'DATE ferm'])) &\
                        (~pd.isnull(df_lsa[u'DATE réouv'])))].copy()
print u'Stores still operating: {0:5d}'.format(len(df_lsa_active))

# Stores no more operating
df_lsa_inactive = df_lsa[(~pd.isnull(df_lsa[u'DATE ferm'])) &\
                         (pd.isnull(df_lsa[u'DATE réouv']))].copy()
print u'Stores no more operating: {0:5d}'.format(len(df_lsa_inactive))

# Describe variables of operating stores
for field in ['Statut', 'Type', 'Enseigne', 'Ex enseigne', 'Groupe']:
  print u'\nValue counts for:', field
  print u'-'*20
  print df_lsa_active[field].value_counts()

# STATS BY TYPE
pd.set_option('float_format', '{:10.0f}'.format)

dict_type_out = {'S' : 'Supermarkets',
                 'H' : 'Hypermarkets',
                 'DRIN' : 'Drive in',
                 'X' : 'Hard discount',
                 'DRIVE' : 'Drive',
                 'MP' : '"Magasins populaires'}

for field in ['Surf Vente', 'Nbr de caisses', 'Nbr parking', 'Pompes']:
  print '\n', field
  gbt = df_lsa_active[['Type', field]].groupby('Type',
                                                      as_index = False)
  df_surf = gbt.agg([len, np.mean, np.median, np.min, np.max, np.sum])[field]
  df_surf.sort('len', ascending = False, inplace = True)
  se_null_vc = df_lsa_active['Type'][pd.isnull(df_lsa_active[field])].value_counts()
  df_surf['#Null'] = se_null_vc
  df_surf.rename(columns = {'len' : '#Tot',
                            'mean': 'Avg',
                            'median': 'Med',
                            'amin': 'Min',
                            'amax': 'Max',
                            'sum': 'Cum'}, inplace = True)
  ls_surf_disp = ['#Tot', '#Null', 'Avg', 'Med', 'Min', 'Max', 'Cum']
  df_surf.reset_index(inplace = True)
  df_surf['Type'] = df_surf['Type'].apply(lambda x: dict_type_out[x])
  df_surf.set_index('Type', inplace = True)
  print df_surf[ls_surf_disp].to_latex(index_names = False)

# todo: inspect suspect values
pd.set_option('display.max_columns', 50)
#print df_lsa_active[df_lsa_active['Nbr de caisses'] > 100]
#print df_lsa_active[(df_lsa_active['Type'] == 'X') &\
#                    (df_lsa_active['Nbr de caisses'] > 20)]
#print df_lsa_active[(df_lsa_active['Type'] == 'DRIVE') &\
#                    (df_lsa_active['Nbr de caisses'] > 20)]
#df_lsa_active[df_lsa_active['Nbr parking']<10]

# STATS ON NB OF STORES AND SURFACE BY RETAIL GROUPS/CHAINS

# Stats desc by retail group
print '\nStats des per retail group'
df_lsa_gps = df_lsa_active[(df_lsa_active['Type'] != 'DRIN') &\
                           (df_lsa_active['Type'] != 'DRIVE')]
gbg = df_lsa_gps[['Groupe', 'Surf Vente']].groupby('Groupe',
                                                   as_index = False)
df_surf = gbg.agg([len, np.mean, np.median, np.min, np.max, np.sum])['Surf Vente']
df_surf.sort('len', ascending = False, inplace = True)
# print df_surf.to_string()
df_types = pd.DataFrame(columns = ['H', 'S', 'X', 'MP']).T
for groupe in df_lsa_gps['Groupe'].unique():
  se_types_vc = df_lsa_gps['Type'][df_lsa_gps['Groupe'] == groupe].value_counts()
  df_types[groupe] = se_types_vc
df_types.fillna(0, inplace = True)
df_types = df_types.T
# print df_types.to_string()
df_rgps = pd.merge(df_types, df_surf, left_index = True, right_index = True)
df_rgps.sort('len', ascending = False, inplace = True)
df_rgps.rename(columns = {'len' : '#Tot',
                          'mean': 'Avg S.',
                          'median': 'Med S.',
                          'amin': 'Min S.',
                          'amax': 'Max S.',
                          'sum': 'Cum S.',
                          'H' : '#Hyp',
                          'S' : '#Sup',
                          'X' : '#Dis',
                          'MP': '#MP'}, inplace = True)
ls_rgps_disp = ['#Tot', '#Hyp', '#Sup', '#Dis', '#MP',
                'Avg S.', 'Med S.', 'Min S.', 'Max S.', 'Cum S.']
print df_rgps[ls_rgps_disp].to_latex()

# Stats desc by enseigne (and by group)
print '\nStats des per retail group'
for retail_group in dict_groupes.keys():
  print '\n', retail_group
  df_lsa_rgp = df_lsa_active[(df_lsa_active['Groupe'] == retail_group) &\
                             (df_lsa_active['Type'] != 'DRIN') &\
                             (df_lsa_active['Type'] != 'DRIVE')]
  gbg = df_lsa_rgp[['Enseigne', 'Surf Vente']].groupby('Enseigne',
                                                       as_index = False)
  df_surf = gbg.agg([len, np.mean, np.median, np.min, np.max, np.sum])['Surf Vente']
  df_surf.sort('len', ascending = False, inplace = True)
  # print df_surf.to_string()
  df_types = pd.DataFrame(columns = ['H', 'S', 'X', 'MP']).T
  for enseigne in df_lsa_rgp['Enseigne'].unique():
    se_types_vc = df_lsa_rgp['Type'][df_lsa_rgp['Enseigne'] == enseigne].value_counts()
    df_types[enseigne] = se_types_vc
  df_types.fillna(0, inplace = True)
  df_types = df_types.T
  # print df_types.to_string()
  df_rgp = pd.merge(df_types, df_surf, left_index = True, right_index = True)
  df_rgp.sort('len', ascending = False, inplace = True)
  df_rgp.rename(columns = {'len' : '#Tot',
                           'mean': 'Avg S.',
                           'median': 'Med S.',
                           'amin': 'Min S.',
                           'amax': 'Max S.',
                           'sum': 'Cum S.',
                           'H' : '#Hyp',
                           'S' : '#Sup',
                           'X' : '#Dis',
                           'MP': '#MP'}, inplace = True)
  ls_rgp_disp = ['#Tot', '#Hyp', '#Sup', '#Dis', '#MP',
                 'Avg S.', 'Med S.', 'Min S.', 'Max S.', 'Cum S.']
  print df_rgp[ls_rgp_disp].to_latex()

#print u'\nNb stores (dead or alive) with valid gps:'
#print len(df_lsa[(~pd.isnull(df_lsa['Longitude'])) &\
#                 (~pd.isnull(df_lsa['Latitude']))])
#

# STATS ON NB OF STORES BY GROUP AND REGION

dict_dpts_regions = dec_json(os.path.join(path_dir_insee,
                                          'dpts_regions',
                                          'dict_dpts_regions.json'))
df_lsa_active['Dpt'] = df_lsa_active['Code INSEE'].str.slice(stop=-3)
df_lsa_active['Reg'] = df_lsa_active['Dpt'].apply(\
                         lambda x: dict_dpts_regions.get(x, 'DOMTOM'))
df_reg = pd.DataFrame(columns = df_lsa_active['Reg'].unique()).T
for groupe in df_lsa_active['Groupe'].unique():
  se_reg_vc = df_lsa_active['Reg'][(df_lsa_active['Groupe'] == groupe) &
                                   (df_lsa_active['Type'] != 'DRIN') &\
                                   (df_lsa_active['Type'] != 'DRIVE')].value_counts()
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
## OUTPUT FOR MAP CREATION
#df_lsa_active.to_csv(os.path.join(path_dir_built_csv, 'df_lsa_active.csv'),
#                     encoding = 'UTF-8', float_format='%.3f')

# INSPECT ACT ANNEXES / DRIVE
ls_drive_temp = df_lsa_active['Act Annexes'][~pd.isnull(df_lsa_active['Act Annexes'])].values
ls_drive_idents = []
for x in ls_drive_temp:
  if isinstance(x, unicode):
    for y in x.split(','):
      ls_drive_idents.append(int(y.strip()))
  else:
    ls_drive_idents.append(x)
df_drive = df_lsa_active[df_lsa_active['Ident'].isin(ls_drive_idents)]

#ls_acp_types = []
#for x in ls_ident_drive:
#  if isinstance(x, unicode):
#    type_val = df_lsa_active['Type'][df_lsa_active['Ident'] ==\
#                                       int(x.split(',')[-1].strip())].values
#  else:
#    type_val = df_lsa_active['Type'][df_lsa_active['Ident'] == x].values
#  if type_val:
#    ls_acp_types.append(type_val[0])
## pd.Series(ls_acp_types).value_counts()

# INTER RETAIL GROUP BRAND CHANGES (ACTIVE STORES)

ls_disp_1 = [u'Ident', u'Enseigne', u'ADRESSE1', u'Ville', 'Code INSEE',
             u'DATE ouv', u'DATE ferm', u'DATE réouv']

ls_disp_2 = [u'Ident', u'Enseigne', u'Ex enseigne', u'DATE chg enseigne', u'Ville', 'Code INSEE',
             u'DATE ouv', u'DATE ferm', u'DATE réouv']

print u'\nStores with retail group change'
df_lsa_chge = df_lsa_active[(~pd.isnull(df_lsa_active['Ex groupe'])) &\
                            (df_lsa_active['Groupe'] != df_lsa_active['Ex groupe'])]
print u'Stores in groupe chge (incl. AUTRE): {0:5d}'.format(len(df_lsa_chge))

df_lsa_chge_2 = df_lsa_active[(~pd.isnull(df_lsa_active['Ex groupe'])) &\
                              (df_lsa_active['Ex groupe'] != 'AUTRE') &\
                              (df_lsa_active['Groupe'] != 'AUTRE') &\
                              (df_lsa_active['Groupe'] != df_lsa_active['Ex groupe'])]
print u'Stores in groupe chge (no AUTRE): {0:5d}'.format(len(df_lsa_chge_2))

#print df_lsa_chge[ls_disp_2].to_string()
#print df_lsa_chge_2[ls_disp_2].to_string()

# SIRET/SIREN: duplicates
df_lsa[u'N°Siren'] = df_lsa[u'N°Siren'].apply(\
                       lambda x: u'{:09d}'.format(int(x)) if not pd.isnull(x)\
                                                          else None)
df_lsa[u'N°Siret'] = df_lsa[u'N°Siret'].apply(\
                       lambda x: u'{:05d}'.format(int(x)) if not pd.isnull(x)\
                                                          else None)
df_lsa[u'Siret'] = df_lsa[u'N°Siren'] + df_lsa[u'N°Siret']
se_siret_vc = df_lsa[u'Siret'].value_counts()
df_lsa.set_index(u'Siret', inplace = True)
df_lsa[u'dup'] = se_siret_vc

df_dup = df_lsa[df_lsa['dup'] == 2].copy()
df_dup.sort(inplace = True)
#print df_dup[ls_disp_1].to_string()

# GENERA DUPLICATE DETECTION
# loop on closed store... search newly opened stores within same area (or same siret btw)
df_lsa_closed_a = df_lsa[(~pd.isnull(df_lsa[u'DATE ferm'])) &\
                         (pd.isnull(df_lsa[u'DATE réouv']))].copy()
df_lsa_closed_a.sort(columns = ['Code INSEE', 'DATE ouv'], inplace = True)
# Quite a few indec (siret) are NaN (see why) hence change index back to Ident
df_lsa_closed_a['Siret'] = df_lsa_closed_a.index
df_lsa_closed_a.index = df_lsa_closed_a['Ident']
df_lsa['Siret'] = df_lsa.index
df_lsa.index = df_lsa['Ident']
# Look for store opened after store closed within same INSEE area
ls_suspects = []
for i, row_i in df_lsa_closed_a.iterrows():
  # print '\nFermeture:', row_i[u'DATE ferm']
  ls_open = []
  for j, row_j in df_lsa[df_lsa[u'Code INSEE'] == row_i['Code INSEE']].iterrows():
    # crashes if DATE ouv is NaT (how many?)
    if not pd.isnull(row_j[u'DATE ouv']):
      td = row_j[u'DATE ouv'] - row_i[u'DATE ferm']
      # could drop second condition
      if (td >= datetime.timedelta(days=0)) and\
         (td <= datetime.timedelta(days=365)):
        #print 'Ouverture, :', row_i[u'DATE ouv'], 'Time delta:', td
        #print row_i[u'Enseigne'], row_i['ADRESSE1'], row_i['Siret']
        #print row_j[u'Enseigne'], row_j['ADRESSE1'], row_j['Siret']
        ls_open.append([row_j['Ident'], td])
  ls_suspects.append([row_i['Ident'], ls_open])

# Check chains and if stores closed after reconciliation
# Check results (can use index)
ls_s_noclosed_ind = []
ls_s_closed_ind = []
for row in ls_suspects:
  if row[1]:
    ls_s_noclosed_ind.append(row[0])
    for subrow in row[1]:
      ls_s_noclosed_ind.append(subrow[0])
  else:
    ls_s_closed_ind.append(row[0])

# df_lsa[ls_disp_1].ix[[20, 124704]]

#print u'\nStores with multiple lines'
#print df_lsa[ls_disp_1].ix[ls_s_noclosed_ind].to_string()
#
#print u'\nStores potentially closed and not replaced'
#print df_lsa[ls_disp_1].ix[ls_s_closed_ind].to_string()
#
## Inspect: new opening very same day
## Inspect: new opening later on (any date...)
#
## Check these weird lines
#print u'\nWeird lines: opened and closed on same date'
#print df_lsa[ls_disp_1][df_lsa['DATE ouv'] == df_lsa['DATE ferm']].to_string()

# todo: increase in store surface?
# todo: gps quality? missing data? distances? (google API)

#
### FORMAT DATE AND OUTPUT TO EXCEL FILE
##for field in [u'DATE ouv', u'DATE ferm', u'DATE réouv',
##              u'DATE chg enseigne', u'DATE chgt surf']:
##  df_lsa[field][df_lsa[field] < '1900'] = pd.tslib.NaT
##  df_lsa[field] = df_lsa[field].apply(lambda x: x.date()\
##                                        if type(x) is pd.tslib.Timestamp\
##                                        else pd.tslib.NaT)
##
##writer = pd.ExcelWriter(os.path.join(path_dir_built_csv, 'LSA_enriched.xlsx'))
##df_lsa.to_excel(writer, index = False)
##writer.close()

# todo: get ARDT for big cities thx to gps

## INTEGRATE INSEE DATA FOR ANALYSIS
#df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_insee_areas.csv'))
#df_au_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_au_agg_final.csv'))
#df_uu_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_uu_agg_final.csv'))
#
## Add insee area codes to df_fra_stores
#df_lsa = pd.merge(df_insee_areas,
#                  df_lsa,
#                  left_on = 'CODGEO',
#                  right_on = 'Code INSEE',
#                  how = 'right')
#
## NB STORES BY AU IN A GIVEN PERIOD
#df_au_agg.index = df_au_agg['AU2010']
#ls_disp_au = ['AU2010', 'LIBAU2010', 'P10_POP', 'SUPERF', 'POPDENSITY10', 'QUAR2UC10',
#              'nb_stores', 'pop_by_store']
#
#se_au_vc = df_lsa['AU2010'][~pd.isnull(df_lsa['2010-03'])].value_counts()
#df_au_agg['nb_stores'] = se_au_vc
#df_au_agg['pop_by_store'] = df_au_agg['P10_POP'] / df_au_agg['nb_stores'] 
#
#print df_au_agg[ls_disp_au][0:10].to_string()
#
#
## Nb stores vs. population (# stores by head decreasing in population density?)
## exclude paris (+ todo: check with exclusion of au internationales)
#plt.scatter(df_au_agg['P10_POP'][df_au_agg['AU2010']!='001'],
#            df_au_agg['nb_stores'][df_au_agg['AU2010']!='001'])
#plt.show()
#
### Store density vs. pop density (# stores by head decreasing in population density?)
##plt.scatter(df_au_agg['POPDENSITY10'][df_au_agg['AU2010']!='001'],
##            df_au_agg['pop_by_store'][df_au_agg['AU2010']!='001'])
##plt.show()
#
## STORE SURFACE BY AU (todo: take period into account)
#df_au_agg['surf_vente_cum'] = df_lsa[['AU2010', 'Surf Vente']].groupby('AU2010').sum()
#df_au_agg['pop_by_surf_vente'] = df_au_agg['P10_POP'] / df_au_agg['surf_vente_cum']
#print df_au_agg[ls_disp_au + ['surf_vente_cum', 'pop_by_surf_vente']][0:10].to_string()


## NB STORES BY UU
#df_uu_agg.index = df_uu_agg['UU2010']
#ls_disp_uu = ['UU2010', 'LIBUU2010', 'P10_POP', 'SUPERF', 'POPDENSITY10', 'QUAR2UC10',
#              'nb_stores', 'pop_by_store']
#
#se_au_vc = df_fra_stores['UU2010'].value_counts()
#df_uu_agg['nb_stores'] = se_au_vc
#df_uu_agg['pop_by_store'] = df_uu_agg['P10_POP'] / df_uu_agg['nb_stores']
#
#df_uu_agg.sort('P10_POP', ascending=False, inplace=True)
#print df_uu_agg[ls_disp_uu][df_uu_agg['nb_stores'] >= 1][0:10].to_string()
#
### Nb stores vs. population (# stores by head decreasing in population density?)
### exclude paris (+ todo: check with exclusion of au internationales)
##plt.scatter(df_uu_agg['P10_POP'][df_uu_agg['AU2010']!='001'],
##            df_uu_agg['nb_stores'][df_uu_agg['AU2010']!='001'])
##plt.show()
##
### Store density vs. pop density (# stores by head decreasing in population density?)
##plt.scatter(df_uu_agg['POPDENSITY10'][df_uu_agg['AU2010']!='001'],
##            df_uu_agg['pop_by_store'][df_uu_agg['AU2010']!='001'])
##plt.show()
