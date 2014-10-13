#!/usr/bin/python
# -*- coding: utf-8 -*-

# ADD STRING INSEE HARMONIZATION

def format_low_noacc(word):
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

def format_city_insee(word):
  # Just for comparison's sake: no accent and word-word (maybe insufficient?)
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
  correspondence = [(format_city_insee(commune),
                     zip_code,
                     deparment,
                     insee_code.rjust(5, '0')) for (commune,
                                                    zip_code,
                                                    department,
                                                    insee_code) in correspondence]
  return correspondence

def match_insee_code(correspondence, zip_code, dpt_code, city):
  """
  returns insee code corresponding to dpt, city
  ---
  need to make sure that city is no accent and harmonized insee way 
  """
  dict_corr_zip_insee = {}
  for (city, zip_code, department, insee_code) in correspondence:
    dict_corr_zip_insee.setdefault(zip_code, []).append((city,
                                                         zip_code,
                                                         department,
                                                         insee_code))
  dict_corr_dpt_insee = {}
  for (city, zip_code, department, insee_code)  in correspondence:
    dict_corr_dpt_insee.setdefault(zip_code[:-3], []).append((city,
                                                              zip_code,
                                                              department,
                                                              insee_code))
 
  # Based on zip code and city name
  found_indicator = False
  for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
    if city == city_insee:
      ls_matching.append((indiv_id, zip_code, code_insee))
      return (ls_matching, 'zip_city_match'
  # If no exact zip, city match: check if city name in insee city names
  for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_zip_insee[zip_code]:
    if city in city_insee:
      ls_matching.append((indiv_id, zip_code, code_insee))
      found_indicator = True
  if found_indicator:
    return (ls_matching, 'zip_city_in_match(es)'

  # Based on dpt code and city name
  for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_dpt_insee[dpt_code]:
    if city == city_insee:
      ls_matching.append((indiv_id, zip_code, code_insee))
      found_indicator = True
  if found_indicator:
    return (ls_matching, 'dpt_city_match'
      # If no exact dpt, city match: check if city name in insee city names
  for city_insee, zip_insee, dpt_insee, code_insee  in dict_corr_dpt_insee[dpt_code]:
    if city in city_insee:
      ls_matching.append((indiv_id, zip_code, code_insee))
      found_indicator = True
  if found_indicator:
    return (ls_matching, 'dpt_city_in_match(es)'
  # No match
  return (None, 'no_match')

if __name__ == "__main__":
  ## Load zip code - insee code correspondence file
  #file_correspondence = open(os.path.join(path_dir_match_insee_codes,
  #                                        'corr_cinsee_cpostal'),'r')
  #correspondence = file_correspondence.read().split('\n')[1:-1]
  ## Update changes in city codes (correspondence is a bit old)
  #file_correspondence_update = open(os.path.join(path_dir_match_insee_codes,
  #                                               'corr_cinsee_cpostal_update'),'r')
  #correspondence_update = file_correspondence_update.read().split('\n')[1:]
  #correspondence += correspondence_update
  ## Patch ad hoc for gas station cedexes
  #file_correspondence_gas_path = open(os.path.join(path_dir_match_insee_codes,
  #                                                 'corr_cinsee_cpostal_gas_patch'),'r')
  #correspondence_gas_patch = file_correspondence_gas_path.read().split('\n')
  #correspondence += correspondence_gas_patch
  #correspondence = [row.split(';') for row in correspondence]
  #
  ## Check insee codes are still in use
  #pd_df_insee = pd.read_csv(path_csv_insee_extract, encoding = 'utf-8', dtype = str)
  #ls_france_insee_codes = list(pd_df_insee[u'Département - Commune CODGEO'].astype(str))

  #dict_large_cities = dict(list(itertools.product(map(str,range(13201, 13217)), ['13055']))+\
  #                         list(itertools.product(map(str,range(69381, 69390)), ['69123']))+\
  #                         list(itertools.product(map(str,range(75101, 75121)), ['75056'])))
  #
  #ls_unmatched_code_geo = []
  #ls_indiv_id_not_in_master_price = []
  #for (indiv_id, indiv_zip, indiv_insee_code) in ls_matching:
  #  if indiv_id in master_price['dict_info']:
  #    if indiv_insee_code in ls_france_insee_codes:
  #      final_insee_code, final_ardt_insee_code = indiv_insee_code, indiv_insee_code
  #    elif indiv_insee_code[:2] == '20':
  #      indiv_insee_code_a = indiv_insee_code[:1] + 'A' + indiv_insee_code[2:]
  #      indiv_insee_code_b = indiv_insee_code[:1] + 'B' + indiv_insee_code[2:]
  #      if indiv_insee_code_a in ls_france_insee_codes:
  #        final_insee_code, final_ardt_insee_code = indiv_insee_code_a, indiv_insee_code_a
  #      elif indiv_insee_code_b in ls_france_insee_codes:
  #        final_insee_code, final_ardt_insee_code = indiv_insee_code_b, indiv_insee_code_b
  #      else:
  #        final_insee_code, final_ardt_insee_code = None, None
  #        ls_unmatched_code_geo.append(indiv_insee_code)
  #    elif indiv_insee_code in dict_large_cities:
  #      final_insee_code, final_ardt_insee_code = dict_large_cities[indiv_insee_code], indiv_insee_code
  #    else:
  #      final_insee_code, final_ardt_insee_code = None, None
  #      ls_unmatched_code_geo.append(indiv_insee_code)
  #    master_price['dict_info'][indiv_id]['code_geo'] = final_insee_code
  #    master_price['dict_info'][indiv_id]['code_geo_ardts'] = final_ardt_insee_code
  #  else:
  #    ls_indiv_id_not_in_master_price.append(indiv_id)
  #print len(ls_unmatched_code_geo), 'code_geo not present in recent insee files'
  #print len(ls_indiv_id_not_in_master_price), 'indiv_id matched (insee) not in master_price'
