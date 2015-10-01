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
folder_source_zagaz = r'\data_gasoline\data_source\data_json_prices\zagaz'

def enc_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def parse_soup_bloc_stations(soup):
  dict_stations = {}
  table_stations = soup.find('div', {'class' : 'tableau_prix_carburant'})
  ls_bloc_stations = table_stations.findAll('tr')
  for bloc_station in ls_bloc_stations:
    bloc_id_station = bloc_station.find('a', {'href' : re.compile('station\.php\?id_s.*')})
    if bloc_id_station:
      match_id_station = re.match('station\.php\?id_s=(.*)', bloc_id_station['href'])
      if match_id_station:
        try:
          id_station = match_id_station.group(1)
          # city = bloc_station.find('td', {'class' : 'ville'}).find(text=True)
          # name = bloc_station.find('div', {'class' : 'station_add'}).find('a').find(text=True)
          
          # ls_address = bloc_station.find('div', {'class' : 'station_add'}).findAll(text=True)
          # ls_address = [x for x in map(lambda x: x.strip(), ls_address)  if x]
          ls_ls_address = bloc_station.find('div', {'class' : 'station_add'}).findAll('p')
          ls_ls_address = [map(lambda x: x.strip(), ls_address.findAll(text=True))\
                             for ls_address in ls_ls_address]
          ls_ls_address = [[x for x in ls_address if x] for ls_address in  ls_ls_address]
                    
          detail_user = bloc_station.find('a', {'href' : re.compile('userDetail.*')})
          if detail_user:
            href_user = bloc_station.find('a', {'href' : re.compile('userDetail.*')})['href']
            pseudo_user = bloc_station.find('a', {'href' : re.compile('userDetail.*')}).string
          else:
            href_user, pseudo_user = None, None
          
          ls_prices = [None for x in range(5)]
          price_time = bloc_station.find('span', {'class' : 'discret'})
          if price_time:
            price_time = price_time.string
            ls_prices = [bloc_station.find('td', {'class' : 'col_gaz '}).string.strip(),
                         bloc_station.find('td', {'class' : 'col_gazp css_cache'}).string.strip(),
                         bloc_station.find('td', {'class' : 'col_sp95 css_cache'}).string.strip(),
                         bloc_station.find('td', {'class' : 'col_e10 css_cache'}).string.strip(),
                         bloc_station.find('td', {'class' : 'col_sp98 css_cache'}).string.strip()]
            # ls_prices = [price_gaz, price_gazp, price_sp95, price_e10, price_sp98]
          
          comment = bloc_station.find('div', {'class' : 'station_comm'})
          if comment:
            comment = [elt for elt in map(lambda x: x.strip(), comment.findAll(text=True)) if elt]
          
          bloc_alert = bloc_station.find('div', {'class' : 'box_alert txt_taille_90'})
          if bloc_alert:
            bloc_alert = [elt for elt in map(lambda x: x.strip(), bloc_alert.findAll(text=True)) if elt]
          
          dict_stations[id_station] = (pseudo_user,
                                       href_user,
                                       price_time,
                                       ls_prices,
                                       ls_ls_address,
                                       comment,
                                       bloc_alert)
        except:
          print bloc_station
  return dict_stations

dict_all_stations = {}

departments = range(1,96) + ['2A'] # 2B is 20
for department in departments:
  print department
  base_url = r'http://www.zagaz.com'
  try:
    department_extension = r'/prix-carburant.php?departement=%02d' %department
  except:
    department_extension = r'/prix-carburant.php?departement=%s' %department
  response = urllib2.urlopen(base_url + department_extension)
  data = response.read()
  soup = BeautifulSoup(data)
  dict_all_stations.update(parse_soup_bloc_stations(soup))
  
  # can't have more than 20 results per page
  # soup.find('div', {'class' : 'suiv'}).string not None at last page
  while not soup.find('div', {'class' : 'suiv'}).string:
    dict_all_stations.update(parse_soup_bloc_stations(soup))
    bloc_next_page = soup.find('div', {'class' : 'suiv'})
    next_page_url_extension =\
        bloc_next_page.find('a', {'href' : re.compile('prix-carburant.php*')})['href']
    response = urllib2.urlopen(base_url + r'/' + next_page_url_extension)
    data = response.read()
    soup = BeautifulSoup(data)
  dict_all_stations.update(parse_soup_bloc_stations(soup)) # parse last page

# enc_json(dict_all_stations, path_data + folder_source_info_stations + r'\20140124_zagzag_stations')
