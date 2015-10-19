#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re
import itertools
import pandas as pd

def format_str_low_noacc(word):
  word = word.lower()
  dict_drop_accents  = {u'a': [u'â', u'à', u'ã', u'á'],
                        u'c': [u'ç'],
                        u'i': [u'î', u'ï'],
                        u'o': [u'ô', u'ö'],
                        u'u': [u'û', u'ù', u'ü'], 
                        u'e': [u'é', u'è', u'ê', u'ë'],
                        u'y': [u'ÿ']}
  for char, ls_accented_chars in dict_drop_accents.iteritems():
    for accented_char in ls_accented_chars:
      word = word.replace(accented_char, char)
  word = re.sub(ur'\b-\b', ur' ', word)
  for char in [u"'", u'"', u'[', u']', u'(', u')', u'.', u',']:
    word = word.replace(char, u' ')
  return ' '.join(word.strip().split())

def format_str_city_insee(word):
  word = format_str_low_noacc(word)
  word = re.sub(ur"(^|\s)st(s?)(\s|$|-)", ur" saint\2 ", word)
  word = re.sub(ur"(^|\s)ste(s?)(\s|$|-)", ur" sainte\2 ", word)
  word = word.replace("'", " "
  word = word.replace("-", " ")
  word = re.sub(u'cedex', u'', word)
  return ' '.join(word.strip().split())

class MatchingINSEE:
  def __init__(self, file_name):
    """
    @param file_name: path to a csv file with city names, zips, dpts, and insee codes
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

def get_dict_refine_insee_code(ls_valid_ic):
  """
  returns dict of (insee_code, insee_code_ardt)
  hence should be used with dict_refine_ic.get(some_ic, (None, None))
  """
  dict_refine_ic = {x: (x, x) for x in ls_valid_ic}
  ls_valid_ic_corse = [x for x in ls_valid_ic if re.match('2[AB]', x)]
  for ic in ls_valid_ic_corse:
    dict_refine_ic[ic[:1] + u'0' + ic[2:]] = (ic, ic) # assumed unicity was checked
  dict_ic_ardts = dict(list(itertools.product(map(str,range(13201, 13217)), ['13055']))+\
                       list(itertools.product(map(str,range(69381, 69390)), ['69123']))+\
                       list(itertools.product(map(str,range(75101, 75121)), ['75056'])))
  dict_ic_ardts = {k : (v,k) for k,v in dict_ic_ardts.items()}
  dict_refine_ic.update(dict_ic_ardts)
  return dict_refine_ic

if __name__ == "__main__":
  
  path_data = os.path.join(u'W:\\', u'Bureau', 'Etienne_work', 'Data')
  if not os.path.exists(path_data):
    path_data = os.path.join(u'C:\\', u'Users', 'etna', 'Desktop', 'Etienne_work', 'Data')
  path_dir_match_insee = os.path.join(path_data, u'data_insee', 'match_insee_codes')
  path_dir_ameli_built_json = os.path.join(path_data, u'data_ameli', 'data_built', 'json')
  path_dir_insee_extracts = os.path.join(path_data, u'data_insee', 'data_extracts')

  # TEST MATCHING
  path_df_corr = os.path.join(path_dir_match_insee, 'df_corr_gas.csv')
  matching_insee = MatchingINSEE(path_df_corr)
  ls_matched = [matching_insee.match_city('PARIS', '75', '75006')]
  
  # CHECK INSEE CODES STILL IN USE AND ADD DISTRICT FOR BIG CITIES
  df_com = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                    u'df_communes.csv'),
                       encoding = 'utf-8',
                       dtype = str)

  ls_valid_ic = list(df_com['CODGEO'].values)
  dict_refine_ic = get_dict_refine_insee_code(ls_valid_ic)
  ls_refined = [dict_refine_ic.get(x[0][0][2], (None, None)) for x in ls_matched]
