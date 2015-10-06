#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
import pprint

path_dir_built = os.path.join(path_data,
                              'data_gasoline',
                              'data_built',
                              'data_scraped_2011_2014')

path_dir_built_json = os.path.join(path_dir_built, u'data_json')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')

path_dir_match_insee = os.path.join(path_data, u'data_insee', u'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_data, u'data_insee', u'data_extracts')
path_dir_insee_dpts_regions = os.path.join(path_data, u'data_insee', u'dpts_regions')

# LOAD GAS STATION INFO AND ADDRESSES

master_info = dec_json(os.path.join(path_dir_built_json, u'master_info_fixed.json'))

# Build master_addresses (addresses corrected for html pbms and somewhat stdized)
dict_addresses = {indiv_id: [indiv_info['address'][i]\
                               for i in (8, 7, 6, 5, 3, 4, 0)\
                                 if (indiv_info['address'][i]) and\
                                    (len(indiv_info['address'][i]) == 2)]\
                    for (indiv_id, indiv_info) in master_info.items()}

master_addresses = build_master_addresses(dict_addresses)

# Check zip from address vs. zip from indiv_id (breaks if zip not found in address)
dict_describe_addresses = {}
for indiv_id, ls_addresses in master_addresses.items():
  zip_indiv_id = indiv_id[:-3].rjust(5, '0')
  ls_zip_address = [re.match('([0-9]{5})\s.*', address[1]).group(1).rjust(5, '0')\
                      for address in ls_addresses if re.match('([0-9]{5})\s.*',
                                                              address[1])] 
  if not ls_addresses:
    dict_describe_addresses.setdefault('No_address', []).append(indiv_id)
  else:
    if len(ls_addresses) > 1:
      dict_describe_addresses.setdefault('Multi_address', []).append(indiv_id)
    if len(ls_addresses) != len(ls_zip_address):
      dict_describe_addresses.setdefault('No_zip_address', []).append(indiv_id)
    if any(zip_address != zip_indiv_id for zip_address in ls_zip_address):
      dict_describe_addresses.setdefault('Several_zip', []).append(indiv_id)
print '\nOverview addresses / zip codes:'
for k, v in dict_describe_addresses.items():
  print k, len(v)

# LOAD INSEE CORRESPONDENCE AND RUN MATCHING

path_df_corr = os.path.join(path_dir_match_insee, 'df_corr_gas.csv')
matching_insee = MatchingINSEE(path_df_corr)

# Perform matching for each address by station
ls_row_matches = []
for indiv_id, ls_addresses in master_addresses.iteritems():
  ls_matches = []
  for address in ls_addresses:
    zip_and_city = re.match('([0-9]{5,5}) (.*)', address[1])
    zip_code = zip_and_city.group(1)
    city = zip_and_city.group(2)
    ls_matches.append(matching_insee.match_city(city, zip_code[:-3], zip_code))
  ls_row_matches.append((indiv_id,
                         ls_matches))

# Get a list of unique insee codes by station
ls_row_unique_ics, dict_nb_ics = [], {}
for indiv_id, ls_matches in ls_row_matches:
  ls_ics = [match[0][0][2] for match in ls_matches\
              if match[1] != 'no_match']
  ls_unique_ics = list(set(ls_ics))
  dict_nb_ics.setdefault(len(ls_unique_ics),[]).append(indiv_id)
  ls_row_unique_ics.append((indiv_id, ls_unique_ics))
print u'\nOverview nb of insee codes by indiv:'
for k, v in dict_nb_ics.items():
  print k, len(v)

## Inspect cases with several occurencs
#dict_matches = dict(ls_row_matches)
#for indiv_id in dict_nb_ics[2][0:10]:
#  print u'\n'
#  pprint.pprint(master_addresses[indiv_id])
#  pprint.pprint(dict_matches[indiv_id])

# CHECK INSEE CODE VALIDITY AND ADD DISTRICTS CODES FOR LARGE CITIES

df_com = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                  u'df_communes.csv'),
                     encoding = 'utf-8',
                     dtype = str)

ls_valid_ic = list(df_com['CODGEO'].values)
dict_refine_ic = get_dict_refine_insee_code(ls_valid_ic)

ls_rows_final = []
for indiv_id, ls_unique_ics in ls_row_unique_ics:
  ls_final_ics = [dict_refine_ic.get(x, (None, None))\
                      for x in ls_unique_ics]
  ls_final_ics = [ic for ls_ic in ls_final_ics for ic in ls_ic]
  ls_rows_final.append([indiv_id] + ls_final_ics)

# BUILD DF INSEE CODE
df_ci = pd.DataFrame(ls_rows_final,
                     columns = ['id_station',
                                'ci_1',
                                'ci_ardt_1',
                                'ci_2',
                                'ci_ardt_2'])
df_ci.set_index('id_station', inplace = True)

df_ci['ci_1'][pd.isnull(df_ci['ci_1'])] = df_ci['ci_2']
df_ci['ci_ardt_1'][pd.isnull(df_ci['ci_ardt_1'])] = df_ci['ci_ardt_2']

dict_dpts_regions = dec_json(os.path.join(path_dir_insee_dpts_regions,
                                          'dict_dpts_regions.json'))

df_ci['dpt'] = df_ci['ci_1'].str.slice(stop = 2)
df_ci['reg'] = df_ci['dpt'].apply(lambda x: dict_dpts_regions[x])

df_ci.to_csv(os.path.join(path_dir_built_csv,
                          'df_ci.csv'),
             index_label = 'id_station',
             float_format= '%.3f',
             encoding = 'utf-8')
