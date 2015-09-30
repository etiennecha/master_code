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

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_scraped_2011_2014')

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_dir_built_json = os.path.join(path_dir_built_paper,
                                   u'data_json')

path_dir_match_insee = os.path.join(path_data, u'data_insee', u'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_data, u'data_insee', u'data_extracts')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dir_zagaz = os.path.join(path_dir_source, 'data_stations', 'data_zagaz')

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


dict_brands = dec_json(os.path.join(path_dir_source, 'data_other', 'dict_brands.json'))

# TODO: INTEGRATE IN BUILD DF ZAGAZ
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
dict_brands.update(dict_brands_update)
df_zagaz['brand'] = df_zagaz['brand'].apply(\
                      lambda x: dict_brands.get(str_low_noacc(x).upper(), [None, None])[0])

# NORMALIZATION FOR MATCHING
dict_brands_std = {v[0]: v[1:] for k,v in dict_brands.items()}
dict_brands_norm = {u'SHOPI': [u'CARREFOUR', u'GMS'],
                    u'CARREFOUR_CONTACT': [u'CARREFOUR', u'GMS'],
                    u'ECOMARCHE' : [u'MOUSQUETAIRES', u'GMS'],
                    u'INTERMARCHE_CONTACT' : [u'MOUSQUETAIRES', u'GMS'],
                    u'INTERMARCHE' : [u'MOUSQUETAIRES', u'GMS'],
                    u'ESSO_EXPRESS' : [u'ESSO', u'OIL']}
dict_brands_std.update(dict_brands_norm)

df_zagaz['brand'] = df_zagaz['brand'].apply(\
                      lambda x: dict_brands_std.get(x, [None, None])[0])

# ################
# LOAD DF GOUV
# ################

# duplicates within master_info... (hence might match dropped ids)
master_info = dec_json(os.path.join(path_dir_built_json, 'master_info_fixed.json'))


dict_addresses = {indiv_id: [indiv_info['address'][i] for i in (8, 7, 6, 5, 3, 4, 0)\
                               if indiv_info['address'][i]]\
                    for indiv_id, indiv_info in master_info.items()}
master_addresses = build_master_addresses(dict_addresses)

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
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

for field_brand in ['brand_0', 'brand_1',  'brand_2']:
  df_info[field_brand] = df_info[field_brand].apply(\
                              lambda x: dict_brands_std.get(x, [None, None])[0])

# #############
# LOAD MATCH 0
# #############

df_zagaz_match_0 = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_zagaz_match_0.csv'),
                               dtype = {'zag_id' : str,
                                        'gov_id' : str,
                                        'ci' : 'str'},
                               encoding = 'UTF-8')
ls_unmatched_gov_ids = [gov_id for gov_id in df_info.index\
                           if gov_id not in df_zagaz_match_0['gov_id'].values]
ls_unmatched_zag_ids = [zag_id for zag_id in df_zagaz.index\
                           if zag_id not in df_zagaz_match_0['zag_id'].values]

df_info_um = df_info.ix[ls_unmatched_gov_ids].copy()
df_zagaz_um = df_zagaz.ix[ls_unmatched_zag_ids].copy()

ls_cols = 0
dict_no_match = {'zag_ci_n' : [],
                 'zag_ci_m_nbr' : [],
                 'zag_ci_m_mbr' : []} # several in ci, several of same brand
dict_matching_quality = {'zag_ci_u_ebr' : [],
                         'zag_ci_u_dbr' : [], # diff brand, match but not good?
                         'zag_ci_m_ebr' : []} # several in ci but only one of same brand
for gov_id, gov_station in df_info_um.iterrows():
  gov_station_ci = gov_station['ci_1']
  brand_station = gov_station['brand_0']
  df_zagaz_ci = df_zagaz_um[df_zagaz_um['ci_1'] == gov_station_ci]
  if len(df_zagaz_ci) == 0:
    dict_no_match['zag_ci_n'].append(gov_id)
  elif len(df_zagaz_ci) == 1:
    if len(df_zagaz_ci[df_zagaz_ci['brand'] == brand_station]) == 1:
      dict_matching_quality['zag_ci_u_ebr'].append((gov_id,
                                                    df_zagaz_ci.index[0]))
    else:
      dict_matching_quality['zag_ci_u_dbr'].append((gov_id,
                                                    df_zagaz_ci.index[0]))
  else:
    df_zagaz_ci_br = df_zagaz_ci[df_zagaz_ci['brand'] == brand_station]
    if len(df_zagaz_ci_br) == 0:
      dict_no_match['zag_ci_m_nbr'].append(gov_id)
    elif len(df_zagaz_ci_br) == 1:
      dict_matching_quality['zag_ci_m_ebr'].append((gov_id,
                                                    df_zagaz_ci_br.index[0]))
    else:
      dict_no_match['zag_ci_m_mbr'].append(gov_id)

for k, v in dict_matching_quality.items():
	print k, len(v)

for k, v in dict_no_match.items():
	print k, len(v)

# Not many no match left... but probably quite a few duplicates
# Clean results first, then finish

# ################
# BUILD DF RESULTS
# ################

ls_hand_matching = [('10210001', '15803'),
                    ('10270003',   '679'), # Total => Carrefour
                    ('11390001', '15657'),
                    ('11590001',   '757'), 
                    ('1250001' ,    '35'),
                    ('1250002' ,    '63'),
                    ('12780002',   '908'),
                    ('13130006',   '976'),
                    ('1360001' , '19981'), # duplicates?
                    ('1360002' , '19981'),
                    ('14760001',  '1263'),
                    ('15290001',  '1426'),
                    ('15500002', '13814'),
                    ('16230002',  '1544'),
                    ('16270001',  '1560'),
                    ('16400002', '13592'),
                    ('16400002', '13592'), # check
                    ('17110001',  '1705'),
                    ('17120002',  '1610'),
                    ('17139002', '13984'),
                    ('17160002', '18328'),
                    ('17360001',  '1693'),
                    ('17420001',  '1720'),
                    ('19800001',  '1908'),
                    ('20156001',  '2086'),
                    ('21240001',  '2222'),
                    ('21800006',  '2197'),
                    ('22290003', '15762'),
                    ('22400002',  '2254'),
                    ('24160001',  '2592'),
                    ('24170002',  '2607'),
                    ('25420004', '14978'),
                    ('26170001', '18955'),
                    ('27350003',  '3012'),
                    ('27930003',  '2948'),
                    ('2880001' ,   '156'),
                    ('29160001',  '3213'),
                    ('30210005',  '3461'), # check
                    ('30340002',  '3540'),
                    ('30960001',  '3474'),
                    ('31240005',  '3630'),
                    ('31420001', '18693'), # duplicates? 
                    ('31420002', '18693'), # duplicates?
                    ('32340001', '17370'), # check
                    ('32460001', '17387'), # check
                    ('32730003',  '3851'),
                    ('33260010', '20220'), # check
                    ('33290005',  '3890'),
                    ('33480004', '13991'),
                    ('33490001',  '4100'), # check
                    ('34160001',  '4184'),
                    ('34320003', '14487'), # check
                    ('34620001',  '4299'), # check
                    ('34670001',  '4155'), # check
                    ('35111001', '18218'), # check
                    ('35800001', '16640'),
                    ('35850004', '18725'), # end of 0:100
                    ('36110001',  '4621'),
                    ('36290001', '17537'),
                    ('37370001',  '4766'),
                    ('38450001',  '5004'), # check
                    ('38570001', '15002'),
                    ('38850001',  '4840'), # check
                    ('38850002',  '4835'),
                    ('39170001',  '5100'),
                    ('39230004', '16818'), # check
                    ('39570007', ' 5087'),
                    ('40140001', '15853'),
                    ('40280004',  '5173'),
                    ('40420003',  '5140'), # check
                    ('4120002',  '19752'), # check
                    ('44115001',  '5573'),
                    ('44260003', '14170'), # check
                    ('47300002', '15769'),
                    ('49360001',  '6332'),
                    ('50690001',  '6489'), # check
                    ('51800004', '15968'), # check
                    ('52400003', '16055'),
                    ('56170001',  '7217'), # check
                    ('56350003',  '7038'), # check
                    ('57660001', '15228'),
                    ('59110002',  '7649'),
                    ('59223002',  '7729'),
                    ('59260001',  '7668'),
                    ('59279002', '15177'), 
                    ('59370003', '13108'),
                    ('59510002',  '7638'),
                    ('59850002',  '7707'),
                    ('60270002', '15825'),
                    ('60300006', '15321'), # check just with ids
                    ('60350001',  '7864'),
                    ('62250006',  '8225'),
                    ('62770001',  '8058')] # check, end of 100:200

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

ls_ma_di_0 = ['gov_id', 'zag_id',
              'gov_street', 'zag_street',
              'gov_br_0', 'gov_br_1', 'zag_br', 'dist']

ls_ma_di_1 = ['gov_id', 'zag_id', 'gov_city', 'zag_city',
              'gov_street', 'zag_street',
              'gov_br_0', 'gov_br_1', 'zag_br', 'dist']

# may not want to keep one result but diff brand?
print '\n One match in ci, different brands:'
print df_matches[ls_ma_di_0][df_matches['quality'] == 'zag_ci_u_dbr'].to_string()
# todo: drop this from final matching and keep only handpicked selection

print '\n One match in ci, same brands:'
print df_matches[ls_ma_di_0][df_matches['quality'] == 'zag_ci_u_ebr'][0:200].to_string()

print '\n Mult match in ci, only one w/ same brande:'
print df_matches[ls_ma_di_0][df_matches['quality'] == 'zag_ci_m_ebr'][0:200].to_string()

# ############################
# DF OUTPUT (DF ZAGAZ MATCH 1)
# ############################

# todo:
# add matches manually detected

df_output = pd.concat([df_zagaz_match_0,
                       df_matches[df_matches['quality'] != 'zag_ci_u_dbr']])
print df_output[ls_ma_di_1][0:10].to_string()

# Inspect duplicates (can be only in zagaz)
se_zag_id_vc = df_output['zag_id'].value_counts()
se_zag_id_dup = se_zag_id_vc[se_zag_id_vc > 1]

df_duplicates = df_output.copy()
df_duplicates.set_index('zag_id', inplace = True)
# caution: diff from .ix[] which does not get all
df_duplicates = df_duplicates.loc[se_zag_id_dup.index]
df_duplicates.reset_index(inplace = True)
# might have want to be more careful before
pd.set_option('display.max_colwidth', 30)
print df_duplicates[ls_ma_di_1][0:100].to_string()

## #######################
## MATCHING GOUV VS. ZAGAZ
## #######################
#
## Strategy 1: within similar ZIP, compare standardized address 
##             + check on name station (print) if score is ambiguous
## Strategy 2: compare standardized string: address, ZIP, City
#
## Standardization: suppress '-' (?), replace ' st ' by 'saint'
## master: 26200005, 40390001 (C/C => Centre Commercial ?), 35230001, 13800007 (Av. => Avenue)
## master: 67540002 (\\ => ), 59860002 (386/388 => 386/388 (?))
## master: lack of space (not necessarily big pbm) 78120010
## check weird : 18000014, 82500001, 58240002
#
## loop on all zagaz stations within zip code area
## loop on all master sub-adresses vs. zagaz sub-addresses: keep best match
## produces a list with best match for each zagaz station within zip code are
## can be more than 2 components... some seem to have standard format DXXX=NXX
#
## To make comparison easier
#df_zagaz.loc[pd.isnull(df_zagaz['street']), 'street'] = u''
#
## MATCHING BASED ON INSEE CODE
#dict_matches = {}
#ls_ci_not_in_zag = []
#for gov_id, gov_row in df_info.iterrows():
#  if master_addresses.get(gov_id, None):
#    gov_addresses = master_addresses[gov_id]
#    # check if any zagaz station has same ci
#    if gov_row['ci_1'] in df_zagaz['ci_1'].unique():
#      ls_station_results = []
#      # loop on zagaz stations with same ci
#      for zag_id, zag_row in df_zagaz[df_zagaz['ci_1'] == gov_row['ci_1']].iterrows():
#        ls_station_levenshtein = []
#        # want to compare each sub gov address
#        for gov_street in str_low_noacc(gov_row['adr_street']).split(' - '):
#          for zag_street in zag_row['street'].split(' - '):
#            if not ('=' in zag_street):
#              std_zag_street = str_corr_low_std_noacc(zag_street, False)
#              levenshtein_tuple = get_levenshtein_tuple(gov_street, std_zag_street)
#              ls_station_levenshtein.append(levenshtein_tuple)
#            else:
#              for sub_zag_street in zag_street.split('='):
#                std_sub_zag_street = str_corr_low_std_noacc(sub_zag_street, False)
#                std_sub_zag_street = str_zagaz_corrections(std_sub_zag_street)
#                levenshtein_tuple = get_levenshtein_tuple(gov_street, std_sub_zag_street)
#                ls_station_levenshtein.append(levenshtein_tuple)
#        ls_station_levenshtein = sorted(ls_station_levenshtein, key=lambda tup: tup[0])
#        ls_station_results.append([zag_id] + list(ls_station_levenshtein[0]))
#      dict_matches[gov_id] = sorted(ls_station_results, key=lambda tup: tup[1])
#    else:
#      ls_ci_not_in_zag.append(gov_id)
#  else:
#    print gov_id, 'no address'
#
## Results are ranked based on first but if short... second could be right one
#dict_matching_quality = {}
#for gov_id, ls_matches in dict_matches.items():
#  if not ls_matches:
#    pass
#  elif len(ls_matches) == 1:
#    if ls_matches[0][1] == 0:
#      dict_matching_quality.setdefault('ci_u_lev_top', []).append((gov_id, ls_matches[0][0]))
#    elif (min(*ls_matches[0][2:4]) >= 8) and\
#        (1 - float(ls_matches[0][1])/float(ls_matches[0][3]) >= 0.5):
#      dict_matching_quality.setdefault('ci_u_lev_ok', []).append((gov_id, ls_matches[0][0]))
#    else:
#      dict_matching_quality.setdefault('ci_u_lev_bad', []).append((gov_id, ls_matches[0][0]))
#  else:
#    if ls_matches[0][1] == 0:
#      dict_matching_quality.setdefault('ci_m_lev_top', []).append((gov_id, ls_matches[0][0]))
#    elif (min(*ls_matches[0][2:4]) >= 8) and\
#        (1 - float(ls_matches[0][1])/float(ls_matches[0][3]) >= 0.5):
#      dict_matching_quality.setdefault('ci_m_lev_ok', []).append((gov_id, ls_matches[0][0]))
#    else:
#      dict_matching_quality.setdefault('ci_m_lev_bad', []).append((gov_id, ls_matches[0][0]))
#
## Build df results (slight pbm... not gov address from master_address but df_info)
#ls_rows_matches = []
#for quality, ls_matches in dict_matching_quality.items():
#  for gov_id, zag_id in ls_matches:
#    ls_rows_matches.append([quality,
#                            gov_id,
#                            zag_id] +\
#                           list(df_info.ix[gov_id][['adr_street',
#                                                    'adr_city',
#                                                    'brand_0',
#                                                    'brand_1',
#                                                    'lat_gov_1',
#                                                    'lng_gov_1',
#                                                    'ci_1']]) +\
#                           list(df_zagaz.ix[zag_id][['street',
#                                                     'city',
#                                                     'brand',
#                                                     'lat',
#                                                     'lng']]))
#
#ls_columns = ['quality', 'gov_id', 'zag_id',
#              'gov_street', 'gov_city',
#              'gov_br_0', 'gov_br_1', 'gov_lat', 'gov_lng', 'ci',
#              'zag_street', 'zag_city',
#              'zag_br', 'zag_lat', 'zag_lng']
#df_matches = pd.DataFrame(ls_rows_matches,
#                          columns = ls_columns)
#
#df_matches['dist'] = df_matches.apply(\
#                           lambda x: compute_distance(\
#                                            (x['gov_lat'], x['gov_lng']),
#                                            (x['zag_lat'], x['zag_lng'])), axis = 1)
#
## todo: check on brand (flexibility?) + gps coordinates
## get rid of pbms by observation
## then restart procss on remaining stations
#
## CHECK RESULT QUALITY WITH BRAND / GROUP
#
## Update dict_brands with zagaz specific brands
#dict_brands.update(dict_brands_update)
#
#df_matches['zag_br'] = df_matches['zag_br'].apply(\
#                         lambda x: dict_brands[str_low_noacc(x).upper()][0])
#
## Further normalize brands (applied to standardized brands)
#dict_brands_norm = {u'SHOPI': [u'CARREFOUR', u'GMS'],
#                    u'CARREFOUR_CONTACT': [u'CARREFOUR', u'GMS'],
#                    u'ECOMARCHE' : [u'MOUSQUETAIRES', u'GMS'],
#                    u'INTERMARCHE_CONTACT' : [u'MOUSQUETAIRES', u'GMS'],
#                    u'INTERMARCHE' : [u'MOUSQUETAIRES', u'GMS'],
#                    u'ESSO_EXPRESS' : [u'ESSO', u'OIL']}
#dict_brands_std.update(dict_brands_norm)
#for field_brand in ['zag_br', 'gov_br_0', 'gov_br_1']:
#  df_matches[field_brand] = df_matches[field_brand].apply(\
#                              lambda x: dict_brands_std.get(x, [None, None])[0])
#
## Top quality
#print '\nMatched (top) and same brand:',\
#      len(df_matches[((df_matches['quality'] == 'ci_u_lev_top') |\
#                      (df_matches['quality'] == 'ci_m_lev_top')) &\
#                     ((df_matches['zag_br'] == df_matches['gov_br_0']) |\
#                      (df_matches['zag_br'] == df_matches['gov_br_1']))])
#
#print 'Matched (top) and diff brand:',\
#      len(df_matches[((df_matches['quality'] == 'ci_u_lev_top') |\
#                      (df_matches['quality'] == 'ci_m_lev_top')) &\
#                     (df_matches['zag_br'] != df_matches['gov_br_0']) &\
#                     (df_matches['zag_br'] != df_matches['gov_br_1'])])
#
## Different brand: really not to be matched?
#
#ls_ma_di_0 = ['gov_id', 'zag_id',
#              'gov_street', 'zag_street',
#              'gov_br_0', 'gov_br_1', 'zag_br', 'dist']
#
#print df_matches[ls_ma_di_0][((df_matches['quality'] == 'ci_u_lev_top') |\
#                               (df_matches['quality'] == 'ci_m_lev_top')) &\
#                              (df_matches['zag_br'] != df_matches['gov_br_0']) &\
#                              (df_matches['zag_br'] != df_matches['gov_br_1'])].to_string()
#
## Unique possibility at code insee level but matching not great: just diff address?
#
#pd.set_option('display.max_colwidth', 30)
#
#print '\nMatched (bad) but unique at insee code level and same brand:',\
#      len(df_matches[(df_matches['quality'] == 'ci_u_lev_bad') &\
#                     ((df_matches['zag_br'] == df_matches['gov_br_0']) |\
#                      (df_matches['zag_br'] == df_matches['gov_br_1']))])
#
#ls_ma_di_1 = ['gov_id', 'zag_id', 'gov_city', 'zag_city',
#              'gov_street', 'zag_street',
#              'gov_br_0', 'gov_br_1', 'zag_br', 'dist']
#
#print df_matches[ls_ma_di_1][(df_matches['quality'] == 'ci_u_lev_bad') &\
#                             ((df_matches['zag_br'] == df_matches['gov_br_0']) |\
#                              (df_matches['zag_br'] == df_matches['gov_br_1']))].to_string()
#
#print '\nMatched (bad) but unique at insee code level and diff brand:',\
#      len(df_matches[(df_matches['quality'] == 'ci_u_lev_bad') &\
#                     (df_matches['zag_br'] != df_matches['gov_br_0']) &\
#                     (df_matches['zag_br'] != df_matches['gov_br_1'])])
#
#print df_matches[ls_ma_di_1][(df_matches['quality'] == 'ci_u_lev_bad') &\
#                             (df_matches['zag_br'] != df_matches['gov_br_0']) &\
#                             (df_matches['zag_br'] != df_matches['gov_br_1'])].to_string()
#
## OUTPUT ACCEPTED MATCHES
#df_output = df_matches[((df_matches['quality'] == 'ci_u_lev_top') |\
#                        (df_matches['quality'] == 'ci_u_lev_bad') |\
#                        (df_matches['quality'] == 'ci_m_lev_top')) &\
#                       ((df_matches['zag_br'] == df_matches['gov_br_0']) |\
#                        (df_matches['zag_br'] == df_matches['gov_br_1']))]
#
#df_output.to_csv(os.path.join(path_dir_built_csv,
#                              'df_match_zagaz_0.csv'),
#                 encoding = 'UTF-8')
#
### ###########
### DEPRECATED?
### ###########
#
### Distance : gouv error: 13115001 ("big" mistake still on website)
### Correct zagaz error
##dict_zagaz_stations['14439'][7] = (dict_zagaz_stations['14439'][7][0],
##                                   str(-float(dict_zagaz_stations['14439'][7][1])),
##                                   dict_zagaz_stations['14439'][7][2]) # was fixed on zagaz already
##dict_zagaz_stations['19442'][7] = (u'46.527805',
##                                   u'5.60754',
##                                   dict_zagaz_stations['19442'][7][2]) # fixed it on zagaz
##
### Stations out of France: short term fix for GFT/GMap output
##ls_temp_matching = {'4140001'  : '20101',
##                    '33830004' : '17259',
##                    '13115001' : '20072', # included in top mistakes found upon matching
##                    '20189002' : '1980',  # from here on: Corsica
##                    '20167010' : '13213',
##                    '20118004' : '13220',
##                    '20213004' : '13600',
##                    '20213003' : '17310'}
