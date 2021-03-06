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

path_source = os.path.join(path_data,
                           'data_supermarkets',
                           'data_source',
                           'data_lsa')

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                            'data_csv')

path_insee = os.path.join(path_data, 'data_insee')
path_insee_match = os.path.join(path_insee, 'match_insee_codes')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

# ###################
# READ LSA EXCEL FILE
# ###################

# Need to work with _no1900 at CREST for now (older versions of numpy/pandas/xlrd...?)
df_lsa = pd.read_excel(os.path.join(path_source,
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

# ####################
# FORMAT SIRET & SIREN
# ####################

df_lsa[u'Code SIREN'] = df_lsa[u'N°Siren'].apply(\
                          lambda x: u'{:09d}'.format(int(x)) if not pd.isnull(x)\
                                                             else None)
df_lsa[u'Code NIC'] = df_lsa[u'N°Siret'].apply(\
                        lambda x: u'{:05d}'.format(int(x)) if not pd.isnull(x)\
                                                           else None)
df_lsa[u'Code SIRET'] = df_lsa[u'Code SIREN'] + df_lsa[u'Code NIC']
df_lsa.drop([u'N°Siren', u'N°Siret'], axis = 1, inplace = True)

# ##########################
# FORMAT CODE POSTAL & INSEE
# ##########################

df_lsa['Code postal'] = df_lsa['Code postal'].apply(\
                          lambda x: u'{:05d}'.format(x) if not pd.isnull(x)\
                                                        else None)

# Code INSEE properly read as string thanks to Corse
df_lsa['Code INSEE'] = df_lsa['Code INSEE'].apply(\
                         lambda x: str(x).replace('76095', '76108'))

def get_insee_from_zip_ardt(zip_code):
  """
  Uses zip to get INSEE code at district level (Paris/Lyon/Marseille)
  """
  zip_code = re.sub(u'750([0-9]{2})', u'751\\1', zip_code) # 75116 untouched
  zip_code = re.sub(u'130([0-9]{2})', u'132\\1', zip_code)
  zip_code = re.sub(u'6900([0-9])', u'6938\\1', zip_code)
  return zip_code

ls_insee_bc = ['75056', '13055', '69123']

df_lsa['Code INSEE ardt'] = df_lsa['Code INSEE']
df_lsa.loc[df_lsa['Code INSEE'].isin(ls_insee_bc), 'Code INSEE ardt'] =\
    df_lsa.loc[df_lsa['Code INSEE'].isin(ls_insee_bc), 'Code postal'].apply(\
       lambda x: get_insee_from_zip_ardt(unicode(x)))

# ############################
# CREATE DPT AND REG VARIABLES
# ############################

dict_dpts_regions = dec_json(os.path.join(path_insee,
                                          'dpts_regions',
                                          'dict_dpts_regions.json'))
df_lsa['c_departement'] = df_lsa['Code INSEE'].str.slice(stop=-3)
df_lsa['region'] = df_lsa['c_departement'].apply(\
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
df_lsa['Groupe Alt'] = df_lsa['Enseigne'].apply(\
                     lambda x: dict_enseigne_groupe.get(x, 'AUTRE') if not pd.isnull(x)\
                                                       else None)
df_lsa['Ex Groupe'] = df_lsa['Ex enseigne'].apply(\
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

df_lsa['Enseigne alt'] = df_lsa['Enseigne']
df_lsa['Enseigne alt'] = df_lsa['Enseigne alt'].apply(\
                           lambda x: dict_alt_enseignes[x] if x in dict_alt_enseignes\
                                                           else x)

df_lsa['Ex enseigne alt'] = df_lsa['Ex enseigne']
df_lsa['Ex enseigne alt'] = df_lsa['Ex enseigne alt'].apply(\
                           lambda x: dict_alt_enseignes[x] if x in dict_alt_enseignes\
                                                           else x)

# ###############################
# GET RID OF MAGASINS POPULAIRES
# ###############################

# Drop if surface below 400m2, else either Supermarket or Hypermarket
df_lsa = df_lsa[~((df_lsa['Type'] == 'MP') & (df_lsa['Surf Vente'] < 400))].copy()
df_lsa['Type Alt'] = df_lsa['Type']
df_lsa.loc[(df_lsa['Type'] == 'MP') & (df_lsa['Surf Vente'] < 2500),
           'Type Alt'] = 'S'
df_lsa.loc[(df_lsa['Type'] == 'MP') & (df_lsa['Surf Vente'] >= 2500),
           'Type Alt'] = 'H'

# ##############
# RENAME COLUMNS
# ##############

# drop empty columns
df_lsa.drop(['Surf alim/couverte', 'Surf non alim/non couverte'],
            axis = 1,
            inplace = True)

df_lsa.rename(columns = {u'Ident' : 'id_lsa',
                         u'Centrale/Siege' : u'centrale_siege',
                         u'Etb affiliation' : u'etb_affiliation',
                         u"Nom de l'établissement" : u'nom',
                         u'Sté exploit': u'ste_exploitante',
                         u'ADRESSE1' : u'adresse1',
                         u'ADRESSE2' : u'adresse2',
                         u'ADRESSE3' : u'adresse3',
                         u'Surf Vente' : u'surface',
                         u'Anc Surf Vente' : u'ex_surface',
                         u'Nbr de caisses' : u'nb_caisses',
                         u'Nbr emp' : u'nb_emplois',
                         u'Nbr parking' : u'nb_parking',
                         u'Pompes' : u'nb_pompes',
                         u'Code postal' : u'c_postal',
                         u'Code INSEE' : u'c_insee',
                         u'Code INSEE ardt' : u'c_insee_ardt',
                         u'Code SIREN' : u'c_siren',
                         u'Code NIC' : u'c_nic',
                         u'Code SIRET': u'c_siret',
                         u'Intégré / Indépendant' : u'int_ind',
                         u'DRIVE' : u'drive',
                         u'DATE ouv' : u'date_ouv',
                         u'DATE ferm' : u'date_fer',
                         u'DATE réouv' : u'date_reouv',
                         u'DATE chg enseigne' : u'date_chg_enseigne',
                         u'DATE chgt surf' : u'date_chg_surface',
                         u'Ex enseigne' : u'ex_enseigne',
                         u'Ex enseigne alt' : u'ex_enseigne_alt',
                         u'Enseigne alt' : u'enseigne_alt',
                         u'Type Alt': 'type_alt',
                         u'Verif' : 'gps_verif'},
              inplace = True)

df_lsa.columns = [x.replace(u' ', u'_').lower() for x in df_lsa.columns]

print u'Overview columns of df_lsa:'
print df_lsa.info()

print u'\nDescribe variables in df_lsa:'
print u'\n', u'-'*120
for field in ['statut', 'type_alt', 'enseigne_alt', 'ex_enseigne', 'groupe']:
  print u'\nValue counts for:', field
  print df_lsa[field].value_counts()
  print u'-'*30

# #########
# BUILD DFS
# #########

print u'\nStores in data: {0:5d}'.format(len(df_lsa)) 
print u'Stores in Dom-Tom dropped from now on'
df_lsa = df_lsa[df_lsa['region'] != 'DOMTOM']
print u'Stores in data without Dom-Tom: {0:5d}'.format(len(df_lsa)) 

# Stores no more operating
df_lsa_inactive = df_lsa[(~pd.isnull(df_lsa[u'date_fer'])) &\
                         (pd.isnull(df_lsa[u'date_reouv']))].copy()
print u'Stores no more operating: {0:5d}'.format(len(df_lsa_inactive))

# Stores still operating (add for any date e.g. 01/01/2014)
df_lsa_active = df_lsa[(pd.isnull(df_lsa[u'date_fer'])) |\
                       ((~pd.isnull(df_lsa[u'date_fer'])) &\
                        (~pd.isnull(df_lsa[u'date_reouv'])))].copy()
print u'Stores still operating: {0:5d}'.format(len(df_lsa_active))

# Stores HSX active
df_lsa_active_hsx = df_lsa_active[(df_lsa_active['type_alt'] != 'DRIN') &\
                                  (df_lsa_active['type_alt'] != 'DRIVE')]
print u'Stores HSX active: {0:5d}'.format(len(df_lsa_active_hsx))

# Stores HSX
df_lsa_hsx = df_lsa[(df_lsa['type_alt'] != 'DRIN') &\
                    (df_lsa['type_alt'] != 'DRIVE')]

print u'Stores HSX: {0:5d}'.format(len(df_lsa_hsx))

# ###############
# OUTPUT TO CSV
# ###############

# ALL
df_lsa.to_csv(os.path.join(path_built_csv,
                           'df_lsa.csv'),
              encoding = 'UTF-8',
              float_format ='%.3f',
              index = False)

# ACTIVE STORES
df_lsa_active.to_csv(os.path.join(path_built_csv,
                                  'df_lsa_active.csv'),
                     encoding = 'UTF-8',
                     float_format = '%.3f',
                     index = False)

# ACTIVE STORES H/S/X
df_lsa_active_hsx.to_csv(os.path.join(path_built_csv,
                                      'df_lsa_active_hsx.csv'),
                         encoding = 'UTF-8',
                         float_format='%.3f',
                         index = False)

# H/S/X
df_lsa_hsx.to_csv(os.path.join(path_built_csv,
                               'df_lsa_hsx.csv'),
                  encoding = 'UTF-8',
                  float_format='%.3f',
                  index = False)

# ###############
# OUTPUT TO EXCEL
# ###############

## todo check if valid
#for field in [u'date_ouv', u'date_fer', u'date_reouv',
#              u'date_chg_enseigne', u'DATE_chg_surface']:
#  df_lsa[field][df_lsa[field] < '1900'] = pd.tslib.NaT
#  df_lsa[field] = df_lsa[field].apply(lambda x: x.date()\
#                                        if type(x) is pd.tslib.Timestamp\
#                                        else pd.tslib.NaT)
#
#writer = pd.ExcelWriter(os.path.join(path_built_csv, 'LSA_enriched.xlsx'))
#df_lsa.to_excel(writer, index = False)
#writer.close()
