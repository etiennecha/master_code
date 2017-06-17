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

# Caution: using old versions of BeautifulSoup
# may lead to miss results (incomplete page parsing)

def collect_dpt_stations(i):
  recherche_url = 'http://www.prix-carburants.gouv.fr/recherche/' +\
                  '?sort=commune&direction=asc&page={:d}&lettre=%23&limit=100'.format(i)
  r3 = s.get(recherche_url)
  soup3 = BeautifulSoup(r3.text, 'lxml')
  ls_station_blocs = soup3.findAll('tr', {'class' : re.compile('data.*')})
  for bloc_station in ls_station_blocs:
    id_station = bloc_station['id']
    ls_info_blocs = bloc_station.findAll('td', {'class' : 'pointer'})
    ls_info = [info.text for info in ls_info_blocs]
    type_station = 'normal'
    if bloc_station.find('img', {'alt' : True, 'title' : 'Autoroute'}):
      type_station = 'highway'
    ls_dpt_stations.append([id_station, type_station] + ls_info)
  if len(ls_station_blocs) == 100:
    collect_dpt_stations(i+1)

ls_essence_cols = ['c_dpt', 'id', 'type', 'blank',
                   'municipality', 'name', 'brand',
                   'sp95', 'date_sp95',
                   'sp95-e10', 'date_sp95-e10', 'blank_2']

ls_diesel_cols = ['c_dpt', 'id', 'type', 'blank',
                  'municipality', 'name', 'brand',
                  'diesel', 'date_diesel', 'blank_2']

# Rappel: choix carburant: diesel = 1, essence = 'a'
ls_choices = [['diesel', '1', ls_diesel_cols],
              ['essence', 'a', ls_essence_cols]]

#carb, c_carb, ls_carb_cols = ls_choices[1]
for carb, c_carb, ls_carb_cols in ls_choices:

  s = requests.Session()
  website_url = 'http://www.prix-carburants.gouv.fr'
  r = s.get(website_url)
  soup = BeautifulSoup(r.text, 'lxml')
  token = soup.find('input', {'type' : 'hidden',
                              'id':'recherche_recherchertype__token'})['value']
  print('Got token:', token)
  ls_station_rows = []
  for c_dpt in range(1, 96):
    str_c_dpt = '{:02d}'.format(c_dpt)
    # query with token
    post_data = {'_recherche_recherchertype[choix_carbu]' : c_carb,
                 '_recherche_recherchertype[localisation]' : str_c_dpt,
                 '_recherche_recherchertype[_token]' : token}
    r2 = s.post('http://www.prix-carburants.gouv.fr', data = post_data)
    soup2 = BeautifulSoup(r2.text, 'lxml')
    # get page with 100 results (still: can be several pages)
    ls_dpt_stations = []
    collect_dpt_stations(1)
    ls_station_rows += [[str_c_dpt] + dpt_station for dpt_station in ls_dpt_stations]
  
  df = pd.DataFrame(ls_station_rows, columns = ls_carb_cols)
  df.drop(['blank', 'blank_2'], axis = 1, inplace = True)
  
  for col_date in df.columns:
    if col_date[:5] == 'date_':
      df[col_date] = pd.to_datetime(df[col_date],
                                    errors = 'coerce',
                                    format = '%d/%m/%y')
      ## String for lighter output (done with to_csv())
      #df[col_date] = df[col_date].dt.strftime('%Y-%m-%d')
      #df.loc[df[col_date] == 'NaT', col_date] = None
  
  for col_price in ['diesel', 'sp95', 'sp95-e10']:
    if col_price in df.columns:
      df.loc[df[col_price] == '--', col_price] = None
      df[col_price] = df[col_price].astype(float)
  
  str_today = date.today().strftime('%Y%m%d')
  
  df.to_csv(os.path.join(path_data,
                         'data_gasoline',
                         'data_built',
                         'data_scraped_2017',
                         'data_gouv_raw',
                         '{:s}_{:s}.csv'.format(str_today, carb)),
            index = False,
            encoding = 'utf-8',
            float_format = '%.3f',
            date_format = '%Y-%m-%d')
