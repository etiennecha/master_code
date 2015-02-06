#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import xml.etree.ElementTree as ET
from BeautifulSoup import BeautifulStoneSoup
import pandas as pd
import matplotlib.pyplot as plt
 
path_dir_opendata = os.path.join(path_data,
                                 'data_gasoline',
                                 'data_source',
                                 'data_opendata')

path_dir_xml = os.path.join(path_dir_opendata, 'xml_files')
path_dir_csv = os.path.join(path_dir_opendata, 'csv_files')

def clean_str(word):
  ls_replace = [(u'&#xC0;' , u'À'),
                (u'&#xE0;' , u'à'),
                (u'&#xC2;' , u'Â'),
                (u'&#xE2;' , u'â'),
                (u'&#xC6;' , u'Æ'),
                (u'&#xE6;' , u'æ'),
                (u'&#xC7;' , u'Ç'),
                (u'&#xE7;' , u'ç'),
                (u'&#xC8;' , u'È'),
                (u'&#xE8;' , u'è'),
                (u'&#xC9;' , u'É'),
                (u'&#xE9;' , u'é'),
                (u'&#xCA;' , u'Ê'),
                (u'&#xEA;' , u'ê'),
                (u'&#xCB;' , u'Ë'),
                (u'&#xEB;' , u'ë'),
                (u'&#xCE;' , u'Î'),
                (u'&#xEE;' , u'î'),
                (u'&#xCF;' , u'Ï'),
                (u'&#xEF;' , u'ï'),
                (u'&#xD4;' , u'Ô'),
                (u'&#xF4;' , u'ô'),
                (u'&#x152;', u'Œ'),
                (u'&#x153;', u'œ'),
                (u'&#xD9;' , u'Ù'),
                (u'&#xF9;' , u'ù'),
                (u'&#xDB;' , u'Û'),
                (u'&#xFB;' , u'û'),
                (u'&#xDC;' , u'Ü'),
                (u'&#xFC;' , u'ü'),
                (u'&#xAB;' , u'«'),
                (u'&#xBB;' , u'»')]
  for old, new in ls_replace:
    word = word.replace(old, new)
  return word

## Invalid xml?
#tree = ET.parse(path_xml_file)
#root = tree.getroot()

ls_dict_fermetures = []
for year in ['20{:02d}'.format(i) for i in range(7, 15)[0:1]]:

  xml = open(os.path.join(path_dir_xml,
                          u'PrixCarburants_annuel_%s.xml' %year), 'r').read()
  soup = BeautifulStoneSoup(xml)
  
  ## Overview
  #soup = BeautifulStoneSoup(xml[0:10000])
  #print soup.prettify()
  
  # Extraction of info and services
  ls_pdv_blocs = soup.findAll('pdv', {'id' : True})
  ls_fuel_types = ['SP95', 'Gazole']
  dict_ls_se_prices = {k: [] for k in ls_fuel_types}
  ls_rows_info, ls_rows_services = [], []
  dict_fermetures = {}
  for pdv_bloc in ls_pdv_blocs:
    id_pdv = pdv_bloc['id']
    
    # info
    lat, lng = pdv_bloc.get('latitude', None), pdv_bloc.get('longitude', None)
    zip_code, pop = pdv_bloc.get('cp', None), pdv_bloc.get('pop', None)
    # street
    bloc_street, street = pdv_bloc.find('adresse'), None
    if bloc_street:
      street = bloc_street.string
    # street
    bloc_city, city = pdv_bloc.find('ville'), None
    if bloc_city:
      city = bloc_city.string
    # opening hours, closed days
    bloc_opening = pdv_bloc.find('ouverture')
    opening_hour, closing_hour, closed_days = None, None, None
    if bloc_opening:
      opening_hour = bloc_opening.get('debut')
      closing_hour = bloc_opening.get('fin')
      closed_days = bloc_opening.get('saufjour')
    # amenities
    bloc_services, ls_services = pdv_bloc.find('services'), []
    if bloc_services:
      ls_services = [x.string for x in bloc_services.findAll('service')]
    ls_rows_info.append([id_pdv,
                         lat, lng, pop,
                         zip_code, city, street,
                         opening_hour, closing_hour, closed_days])
    ls_rows_services.append(ls_services)
    
    # prices
    for fuel_type in ls_fuel_types:
      ls_price_blocs = pdv_bloc.findAll('prix', {'nom' : fuel_type}) # alt id = 2
      ls_maj, ls_val = [], []
      for price_bloc in ls_price_blocs:
        # strip maj to keep day at str (could be more robust)
        ls_maj.append(price_bloc['maj'][0:10])
        ls_val.append(price_bloc['valeur'])
      se_prices = pd.Series(ls_val, index = ls_maj, name = id_pdv)
      dict_ls_se_prices[fuel_type].append(se_prices)
  
    if pdv_bloc.find('fermeture') and pdv_bloc.findAll('fermeture', {'type' : True}):
      ls_fermetures = pdv_bloc.findAll('fermeture', {'type' : True})
      dict_fermetures[pdv_bloc['id']] = [x['type'] for x in ls_fermetures]
  ls_dict_fermetures.append(dict_fermetures)

  # BUILD DF INFO
  
  ls_columns = ['id_station', 'lat', 'lng', 'pop',
                'zip_code', 'city', 'street',
                'op_h', 'cl_h', 'cl_days']
  # df_info = pd.DataFrame(ls_rows_info, columns = ls_columns)
  
  ls_unique_services = list(set([service for row_service in ls_rows_services\
                                   for service in row_service]))
  ls_rows_info_final = []
  for ls_info, ls_services in zip(ls_rows_info, ls_rows_services):
    ls_services = [0 if service not in ls_services else 1\
                     for service in ls_unique_services]
    ls_rows_info_final.append(ls_info + ls_services)
  
  df_info = pd.DataFrame(ls_rows_info_final,
                         columns = ls_columns + ls_unique_services)
  
  df_info.columns = [clean_str(x) for x in df_info.columns]
  df_info['city'] = df_info['city'].apply(lambda x: clean_str(x) if x else x)
  df_info['street'] = df_info['street'].apply(lambda x: clean_str(x) if x else x)
  df_info.set_index('id_station', inplace = True)
  df_info.to_csv(os.path.join(path_dir_csv,
                              u'df_info_%s.csv' %year),
                   index = 'id_station',
                   encoding = 'utf-8')

  # BUILD DFS PRICES 

  # erases intra day changes (keep last)
  # todo: evaluate loss of information
  # todo: most easy fix: prices at midnight (ok w/ last?)
  for fuel_type in ls_fuel_types:
    ls_se_prices = [se_prices.groupby(level=0).last()\
                           for se_prices in dict_ls_se_prices[fuel_type]]
    df_prices = pd.concat(ls_se_prices, axis = 1)
    
    # reindex on dates, fill holes, convert to numeric
    df_prices.index = pd.to_datetime(df_prices.index)
    
    index = pd.date_range(start = pd.to_datetime('%s0101' %year),
                          end   = pd.to_datetime('%s1231' %year), 
                          freq='D')
    df_reindex = pd.DataFrame(None, index = index)
    df_prices = pd.merge(df_reindex, df_prices,
                       left_index = True, right_index = True, how = 'left')
    # df_prices = df_prices.fillna(method = 'ffill', axis = 0, limit = 14)
    df_prices = df_prices.convert_objects(convert_numeric=True)
  
    df_prices.to_csv(os.path.join(path_dir_csv,
                                  u'%s_%s.csv' %(year, fuel_type)),
                     index_label = 'date',
                     encoding = 'utf-8')
