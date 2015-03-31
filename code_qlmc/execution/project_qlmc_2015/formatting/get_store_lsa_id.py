#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
from functions_string import *
from functions_generic_qlmc import *
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
                                  'df_lsa_active.csv'),
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
                            (df_lsa['Enseigne'] == enseigne_fra)].copy()
    tup_store_info = tuple(row[['store_chain', 'store_id', 'store_city',
                                'ic_city', 'ic']].values)
    if len(df_city_stores) == 1:
      ls_matched_stores.append(tup_store_info +\
                               (df_city_stores.iloc[0]['Ident'],
                                enseigne_fra,
                                'direct'))
    elif len(df_city_stores) > 1:
      # check with distances
      df_city_stores['qlmc_lat'] = row['store_lat']
      df_city_stores['qlmc_lng'] = row['store_lng']
      df_city_stores['dist'] =\
         df_city_stores.apply(lambda x: compute_distance_ar(x['qlmc_lat'],
                                                            x['qlmc_lng'],
                                                            x['Latitude'],
                                                            x['Longitude']),
                              axis = 1)
      print u'\n', tup_store_info
      print df_city_stores[['Ident', 'Enseigne', 'ADRESSE1',
                            'Code postal', 'Ville', 'dist']].to_string()
      if len(df_city_stores[df_city_stores['dist'] <= 0.1]) == 1:
        ls_matched_stores.append(tup_store_info +\
                                 (df_city_stores\
                                    [df_city_stores['dist'] <= 0.1].iloc[0]['Ident'],
                                  enseigne_fra,
                                  'direct_gps'))
      else:
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
        # do: check with distances
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

print df_matching[df_matching['lsa_id'].isnull()].to_string()

# todo: use LSA file including Corsica
# todo: check by hand when matching ambiguous (use gps with Google Drive?)
# todo: check for new stores (not in LSA?)
# todo: check results for Casino and others? (pbm in chosing type? use gps dist)

# TODO: finish casino
ls_fix = [['super-u-rennes', '10914'],
          ['super-u-rennes-1', '18433'],
          ['super-u-brest', '140546'],
          ['super-u-le-havre', '3461'],
          ['super-u-le-havre-1', '14755'],
          ['super-u-limoges', '1458'],
          ['super-u-nantes', '740'],
          ['carrefour-market-le-mans-sablons', '1367'], # MARKET in LSA
          ['carrefour-market-le-mans', '974'], # distance 0.16
          ['carrefour-market-bordeaux', '1045'], # distance 0.12
          ['carrefour-market-peyrehorade', '3753'], # distance 0.29
          ['carrefour-market-bourges', '3782'], # distance 0.10 not necessary?
          ['carrefour-market-vierzon', '2462'],
          ['carrefour-market-laon', '1565'],
          ['carrefour-market-les-sables-d-olonne-petite-garliere', '1445'],
          ['carrefour-market-les-sables-d-olonne-castelnau', '11029'],
          ['carrefour-market-colomiers', '2396'], # distance 0.19
          ['carrefour-market-sainte-maxime-1', '2414'], # distance 0.10 not necessary?
          ['carrefour-market-reims-clemenceau', '2864'],
          ['carrefour-market-nevers', '176597']] # distance 0.57 => Colbert
