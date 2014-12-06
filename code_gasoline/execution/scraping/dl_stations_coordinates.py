#!/usr/bin/python
# -*- coding: utf-8 -*-

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

def get_coordinates(fuel_type):
  """
  Returns a list of lists containing station coordinates
  
  @param fuel_type  leaded (diesel) = 1, unleaded (essence) = 'a'
  """
  list_coordinates = []
  cookie_jar = cookielib.LWPCookieJar()
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
  opener.addheaders = [(u'User-agent', u'Mozilla/5.0 (Windows NT 6.1; WOW64)' + 
                                       u'AppleWebKit/537.11 (KHTML, like Gecko)' +\
                                       u'Chrome/23.0.1271.64 Safari/537.11')]
  urllib2.install_opener(opener)
  website_url = 'http://www.prix-carburants.economie.gouv.fr'
  response = urllib2.urlopen(website_url)
  data = response.read()
  soup = BeautifulSoup(data)
  token = soup.find('input', {'type' : 'hidden',
                              'id':'recherche_recherchertype__token'})['value']
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

if __name__ == '__main__':

  # path_data: default to CREST location, else try home location
  path_data = os.path.join(u'W:\\', u'Bureau', u'Etienne_work', u'Data')
  if not os.path.exists(path_data):
    path_data = os.path.join(u'C:\\', u'Users', u'etna', u'Desktop',
                             u'Etienne_work', u'Data')
  
  path_raw_coordinates = os.path.join(path_data,
                                      u'data_gasoline',
                                      u'data_source',
                                      u'data_prices')
  
  ls_diesel = get_coordinates('1')
  ls_essence =  get_coordinates('a')
  today_date = date.today().strftime("%y%m%d")
  enc_json(ls_essence, os.path.join(path_raw_coordinates,
                                    u'20%s_list_coordinates_essence' %today_date))
  enc_json(ls_diesel, os.path.join(path_raw_coordinates,
                                   u'20%s_list_coordinates_diesel' %today_date))
