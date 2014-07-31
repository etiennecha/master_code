#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import *
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import pandas as pd
from mpl_toolkits.basemap import Basemap
import pprint

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_excel = os.path.join(path_dir_qlmc, 'data_built' , 'data_excel')
path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))
fra_stores = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'fra_stores.h5'))

df_fra_stores = fra_stores['df_fra_stores_current']
df_qlmc_stores = qlmc_data['df_qlmc_stores']

# Ad hoc corrections (temp): to be improved!
# Seems that I need to proceed via index to fix data
print u'\nTo be fixed: ix 6715, insee code 14225'
print df_fra_stores['insee_code'][(df_fra_stores['type'] == u'Hyper U') &\
                                  (df_fra_stores['city'] == u'DIVES SUR MER') &\
                                  (df_fra_stores['street'] == u'Boulevard Maurice Thorez')]
df_fra_stores.ix[6715]['insee_code'] = u'14225'
print u'\nTo be fixed: ix 3177, insee code 36044'
print df_fra_stores['insee_code'][(df_fra_stores['name'] == u'Franprix CHATEAUROUX') &\
                                  (df_fra_stores['zip'] == '36000')]
df_fra_stores.ix[3177]['insee_code'] = u'36044'

# STORE BRAND/TYPE IN EACH DF: NEED TO HARMONIZE

## types in df_qlmc_stores
#print df_qlmc_stores['Enseigne'].value_counts()

# INTERMARCHE          745 : keep => rgp in df_fra_stores
# AUCHAN               705 : keep => same in df_fra_stores
# SUPER U              610 : keep or SYSTEME U (HYPER U + SUPER U?) in df_fra_stores
# GEANT CASINO         581 : keep or CASINO
# LECLERC              540 : keep
# CARREFOUR MARKET     498 : keep or CARREFOUR
# CARREFOUR            472 : keep
# CORA                 416 : keep
# CHAMPION             341 : CARREFOUR MARKET OR CARREFOUR
# CENTRE E. LECLERC    144 : LECLERC
# HYPER U               64 : keep or SYSTEME U
# SYSTEME U             50 : keep
# E.LECLERC             49 : LECLERC
# GEANT                 49 : GEANT CASINO or?
# HYPER CHAMPION        20 : CARREFOUR AND CARREFOUR MARKET
# GEANT DISCOUNT         9 : GEANT CASINO or ?
# LECLERC EXPRESS        4 : LECLERC (check what it means)
# U EXPRESS              3 : keep or SYSTEME U?
# MARCHE U               2 : keep or SYSTEME U?
# CENTRE LECLERC         1 : LECLERC
# CARREFOUR CITY         1 : keep or CARREFOUR CITY?

## types in df_fra_stores
#print df_fra_stores['type'].value_counts()

dict_fra_stores_alt_brand = {u'Intermarché Super': u'Intermarché',
                             u'Intermarché Contact': u'Intermarché',
                             u'Intermarché Hyper' : u'Intermarché',
                             u'Intermarché Express': u'Intermarché',
                             u'Carrefour Market' : u'Carrefour',
                             #u'Carrefour City': u'Carrefour',
                             #u'Carrefour Contact': u'Carrefour',
                             #u'Carrefour Express' : u'Carrefour',
                             u'Market': u'Carrefour',
                             u'Super U' : u'Système U',
                             u'U Express' : u'Système U',
                             u'Marche U': u'Système U',
                             u'Hyper U': u'Système U',
                             u'U Express' : u'Système U',
                             u'Supermarché Casino' : u'Casino',
                             u'Hyper Casino': u'Casino',
                             u'Géant Casino' : u'Casino'}

df_fra_stores['type_alt'] = df_fra_stores['type'].apply(\
                              lambda x: dict_fra_stores_alt_brand[x]\
                                          if dict_fra_stores_alt_brand.get(x)\
                                          else x)

ls_matching = [[u'INTERMARCHE', u'Intermarché Super', u'Intermarché'],
               [u'AUCHAN', u'Auchan', u'Auchan'],
               [u'SUPER U', 'Super U', u'Système U'],
               [u'GEANT CASINO', u'Géant Casino', u'Casino'],
               [u'LECLERC', u'Leclerc', u'Leclerc'],
               [u'CARREFOUR MARKET', u'Carrefour Market', u'Carrefour'],
               [u'CARREFOUR', u'Carrefour', u'Carrefour'],
               [u'CORA', u'Cora', u'Cora'],
               [u'CHAMPION', u'Carrefour Market', u'Carrefour'],
               [u'CENTRE E. LECLERC', u'Leclerc', u'Leclerc'],
               [u'GEANT', u'Géant Casino', u'Casino'],
               [u'HYPER CHAMPION', u'Carrefour', u'Carrefour'],
               [u'GEANT DISCOUNT', u'Géant Casino', u'Casino'],
               [u'LECLERC EXPRESS', u'Leclerc', u'Leclerc'],
               [u'U EXPRESS', u'U Express', u'Système U'],
               [u'MARCHE U', u'Marche U', u'Marche U'],
               [u'CENTRE LECLERC', u'Leclerc', u'Leclerc'],
               [u'CARREFOUR CITY', u'Carrefour City', u'Carrefour']]

# PRELIMINARY MATCHING
# Meant for specific enough brands found in both df

ls_spe_matched = []
enseigne_qlmc, enseigne_fra = u'HYPER U', u'Hyper U'
for row_ind, row in df_qlmc_stores[(df_qlmc_stores['Enseigne'] == enseigne_qlmc)].iterrows():
  insee_code = row['INSEE_Code']
  df_city_stores = df_fra_stores[(df_fra_stores['insee_code'] == insee_code) &\
                                 (df_fra_stores['type'] == enseigne_fra)]
  if len(df_city_stores) == 1:
    ls_spe_matched.append([row['Enseigne'], row['Commune'], df_city_stores['name']])
  else:
    print '\n', row['Enseigne'], row['Commune'], row['INSEE_Code']
    print df_city_stores.to_string()

#print df_fra_stores[(df_fra_stores['type'] == 'Auchan') &\
#                    (df_fra_stores['zip'].str.slice(stop=2)=='59')].to_string()

# add Auchan La Seyne sur Mer: travaux...
# http://www.varmatin.com/la-seyne-sur-mer/le-futur-auchan-de-la-seyne-se-devoile.1490487.html
# add Auchan Montgeron Vigneux sur Seine: no idea why not in data

## SYSTEMATIC MATCHING

ls_matched_stores = []
for enseigne_qlmc, enseigne_fra, enseigne_fra_alt in ls_matching:
  for row_ind, row in df_qlmc_stores[(df_qlmc_stores['Enseigne'] == enseigne_qlmc)].iterrows():
    insee_code = row['INSEE_Code']
    df_city_stores = df_fra_stores[(df_fra_stores['insee_code'] == insee_code) &\
                                   (df_fra_stores['type'] == enseigne_fra)]
    if len(df_city_stores) == 1:
      ls_matched_stores.append((int(row['P']),
                                row['Enseigne'],
                                row['Commune'],
                                df_city_stores.index[0]))
    else:
      df_city_stores_alt = df_fra_stores[(df_fra_stores['insee_code'] == insee_code) &\
                                         (df_fra_stores['type_alt'] == enseigne_fra_alt)]
      if len(df_city_stores_alt) == 1:
        ls_matched_stores.append((int(row['P']),
                                  row['Enseigne'],
                                  row['Commune'],
                                  df_city_stores_alt.index[0]))

df_matched = pd.DataFrame(ls_matched_stores,
                          columns = ['P', 'Enseigne', 'Commune', 'ind_fra_stores'])

df_qlmc_stores_ma = pd.merge(df_matched, df_qlmc_stores,
                             on = ['P', 'Enseigne', 'Commune'],
                             how = 'right')

# Disambiguiation: big communes
df_unmatched = df_qlmc_stores_ma[pd.isnull(df_qlmc_stores_ma['ind_fra_stores'])]
print df_unmatched['INSEE_Code'].value_counts()[0:10]
print df_qlmc_stores_ma[df_qlmc_stores_ma['INSEE_Code'] == u'49007'].to_string()

ls_df_toextract = []
for insee_code in df_unmatched['INSEE_Code'].value_counts()[0:30].index:
  ls_df_toextract.append(df_qlmc_stores_ma[df_qlmc_stores_ma['INSEE_Code'] == insee_code])
df_to_extract = pd.concat(ls_df_toextract)
df_to_extract.sort(columns=['INSEE_Code', 'Enseigne', 'Commune'], inplace = True)
print df_to_extract.to_string()

# Rather: create excel file... fill it and re-read it
ls_fix_ms = [[[u'452'   , u'2784' , u"Avenue Montaigne"],
              [u'GEANT CASINO'],
              [u'ANGERS CC ANJOU',
               u'ANGERS CC ESPACE ANJOU',
               u'ANGERS ESPACE ANJOU']],
             [[u'12507' , u'2785' , u"172 rue Létanduère" ],
              [u'GEANT CASINO'],
              [u'ANGERS LA ROSERAIE']], # P 10 is ROSERAIE by deduction... 1/7/9 still pbm
             [[u'123'   , u'141'  , u"Boulevard Gaston Ramon"],
              [u'CARREFOUR'],
              [u'ANGERS CC ST SERGE']],
             [[u'603'   , u'140'  , u"Centre commercial Grand Maine - Rue du Grand Launay"],
              [u'CARREFOUR'],
              [u'ANGERS CC GD MAINE']], # detail seulement en P8, sinon un non precise
             [[u'3028'  , u'7264' , u"6 Square Louis Jouvet"],
              ['SUPER U'],
              [u'ANGERS L. JOUVET']], # detail seulement en P4, sinon un non precise
             [[u'446'   , u'2718' , u"504 avenue du Mas d'Argelliers"],
              [u'GEANT CASINO'],
              [u"MONTPELLIER ARGELLIERS",
               u"MONTPELLIER AV ARGELLIERS",
               u"MONTPELLIER AVE ARGELLIERS",
               u"MONTPELLIER MAS ARGELLIERS",
               u"MONTPELLIER D''ARGELLIERS",
               u"MONTPELLIER MAS D''ARGE",
               u"MONTPELLIER MAS D''ARGELLIERS"]],
             [[u'3475'  , u'2719' , u"129 bis abvenue de Lodève"], # fix?
              [u'GEANT CASINO'],
              [u"MONTPELLIER LODEVE",
               u"MONTPELLIER AV LODEVE",
               u"MONTPELLIER AV DE LODEVE",
               u"MONTPELLIER AVE DE LODEVE",
               u"MONTPELLIER AVE LODEVE",
               u"MONTPELLIER AVENUE DE LODÈVE"]],
             [[u'171296', u'2721' , u'Rue G. Melies'],
              [u'GEANT CASINO'],
              [u'MONTPELLIER CC ODYSSEUM',
               u'MONTPELLIER C C ODYSSEUM',
               u'MONTPELLIER PLACE LISBONNE',
               u'MONTPELLIER ODYSSEUM']], # P 0 can not be identified
             [[u'503'   , u'2704', u"Avenue du Souvenir Français"],
              [u'GEANT CASINO'],
              [u'CARCASSONNE C.C. CITE2',
               u'CARCASSONNE SOUV. Français',
               u'CARCASSONNE AV S.FRANCAIS',
               u'CARCASSONNE AVE DU SOUVENIR',
               u'CARCASSONNE SOUV.FRANCAIS',
               u'CARCASSONNE AV DU SOUVENIR',
               u'CARCASSONNE SOUV. FRAN',
               u'CARCASSONNE SOUVENIR Fr',
               u'CARCASSONNE SOUVENIR FRANÇAIS']],
             [[u'77'    , u'2703' , u"Centre Commercial Salvaza"],
              [u'GEANT CASINO'],
              [u'CARCASSONNE CC SALVAZA',
                u'CARCASSONNE C C SALVAZA',
                u'CARCASSONNE ZI LA BOURIETTE',
                u'CARCASSONNE SALVAZA']],
             [[u'333'   , u'17'   , u"57, rue du Château d'eau"],
              [u'AUCHAN'],
              [u'BORDEAUX C.C. MERIADECK',
               u'BORDEAUX CC MERIADECK',
               u'BORDEAUX MERIADECK']],
             [[u'114'   , u'18'   , u"Auchan Bordeaux Lac"],
              [u'AUCHAN'],
              [u'BORDEAUX CC LE LAC',
               u'BORDEAUX QUARTIER DU LAC',
               u'BORDEAUX LE LAC']],
             [[u'49262' , u'473'  , u"13 RUE SAGET"],
              [u'CARREFOUR MARKET'],
              [u'BORDEAUX SAINT JEAN']]] # could be ambiguous

ls_rows_fix_ms = []
for ls_store_fix in ls_fix_ms:
  for magasin_libelle in ls_store_fix[2]:
    ls_rows_fix_ms.append(ls_store_fix[0] + ls_store_fix[1] + [magasin_libelle])
ls_columns = ['ind_lsa', 'ind_fra_stores_2', 'street_fra_stores', 'Enseigne', 'Commune']
df_fix_ms = pd.DataFrame(ls_rows_fix_ms, columns = ls_columns)

df_to_extract = pd.merge(df_fix_ms, df_to_extract, on=['Enseigne', 'Commune'], how='right')
df_to_extract.sort(columns = ['INSEE_Code', 'Enseigne', 'P', 'Commune'], inplace = True)
ls_extract_disp = ['P', 'Enseigne', 'Commune',
                   'ind_fra_stores', 'ind_lsa', 'ind_fra_stores_2', 'street_fra_stores']

#http://stackoverflow.com/questions/20219254/
#how-to-write-to-an-existing-excel-file-without-overwriting-data
writer = pd.ExcelWriter(os.path.join(path_dir_built_excel, 'output.xlsx'))
df_to_extract[ls_extract_disp].to_excel(writer, index=False)
writer.close()

# to be applied before corrections
ls_fix_ms_2 = [[u'10', u'GEANT CASINO', u'ANGERS', 'ANGERS LA ROSERAIE'],   #todo: check
               [u'2' , u'GEANT CASINO', u'CARCASSONNE', u'CARCASSONE CC SALVAZA']] # todo: check


# Output for merger with price file
#df_qlmc_stores_matched.to_csv(os.path.join(path_dir_built_csv, 'df_qlmc_stores_matched.csv'),
#                              float_format='%.0f', encoding='utf-8', index=False)


# BACKUP SYSTEMATIC MATCHING

#dict_matched = {}
#dict_nmatched = {}
#for enseigne_qlmc, enseigne_fra, enseigne_fra_alt in ls_matching:
#  dict_matched[enseigne_qlmc], dict_nmatched[enseigne_qlmc] = [[],[]], [[], []]
#  for row_ind, row in df_qlmc_stores[(df_qlmc_stores['Enseigne'] == enseigne_qlmc)].iterrows():
#    insee_code = row['INSEE_Code']
#    df_city_stores = df_fra_stores[(df_fra_stores['insee_code'] == insee_code) &\
#                                   (df_fra_stores['type'] == enseigne_fra)]
#    if len(df_city_stores) == 1:
#      dict_matched[enseigne_qlmc][0].append([row['Enseigne'],
#                                             row['Commune'], 
#                                             df_city_stores['name']])
#    else:
#      dict_nmatched[enseigne_qlmc][0].append([row['Enseigne'],
#                                              row['Commune'],
#                                              row['INSEE_Code'],
#                                              df_city_stores])
#    df_city_stores_alt = df_fra_stores[(df_fra_stores['insee_code'] == insee_code) &\
#                                       (df_fra_stores['type_alt'] == enseigne_fra_alt)]
#    if len(df_city_stores_alt) == 1:
#      dict_matched[enseigne_qlmc][1].append([row['Enseigne'],
#                                             row['Commune'], 
#                                             df_city_stores_alt['name']])
#    else:
#      dict_nmatched[enseigne_qlmc][1].append([row['Enseigne'],
#                                              row['Commune'],
#                                              row['INSEE_Code'],
#                                              df_city_stores_alt])
#
      
#print '\nSuccesful Matching'
#for x in ls_matching:
#	print x[0], len(dict_matched[x[0]][0]), len(dict_matched[x[0]][1])
#
#print '\nNo match or ambiguity'
#for x in ls_matching:
#	print x[0], len(dict_nmatched[x[0]][0]), len(dict_nmatched[x[0]][1])
#
## todo: iterate over each enseigne_qlmc: first result then second
## todo: check how can be improved... + closed stores / changes in brand
