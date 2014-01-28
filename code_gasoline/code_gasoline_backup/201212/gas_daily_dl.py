import httplib, urllib
from BeautifulSoup import BeautifulSoup
import re
import sys
import json
from datetime import date

# rappel: ds les requetes, diesel = 1 et essence = 'a'

json_folder = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\json_daily_data'

def enc_stock_json(database, chemin):
 with open(chemin, 'w') as fichier:
  json.dump(database, fichier)

def get_price_of_dept_stations(dept, fuel_type):
  gcount = 0
  list_stations_in_dpt = []
  c = httplib.HTTPConnection('www.prix-carburants.economie.gouv.fr')
  for page in range(1, 100):
    c.request('GET',
              '/index.php?module=dbgestion&action=fsearch&fuel=%s&search_departement=%s&nb_search_per_page=100&thisPageNumber=%d' % (fuel_type, dept, page))
    r = c.getresponse()
    data = r.read()
    soup = BeautifulSoup(data)
    trs = soup.findAll('tr', id=re.compile('pdv.*'))
    count = 0 # la derniere page est sans resultat, si count reste a 0 la boucle s'acheve
    for tr in trs:
      count += 1
      try:
        gcount += 1
        id_station = tr['id']
        if fuel_type == 1:
          dico_station = {'city_station' : tr.contents[3].string,
                          'name_station' : tr.contents[5].string,
                          'brand_station' : tr.contents[7].string,
                          'diesel_price_station' : tr.contents[9].string,
                          'diesel_date_station' : tr.contents[11].string}
        if fuel_type == 'a':
          dico_station = {'city_station' : tr.contents[3].string,
                          'name_station' : tr.contents[5].string,
                          'brand_station' : tr.contents[7].string,
                          'e10_price_station' : tr.contents[9].string,
                          'e10_date_station' : tr.contents[11].string,
                          'sp95_price_station' : tr.contents[13].string,
                          'sp95_date_station' : tr.contents[15].string}
        list_stations_in_dpt.append([id_station, dico_station])
      except TypeError:
        print 'pbm d\'ecriture ds le dico'
    if count == 0:
      print >> sys.stderr, 'DEBUG departement %s pages %s resultats %s' % (dept, page - 1, gcount)
      return list_stations_in_dpt

list_stations_diesel = []
list_stations_e10_sp95 = []
for i in range(1, 96):
  list_stations_in_dpt_diesel = get_price_of_dept_stations('%02d' % i, 1)
  list_stations_in_dpt_e10_sp95 = get_price_of_dept_stations('%02d' % i, 'a')
  list_stations_diesel += list_stations_in_dpt_diesel
  list_stations_e10_sp95 += list_stations_in_dpt_e10_sp95

master = {}
for station_diesel in list_stations_diesel:
  master[station_diesel[0]] = station_diesel[1]
for station_e10_sp95 in list_stations_e10_sp95:
  try:
    master[station_e10_sp95[0]]['e10_price_station'] = station_e10_sp95[1]['e10_price_station']
    master[station_e10_sp95[0]]['e10_date_station'] = station_e10_sp95[1]['e10_date_station']
    master[station_e10_sp95[0]]['sp95_price_station'] = station_e10_sp95[1]['sp95_price_station']
    master[station_e10_sp95[0]]['sp95_date_station'] = station_e10_sp95[1]['sp95_date_station']
  except:
    master[station_e10_sp95[0]] = station_e10_sp95[1]

today_date = date.today().strftime("%y%m%d")
enc_stock_json(master, '%s\\20%s_gas_prices' %(json_folder, today_date))
