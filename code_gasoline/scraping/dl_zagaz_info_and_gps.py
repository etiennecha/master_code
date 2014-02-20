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

def parse_page_dpt(soup):
  dict_dpt_page = {}
  table_stations = soup.find('div', {'class' : 'tableau_prix_carburant'})
  ls_bloc_stations = table_stations.findAll('tr')
  for bloc_station in ls_bloc_stations:
    bloc_id_station = bloc_station.find('a', {'href' : re.compile('station\.php\?id_s.*')})
    if bloc_id_station:
      try:
        match_id_station = re.match('station\.php\?id_s=(.*)', bloc_id_station['href'])
        id_station = match_id_station.group(1)
        ls_ls_address = bloc_station.find('div', {'class' : 'station_add'}).findAll('p')
        ls_ls_address = [map(lambda x: x.strip(), ls_address.findAll(text=True))\
                          for ls_address in ls_ls_address]
        ls_ls_address = [[x for x in ls_address if x] for ls_address in  ls_ls_address]
        carte_url_bloc = bloc_station.find('a', {'href' : re.compile('carte.php*')})
        if carte_url_bloc:
          carte_url = carte_url_bloc['href']
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
          ls_prices = [bloc_station.find('td', {'class' : 'col_gaz '}).string,
                       bloc_station.find('td', {'class' : 'col_gazp css_cache'}).string,
                       bloc_station.find('td', {'class' : 'col_sp95 css_cache'}).string,
                       bloc_station.find('td', {'class' : 'col_e10 css_cache'}).string,
                       bloc_station.find('td', {'class' : 'col_sp98 css_cache'}).string]
          ls_prices = [x.strip() if x else x for x in ls_prices]
          # ls_prices = [price_gaz, price_gazp, price_sp95, price_e10, price_sp98]
        comment = bloc_station.find('div', {'class' : 'station_comm'})
        if comment:
          comment = [elt for elt in map(lambda x: x.strip(), comment.findAll(text=True)) if elt]
        bloc_alert = bloc_station.find('div', {'class' : 'box_alert txt_taille_90'})
        if bloc_alert:
          bloc_alert = [elt for elt in map(lambda x: x.strip(), bloc_alert.findAll(text=True)) if elt]
        dict_dpt_page[id_station] = (pseudo_user,
                                     href_user,
                                     price_time,
                                     ls_prices,
                                     ls_ls_address,
                                     comment,
                                     bloc_alert,
                                     carte_url)
      except:
        print bloc_station
  return dict_dpt_page

def parse_station_page_details(soup):
  table_0 = soup.find('table', {'border' : '0'})
  ls_name = table_0.p
  if ls_name:
    ls_name = ls_name.findAll(text=True)
  ls_address = table_0.find('p', {'class' : 'clear'})
  if ls_address:
    ls_address = table_0.find('p', {'class' : 'clear'}).findAll(text=True)

  bloc_services = soup.find('div', {'class' : 'box_picto_service'})
  ls_services = bloc_services.findAll('img', {'class' : 'tooltip'})
  if ls_services:
    ls_services = [elt['title'].replace(ur'<b>', '').replace(ur'</b>','') for elt in ls_services]

  website = soup.find('a', {'class' : 'station_lien tooltip'})
  if website:
    website = website['href']
  
  # Current prices: collects [1] (prices) and [2] (user/date)
  ls_current_result = []
  table_current_prices = soup.find('table', {'class' : 'deco align_center'})
  ls_bloc_tr_current = table_current_prices.findAll('tr') # check len is 3
  if len(ls_bloc_tr_current) == 3:
    ls_current_prices_td = ls_bloc_tr_current[1].findAll('td', {'class' : re.compile('col_.*')})
    ls_current_users_td = ls_bloc_tr_current[2].findAll('td')
    if ls_current_prices_td: #and len(ls_current_prices_td) == len(ls_current_users_td):
      ls_current_prices = [[elt['class'], elt.find(text=True)] for elt in ls_current_prices_td]
      ls_current_users = [elt.findAll('span', {'class' : 'discret'}) for elt in ls_current_users_td]
      ls_current_users = [[ls_current_users[0][0].a['href'],
                           elt[0].a.find(text=True),
                           elt[1].find(text=True)]
                             for elt in ls_current_users]
      ls_current_maj = [elt.find('a', {'href' : True, 'title': True})['href']\
                          if elt.find('a', {'href' : True, 'title': True})\
                          else None for elt in ls_current_users_td]
      ls_current_result = [ls_current_prices, ls_current_users, ls_current_maj]
  else:
    print 'Pbm with prices', url
  
  # History of price (TODO: clean text)
  ls_ls_price_history = []
  table_history_prices = soup.find('table' , {'class' : 'txt_taille_90',
                                              'summary': re.compile('Historique.*')})
  if table_history_prices:
    ls_bloc_tr_history = table_history_prices.findAll('tr')
    if ls_bloc_tr_history and ls_bloc_tr_history[0].find('td', {'class' : 'txt_gris'}):
      date = ls_bloc_tr_history[0].find('td', {'class' : 'txt_gris'}).findAll(text=True)
      ls_price_history = [date, []]
      for bloc_tr_history in ls_bloc_tr_history[1:]:
        if bloc_tr_history.find('td', {'class' : 'txt_gris'}):
          ls_ls_price_history.append(ls_price_history)
          date = bloc_tr_history.find('td', {'class' : 'txt_gris'}).findAll(text=True)
          ls_price_history = [date, []]
        else:
          price_info = bloc_tr_history.findAll('td', {'class' : 'col_contenu'})
          price_info = [elt.findAll(text=True) for elt in price_info]
          ls_price_history[1].append(price_info)
      ls_ls_price_history.append(ls_price_history)
  
  ls_result = [ls_name,
               ls_address,
               website,
               ls_services,
               ls_current_result,
               ls_ls_price_history]
  return ls_result


# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
# structure of the data folder should be the same
folder_source_zagaz = r'\data_gasoline\data_source\data_json_prices\zagaz'

dict_all_stations = dec_json(path_data + folder_source_zagaz + r'\20140124_zagzag_stations')

ls_id_stations = dict_all_stations.keys()

base_url = r'http://www.zagaz.com'

path_zagaz_ext_prices = path_data + folder_source_zagaz + r'\20140127_zagzag_dict_ext_prices'
# dict_station_ext_prices = {}
dict_station_ext_prices = dec_json(path_zagaz_ext_prices)

for id_station in ls_id_stations[0:8000]:
  if id_station not in dict_station_ext_prices:
    url = '/'.join([base_url, 'station.php?id_s=%s' %id_station])
    response = urllib2.urlopen(url)
    try:
      soup = BeautifulSoup(response.read())
      dict_station_ext_prices[id_station] = parse_station_page_details(soup)
      time.sleep(0.3)
    except Exception, e: 
      print id_station, e

# enc_json(dict_station_ext_prices, path_zagaz_ext_prices)      

# TODO: collect closed gas stations and check those recently closed (!)

# dict_dpt = {}
# departments = range(1,96) + ['2A'] # 2B is 20
# for department in departments[0:1]:
  # print department
  # base_url = r'http://www.zagaz.com'
  # department_extension = r'/prix-carburant.php?departement=%02d' %department
  # response = urllib2.urlopen(base_url + department_extension)
  # data = response.read()
  # soup = BeautifulSoup(data)
  
  # dict_dpt.update(parse_page_dpt(soup))
  
  # # can't have more than 20 results per page
  # # soup.find('div', {'class' : 'suiv'}).string not None at last page
  # while not soup.find('div', {'class' : 'suiv'}).string:
    # master_results_stations += collect_page_info(soup)
    # bloc_next_page = soup.find('div', {'class' : 'suiv'})
    # next_page_url_extension = bloc_next_page.find('a', {'href' : re.compile('prix-carburant.php*')})['href']
    # response = urllib2.urlopen(base_url + r'/' + next_page_url_extension)
    # data = response.read()
    # soup = BeautifulSoup(data)
  # master_results_stations += collect_page_info(soup) # parse last page