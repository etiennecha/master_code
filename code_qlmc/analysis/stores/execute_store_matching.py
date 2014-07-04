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

ls_ls_tuple_stores = dec_json(os.path.join(path_dir_built_json, 'ls_ls_tuple_stores'))

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))
fra_stores = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'fra_stores.h5'))

df_fra_stores = fra_stores['df_fra_stores_current']
df_qlmc_stores = qlmc_data['df_qlmc_stores']

# todo: add adequate Brand/Type for matching in df_fra_stores
# lookup each qlmc_store in df_fra_stores based on INSEE Code and Brand/Type

# STORE BRAND/TYPE IN EACH DF: NEED TO HARMONIZE

# types in df_qlmc_stores
df_qlmc_stores['Enseigne'].value_counts()
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

# types in df_fra_stores
df_fra_stores['type'].value_counts()

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
df_fra_stores['type_alt'] = df_fra_stores['type'].apply(lambda x: dict_fra_stores_alt_brand[x]\
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

# PRELIMINARY MATCHING BY PERIOD

ls_matched = []
enseigne_qlmc, enseigne_fra = u'E.LECLERC', u'Leclerc' 
# enseigne_qlmc, enseigne_fra = u'AUCHAN', u'Auchan'
# enseigne_qlmc, enseigne_fra = u'CARREFOUR', u'Carrefour'
# enseigne_qlmc, enseigne_fra = u'SYSTEME U', u'Hyper U'
# enseigne_qlmc, enseigne_fra = u'SYSTEME U', u'Super U' # => NEED TO REGROUP
## Need to work with both... check disambiguation with prices (can we?)

for row_ind, row in df_qlmc_stores[(df_qlmc_stores['Enseigne'] == enseigne_qlmc) &\
                          (df_qlmc_stores['P'] == 0)].iterrows():
  insee_code = row['INSEE_Code']
  df_city_stores = df_fra_stores[(df_fra_stores['insee_code'] == insee_code) &\
                                 (df_fra_stores['type'] == enseigne_fra)]
  if len(df_city_stores) == 1:
    ls_matched.append([row['Enseigne'], row['Commune'], df_city_stores['name']])
  else:
    print '\n', row['Enseigne'], row['Commune'], row['INSEE_Code']
    print df_city_stores.to_string()

#print df_fra_stores[(df_fra_stores['type'] == 'Auchan') &\
#                    (df_fra_stores['zip'].str.slice(stop=2)=='59')].to_string()

# add Auchan La Seyne sur Mer: travaux...
# http://www.varmatin.com/la-seyne-sur-mer/le-futur-auchan-de-la-seyne-se-devoile.1490487.html
# add Auchan Montgeron Vigneux sur Seine: no idea why not in data

# PRELIMINARY MATCHING: ALL PERIODS
# Meant for specific enough brands found in both df

# Seems that I need to proceed via index to fix data (check)
print u"\nTo be fixed: insee code u'14225'"
print df_fra_stores['insee_code'][(df_fra_stores['type'] == u'Hyper U') &\
                                  (df_fra_stores['city'] == u'DIVES SUR MER') &\
                                  (df_fra_stores['street'] == u'Boulevard Maurice Thorez')]
df_fra_stores.ix[6715]['insee_code'] = '14225'

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

# SYSTEMATIC MATCHING
dict_matched = {}
dict_nmatched = {}
for enseigne_qlmc, enseigne_fra, enseigne_fra_alt in ls_matching:
  dict_matched[enseigne_qlmc], dict_nmatched[enseigne_qlmc] = [[],[]], [[], []]
  for row_ind, row in df_qlmc_stores[(df_qlmc_stores['Enseigne'] == enseigne_qlmc)].iterrows():
    insee_code = row['INSEE_Code']
    df_city_stores = df_fra_stores[(df_fra_stores['insee_code'] == insee_code) &\
                                   (df_fra_stores['type'] == enseigne_fra)]
    if len(df_city_stores) == 1:
      dict_matched[enseigne_qlmc][0].append([row['Enseigne'],
                                             row['Commune'], 
                                             df_city_stores['name']])
    else:
      dict_nmatched[enseigne_qlmc][0].append([row['Enseigne'],
                                              row['Commune'],
                                              row['INSEE_Code'],
                                              df_city_stores])
    df_city_stores_alt = df_fra_stores[(df_fra_stores['insee_code'] == insee_code) &\
                                       (df_fra_stores['type_alt'] == enseigne_fra_alt)]
    if len(df_city_stores_alt) == 1:
      dict_matched[enseigne_qlmc][1].append([row['Enseigne'],
                                             row['Commune'], 
                                             df_city_stores_alt['name']])
    else:
      dict_nmatched[enseigne_qlmc][1].append([row['Enseigne'],
                                              row['Commune'],
                                              row['INSEE_Code'],
                                              df_city_stores_alt])

print '\nSuccesful Matching'
for x in ls_matching:
	print x[0], len(dict_matched[x[0]][0]), len(dict_matched[x[0]][1])

print '\nNo match or ambiguity'
for x in ls_matching:
	print x[0], len(dict_nmatched[x[0]][0]), len(dict_nmatched[x[0]][1])

# todo: iterate over each enseigne_qlmc: first result then second
# todo: check how can be improved... + closed stores / changes in brand
