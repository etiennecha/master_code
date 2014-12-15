#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import re
from params import *
import pprint

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    data_paper_folder)


path_dir_built_json = os.path.join(path_dir_built_paper, u'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

# LOAD SCRAPED DATA

master_info = dec_json(os.path.join(path_dir_built_json,
                                    'master_info_raw.json'))
master_diesel = dec_json(os.path.join(path_dir_built_json,
                                    'master_price_diesel_raw.json'))

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
nb_info_records = len(master_info[master_info.keys()[0]])

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
  # check validity of addresses (add zip_code check)
  if any([len([x for x in address if x]) != 2 for address in ls_addresses]):
    print '\n', id_gouv, 'has an invalid address:'
    print station_info['address'] 

#master_info.pop('99999002', None) # drop it at build to avoid pbms

# todo: if missing street once but other valid addresses, just drop problematic address
# todo: loop + check if id_gouv in master_info

master_info['76170004']['address'] = [None for i in range(nb_info_records)] +\
                                     [[u'Toulbroche',
                                       u'56870 BADEN']]

master_info['40410003']['address']= [None for i in range(nb_info_records)] +\
                                     [[u'aire porte des landes est',
                                       u'40410 saugnacq et muret']]

master_info['40410003']['address']= [None for i in range(nb_info_records)] +\
                                     [[u'aire porte des landes est',
                                       u'40410 saugnacq et muret']]

master_info['40410004']['address'] = [None for i in range(nb_info_records)] +\
                                     [[u'aire porte des landes ouest',
                                       u'40410 saugnacq et muret']]

master_info['29140005']['address']= [None for i in range(nb_info_records)] +\
                                    [[u'RN165 voie express', u'29140 SAINT-YVI']]

master_info['74600011']['address'][6] = [None for i in range(nb_info_records)] +\
                                        [[u'AUTOROUTE A41 NORD', u'74600 SEYNOD']] # for insee

## Get rid or clean 4, 5, 6 if included
#master_info['15400003']['address'][6] = (u'zone industrielle du sedour',
#                                         u'15400 riom-\xc8s-montagnes')
# OUTPUT

## No preliminary fix deemed necessary at this stage... could add (e.g. brands)
#enc_json(master_info, os.path.join(path_dir_built_json,
#                                   'master_info_fixed.json'))
#
#print u'\nCreation of master_info_fixed.json successful'
#print type(master_info)
#print u'Length:', len(master_info)
