import json
import os, sys, codecs
from datetime import date, timedelta
import datetime
import time
import re

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())
  
def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)
   
def daterange(start_date, end_date):
  list_dates = []
  for n in range((end_date + timedelta(1) - start_date).days):
    temp_date = start_date + timedelta(n)
    list_dates.append(temp_date.strftime('%Y%m%d'))
  return list_dates

txt_path = 'C:\Users\Etienne\Desktop\Programmation\Python\Scrapping_project_staser\outcomeoftest'

def get_scrapping_content(path):
  keys = ['id_station', 'commune', 'nom_station','marque', 'prix', 'date']
  first_part_re = re.compile(r"(,\s[0-9],[0-9]{2,3})|(,\s--)")
  list_id_stations = []
  list_results = []
  inputFile = codecs.open(path, 'rb', 'utf-8')
  inputFile.read(0)
  dbtext = inputFile.read()
  for line in dbtext.split('\r\n'):
    re_1 = first_part_re.search(line)
    if re_1 is not None:
      split_point = re_1.start()
      # gas station information part
      id = line[:split_point].split(',')[0][3:]
      city_station = line[:split_point].split(',')[1]
      name_station = ' '.join(line[:split_point].split(',')[2:-1])
      brand_station = line[:split_point].split(',')[-1]
      if len(line[:split_point].split(',')) != 4:
        print [id, city_station, name_station, brand_station]
      # gas station price part (if 4, : no price, 5: one, 6: two)
      start_price = split_point + 1
      if len(line[start_price:].split(',')) == 6:
        price_1 = '.'.join(line[start_price:].split(',')[0:2])
        date_1 = line[start_price:].split(',')[2]
        price_2 = '.'.join(line[start_price:].split(',')[3:5])
        date_2 = line[start_price:].split(',')[5]
      elif len(line[start_price:].split(',')) == 5:
        # depends is first or second price is missing
        if line[start_price:].split(',')[0] == ' --':
          price_1 = line[start_price:].split(',')[0]
          date_1 = line[start_price:].split(',')[1]
          price_2 = '.'.join(line[start_price:].split(',')[2:4])
          date_2 = line[start_price:].split(',')[4]
        else:
          price_1 = '.'.join(line[start_price:].split(',')[0:2])
          date_1 = line[start_price:].split(',')[2]
          price_2 = line[start_price:].split(',')[3]
          date_2 = line[start_price:].split(',')[4]
      station = [id, city_station, name_station, brand_station] + [price_1, date_1, price_2, date_2]
      if station[0] not in list_id_stations:
        list_results.append(dict(zip(keys, station[:4] + station[-2:])))
        list_id_stations.append(station[0])
    else:
      print line
  return list_results

start_date = date(2011,9,4)
end_date = date(2012,5,14)

master_dates = daterange(start_date, end_date)
missing_dates = []
master_dico_gas_stations = {}
master_list_gas_stations_id = []
master_list_gas_stations_prices = []

# Creation des fichiers principaux (a adapter pr maj)

for date in master_dates:
  day_count = master_dates.index(date)
  if os.path.exists('%s\sp%s.txt' %(txt_path, date)):
    temp_list_gas_stations = get_scrapping_content('%s\sp%s.txt' %(txt_path, date))
    # ici on recupere liste de dictionnaires ['id_station', 'commune', 'nom_station', 'marque', 'prix', 'date']
    for gas_station in temp_list_gas_stations:
      try:
        gas_station_index = master_list_gas_stations_id.index(gas_station['id_station'])
        try:
          if gas_station['marque'] != master_dico_gas_stations[gas_station['id_station']]['brand_station'][len(master_dico_gas_stations[gas_station['id_station']]['brand_station'])-1]:
            master_dico_gas_stations[gas_station['id_station']]['brand_station'].append(gas_station['marque'])
            master_dico_gas_stations[gas_station['id_station']]['brand_changes'].append(day_count)
        except:
          print 'pbm', gas_station['id_station'], date
      except:
        master_list_gas_stations_id.append(gas_station['id_station'])
        gas_station_index = master_list_gas_stations_id.index(gas_station['id_station'])
        master_list_gas_stations_prices.append([])
        master_dico_gas_stations[gas_station['id_station']] = {'rank_station' : gas_station_index,
                                                               'name_station' : gas_station['nom_station'],
                                                               'city_station' : gas_station['commune'],
                                                               'brand_station' : [gas_station['marque']],
                                                               'brand_changes' : [day_count]}
      while len(master_list_gas_stations_prices[gas_station_index]) < day_count:
        master_list_gas_stations_prices[gas_station_index].append(None)
      master_list_gas_stations_prices[gas_station_index].append(gas_station['prix'])
  else:
    missing_dates.append(date)
    for list_of_prices in master_list_gas_stations_prices:
      # for stations no more registered on website: filled of None up to last missing date
      while len(list_of_prices) < day_count:
        list_of_prices.append(None)
      list_of_prices.append(None)

# dead gas stations will have a short length compared to other: fill with None? (except if set days to one more day than actually exists...)

# Combler les trous
for missing_date in missing_dates:
  date_missing_date = datetime.date(*time.strptime(missing_date, '%Y%m%d')[0:3])
  date_day_after = date_missing_date + timedelta(1)
  missing_spell = 1
  while date_day_after.strftime("%Y%m%d") in missing_dates:
    date_day_after += timedelta(1)
    missing_spell += 1
  date_to_search = date_day_after.strftime("%Y%m%d")
  count_of_date_to_change = master_dates.index(missing_date)
  temp_list_gas_stations = get_scrapping_content('%s\sp%s.txt' %(txt_path, date_to_search))
  for gas_station in temp_list_gas_stations:
    try:
      if '20'+gas_station['date'][7:9] + gas_station['date'][4:6] + gas_station['date'][1:3] == missing_date:
        master_list_gas_stations_prices[master_dico_gas_stations[gas_station['id_station']]['rank_station']][count_of_date_to_change] = gas_station['prix']
      else:
        master_list_gas_stations_prices[master_dico_gas_stations[gas_station['id_station']]['rank_station']][count_of_date_to_change] = master_list_gas_stations_prices[master_dico_gas_stations[gas_station['id_station']]['rank_station']][count_of_date_to_change - 1]
    except:
      print 'pbm', gas_station

# Recherche les None restants ds des chaines (prix d'une station particuliere non renseigne tandis que les autres prix sont dispos)
for price_list_ind in range(0,len(master_list_gas_stations_prices)):
  first_non_none = 0
  while master_list_gas_stations_prices[price_list_ind][first_non_none] is None:
    first_non_none +=1
  last_non_none = 0
  while master_list_gas_stations_prices[price_list_ind][::-1][last_non_none] is None:
    last_non_none +=1
  if None in master_list_gas_stations_prices[price_list_ind][first_non_none:-last_non_none]:
    print price_list_ind

json_master_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\json_master'
master_1 = 'master_unleaded'
enc_stock_json([master_dates, missing_dates], '%s\\%s\\dates' %(json_master_path, master_1))
enc_stock_json([master_list_gas_stations_id, master_list_gas_stations_prices], '%s\\%s\\lists_gas_stations' %(json_master_path, master_1))
enc_stock_json(master_dico_gas_stations, '%s\\%s\\dico_gas_stations' %(json_master_path, master_1))

"""
test_file = 'sp20110920.txt'
path_test = '%s\%s' %(txt_path, test_file)
list_stations_test = get_scrapping_content(path_test)
"""