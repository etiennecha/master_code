#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re
import itertools
import pandas as pd

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

def format_str_city_insee(word):
  word = format_str_low_noacc(word)
  word = re.sub(ur"(^|\s)st(s?)(\s|$|-)", ur" saint\2 ", word)
  word = re.sub(ur"(^|\s)ste(s?)(\s|$|-)", ur" sainte\2 ", word)
  word = word.replace("'", " ")
  word = word.replace("-", " ")
  word = re.sub(u'cedex', u'', word)
  word = ' '.join(word.split())
  return word.strip()

def format_correspondence(ls_corr):
  """
  DEPRECATED : use class
  returns correspondence with 0 at beginning of insee_code if 4 chars only
  ---
  correspondence: list of tup (commune, zip_code, department, insee_code) 
  """
  ls_corr = [(format_str_city_insee(city_insee),
              zip_code_insee.rjust(5, '0'),
              department_insee,
              code_insee.rjust(5, '0')) for (city_insee,
                                             zip_code_insee,
                                             department_insee,
                                             code_insee) in ls_corr]
  return ls_corr


class MatchingINSEE:
  def __init__(self, file_name):
    """
    @param file_name: path to a csv file containing citys names, zips, dpts, and insee codes
    @type file_name: C{str}
    """
    df_corr = pd.read_csv(file_name, dtype = str)
    ls_corr = [list(x) for x in df_corr.to_records(index = False)]
    ls_corr = [(format_str_city_insee(city_insee),
               zip_code_insee.rjust(5, '0'),
               department_insee,
               code_insee.rjust(5, '0')) for (city_insee,
                                                   zip_code_insee,
                                                   department_insee,
                                                   code_insee) in ls_corr]
    self.dict_corr_zip_insee = {}
    for city_insee, zip_code_insee, department_insee, code_insee in ls_corr:
      self.dict_corr_zip_insee.setdefault(zip_code_insee, []).append((city_insee,
                                                                      zip_code_insee,
                                                                      department_insee,
                                                                      code_insee))

    self.dict_corr_dpt_insee = {}
    for city_insee, zip_code_insee, department_insee, code_insee in ls_corr:
      self.dict_corr_dpt_insee.setdefault(zip_code_insee[:-3], []).append((city_insee,
                                                                           zip_code_insee,
                                                                           department_insee,
                                                                           code_insee))

  def match_city(self, city, dpt_code, zip_code = None):
    """
    returns insee code corresponding to dpt, city
    """
    city = format_str_city_insee(city)
    dpt_code = dpt_code.rjust(2, '0')
    if zip_code:
      zip_code.rjust(5, '0')
    # Based on zip code and city name
    ls_matching = []
    found_indicator = False
    if zip_code:
      if zip_code in self.dict_corr_zip_insee:
        for city_insee, zip_insee, dpt_insee, code_insee in self.dict_corr_zip_insee[zip_code]:
          if city == city_insee:
            ls_matching.append((city_insee, zip_insee, code_insee))
            found_indicator = True
        if found_indicator:
          return (ls_matching, 'zip_city_match')
        # If no exact zip, city match: check if city name in insee city names
        for city_insee, zip_insee, dpt_insee, code_insee in self.dict_corr_zip_insee[zip_code]:
          if city in city_insee:
            ls_matching.append((city_insee, zip_insee, code_insee))
            found_indicator = True
        if found_indicator:
          return (ls_matching, 'zip_city_in_match(es)')
    # Based on dpt code and city name
    for city_insee, zip_insee, dpt_insee, code_insee in self.dict_corr_dpt_insee[dpt_code]:
      if city == city_insee:
        ls_matching.append((city_insee, zip_insee, code_insee))
        found_indicator = True
    if found_indicator:
      return (ls_matching, 'dpt_city_match')
        # If no exact dpt, city match: check if city name in insee city names
    for city_insee, zip_insee, dpt_insee, code_insee in self.dict_corr_dpt_insee[dpt_code]:
      if city in city_insee:
        ls_matching.append((city_insee, zip_insee, code_insee))
        found_indicator = True
    if found_indicator:
      return (ls_matching, 'dpt_city_in_match(es)')
    # No match
    return (None, 'no_match')

def match_insee_code(ls_corr, city, dpt_code, zip_code = None):
  """
  DEPRECATED : use class
  """
  city = format_str_city_insee(city)
  dpt_code = dpt_code.rjust(2, '0')
  if zip_code:
    zip_code.rjust(5, '0')

  # Based on zip code and city name
  ls_matching = []
  found_indicator = False
  if zip_code:
    dict_corr_zip_insee = {}
    for city_insee, zip_code_insee, department_insee, code_insee in ls_corr:
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
  for city_insee, zip_code_insee, department_insee, code_insee in ls_corr:
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

def refine_insee_code(ls_fra_insee_codes, candidate):
  dict_large_cities = dict(list(itertools.product(map(str,range(13201, 13217)), ['13055']))+\
                           list(itertools.product(map(str,range(69381, 69390)), ['69123']))+\
                           list(itertools.product(map(str,range(75101, 75121)), ['75056'])))
  if candidate in ls_fra_insee_codes:
    if candidate in dict_large_cities:
      final_ic, final_ic_ardt = dict_large_cities[candidate], candidate
    elif candidate in ['13055', '69123', '75056']:
      final_ic, final_ic_ardt = candidate, None # could keep candidate
    else:
      final_ic, final_ic_ardt = candidate, candidate
  elif candidate[:2] == '20':
    candidate_A = candidate[:1] + 'A' + candidate[2:]
    candidate_B = candidate[:1] + 'B' + candidate[2:]
    if candidate_A in ls_fra_insee_codes:
      final_ic, final_ic_ardt = candidate_A, candidate_A
    elif candidate_B in ls_fra_insee_codes:
      final_ic, final_ic_ardt = candidate_B, candidate_B
    else:
      final_ic, final_ic_ardt = None, None
  else:
    final_ic, final_ic_ardt = None, None
  return final_ic, final_ic_ardt

if __name__ == "__main__":
  
  path_data = os.path.join(u'W:\\', u'Bureau', 'Etienne_work', 'Data')
  path_dir_match_insee = os.path.join(path_data, u'data_insee', 'match_insee_codes')
  path_dir_ameli_built_json = os.path.join(path_data, u'data_ameli', 'data_built', 'json')
  path_dir_insee_extracts = os.path.join(path_data, u'data_insee', 'data_extracts')

  ## LOAD CORRESPONDENCE AND TEST MATCHING (DEPRECATED)

  #df_corr = pd.read_csv(os.path.join(path_dir_match_insee, 'df_corr_gas.csv'),
  #                      dtype = str)
  #ls_corr = [list(x) for x in df_corr.to_records(index = False)]
  #ls_corr = format_correspondence(ls_corr)
  #ls_matched = [match_insee_code(ls_corr, 'PARIS', '75', '75006')]
  
  # TEST MATCHING
  
  path_df_corr = os.path.join(path_dir_match_insee, 'df_corr_gas.csv')
  matching_insee = MatchingINSEE(path_df_corr)
  ls_matched = [matching_insee.match_city('PARIS', '75', '75006')]
  
  # LOAD CURRENT INSEE CODES
  
  df_insee = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                      u'df_communes.csv'),
                         encoding = 'utf-8',
                         dtype = str)
  
  # CHECK INSEE CODES STILL IN USE
  ic, ic_ardt = refine_insee_code(df_insee['CODGEO'].values,
                                  ls_matched[0][0][0][2])
