#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re
import json
import pprint
from BeautifulSoup import BeautifulSoup
import copy

def enc_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def get_dict_stat(list_items):
  dict_stats = {}
  for item in list_items:
    if item in dict_stats.keys():
      dict_stats[item] += 1
    else:
      dict_stats[item] = 1
  return dict_stats

if __name__=="__main__":
  # path_data: data folder at different locations at CREST vs. HOME
  # could do the same for path_code if necessary (import etc).
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
    path_code = r'W:\Bureau\Etienne_work\Code'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  
  sys.path.append(r'W:\Bureau\Etienne_work\Code\code_gasoline\code_gasoline_db_analysis')
  from functions_string import *
  
  folder_source_zagaz_raw = r'\data_gasoline\data_source\data_stations\data_zagaz\raw'
  folder_source_zagaz_std = r'\data_gasoline\data_source\data_stations\data_zagaz\std'  
  ls_zagaz_info_stations_raw = dec_json(path_data + folder_source_zagaz_raw + r'\zagzag_info_and_gps_stations')
  
  folder_source_brand = r'\data_gasoline\data_source\data_stations\data_brands'
  dict_brands = dec_json(path_data + folder_source_brand + r'\dict_brands')
  
  # folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  # master_info = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_info_diesel')
  # master_price = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')  
  
  # #####################
  # CLEANING ZAGAZ DATA
  # #####################
  
  ls_ls_zagaz_stations = []
  dict_zagaz = {}
  for i, station in enumerate(ls_zagaz_info_stations_raw):
    href_string = BeautifulSoup(station[0][0])\
                    .find('a', {'href' : re.compile('station.php\?id_s*')})['href']
    id_station = re.search('station.php\?id_s=([0-9]*)', href_string).group(1)
    highway =  BeautifulSoup(station[0][0])\
                    .find('a', {'href' : re.compile('autoroute.php\?id_a*')})
    if highway:
      highway = highway['title']
    brand_and_name_station = BeautifulSoup(station[0][0])('strong')[0].string
    # check if other ('strong') with highway?
    brand_station = brand_and_name_station.split('&nbsp;-&nbsp;')[0]
    name_station = brand_and_name_station.split('&nbsp;-&nbsp;')[1]
    street_station = str_correct_html(BeautifulSoup(station[0][1])('p')[0].string)
    zip_station = BeautifulSoup(station[0][2])('p')[0].contents[0].strip()
    city_station = str_correct_html(BeautifulSoup(station[0][2])\
                    .find('a', {'href' : re.compile('prix-carburant.php*')}).string)
    if station[1]:
      comment_station = BeautifulSoup(station[1][0]).find('div', {'class' : 'station_comm'}).string
    else:
      comment_station = None
    latitude = re.search('Latitude: ([0-9.]*)', station[2][0])
    longitude = re.search('longitude: ([0-9.]*)', station[2][0])
    if latitude and longitude:
      gps_station = (latitude.group(1), longitude.group(1), station[2][1])
    else:
      gps_station = (None, None, None)
    ls_zagaz_station = [id_station,
                                  brand_station,
                                  name_station,
                                  comment_station,
                                  street_station,
                                  zip_station,
                                  city_station,
                                  gps_station,
                                  highway]
    ls_ls_zagaz_stations.append(ls_zagaz_station)
    dict_zagaz[id_station] = ls_zagaz_station
  # enc_json(dict_zagaz, path_data + folder_source_zagaz_std + r'\zagzag_info_and_gps_stations')
  
  # brands and gps quality in zagaz
  dict_zagaz_brands = get_dict_stat([ls_zagaz_station[1] for ls_zagaz_station in ls_ls_zagaz_stations])
  dict_zagaz_gps_quality = get_dict_stat([ls_zagaz_station[7][2] for ls_zagaz_station \
                                            in ls_ls_zagaz_stations if ls_zagaz_station[7]])
  
  # build a dict_zagzag id keys (now redundant with dict_zagaz)
  dict_id_zagaz = {}
  for ls_zagaz_station in ls_ls_zagaz_stations:
    dict_id_zagaz.setdefault(ls_zagaz_station[0], []).append((ls_zagaz_station[2], 
                                                              ls_zagaz_station[4], 
                                                              ls_zagaz_station[5], 
                                                              ls_zagaz_station[6]))
  
  # build a dict_zagzag zip keys
  dict_zip_zagaz = {}
  for ls_zagaz_station in ls_ls_zagaz_stations:
    dict_zip_zagaz.setdefault(ls_zagaz_station[5], []).append((ls_zagaz_station[0],
                                                               ls_zagaz_station[4]))              
  
  # ########
  # BRANDS
  # ########
  
  dict_brands_not_in_dict_brands = {}
  for ls_zagaz_station in ls_ls_zagaz_stations:
    str_standardized_brand = str_low_noacc(str_correct_html(ls_zagaz_station[1])).upper()
    if str_standardized_brand not in dict_brands.keys():
      dict_brands_not_in_dict_brands.setdefault(str_standardized_brand, []).append(ls_zagaz_station)
  print 'Zagaz brands not in dict_brands: ', dict_brands_not_in_dict_brands.keys()
  
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
  
  # ###############
  # HIGHWAY (TODO)
  # ###############
  
  # ###############
  # INSEE MATCHING
  # ###############
  
  # Load zip code - insee code correspondence file
  file_correspondence = open(path_data + r'\data_insee\corr_cinsee_cpostal','r')
  correspondence = file_correspondence.read().split('\n')[1:-1]
  # Update changes in city codes (correspondence is a bit old)
  file_correspondence_update = open(path_data + r'\data_insee\corr_cinsee_cpostal_update','r')
  correspondence_update = file_correspondence_update.read().split('\n')[1:]
  correspondence += correspondence_update
  # Patch ad hoc for gas station cedexes
  file_correspondence_gas_path = open(path_data + r'\data_insee\corr_cinsee_cpostal_gas_patch','r')
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
  
  for i, zagaz_station in enumerate(ls_ls_zagaz_stations):
    ls_ls_zagaz_stations[i][6] = re.sub(ur'^Paris 0([1-9])eme$', ur'Paris \1eme', zagaz_station[6])
    ls_ls_zagaz_stations[i][6] = re.sub(ur'^Paris 01er$', ur'Paris 1er', zagaz_station[6])
    ls_ls_zagaz_stations[i][6] = zagaz_station[6].replace(u'\x9c', u'oe')
    if zagaz_station[6] == u"Château-d'Olonne" and zagaz_station[5] == '85100':
      ls_ls_zagaz_stations[i][5] = u'85180'
    if zagaz_station[6] == u'Noiseau' and zagaz_station[5] == '94370':
      ls_ls_zagaz_stations[i][5] = u'94880'
    if zagaz_station[6] == u'Dompierre-sur-Chalaronne' and zagaz_station[5] == '01140':
      ls_ls_zagaz_stations[i][5] = u'01400'
    if zagaz_station[6] == u'Tramayes' and zagaz_station[5] == '71630':
      ls_ls_zagaz_stations[i][5] = u'71520'
    if zagaz_station[6] == u"La Chapelle-d'Aligné" and zagaz_station[5] == '72410':
      ls_ls_zagaz_stations[i][5] = u'72300'
    if zagaz_station[6] == u"Précigné" and zagaz_station[5] == '72410':
      ls_ls_zagaz_stations[i][5] = u'72300'
    if zagaz_station[6] == u'Saint-Mars-la-Brière' and zagaz_station[5] == '72680':
      ls_ls_zagaz_stations[i][5] = u'72470'
    if zagaz_station[6] == u'Saint-Cosme-en-Vairais' and zagaz_station[5] == '72580':
      ls_ls_zagaz_stations[i][5] = u'72110'
    if zagaz_station[6] == u'Coulanges-lès-Nevers' and zagaz_station[5] == '58640':
      ls_ls_zagaz_stations[i][5] = u'58660'
    if zagaz_station[6] == u'Marzy' and zagaz_station[5] == '58000':
      ls_ls_zagaz_stations[i][5] = u'58180'
    if zagaz_station[6] == u'Sault-Brénaz' and zagaz_station[5] == '01790':
      ls_ls_zagaz_stations[i][5] = u'01150'
    if zagaz_station[6] == u'Diou' and zagaz_station[5] == '03490':
      ls_ls_zagaz_stations[i][5] = u'03290'
    if zagaz_station[6] == u'Châtillon-sur-Colmont' and zagaz_station[5] == '53510':
      ls_ls_zagaz_stations[i][5] = u'53100'
    if zagaz_station[6] == u'Liginiac' and zagaz_station[5] == '19440':
      ls_ls_zagaz_stations[i][5] = u'19160'
    if zagaz_station[6] == u'Prunelli-di-Fiumorbo' and zagaz_station[5] == '20240':
      ls_ls_zagaz_stations[i][5] = u'20243'
    if zagaz_station[6] == u'Saint-Martin-de-Bonfossé' and zagaz_station[5] == '50860':
      ls_ls_zagaz_stations[i][5] = u'50750'
    if zagaz_station[6] == u'Saint-Hilaire' and zagaz_station[5] == '38720':
      ls_ls_zagaz_stations[i][5] = u'38660'
    if zagaz_station[6] == u'Périgueux' and zagaz_station[5] == '24750':
      ls_ls_zagaz_stations[i][6] = u'Boulazac'
    if zagaz_station[6] == u'Château-Chinon(Ville)' and zagaz_station[5] == '58120':
      ls_ls_zagaz_stations[i][6] = u'Château-Chinon Ville'
  
  # Check best matching based on zip: first if same city name then if contained
  ls_matching = []
  ls_not_matched = []
  ls_zip_code_pbm = []
  for zagaz_station in ls_ls_zagaz_stations:
    zip_code = zagaz_station[5]
    city = zagaz_station[6]
    found_indicator = False
    if zip_code in dict_corr_zip_insee:
      for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
        if str_insee_harmonization(str_low_noacc(city)) == str_insee_harmonization(city_insee):
          ls_matching.append(zagaz_station + [code_insee])
          found_indicator = True
          break
      if not found_indicator:
        for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
          if str_insee_harmonization(str_low_noacc(city)) in str_insee_harmonization(city_insee):
            ls_matching.append(zagaz_station + [code_insee])
            print 'Matched', city, city_insee, zip_insee
            found_indicator = True
            break
      if not found_indicator:
        print zagaz_station[0], zagaz_station[5], zagaz_station[6]
        print 'Could not match', str_insee_harmonization(str_low_noacc(city))
        ls_not_matched.append(zagaz_station)
    else:
      print 'Zip code not in correspondence:', zip_code, str_insee_harmonization(str_low_noacc(city))
      ls_zip_code_pbm.append(zagaz_station)
  
  # TODO: Correct Paris and small cities
  # PBM: may not work for all (not registered with same city/zip in zagaz and gouv)
  # SOLUTION: Could look with UU or UA... less risk
  
  # # #######################
  # # MATCHING GOUV VS. ZAGAZ
  # # #######################
  
  # # Strategy 1: within similar ZIP, compare standardized address 
  # #             + check on name station (print) if score is ambiguous
  # # Strategy 2: compare standardized string: address, ZIP, City

  # # Standardization: suppress '-' (?), replace ' st ' by 'saint'
  # # master: 26200005, 40390001 (C/C => Centre Commercial ?), 35230001, 13800007 (Av. => Avenue)
  # # master: 67540002 (\\ => ), 59860002 (386/388 => 386/388 (?))
  # # master: lack of space (not necessarily big pbm) 78120010
  # # check weird : 18000014, 82500001, 58240002
  
  # # loop on all zagaz stations within zip code area
  # # loop on all master sub-adresses vs. zagaz sub-addresses: keep best match
  # # produces a list with best match for each zagaz station within zip code are
  # # can be more than 2 components... some seem to have standard format DXXX=NXX

  # list_zip_not_in_zagaz = []
  # list_info_levenshtein = []
  # for id, station in master_addresses_final.iteritems():
    # if station:
      # zip_and_city = re.match('([0-9]{5,5}) (.*)', station[0][1])
      # zip = zip_and_city.group(1)
      # if zip in dict_zip_zagaz.keys():
        # station_results = []
        # for (id_zagaz, address_zagaz) in dict_zip_zagaz[zip]:
          # for address in str_low_noacc(station[0][0]).split(' - '):
            # list_station_levenshtein = []
            # for sub_address_zagaz in address_zagaz.split(' - '):
              # if not ('=' in sub_address_zagaz) or\
                # all('=' in e for e in address_zagaz.split(' - ')):
                # std_sub_address_zagaz = str_corr_low_std_noacc(sub_address_zagaz, False)
                # levenshtein_tuple = get_levenshtein_tuple(address, std_sub_address_zagaz)
                # list_station_levenshtein.append(levenshtein_tuple)
          # sorted(list_station_levenshtein, key=lambda tup: tup[0])
          # station_results.append([id_zagaz] + list(list_station_levenshtein[0]))
        # list_info_levenshtein.append((id, sorted(station_results, key=lambda tup: tup[1])))
      # else:
        # list_info_levenshtein.append([])
        # list_zip_not_in_zagaz.append((zip, id))
    # else:
      # list_info_levenshtein.append([])

  # # TODO: c. 100 zip are unmatched (merely?) because of cedex => use city
  # # TODO: drop duplicate gas stations in master
  # # TODO: some are matched with the same zagaz => check them, may want to match from each side
  # # TODO: check GPS proximity
  # # TODO: some short addresses (part of which: highway, to be excluded)    

  # list_accepted = []
  # list_rejected = []
  # for elt in list_info_levenshtein:
    # if elt:
      # temp_tuple= ([elt[0]] + elt[1][0],\
                  # master_addresses_final[elt[0]][0][0],\
                  # dict_id_zagaz[elt[1][0][0]][0][1])
      # if 1 - float(elt[1][0][1])/float(elt[1][0][3]) >= 0.5:
        # list_accepted.append(temp_tuple)
      # else:
        # list_rejected.append(temp_tuple)

  # # Check result quality with brand
  # list_accepted_2 = []
  # list_rejected_2 = []
  # for row in list_accepted:
    # if row[0][0] in master_price['dict_info'].keys():
      # brand_gouv = str_low_noacc(str_correct_html(\
                      # master_price['dict_info'][row[0][0]]['brand'][-1][0]))
      # brand_zagaz = str_low_noacc(str_correct_html(dict_zagaz[row[0][1]][1]))
      # if dict_brands.get(brand_gouv.upper()) != dict_brands.get(brand_zagaz.upper()):
        # list_rejected_2.append((row, brand_gouv, brand_zagaz))
      # else:
        # list_accepted_2.append(row)
    # else:
      # print row[0][0], 'not in master_price'

  # # len(list_accepted_2) = 5988
  # # TODO: check GPS consistence (could check double attributions first...)
     
  # for row in list_rejected:
    # if row[0][0] in master_price['dict_info'].keys():
      # brand_gouv = str_low_noacc(str_correct_html(\
                    # master_price['dict_info'][row[0][0]]['brand'][-1][0]))
      # brand_zagaz = str_low_noacc(str_correct_html(dict_zagaz[row[0][1]][1]))
      # if dict_brands.get(brand_gouv.upper()) == dict_brands.get(brand_zagaz.upper()):
        # print row, brand_gouv, brand_zagaz
    # else:
      # print row[0][0], 'not in master_price'

  # for elt in list_accepted[0:1000]:
    # print elt[0]
    # print elt[1]
    # print elt[2],'\n'