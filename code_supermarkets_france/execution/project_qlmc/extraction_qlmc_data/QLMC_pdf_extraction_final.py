#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import os
import sys
import subprocess
from subprocess import PIPE, Popen
import re
import string
import sqlite3
import json
import pprint

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def read_pdftotext(path_file, path_pdftotext):
  file = subprocess.Popen([path_pdftotext + r'/pdftotext.exe',\
                            '-layout' , path_file, '-'], stdout=PIPE)
  data = file.communicate()[0].split('\r\n') # not good on linux?
  return data

def get_split_on_brands(string_to_split, list_split_string):
  """
  # "avec pulpe, 1L INTERMARCHE AURILLAC AV GAL LECLERC 02/09/2009 " => avoid cutting on LECLERC
  # solved by adapting the order of brand list (INTERMARCHE BEFORE LECLERC)
  """
  result = ()
  for split_string in list_split_string:
    split_search = re.search('%s' %split_string, string_to_split.strip())
    if split_search:
      if split_search.start() != 0:
        result = [string_to_split[:split_search.start()],\
                  string_to_split[split_search.start():]]
      break
  return result

def get_preliminary_check(master_period):
  set_familles = set()
  set_magasins = set()
  set_produits = set()
  for observation in master_period:
    set_familles.add(observation[1])
    set_magasins.add(observation[3])
    set_produits.add(observation[2])
  return (set_familles, set_magasins, set_produits)

list_shop_brands = ['HYPER CHAMPION', # NECESSARY IN SEP09 => Respect order
                    'INTERMARCHE SUPER',
                    'INTERMARCHE',
                    'AUCHAN',
                    'CARREFOUR MARKET',
                    'CARREFOUR',
                    'CORA',
                    'CENTRE E. LECLERC',
                    'E. LECLERC',
                    'LECLERC',
                    'GEANT CASINO',
                    'GEANT DISCOUNT',
                    'HYPER U',
                    'SUPER U',
                    'U EXPRESS',
                    'CHAMPION', # NECESSARY IN SEP09
                    'MARCHE U'] # NECESSARY IN SEP09

def format_simple(data):
  master_period = []
  dict_observation_length = {}
  list_reconstitutions = []
  for observation_index, observation in enumerate(data):
    observation_list = re.split('\s{2,}', observation)
    # check row length
    dict_observation_length.setdefault(len(observation_list), [])\
    .append((observation_index, observation_list))
    # get rid of empty string generated in the process
    observation_list = [x for x in observation_list if x]
    # if len is 3 or more, split between product name and store name when it was not done
    if len(observation_list) >= 3:
      list_split = get_split_on_brands(observation_list[2], list_shop_brands)
      if list_split:
        observation_list = observation_list[0:2] + list_split + observation_list[3:]
    # if last element has date and price (observation_list can be empty)
    if observation_list:
      price_search = re.search('[0-9]{1,3},[0-9]{1,3}', observation_list[-1])
      if price_search and ('/' in observation_list[-1]):
        split_correction = observation_list[-1].strip().split(' ')
        if len(split_correction) == 2:
          observation_list = observation_list[:-1] + split_correction
          print 'Split price/date:', observation_list
        else:
          print 'Could not split price/date:', observation_list
    # Normal line: len(observation_list) = 6
    # If less: drop, more: assume it is because of product title
    if len(observation_list) < 3:
      print 'Not written to master (len < 3):', observation_list
    else:
      if len(observation_list) >= 6:
        # else: len is big enough, may be > 6 due to product title
        observation_list = observation_list[:2] +\
                           [' '.join(observation_list[2:-3])] +\
                           observation_list[-3:]
        master_period.append(observation_list)
      else:
        print 'Not written to master (3 <= len < 6)', observation_list
  # Check that first line is to be removed
  print '\nCheck that 1st line is to be removed, not 2d'
  print master_period[0], '\n', master_period[1], '\n'
  master_period = master_period[1:]
  for observation_index, observation in enumerate(master_period):
    master_period[observation_index] = [elt.strip().replace('\x0c', '') for elt\
                                          in master_period[observation_index]]
  return (master_period, dict_observation_length, list_reconstitutions)

def format_200804(data):
  """
  # r'/200903_releves_QLMC.pdf'
  # len(observation)  == 3 => contains: rayon / famille / fin_nom_produit 
  # len(observation)  == 4 => contains: rayon / famille / debut_nom_produit / fin_nom_produit 
  """
  master_period = []
  dict_observation_length = {}
  list_short_rows = []
  cache_observation_list = None
  list_reconstitutions_1 = []
  list_reconstitutions_2 = []
  for observation_index, observation in enumerate(data):
    # split on 2 spaces or more w/ exception: no space between store and date
    date_search = re.search(ur'[0-9]{2,2}/[0-9]{2,2}/[0-9]{4,4}', observation)
    if date_search:
      observation_list = re.split('\s{2,}', observation[:date_search.start()]) +\
                         re.split('\s{2,}', observation[date_search.start():])
    else:
      observation_list = re.split('\s{2,}', observation)
    # get rid of empty string generated in the process
    observation_list = [x for x in observation_list if x]  
    # if len is 3 or more, split between product name and store name when it was not done
    if len(observation_list) >= 3:
      list_split = get_split_on_brands(observation_list[2], list_shop_brands)
      if list_split:
        observation_list = observation_list[0:2] + list_split + observation_list[3:]
    # check row length
    dict_observation_length.setdefault(len(observation_list), [])\
      .append((observation_index, observation_list))
    # Normal line: len(observation_list) == 6
    if len(observation_list) < 3:
      list_short_rows.append((observation_index, observation_list))
    else:
      if not cache_observation_list:
        if (len(observation_list) == 3 or len(observation_list) == 4):
          cache_observation_list = observation_list
        elif len(observation_list) >= 6:
          observation_list = observation_list[:2]+\
                             [' '.join(observation_list[2:-3])]+\
                             observation_list[-3:]
          master_period.append(observation_list)
        else:
          print 'Too short (no cache):', observation_list, observation_index
      else:
        if len(observation_list) == 3:
          print 'Cache but too short :', cache_observation_list, observation_list, observation_index
        elif len(cache_observation_list) == 3:
          observation_list = [''.join(observation_list[:-3])]+\
                           observation_list[-3:]
          observation_list = cache_observation_list[:2]+\
                             [''.join([observation_list[0], cache_observation_list[2]])]+\
                             observation_list[1:]
          list_reconstitutions_1.append((observation_index, observation_list))
          master_period.append(observation_list)
        elif len(cache_observation_list) == 4:
          observation_list = [''.join(observation_list[:-3])]+\
                           observation_list[-3:]
          observation_list = cache_observation_list[:2]+\
                             [''.join([cache_observation_list[2], observation_list[0], cache_observation_list[3]])]+\
                             observation_list[1:]
          list_reconstitutions_2.append((observation_index, observation_list))
          master_period.append(observation_list)
        else:
          print 'Unexpected error', observation_list, observation_index
        cache_observation_list = None
  # Check that first line is to be removed
  print master_period[0], '\n', master_period[1], '\n'
  master_period = master_period[1:]
  for observation_index, observation in enumerate(master_period):
    master_period[observation_index] = [elt.strip().replace('\x0c', '') for elt\
                                          in master_period[observation_index]]
  return [master_period, dict_observation_length, (list_reconstitutions_1,\
                                                   list_reconstitutions_2)]

def format_200903(data):
  """
  # r'/200903_releves_QLMC.pdf'
  # len(observation)  == 0 and len == 1 (1 ['\x0c']) => ignore
  # len(observation) == 3 => in cache: rayon / famille / magasin 
  # len(observation) == 4 => in cache: rayon / famille / fin_nom_produit ds la cache
  # -------------------------------------------------------------------------------
  # r'200903b_releves_QLMC.pdf' A PRIORI REDUNDANT (could further check)
  # some observations over several lines in disorder... not so many though...
  """
  master_period = []
  dict_observation_length = {}
  list_short_rows = []
  cache_observation_list = None
  list_reconstitutions_1 = []
  list_reconstitutions_2 = []
  for observation_index, observation in enumerate(data):
    # split on 2 spaces or more w/ exception: no space between store and date
    date_search = re.search(ur'[0-9]{2,2}/[0-9]{2,2}/[0-9]{4,4}', observation)
    if date_search:
      observation_list = re.split('\s{2,}', observation[:date_search.start()]) +\
                         re.split('\s{2,}', observation[date_search.start():])
    else:
      observation_list = re.split('\s{2,}', observation)
    # get rid of empty string generated in the process
    observation_list = [x for x in observation_list if x]  
    # if len is 3 or more, split between product name and store name when it was not done
    if len(observation_list) >= 3:
      list_split = get_split_on_brands(observation_list[2], list_shop_brands)
      if list_split:
        observation_list = observation_list[0:2] + list_split + observation_list[3:]
    # check row length
    dict_observation_length.setdefault(len(observation_list), [])\
      .append((observation_index, observation_list))
    # Normal line: len(observation_list) = 6
    if len(observation_list) < 3:
      list_short_rows.append((observation_index, observation_list))
    else:
      if len(observation_list) == 3 and not cache_observation_list:
        cache_observation_list = observation_list
      else:
        # if len is small and there is cache: append
        if len(observation_list) == 3 and cache_observation_list:
          observation_list = cache_observation_list[:2] +\
                             [observation_list[0]] +\
                             [cache_observation_list[2]]+\
                             observation_list[1:]
          list_reconstitutions_1.append((observation_index, observation_list))
        elif len(observation_list) == 4 and cache_observation_list:
          observation_list = cache_observation_list[:2] +\
                             [''.join([observation_list[0], cache_observation_list[2]])]+\
                             observation_list[1:]
          list_reconstitutions_2.append((observation_index, observation_list))
        elif cache_observation_list:
          print observation_index-1, cache_observation_list, 'was not attributed'
        cache_observation_list = None
        if len(observation_list) == 6:
          master_period.append(observation_list)
        else:
          print observation_index, observation_list, 'not written to master'
  # Check that first line is to be removed
  print master_period[0], '\n', master_period[1], '\n'
  master_period = master_period[1:]
  for observation_index, observation in enumerate(master_period):
    master_period[observation_index] = [elt.strip().replace('\x0c', '') for elt\
                                          in master_period[observation_index]]
  return [master_period, dict_observation_length, (list_reconstitutions_1,\
                                                   list_reconstitutions_2)]

def format_200909(data):
  """
  # len == 1: product title (rest at following line)
  # len == 2: price and date (rest is before)
  """
  data = data[1:-1] # get rid of first and last rows (one elt)
  master_period = []
  dict_observation_length = {}
  list_short_rows = []
  cache_observation_list = None
  list_cache_updates = []
  list_reconstitutions_1 = []
  list_reconstitutions_2 = []
  for observation_index, observation in enumerate(data):
    # split on 2 spaces or more w/ exception: no space between store and date
    date_search = re.search(ur'[0-9]{2,2}/[0-9]{2,2}/[0-9]{4,4}', observation)
    if date_search:
      observation_list = re.split('\s{2,}', observation[:date_search.start()]) +\
                         re.split('\s{2,}', observation[date_search.start():])
    else:
      observation_list = re.split('\s{2,}', observation)
    # get rid of empty string generated in the process
    observation_list = [x for x in observation_list if x]
    # if len is 3 or more, split between product name and store name when it was not done
    if len(observation_list) >= 3:
      list_split = get_split_on_brands(observation_list[2], list_shop_brands)
      if list_split:
        observation_list = observation_list[0:2] + list_split + observation_list[3:]
    # check row length
    dict_observation_length.setdefault(len(observation_list), [])\
      .append((observation_index, observation_list))
    # Normal line: len(observation_list) = 6... reconstitutions with len 1 and  len 4
    if len(observation_list) == 0:
      list_short_rows.append((observation_index, observation_list))
    else:
      # no cache => put in memory product name or beginning of row
      if (len(observation_list) == 1 or len(observation_list) == 4) and\
         (not cache_observation_list):
        cache_observation_list = observation_list
      # in cache: product name, still it's row where price and date are missing => update cache
      elif (len(observation_list) == 4 and cache_observation_list) and\
           (len(cache_observation_list) == 1):
        cache_observation_list = observation_list[:2] +\
                                 [''.join(cache_observation_list[0] + observation_list[2])] +\
                                 observation_list[3:]
        list_cache_updates.append(cache_observation_list)
      else:
        # case where product name (the bulk of it) precedes product info
        if len(observation_list) == 6 and cache_observation_list and len(cache_observation_list) == 1:
          observation_list = observation_list[:2] +\
                             [''.join(cache_observation_list[0] + observation_list[2])] +\
                             observation_list[3:]
          list_reconstitutions_1.append((observation_index, observation_list))
        # case where product family name and store precedes date and price
        elif len(observation_list) == 2 and cache_observation_list and len(cache_observation_list) == 4:
          observation_list = cache_observation_list + observation_list
          list_reconstitutions_2.append((observation_index, observation_list))
        elif cache_observation_list:
          print observation_index-1, cache_observation_list, 'was not attributed'
        cache_observation_list = None
        if len(observation_list) == 6:
          master_period.append(observation_list)
        else:
          print observation_list, 'not written to master'
  # Check that first line is to be removed
  print master_period[0], '\n', master_period[1], '\n'
  master_period = master_period[1:]
  for observation_index, observation in enumerate(master_period):
    master_period[observation_index] = [elt.strip().replace('\x0c', '') for elt\
                                          in master_period[observation_index]]
  return [master_period, dict_observation_length, (list_reconstitutions_1,\
                                                   list_reconstitutions_2,\
                                                   list_cache_updates)]

def print_dict_stats(dict_stat_des):
  for key, content in dict_stat_des.iteritems():
    print key, len(content)

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:/Bureau/Etienne_work/Data'):
  path_data = r'W:/Bureau/Etienne_work/Data'
else:
  path_data = r'C:/Users/etna/Desktop/Etienne_work/Data'
folder_source_json = r'/data_qlmc/data_source/data_json'

folder_source_pdftottext = r'/data_qlmc/data_source/data_pdf_qlmc'
list_folders_source_pdf = [r'/data_qlmc/data_source/data_pdf_qlmc/0_old_with_recent_format',
                           r'/data_qlmc/data_source/data_pdf_qlmc/1_previous_format',
                           r'/data_qlmc/data_source/data_pdf_qlmc/2_recent_format',
                           r'/data_qlmc/data_source/data_pdf_qlmc/3_forgotten_files']
path_pdftotext = path_data + folder_source_pdftottext

list_to_iterate = [(format_simple, list_folders_source_pdf[0], r'/200705_releves_QLMC','pd'),
                   (format_simple, list_folders_source_pdf[0], r'/200708_releves_QLMC','pd'),
                   (format_simple, list_folders_source_pdf[0], r'/200801_releves_QLMC','pd'),
                   (format_200804, list_folders_source_pdf[0], r'/200804_releves_QLMC','pd'),
                   (format_200903, list_folders_source_pdf[3], r'/200903_releves_QLMC','pd'),
                   (format_200909, list_folders_source_pdf[3], r'/200909_releves_QLMC','dp'),
                   (format_simple, list_folders_source_pdf[1], r'/201003_releves_QLMC','dp'),
                   (format_simple, list_folders_source_pdf[1], r'/201010_releves_QLMC','dp'),
                   (format_simple, list_folders_source_pdf[1], r'/201101_releves_QLMC','dp'),
                   (format_simple, list_folders_source_pdf[1], r'/201104_releves_QLMC','dp'),
                   (format_simple, list_folders_source_pdf[2], r'/201110_releves_QLMC','pd'),
                   (format_simple, list_folders_source_pdf[2], r'/201201_releves_QLMC','pd'),
                   (format_simple, list_folders_source_pdf[2], r'/201206_releves_QLMC','pd')]

# LOOP ON ALL FILES
master_check = []
for format_function, folder, file, order in list_to_iterate[0:1]:
  print file, '\n'
  # Read pdf with pdftotext
  data = read_pdftotext(path_data + folder + file + '.pdf', path_pdftotext)
  # Correct some specific problems
  if file == r'/200705_releves_QLMC':
    data = zip(data[:554692], data[554692:-1])
    data = [elt[0] + '  ' + elt[1] for elt in data]
  if file == r'/201010_releves_QLMC':
    data[385200] = data[385200].replace('02/11/201;01,72 "', '02/11/2010          1,72 ')
  # Format master (order, decode string)
  master, dict_len, list_reconstitutions = format_function(data)
  if order == 'dp':
    master = [row[0:4] + row[5:6] + row[4:5] for row in master]
  master = [[elt.decode('latin-1') for elt in row] for row in master]
  for row_id, row in enumerate(master):
    try:
      row[4] = float(row[4].replace(',','.'))
    except:
      row[4] = None
      print 'No float', file, row_id, row
  # Check consistency and encode json master
  familles, magasins, produits = get_preliminary_check(master)
  master_check.append((list_reconstitutions, familles, magasins, produits))
  enc_json(master, path_data + folder_source_json + file)
  # Print dict_len: can't store it since it contains data  
  print_dict_stats(dict_len)
  print '--------------------\n'

# EXTRACT ONE FILE
"""
path_file = path_data + list_folders_source_pdf[3] + r'/200909_releves_QLMC.pdf'
data = read_pdftotext(path_file, path_pdftotext)
master, dict_len, list_reconstitutions = format_200909(data)
familles, magasins, produits = get_preliminary_check(master)
"""

# PATH/ORDER REMINDER
"""
# rayon - famille - produit - magasin - prix - date
path_file_200708 = path_data + list_folders_source_pdf[0] + r'/200708_releves_QLMC.pdf'
path_file_200801 = path_data + list_folders_source_pdf[0] + r'/200801_releves_QLMC.pdf'
path_file_200804 = path_data + list_folders_source_pdf[0] + r'/200804_releves_QLMC.pdf'

# rayon - famille - produit - magasin - prix - date
path_file_200903 = path_data + list_folders_source_pdf[3] + r'/200903_releves_QLMC.pdf'

# rayon - famille - produit - magasin - date - prix
path_file_200909 = path_data + list_folders_source_pdf[3] + r'/200909_releves_QLMC.pdf'

# rayon - famille - produit - magasin - date - prix
path_file_201003 = path_data + list_folders_source_pdf[1] + r'/201003_releves_QLMC.pdf'
path_file_201010 = path_data + list_folders_source_pdf[1] + r'/201010_releves_QLMC.pdf'
path_file_201101 = path_data + list_folders_source_pdf[1] + r'/201101_releves_QLMC.pdf'
path_file_201104 = path_data + list_folders_source_pdf[1] + r'/201104_releves_QLMC.pdf'

# rayon - famille - produit - magasin - prix - date
path_file_201110 = path_data + list_folders_source_pdf[2] + r'/201110_releves_QLMC.pdf'
path_file_201201 = path_data + list_folders_source_pdf[2] + r'/201201_releves_QLMC.pdf'
path_file_201206 = path_data + list_folders_source_pdf[2] + r'/201206_releves_QLMC.pdf'
"""