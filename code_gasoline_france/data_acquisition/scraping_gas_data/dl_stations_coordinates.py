#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from add_to_path import path_data
import os, sys
import requests
from bs4 import BeautifulSoup
import httplib, urllib2
import urllib
import cookielib
import re
from datetime import date
import json

def enc_json(data, path):
  with open(path, 'w') as f:
    json.dump(data, f)

def get_coordinates(fuel_type):
  """
  Returns a list of lists containing station coordinates
  
  @param fuel_type  leaded (diesel) = 1, unleaded (essence) = 'a'
  """
  s = requests.Session()
  website_url = 'http://www.prix-carburants.gouv.fr'
  r = s.get(website_url)
  soup = BeautifulSoup(r.text, 'lxml')
  token = soup.find('input', {'type' : 'hidden',
                              'id':'recherche_recherchertype__token'})['value']
  print('Got token:', token)
  ls_coordinates = []
  for i in range(1, 96):
    # query with token
    post_data = {'_recherche_recherchertype[choix_carbu]' : fuel_type,
                 '_recherche_recherchertype[localisation]' : '%02d' %i,
                 '_recherche_recherchertype[_token]' : token}
    r2 = s.post('http://www.prix-carburants.gouv.fr', data = post_data)
    soup2 = BeautifulSoup(r2.text, 'lxml')
    # get map page
    recherche_url = 'https://www.prix-carburants.gouv.fr/recherche/map'
    r3 = s.get(recherche_url)
    soup3 = BeautifulSoup(r3.text, 'lxml')
    dpt_coordinates_bloc = soup3.find('div', {'id' : 'pagecarto'})
    ls_dpt_coordinate_blocs = dpt_coordinates_bloc.findAll('span', {'class' : 'infoPdv',
                                                                    'data-id' : True,
                                                                    'data-lon' : True,
                                                                    'data-lat' : True})
    ls_dpt_coordinates = [(x['data-id'], x['data-lon'], x['data-lat'])\
                            for x in ls_dpt_coordinate_blocs]
    ls_coordinates += ls_dpt_coordinates
  return ls_coordinates

path_temp = os.path.join(path_data,
                         'data_gasoline',
                         'data_built',
                         'data_scraped_2017',
                         'data_gouv_raw')

ls_diesel_gps = get_coordinates('1')
ls_essence_gps =  get_coordinates('a')

str_today = date.today().strftime('%Y%m%d')

enc_json(ls_essence_gps,
         os.path.join(path_temp,
                      u'{:s}_essence_gps.json'.format(str_today)))

enc_json(ls_diesel_gps,
         os.path.join(path_temp,
                      u'{:s}_diesel_gps.json'.format(str_today)))
