import httplib, urllib2
import urllib
from BeautifulSoup import BeautifulSoup
import re
import sys
import json
from datetime import date
import cookielib

json_folder = 'C:\Users\Etienne\Desktop\work_temp'

def enc_stock_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

# rappel: ds les requetes, diesel = 1 et essence = 'a'

# welcome page: get token
def get_coordinates(fuel_type):
  list_coordinates = []
  cookie_jar = cookielib.LWPCookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
  opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')]
  urllib2.install_opener(opener)
  website_url = 'http://www.prix-carburants.economie.gouv.fr'
  response = urllib2.urlopen(website_url)
  data = response.read()
  soup = BeautifulSoup(data)
  token = soup.find('input', {'type' : 'hidden', 'id':'recherche_recherchertype__token'})['value']
  print 'token is', token
  for i in range(1, 96):
    # query with token
    query = {'_recherche_recherchertype[choix_carbu]' : fuel_type,
             '_recherche_recherchertype[localisation]' : '%02d' %i,
             '_recherche_recherchertype[_token]' : token}
    param = urllib.urlencode(query)
    response_2 = urllib2.urlopen('http://www.prix-carburants.economie.gouv.fr', param)
    data_2 = response_2.read()
    soup_2 = BeautifulSoup(data_2)
    # get map page
    recherche_url = 'http://www.prix-carburants.economie.gouv.fr/recherche/map'
    response_3 = urllib2.urlopen(recherche_url)
    data_3 = response_3.read()
    soup_3 = BeautifulSoup(data_3)
    dpt_coordinates_bloc = soup_3.find('div', {'id' : 'mc_pdv'})
    dpt_coordinates_list = dpt_coordinates_bloc.string.split(',')
    list_coordinates += dpt_coordinates_list
  return list_coordinates

list_diesel = get_coordinates('1')
list_essence =  get_coordinates('a')

enc_stock_json(list_diesel, json_folder + r'\20130117_list_coordinates_diesel')
enc_stock_json(list_essence, json_folder + r'\20130117_list_coordinates_essence')