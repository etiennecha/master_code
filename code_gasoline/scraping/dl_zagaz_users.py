import os, sys
import httplib, urllib2
import urllib
import cookielib
from BeautifulSoup import BeautifulSoup
import re
from datetime import date
import json
import time

def enc_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def parse_user_page(soup):
  ls_ls_user_info = []
  bloc_table_user = soup.find('table', {'summary' : '', 'class' : 'deco'})
  if bloc_table_user and bloc_table_user.find('table', {'summary' : '', 'class' : 'deco'}):
    bloc_user = bloc_table_user.find('table', {'summary' : '', 'class' : 'deco'})
    ls_ls_user_info = [elt.findAll(text=True) for elt in bloc_user.findAll('tr')]
    ls_ls_user_info = [map(lambda x: x.strip(), [elt for elt in ls_user_info if elt])\
                          for ls_user_info in ls_ls_user_info]
  
  ls_ls_stations_info = []
  bloc_table_stations = soup.find('table', {'class' : 'deco', 'summary' : re.compile('Mise.*')})
  if bloc_table_stations:
    ls_blocs_stations = bloc_table_stations.findAll('tr')
    for bloc_station in ls_blocs_stations:
      bloc_id_station = bloc_station.find('a', {'href' : re.compile('station\.php\?id_s.*')})
      if bloc_id_station:
        match_id_station = re.match('station\.php\?id_s=(.*)', bloc_id_station['href'])
        id_station = match_id_station.group(1)
        ls_prices = [None for x in range(5)]
        price_time = bloc_station.find('span', {'class' : 'discret'})
        if price_time:
          price_time = price_time.string
          ls_prices = [bloc_station.find('td', {'class' : 'col_gaz'}).string,
                       bloc_station.find('td', {'class' : 'col_gazp'}).string,
                       bloc_station.find('td', {'class' : 'col_sp95'}).string,
                       bloc_station.find('td', {'class' : 'col_e10'}).string,
                       bloc_station.find('td', {'class' : 'col_sp98'}).string]
        ls_ls_stations_info.append([id_station, price_time, ls_prices])
  return [ls_ls_user_info, ls_ls_stations_info]


# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
# structure of the data folder should be the same
folder_source_zagaz = r'\data_gasoline\data_source\data_json_prices\zagaz'  

dict_all_stations = dec_json(path_data + folder_source_zagaz + r'\20140124_zagzag_stations')
ls_users = list(set([tuple(v[:2]) for k,v in dict_all_stations.items() if k and v[0]]))

# dict_users_info = {}
dict_users_info = dec_json(path_data + folder_source_zagaz + r'\20140124_dict_active_users')

base_url = r'http://www.zagaz.com'
for user_pseudo, user_url in ls_users:
  if user_url not in dict_users_info:
    url = '/'.join([base_url, user_url])
    try:
      response = urllib2.urlopen(url)
      dict_users_info[user_url] = parse_user_page(BeautifulSoup(response.read()))
    except:
      'Could not collect:', user_pseudo, user_url
    time.sleep(0.3)
  else:
    # print 'User already in dict (?):', user_pseudo, user_url
    pass

path_zagaz_users = path_data + folder_source_zagaz + r'\20140124_dict_active_users'
# enc_json(dict_users_info, path_zagaz_users)