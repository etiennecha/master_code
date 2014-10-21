#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
from functions_string import *
from BeautifulSoup import BeautifulSoup
import copy
import collections

def str_zagaz_corrections(word):
  word = word.lower()
  word = re.sub(ur'(^|\s|,)r?\.?\s?d\.?\s?([0-9]{0,5})(\s|$|,)', ur'\1 route departementale \2 \3', word)
  word = re.sub(ur'(^|\s|,)r?\.?\s?n\.?\s?([0-9]{0,5})(\s|$|,)', ur'\1 route nationale \2 \3', word) 
  return word.strip()

# LOAD ZAGAZ DATA

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')

path_dir_match_insee = os.path.join(path_data, u'data_insee', u'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_data, u'data_insee', u'data_extracts')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dir_zagaz = os.path.join(path_dir_source, 'data_stations', 'data_zagaz')

# ################
# LOAD DF ZAGAZ
# ################

df_zagaz = pd.read_csv(os.path.join(path_dir_built_csv, 'df_zagaz_stations_2012.csv'),
                       encoding='utf-8',
                       dtype = {'id_zagaz' : str,
                                'zip' : str,
                                'ci_1' : str,
                                'ci_ardt_1' : str})

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

dict_brands_update = {'OIL' : [u'AUTRE_IND', u'AUTRE_IND', u'IND'],
                      'TEXACO' : [u'AUTRE_IND', u'AUTRE_IND', u'IND'],
                      'ENI' : [u'AGIP', u'AGIP', u'OIL'],
                      'IDS': [u'AUTRE_IND', u'AUTRE_IND', u'IND'],
                      '8 A HUIT' : [u'HUIT_A_HUIT', u'CARREFOUR', u'SUP'],
                      'AS 24' : [u'AUTRE_IND', u'AUTRE_IND', u'IND'],
                      'SPAR' : [u'CASINO', u'CASINO', u'SUP'],
                      'ANTARGAZ' : [u'AUTRE_IND', u'AUTRE_IND', u'IND'],
                      'DIVERS' : [u'AUTRE_IND', u'AUTRE_IND', u'IND'],
                      'MATCH' : [u'CORA', u'CORA', u'SUP'],
                      'PRIMAGAZ' : [u'AUTRE_IND', u'AUTRE_IND', u'IND']}

# ################
# LOAD DF GOUV
# ################


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

dict_addresses = {indiv_id: [indiv_info['address'][i] for i in (5, 3, 4, 0)\
                               if indiv_info['address'][i]]\
                    for indiv_id, indiv_info in master_info.items()}
master_addresses = build_master_addresses(dict_addresses)

## MATCHING BASED ON ZIP 
#dict_matches = {}
#ls_zip_not_in_zagaz = []
#for indiv_id, indiv_addresses in master_addresses.items():
#  if indiv_addresses:
#    zip_and_city = re.match('([0-9]{5,5}) (.*)', indiv_addresses[0][1])
#    zip_code = zip_and_city.group(1)
#    if zip_code in dict_zagaz_zip.keys():
#      station_results = []
#      for (id_zagaz, address_zagaz) in dict_zagaz_zip[zip_code]:
#        ls_station_levenshtein = []
#        for address in str_low_noacc(indiv_addresses[0][0]).split(' - '):
#          for sub_address_zagaz in address_zagaz.split(' - '):
#            if not ('=' in sub_address_zagaz):
#              std_sub_address_zagaz = str_corr_low_std_noacc(sub_address_zagaz, False)
#              levenshtein_tuple = get_levenshtein_tuple(address, std_sub_address_zagaz)
#              ls_station_levenshtein.append(levenshtein_tuple)
#            else:
#              for sub_sub_address_zagaz in sub_address_zagaz.split('='):
#                std_sub_sub_address_zagaz = str_corr_low_std_noacc(sub_sub_address_zagaz, False)
#                std_sub_sub_address_zagaz = str_zagaz_corrections(std_sub_sub_address_zagaz)
#                levenshtein_tuple = get_levenshtein_tuple(address, std_sub_sub_address_zagaz)
#                ls_station_levenshtein.append(levenshtein_tuple)
#        ls_station_levenshtein = sorted(ls_station_levenshtein, key=lambda tup: tup[0])
#        station_results.append([id_zagaz] + list(ls_station_levenshtein[0]))
#      dict_matches[indiv_id] = sorted(station_results, key=lambda tup: tup[1])
#    else:
#      ls_zip_not_in_zagaz.append((zip_code, indiv_id))
#  else:
#    print indiv_id, 'no address'

# MATCHING BASED ON INSEE CODE
dict_geo_zagaz = {}
for pair in ls_matching:
  dict_geo_zagaz.setdefault(pair[-1], []).append((pair[0], pair[4]))

dict_matches = {}
ls_geo_not_in_zagaz = []
for indiv_id, indiv_info in master_price['dict_info'].items():
  if (indiv_id in master_addresses) and (master_addresses[indiv_id]): 
    indiv_addresses = master_addresses[indiv_id]
    if 'code_geo' in indiv_info:
      code_geo = indiv_info['code_geo']
      if code_geo not in dict_geo_zagaz.keys():
        code_geo = indiv_info['code_geo_ardts']
      if code_geo in dict_geo_zagaz.keys():
        station_results = []
        for (zagaz_id, zagaz_address) in dict_geo_zagaz[code_geo]:
          ls_station_levenshtein = []
          for address in str_low_noacc(indiv_addresses[0][0]).split(' - '):
            for sub_zagaz_address in zagaz_address.split(' - '):
              if not ('=' in sub_zagaz_address):
                std_sub_zagaz_address = str_corr_low_std_noacc(sub_zagaz_address, False)
                levenshtein_tuple = get_levenshtein_tuple(address, std_sub_zagaz_address)
                ls_station_levenshtein.append(levenshtein_tuple)
              else:
                for sub_sub_zagaz_address in sub_zagaz_address.split('='):
                  std_sub_sub_zagaz_address = str_corr_low_std_noacc(sub_sub_zagaz_address, False)
                  std_sub_sub_zagaz_address = str_zagaz_corrections(std_sub_sub_zagaz_address)
                  levenshtein_tuple = get_levenshtein_tuple(address, std_sub_sub_zagaz_address)
                  ls_station_levenshtein.append(levenshtein_tuple)
          ls_station_levenshtein = sorted(ls_station_levenshtein, key=lambda tup: tup[0])
          station_results.append([zagaz_id] + list(ls_station_levenshtein[0]))
        dict_matches[indiv_id] = sorted(station_results, key=lambda tup: tup[1])
      else:
         ls_geo_not_in_zagaz.append((zip_code, indiv_id))
    else:
      print indiv_id, 'no code_geo'
  else:
    print indiv_id, 'no address'
# todo: deal with short addresses ?

# Results ranked? second can be right one?
ls_accepted, ls_ambiguous, ls_rejected = [], [], []
for gouv_id, ls_matches in dict_matches.items():
  if ls_matches:
    temp_res = [[gouv_id, ls_matches[0][0]],
                [master_addresses[gouv_id][0][0], dict_zagaz_stations[ls_matches[0][0]][4]]]
    if (1 - float(ls_matches[0][1])/float(ls_matches[0][3]) >= 0.5):
      if (len(ls_matches) == 1) or\
         (ls_matches[0][1] < ls_matches[1][1]):
        ls_accepted.append(temp_res)
      else:
        ls_ambiguous.append(temp_res + [ls_matches[0][1], dict_zagaz_stations[ls_matches[1][0]][4]])
    else:
      ls_rejected.append(temp_res)
 
# Update dict_brands with zagaz specific brands
dict_brands.update(dict_brands_update)
 
# Check result quality with brand
ls_accepted_2, ls_rejected_2 = [], []
for row in ls_accepted:
  gouv_id = row[0][0]
  zagaz_id = row[0][1]
  if gouv_id in master_price['dict_info'].keys():
    ls_brand_gouv = [brand[0] for brand in master_price['dict_info'][gouv_id]['brand']]
    ls_brand_gouv = [dict_brands[brand][1] for brand in ls_brand_gouv]
    brand_zagaz = str_low_noacc(str_correct_html(dict_zagaz_stations[zagaz_id][1])).upper()
    brand_zagaz = dict_brands[brand_zagaz][1]
    if brand_zagaz not in ls_brand_gouv:
      ls_rejected_2.append([row[0], row[1:], [brand_zagaz, ls_brand_gouv]])
    else:
      ls_accepted_2.append([row[0], row[1:], [brand_zagaz, ls_brand_gouv]])
  else:
    print gouv_id, 'not in master_price'
 
# Check those present twice ? => FIX BY HAND
ls_gouv_ids = [station[0][0] for station in ls_accepted_2]
print len(ls_gouv_ids), len(set(ls_gouv_ids))
ls_zagaz_ids = [station[0][1] for station in ls_accepted_2]
print len(ls_zagaz_ids), len(set(ls_zagaz_ids)) # some attributed twice !

ls_pbms = [x for x, y in collections.Counter(ls_zagaz_ids).items() if y > 1]
for pair in ls_accepted_2:
  if pair[0][1] in ls_pbms:
    print pair
# looks like some are simply duplicates... check !

# len(ls_accepted_2) = 5988 (5869 new but total access etc?)
# todo: check double attributions + gps consistency

# Check distance for accepted
# print ls_accepted[0]
# compute_distance(master_info['75014005']['gps'][-1], dict_zagaz[u'10112'][7][0:2])
ls_distance = []
for pair in ls_accepted_2:
  gouv_id, zagaz_id = pair[0]
  # todo: use dict_ls_ids_gps (gouv else geocoding)
  if master_info[gouv_id]['gps'][4] and dict_zagaz_stations[zagaz_id][7][0:2]:
    ls_distance.append([compute_distance(master_info[gouv_id]['gps'][4],
                                        dict_zagaz_stations[zagaz_id][7][0:2])] + pair)
# shows only one address from gouv data
ls_distance = [ls_x[0:1] + ls_x[1] + ls_x[2][0] + [ls_x[3][0]] for ls_x in ls_distance]
ls_columns = ['dist', 'gouv_id', 'zagaz_id', 'ad_1', 'ad_2', 'brand_zagaz']
df_distance = pd.DataFrame(ls_distance, columns = ls_columns)

# todo: exlude highway (and corsica?)
ls_highway = [(k, v['highway'][-1]) for k,v in master_info.items()]
df_highway = pd.DataFrame(ls_highway, columns = ['id', 'highway'])
df_distance = pd.merge(df_distance, df_highway, how = 'inner', left_on = 'gouv_id', right_on ='id')
# print df_distance[df_distance['highway'] == 1].to_string()
df_distance = df_distance[df_distance['highway'] != 1]
del(df_distance['id'], df_distance['highway'])
df_distance = df_distance.sort(['dist'], ascending = [0])

print df_distance[0:100].to_string()

for row_ind, row in df_distance[0:10].iterrows():
	print row_ind, row.dist, row.gouv_id, row.zagaz_id
	print master_info[row.gouv_id]['address'][-1], master_info[row.gouv_id]['gps'][4],\
        dict_zagaz_stations[row.zagaz_id][7][0:2]

# Gouv error: 13115001 ("big" mistake still on website)
# Correct zagaz error
dict_zagaz_stations['14439'][7] = (dict_zagaz_stations['14439'][7][0],
                                   str(-float(dict_zagaz_stations['14439'][7][1])),
                                   dict_zagaz_stations['14439'][7][2]) # was fixed on zagaz already
dict_zagaz_stations['19442'][7] = (u'46.527805',
                                   u'5.60754',
                                   dict_zagaz_stations['19442'][7][2]) # fixed it on zagaz

# Stations out of France: short term fix for GFT/GMap output
ls_temp_matching = {'4140001'  : '20101',
                    '33830004' : '17259',
                    '13115001' : '20072', # included in top mistakes found upon matching
                    '20189002' : '1980',  # from here on: Corsica
                    '20167010' : '13213',
                    '20118004' : '13220',
                    '20213004' : '13600',
                    '20213003' : '17310'}

