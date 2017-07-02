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

path_source = os.path.join(path_data,
                           'data_supermarkets',
                           'data_source',
                           'data_qlmc_2007-12')

path_source_csv = os.path.join(path_source,
                               'data_csv')

path_source_json = os.path.join(path_source,
                                'data_json')

path_source_excel = os.path.join(path_source,
                                 'data_excel')

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

# #############
# LOAD DF QLMC
# #############

df_qlmc_stores = pd.read_csv(os.path.join(path_source_csv,
                                          'df_stores_w_municipality.csv'),
                             dtype = {'period' : str,
                                      'c_qlmc_departement': str,
                                      'c_insee' : str},
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


# ############
# LOAD DF LSA
# ############

df_lsa = pd.read_csv(os.path.join(path_built_lsa_csv,
                                  'df_lsa_for_qlmc.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

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
#lsds = [u'id_lsa', u'Enseigne', u'Adresse1', u'Ville', 'C_INSEE',
#         u'Date_Ouv', u'Date_Chg_Enseigne', 'Ex_Enseigne']
#print df_lsa[lsd0][df_lsa['Enseigne_Alt_{:s}'.format(qlmc_date)] ==\
#                     'CARREFOUR MARKET'][0:30].to_string()

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

ls_matching = [[u'INTERMARCHE', u'XXX', u'INTERMARCHE'], # give up direct matching (first period..)
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
  df_lsa['ea_temp'] = df_lsa['enseigne_alt_{:s}'.format(qlmc_date)]
  
  df_lsa['ea_temp_2'] = df_lsa['ea_temp'].apply(\
                                lambda x: dict_lsa_stores_alt_brand[x]\
                                            if dict_lsa_stores_alt_brand.get(x)\
                                            else x)
  ls_matched_stores = []
  for enseigne_qlmc, enseigne_fra, enseigne_fra_alt in ls_matching:
    for row_ind, row in df_qlmc_stores[(df_qlmc_stores['store_chain'] == enseigne_qlmc) &\
                                       (df_qlmc_stores['period'] == '{:d}'.format(date_ind))]\
                                          .iterrows():
      insee_code = row['c_insee']
      df_city_stores = df_lsa[(df_lsa['c_insee_ardt'] == insee_code) &\
                              (df_lsa['ea_temp'] == enseigne_fra)]
      if len(df_city_stores) == 1:
        ls_matched_stores.append((row['period'],
                                  row['store_chain'],
                                  row['store_municipality'],
                                  df_city_stores.iloc[0]['id_lsa'],
                                  'direct'))
      elif len(df_city_stores) == 0:
        df_city_stores_alt = df_lsa[(df_lsa['c_insee_ardt'] == insee_code) &\
                                    (df_lsa['ea_temp_2'] == enseigne_fra_alt)]
        if len(df_city_stores_alt) == 1:
          ls_matched_stores.append((row['period'],
                                    row['store_chain'],
                                    row['store_municipality'],
                                    df_city_stores_alt.iloc[0]['id_lsa'],
                                    'indirect'))
        elif len(df_city_stores_alt) == 0:
          ls_matched_stores.append((row['period'],
                                    row['store_chain'],
                                    row['store_municipality'],
                                    None,
                                    'aucun'))
  ls_ls_matched_stores.append(ls_matched_stores)

ls_matched_stores = [ms for ls_ms in ls_ls_matched_stores for ms in ls_ms]

df_matching = pd.DataFrame(ls_matched_stores,
                           columns = ['period',
                                      'store_chain',
                                      'store_municipality',
                                      'id_lsa',
                                      'matching_quality'])

df_qlmc_stores_ma = pd.merge(df_matching,
                             df_qlmc_stores,
                             on = ['period', 'store_chain', 'store_municipality'],
                             how = 'right')

# READ MATCHED STORES FROM CSV FILE AND UPDATE FIX
file_fix_matching = 'fix_store_matching.csv'
df_read_fix_ms = pd.read_csv(os.path.join(path_source_excel,
                                          file_fix_matching),
                               sep = ';',
                               dtype = {'period' : str,
                                        'c_insee' : str,
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
df_stores = pd.merge(df_read_fix_ms[['period', 'store_chain', 'store_municipality',
                                    'id_lsa_adhoc',
                                    'id_fra_stores', 'id_fra_stores_2',
                                    'street_fra_stores']],
                     df_qlmc_stores_ma,
                     on = ['period', 'store_chain', 'store_municipality'],
                     how = 'right')

# priority given to hand info
df_stores.loc[~pd.isnull(df_stores['id_lsa_adhoc']),
              'matching_quality'] = 'manuel'

df_stores.loc[~pd.isnull(df_stores['id_lsa_adhoc']),
             'id_lsa'] = df_stores['id_lsa_adhoc']

df_stores.loc[pd.isnull(df_stores['matching_quality']),
              'matching_quality'] = 'ambigu' # check

df_stores.drop(['id_lsa_adhoc'], axis = 1, inplace = True)
df_stores.sort(columns=['period', 'c_insee', 'store_chain'], inplace = True)

# CHECK FOR DUPLICATES IN MATCHING
df_matched = df_stores[~pd.isnull(df_stores['id_lsa'])]
df_dup = df_matched[(df_matched.duplicated(subset = ['period', 'id_lsa'],
                                           take_last = True)) |\
                    (df_matched.duplicated(subset = ['period', 'id_lsa'],
                                           take_last = False))]
print '\nNb id_lsa associated with two different stores: {:d}'.format(len(df_dup))
print '\nInspect duplicates:'
ls_dup_disp = ['period', 'store_chain', 'store_municipality', 'c_insee', 'id_lsa']
print df_dup[ls_dup_disp].to_string()

# OUTPUT NO MATCH (INCLUDING MANUAL INPUT) FOR FURTHER INVESTIGATIONS
df_unmatched = df_stores[(pd.isnull(df_stores['id_lsa'])) |\
                         (df_stores['matching_quality'] == 'manuel')].copy()
# Cannot accomodate null c_insee with following method
# Anyway.. if insee code could not be found...?
df_unmatched = df_unmatched[~df_unmatched['c_insee'].isnull()]
df_unmatched['nb_same_ic'] =\
  df_unmatched.groupby('c_insee').c_insee.transform('size')
df_unmatched.sort(['nb_same_ic', 'c_insee', 'store', 'period'],
                  ascending = False,
                  inplace = True)
ls_unmatched_disp = ['period', 'store_chain', 'store_municipality',
                     'street_fra_stores', 'id_fra_stores', 'id_fra_stores_2',
                     'id_lsa', 'matching_quality', 'c_insee', 'nb_same_ic',
                     'qlmc_surface']

print u'\nNb unmatched period/store (before): {:d}'.format(len(df_unmatched))
print u'\nNb manually matched: {:d}'.format(\
        len(df_unmatched[~df_unmatched['id_lsa'].isnull()]))
print '\nInspect unmatched:'
print df_unmatched[ls_unmatched_disp][0:30].to_string()

# ######
# OUTPUT
# ######

# STORES NOT FOUND: STANDARD EXCEL CSV FOR MANUAL MATCHING
df_unmatched[ls_unmatched_disp].to_csv(os.path.join(path_source_excel,
                                                    'fix_store_matching.csv'),
                                       index = False,
                                       encoding = 'latin-1',
                                       sep = ';',
                                       quoting = 3) # no impact, cannot have trailing 0s

# MATCHED STORES: CSV
df_stores['store']= df_stores['store_chain'] + u' ' + df_stores['store_municipality']
df_stores.to_csv(os.path.join(path_source_csv,
                             'df_stores_w_municipality_and_lsa_id.csv'),
                index = False,
                encoding = 'utf-8')
