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
folder_current_prices = r'\data_gasoline\data_source\data_json_prices\current_prices'

def enc_stock_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def get_list_prices(fuel_type):
  """
  Returns a list of lists containing station info (incl. daily price)
  Station info sublists are lists of form [[id], [info], [price]]
  
  @param fuel_type  leaded (diesel) = 1, unleaded (essence) = 'a'
  """
  # build urllib2 opener
  cookie_jar = cookielib.LWPCookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
  opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')]
  urllib2.install_opener(opener)
  # welcome page: get token
  website_url = 'http://www.prix-carburants.economie.gouv.fr'
  response = urllib2.urlopen(website_url)
  data = response.read()
  soup = BeautifulSoup(data)
  token = soup.find('input', {'type' : 'hidden', 'id':'recherche_recherchertype__token'})['value']
  print 'token is', token
  # queries with token to fill list_station
  list_stations = []
  for i in range(1, 96):
    query = {'_recherche_recherchertype[choix_carbu]' : fuel_type,
             '_recherche_recherchertype[localisation]' : '%02d' %i,
             '_recherche_recherchertype[_token]' : token}
    param = urllib.urlencode(query)
    response_2 = urllib2.urlopen('http://www.prix-carburants.economie.gouv.fr', param)
    data_2 = response_2.read()
    soup_2 = BeautifulSoup(data_2)
    # get page with all results
    recherche_url = 'http://www.prix-carburants.economie.gouv.fr/recherche/?sort=commune&direction=asc&page=1&lettre=%23&limit='
    response_3 = urllib2.urlopen(recherche_url)
    data_3 = response_3.read()
    soup_3 = BeautifulSoup(data_3)
    stations_blocs = soup_3.findAll('tr', {'class' : re.compile('data.*')})
    list_dpt_stations = []
    for station_bloc in stations_blocs:
      id_station = station_bloc['id']
      info_station = station_bloc.findAll('td', {'class' : 'pointer'})
      price_station = station_bloc.findAll('td', {'class' : 'pointer center chiffres'})
      info_station = [unicode(info.string) for info in info_station]
      price_station = [unicode(price.string) for price in price_station]
      list_dpt_stations.append([id_station] + info_station + price_station)
    print len(list_dpt_stations), 'stations ds le departement', i
    list_stations += list_dpt_stations
  return list_stations

list_essence = get_list_prices('a')
list_diesel = get_list_prices(1)
today_date = date.today().strftime("%y%m%d")
print today_date
enc_stock_json(list_essence, '%s\\20%s_essence_gas_prices' %(path_data + folder_current_prices, today_date))
enc_stock_json(list_diesel, '%s\\20%s_diesel_gas_prices' %(path_data + folder_current_prices, today_date))

list_sp98 = get_list_prices(6)
enc_stock_json(list_sp98, '%s\\20%s_sp98_gas_prices' %(path_data + folder_current_prices, today_date))