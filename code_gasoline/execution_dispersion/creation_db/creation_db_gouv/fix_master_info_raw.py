#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import re
import pprint

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_paper_dispersion')

path_dir_built_json = os.path.join(path_dir_built_paper, u'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

# LOAD SCRAPED DATA

master_info = dec_json(os.path.join(path_dir_built_json,
                                    'master_info_raw.json'))
master_diesel = dec_json(os.path.join(path_dir_built_json,
                                    'master_price_diesel_raw.json'))
# could check master_gas too if needed

# LOAD OPEN DATA

df_info_open = pd.read_csv(os.path.join(path_data,
                                        'data_gasoline',
                                        'data_source',
                                        'data_opendata',
                                        'csv_files',
                                        'df_info_all.csv'),
                           dtype = {'id_station' : str,
                                    'zip_code' : str},
                           encoding = 'UTF-8')
df_info_open.set_index('id_station', inplace = True)

# List of services:
ls_open_columns = df_info_open.columns
ls_no_service_cols = ['city', 'street', 'lat', 'lng', 'pop',
                      'zip_code', 'op_h', 'cl_h', 'cl_days']
ls_service_cols = [x for x in ls_open_columns if x not in ls_no_service_cols]
print '\nCheck all the following are gas station services:'
print ls_service_cols

# FILL SCRAPED DATA

ls_info_ids = master_info.keys()
ls_missing_ids = [id_gouv for id_gouv in master_diesel['ids']\
                    if id_gouv not in ls_info_ids]
ls_ids_tofill = [id_gouv for id_gouv in ls_missing_ids\
                   if id_gouv in df_info_open.index]
ls_ids_lost = [id_gouv for id_gouv in ls_missing_ids\
                 if id_gouv not in df_info_open.index]

# Nb of elements for each info field (nb of records over time)
nb_info_records = len(master_info[master_info.keys()[0]]['address'])

for id_gouv in ls_ids_tofill:
  highway = 0 if df_info_open.ix[id_gouv]['pop'] == 'A' else 1
  services = [x for x in ls_service_cols if df_info_open.ix[id_gouv][x] == 1]
  closed_days = df_info_open.ix[id_gouv]['cl_days']
  master_info[id_gouv] =\
    {'address' : [[] for i in range(nb_info_records -1)] +\
                    [[df_info_open.ix[id_gouv]['street'],
                     ' '.join(df_info_open.ix[id_gouv][['zip_code', 'city']].values)]],
     'highway' : [None for i in range(nb_info_records - 1)] + [highway],
     'services' : [None for i in range(nb_info_records - 1)] + [services],
     'closed_days' : [None for i in range(nb_info_records - 1)] + [closed_days],
     'name' : [None for i in range(nb_info_records)], # info not in opendata
     'hours' : [None for i in range(nb_info_records)], # see if can do smth
     'gps' : [None for i in range(nb_info_records)], # so far only for old geocoding
     'gas_types' : [None for i in range(nb_info_records)]}
  # print master_info[id_gouv]['address']

# GET RID OF MEANINGLESS STATION RECORDS AND FIX ADDRESSES
# based mainly on issues met while matching city and zip to insee code
# fixed here to have right addresses in geocoding
# could be an order in execution though so addresses have been fixed while matching

print '\nCheck station address(es)'
for id_gouv, station_info in master_info.items():
  # check no address
  ls_addresses = [x for x in station_info['address'] if x]
  if not ls_addresses:
    print '\n', id_gouv, 'has no address'
  elif all([len([x for x in address if x]) != 2 for address in ls_addresses]):
    print '\n', id_gouv, 'has only invalid addresses:'
    print station_info['address']
  elif any([len([x for x in address if x]) != 2 for address in ls_addresses]):
    print '\n', id_gouv, 'has some invalid addresses:'
    master_info[id_gouv]['address'] = \
      [address if ((address) and (len([x for x in address if x]) == 2)) else None\
         for address in station_info['address']]
    print 'Fixed master info:',
    print master_info[id_gouv]['address']

# todo: if missing street once but other valid addresses, just drop problematic address

print '\nRemaining problems'
for id_gouv in ['76170004', '74600011', '63190008', '99999001']:
  if id_gouv in master_info:
    print id_gouv, master_info[id_gouv]['address']

ls_address_fix = [['76170004', [u'autoroute a 29', 
                                 u'76210 bolleville']], # no address
                  ['63190008', [u'AIRE DE LEZOUX - A72',
                                u'63190 LEZOUX']]] # for insee matching
                  #['74600011', [u'AUTOROUTE A41 NORD',
                  #              u'74600 SEYNOD']] # for insee matching
                  #['76170004', [u'Toulbroche',
                  #              u'56870 BADEN']],
                  #['40410003', [u'aire porte des landes est',
                  #              u'40410 saugnacq et muret']],
                  #['40410004', [u'aire porte des landes ouest',
                  #              u'40410 saugnacq et muret']],
                  #['29140005', [u'RN165 voie express',
                  #              u'29140 SAINT-YVI']],

# Commented out: no more necessary with last info record

for id_gouv, address in ls_address_fix:
  if id_gouv in master_info:
    master_info[id_gouv]['address']= [None for i in range(nb_info_records - 1)] +\
                                     [address]

# First in master_info, other just in master_price: test stations...
for id_gouv in ['99999001', '99999002']:
  master_info.pop(id_gouv, None)

# OUTPUT

enc_json(master_info, os.path.join(path_dir_built_json,
                                   'master_info_fixed.json'))

print u'\nCreation of master_info_fixed.json successful'
print type(master_info)
print u'Length:', len(master_info)
