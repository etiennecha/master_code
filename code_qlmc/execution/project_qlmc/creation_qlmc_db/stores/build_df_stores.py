#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
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
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')
path_dir_built_excel = os.path.join(path_dir_qlmc, 'data_built' , 'data_excel')

# #############
# LOAD DF QLMC
# #############

df_qlmc_stores = pd.read_csv(os.path.join(path_dir_built_csv,
                                      'df_qlmc_stores_raw.csv'),
                             dtype = {'P' : str,
                                      'QLMC_Dpt': str,
                                      'INSEE_ZIP': str,
                                      'INSEE_Dpt' : str,
                                      'INSEE_Code' : str},
                             encoding = 'UTF-8')

### types in df_qlmc_stores
##print df_qlmc_stores['Enseigne'].value_counts()
#date_ind = 1
#print df_qlmc_stores['Enseigne'][df_qlmc_stores['P'] == date_ind].value_counts()

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

## DEPRECATED: get rid of ardts in large cities in LSA
#dict_large_cities = {'13055' : ['%s' %elt for elt in range(13201, 13217)], # Marseille
#                     '69123' : ['%s' %elt for elt in range(69381, 69390)], # Lyon
#                     '75056' : ['%s' %elt for elt in range(75101, 75121)]} # Paris
#dict_large_cities_alt = dict([(v, k) for k, ls_v in dict_large_cities.items()\
#                                for v in ls_v])
## not sure want to keep that one then?
#df_qlmc_stores['INSEE_Code'] = df_qlmc_stores['INSEE_Code'].apply(\
#                                 lambda x: dict_large_cities_alt[x]\
#                                   if x in dict_large_cities_alt else x)

# ############
# LOAD DF LSA
# ############

df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_lsa_for_qlmc.csv'),
                     dtype = {'Ident': str,
                              'Code INSEE' : str,
                              'Code INSEE ardt' : str,
                              'Siret' : str},
                     parse_dates = [u'DATE ouv',
                                    u'DATE ferm',
                                    u'DATE réouv',
                                    u'DATE chg enseigne',
                                    u'DATE chgt surf'],
                     encoding = 'UTF-8')

## todo: fix and drop
#if u'Unnamed: 0' in df_lsa.columns:
#  df_lsa.drop(u'Unnamed: 0', axis = 1, inplace = True)

# Dates in LSA for matching by period
ls_qlmc_dates = ['2007-05',
                 '2007-08',
                 '2008-01',
                 '2008-04',
                 '2009-03',
                 '2009-09',
                 '2010-03',
                 '2010-10',
                 '2011-01',
                 '2011-04',
                 '2011-10',
                 '2012-01',
                 '2012-06']

#qlmc_date = ls_qlmc_dates[date_ind]
#print df_lsa[qlmc_date].value_counts().to_string()
#ls_disp_2 = [u'Ident', u'Enseigne', u'ADRESSE1', u'Ville', 'Code INSEE',
#             u'DATE ouv', u'DATE chg enseigne', 'Ex enseigne']
#print df_lsa[ls_disp_2][df_lsa[qlmc_date] == 'CARREFOUR MARKET'][0:30].to_string()

# ##########
# MATCHING
# ##########

dict_lsa_stores_alt_brand = {u'INTERMARCHE SUPER': u'INTERMARCHE',
                             u'INTERMARCHE CONTACT': u'INTERMARCHE',
                             u'INTERMARCHE HYPER' : u'INTERMARCHE',
                             u'INTERMARCHE EXPRESS': u'INTERMARCHE',
                             u'RELAIS DES MOUSQUETAIRES' : u'INTERMARCHE',
                             u'SUPER U' : u'SYSTEME U',
                             u'U EXPRESS': u'SYSTEME U',
                             u'HYPER U' : u'SYSTEME U',
                             u'MARCHE U' : u'SYSTEME U',
                             u'CARREFOUR CITY' : u'CARREFOUR MARKET',
                             u'MARKET' : u'CARREFOUR MARKET',
                             u'SHOPI' : u'CARREFOUR MARKET',
                             u'CARREFOUR EXPRESS' : u'CARREFOUR MARKET',
                             u'CHAMPION': u'CARREFOUR MARKET',
                             u'GEANT CASINO' : u'GEANT CASINO',
                             u'HYPER CASINO': u'GEANT CASINO',
                             # u'CASINO' : u'GEANT CASINO',
                             u'GEANT' : u'GEANT CASINO',
                             u'CENTRE E.LECLERC' : u'LECLERC',
                             u'LECLERC EXPRESS' : u'LECLERC'}

ls_matching = [[u'INTERMARCHE', u'XXX', u'INTERMARCHE'], # give up direct matching (first period...)
               [u'INTERMARCHE SUPER', u'INTERMARCHE SUPER', u'INTERMARCHE'],
               [u'INTERMARCHE HYPER', u'INTERMARCHE HYPER', u'INTERMARCHE'],
               [u'AUCHAN', u'AUCHAN', u'AUCHAN'],
               [u'LECLERC', u'CENTRE E.LECLERC', u'LECLERC'],
               [u'E.LECLERC', u'CENTRE E.LECLERC', u'LERCLERC'],
               [u'E. LECLERC', u'CENTRE E.LECLERC', u'LERCLERC'],
               [u'CENTRE LECLERC', u'CENTRE E.LECLERC', u'LECLERC'],
               [u'CENTRE E. LECLERC', u'CENTRE E.LECLERC', u'LECLERC'],
               [u'CARREFOUR', u'CARREFOUR', u'CARREFOUR'],
               [u'CARREFOUR MARKET', u'CARREFOUR MARKET', u'CARREFOUR MARKET'],
               [u'CARREFOUR CITY', u'CARREFOUR CITY', u'CARREFOUR MARKET'],
               [u'CARREFOUR CONTACT', u'CARREFOUR CONTACT', u'CARREFOUR MARKET'],
               [u'CARREFOUR PLANET', u'CARREFOUR', u'CARREFOUR MARKET'], # unsure
               [u'HYPER CHAMPION', u'CARREFOUR', u'CARREFOUR MARKET'], # unsure
               [u'CHAMPION', u'XXX', u'CARREFOUR MARKET'], # give up direct matching...
               [u'CORA', u'CORA', u'CORA'],
               [u'GEANT', u'GEANT', u'GEANT CASINO'], # ok if beginning only?
               [u'GEANT CASINO', u'GEANT CASINO', u'GEANT CASINO'], # avoid first stage (middle)?
               [u'GEANT DISCOUNT', u'HYPER CASINO', u'GEANT CASINO'], # unsure
               [u'HYPER U', u'HYPER U', 'SYSTEME U'],
               [u'SUPER U', 'SUPER U', u'SYSTEME U'],
               [u'SYSTEME U', 'SUPER U', 'SYSTEME U'],
               [u'U EXPRESS', u'U EXPRESS', u'SYSTEME U'],
               [u'MARCHE U', u'MARCHE U', u'SYSTEME U']]

ls_ls_matched_stores = []
for date_ind, qlmc_date in enumerate(ls_qlmc_dates):
  df_lsa['type'] = df_lsa[qlmc_date]
  
  df_lsa['type_alt'] = df_lsa['type'].apply(\
                                lambda x: dict_lsa_stores_alt_brand[x]\
                                            if dict_lsa_stores_alt_brand.get(x)\
                                            else x)
  ls_matched_stores = []
  for enseigne_qlmc, enseigne_fra, enseigne_fra_alt in ls_matching:
    for row_ind, row in df_qlmc_stores[(df_qlmc_stores['Enseigne'] == enseigne_qlmc) &\
                                       (df_qlmc_stores['P'] == '{:d}'.format(date_ind))].iterrows():
      insee_code = row['INSEE_Code']
      df_city_stores = df_lsa[(df_lsa['Code INSEE ardt'] == insee_code) &\
                              (df_lsa['type'] == enseigne_fra)]
      if len(df_city_stores) == 1:
        ls_matched_stores.append((row['P'],
                                  row['Enseigne'],
                                  row['Commune'],
                                  df_city_stores.iloc[0]['Ident'],
                                  'direct'))
      elif len(df_city_stores) == 0:
        df_city_stores_alt = df_lsa[(df_lsa['Code INSEE ardt'] == insee_code) &\
                                    (df_lsa['type_alt'] == enseigne_fra_alt)]
        if len(df_city_stores_alt) == 1:
          ls_matched_stores.append((row['P'],
                                    row['Enseigne'],
                                    row['Commune'],
                                    df_city_stores_alt.iloc[0]['Ident'],
                                    'indirect'))
        elif len(df_city_stores_alt) == 0:
          ls_matched_stores.append((row['P'],
                                    row['Enseigne'],
                                    row['Commune'],
                                    None,
                                    'aucun'))
  ls_ls_matched_stores.append(ls_matched_stores)

ls_matched_stores = [ms for ls_ms in ls_ls_matched_stores for ms in ls_ms]

df_matching = pd.DataFrame(ls_matched_stores,
                          columns = ['P', 'Enseigne', 'Commune', 'id_lsa', 'Q'])

df_qlmc_stores_ma = pd.merge(df_matching, df_qlmc_stores,
                             on = ['P', 'Enseigne', 'Commune'],
                             how = 'right')



# READ MATCHED STORES FROM CSV FILE AND UPDATE FIX
df_read_fix_ms = pd.read_csv(os.path.join(path_dir_built_excel,
                                          'fix_store_matching.csv'),
                               sep = ';',
                               dtype = {'P' : str,
                                        'INSEE_Code' : str,
                                        'id_fra_stores' : str,
                                        'id_lsa' : str,
                                        'id_fra_stores_2' : str},
                               encoding = 'latin-1')
# keep only those with some added info
df_read_fix_ms = df_read_fix_ms[(~pd.isnull(df_read_fix_ms['id_lsa'])) |
                                (~pd.isnull(df_read_fix_ms['id_fra_stores_2'])) |
                                (~pd.isnull(df_read_fix_ms['street_fra_stores']))].copy()
# df_read_fix_ms contains all ad hoc matching
df_read_fix_ms.rename(columns={'id_lsa' : 'id_lsa_adhoc'}, inplace = True)
df_stores = pd.merge(df_read_fix_ms[['P', 'Enseigne', 'Commune',
                                    'id_lsa_adhoc', 'id_fra_stores', 'id_fra_stores_2',
                                    'street_fra_stores']],
                    df_qlmc_stores_ma, on = ['P', 'Enseigne', 'Commune'],
                    how = 'right')
# priority given to hand info
df_stores.loc[~pd.isnull(df_stores['id_lsa_adhoc']), 'Q'] = 'manuel'

df_stores.loc[~pd.isnull(df_stores['id_lsa_adhoc']),
             'id_lsa'] = df_stores['id_lsa_adhoc']

df_stores.loc[pd.isnull(df_stores['Q']), 'Q'] = 'ambigu' # check

df_stores.drop(['id_lsa_adhoc'], axis = 1, inplace = True)
df_stores.sort(columns=['P', 'INSEE_Code', 'Enseigne'], inplace = True)

# INSPECT NO MATCH
df_unmatched = df_stores[pd.isnull(df_stores['id_lsa'])]
print '\nTop insee areas in terms of no match'
print df_unmatched['INSEE_Code'].value_counts()[0:10]
print '\nINSEE area with code 49007:'
ls_store_disp = ['P', 'Magasin', 'INSEE_Code', 'Commune', 'QLMC_Surface', 'id_lsa', 'Q']
print df_stores[ls_store_disp][df_stores['INSEE_Code'] == u'49007'].to_string()

# DIPLAY MAIN NO MATCH MUNICIPALITIES
ls_df_toextract = []
for insee_code in df_unmatched['INSEE_Code'].value_counts()[0:30].index:
  ls_df_toextract.append(df_stores[df_stores['INSEE_Code'] == insee_code])
df_to_extract = pd.concat(ls_df_toextract)
df_to_extract.sort(columns=['INSEE_Code', 'Enseigne', 'Commune'], inplace = True)
print df_to_extract[ls_store_disp].to_string()

# INSPECT MATCHES: DUPLICATES?

df_matched = df_stores[~pd.isnull(df_stores['id_lsa'])]
print '\nNb id_lsa associated with two different stores:',\
       len(df_matched[df_matched.duplicated(subset = ['P', 'id_lsa'])])
ls_pbm_lsa_ids = df_matched['id_lsa'][df_matched.duplicated(subset = ['P', 'id_lsa'])].values
print 'Inspect concerned stores:'
ls_final_disp = ['P', 'Enseigne', 'Commune', 'INSEE_Code', 'id_lsa']
print df_matched[ls_final_disp][df_matched['id_lsa'].isin(ls_pbm_lsa_ids)]

# TODO: OUTPUT NO MATCH FOR POTENTIAL HAND WRITTEN UPDATES

## OUTPUT
#
## HDF (abandon?)
#path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')
#qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))
#qlmc_data['df_qlmc_stores'] = df_stores
#qlmc_data.close()
#
## CSV
#df_stores.to_csv(os.path.join(path_dir_built_csv,
#                             'df_qlmc_stores.csv'),
#                index = False,
#                encoding = 'UTF-8')



# DEPREACTED

# ADD QLMC NO MATCH TO BE EXAMINED (MOVE ?)

#df_to_extract = pd.merge(df_fix_ms, df_to_extract, on=['P', 'Enseigne', 'Commune'], how='right')
#df_to_extract.sort(columns = ['INSEE_Code', 'Enseigne', 'P', 'Commune'], inplace = True)
#ls_extract_disp = ['P', 'Enseigne', 'Commune', 'INSEE_Code',
#                   'id_fra_stores', 'id_lsa', 'id_fra_stores_2', 'street_fra_stores']

# UPDATE JSON FILE WITH MATCHED STORES

## list for json
#ls_read_fix_ms = [list(x) for x in df_read_fix_ms.to_records(index=False)]
## NB: no equality when nan (even in list)
#ls_fix_ms_check = [x[0:3] for x in ls_fix_ms]
#ls_fix_ms += [x for x in ls_read_fix_ms if x[0:3] not in ls_fix_ms_check]
# enc_json(ls_fix_ms, os.path.join(path_dir_built_json, u'ls_fix_ms.json'))

## LOAD HAND WRITTEN LSA/QLMC MATCHES (JSON => DEPRECATE?)
#ls_columns_fix_ms = ['P', 'Enseigne', 'Commune', 'INSEE_Code',
#                     'id_fra_stores', 'id_lsa', 'id_fra_stores_2', 'street_fra_stores']
#ls_fix_ms = dec_json(os.path.join(path_dir_built_json, u'ls_fix_ms.json'))
#df_fix_ms = pd.DataFrame(ls_fix_ms, columns = ls_columns_fix_ms)
#df_fix_ms.drop(['id_fra_stores', 'INSEE_Code'], axis = 1, inplace = True)

## RE-GENERATE EXCEL FILE WITH ALL MATCHED STORES
##http://stackoverflow.com/questions/20219254/
##how-to-write-to-an-existing-excel-file-without-overwriting-data
## pip install openpyxl==1.8.6
#writer = pd.ExcelWriter(os.path.join(path_dir_built_excel, 'fix_store_matching.xlsx'))
#df_to_extract[ls_extract_disp].to_excel(writer, index=False)
#writer.close()

## to be applied before corrections
#ls_fix_ms_2 = [[u'10', u'GEANT CASINO', u'ANGERS', 'ANGERS LA ROSERAIE'],   #check
#               [u'2' , u'GEANT CASINO', u'CARCASSONNE', u'CARCASSONE CC SALVAZA']] #check

# Output for merger with price file
#df_qlmc_stores_matched.to_csv(os.path.join(path_dir_built_csv, 'df_qlmc_stores_matched.csv'),
#                              float_format='%.0f', encoding='utf-8', index=False)


## READ MANUAL LSA MATCHING BASED ON XLS FILE

#df_read_fix_ms = pd.read_excel(os.path.join(path_dir_built_excel, 'fix_store_matching.xlsx'),
#                               sheetname = 'Sheet1')
#df_read_fix_ms_fi = df_read_fix_ms[(~pd.isnull(df_read_fix_ms['id_lsa'])) |
#                                   (~pd.isnull(df_read_fix_ms['id_fra_stores_2'])) |
#                                   (~pd.isnull(df_read_fix_ms['street_fra_stores']))].copy()
##df_read_fix_ms_fi['P'] = df_read_fix_ms_fi['P'].apply(lambda x: int(x))
#ls_read_fix_ms = [list(x) for x in df_read_fix_ms_fi.to_records(index=False)]
#
#def get_as_str(some_number, missing = None):
#  # float are expected to be int or nan
#  if np.isnan(some_number):
#    return missing
#  else:
#    return u'{0:.0f}'.format(some_number)
#
#def get_cinsee_as_str(some_number):
#  cinsee = get_as_str(some_number)
#  if len(cinsee) == 5:
#    return cinsee
#  elif cinsee and len(cinsee) == 4:
#    return u'0' + cinsee
#  else:
#    print u'Can not convert', some_number
#    return None
#
#ls_read_fix_ms = [[int(x[0])] + x[1:3] + [get_cinsee_as_str(x[3])] +\
#                  map(get_as_str, x[4:7]) + x[7:8] for x in ls_read_fix_ms]
