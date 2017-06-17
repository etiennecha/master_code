#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from add_to_path import path_data
import os, sys
import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from datetime import date
import json

def enc_json(data, path):
  with open(path, 'w') as f:
    json.dump(data, f)

def dec_json(path):
  with open(path, 'r') as f:
    return json.loads(f.read())

def clean_souptag(souptag):
  ls_clean = re.split(ur'<p class="hours">|<p>|<strong>|</strong>|'+\
                        ur'<br\s?/>(.*)<p>|<strong>|</strong>|<br\s?/>',
                      unicode(souptag))
  ls_clean = [elt.replace('\n', '').replace('</p>','').strip()\
                for elt in ls_clean\
                  if (elt is not None) and\
                     (elt.replace('\n', '').replace('</p>','').strip()  != '')]
  return ls_clean

def get_station_info(id_station):
  r2 = s.post('https://www.prix-carburants.gouv.fr/itineraire/infos/{:s}'.format(id_station),
              headers = {'Host' : 'www.prix-carburants.gouv.fr',
                         'Origin': 'https://www.prix-carburants.gouv.fr',
                         'Referer' : 'https://www.prix-carburants.gouv.fr/recherche/',
                          'X-Prototype-Version' : '1.7',
                          'X-Requested-With' : 'XMLHttpRequest'})
  soup2 = BeautifulSoup(r2.text, 'lxml')
  name_and_address_bloc = soup2.find('p')
  name_and_brand = re.findall('<strong>(.*?)</strong>', unicode(name_and_address_bloc))
  address = clean_souptag(re.search(ur'.*</strong><br\s?/>(.*?)</p>',
                                    unicode(name_and_address_bloc).replace('\n','')).group(1))
  opening_hours_bloc = soup2.findAll('p', {'class': 'hours'})
  opening_hours = clean_souptag(opening_hours_bloc[0])
  if len(opening_hours_bloc) == 2:
    closed_days = clean_souptag(opening_hours_bloc[1])
  else:
    closed_days = None
  if len(opening_hours_bloc) > 2:
    print(id_gouv, opening_hours_bloc)
  services_bloc = soup2.find('p', {'class': 'services'})
  services = services_bloc.findAll('img',
                                   {'src': re.compile('/bundles/public/images/pictos/service_.*')})
  ls_services = [service['alt'] for service in services]
  return [name_and_brand, address, opening_hours, closed_days, ls_services]

path_temp = os.path.join(path_data,
                         'data_gasoline',
                         'data_built',
                         'data_scraped_2017',
                         'data_gouv_raw')

df_diesel = pd.read_csv(os.path.join(path_temp, '20170501_diesel.csv'),
                        dtype = {'id' : str})
df_essence = pd.read_csv(os.path.join(path_temp, '20170501_essence.csv'),
                         dtype = {'id' : str})

ls_ids = list(set(df_diesel['id'].values)\
               .union(set(df_essence['id'].values)))


# Open connection
s = requests.Session()
website_url = 'http://www.prix-carburants.gouv.fr'
r = s.get(website_url)
soup = BeautifulSoup(r.text, 'lxml')

# Loop and scrap
#dict_stations = {}
ls_field_keys = ['name', 'address', 'hours', 'closed_days', 'services']
dict_stations = {}
for id_station in ls_ids:
  try:
    dict_stations[id_station] = dict(zip(ls_field_keys,
                                         get_station_info(id_station)))
  except:
    print('Couldnt get info for', id_station)

## todo: finish it
#str_today = date.today().strftime('%Y%m%d')
enc_json(dict_stations,
         os.path.join(path_temp,
                      '{:s}_dict_info_stations.json'.format(str_today)))

#dict_stations = dec_json(os.path.join(path_temp,
#                                      '20170502_dict_info_stations.json'))
