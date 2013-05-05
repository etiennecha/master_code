import httplib, urllib2
import urllib
from bs4 import BeautifulSoup
import re, string
import sys
import json
from datetime import date
import cookielib

json_folder = r'C:\Users\etna\Desktop\20120218_final_gasoline_project\data_stations\data_info_stations_prix_carb'
json_folder_prices = r'C:\Users\etna\Desktop\20120218_final_gasoline_project\data_prices\20130121-20130213_lea'

def enc_stock_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def clean_souptag(souptag):
  cleaned_list = re.split('<p class="hours">|<p>|<strong>|</strong>|<br/>(.*)<p>|<strong>|</strong>|<br/>', unicode(souptag))
  cleaned_list = [elt.replace('\n', '').replace('</p>','').strip() for elt in cleaned_list if elt is not None and elt.replace('\n', '').replace('</p>','').strip()  != '']
  return cleaned_list

def get_station_info(id):
  base_url = 'http://www.prix-carburants.economie.gouv.fr/itineraire/infos/'
  response = urllib2.urlopen(base_url + id)
  data = response.read()
  soup = BeautifulSoup(data)
  name_and_address_bloc = soup.find('p')
  name_and_brand = re.findall('<strong>(.*?)</strong>', unicode(name_and_address_bloc))
  address = clean_souptag(re.search('.*</strong><br/>(.*?)</p>', unicode(name_and_address_bloc).replace('\n','')).group(1))
  opening_hours_bloc = soup.findAll('p', {'class': 'hours'})
  opening_hours = clean_souptag(opening_hours_bloc[0])
  if len(opening_hours_bloc) == 2:
    closed_days = clean_souptag(opening_hours_bloc[1])
  else:
    closed_days = None
  if len(opening_hours_bloc) > 2:
    print id, opening_hours_bloc
  services_bloc = soup.find('p', {'class': 'services'})
  services = services_bloc.findAll('img', {'src': re.compile('/bundles/public/images/pictos/service_.*')})
  list_services = [service['alt'] for service in services]
  return [name_and_brand, address, opening_hours, closed_days, list_services]

# use any file and get its id list: typically dico_name.keys()

price_file = dec_json(json_folder_prices + r'\20130213_diesel_gas_prices')
list_ids = [elt[0] for elt in price_file] #for the example

dict_info_stations = {}
list_field_keys = ['name', 'address', 'hours', 'closed_days', 'services']
for id in list_ids:
  try:
    dict_info_stations[id] = dict(zip(list_field_keys, get_station_info(id)))
  except:
    print 'couldnt get info for', id

enc_stock_json(dict_info_stations, json_folder + r'\20130220_diesel_info_stations')