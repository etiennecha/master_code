#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_ameli import *
from geocoding import *
import numpy as np
import pandas as pd
import pprint

#path_dir_built_hdf5 = os.path.join(path_dir_built, 'hdf5')
#ameli_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'ameli_data.h5'))

path_dir_built_json = os.path.join(path_data, u'data_ameli', 'data_built', 'json')

ls_file_extensions = [u'ophtalmologiste_75',
                      u'generaliste_75',
                      u'gynecologue-medical_75',
                      u'ophtalmologiste_suburb']

file_extension = ls_file_extensions[3]
path_ls_ls_physicians = os.path.join(path_dir_built_json, '%s.json' %file_extension)
path_dict_gps = os.path.join(path_dir_built_json, 'dict_gps_%s.json' %file_extension)

ls_ls_physicians = dec_json(os.path.join(path_dir_built_json, '%s.json' %file_extension))
# ls_physicians : 0 is id_physician, 4 is street, 5 is zip_city (could be cedex?)

# Update ls_ls_physicians with addresses fix
path_dict_dict_fix_addresses = os.path.join(path_dir_built_json, 'dict_dict_fix_addresses.json')
dict_dict_fix_addresses = dec_json(path_dict_dict_fix_addresses)
dict_fix_addresses = dict_dict_fix_addresses.get(file_extension, {})
if dict_fix_addresses:
  for i, ls_physician in enumerate(ls_ls_physicians):
    if ls_physician[0] in dict_fix_addresses:
      ls_ls_physicians[i][4:6] = dict_fix_addresses[ls_physician[0]]

# First creation: list of addresses in case want to consider variations etc.
# Assumes never two addresses for one key
if not os.path.exists(path_dict_gps):
  dict_gps = {ls_physician[0] : [[ls_physician[4:6]], [[]]]\
                         for ls_physician in ls_ls_physicians}
  print 'dict_gps did not exist so it was created and saved'
  enc_json(dict_gps, os.path.join(path_dict_gps))
else:
  print 'dict_gps alread exists and was loaded'
  dict_gps = dec_json(os.path.join(path_dict_gps))

# Check if id_physicians in dict_gps are up to date
ls_missing_physicians = [ls_physicians[0] for ls_physicians in ls_ls_physicians\
                           if ls_physicians[0] not in dict_gps]
print '\nNb of physicians not in dict_gps:', len(ls_missing_physicians)

# Check if addresses in dict_gps are up to date
dict_missing_addresses = {}
for ls_physician in ls_ls_physicians:
  if (ls_physician[0] in dict_gps) and\
     (ls_physician[4:6] not in dict_gps[ls_physician[0]][0]):
    dict_missing_addresses.setdefault(ls_physician[0], []).append(ls_physician[4:6])
print '\nNb of id_physicians with missing addresses:', len(dict_missing_addresses)

# USE WITH CAUTION : Update addresses in dict_gps (only for existing physicians)
for ls_physician in ls_ls_physicians:
  if (ls_physician[0] in dict_gps) and\
     (ls_physician[4:6] not in dict_gps[ls_physician[0]][0]):
    dict_gps[ls_physician[0]][0].append(ls_physician[4:6])
    dict_gps[ls_physician[0]][1].append([])

# Geocode dict_gps
over_query = False
c = 0
for id_physician, geo_physician in dict_gps.items():
  if not over_query:
    for i, (address, gps) in enumerate(zip(*geo_physician)):
      if not gps:
        google_res = geocode_via_google(', '.join(address))
        c += 1
        if google_res['status'] == u'OVER_QUERY_LIMIT':
          over_query = True
          print '\nQuery quota used'
          break
        else:
          dict_gps[id_physician][1][i] = google_res
          time.sleep(0.15)
      # not sure if this one necessary:
      if over_query:
        break
print '\nQueries performed (expected to be < 2500):', c

# Describe quality
dict_gps_quality = get_google_geocoding_stats(dict_gps)
for k,v in dict_gps_quality.items():
  print u'{0:<20}{1:>6d}'.format(k, len(v))

# Inspect low quality
print '\nLow quality geocoding results'
for google_status in ['APPROXIMATE', 'GEOMETRIC_CENTER', 'ZERO_RESULTS']:
  print '\n', google_status
  for id_physician in dict_gps_quality.get(google_status, []):
    print id_physician, dict_gps[id_physician][0]
    # pprint.pprint(dict_gps[id_physician][1])
# todo: inspect RANGE_INTERPOLATED

# enc_json(dict_gps, os.path.join(path_dict_gps))
