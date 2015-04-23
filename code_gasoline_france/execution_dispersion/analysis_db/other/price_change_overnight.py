import json
import os, sys, codecs
from datetime import date, timedelta
import datetime
import time
import itertools
import pprint
import numpy as np
import matplotlib.pyplot as plt

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
# structure of the data folder should be the same
folder_source_prices_day = r'\data_gasoline\data_source\data_json_prices\current_prices'
folder_source_prices_night = r'\data_gasoline\data_source\data_json_prices\20130121-20130213_lea'
folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def date_range(start_date, end_date):
  """Creates a list of dates (string %Y%m%d)"""
  list_dates = []
  for n in range((end_date + timedelta(1) - start_date).days):
    temp_date = start_date + timedelta(n)
    list_dates.append(temp_date.strftime('%Y%m%d'))
  return list_dates

def get_formatted_file(path_file):
  list_observations = dec_json(path_file)
  keys = ['id_station', 'commune', 'nom_station','marque', 'prix', 'date']
  list_dict = []
  for observation in list_observations:
    list_dict.append(dict(zip(keys, observation)))
  return list_dict  

def build_master(get_formatted_file, list_folders_source_prices, file_extension, start_date, end_date, id_str, price_str, date_str, key_dico):
  """
  The function aggregates files i.e. lists of dicos to produce a master (incl. several components)
  So far it uses a function to read and format the raw files.. but that should be dropped later on
  ----
  Arguments description:
  - folder_source_prices: location of files
  - file_extension, start_date, end_date: files names must be : date + extension
  - id_str, price_str, date_str: names of id, price and date keys in file individual dicos
  - key_dico: all other keys in file individual dicos
  """
  master_dates = date_range(start_date, end_date)
  missing_dates = []
  master_dico_general_info = {}
  master_list_ids = []
  master_list_prices = []
  master_list_dates = []
  # order matters in the list, thus in the cartesian product
  list_file_paths = ['\\'.join(pair[::-1]) for pair in \
                list(itertools.product([date + file_extension for date in master_dates], list_folders_source_prices))]
  # duplicate each date and add 0 if day and 1 if night to fit with list_file_paths
  master_dates = [''.join(pair) for pair in list(itertools.product(master_dates,['0','1']))]
  for day_index, file_path in enumerate(list_file_paths):
    if os.path.exists(file_path):
      temp_master_list = get_formatted_file(file_path)
      for individual in temp_master_list:
        if individual[id_str] in master_list_ids:
          individual_index = master_list_ids.index(individual[id_str])
          for original_key, new_key in key_dico.iteritems():
            if individual[original_key] != master_dico_general_info[individual[id_str]][new_key][-1][0]:
              master_dico_general_info[individual[id_str]][new_key].append((individual[original_key], day_index))
        else:
          master_list_ids.append(individual[id_str])
          individual_index = master_list_ids.index(individual[id_str])
          master_dico_general_info[individual[id_str]] = {'rank': individual_index}
          for original_key, new_key in key_dico.iteritems():
            master_dico_general_info[individual[id_str]][new_key] = [(individual[original_key], day_index)]
          master_list_prices.append([])
          master_list_dates.append([])
        # fill price/date holes (either because of missing dates or individuals occasionnally missing)
        while len(master_list_prices[individual_index]) < day_index:
          master_list_prices[individual_index].append(None)
        master_list_prices[individual_index].append(individual[price_str])
        while len(master_list_dates[individual_index]) < day_index:
          master_list_dates[individual_index].append(None)
        master_list_dates[individual_index].append(individual[date_str])
    else:
      missing_dates.append(date)
  # add None if list of prices/dates shorter than nb of days (not for dates so far)
  nb_periods = len(list_file_paths)
  for list_prices in master_list_prices:
    while len(list_prices) < nb_periods:
      list_prices.append(None)
  for list_dates in master_list_dates:
    while len(list_dates) < nb_periods:
      list_dates.append(None)
  master_price = {'list_dates' : master_dates,
                  'list_missing_dates' : missing_dates, 
                  'dict_general_info': master_dico_general_info,
                  'list_ids' : master_list_ids, 
                  'list_indiv_prices' : master_list_prices,
                  'list_indiv_dates' : master_list_dates}
  return master_price

def fill_holes(master_price, lim):
  for individual_index in range(len(master_price['list_indiv_prices'])):
    for day_index in range(len(master_price['list_indiv_prices'][individual_index])):
      if master_price['list_indiv_prices'][individual_index][day_index] is None:
        relative_day = 0
        while master_price['list_indiv_prices'][individual_index][day_index + relative_day] is None \
              and day_index + relative_day < len(master_price['list_dates']) - 1:
          relative_day += 1
        if master_price['list_dates'][day_index] == master_price['list_indiv_dates'][individual_index][day_index + relative_day]:
          master_price['list_indiv_prices'][individual_index][day_index] = master_price['list_indiv_prices'][individual_index][day_index + relative_day]
        elif day_index > 0 and day_index + relative_day != len(master_price['list_dates'])-1 and relative_day < lim:
        # replaces also if change on the missing date... which makes data inaccurate (???)
          master_price['list_indiv_prices'][individual_index][day_index] = master_price['list_indiv_prices'][individual_index][day_index - 1]
  return master_price

def analyse_remaining_holes(master_price):
  list_dilettante = []
  for individual_index in range(len(master_price['list_indiv_prices'])):
    first_non_none = 0
    last_non_none = 0
    while master_price['list_indiv_prices'][individual_index][first_non_none] is None:
      first_non_none += 1
    while master_price['list_indiv_prices'][individual_index][::-1][last_non_none] is None:
      last_non_none += 1
    last_non_none= len(master_price['list_indiv_prices'][individual_index]) - last_non_none
    if None in master_price['list_indiv_prices'][individual_index][first_non_none:last_non_none]:
      list_dilettante.append(individual_index)
  return list_dilettante

def convert_master_price_to_float(master_price):
  """Converts a list of lists of string to a list of lists of float"""
  list_price_lists = []
  for list_price in master_price['list_indiv_prices']:
    list_price_float = []
    for price in list_price:
      try:
        list_price_float.append(float(price))
      except:
        list_price_float.append(None)
    list_price_lists.append(list_price_float)
  master_price['list_indiv_prices'] = list_price_lists

def get_id(rank, master_price):
  return master_price['list_ids'][rank]

def get_rank(id, master_price):
  return master_price['dict_general_info'][id]['rank']

def get_plot_prices(list_of_ranks, master_price):
  plt.figure()
  for rank in list_of_ranks:
    price_array = np.array([x if x not in [None, ' --'] else np.nan for x in master_price['list_indiv_prices'][rank]])
    price_array_ma = np.ma.masked_array(price_array, np.isnan(price_array))
    axis = np.array([i for i in range(len(master_price['list_indiv_prices'][rank]))])
    plt.plot(axis, price_array_ma, label='%s%s' %(get_id(rank, master_price), master_price['dict_general_info'][get_id(rank, master_price)]['brand_station'][0][0]))
    plt.legend(loc = 4)
  plt.show()
  
example = dec_json(path_data + folder_source_prices_day + r'\20130523_diesel_gas_prices')

list_folders_source_prices = [path_data + folder_source_prices_day, path_data + folder_source_prices_night]
file_extension = '_diesel_gas_prices'
start_date = date(2013,5,21)
end_date = date(2013,5,31)
id_str = 'id_station'
price_str = 'prix'
date_str = 'date'
key_dico = {'commune' : 'city_station', 'nom_station' : 'name_station', 'marque': 'brand_station'}
master_test = build_master(get_formatted_file, list_folders_source_prices, file_extension, start_date, end_date, id_str, price_str, date_str, key_dico)
master_test = fill_holes(master_test, 5)
dilettante = analyse_remaining_holes(master_test)
convert_master_price_to_float(master_test)

list_index_changes = []
for i in range(0,3):
  period_changes = []
  for index_station, list_prices in enumerate(master_test['list_indiv_prices']):
    if list_prices[i] and list_prices[i+1] and list_prices[i+2]:
      if list_prices[i]== list_prices[i+2] and list_prices[i]!= list_prices[i+1]:
        period_changes.append(index_station)
  list_index_changes.append(period_changes)

# what seems to be the most comprehensive
for ind in list_index_changes[1]:
  print 'id_station', master_test['list_ids'][ind]
  pprint.pprint(master_test['dict_general_info'][master_test['list_ids'][ind]])
  print master_test['list_indiv_prices'][ind], '\n'

get_plot_prices(list_index_changes[1], master_test)

"""
#Function as an argument of another function
def x(a,b):
  print "param 1 %s param 2 %s"%(a,b)
def y(z,t,m):
  z(*t)
  print m
y(x,("hello","manuel"), 5)
"""