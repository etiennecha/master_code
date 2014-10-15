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

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_info_output = os.path.join(path_dir_built_json, 'master_info_diesel_for_output.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_zagaz = os.path.join(path_dir_source, 'data_stations', 'data_zagaz')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_match_insee_codes = os.path.join(path_dir_insee, 'match_insee_codes')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info_output)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

dict_zagaz_stations = dec_json(os.path.join(path_dir_zagaz, '2012_dict_zagaz_info_gps.json'))
#dict_zagaz_all = dec_json(os.path.join(path_dir_zagaz, '20140124_zagaz_stations.json'))
#dict_zagaz_prices = dec_json(os.path.join(path_dir_zagaz, '20140127_zagaz_dict_ext_prices.json'))
#dict_zagaz_users = dec_json(os.path.join(path_dir_zagaz, '20140124_zagaz_dict_active_users.json'))

# Content of station description within dict_zagaz_stations:
# [id, brand, name, comment, street, zip_code, city, gps_tup, other?]

# Build dicts: brands, gps quality and zip
dict_zagaz_brands, dict_zagaz_gps_quality, dict_zagaz_zip = {}, {}, {}
for zagaz_id, ls_zagaz_info in dict_zagaz_stations.items():
  dict_zagaz_brands.setdefault(ls_zagaz_info[1], []).append(zagaz_id)
  dict_zagaz_gps_quality.setdefault(ls_zagaz_info[7][2], []).append(zagaz_id)
  dict_zagaz_zip.setdefault(ls_zagaz_info[5], []).append((zagaz_id, ls_zagaz_info[4]))

# Inspect Zagaz brands and look for those missing in dict_brands
dict_missing_brands = {}
for zagaz_brand, ls_zagaz_ids in dict_zagaz_brands.items():
  str_standardized_brand = str_low_noacc(str_correct_html(zagaz_brand)).upper()
  if str_standardized_brand not in dict_brands.keys():
    dict_missing_brands[str_standardized_brand] = ls_zagaz_ids
print 'Zagaz brands not in dict_brands: ', dict_missing_brands.keys()

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

# Highway: todo

# INSEE: geo code matching

# Load zip code - insee code correspondence file
file_correspondence = open(os.path.join(path_dir_match_insee_codes,
                                        'corr_cinsee_cpostal'),'r')
correspondence = file_correspondence.read().split('\n')[1:-1]
# Update changes in city codes (correspondence is a bit old)
file_correspondence_update = open(os.path.join(path_dir_match_insee_codes,
                                               'corr_cinsee_cpostal_update'),'r')
correspondence_update = file_correspondence_update.read().split('\n')[1:]
correspondence += correspondence_update
# Patch ad hoc for gas station cedexes
file_correspondence_gas_path = open(os.path.join(path_dir_match_insee_codes,
                                                 'corr_cinsee_cpostal_gas_patch'),'r')
correspondence_gas_patch = file_correspondence_gas_path.read().split('\n')
correspondence += correspondence_gas_patch
correspondence = [row.split(';') for row in correspondence]

# Two issues: 5 vs 4. chars codes and Corsica: A and B (no mistake possible in principle)
# Insee code standardized to 5 characters (but not zip code?)
for i, (commune, zip_code, department, insee_code) in enumerate(correspondence):
  if len(insee_code) == 4:
    insee_code = '0%s' %insee_code
    correspondence[i] = (commune, zip_code, department, insee_code)
# Generate dict (key: zip code) with correspondence file
dict_corr_zip_insee = {}
for (city, zip_code, department, insee_code) in correspondence:
  dict_corr_zip_insee.setdefault(zip_code, []).append((city, zip_code, department, insee_code))
# Generate dict (key: dpt code) with correspondence file
dict_corr_dpt_insee = {}
for (city, zip_code, department, insee_code)  in correspondence:
  dict_corr_dpt_insee.setdefault(zip_code[:-3], []).append((city, zip_code, department, insee_code))

# Fix zagaz data based on observed matching pbms
ls_fix_zip  = [[[u"Château-d'Olonne", u'85100'], u'85180'],
               [[u'Noiseau', u'94370'], u'94880'],
               [[u'Dompierre-sur-Chalaronne', u'01140'], u'01400'],
               [[u'Tramayes', u'71630'], u'71520'],
               [[u"La Chapelle-d'Aligné", u'72410'], u'72300'],
               [[u"Précigné", u'72410'], u'72300'],
               [[u'Saint-Mars-la-Brière', u'72680'], u'72470'],
               [[u'Saint-Cosme-en-Vairais', u'72580'], u'72110'],
               [[u'Coulanges-lès-Nevers', u'58640'], u'58660'],
               [[u'Marzy', u'58000'], u'58180'],
               [[u'Sault-Brénaz', u'01790'], u'01150'],
               [[u'Diou', u'03490'], u'03290'],
               [[u'Châtillon-sur-Colmont', u'53510'], u'53100'],
               [[u'Liginiac', u'19440'], u'19160'],
               [[u'Prunelli-di-Fiumorbo', u'20240'], u'20243'],
               [[u'Saint-Martin-de-Bonfossé', u'50860'], u'50750'],
               [[u'Saint-Hilaire', u'38720'], u'38660']]

ls_fix_city = [[[u'Périgueux', u'24750'], u'Boulazac'],
               [[u'Château-Chinon(Ville)', u'58120'], u'Château-Chinon Ville']]

for zagaz_id, ls_zagaz_info in dict_zagaz_stations.items():
  ls_zagaz_info[6] = re.sub(ur'^Paris 0([1-9])eme$', ur'Paris \1eme', ls_zagaz_info[6])
  ls_zagaz_info[6] = re.sub(ur'^Paris 01er$', ur'Paris 1er', ls_zagaz_info[6])
  ls_zagaz_info[6] = ls_zagaz_info[6].replace(u'\x9c', u'oe')
  for (zagaz_city, zagaz_zip_code_bad), zagaz_zip_code_good in ls_fix_zip:
    if ls_zagaz_info[6] == zagaz_city and ls_zagaz_info[5] == zagaz_zip_code_bad:
      ls_zagaz_info[5] = zagaz_zip_code_good
  for (zagaz_city_bad, zagaz_zip_code), zagaz_city_good in ls_fix_city:
    if ls_zagaz_info[6] == zagaz_city_bad and ls_zagaz_info[5] == zagaz_zip_code:
      ls_zagaz_info[6] = zagaz_city_good
  dict_zagaz_stations[zagaz_id] = ls_zagaz_info
 
# Check best matching based on zip: first if same city name then if contained
ls_matching = []
ls_not_matched = []
ls_zip_code_pbm = []
for zagaz_id, ls_zagaz_info in dict_zagaz_stations.items():
  zip_code, city = ls_zagaz_info[5], ls_zagaz_info[6]
  found_indicator = False
  if zip_code in dict_corr_zip_insee:
    for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
      if str_insee_harmonization(str_low_noacc(city)) == str_insee_harmonization(city_insee):
        ls_matching.append(ls_zagaz_info + [code_insee])
        found_indicator = True
        break
    if not found_indicator:
      for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
        if str_insee_harmonization(str_low_noacc(city)) in str_insee_harmonization(city_insee):
          ls_matching.append(ls_zagaz_info + [code_insee])
          print 'Matched', city, city_insee, zip_insee
          found_indicator = True
          break
    if not found_indicator:
      print zagaz_id, zip_code, city
      print 'Could not match', str_insee_harmonization(str_low_noacc(city))
      ls_not_matched.append(ls_zagaz_info)
  else:
    print 'Zip code not in corresp:', zip_code, str_insee_harmonization(str_low_noacc(city))
    ls_zip_code_pbm.append(ls_zagaz_info)

# enc_json(ls_matching, path_data + folder_source_zagaz_std + r'\2012_zagzag_stations')

# BUILD DF ZAGAZ
# No brand harmonization for now
ls_rows = []
for zagaz_station in ls_matching:
  ls_rows.append(zagaz_station[:7] + list(zagaz_station[7]) + zagaz_station[8:10])
ls_columns = ['id', 'brand', 'name', 'comment', 'street', 'zip', 'city',
              'lon', 'lat', 'quality', 'highway', 'code_geo'] 
df_zagaz = pd.DataFrame(ls_rows, columns = ls_columns)
ls_quality = [u"Ces coordonn\xe9es n'ont pas \xe9t\xe9 v\xe9rifi\xe9es et sont sujettes \xe0 caution",
              u'Ces coordonn\xe9es ont \xe9t\xe9 v\xe9rifi\xe9es par un internaute']
df_zagaz['quality'] = df_zagaz['quality'].apply(lambda x: x if x != ls_quality[0] else 'Unverified')
df_zagaz['quality'] = df_zagaz['quality'].apply(lambda x: x if x != ls_quality[1] else 'Unverified')
df_zagaz['gps'] = df_zagaz['lon'].str.cat(df_zagaz['lat'], sep = ' ')
del(df_zagaz['lon'], df_zagaz['lat'])

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

