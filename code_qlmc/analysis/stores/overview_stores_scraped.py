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
                  'list_geant_casino_full_info']
                    
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
    gps = map(lambda x: x.replace(u',', u'.').strip(), [gps[1], gps[3]])
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

# MONOPRIX
ls_rows_monoprix = []
for ls_store in ls_chain_general_info[8]:
  ls_rows_monoprix.append([ls_store[0],
                           ls_store[1],
                           '',
                           ls_store[3][2],
                           ls_store[3][1],
                           ls_store[3][0]])
df_monoprix = pd.DataFrame(ls_rows_monoprix, columns = ls_columns)

# FRANPRIX (supermarkets or smaller?... scrap zip code too?)
ls_rows_franprix = []
for dict_store in ls_chain_general_info[6]:
  re_street = re.search(u'\s-\s', dict_store['address'])
  city = dict_store['address'][:re_street.start()].replace(u'&#039;', u'').strip()
  street = dict_store['address'][re_street.end():].strip().replace(u'&#039;', u'').strip()
  ls_rows_franprix.append([u'Franprix',
                           u'Franprix ' + city,
                           ' '.join(map(lambda x: u'{:2.4f}'.format(float(x)), dict_store['gps'])),
                           street,
                           u'',
                           city])
df_franprix = pd.DataFrame(ls_rows_franprix, columns = ls_columns)

# OTHER DATA

# INTERMARCHE (new data, no gps, see below for more)
def get_itm_type(word):
  dict_itm_types = {u'logo_intermarche_Express.png' : u'Intermarché Express',
                    u'logo_intermarche_Hyper.png'   : u'Intermarché Hyper',
                    u'logo_intermarche.png'         : u'Intermarché',
                    u'logo_intermarche_Super.png'   : u'Intermarché Super',
                    u'logo_intermarche_Contact.png' : u'Intermarché Contact'}
  for itm_logo, itm_type in dict_itm_types.items():
    if itm_logo in word:
      return itm_type
  return None

ls_rows_intermarche = []
for ls_store in ls_chain_general_info[10]:
  store_type = get_itm_type(ls_store[1])
  address =  [elt.replace(u'\n', u'').replace(u'\t', u'').strip() for elt in ls_store[2]\
                if elt.replace(u'\n', u'').replace(u'\t', u'').strip()]
  re_zip = re.search(u'\(([0-9]{5})\)', address[0])
  ls_rows_intermarche.append([store_type,
                              ' '.join([store_type, address[0][:re_zip.start()]]),
                              '',
                              ' '.join(address[1:]),
                              re_zip.group(1),
                              address[0][:re_zip.start()]])
df_intermarche = pd.DataFrame(ls_rows_intermarche, columns = ls_columns)
# todo: get gps for following at least...
# print df_intermarche[df_intermarche['type'] == u'Intermarché Hyper'].to_string()

# INTERMARCHE: OLD DATA + POI/KML FILE
ls_itm = ls_chain_general_info[9]
ls_itm_kml = ls_chain_kml[1]
ls_itm_kml_names = [x[0].decode('latin-1').lower() for x in ls_itm_kml]
ls_itm_matched_q = [x[0] for x in ls_itm if x[0].lower() in ls_itm_kml_names]
ls_itm_no_q = [x[0] for x in ls_itm if x[0].lower() not in ls_itm_kml_names]

# built df intermarche website data: pbm with "'"... rubish data..
ls_itm_rows = []
for ls_store in ls_chain_general_info[9]:
  street = ls_store[1].split('=')[0].rstrip(u'"').lstrip(u'"')
  street = re.split(u'[0-9]{5}', street)[0].replace(u'" ', u"'").strip()
  ls_itm_rows.append([u'Intermarché',
                     ls_store[0],
                     '',
                     street,
                     ls_store[2][0],
                     ls_store[2][1]])
df_itm = pd.DataFrame(ls_itm_rows, columns=ls_columns)
df_itm['name_2'] = df_itm['name'].apply(lambda x: standardize_intermarche(str_low_noacc(x)))
se_itm_vc = df_itm['name_2'].value_counts()
se_itm_unique = se_itm_vc[se_itm_vc == 1]
str_unique = u'|'.join(se_itm_unique.index)
df_itm = df_itm[df_itm['name_2'].str.contains(str_unique)]

# build df intermarche kml data
df_itm_kml = pd.DataFrame(ls_chain_kml[1],
                          columns = ['name', 'gps'])
df_itm_kml['name_2'] = df_itm_kml['name'].apply(lambda x: standardize_intermarche(\
                                                            str_low_noacc(x.decode('latin-1'))))
df_itm_kml['gps'] = df_itm_kml['gps'].apply(lambda y: ' '.join(\
                                              map(lambda x: u'{:2.4f}'.format(float(x)), y)))

se_itm_kml_vc = df_itm_kml['name_2'].value_counts()
se_itm_kml_unique = se_itm_kml_vc[se_itm_kml_vc == 1]
str_kml_unique = u'|'.join(se_itm_kml_unique.index)
ls_replace = [[u'(', u'\('],
              [u')', u'\)'],
              [u'.', u'\.']]
for old, new in ls_replace:
  str_kml_unique = str_kml_unique.replace(old, new)
df_itm_kml = df_itm_kml[df_itm_kml['name_2'].str.contains(str_kml_unique)]

# match: old intermarche website (including entity names) vs. kml
ls_itm_matched = [x for x in df_itm['name_2'].values if x in  df_itm_kml['name_2'].values]
ls_itm_no = [x for x in df_itm['name_2'].values if x not in df_itm_kml['name_2'].values]

df_itm.index = df_itm['name_2']
df_itm_kml.index = df_itm_kml['name_2']
df_itm_all = df_itm.join(df_itm_kml, rsuffix='_kml')
#df_itm_all_o = df_itm.join(df_itm_kml, rsuffix='_kml', how='outer')
df_itm_all['gps'] = df_itm_all['gps_kml']
del(df_itm_all['gps_kml'])
# print df_itm_all[['name', 'gps', 'street', 'zip', 'city']].to_string()

# match 2: old website with kml vs. new website (including type of supermarket)

# clean street in itm
def clean_itm_street(word):
  ls_replace = [[u'\n', u''],
                [u'\t', u''],
                [u"'",  u' '],
                [u'"',  u' ']]
  for old, new in ls_replace:
    word = word.replace(old, new)
  word = u' '.join([x for x in word.split(u' ') if x])
  return word

df_itm_all['street'] = df_itm_all['street'].apply(lambda x: clean_itm_street(x).lower())
df_intermarche['street'] = df_intermarche['street'].apply(lambda x: clean_itm_street(x).lower())

df_intermarche['street_zip'] = df_intermarche['street'] + u' ' + df_intermarche['zip']
df_itm_all['street_zip'] = df_itm_all['street'] + u' ' + df_itm_all['zip']
ls_itm_matched_2 = [x for x in df_intermarche['street_zip'].values\
                      if x in df_itm_all['street_zip'].values]
ls_itm_no_2 = [x for x in df_intermarche['street_zip'].values\
                 if x not in df_itm_all['street_zip'].values]

df_itm_all.set_index('street_zip', inplace = True)
df_intermarche.set_index('street_zip', inplace = True)
df_intermarche_all = df_intermarche.join(df_itm_all[['name', 'gps', 'city']],
                                         rsuffix='_o',
                                         how = 'outer')
df_intermarche_all.reset_index(drop = True, inplace = True)

# first matching
len(df_intermarche_all[(~pd.isnull(df_intermarche_all['name_o'])) &\
                       (~pd.isnull(df_intermarche_all['gps_o']))])

# full matching
len(df_intermarche_all[(~pd.isnull(df_intermarche_all['type'])) &\
                        (~pd.isnull(df_intermarche_all['gps_o']))])

pd.set_option('display.max_colwidth', 30)
ls_disp_itm = ['name', 'street', 'zip', 'city', 'name_o', 'gps_o', 'city_o']
# print df_intermarche_all[ls_disp_itm][0:100].to_string()

# todo: correct in kml
# "a. midel" => "midel"

df_intermarche_all.drop(['name_o', 'city_o', 'gps'], 1, inplace = True)
df_intermarche_all.rename(columns = {'gps_o' : 'gps'}, inplace = True)

# DF ALL STORES IN FRANCE

ls_df_stores_france = [df_auchan,
                       df_carrefour, # exclude small formats
                       df_leclerc,
                       df_u,
                       df_casino, # exclude duplicates?
                       df_cora,
                       df_monoprix, # no gps for now + duplicates to exclude
                       df_franprix,
                       df_intermarche_all] # partial gps info

df_stores_france = pd.concat(ls_df_stores_france, ignore_index = True)

# No gps
len(df_stores_france[(df_stores_france['gps'] == '') | (pd.isnull(df_stores_france['gps']))])

print df_stores_france[ls_columns].to_string()

df_itm_all.reset_index(drop = True, inplace = True)
df_itm_all[df_itm_all['city'] == 'volgelsheim']
# duplicate ???

# todo: DF HD: dia, leaderprice, lidl, aldi, netto
