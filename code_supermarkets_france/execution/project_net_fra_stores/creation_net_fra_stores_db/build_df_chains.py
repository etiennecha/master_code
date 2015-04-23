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
import pprint

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_source_json = os.path.join(path_dir_qlmc, 'data_source', 'data_json_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_source_chains = os.path.join(path_dir_qlmc, 'data_source', 'data_chain_websites')
path_dir_source_kml = os.path.join(path_dir_qlmc, 'data_source', 'data_kml')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

ls_chain_general = ['list_auchan_general_info',
                    'list_carrefour_general_info',
                    'list_leclerc_general_info',
                    'list_geant_casino_general_info',
                    'list_u_general_info', # contains gps
                    'list_cora_general_info', # contains gps
                    'list_franprix_general_info', # contains gps (small stores though?)
                    'list_super_casino_general_info_new', # contains gps...
                    'list_monoprix_general_info', # gps in kml (for now: todo: collect)
                    'list_intermarche_general_info_alt', # gps in kml (for now)
                    'list_intermarche_general_info_new'] # need geocoding / osm ?

ls_chain_full = [ 'list_auchan_full_info',
                  'list_carrefour_full_info',
                  'list_leclerc_full_info',
                  'list_geant_casino_full_info',
                  'list_franprix_full_info']
                    
ls_kml = ['monoprix.kml',
          'intermarche.kml']

# READ WEBSITE CHAIN DATA

# Load files
ls_chain_general_info = []
for file_general_info in ls_chain_general:
  ls_chain_general_info.append(dec_json(os.path.join(path_dir_source_chains, file_general_info)))

ls_chain_full_info = []
for file_full_info in ls_chain_full:
  ls_chain_full_info.append(dec_json(os.path.join(path_dir_source_chains, file_full_info)))

ls_chain_kml = []
for file_kml in ls_kml:
  ls_chain_kml.append(parse_kml(open(os.path.join(path_dir_source_kml, file_kml), 'r').read()))

ls_columns = ['type', 'name', 'gps', 'street', 'zip', 'city']

# AUCHAN (135)
def clean_auchan_str(word):
  ls_replace = [[u'&eacute;', u'é'],
                [u'&icirc;', u'î'],
                [u'&egrave;', u'è'],
                [u'&acirc;', u'â'],
                [u'&ecirc;', u'ê'],
                [u'&ccedil;', u'ç'],
                [u'&ocirc;', u'ô']]
  for old, new in ls_replace:
    word = word.replace(old, new)
  return word

ls_rows_auchan = []
for x in ls_chain_full_info[0]:
  gps =  x.get('gps', [])
  if gps and gps[1].strip() != '-' and gps[3].strip() != '0':
    gps = map(lambda x: x.replace(u',', u'.').strip(), [gps[3], gps[1]])
  else:
    gps = []
  address = x['list_opening_address'][1][0]
  re_zip = re.search(',\s[0-9]{5}', address)# visual check... could be 4
  ls_rows_auchan.append([u'Auchan',
                         clean_auchan_str(x['name']),
                         ' '.join(gps),
                         address[:re_zip.start()].strip(),
                         address[re_zip.start()+1:re_zip.end()].strip(),
                         re.split(u'cedex', 
                                  address[re_zip.end():],
                                  flags=re.IGNORECASE)[0].strip()])
df_auchan = pd.DataFrame(ls_rows_auchan, columns = ls_columns)

# CARREFOUR (2354, of which 1079 Carrefour and Carrefour markets: keep only hyper)
ls_rows_carrefour = []
for x in ls_chain_full_info[1]:
  ls_rows_carrefour.append([x['type'],
                            x['name'],
                            ' '.join(x['gps']), # clearly from geocoding
                            x['address'], # fix and regeocode
                            x['zip'],
                            x['city']])
ls_rows_carrefour[1085] = [u'Carrefour Contact',
                           u'Contact Allonnes',
                           u'47.293 0.029',
                           u'25 rue Albert Pottier',
                           u'49650',
                           u'ALLONNES'] # VIBRAYE (some default value?)
ls_rows_carrefour[2004] = [u'Carrefour Express',
                           u'Express Boulogne',
                           u'50.727 1.618',
                           u'31 rue Porte Neuve',
                           u'62200',
                           u'BOULOGNE SUR MER'] # VIBRAYE (some default value?)

df_carrefour = pd.DataFrame(ls_rows_carrefour, columns = ls_columns)

# LECLERC (591... majority of hypermarches... dunno exactly)
ls_rows_leclerc = []
for x in ls_chain_full_info[2]:
  ls_rows_leclerc.append([u'Leclerc',
                          x['name'],
                          ' '.join(x['gps']), # clearly from geocoding
                          x['address'], # fix and regeocode
                          x['zip'],
                          x['city']])
df_leclerc = pd.DataFrame(ls_rows_leclerc, columns = ls_columns)

# SYSTEME U (1147 of which 47 hypers)
ls_rows_u  = []
for dict_store in ls_chain_general_info[4]:
  ls_rows_u.append([dict_store['type'],
                    dict_store['name'],
                    ' '.join(map(lambda x: u'{:2.4f}'.format(float(x)), dict_store['gps'])),
                    dict_store['street'],
                    dict_store['zip'],
                    dict_store['city']])
# todo: fix scraping script
ls_rows_u[663] = [u'U Express',
                  u'U Express - STRASBOURG ROBERTSAU',
                  u'48.6007 7.7805',
                  u'67 rue Boecklin',
                  u'67000',
                  u'STRASBOURG']
ls_rows_u[821] = [u'Super U',
                  u'Super U - SAINT GERMAIN LEMBRON',
                  u'45.4606 3.2542',
                  u'ZAC des Coustilles ',
                  u'63340',
                  u'SAINT GERMAIN LEMBRON']
df_u = pd.DataFrame(ls_rows_u, columns = ls_columns)

# SUPER CASINO (update... may not have changed and quite a few gps missing)
def get_casino_type_name(word):
  ls_casino_types = [u'Hyper Casino',
                     u'Géant Casino',
                     u'Supermarché Casino',
                     u'Casino Cafétéria']
  for casino_type in ls_casino_types:
    if casino_type in word:
      word = word.rstrip(casino_type).strip()
      return (casino_type, word)
  return None

ls_rows_casino = []
for x in ls_chain_general_info[7]:
  gps = x.get('gps', [])
  if not gps:
    gps = []
  else:
    gps = map(lambda x: u'{:2.4f}'.format(x), gps)
  casino_type, casino_name = get_casino_type_name(x['name'])
  ls_rows_casino.append([casino_type,
                         casino_name.replace(u'&#039;', u"'"),
                         ' '.join(gps),
                         x['address'][0].replace(u'&#039;', u"'"),
                         x['address'][1][0:6].strip(),
                         x['address'][1][6:].strip().replace(u'&#039;', u"'")])
df_casino = pd.DataFrame(ls_rows_casino,  columns = ls_columns)
df_casino = df_casino[df_casino['type'] != u'Casino Cafétéria']
df_casino.reset_index(drop=True, inplace = True)
# todo : duplicate detection + a lot of gps missing?

## GEANT CASINO (110: included in CASINO)
#ls_rows_geant = [[x['name'], x['city'], x['gps'], x['zip'], x['city'], x['address']]\
#                  for x in ls_chain_full_info[3]]
#df_geant = pd.DataFrame(ls_rows_geant)

# CORA (59)
ls_rows_cora = []
for dict_store in ls_chain_general_info[5]:
  ls_rows_cora.append([u'Cora',
                       dict_store['name'],
                       ' '.join(map(lambda x: u'{:2.4f}'.format(float(x)), dict_store['gps'])),
                       dict_store['street'],
                       dict_store['zip_city'][0:6].strip(),
                       re.split(u'cedex',
                                dict_store['zip_city'][6:].replace(u'&lt;br&gt;', u''),
                                flags=re.IGNORECASE)[0].strip()])
df_cora = pd.DataFrame(ls_rows_cora, columns = ls_columns)

# FRANPRIX (supermarkets or smaller?... scrap zip code too?)
#ls_rows_franprix = []
#for dict_store in ls_chain_general_info[6]:
#  re_street = re.search(u'\s-\s', dict_store['address'])
#  city = dict_store['address'][:re_street.start()].replace(u'&#039;', u'').strip()
#  street = dict_store['address'][re_street.end():].strip().replace(u'&#039;', u'').strip()
#  ls_rows_franprix.append([u'Franprix',
#                           u'Franprix ' + city,
#                           ' '.join(map(lambda x: u'{:2.4f}'.format(float(x)), dict_store['gps'])),
#                           street,
#                           u'',
#                           city])
#df_franprix = pd.DataFrame(ls_rows_franprix, columns = ls_columns)

ls_rows_franprix = []
for ls_store in ls_chain_full_info[4]:
  city = ls_store[3][1][6:].replace(u"&#039;", u"'").strip()
  ls_rows_franprix.append([u'Franprix',
                           ' '.join([u'Franprix', city]),
                           ' '.join(map(lambda x: u'{:2.4f}'.format(float(x)), ls_store[2])),
                           ls_store[3][0].replace(u"&#039;", u"'").strip(),
                           ls_store[3][1][:6].strip(),
                           city])
df_franprix = pd.DataFrame(ls_rows_franprix, columns = ls_columns)

# DF ALL STORES IN FRANCE (EXCEPT MONOPRIX AND INTERMARCHE)

ls_df_stores_france = [df_auchan,
                       df_carrefour, # exclude small formats
                       df_leclerc,
                       df_u,
                       df_casino, # exclude duplicates?
                       df_cora,
                       df_franprix] # partial gps info

df_stores_france = pd.concat(ls_df_stores_france, ignore_index = True)

# No gps
len(df_stores_france[(df_stores_france['gps'] == '') | (pd.isnull(df_stores_france['gps']))])
print df_stores_france[ls_columns].to_string()

### Reads or creates
#fra_stores = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'fra_stores.h5'))
#fra_stores['df_auchan'] = df_auchan
#fra_stores['df_carrefour'] = df_carrefour
#fra_stores['df_leclerc'] = df_leclerc
#fra_stores['df_u'] = df_u
#fra_stores['df_casino'] = df_casino
#fra_stores['df_cora'] = df_cora
#fra_stores['df_franprix'] = df_franprix
#fra_stores.close()

# TODO:
# duplicate ???
# DF HD: dia, leaderprice, lidl, aldi, netto
