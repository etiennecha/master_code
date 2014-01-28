import json
import os
import codecs
import string
import math
import datetime
import time
from datetime import date, timedelta
import sys
sys.path.append('C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\final_code')
from master_geocoding import *

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

json_master_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\json_master'
master_1 = 'master_unleaded'

rotterdam_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\masterpgmtest\\rotterdam\\rotterdam_unleaded.txt'
historic_gas_stations_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\fusiontabletest\\jsondb_competition.txt'
rls_data_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\adr_and_servs\\data_rls\\data_rls.csv'
latest_gas_stations_info = dec_json('C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\adr_and_servs\\master_adr_servs.txt')

master_and_missing_dates = dec_json('%s\\%s\\dates' %(json_master_path, master_1))
master_gas_stations_id_and_prices = dec_json('%s\\%s\\lists_gas_stations' %(json_master_path, master_1))
master_dico_gas_stations = dec_json('%s\\%s\\dico_gas_stations' %(json_master_path, master_1))
master_dates = master_and_missing_dates[0]
missing_dates = master_and_missing_dates[1]
master_gas_stations_id = master_gas_stations_id_and_prices[0]
master_gas_stations_prices = master_gas_stations_id_and_prices[1]
rotterdam_prices = dec_rotterdam(rotterdam_path)
dico_brands = dec_json('%s\\%s\\dico_brands' %(json_master_path, master_1))

# Check that all brands are included in the brand dictionnary
list_of_brands = check_gas_stations_brands(master_dico_gas_stations, dico_brands)

# Load old info on gas stations characteristics (could add highway file) and restructure
list_historic_gas_stations_details = dec_json(historic_gas_stations_path)
dico_historic_gas_stations_details = {}
for station_info in list_historic_gas_stations_details:
  dico_historic_gas_stations_details[station_info['id_station']] = station_info
list_services_str = ['ser%s' %i for i in range(1,21)]
for id, details in dico_historic_gas_stations_details.iteritems():
  details['service_list'] = []
  for service_str in list_services_str:
    details['service_list'].append(details[service_str])
  if 'lat' in details.keys():
    details['gps_coordinates_1'] = [details['lat'], details['long'], details['score']]
  if 'geolocalisation' in details.keys():
    temp_lat = details['geolocalisation']['results'][0]['geometry']['location']['lat']
    temp_long = details['geolocalisation']['results'][0]['geometry']['location']['lng']
    temp_score = details['geolocalisation']['results'][0]['geometry']['location_type']
    details['gps_coordinates_2'] = [temp_lat, temp_long, temp_score]
  historic_competition_info = ['competitors1', 'competitors3', 'competitors10']
  for competition_info in historic_competition_info:
    if competition_info in details.keys():
      del(details[competition_info]) 
  try:
    master_dico_gas_stations[id].update(details)
  except:
    pass

# Load info file received from Ronan Le Saout
# Some gps coordinates are not floats thus can't be converted (error)
dico_gas_stations_rls = {}
file_rls = open(rls_data_path,'r')
data_rls = file_rls.read()
for line in data_rls.split('\n')[1:]:
  if line != '':
    dico_gas_stations_rls[line.split(',')[0]] = dict(zip(data_rls.split('\n')[0].split(','), line.split(',')))
for id, details in dico_gas_stations_rls.iteritems():
  try:
    details['gps_coordinates_rls'] = [float(details['latDeg']), float(details['longDeg'])]
  except:
    pass
  if id in master_dico_gas_stations.keys():
    master_dico_gas_stations[id].update(dico_gas_stations_rls[id])

# Temporary, updates
for id, details in master_dico_gas_stations.iteritems():
  if 'service_list' not in details.keys():
    details['service_list'] = [u'.' for x in range(0,20)]
  if 'highway' not in details.keys():
    details['highway'] = '.'
  if id in latest_gas_stations_info.keys() and 'autoroute' in latest_gas_stations_info[id]:
    details['highway'] =  latest_gas_stations_info[id]['autoroute']

#enc_stock_json(dico_gas_stations_rls, '%s\\%s\\dico_gas_stations_rls' %(json_master_path, master_1))
#enc_stock_json(master_dico_gas_stations, '%s\\%s\\dico_gas_stations' %(json_master_path, master_1))