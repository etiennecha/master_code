import os, sys
import httplib, urllib2
import urllib
import cookielib
from BeautifulSoup import BeautifulSoup
import re
from datetime import date
import json

def enc_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def get_list_prices(fuel_type, highway = False):
  """
  Returns a list of lists containing station info (incl. daily price)
  Station info sublists are lists of form [[id], [info], [price]]
  
  @param fuel_type  leaded (diesel) = 1, unleaded (essence) = 'a'
  """
  cookie_jar = cookielib.LWPCookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
  opener.addheaders = [('User-agent', u'Mozilla/5.0 (Windows NT 6.1; WOW64) '+\
                                      u'AppleWebKit/537.11 (KHTML, like Gecko) '+\
                                      u'Chrome/23.0.1271.64 Safari/537.11')]
  urllib2.install_opener(opener)
  website_url = 'http://www.prix-carburants.economie.gouv.fr'
  response = urllib2.urlopen(website_url)
  data = response.read()
  soup = BeautifulSoup(data)
  token = soup.find('input', {'type' : 'hidden',
                              'id':'recherche_recherchertype__token'})['value']
  print 'token is', token
  ls_stations = []
  ls_highway_ids = []
  for i in range(1, 96):
    query = {'_recherche_recherchertype[choix_carbu]' : fuel_type,
             '_recherche_recherchertype[localisation]' : '%02d' %i,
             '_recherche_recherchertype[_token]' : token}
    param = urllib.urlencode(query)
    response_2 = urllib2.urlopen('http://www.prix-carburants.economie.gouv.fr', param)
    data_2 = response_2.read()
    soup_2 = BeautifulSoup(data_2)
    # get page with all results
    recherche_url = u'http://www.prix-carburants.economie.gouv.fr/'+\
                    u'recherche/?sort=commune&direction=asc&page=1&lettre=%23&limit='
    response_3 = urllib2.urlopen(recherche_url)
    data_3 = response_3.read()
    soup_3 = BeautifulSoup(data_3)
    stations_blocs = soup_3.findAll('tr', {'class' : re.compile('data.*')})
    ls_dpt_stations = []
    for station_bloc in stations_blocs:
      id_station = station_bloc['id']
      info_station = station_bloc.findAll('td', {'class' : 'pointer'})
      price_station = station_bloc.findAll('td', {'class' : 'pointer center chiffres'})
      info_station = [unicode(info.string) for info in info_station]
      price_station = [unicode(price.string) for price in price_station]
      ls_dpt_stations.append([id_station] + info_station + price_station)
      # highway
      if station_bloc.find('img', {'src' : True, 'alt' : 'Autoroute'}):
        ls_highway_ids.append(id_station)
    print len(ls_dpt_stations), 'stations ds le departement', i
    ls_stations += ls_dpt_stations
  if highway:
    return (ls_stations, ls_highway_ids)
  else:
    return ls_stations

if __name__ == '__main__':

  # path_data: default to CREST location, else try home location
  path_data = os.path.join(u'W:\\', u'Bureau', u'Etienne_work', u'Data')
  if not os.path.exists(path_data):
    path_data = os.path.join(u'C:\\', u'Users', u'etna', u'Desktop',
                             u'Etienne_work', u'Data')

  path_dir_current_prices = os.path.join(path_data, 
                                         'data_gasoline',
                                         'data_source',
                                         'data_prices',
                                         'current_prices')
  
  today_date = date.today().strftime("%Y%m%d")
  print today_date
  
  # PRICE COLLECT
  ls_essence = get_list_prices('a')
  ls_diesel = get_list_prices(1)
  enc_json(ls_essence, os.path.join(path_dir_current_prices,
                                    today_date + u'_essence_gas_prices'))
  enc_json(ls_diesel, os.path.join(path_dir_current_prices,
                                   today_date + u'_diesel_gas_prices'))
  
  list_sp98 = get_list_prices(6)
  enc_json(ls_sp98, os.path.join(path_dir_current_prices,
                                 today_date + u'_sp98_gas_prices'))
  
  ## HIGHWAY
  #ls_essence, ls_essence_highway = get_list_prices('a', highway = True)
  #ls_diesel, ls_diesel_highway = get_list_prices(1, highway = True)
  #ls_highway_ids = list(set(ls_essence_highway).union(set(ls_diesel_highway)))
  #enc_json(ls_highway_ids, os.path.join(path_dir_current_prices,
  #                                      today_date + u'_highway_ids'))
