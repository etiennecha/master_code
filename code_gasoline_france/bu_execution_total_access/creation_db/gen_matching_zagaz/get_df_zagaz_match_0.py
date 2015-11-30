#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
from functions_string import *
from BeautifulSoup import BeautifulSoup
import copy
import collections

def str_zagaz_corrections(word):
  word = word.lower()
  word = re.sub(ur'(^|\s|,)r?\.?\s?d\.?\s?([0-9]{0,5})(\s|$|,)',
                ur'\1 route departementale \2 \3',
                word)
  word = re.sub(ur'(^|\s|,)r?\.?\s?n\.?\s?([0-9]{0,5})(\s|$|,)',
                ur'\1 route nationale \2 \3',
                word) 
  return word.strip()

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built_paper, u'data_json')

path_dir_match_insee = os.path.join(path_data, u'data_insee', u'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_data, u'data_insee', u'data_extracts')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dir_zagaz = os.path.join(path_dir_source, 'data_stations', 'data_zagaz')

# ################
# LOAD DF GOUV
# ################

# duplicates within master_info... (hence might match dropped ids)
master_info = dec_json(os.path.join(path_dir_built_json, 'master_info_fixed.json'))

dict_brands = dec_json(os.path.join(path_dir_source, 'data_other', 'dict_brands.json'))
dict_brands_std = {v[0]: v[1:] for k,v in dict_brands.items()}

dict_addresses = {indiv_id: [indiv_info['address'][i] for i in (5, 3, 4, 0)\
                               if indiv_info['address'][i]]\
                    for indiv_id, indiv_info in master_info.items()}
master_addresses = build_master_addresses(dict_addresses)

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info.csv'),
                              encoding = 'utf-8',
                              dtype = {'id_station' : str,
                                       'adr_zip' : str,
                                       'adr_dpt' : str,
                                       'ci_1' : str,
                                       'ci_ardt_1' :str,
                                       'ci_2' : str,
                                       'ci_ardt_2' : str,
                                       'dpt' : str})
df_info.set_index('id_station', inplace = True)

# ################
# LOAD DF ZAGAZ
# ################

df_zagaz = pd.read_csv(os.path.join(path_dir_built_csv,
                                    'df_zagaz_stations_2012.csv'),
                       encoding='utf-8',
                       dtype = {'id_zagaz' : str,
                                'zip' : str,
                                'ci_1' : str,
                                'ci_ardt_1' : str})
df_zagaz.set_index('id_zagaz', inplace = True)

# u'MATCH' => u'SUPERMARCHE MATCH'
# u'SPAR' = u'SPAR STATION' or u'SUPERMARCHES SPAR' check if real difference
# u'8 A HUIT' => u'8  A HUIT'
# u'ENI' => u'AGIP' check

# 'OIL' / 'TEXACO' / 'IDS' / 'AS24' / 'ANTARGAZ' / 'PRIMAGAZ' / 'DIVERS'
# 'OIL' (18) => Indpt ss enseigne or small
# 'TEXACO' (2) => not really in france
# 'IDS' (2) => Indpt ss enseigne
# 'AS24' (2) => Not in my data... (one became Total Access?)
# 'ANTARGAZ' / 'PRIMAGAZ' => Not in my data
# 'DIVERS' (1394) => Indpt ss enseigne... or else?

dict_brands_update = {'OIL' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'TEXACO' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'ENI' : [u'AGIP', u'AGIP', u'OIL'],
                      'IDS': [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      '8 A HUIT' : [u'HUIT_A_HUIT', u'CARREFOUR', u'SUP'],
                      'AS 24' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'SPAR' : [u'CASINO', u'CASINO', u'SUP'],
                      'ANTARGAZ' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'DIVERS' : [u'INDEPENDANT', u'INDEPENDANT', u'IND'],
                      'MATCH' : [u'CORA', u'CORA', u'SUP'],
                      'PRIMAGAZ' : [u'INDEPENDANT', u'INDEPENDANT', u'IND']}

# #######################
# MATCHING GOUV VS. ZAGAZ
# #######################

# Strategy 1: within similar ZIP, compare standardized address 
#             + check on name station (print) if score is ambiguous
# Strategy 2: compare standardized string: address, ZIP, City

# Standardization: suppress '-' (?), replace ' st ' by 'saint'
# master: 26200005, 40390001 (C/C => Centre Commercial ?), 35230001, 13800007 (Av. => Avenue)
# master: 67540002 (\\ => ), 59860002 (386/388 => 386/388 (?))
# master: lack of space (not necessarily big pbm) 78120010
# check weird : 18000014, 82500001, 58240002

# loop on all zagaz stations within zip code area
# loop on all master sub-adresses vs. zagaz sub-addresses: keep best match
# produces a list with best match for each zagaz station within zip code are
# can be more than 2 components... some seem to have standard format DXXX=NXX

# To make comparison easier
df_zagaz.loc[pd.isnull(df_zagaz['street']), 'street'] = u''

# MATCHING BASED ON INSEE CODE
dict_matches = {}
ls_ci_not_in_zag = []
for gov_id, gov_row in df_info.iterrows():
  if master_addresses.get(gov_id, None):
    gov_addresses = master_addresses[gov_id]
    # check if any zagaz station has same ci
    if gov_row['ci_1'] in df_zagaz['ci_1'].unique():
      ls_station_results = []
      # loop on zagaz stations with same ci
      for zag_id, zag_row in df_zagaz[df_zagaz['ci_1'] == gov_row['ci_1']].iterrows():
        ls_station_levenshtein = []
        # want to compare each sub gov address
        for gov_street in str_low_noacc(gov_row['adr_street']).split(' - '):
          for zag_street in zag_row['street'].split(' - '):
            if not ('=' in zag_street):
              std_zag_street = str_corr_low_std_noacc(zag_street, False)
              levenshtein_tuple = get_levenshtein_tuple(gov_street, std_zag_street)
              ls_station_levenshtein.append(levenshtein_tuple)
            else:
              for sub_zag_street in zag_street.split('='):
                std_sub_zag_street = str_corr_low_std_noacc(sub_zag_street, False)
                std_sub_zag_street = str_zagaz_corrections(std_sub_zag_street)
                levenshtein_tuple = get_levenshtein_tuple(gov_street, std_sub_zag_street)
                ls_station_levenshtein.append(levenshtein_tuple)
        ls_station_levenshtein = sorted(ls_station_levenshtein, key=lambda tup: tup[0])
        ls_station_results.append([zag_id] + list(ls_station_levenshtein[0]))
      dict_matches[gov_id] = sorted(ls_station_results, key=lambda tup: tup[1])
    else:
      ls_ci_not_in_zag.append(gov_id)
  else:
    print gov_id, 'no address'

# Results are ranked based on first but if short... second could be right one
dict_matching_quality = {}
for gov_id, ls_matches in dict_matches.items():
  if not ls_matches:
    pass
  elif len(ls_matches) == 1:
    if ls_matches[0][1] == 0:
      dict_matching_quality.setdefault('ci_u_lev_top', []).append((gov_id, ls_matches[0][0]))
    elif (min(*ls_matches[0][2:4]) >= 8) and\
        (1 - float(ls_matches[0][1])/float(ls_matches[0][3]) >= 0.5):
      dict_matching_quality.setdefault('ci_u_lev_ok', []).append((gov_id, ls_matches[0][0]))
    else:
      dict_matching_quality.setdefault('ci_u_lev_bad', []).append((gov_id, ls_matches[0][0]))
  else:
    if ls_matches[0][1] == 0:
      dict_matching_quality.setdefault('ci_m_lev_top', []).append((gov_id, ls_matches[0][0]))
    elif (min(*ls_matches[0][2:4]) >= 8) and\
        (1 - float(ls_matches[0][1])/float(ls_matches[0][3]) >= 0.5):
      dict_matching_quality.setdefault('ci_m_lev_ok', []).append((gov_id, ls_matches[0][0]))
    else:
      dict_matching_quality.setdefault('ci_m_lev_bad', []).append((gov_id, ls_matches[0][0]))

# Build df results (slight pbm... not gov address from master_address but df_info)
ls_rows_matches = []
for quality, ls_matches in dict_matching_quality.items():
  for gov_id, zag_id in ls_matches:
    ls_rows_matches.append([quality,
                            gov_id,
                            zag_id] +\
                           list(df_info.ix[gov_id][['adr_street',
                                                    'adr_city',
                                                    'brand_0',
                                                    'brand_1',
                                                    'lat_gov_1',
                                                    'lng_gov_1',
                                                    'ci_1']]) +\
                           list(df_zagaz.ix[zag_id][['street',
                                                     'city',
                                                     'brand',
                                                     'lat',
                                                     'lng']]))

ls_columns = ['quality', 'gov_id', 'zag_id',
              'gov_street', 'gov_city',
              'gov_br_0', 'gov_br_1', 'gov_lat', 'gov_lng', 'ci',
              'zag_street', 'zag_city',
              'zag_br', 'zag_lat', 'zag_lng']
df_matches = pd.DataFrame(ls_rows_matches,
                          columns = ls_columns)

df_matches['dist'] = df_matches.apply(\
                           lambda x: compute_distance(\
                                            (x['gov_lat'], x['gov_lng']),
                                            (x['zag_lat'], x['zag_lng'])), axis = 1)

# todo: check on brand (flexibility?) + gps coordinates
# get rid of pbms by observation
# then restart procss on remaining stations

# CHECK RESULT QUALITY WITH BRAND / GROUP

# Update dict_brands with zagaz specific brands
dict_brands.update(dict_brands_update)

df_matches['zag_br'] = df_matches['zag_br'].apply(\
                         lambda x: dict_brands[str_low_noacc(x).upper()][0])

# Further normalize brands (applied to standardized brands)
dict_brands_norm = {u'SHOPI': [u'CARREFOUR', u'GMS'],
                    u'CARREFOUR_CONTACT': [u'CARREFOUR', u'GMS'],
                    u'ECOMARCHE' : [u'MOUSQUETAIRES', u'GMS'],
                    u'INTERMARCHE_CONTACT' : [u'MOUSQUETAIRES', u'GMS'],
                    u'INTERMARCHE' : [u'MOUSQUETAIRES', u'GMS'],
                    u'ESSO_EXPRESS' : [u'ESSO', u'OIL']}
dict_brands_std.update(dict_brands_norm)
for field_brand in ['zag_br', 'gov_br_0', 'gov_br_1']:
  df_matches[field_brand] = df_matches[field_brand].apply(\
                              lambda x: dict_brands_std.get(x, [None, None])[0])

# Top quality
print '\nMatched (top) and same brand:',\
      len(df_matches[((df_matches['quality'] == 'ci_u_lev_top') |\
                      (df_matches['quality'] == 'ci_m_lev_top')) &\
                     ((df_matches['zag_br'] == df_matches['gov_br_0']) |\
                      (df_matches['zag_br'] == df_matches['gov_br_1']))])

print 'Matched (top) and diff brand:',\
      len(df_matches[((df_matches['quality'] == 'ci_u_lev_top') |\
                      (df_matches['quality'] == 'ci_m_lev_top')) &\
                     (df_matches['zag_br'] != df_matches['gov_br_0']) &\
                     (df_matches['zag_br'] != df_matches['gov_br_1'])])

# Different brand: really not to be matched?

ls_ma_di_0 = ['gov_id', 'zag_id',
              'gov_street', 'zag_street',
              'gov_br_0', 'gov_br_1', 'zag_br', 'dist']

print df_matches[ls_ma_di_0][((df_matches['quality'] == 'ci_u_lev_top') |\
                               (df_matches['quality'] == 'ci_m_lev_top')) &\
                              (df_matches['zag_br'] != df_matches['gov_br_0']) &\
                              (df_matches['zag_br'] != df_matches['gov_br_1'])].to_string()

# Unique possibility at code insee level but matching not great: just diff address?

pd.set_option('display.max_colwidth', 30)

print '\nMatched (bad) but unique at insee code level and same brand:',\
      len(df_matches[(df_matches['quality'] == 'ci_u_lev_bad') &\
                     ((df_matches['zag_br'] == df_matches['gov_br_0']) |\
                      (df_matches['zag_br'] == df_matches['gov_br_1']))])

ls_ma_di_1 = ['gov_id', 'zag_id', 'gov_city', 'zag_city',
              'gov_street', 'zag_street',
              'gov_br_0', 'gov_br_1', 'zag_br', 'dist']

print df_matches[ls_ma_di_1][(df_matches['quality'] == 'ci_u_lev_bad') &\
                             ((df_matches['zag_br'] == df_matches['gov_br_0']) |\
                              (df_matches['zag_br'] == df_matches['gov_br_1']))].to_string()

print '\nMatched (bad) but unique at insee code level and diff brand:',\
      len(df_matches[(df_matches['quality'] == 'ci_u_lev_bad') &\
                     (df_matches['zag_br'] != df_matches['gov_br_0']) &\
                     (df_matches['zag_br'] != df_matches['gov_br_1'])])

print df_matches[ls_ma_di_1][(df_matches['quality'] == 'ci_u_lev_bad') &\
                             (df_matches['zag_br'] != df_matches['gov_br_0']) &\
                             (df_matches['zag_br'] != df_matches['gov_br_1'])].to_string()

# OUTPUT ACCEPTED MATCHES
df_output = df_matches[((df_matches['quality'] == 'ci_u_lev_top') |\
                        (df_matches['quality'] == 'ci_u_lev_bad') |\
                        (df_matches['quality'] == 'ci_m_lev_top')) &\
                       ((df_matches['zag_br'] == df_matches['gov_br_0']) |\
                        (df_matches['zag_br'] == df_matches['gov_br_1']))]

df_output.to_csv(os.path.join(path_dir_built_csv,
                              'df_zagaz_match_0.csv'),
                 encoding = 'UTF-8')

## ###########
## DEPRECATED?
## ###########

## Distance : gouv error: 13115001 ("big" mistake still on website)
## Correct zagaz error
#dict_zagaz_stations['14439'][7] = (dict_zagaz_stations['14439'][7][0],
#                                   str(-float(dict_zagaz_stations['14439'][7][1])),
#                                   dict_zagaz_stations['14439'][7][2]) # was fixed on zagaz already
#dict_zagaz_stations['19442'][7] = (u'46.527805',
#                                   u'5.60754',
#                                   dict_zagaz_stations['19442'][7][2]) # fixed it on zagaz
#
## Stations out of France: short term fix for GFT/GMap output
#ls_temp_matching = {'4140001'  : '20101',
#                    '33830004' : '17259',
#                    '13115001' : '20072', # included in top mistakes found upon matching
#                    '20189002' : '1980',  # from here on: Corsica
#                    '20167010' : '13213',
#                    '20118004' : '13220',
#                    '20213004' : '13600',
#                    '20213003' : '17310'}
