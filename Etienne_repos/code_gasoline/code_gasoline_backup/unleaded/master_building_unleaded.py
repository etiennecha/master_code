import json
import os, sys, codecs
from datetime import date, timedelta
import datetime
import time

txt_path = 'C:\Users\Etienne\Desktop\Programmation\Python\Scrapping_project_staser\outcomeoftest'

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())
  
def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)
   
def daterange(start_date, end_date):
  list_dates = []
  for n in range((end_date + timedelta(1) - start_date).days):
    temp_date = start_date + timedelta(n)
    list_dates.append(temp_date.strftime('%Y%m%d'))
  return list_dates

def formatage(chemin):
  """
  ici on recupere liste de dictionnaires ['id_station', 'commune', 'nom_station','marque', 'prix', 'date']
  """
  keys = ['id_station', 'commune', 'nom_station','marque', 'prix', 'date']
  db_list = []
  inputFile = codecs.open(chemin, 'rb', 'utf-8')
  inputFile.read(0)
  dbtext = inputFile.read()
  list_of_id_stations = []
  for line in dbtext.split('\r\n'):
    memo = ""									# memo enregistre le contenu de l'element precedent (lie au pbm de la virgule dans le prix)
    lineotpt = ""								# loneotpt enregistre le contenu de la nouvelle ligne par appends successifs
    c = 0										# c compte le nombre d'elements de la ligne
  
    # boucle qui reconnait un espace et un caractere comme le debut d'un prix et le stocke (memo) pr l'appender au reste du px ensuite
    for elt in line.split(','):  
      if (elt != ' ' and len(memo) == 2):		# non vide et memo contient le dbt d'un prix (test longueur 2 car il y a espace et le 0 ou 1 du debut du prix
        lineotpt += memo + '.' + elt + ','	# append lineotpt ac dbt du px et sa fin
        c += 1
        memo = elt
      elif (elt != ' ' and len(elt) != 2):		# non vide et non dbt d'un prix
        lineotpt += elt + ','				# ne pas ecrire memo qui n'est pas le dbt d'un px
        c += 1
        memo = elt
      else:									# autre cas (ntmt quand elt = 0 ou 1, correspond au debut du prix): ne pas appender mais garder trace
        memo = elt
   
    # reperer les lignes qui ont plus de X (5) virgules
    # part du principe que le souci est entre les colonnes ville et nom station  
    if c != 6 and c != 1:							# reperer pbms et eviter l'impression de la derniere ligne de chaque fichier (blanche)
      print >> sys.stderr, lineotpt
      co = 0
      newlineotpt = ''
      for elt in lineotpt:
        if elt != ',':
          newlineotpt += elt
        elif co != 2:								# suppression de la 3e virgule l'element litigieux est mis ds le nom de la station
          newlineotpt += elt
          co = co + 1
        else:
          co = co+1
      newobs = newlineotpt.lstrip('pdv')[:-1]		# ligne modifiee car trop de virgules (suppr de la virgule finale)
    elif c == 1:													# derniere ligne de chaque fichier: ne pas stocker
      pass
    else:
      newobs = lineotpt.lstrip('pdv')[:-1]	# ligne non modifiee (suppr de la virgule finale)
  
    #collecter donnees dans liste et alimenter dictionnaire
    liste_station = [elt for elt in newobs.split(',')]
    if liste_station[0] not in list_of_id_stations:
      db_list.append(dict(zip(keys, liste_station)))
      list_of_id_stations.append(liste_station[0])
  return db_list

start_date = date(2011,9,4)
end_date = date(2012,5,14)

master_dates = daterange(start_date, end_date)
missing_dates = []
master_dico_gas_stations = {}
master_list_gas_stations_id = []
master_list_gas_stations_prices = []

# Creation des fichiers principaux (a adapter pr maj)

for date in master_dates:
  day_count = master_dates.index(date)
  if os.path.exists('%s\ga%s.txt' %(txt_path, date)):
    temp_list_gas_stations = formatage('%s\ga%s.txt' %(txt_path, date))
    # ici on recupere liste de dictionnaires ['id_station', 'commune', 'nom_station', 'marque', 'prix', 'date']
    for gas_station in temp_list_gas_stations:
      try:
        gas_station_index = master_list_gas_stations_id.index(gas_station['id_station'])
        try:
          if gas_station['marque'] != master_dico_gas_stations[gas_station['id_station']]['brand_station'][len(master_dico_gas_stations[gas_station['id_station']]['brand_station'])-1]:
            master_dico_gas_stations[gas_station['id_station']]['brand_station'].append(gas_station['marque'])
            master_dico_gas_stations[gas_station['id_station']]['brand_changes'].append(day_count)
        except:
          print 'pbm', gas_station['id_station'], date
      except:
        master_list_gas_stations_id.append(gas_station['id_station'])
        gas_station_index = master_list_gas_stations_id.index(gas_station['id_station'])
        master_list_gas_stations_prices.append([])
        master_dico_gas_stations[gas_station['id_station']] = {'rank_station' : gas_station_index,
                                                               'name_station' : gas_station['nom_station'],
                                                               'city_station' : gas_station['commune'],
                                                               'brand_station' : [gas_station['marque']],
                                                               'brand_changes' : [day_count]}
      while len(master_list_gas_stations_prices[gas_station_index]) < day_count:
        master_list_gas_stations_prices[gas_station_index].append(None)
      master_list_gas_stations_prices[gas_station_index].append(gas_station['prix'])
  else:
    missing_dates.append(date)
    for list_of_prices in master_list_gas_stations_prices:
      # for stations no more registered on website: filled of None up to last missing date
      while len(list_of_prices) < day_count:
        list_of_prices.append(None)
      list_of_prices.append(None)
      
# dead gas stations will have a short length compared to other: fill with None? (except if set days to one more day than actually exists...)

# Combler les trous
for missing_date in missing_dates:
  date_missing_date = datetime.date(*time.strptime(missing_date, '%Y%m%d')[0:3])
  date_day_after = date_missing_date + timedelta(1)
  missing_spell = 1
  while date_day_after.strftime("%Y%m%d") in missing_dates:
    date_day_after += timedelta(1)
    missing_spell += 1
  date_to_search = date_day_after.strftime("%Y%m%d")
  count_of_date_to_change = master_dates.index(missing_date)
  temp_list_gas_stations = formatage('%s\ga%s.txt' %(txt_path, date_to_search))
  for gas_station in temp_list_gas_stations:
    try:
      if '20'+gas_station['date'][7:9] + gas_station['date'][4:6] + gas_station['date'][1:3] == missing_date:
        master_list_gas_stations_prices[master_dico_gas_stations[gas_station['id_station']]['rank_station']][count_of_date_to_change] = gas_station['prix']
      else:
        master_list_gas_stations_prices[master_dico_gas_stations[gas_station['id_station']]['rank_station']][count_of_date_to_change] = master_list_gas_stations_prices[master_dico_gas_stations[gas_station['id_station']]['rank_station']][count_of_date_to_change - 1]
    except:
      print 'pbm', gas_station

# Recherche les None restants ds des chaines (prix d'une station particuliere non renseigne tandis que les autres prix sont dispos)
for price_list_ind in range(0,len(master_list_gas_stations_prices)):
  first_non_none = 0
  while master_list_gas_stations_prices[price_list_ind][first_non_none] is None:
    first_non_none +=1
  last_non_none = 0
  while master_list_gas_stations_prices[price_list_ind][::-1][last_non_none] is None:
    last_non_none +=1
  if None in master_list_gas_stations_prices[price_list_ind][first_non_none:-last_non_none]:
    print price_list_ind

json_master_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\json_master'
master_1 = 'master_1'
enc_stock_json([master_dates, missing_dates], '%s\\%s\\dates' %(json_master_path, master_1))
enc_stock_json([master_list_gas_stations_id, master_list_gas_stations_prices], '%s\\%s\\lists_gas_stations' %(json_master_path, master_1))
enc_stock_json(master_dico_gas_stations, '%s\\%s\\dico_gas_stations' %(json_master_path, master_1))