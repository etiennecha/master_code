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

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

path_qlmc_scraped = os.path.join(path_data,
                                 'data_supermarkets',
                                 'data_source',
                                 'data_qlmc_2015',
                                 'data_scraped_201503')

path_csv = os.path.join(path_data,
                        'data_supermarkets',
                        'data_built',
                        'data_qlmc_2015',
                        'data_csv_201503')

path_lsa_csv = os.path.join(path_data,
                            'data_supermarkets',
                            'data_built',
                            'data_lsa',
                            'data_csv')

df_stores = pd.read_csv(os.path.join(path_csv,
                                     'df_stores.csv'),
                        encoding = 'utf-8',
                        dtype = {'ic' : str})

# todo: move to dedicated script
df_stores.loc[df_stores['store_id'] == 'centre-e-leclerc-clichy',
              'ic'] = '92024'

df_lsa = pd.read_csv(os.path.join(path_lsa_csv,
                                  'df_lsa_active.csv'),
                     dtype = {u'C_INSEE' : str,
                              u'C_INSEE_Ardt' : str,
                              u'C_Postal' : str,
                              u'SIREN' : str,
                              u'NIC' : str,
                              u'SIRET' : str},
                     parse_dates = [u'Date_Ouv', u'Date_Fer', u'Date_Reouv',
                                    u'Date_Chg_Enseigne', u'Date_Chg_Surface'],
                     encoding = 'UTF-8')
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
               [u'G20', u'G 20', u'G 20'], # check if chain in LSA
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
    df_city_stores = df_lsa[(df_lsa['C_INSEE_Ardt'] == insee_code) &\
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
      print df_city_stores[['Ident', 'Enseigne', 'Adresse1',
                            'C_Postal', 'Ville', 'dist']].to_string()
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
      df_city_stores_alt = df_lsa[(df_lsa['C_INSEE_Ardt'] == insee_code) &\
                                  (df_lsa['Enseigne_matching'] == enseigne_fra_alt)].copy()
      if len(df_city_stores_alt) == 1:
        ls_matched_stores.append(tup_store_info +\
                                 (df_city_stores_alt.iloc[0]['Ident'],
                                  enseigne_fra_alt,
                                  'indirect'))
      elif len(df_city_stores_alt) > 1:
        # check with distances
        df_city_stores_alt['qlmc_lat'] = row['store_lat']
        df_city_stores_alt['qlmc_lng'] = row['store_lng']
        df_city_stores_alt['dist'] =\
           df_city_stores_alt.apply(lambda x: compute_distance_ar(x['qlmc_lat'],
                                                                  x['qlmc_lng'],
                                                                  x['Latitude'],
                                                                  x['Longitude']),
                                     axis = 1)
        print u'\n', tup_store_info
        print df_city_stores_alt[['Ident', 'Enseigne', 'Adresse1',
                                  'C_Postal', 'Ville', 'dist']].to_string()
        if len(df_city_stores_alt[df_city_stores_alt['dist'] <= 0.1]) == 1:
          ls_matched_stores.append(tup_store_info +\
                                   (df_city_stores_alt\
                                      [df_city_stores_alt['dist'] <= 0.1].iloc[0]['Ident'],
                                    enseigne_fra_alt,
                                    'direct_gps'))
        else:
          ls_matched_stores.append(tup_store_info +\
                                   (None, enseigne_fra_alt, 'ambiguous'))
      elif len(df_city_stores_alt) == 0:
        ls_matched_stores.append(tup_store_info +\
                                 (None, None, 'aucun'))

df_matching = pd.DataFrame(ls_matched_stores,
                          columns = ['store_chain', 'store_id', 'store_city',
                                     'ic_city', 'ic',
                                     'lsa_id', 'lsa_brand', 'Q'])

# checked by hand when matching ambiguous (use gps with Google Drive?)
ls_fix_matching = [['super-u-rennes', '10914'],
                   ['super-u-rennes-1', '18433'],
                   ['super-u-brest', '140546'],
                   ['super-u-le-havre', '3461'],
                   ['super-u-le-havre-1', '14755'],
                   ['super-u-limoges', '1458'],
                   ['super-u-nantes', '740'],
                   ['carrefour-market-ajaccio', '2762'], # not sure (dist 1.39)
                   ['carrefour-market-le-mans-sablons', '1367'], # MARKET in LSA
                   ['carrefour-market-le-mans', '1366'], # dist 0.16
                   ['carrefour-market-rennes-villejean-kennedy', '1706'], # dist 0.43
                   ['carrefour-market-bordeaux', '1045'], # dist 0.12
                   ['carrefour-market-peyrehorade', '3753'], # dist 0.29
                   ['carrefour-market-bourges', '3782'], # dist 0.10 not necessary?
                   ['carrefour-market-vierzon', '2462'],
                   ['carrefour-market-laon', '1565'],
                   ['carrefour-market-les-sables-d-olonne-petite-garliere', '1445'],
                   ['carrefour-market-les-sables-d-olonne-castelnau', '11029'],
                   ['carrefour-market-colomiers', '2396'], # dist 0.19
                   ['carrefour-market-sainte-maxime-1', '2414'], # dist 0.10 not necessary?
                   ['carrefour-market-reims-clemenceau', '2864'],
                   ['carrefour-market-nevers', '176597'], # dist 0.57 => Colbert
                   ['casino-clichy', '11417'],
                   ['supermarche-match-douai-rue-du-kiosque', '3525'],
                   ['atac-autun', '1559'], # not closest but av republique
                   ['leclerc-express-borgo', '10382'], # no match, diff ic?
                   ['super-u-bihorel', '2539'], # no match, diff ic?
                   ['carrefour-contact-freyming-merlebach', '12719'], # no match, chain?
                   ['carrefour-contact-gramat', '10235'],
                   ['carrefour-marseille-grand-littoral', '39135'],
                   ['carrefour-contact-plouguerneau', '11454'],
                   ['carrefour-contact-grenade-sur-l-adour', '9450'],
                   ['carrefour-city-deuil-la-barre', '9702'],
                   ['carrefour-contact-st-nicolas-de-la-grave', '195959'],
                   ['auchan-city-tourcoing', '181644'],
                   ['casino-blanzac-les-matha', '4054'], # no match, diff ic
                   ['les-halles-d-auchan-le-blanc-mesnil', '158859'], # no match, chain
                   ['leclerc-express-montlucon-le-pont-vert', '1147'],
                   ['centre-e-leclerc-ajaccio-rte-d-alata', '50986'], # dist 0.120
                   ['centre-e-leclerc-onet-le-chateau-rte-de-severac', '2232'], # dist 0.640
                   ['centre-e-leclerc-varennes-sur-seine', '172159'],
                   ['centre-e-leclerc-hyeres', '197842'], # twice same? one closed?
                   ['centre-e-leclerc-dunkerque-centre-marine', '50061'],
                   ['centre-e-leclerc-ajaccio-prince-imperial', '3503'],
                   ['centre-e-leclerc-lannion-rte-de-guingamp', '2238'],
                   ['centre-e-leclerc-le-cannet-rocheville-46-avenue-franklin-roosevelt', '436'],
                   ['intermarche-super-cagnes-sur-mer', '10376'],
                   ['intermarche-super-concarneau-korrigans', '3676'],
                   ['intermarche-super-carcassonne', '1157'],
                   ['intermarche-super-rodez', '13006'],
                   ['intermarche-hyper-moissac', '171579'],
                   ['intermarche-super-laval', '158676'],
                   ['intermarche-super-niort', '3302'],
                   ['intermarche-super-brest-1', '4114'],
                   ['intermarche-super-brest-2', '4194'],
                   ['intermarche-super-coudekerque-branche-89-av-jb-lebas', '177517'],
                   ['intermarche-super-cahors', '2461'],
                   ['intermarche-super-saint-malo', '4160'],
                   ['intermarche-super-brest', '1028'], # dist 3.120 but only one remaining.. check
                   ['intermarche-super-bergerac', '13340'],
                   ['intermarche-super-la-teste-de-buch', '4154'],
                   ['intermarche-contact-pontivy', '10968'],
                   ['intermarche-super-langres', '4497'],
                   ['intermarche-super-chateaudun-rte-d-orleans', '1203'],
                   ['intermarche-super-clermont-ferrand', '1335'],
                   ['intermarche-super-gradignan', '2835'],
                   ['intermarche-super-la-seyne-sur-mer', '1429'],
                   ['intermarche-super-toulon', '3319'],
                   ['intermarche-super-muret', '1679'],
                   ['intermarche-super-vienne', '4293'],
                   ['super-u-donzere', '151457']] # other is drive

# centre-e-leclerc-thury-harcourt : sold => Super U (July 2014)
# intermarche-super-sainte-gemmes-d-andigne : opened Nov 2014 (2400m2)

ls_drive = [['casino-drive-lagny-sur-marne', '197888']] # drive

ls_chain_chge = [['super-u-laguenne', '693'], # ex SIMPLY
                 ['casino-le-blanc-mesnil-25-27-av-henri-barbusse', '12349']] # ex MONOPRIX

for qlmc_id, lsa_id in ls_fix_matching:
  df_matching.loc[df_matching['store_id'] == qlmc_id, 'lsa_id'] = lsa_id
  df_matching.loc[df_matching['store_id'] == qlmc_id, 'Q'] = 'amb_fixed'

print len(df_matching[df_matching['lsa_id'].isnull()])
print df_matching[df_matching['lsa_id'].isnull()].to_string()
# todo: check for new stores (not in LSA?)
# todo: check results for Casino and others? (pbm in chosing type? use gps dist)

# Check matching with distance
df_stores_f = pd.merge(df_stores,
                       df_matching[['store_id', 'lsa_id']],
                       on = 'store_id',
                       how = 'left')

ls_lsa_cols = ['Ident',
               'Enseigne',
               'Enseigne_Alt',
               'Groupe',
               'Adresse1',
               'Ville',
               'C_INSEE_Ardt',
               'Surface',
               'Nb_Caisses',
               'Nb_Emplois',
               'Nb_Pompes',
               'Longitude',
               'Latitude',
               'Verif',
               'Type']

df_stores_f = pd.merge(df_stores_f,
                       df_lsa[ls_lsa_cols],
                       left_on = 'lsa_id',
                       right_on = 'Ident',
                       how = 'left')

df_stores_f['dist'] =\
   df_stores_f.apply(lambda x: compute_distance_ar(x['store_lat'],
                                                   x['store_lng'],
                                                   x['Latitude'],
                                                   x['Longitude']),
                        axis = 1)

ls_di = ['store_id', 'store_lat', 'store_lng',
         'Enseigne', 'Adresse1', 'Ville', 'Latitude', 'Longitude', 'Verif']

print u'\n', df_stores_f[df_stores_f['dist'] > 5][ls_di + ['dist']].to_string()
# todo: extend to 3
# check that (when?) LSA should be preferred...

ls_final_gps = [['casino-prunelli-di-fiumorbo', 'qlmc'], # 4 and bad
                ['carrefour-market-beaumont-le-roger', 'lsa'],
                ['carrefour-market-anse', (45.9380, 4.7201)], # 2 and bad
                ['super-u-saint-brevin-les-pins', 'lsa'],
                ['centre-e-leclerc-oletta', 'lsa'],
                ['leclerc-express-borgo', 'lsa'],
                ['casino-rivieres', (45.7463, 0.3830)], # 3 and bad
                ['u-express-bagnoles-de-l-orne', 'qlmc'], # 4 and bad
                ['casino-estancarbon', 'lsa'],
                ['intermarche-super-surgeres', 'lsa'],
                ['centre-e-leclerc-joue-les-tours', 'lsa'],
                ['carrefour-market-aussonne', 'lsa'], # check (resumed activity?)
                ['carrefour-market-vauvert', 'qlmc']] # 3 and bad

# Whenever 4 (and 3): not good idea to take LSA
# Check if 4 means center of commune... if qlmc different then maybe best?
# Anyway: only 7 have 4... and 122 have 3 => those should be inspected (use dist?)

#print u'\n', df_stores_f[(df_stores_f['Verif'] == 1) &\
#                         (df_stores_f['dist'] >= 1)][ls_di + ['dist']].to_string()

df_stores_f.to_csv(os.path.join(path_csv,
                                'df_stores_final.csv'),
                   encoding = 'utf-8',
                   float_format='%.4f',
                   index = False)
