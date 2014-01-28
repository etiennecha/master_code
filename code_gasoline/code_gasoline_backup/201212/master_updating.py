import json
import os
import codecs
import string
import math
import datetime
import time
from datetime import date, timedelta
import sys
sys.path.append(r'C:\Users\etna\Desktop\final_gasoline_project\scripts\bu')
from master_geocoding import *

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

json_master_path = r'C:\Users\etna\Desktop\final_gasoline_project\scripts\bu'
master_1 = 'master_3'
master_and_missing_dates = dec_json(r'%s\%s\dates' %(json_master_path, master_1))
master_gas_stations_id_and_prices = dec_json(r'%s\%s\lists_gas_stations' %(json_master_path, master_1))
master_dico_gas_stations = dec_json(r'%s\%s\dico_gas_stations' %(json_master_path, master_1))
master_dates = master_and_missing_dates[0]
missing_dates = master_and_missing_dates[1]
master_gas_stations_id = master_gas_stations_id_and_prices[0]
master_gas_stations_prices = master_gas_stations_id_and_prices[1]
rotterdam_prices = dec_rotterdam(r'C:\Users\etna\Desktop\final_gasoline_project\info_others\rotterdam\rotterdam_unleaded.txt')
dico_brands = dec_json(r'%s\%s\dico_brands' %(json_master_path, master_1))

# Check that the brand dictionnary matches all brands in the gas stations dico
list_of_brands = check_gas_stations_brands(master_dico_gas_stations, dico_brands)

# MY INFO ON GAS STATION CHARACTERISTICS
old_gas_stations_details = dec_json('C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\fusiontabletest\\jsondb_competition.txt')

# UPDATE master_dico_gas_stations WITH MY INFOS
list_services_string = ['ser%s' %i for i in range(1,21)]
for old_gas_station in old_gas_stations_details:
  # list of services
  gas_station_service_list = []
  for service_string in list_services_string:
    gas_station_service_list.append(old_gas_station[service_string])
  try:
    master_dico_gas_stations[old_gas_station['id_station']]['service_list'] = gas_station_service_list
  except:
    pass
  # data from first geocoding attempt (with Google)
  try:
    master_dico_gas_stations[old_gas_station['id_station']]['gps_coordinates_1'] = [old_gas_station['lat'], old_gas_station['long'], old_gas_station['score']]
  except:
    pass
  # data from second geocoding attempt (with Google, not sure what's best, see score and distance between both)
  try:
    temp_lat = old_gas_station['geolocalisation']['results'][0]['geometry']['location']['lat']
    temp_long = old_gas_station['geolocalisation']['results'][0]['geometry']['location']['lng']
    temp_score = old_gas_station['geolocalisation']['results'][0]['geometry']['location_type']
    master_dico_gas_stations[old_gas_station['id_station']]['gps_coordinates_2'] = [temp_lat, temp_long, temp_score]
  except:
    pass
  # competition
  try:
    master_dico_gas_stations[old_gas_station['id_station']]['competitors_1km'] = old_gas_station['competitors1']
    master_dico_gas_stations[old_gas_station['id_station']]['competitors_3km'] = old_gas_station['competitors3']
    master_dico_gas_stations[old_gas_station['id_station']]['competitors_10km'] = old_gas_station['competitors10']
  except:
    pass
  # highway
  try:
    master_dico_gas_stations[old_gas_station['id_station']]['highway'] = old_gas_station['autoroute']
  except:
    pass
  # street (a bit 'risky'... should check with city)
  try:
    master_dico_gas_stations[old_gas_station['id_station']]['street_station'] = old_gas_station['rue']
  except:
    pass
    
# Suppress own id in competitor lists (was stupidly done before...)
for id, details in master_dico_gas_stations.iteritems():
  for competition_distance in ['competitors_%skm' %i for i in [1,3,10]]:
    try:
      details[competition_distance].remove(id)
    except:
      print 'no info on competition for', id
      
# In fact drop it for now...
for id, details in master_dico_gas_stations.iteritems():
  for competition_distance in ['competitors_%skm' %i for i in [1,3,10]]:
    try:
      del(details[competition_distance])
    except:
      pass

enc_stock_json(master_dico_gas_stations, '%s\\%s\\master_dico_gas_stations_my_info' %(json_master_path, master_1))

# Load info file received from Ronan Le Saout
old_rls_data_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\adr_and_servs\\data_rls\\data_rls.csv'
f = open(old_rls_data_path,'r')
g = f.read()
old_rls_data = g.split('\n')
dico_gas_stations_rls = {}
for line in old_rls_data[1:]:
  if line != '':
    dico_gas_stations_rls[line.split(',')[0]] = dict(zip(old_rls_data[0].split(','), line.split(',')))
# Convert gps coordinates to float
for id, details in dico_gas_stations_rls.iteritems():
  try:
    details['gps_coordinates_rls'] = [float(details['latDeg']), float(details['longDeg'])]
  except:
    pass

# Update master dico with rls data
for id, details in dico_gas_stations_rls.iteritems():
  try:
    master_dico_gas_stations[id]['gps_coordinates_rls'] = details['gps_coordinates_rls']
    master_dico_gas_stations[id]['TAU2010'] = details['TAU2010']
    master_dico_gas_stations[id]['INSEE_code'] = details['CodeCom']
    master_dico_gas_stations[id]['INSEE_code'] = details['CodeCom']
    master_dico_gas_stations[id]['Ninf2All'] = details['Ninf2All']
    master_dico_gas_stations[id]['Ninf5All'] = details['Ninf5All']
    master_dico_gas_stations[id]['Ninf10All'] = details['Ninf10All']
    master_dico_gas_stations[id]['Ninf2LD'] = details['Ninf2LD']
    master_dico_gas_stations[id]['Ninf5LD'] = details['Ninf5LD']
    master_dico_gas_stations[id]['Ninf10LD'] = details['Ninf10LD']
    master_dico_gas_stations[id]['DistMinAll'] = details['DistMinAll']
    master_dico_gas_stations[id]['DistMinSuper'] = details['DistMinSuper']
  except:
    pass

# temporary: update:
for id, details in master_dico_gas_stations.iteritems():
  if 'service_list' not in details.keys():
    details['service_list'] = [u'.' for x in range(0,20)]
  if 'highway' not in details.keys():
    details['highway'] = u'.'

latest_gas_stations_info = dec_json('C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\adr_and_servs\\master_adr_servs.txt')

for k,v in master_dico_gas_stations.iteritems():
	try:
		v['highway']=latest_gas_stations_info[k]['autoroute']
    v['service_list']=latest_gas_stations_info[k]['services']
	except:
		pass

enc_stock_json(dico_gas_stations_rls, '%s\\%s\\dico_gas_stations_rls' %(json_master_path, master_1))
enc_stock_json(master_dico_gas_stations, '%s\\%s\\dico_gas_stations' %(json_master_path, master_1))