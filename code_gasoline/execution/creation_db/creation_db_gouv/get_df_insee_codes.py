#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
import pprint

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')
path_dir_built_json = os.path.join(path_dir_built_paper, u'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

path_dir_match_insee = os.path.join(path_data, u'data_insee', u'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_data, u'data_insee', u'data_extracts')
path_dir_insee_dpts_regions = os.path.join(path_data, u'data_insee', u'dpts_regions')

# LOAD GAS STATION ADDRESSES

#master_price_raw = dec_json(os.path.join(path_dir_built_json, u'master_price_diesel_raw.json'))
#master_info_raw = dec_json(os.path.join(path_dir_built_json, u'master_info_raw.json'))

master_price = dec_json(os.path.join(path_dir_built_json, u'master_price_diesel_fixed.json'))
master_info = dec_json(os.path.join(path_dir_built_json, u'master_info_fixed.json'))

# Build master_addresses (addresses corrected for html pbms and somewhat stdized)
dict_addresses = {indiv_id: [indiv_info['address'][i]\
                               for i in (5, 3, 4, 0) if indiv_info['address'][i]]\
                    for (indiv_id, indiv_info) in master_info.items()}
master_addresses = build_master_addresses(dict_addresses)
master_addresses['15400003'] = [(u'zone industrielle du sedour', u'15400 riom-\xc8s-montagnes')]
master_addresses['76170004'] = [(u'autoroute a 29', u'76210 bolleville')]

# Check zip from station address vs. zip from indiv_id (break if zip code not found in address)
dict_describe_addresses = {}
for indiv_id, ls_addresses in master_addresses.items():
  zip_indiv_id = indiv_id[:-3].rjust(5, '0')
  ls_zip_address = [re.match('([0-9]{5})\s.*', address[1]).group(1).rjust(5, '0')\
                      for address in ls_addresses if re.match('([0-9]{5})\s.*', address[1])] 
  if not ls_addresses:
    dict_describe_addresses.setdefault('No_address', []).append(indiv_id)
  else:
    if len(ls_addresses) > 1:
      dict_describe_addresses.setdefault('Multi_address', []).append(indiv_id)
    if len(ls_addresses) != len(ls_zip_address):
      dict_describe_addresses.setdefault('No_zip_address', []).append(indiv_id)
    if any(zip_address != zip_indiv_id for zip_address in ls_zip_address):
      dict_describe_addresses.setdefault('Several_zip', []).append(indiv_id)
print 'Issues with addresses / zip codes:'
for k, v in dict_describe_addresses.items():
  print k, len(v)

# LOAD INSEE CORRESPONDENCE AND RUN MATCHING

df_corr = pd.read_csv(os.path.join(path_dir_match_insee, 'df_corr_gas.csv'),
                      dtype = str)
ls_corr = [list(x) for x in df_corr.to_records(index = False)]
ls_corr = format_correspondence(ls_corr)

# Match on master_info_raw
# Caution match_res can contain several results
ls_ls_match_res = []
for indiv_id, ls_addresses in master_addresses.iteritems():
  ls_match_res = []
  for address in ls_addresses:
    zip_and_city = re.match('([0-9]{5,5}) (.*)', address[1])
    zip_code = zip_and_city.group(1)
    city = zip_and_city.group(2)
    match_res = match_insee_code(ls_corr, city, zip_code[:-3], zip_code)
    ls_match_res.append(match_res)
  ls_ls_match_res.append(ls_match_res)

# Flatten results in one list (via set) per indiv
ls_rows = []
for ls_match_res in ls_ls_match_res:
  ls_res = []
  for match_res in ls_match_res:
    if match_res[1] != 'no_match':
      ls_res.append(match_res[0][0][2])
  ls_rows.append(list(set(ls_res)))

# Explore cases with several different results
dict_len = {}
for i,x in enumerate(ls_rows):
  dict_len.setdefault(len(x),[]).append(i)
for k, v in dict_len.items():
  print k, len(v)
# Only 2 in current case
for id_indiv in dict_len[2]:
  pprint.pprint(ls_ls_match_res[id_indiv])

# CHECK INSEE CODES STILL IN USE + DISAMB BIG CITY ARDTS

df_com = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                  u'df_communes.csv'),
                     encoding = 'utf-8',
                     dtype = str)

ls_rows_final = []
for row in ls_rows:
  row_final = [refine_insee_code(df_com['CODGEO'].values, x) for x in row]
  ls_rows_final.append([ic for ls_ic in row_final for ic in ls_ic])

# BUILD DF INSEE CODE
df_ci = pd.DataFrame(ls_rows_final,
                     columns = ['ci_1',
                                'ci_ardt_1',
                                'ci_2',
                                'ci_ardt_2'],
                     index = master_addresses.keys())

df_ci['ci_1'][pd.isnull(df_ci['ci_1'])] = df_ci['ci_2']
df_ci['ci_ardt_1'][pd.isnull(df_ci['ci_ardt_1'])] = df_ci['ci_ardt_2']

dict_dpts_regions = dec_json(os.path.join(path_dir_insee_dpts_regions,
                                          'dict_dpts_regions.json'))
df_ci['dpt'] = df_ci['ci_1'].str.slice(stop = 2)
df_ci['reg'] = df_ci['dpt'].apply(lambda x: dict_dpts_regions[x])

# todo: store csv with indiv_id and insee_code
# todo: confront municipality polygon w/ gps (rather checkin gps...)
# todo: check master_price not in master_info (i.e. short lived a priori...)

df_ci.to_csv(os.path.join(path_dir_built_csv,
                          'df_ci.csv'),
             index_label = 'id_station',
             float_format= '%.3f',
             encoding = 'utf-8')
