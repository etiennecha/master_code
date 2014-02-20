import os, sys
import httplib, urllib2
import urllib
import cookielib
from BeautifulSoup import BeautifulSoup
import re
from datetime import date
import json

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
# structure of the data folder should be the same
folder_source_some_prices = r'\data_gasoline\data_source\data_json_prices\current_prices'
folder_source_info_stations = r'\data_gasoline\data_source\data_stations\data_gouv_stations\raw'

def enc_stock_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def clean_souptag(souptag):
  cleaned_list = re.split(ur'<p class="hours">|<p>|<strong>|</strong>|<br\s?/>(.*)<p>|<strong>|</strong>|<br\s?/>', unicode(souptag))
  cleaned_list = [elt.replace('\n', '').replace('</p>','').strip() for elt in cleaned_list if elt is not None and elt.replace('\n', '').replace('</p>','').strip()  != '']
  return cleaned_list

def get_station_info(id):
  base_url = r'http://www.prix-carburants.economie.gouv.fr/itineraire/infos/'
  response = urllib2.urlopen(base_url + id)
  data = response.read()
  soup = BeautifulSoup(data)
  name_and_address_bloc = soup.find('p')
  name_and_brand = re.findall('<strong>(.*?)</strong>', unicode(name_and_address_bloc))
  address = clean_souptag(re.search(ur'.*</strong><br\s?/>(.*?)</p>', unicode(name_and_address_bloc).replace('\n','')).group(1))
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

# use any file and get its id list: typically dict_name.keys() if dict
price_file = dec_json(path_data + folder_source_some_prices + r'\20131114_diesel_gas_prices')
list_ids = [elt[0] for elt in price_file] #for the example

dict_info_stations = {}
list_field_keys = ['name', 'address', 'hours', 'closed_days', 'services']
for id in list_ids:
  try:
    dict_info_stations[id] = dict(zip(list_field_keys, get_station_info(id)))
  except:
    print 'couldnt get info for', id

# enc_stock_json(dict_info_stations, path_data + folder_source_info_stations + r'\20131115_diesel_info_stations')