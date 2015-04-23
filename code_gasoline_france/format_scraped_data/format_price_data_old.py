import json
import os, sys, codecs
from datetime import date, timedelta
import datetime
import time
import re

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:/Bureau/Etienne_work/Data'):
  path_data = r'W:/Bureau/Etienne_work/Data'
elif os.path.exists(r'C:/Users/etna/Desktop/Etienne_work/Data'):
  path_data = r'C:/Users/etna/Desktop/Etienne_work/Data'
else:
  path_data = r'/mnt/Data'
# structure of the data folder should be the same
folder_source_prices_diesel = r'\data_gasoline\data_source\data_json_prices\20110904_20120514_lea'
folder_source_prices_gas = r'\data_gasoline\data_source\data_json_prices\20110903_20120514_unl'

def format_price_2011_diesel(path, output_list = True):
  keys = ['id_station', 'commune', 'nom_station','marque', 'prix', 'date']
  input_file = codecs.open(path, 'rb', 'utf-8')
  data = input_file.read()
  list_rows = [row for row in data.split('\r\n') if row]
  list_ids = []
  list_stations = []
  for row in list_rows:
    re_1 = re.search(ur",\s[0-9],[0-9]{2,3}|,\s--", row)
    if re_1 is not None:
      split_point = re_1.start()
      # gas station information part
      gas_station_info = row[:split_point].split(',')
      id = gas_station_info[0]
      city_station = gas_station_info[1]
      name_station = u' '.join(gas_station_info[2:-1])
      brand_station = gas_station_info[-1]
      # gas station price date part
      price_and_date = re.findall(ur",\s([0-9],[0-9]{2,3}|--|[0-9]{2}/[0-9]{2}/[0-9]{2})", row)
      if len(price_and_date) == 2:
        price = price_and_date[0].replace(u',', u'.')
        date = price_and_date[1]
        station = [id, city_station, name_station, brand_station, price, date]
        if station[0] not in list_ids:
          if output_list:
            list_stations.append(tuple(station))
          else:
            list_stations.append(dict(zip(keys, station)))
          list_ids.append(station[0])
        """
        else:
          print 'duplicate', row
        """
      else:
        print 'pbm with regex 2', row
    else:
      print 'pbm with regex 1', row
  return list_stations

def format_price_2011_gas(path, output_list = True):
  keys = ['id_station', 'commune', 'nom_station', 'marque', 'prix_e10', 'date_e10', 'prix_sp95', 'date_sp95']
  input_file = codecs.open(path, 'rb', 'utf-8')
  data = input_file.read()
  list_rows = [row for row in data.split('\r\n') if row]
  list_ids = []
  list_stations = []
  for row in list_rows:
    re_1 = re.search(ur",\s[0-9],[0-9]{2,3}|,\s--", row)
    if re_1 is not None:
      split_point = re_1.start()
      # gas station information part
      gas_station_info = row[:split_point].split(',')
      id = gas_station_info[0]
      city_station = gas_station_info[1]
      name_station = u' '.join(gas_station_info[2:-1])
      brand_station = gas_station_info[-1]
      # gas station price date part
      price_and_date = re.findall(ur",\s([0-9],[0-9]{2,3}|--|[0-9]{2}/[0-9]{2}/[0-9]{2})", row)
      if len(price_and_date) == 4:
        price_1 = price_and_date[0].replace(u',', u'.')
        date_1 = price_and_date[1]
        price_2 = price_and_date[2].replace(u',', u'.')
        date_2 = price_and_date[3]
        station = [id, city_station, name_station, brand_station, price_1, date_1, price_2, date_2]
        if station[0] not in list_ids:
          if output_list:
            list_stations.append(tuple(station))
          else:
            list_stations.append(dict(zip(keys, station)))
          list_ids.append(station[0])
        """
        else:
          print 'duplicate', row
        """
      else:
        print 'pbm with regex 2', row
    else:
      print 'pbm with regex 1', row
  return list_stations

path_file_diesel = path_data + folder_source_prices_diesel + r'\20111006ga.txt'
path_file_gas = path_data + folder_source_prices_gas + r'\20111006sp.txt'

diesel = format_price_2011_diesel(path_file_diesel)
gas = format_price_2011_gas(path_file_gas)

def loop_and_format(format_function, folder_source):
  list_formatted_data = []
  for file_name in os.listdir(folder_source):
    if re.match('[0-9]{8}[^0-9]', file_name):
      print file_name
      formatted_file = format_function(folder_source + r'/' + file_name)
      list_formatted_data.append(formatted_file)
  return list_formatted_data

# list_diesel = loop_and_format(format_price_2011_diesel, path_data + folder_source_prices_diesel)
# list_gas = loop_and_format(format_price_2011_gas, path_data + folder_source_prices_gas)