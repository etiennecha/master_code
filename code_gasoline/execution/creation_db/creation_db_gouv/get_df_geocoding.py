#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_geocoding import *
import pandas as pd

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

# LOAD GAS STATION ADDRESSES
master_price_raw = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel_raw.json'))
master_price = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel.json'))
master_info_raw = dec_json(os.path.join(path_dir_built_json, 'master_info_diesel_raw.json'))
master_info = dec_json(os.path.join(path_dir_built_json, 'master_info_diesel.json'))

#  Build master_addresses (addresses corrected for html pbms and somewhat stdized)
dict_addresses = {}
for indiv_id, station in master_info_raw.items():
  dict_addresses[indiv_id] = [station['address'][i] for i in (5, 3, 4, 0) if station['address'][i]]
master_addresses = build_master_addresses(dict_addresses)
master_addresses['15400003'] = [(u'zone industrielle du sedour', u'15400 riom-\xc8s-montagnes')]
master_addresses['76170004'] = [(u'autoroute a 29', u'76210 bolleville')]

# UPDATE MASTER GEOCODING
master_geocoding = dec_json(os.path.join(path_dir_built_json, 'master_geocoding.json'))
ls_miss_ids = []
ls_miss_adr_ids = []
for indiv_id, ls_addresses in master_addresses.iteritems():
  if indiv_id not in master_geocoding.keys():
    ls_miss_ids.append(indiv_id)
    master_geocoding[indiv_id] = [ls_addresses,
                                  [None for i in ls_addresses]]
  else:
    for address in ls_addresses:
      if list(address) not in master_geocoding[indiv_id][0]: # json does not support tuples
        ls_miss_adr_ids.append(indiv_id)
        master_geocoding[indiv_id][0].append(list(address))
        master_geocoding[indiv_id][1].append(None)
ls_miss_adr_ids = list(set(ls_miss_adr_ids))
print 'Nb ids not included in master_geocoding', len(ls_miss_ids)
print 'Nb ids w/ missing addresses in master_geocoding:', len(ls_miss_adr_ids)

# todo: may want to use standardized string comparison
# e.g. master_addresses['58640003']

## UPDATE GEOCODING
#over_query = False
#c = 0
#for indiv_id, geo_info in master_geocoding.items():
#  for i, address in enumerate(geo_info[0]):
#    # (geo_info[1][i]['status'] == 'ZERO_RESULTS') or\
#    if (not geo_info[1][i]) or\
#       ((geo_info[1][i]['status'] == 'OK') and\
#        (geo_info[1][i]['results'][0]['geometry']['location_type'] == 'APPROXIMATE')):
#      info_geocoding = geocode_via_google(','.join(address))
#      c += 1
#      if info_geocoding['status'] == u'OVER_QUERY_LIMIT':
#        over_query = True
#        print 'Query quota used'
#        break
#      else:
#        master_geocoding[indiv_id][1][i] = info_geocoding
#        time.sleep(0.15)
#  if over_query:
#    break
#print c, 'queries performed (should be < 2500)'

# CHECK GEOCODING RESULTS
dict_results_geocoding, ls_geocoded_but_weird, ls_not_geocoded =\
    get_stats_geocoding(master_geocoding)
print '\nStations not geocoded yet', len(ls_not_geocoded)
print 'Stations geocoded but result can not be read', len(ls_geocoded_but_weird)
for quality, ls_quality_results in dict_results_geocoding.items():
  print quality, len(ls_quality_results)

# STORE JSON
# enc_json(master_geocoding, os.path.join(path_dir_built_json, 'master_geocoding.json'))

# BUILD DF GEOCODING
ls_rows, ls_ind = [], []
for indiv_id, geo_info in master_geocoding.items():
  ls_ind.append(indiv_id)
  best_geo = get_best_geocoding_info(geo_info[1])
  if best_geo:
    ls_rows.append([best_geo['results'][0]['geometry']['location']['lat'],
                    best_geo['results'][0]['geometry']['location']['lng'],
                    best_geo['results'][0]['geometry']['location_type'],
                    best_geo['results'][0]['formatted_address']])
  else:
    ls_rows.append([None, None, None, None])

df_geocoding = pd.DataFrame(ls_rows,
                            index = ls_ind,
                            columns = ['lat', 'lng', 'quality', 'google_adr'])

# todo: check France and get rid of it for readibility's sake
# todo: could use geocoding result dict structure...
