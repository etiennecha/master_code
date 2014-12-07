#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import httplib, urllib2
import urllib
import cookielib
from BeautifulSoup import BeautifulSoup
import re
from datetime import date
import json

def enc_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def clean_souptag(souptag):
  ls_clean = re.split(ur'<p class="hours">|<p>|<strong>|</strong>|'+\
                        ur'<br\s?/>(.*)<p>|<strong>|</strong>|<br\s?/>',
                      unicode(souptag))
  ls_clean = [elt.replace('\n', '').replace('</p>','').strip()\
                for elt in ls_clean\
                  if (elt is not None) and\
                     (elt.replace('\n', '').replace('</p>','').strip()  != '')]
  return ls_clean

def get_station_info(id_gouv):
  base_url = r'http://www.prix-carburants.economie.gouv.fr/itineraire/infos/'
  response = urllib2.urlopen(base_url + id_gouv)
  data = response.read()
  soup = BeautifulSoup(data)
  name_and_address_bloc = soup.find('p')
  name_and_brand = re.findall('<strong>(.*?)</strong>', unicode(name_and_address_bloc))
  address = clean_souptag(re.search(ur'.*</strong><br\s?/>(.*?)</p>',
                                    unicode(name_and_address_bloc).replace('\n','')).group(1))
  opening_hours_bloc = soup.findAll('p', {'class': 'hours'})
  opening_hours = clean_souptag(opening_hours_bloc[0])
  if len(opening_hours_bloc) == 2:
    closed_days = clean_souptag(opening_hours_bloc[1])
  else:
    closed_days = None
  if len(opening_hours_bloc) > 2:
    print id_gouv, opening_hours_bloc
  services_bloc = soup.find('p', {'class': 'services'})
  services = services_bloc.findAll('img',
                                   {'src': re.compile('/bundles/public/images/pictos/service_.*')})
  list_services = [service['alt'] for service in services]
  return [name_and_brand, address, opening_hours, closed_days, list_services]

if __name__ == '__main__':

  # path_data: default to CREST location, else try home location
  path_data = os.path.join(u'W:\\', u'Bureau', u'Etienne_work', u'Data')
  if not os.path.exists(path_data):
    path_data = os.path.join(u'C:\\', u'Users', u'etna', u'Desktop',
                             u'Etienne_work', u'Data')
  
  path_source_prices = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_source',
                                    u'data_prices')
  
  path_raw_info_stations = os.path.join(path_data,
                                        u'data_gasoline',
                                        u'data_raw',
                                        u'data_stations',
                                        u'data_gouv_stations')
  
  # use both latest (not automatic!) diesel and gas price files to get ids
  diesel_price_file = dec_json(os.path.join(path_source_prices,
                                            u'diesel_standardized_tuple_lists',
                                            u'20141204_diesel'))
  gas_price_file = dec_json(os.path.join(path_source_prices,
                                            u'gas_standardized_tuple_lists',
                                            u'20141204_gas'))
  ls_ids = [row[0] for row in diesel_price_file] +\
           [row[0] for row in gas_price_file]
  ls_ids = list(set(ls_ids))
  
  # loop and scrap
  dict_stations = {}
  ls_field_keys = ['name', 'address', 'hours', 'closed_days', 'services']
  for id_gouv in ls_ids:
    try:
      dict_stations[id_gouv] = dict(zip(ls_field_keys,
                                        get_station_info(id_gouv)))
    except:
      print 'couldnt get info for', id_gouv
  
  # enc_json(dict_stations, os.path.join(path_raw_info_stations, u'20141206_gouv_stations'))
