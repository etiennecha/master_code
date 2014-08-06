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

path_dir_source_lsa = os.path.join(path_dir_qlmc, 'data_source', 'data_lsa_xls')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))
fra_stores = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'fra_stores.h5'))

# df_fra_stores = fra_stores['df_fra_stores_current']
df_qlmc_stores = qlmc_data['df_qlmc_stores']

date_ind = 0

# STORE BRAND/TYPE IN EACH DF: NEED TO HARMONIZE

## types in df_qlmc_stores
#print df_qlmc_stores['Enseigne'].value_counts()
print df_qlmc_stores['Enseigne'][df_qlmc_stores['P'] == date_ind].value_counts()

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

# LSA data: no ardt insee codes... hence regroup in qlmc
dict_large_cities = {'13055' : ['%s' %elt for elt in range(13201, 13217)], # Marseille
                     '69123' : ['%s' %elt for elt in range(69381, 69390)], # Lyon
                     '75056' : ['%s' %elt for elt in range(75101, 75121)]} # Paris
dict_large_cities_alt = dict([(v, k) for k, ls_v in dict_large_cities.items()\
                                for v in ls_v])
# not sure want to keep that one then?
df_qlmc_stores['INSEE_Code'] = df_qlmc_stores['INSEE_Code'].apply(\
                                 lambda x: dict_large_cities_alt[x]\
                                   if x in dict_large_cities_alt else x)

# types in df_lsa_all / df_lsa
# need to work with _no1900 at CREST for now (older versions of numpy/pandas/xlrd...?)
#df_lsa_stores_all = pd.read_excel(os.path.join(path_dir_source_lsa,
#                                               '2014-07-30-export_CNRS.xlsx'),
#                                  sheetname = 'Feuil1')
df_lsa_stores_all = pd.read_excel(os.path.join(path_dir_built_csv,
                                               'LSA_enriched.xlsx'),
                                  sheetname = 'Sheet1')

# Exclude drive and hard discount for matching
df_lsa_stores = df_lsa_stores_all[(df_lsa_stores_all['Type'] == 'H') |\
                                  (df_lsa_stores_all['Type'] == 'S') |\
                                  (df_lsa_stores_all['Type'] == 'MP')]

# Enseignes in LSA
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

qlmc_date = ls_qlmc_dates[date_ind]
print df_lsa_stores[qlmc_date].value_counts().to_string()

ls_disp_2 = [u'Ident', u'Enseigne', u'ADRESSE1', u'Ville', 'Code INSEE',
             u'DATE ouv', u'DATE chg enseigne', 'Ex enseigne']

print df_lsa_stores[ls_disp_2][df_lsa_stores[qlmc_date] == 'CARREFOUR MARKET'][0:30].to_string()

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
                             u'GEANT CASINO' : u'GEANT CASINO',
                             u'HYPER CASINO': u'GEANT CASINO',
                             u'CASINO' : u'GEANT CASINO',
                             u'GEANT' : u'GEANT CASINO',
                             u'CENTRE E.LECLERC' : u'LECLERC',
                             u'LECLERC EXPRESS' : u'LECLERC'}

df_lsa_stores['type'] = df_lsa_stores[qlmc_date]
df_lsa_stores['insee_code'] = df_lsa_stores['Code INSEE']

df_lsa_stores['type_alt'] = df_lsa_stores['type'].apply(\
                              lambda x: dict_lsa_stores_alt_brand[x]\
                                          if dict_lsa_stores_alt_brand.get(x)\
                                          else x)

ls_matching = [[u'INTERMARCHE', u'INTERMARCHE', u'INTERMARCHE'],
               [u'AUCHAN', u'AUCHAN', u'AUCHAN'],
               [u'E.LECLERC', u'CENTRE E.LECLERC', u'LERCLERC'],
               [u'CARREFOUR', u'CARREFOUR', u'CARREFOUR'],
               [u'CORA', u'CORA', u'CORA'],
               [u'CHAMPION', u'CHAMPION', u'CARREFOUR MARKET'], # unsure...
               [u'GEANT', u'GEANT CASINO', u'GEANT CASINO'],
               [u'SYSTEME U', 'SUPER U', 'SYSTEME U']]

#ls_matching = [[u'INTERMARCHE', u'INTERMARCHE', u'INTERMARCHE'],
#               [u'AUCHAN', u'AUCHAN', u'AUCHAN'],
#               [u'SUPER U', 'SUPER U', u'SYSTEME U'],
#               [u'GEANT CASINO', u'GEANT CASINO', u'GEANT CASINO'],
#               [u'LECLERC', u'CENTRE E.LECLERC', u'LECLERC'],
#               [u'E.LECLERC', u'CENTRE E.LECLERC', u'LERCLERC'],
#               [u'CARREFOUR MARKET', u'CARREFOUR MARKET', u'CARREFOUR MARKET'],
#               [u'CARREFOUR', u'CARREFOUR', u'CARREFOUR'],
#               [u'CORA', u'CORA', u'CORA'],
#               [u'CHAMPION', u'CHAMPION', u'CARREFOUR MARKET'], # unsure...
#               [u'CENTRE E. LECLERC', u'CENTRE E.LECLERC', u'LECLERC'],
#               [u'GEANT', u'GEANT CASINO', u'GEANT CASINO'],
#               [u'HYPER CHAMPION', u'CARREFOUR', u'CARREFOUR'],
#               [u'GEANT DISCOUNT', u'HYPER CASINO', u'GEANT CASINO'],
#               [u'LECLERC EXPRESS', u'LECLERC EXPRESS', u'LECLERC'],
#               [u'U EXPRESS', u'U EXPRESS', u'SYSTEME U'],
#               [u'SYSTEME U', 'SUPER U', 'SYSTEME U'],
#               [u'MARCHE U', u'MARCHE U', u'SYSTEME U'],
#               [u'CENTRE LECLERC', u'CENTRE E.LECLERC', u'LECLERC'],
#               [u'CARREFOUR CITY', u'CARREFOUR CITY', u'CARREFOUR MARKET'],
#               [u'CARREFOUR PLANET', u'CARREFOUR', u'CARREFOUR'],
#               [u'GEANT DISCOUNT', u'HYPER CASINO', u'GEANT CASINO'],
#               [u'HYPER U', u'HYPER U', 'SYSTEME U']]

## SYSTEMATIC MATCHING

ls_matched_stores = []
for enseigne_qlmc, enseigne_fra, enseigne_fra_alt in ls_matching:
  for row_ind, row in df_qlmc_stores[(df_qlmc_stores['Enseigne'] == enseigne_qlmc) &\
                                     (df_qlmc_stores['P'] == date_ind)].iterrows():
    insee_code = row['INSEE_Code']
    df_city_stores = df_lsa_stores[(df_lsa_stores['insee_code'] == insee_code) &\
                                   (df_lsa_stores['type'] == enseigne_fra)]
    if len(df_city_stores) == 1:
      ls_matched_stores.append((int(row['P']),
                                row['Enseigne'],
                                row['Commune'],
                                df_city_stores.iloc[0]['Ident'],
                                'direct'))
    elif len(df_city_stores) == 0:
      df_city_stores_alt = df_lsa_stores[(df_lsa_stores['insee_code'] == insee_code) &\
                                         (df_lsa_stores['type_alt'] == enseigne_fra_alt)]
      if len(df_city_stores_alt) == 1:
        ls_matched_stores.append((int(row['P']),
                                  row['Enseigne'],
                                  row['Commune'],
                                  df_city_stores_alt.iloc[0]['Ident'],
                                  'indirect'))
      elif len(df_city_stores_alt) == 0:
        ls_matched_stores.append((int(row['P']),
                                  row['Enseigne'],
                                  row['Commune'],
                                  None,
                                  'aucun'))
df_matched = pd.DataFrame(ls_matched_stores,
                          columns = ['P', 'Enseigne', 'Commune', 'ind_lsa_stores', 'Q'])

df_qlmc_stores_ma = pd.merge(df_matched, df_qlmc_stores,
                             on = ['P', 'Enseigne', 'Commune'],
                             how = 'right')

## Disambiguiation: big communes
#df_unmatched = df_qlmc_stores_ma[pd.isnull(df_qlmc_stores_ma['ind_lsa_stores'])]
#print df_unmatched['INSEE_Code'].value_counts()[0:10]
#print df_qlmc_stores_ma[df_qlmc_stores_ma['INSEE_Code'] == u'49007'].to_string()
#
#ls_df_toextract = []
#for insee_code in df_unmatched['INSEE_Code'].value_counts()[0:30].index:
#  ls_df_toextract.append(df_qlmc_stores_ma[df_qlmc_stores_ma['INSEE_Code'] == insee_code])
#df_to_extract = pd.concat(ls_df_toextract)
#df_to_extract.sort(columns=['INSEE_Code', 'Enseigne', 'Commune'], inplace = True)
#print df_to_extract.to_string()
#
##ls_rows_fix_ms = []
##for ls_store_fix in ls_fix_ms:
##  for magasin_libelle in ls_store_fix[2]:
##    ls_rows_fix_ms.append(ls_store_fix[0] + ls_store_fix[1] + [magasin_libelle])
##ls_columns = ['ind_lsa', 'ind_lsa_stores_2', 'street_lsa_stores', 'Enseigne', 'Commune']
##df_fix_ms = pd.DataFrame(ls_rows_fix_ms, columns = ls_columns)
#
#ls_columns_fix_ms = ['P', 'Enseigne', 'Commune', 'INSEE_Code',
#                     'ind_fra_stores', 'ind_lsa', 'ind_fra_stores_2', 'street_fra_stores']
#ls_fix_ms = dec_json(os.path.join(path_dir_built_json, u'ls_fix_ms'))
#df_fix_ms = pd.DataFrame(ls_fix_ms, columns = ls_columns_fix_ms)
## INSEE_Code: pbm when reading from excel (read as number) hence must drop
#df_fix_ms.drop(['ind_fra_stores', 'INSEE_Code'], axis = 1, inplace = True)
#
#df_to_extract = pd.merge(df_fix_ms, df_to_extract, on=['P', 'Enseigne', 'Commune'], how='right')
#df_to_extract.sort(columns = ['INSEE_Code', 'Enseigne', 'P', 'Commune'], inplace = True)
#ls_extract_disp = ['P', 'Enseigne', 'Commune', 'INSEE_Code',
#                   'ind_fra_stores', 'ind_lsa', 'ind_fra_stores_2', 'street_fra_stores']
#
## READ MATCHED STORES FROM EXCEL FILE
#
#df_read_fix_ms = pd.read_excel(os.path.join(path_dir_built_excel, 'fix_store_matching.xlsx'),
#                               sheetname = 'Sheet1')
#df_read_fix_ms_fi = df_read_fix_ms[(~pd.isnull(df_read_fix_ms['ind_lsa'])) |
#                                   (~pd.isnull(df_read_fix_ms['ind_fra_stores_2'])) |
#                                   (~pd.isnull(df_read_fix_ms['street_fra_stores']))]
## df_read_fix_ms_fi['P'] = df_read_fix_ms_fi['P'].apply(lambda x: int(x))
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
#
## UPDATE JSON FILE WITH MATCHED STORES
#
## ls_fix_ms = dec_json(os.path.join(path_dir_built_json, u'ls_fix_ms'))
#ls_fix_ms = []
## NB: no equality when nan (even in list)
#ls_fix_ms_check = [x[0:3] for x in ls_fix_ms]
### overwrite forbidden (for now?)
### todo: check unexpected duplicates => all hand written field as they should never be nan
#ls_fix_ms += [x for x in ls_read_fix_ms if x[0:3] not in ls_fix_ms_check]
## enc_json(ls_fix_ms, os.path.join(path_dir_built_json, u'ls_fix_ms'))
#
#
### TODO: RE-GENERATE EXCEL FILE WITH ALL MATCHED STORES
###http://stackoverflow.com/questions/20219254/
###how-to-write-to-an-existing-excel-file-without-overwriting-data
### pip install openpyxl==1.8.6
##writer = pd.ExcelWriter(os.path.join(path_dir_built_excel, 'fix_store_matching.xlsx'))
##df_to_extract[ls_extract_disp].to_excel(writer, index=False)
##writer.close()
#
## to be applied before corrections
#ls_fix_ms_2 = [[u'10', u'GEANT CASINO', u'ANGERS', 'ANGERS LA ROSERAIE'],   #todo: check
#               [u'2' , u'GEANT CASINO', u'CARCASSONNE', u'CARCASSONE CC SALVAZA']] # todo: check
#
## Output for merger with price file
##df_qlmc_stores_matched.to_csv(os.path.join(path_dir_built_csv, 'df_qlmc_stores_matched.csv'),
##                              float_format='%.0f', encoding='utf-8', index=False)
#
## OUTPUT RESULT FROM MATCHING (i.e. corr)
## assume df_read_fix_ms_fi contains all ad hoc matching
#df_read_fix_ms_fi.rename(columns={'ind_lsa' : 'ind_lsa_adhoc'}, inplace = True)
#df_final = pd.merge(df_read_fix_ms_fi[['P', 'Enseigne', 'Commune', 'ind_lsa_adhoc']] ,
#                    df_qlmc_stores_ma, on = ['P', 'Enseigne', 'Commune'],
#                    how = 'right')
#df_final['Q'][~pd.isnull(df_final['ind_lsa_adhoc'])] = 'manuel'
#df_final['ind_lsa_stores'][~pd.isnull(df_final['ind_lsa_adhoc'])] = df_final['ind_lsa_adhoc']
#df_final['Q'][pd.isnull(df_final['Q'])] = 'ambigu' # check 
#df_final.drop(['ind_lsa_adhoc'], axis = 1, inplace = True)
#df_final.sort(columns=['P', 'INSEE_Code', 'Enseigne'], inplace = True)
#
#writer = pd.ExcelWriter(os.path.join(path_dir_built_csv, 'matching_qlmc_lsa.xlsx'))
#df_final.to_excel(writer, index = False)
#writer.close()
