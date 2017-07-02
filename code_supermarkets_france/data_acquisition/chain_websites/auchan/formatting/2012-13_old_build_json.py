#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
import json
from datetime import date, timedelta
import datetime
import numpy as np
import pprint

path_auchan = os.path.join(path_data,
                           u'data_drive_supermarkets',
                           u'data_auchan')

path_price_source = os.path.join(path_auchan,
                                 u'data_source',
                                 u'data_json_auchan_velizy')

path_price_built = os.path.join(path_auchan,
                                'data_built',
                                'data_json_auchan_velizy')

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def date_range(start_date, end_date):
  """
  creates a list of dates based on its arguments (beginning and end dates)
  """
  list_dates = []
  for n in range((end_date + timedelta(1) - start_date).days):
    temp_date = start_date + timedelta(n)
    list_dates.append(temp_date.strftime('%Y%m%d'))
  return list_dates

def get_formatted_file(master_period):
  clean_master_period = []
  list_products = []
  for product in master_period:
    # clean fields
    product['product_total_price'] = ''.join(product['product_total_price']).\
                                               replace('<sub>','').\
                                               replace('<span>&euro;</span></sub>','').\
                                               replace(',','.')
    product['price_unit'] = product['product_unit_price'][0]
    product['product_unit_price'] = product['product_unit_price'][2].\
                                      replace('&euro;','').\
                                      replace(',','.')
    product['product_title'] = product['product_title'][0]
    if len(product['product_promo']) == 0:
      product['product_promo_amount'] = '0'
      product['product_promo_type'] = ''
    else:
      product['product_promo_amount'] = product['product_promo'][0].\
                                          replace(',','.')
      product['product_promo_type'] = product['product_promo'][1].\
                                        replace('<sup>','').\
                                        replace('</sup>','')
    del product['product_promo']
    if len(product['product_promo_vignette']) == 0:
      product['product_promo_vignette'] = ''
    else:
      product['product_promo_vignette'] = product['product_promo_vignette'][0]
    # regroup duplicate products
    if product['department'] and product['sub_department']:
      dict_dpt_subdpts.setdefault(product['department'], set()).add(product['sub_department'])
      product['department'] = [product['department']]
      product['sub_department'] = [product['sub_department']]
      if product['product_title'] not in list_products:
        clean_master_period.append(product)
        list_products.append(product['product_title'])
      else:
        product_index = list_products.index(product['product_title'])
        # drop product if same name but different price (not perfect dynamically...)
        if clean_master_period[product_index]['product_total_price'] !=\
                product['product_total_price']:
          del clean_master_period[product_index]
          del list_products[product_index]
        else:
          clean_master_period[product_index]['department'] += product['department']
          clean_master_period[product_index]['sub_department'] += product['sub_department']
          # print clean_master_period[product_index]['product_title'],\
                # clean_master_period[product_index]['department'],\
                # clean_master_period[product_index]['sub_department']
          for key in ['product_unit_price', 'product_promo_type', 'product_promo_amount']:
            if clean_master_period[product_index][key] != product[key]:
              print '\n pbm - same product with different info'
              pprint.pprint(clean_master_period[product_index])
              pprint.pprint(product)
  return clean_master_period

def build_master(get_formatted_file, path_data, file_extension,
                 start_date, end_date, id_str, price_str, date_str, key_dict):
  """
  The function aggregates files i.e. lists of dicts into a dict
  It uses a function to read and format the raw files (to be dropped lated?)
  ----
  Arguments description:
  - raw_data_folder: location of files
  - file_extension, start_date, end_date: files names must be : date + extension
  - id_str, price_str, date_str: names of id, price and date keys in file individual dicos
  - key_dict: all other keys in file individual dicos
  """
  master_dates = date_range(start_date, end_date)
  missing_dates = []
  master_dict_general_info = {}
  master_list_ids = []
  master_list_prices = []
  master_list_dates = []
  for date_index, date in enumerate(master_dates):
    file_path = os.path.join(path_data, r'{:s}{:s}'.format(date, file_extension))
    if os.path.exists(file_path):
      master_period = get_formatted_file(dec_json(file_path))
      for observation in master_period:
        if observation[id_str] in master_list_ids:
          observation_index = master_list_ids.index(observation[id_str])
          for original_key, new_key in key_dict.iteritems():
            if observation[original_key] !=\
                 master_dict_general_info[observation[id_str]][new_key][-1][0]:
              master_dict_general_info[observation[id_str]][new_key].append(\
                     (observation[original_key],
                      date_index))
        else:
          master_list_ids.append(observation[id_str])
          observation_index = master_list_ids.index(observation[id_str])
          master_dict_general_info[observation[id_str]] = {'rank': observation_index}
          for original_key, new_key in key_dict.iteritems():
            master_dict_general_info[observation[id_str]][new_key] =\
                  [(observation[original_key],
                    date_index)]
          master_list_prices.append([])
          master_list_dates.append([])
        # fill price/date holes (either bc of missing dates or individuals occas. missing)
        while len(master_list_prices[observation_index]) < date_index:
          master_list_prices[observation_index].append(None)
        master_list_prices[observation_index].append(observation[price_str])
        while len(master_list_dates[observation_index]) < date_index:
          master_list_dates[observation_index].append(None)
        master_list_dates[observation_index].append(observation[date_str])
    else:
      missing_dates.append(date)
  # add None if list of prices/dates shorter than nb of days (not for dates so far)
  for list_prices in master_list_prices:
    while len(list_prices) < len(master_dates):
      list_prices.append(None)
  for list_dates in master_list_dates:
    while len(list_dates) < len(master_dates):
      list_dates.append(None)
  master_price = {'ls_dates' : master_dates,
                  'ls_missing_dates' : missing_dates, 
                  'dict_info': master_dict_general_info,
                  'ls_ids' : master_list_ids, 
                  'ls_ls_prices' : master_list_prices,
                  'ls_ls_dates' : master_list_dates}
  return master_price

def fill_holes(master_price, fill_limit):
  # no replacement if number of None in a row equal fill_limit
  master_price_filled = []
  for index_list_prices, list_prices in enumerate(master_price):
    first_observation = next(obs_ind for obs_ind, obs in enumerate(list_prices) if obs)
    # next breaks (StopIterration) if one list is full of None (which should not happen)
    last_observation =\
        len(list_prices) - 1 - next(obs_ind for obs_ind, obs\
                                       in enumerate(list_prices[::-1]) if obs)
    list_prices_filled = [None for i in range(first_observation)]
    observation_index = first_observation
    while observation_index < last_observation:
      if list_prices[observation_index]:
        list_prices_filled.append(list_prices[observation_index])
        observation_index += 1
      else:
        next_observation_relative_position = 0
        while not list_prices[observation_index + next_observation_relative_position]:
          next_observation_relative_position += 1
        if next_observation_relative_position < fill_limit:
          # fills with the next available price: could as well be the last available price
          list_prices_filled +=\
              [list_prices[observation_index + next_observation_relative_position]\
                   for i in range(next_observation_relative_position)]
          if list_prices[observation_index-1] !=\
                 list_prices[observation_index + next_observation_relative_position]:
            print 'different prices between and after', index_list_prices
        else:
          list_prices_filled += [None for i in range(next_observation_relative_position)]
        observation_index += next_observation_relative_position
    list_prices_filled += list_prices[last_observation:]
    master_price_filled.append(list_prices_filled)
  return master_price_filled

def get_price_lists_with_holes(master_price):
  list_dilettante = []
  for index_list_prices, list_prices in enumerate(master_price):
    first_observation = next(obs_ind for obs_ind, obs in enumerate(list_prices) if obs)
    last_observation = len(list_prices) - 1 -\
                         next(obs_ind for obs_ind, obs in enumerate(list_prices[::-1]) if obs)
    if None in list_prices[first_observation:last_observation]:
      list_dilettante.append(index_list_prices)
  return list_dilettante

def get_field_as_list(id, field, master_dict_general_info, master_dates):
  field_index = 0
  if not master_dict_general_info[id][field]:
    # fill with none if no info at all for the field
    list_result = [None for i in range(len(master_dates))]
  else:
    period_index = master_dict_general_info[id][field][field_index][1]
    # initiate list_result, fill with None if no info at beginning
    if period_index == 0:
      list_result = []
    else:
      list_result = [None for i in range(period_index)]
    # fill list_results with relevant field info
    while period_index < len(master_dates):
      if field_index < len(master_dict_general_info[id][field]) - 1:
        # before the last change: compare periods
        if period_index < master_dict_general_info[id][field][field_index + 1][1]:
          list_result.append(master_dict_general_info[id][field][field_index][0])
        else:
          field_index += 1
          list_result.append(master_dict_general_info[id][field][field_index][0])
      else:
        # after the last change: fill with last info given
        list_result.append(master_dict_general_info[id][field][-1][0])
      period_index += 1
  return list_result

def display_product_info(ind, master):
  print master['ls_ids'][ind]
  pprint.pprint(master['dict_general_info'][master['ls_ids'][ind]])
  print master['ls_ls_prices'][ind]

# #############
# BUILD MASTER
# #############

dict_dpt_subdpts = {} # needed and filled by get_formatted_file()

# Test formatting function
date_str = '20130411'
path_file =  os.path.join(path_price_source,
                          u'{:s}_auchan_velizy'.format(date_str))
ls_products_ex = get_formatted_file(dec_json(path_file))

# Build master
path_data = path_price_source
file_extension = r'_auchan_velizy'
start_date = date(2012,11,22)
end_date =  date(2012,12,22) # date(2013,5,13)
id_str = 'product_title'
price_str = 'product_total_price'
date_str = 'product_unit_price'
key_dict = {'department' : 'department',
            'sub_department' : 'sub_department',
            'product_flag' : 'product_flag',
            'price_unit' : 'price_unit',
            'product_promo_type' : 'product_promo_type',
            'product_promo_vignette' : 'product_promo_vignette',
            'product_promo_amount' : 'product_promo_amount'}
dict_master = build_master(get_formatted_file, path_data, file_extension,\
                        start_date, end_date, id_str, price_str, date_str, key_dict)
# it may not be appropriate to fill gaps
# however in the short term it makes price changes analysis easier (diff between series)
ls_ls_prices_corrected = fill_holes(dict_master['ls_ls_prices'], 3)
ls_products_with_holes = get_price_lists_with_holes(ls_ls_prices_corrected)

for k, v in dict_dpt_subdpts.iteritems():
  dict_dpt_subdpts[k] = list(v)

#enc_json(dict_master, os.path.join(path_price_built, 'master_duplicate'))
#enc_json(dict_dpt_subdpts, os.path.join(path_price_built, 'dict_dpt_subdpts'))
