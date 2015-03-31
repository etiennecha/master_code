#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
from functions_string import *
import os, sys
import re
import json
import pandas as pd
from mpl_toolkits.basemap import Basemap
from matplotlib.collections import PatchCollection
from shapely.geometry import Point, Polygon, MultiPoint, MultiPolygon, shape
from shapely.prepared import prep
from descartes import PolygonPatch

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_qlmc_scraped = os.path.join(path_data,
                                  'data_qlmc',
                                  'data_source',
                                  'data_scraped')

path_csv = os.path.join(path_data,
                        'data_qlmc',
                        'data_built',
                        'data_csv')

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'qlmc_scraped',
                                     'df_stores.csv'),
                        encoding = 'utf-8')

df_lsa = pd.read_csv(os.path.join(path_csv,
                                  'df_lsa_active_fm_hsx.csv'),
                     encoding = 'UTF-8',
                     dtype = {'Code INSEE' : str,
                              'Code INSEE ardt' : str,
                              'Code postal' : str},
                     parse_dates = [u'DATE ouv', u'DATE ferm', u'DATE réouv'])

#df_lsa['point'] = df_lsa[['Longitude', 'Latitude']].apply(\
#                        lambda x: Point(m_fra(x[0], x[1])), axis = 1)

# DATA FOR MATCHING

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

ls_matching = [[u'LEC', u'LECLERC', u'LECLERC'],
               [u'ITM', u'XXX', u'INTERMARCHE'], # give up direct matching (first period...)
               [u'USM', 'SUPER U', 'SYSTEME U'],
               [u'CAR', u'CARREFOUR', 'CARREFOUR'],
               [u'CRM', u'CARREFOUR MARKET', u'CARREFOUR MARKET'],
               [u'AUC', u'AUCHAN', u'AUCHAN'],
               [u'GEA', u'GEANT', u'GEANT CASINO'], # GEANT vs. GEANT CASINO?
               [u'COR', u'CORA', u'CORA'],
               [u'SCA', u'CASINO', u'CASINO'], # check if CASINO only in LSA? (CASINO)
               [u'HSM', u'HYPER U', 'SYSTEME U'],
               [u'SIM', u'SIMPLY MARKET', u'SIMPLY MARKET'], # check if chain in LSA
               [u'MAT', u'SUPERMARCHE MATCH', u'SUPERMARCHE MATCH'], # check if chain in LSA
               [u'HCA', u'HYPER CASINO', u'GEANT CASINO'], # unsure (HYPER CASINO)
               [u'UEX', u'U EXPRESS', u'SYSTEME U'],
               [u'ATA', u'ATAC', u'ATAC'], # check if chain in LSA
               [u'CAS', u'CASINO', u'CASINO'], # check if CASINO only in LSA (CASINO)
               [u'UHM', u'HYPER U', u'SYSTEME U'],
               [u'MIG', u'MIGROS', u'MIGROS'], # check if chain in LSA
               [u'G20', u'G20', u'G20'], # check if chain in LSA
               [u'REC', u'RECORD', u'RECORD'], # check if chain in LSA
               [u'HAU', u'AUCHAN', u'AUCHAN']] # LES HALLES D AUCHAN?

df_lsa['Enseigne_matching'] = df_lsa['Enseigne'].apply(\
                                lambda x: dict_lsa_stores_alt_brand[x]\
                                            if dict_lsa_stores_alt_brand.get(x)\
                                            else x)

# MATCHING QLMC vs. LSA

ls_matched_stores = []
for enseigne_qlmc, enseigne_fra, enseigne_fra_alt in ls_matching:
  for row_ind, row in df_stores[(df_stores['store_chain'] == enseigne_qlmc)].iterrows():
    insee_code = row['ic']
    df_city_stores = df_lsa[(df_lsa['Code INSEE ardt'] == insee_code) &\
                            (df_lsa['Enseigne'] == enseigne_fra)]
    tup_store_info = tuple(row[['store_chain', 'store_id', 'store_city',
                                'ic_city', 'ic']].values)
    if len(df_city_stores) == 1:
      ls_matched_stores.append(tup_store_info +\
                               (df_city_stores.iloc[0]['Ident'],
                                enseigne_fra,
                                'direct'))
    elif len(df_city_stores) > 1:
      ls_matched_stores.append(tup_store_info +\
                               (None, enseigne_fra, 'ambiguous'))
    elif len(df_city_stores) == 0:
      df_city_stores_alt = df_lsa[(df_lsa['Code INSEE ardt'] == insee_code) &\
                                  (df_lsa['Enseigne_matching'] == enseigne_fra_alt)]
      if len(df_city_stores_alt) == 1:
        ls_matched_stores.append(tup_store_info +\
                                 (df_city_stores_alt.iloc[0]['Ident'],
                                  enseigne_fra_alt,
                                  'indirect'))
      elif len(df_city_stores) > 1:
        ls_matched_stores.append(tup_store_info +\
                                 (None, enseigne_fra_alt, 'ambiguous'))
      elif len(df_city_stores_alt) == 0:
        ls_matched_stores.append(tup_store_info +\
                                 (None, None, 'aucun'))

df_matching = pd.DataFrame(ls_matched_stores,
                          columns = ['store_chain', 'store_id', 'store_city',
                                     'ic_city', 'ic',
                                     'lsa_id', 'lsa_brand', 'Q'])

print len(df_matching[df_matching['lsa_id'].isnull()])
print df_matching[df_matching['lsa_id'].isnull()][0:20].to_string()

# todo: use LSA file including Corsica
# todo: check by hand when matching ambiguous (use gps with Google Drive?)
# todo: check for new stores (not in LSA?)
# todo: check results for Casino and others? (pbm in chosing type? use gps dist)
