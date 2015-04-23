#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
from generic_ameli import * # should not be necessary
import pandas as pd # should not be necessary
import itertools

def format_str_low_noacc(word):
  # Just for comparison's sake: no accent and word-word (maybe insufficient?)
  word = word.lower()
  accents  = {u'a': [u'â', u'à', u'ã', u'á'],
              u'c': [u'ç'],
              u'i': [u'î', u'ï'],
              u'o': [u'ô', u'ö'],
              u'u': [u'û', u'ù', u'ü'], 
              u'e': [u'é', u'è', u'ê', u'ë'],
              u'y': [u'ÿ']}
  for (char, accented_chars) in accents.iteritems():
    for accented_char in accented_chars:
      word = word.replace(accented_char, char)
  word = re.sub(ur'\b-\b', ur' ', word)
  word = word.replace("'", " ").replace('"', ' ')
  word = word.replace('[',' ').replace(']',' ').replace('(','').replace(')',' ')
  word = word.replace('.', ' ').replace(',',' ').strip()
  word = ' '.join(word.split())
  return word.strip()

def format_str_city_insee(word, del_accent = True):
  # Just for comparison's sake: no accent and word-word (maybe insufficient?)
  if del_accent:
    word = format_str_low_noacc(word)
  word = word.lower()
  word = re.sub(ur"(^|\s)st(s?)(\s|$|-)", ur" saint\2 ", word)
  word = re.sub(ur"(^|\s)ste(s?)(\s|$|-)", ur" sainte\2 ", word)
  word = word.replace("'", " ")
  word = word.replace("-", " ")
  word = ' '.join(word.split())
  return word.strip()

def format_correspondence(correspondence):
  """
  returns correspondence with 0 at beginning of insee_code if 4 chars only
  ---
  correspondence: list of tup (commune, zip_code, department, insee_code) 
  """
  correspondence = [(format_str_city_insee(city_insee),
                     zip_code_insee,
                     department_insee,
                     code_insee.rjust(5, '0')) for (city_insee,
                                                    zip_code_insee,
                                                    department_insee,
                                                    code_insee) in correspondence]
  #ls_correspondence = []
  #for city_insee, zip_code_insee, department_insee, code_insee in correspondence:
  #  ls_correspondence.append((city_insee, zip_code_insee, department_insee, code_insee))
  return correspondence

def match_insee_code(correspondence, city, dpt_code, zip_code = None):
  """
  TODO: create class and keep dicts alive
  returns insee code corresponding to dpt, city
  ---
  need to make sure that city is no accent and harmonized insee way 
  """
  
  # Based on zip code and city name
  ls_matching = []
  found_indicator = False
  if zip_code:
    dict_corr_zip_insee = {}
    for city_insee, zip_code_insee, department_insee, code_insee in correspondence:
      dict_corr_zip_insee.setdefault(zip_code_insee, []).append((city_insee,
                                                                 zip_code_insee,
                                                                 department_insee,
                                                                 code_insee))
 
    if zip_code in dict_corr_zip_insee:
      for city_insee, zip_insee, dpt_insee, code_insee in dict_corr_zip_insee[zip_code]:
        if city == city_insee:
          ls_matching.append((city_insee, zip_insee, code_insee))
          found_indicator = True
      if found_indicator:
        return (ls_matching, 'zip_city_match')
      # If no exact zip, city match: check if city name in insee city names
      for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
        if city in city_insee:
          ls_matching.append((city_insee, zip_insee, code_insee))
          found_indicator = True
      if found_indicator:
        return (ls_matching, 'zip_city_in_match(es)')

  # Based on dpt code and city name
  dict_corr_dpt_insee = {}
  for city_insee, zip_code_insee, department_insee, code_insee in correspondence:
    dict_corr_dpt_insee.setdefault(zip_code_insee[:-3], []).append((city_insee,
                                                                    zip_code_insee,
                                                                    department_insee,
                                                                    code_insee))
  
  for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_dpt_insee[dpt_code]:
    if city == city_insee:
      ls_matching.append((city_insee, zip_insee, code_insee))
      found_indicator = True
  if found_indicator:
    return (ls_matching, 'dpt_city_match')
      # If no exact dpt, city match: check if city name in insee city names
  for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_dpt_insee[dpt_code]:
    if city in city_insee:
      ls_matching.append((city_insee, zip_insee, code_insee))
      found_indicator = True
  if found_indicator:
    return (ls_matching, 'dpt_city_in_match(es)')
  # No match
  return (None, 'no_match')

if __name__ == "__main__":
  
  path_data = os.path.join(u'W:\\', u'Bureau', 'Etienne_work', 'Data')
  path_dir_match_insee = os.path.join(path_data, u'data_insee', 'match_insee_codes')
  path_dir_ameli_built_json = os.path.join(path_data, u'data_ameli', 'data_built', 'json')
  path_dir_insee_extracts = os.path.join(path_data, u'data_insee', 'data_extracts')

  # LOAD CORRESPONDENCE

  # Load zip code - insee code correspondence file
  file_correspondence = open(os.path.join(path_dir_match_insee,
                                          'corr_cinsee_cpostal'),'r')
  correspondence = file_correspondence.read().split('\n')[1:-1]
  
  # Update changes in city codes (correspondence is a bit old)
  file_correspondence_update = open(os.path.join(path_dir_match_insee,
                                                 'corr_cinsee_cpostal_update'),'r')
  correspondence_update = file_correspondence_update.read().split('\n')[1:]
  correspondence += correspondence_update
  
  # Patch ad hoc for gas station cedexes
  file_correspondence_gas_path = open(os.path.join(path_dir_match_insee,
                                                   'corr_cinsee_cpostal_gas_patch'),'r')
  correspondence_gas_patch = file_correspondence_gas_path.read().split('\n')
  correspondence += correspondence_gas_patch
  correspondence = [row.split(';') for row in correspondence]
  
  correspondence = format_correspondence(correspondence)
  
  # EXECUTE MATCHING
  
  ls_ophtalmos = dec_json(os.path.join(path_dir_ameli_built_json,
                                       'ophtalmologiste_suburb_2014.json'))
  city, dpt = format_str_low_noacc(ls_ophtalmos[0][5][6:]), ls_ophtalmos[0][5][:2]
  ls_matched = match_insee_code(correspondence, city, dpt)
  
  # LOAD CURRENT INSEE CODES
  
  df_insee = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                      u'df_communes.csv'),
                         encoding = 'utf-8',
                         dtype = str)
  
  # CHECK INSEE CODES STILL IN USE
  # list includes big city code and ardts
  ls_fra_insee_codes = df_insee['CODGEO'].values
  indiv_insee_code = ls_matched[0][0][2]
  if indiv_insee_code in ls_fra_insee_codes:
    final_insee_code = indiv_insee_code
  elif indiv_insee_code[:2] == '20':
    if indiv_insee_code[:1] + 'A' + indiv_insee_code[2:] in ls_france_insee_codes:
      final_insee_code = indiv_insee_code[:1] + 'A' + indiv_insee_code[2:]
    elif indiv_insee_code[:1] + 'B' + indiv_insee_code[2:] in ls_france_insee_codes:
      final_insee_code = indiv_insee_code[:1] + 'B' + indiv_insee_code[2:]
    else:
      print 'Code geo:', invdiv_insee_code, 'absent from recent insee files'
      final_insee_code = None
  else:
    print 'Code geo:', invdiv_insee_code, 'absent from recent insee files'
    final_insee_code = None

  # INSEE CODE big city vs ardt (should use zip if provided to add ardt)

  dict_large_cities = dict(list(itertools.product(map(str,range(13201, 13217)), ['13055']))+\
                           list(itertools.product(map(str,range(69381, 69390)), ['69123']))+\
                           list(itertools.product(map(str,range(75101, 75121)), ['75056'])))
