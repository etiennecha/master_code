import httplib, urllib2
import urllib
from BeautifulSoup import BeautifulSoup
import re
import sys
import json
from datetime import date
import cookielib

# rappel: ds les requetes, diesel = 1 et essence = 'a'
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
list_stations = []
for i in range(1, 3):
  # query with token
  query = {'_recherche_recherchertype[choix_carbu]' : 'a',
           '_recherche_recherchertype[localisation]' : '%02d' %i,
           '_recherche_recherchertype[_token]' : token}
  param = urllib.urlencode(query)
  response_2 = urllib2.urlopen('http://www.prix-carburants.economie.gouv.fr', param)
  data_2 = response_2.read()
  soup_2 = BeautifulSoup(data_2)
  # get page with 100 results (still: can be several pages)
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
    list_dpt_stations.append(info_station + price_station)
  list_stations += list_dpt_stations

"""
response_4 = urllib2.urlopen('http://www.prix-carburants.economie.gouv.fr/itineraire/infos/78400003')
data_4 = response_4.read()
soup_4 = BeautifulSoup(data_4)

fullquery = 'http://www.prix-carburants.economie.gouv.fr/recherche/_recherche_recherchertype%5Bchoix_carbu%5D=a&' + \
'_recherche_recherchertype%5Blocalisation%5D=78' + \
'&_recherche_recherchertype%5B_token%5D=bf00139e2148738da50bf491043788a1aad0f88d'
"""