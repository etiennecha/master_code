import json
import os, sys, codecs
from datetime import date, timedelta
import datetime
import time

machine_path = r'C:\Users\etna\Desktop\Code\Gasoline'
raw_data_folders = [r'\data_prices\20110903_20120514_unl',
                    r'\data_prices\20110904_20120514_lea',
                    r'\data_prices\20120515_20120918_two',
                    r'\data_prices\20120917_20121203_two',
                    r'\data_prices\20130121-20130213_lea',
                    r'\data_prices\20130121-20130213_unl']

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def date_range(start_date, end_date):
  """
  creates a list of dates based on its arguments (beginning and end dates)
  """
  list_dates = []
  for n in range((end_date + timedelta(1) - start_date).days):
    temp_date = start_date + timedelta(n)
    list_dates.append(temp_date.strftime('%Y%m%d'))
  return list_dates

def format_price_file_2011_unl(chemin):
  """
  from each date file, creates a list of dictionnaries (one per gas stations)
  each dictionnary has keys ['id_station', 'commune', 'nom_station','marque', 'prix', 'date']
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

def build_master(raw_data_folder, file_extension, start_date, end_date, id_str, price_str, date_str, key_dico):
  """
  The function aggregates files i.e. lists of dicos to produce a master (incl. several components)
  So far it uses a function to read and format the raw files.. but that should be dropped later on
  ----
  Arguments description:
  - raw_data_folder: location of files
  - file_extension, start_date, end_date: files names must be : date + extension
  - id_str, price_str, date_str: names of id, price and date keys in file individual dicos
  - key_dico: all other keys in file individual dicos
  """
  master_dates = date_range(start_date, end_date)
  missing_dates = []
  master_dico_general_info = {}
  master_list_ids = []
  master_list_prices = []
  master_list_dates = []
  for date in master_dates:
    day_count = master_dates.index(date)
    if os.path.exists('%s\%s%s' %(raw_data_folder, date, file_extension)):
      temp_master_list = format_price_file_2011_unl('%s\%s%s' %(raw_data_folder, date, file_extension))
      for individual in temp_master_list:
        if individual[id_str] in master_list_ids:
          individual_index = master_list_ids.index(individual[id_str])
          for original_key, new_key in key_dico.iteritems():
            if individual[original_key] != master_dico_general_info[individual[id_str]][new_key][len(master_dico_general_info[individual[id_str]][new_key])-1][0]:
              master_dico_general_info[individual[id_str]][new_key].append((individual[original_key], day_count))
        else:
          master_list_ids.append(individual[id_str])
          individual_index = master_list_ids.index(individual[id_str])
          master_dico_general_info[individual[id_str]] = {'rank': individual_index}
          for original_key, new_key in key_dico.iteritems():
            master_dico_general_info[individual[id_str]][new_key] = [(individual[original_key], day_count)]
          master_list_prices.append([])
          master_list_dates.append([])
        # fill price/date holes (either because of missing dates or individuals occasionnally missing)
        while len(master_list_prices[individual_index]) < day_count:
          master_list_prices[individual_index].append(None)
        master_list_prices[individual_index].append(individual[price_str])
        while len(master_list_dates[individual_index]) < day_count:
          master_list_dates[individual_index].append(None)
        master_list_dates[individual_index].append(individual[date_str])
    else:
      missing_dates.append(date)
  # add None if list of prices/dates shorter than nb of days (not for dates so far)
  for list_prices in master_list_prices:
    while len(list_prices) < day_count + 1:
      list_prices.append(None)
  for list_dates in master_list_dates:
    while len(list_dates) < day_count + 1:
      list_dates.append(None)
  master_price = {'list_dates' : master_dates,
                  'list_missing_dates' : missing_dates, 
                  'dict_general_info': master_dico_general_info,
                  'list_ids' : master_list_ids, 
                  'list_indiv_prices' : master_list_prices,
                  'list_indiv_dates' : master_list_dates}
  return master_price

def fill_holes(master_price, lim):
  for individual_index in range(0, len(master_price['list_indiv_prices'])):
    for day_index in range(0, len(master_price['list_indiv_prices'][individual_index])):
      if master_price['list_indiv_prices'][individual_index][day_index] is None:
        relative_day = 0
        while master_price['list_indiv_prices'][individual_index][day_index + relative_day] is None and day_index + relative_day < len(master_price['list_dates']) - 1:
          relative_day += 1
        if master_price['list_dates'][day_index] == master_price['list_indiv_dates'][individual_index][day_index + relative_day]:
          master_price['list_indiv_prices'][individual_index][day_index] = master_price['list_indiv_prices'][individual_index][day_index + relative_day]
        elif day_index > 0 and day_index + relative_day != len(master_price['list_dates'])-1 and relative_day < lim:
        # replaces also if change on the missing date... which makes data inaccurate
          master_price['list_indiv_prices'][individual_index][day_index] = master_price['list_indiv_prices'][individual_index][day_index - 1]
  return master_price

def analyse_remaining_holes(master_price):
  list_dilettante = []
  for individual_index in range(0,len(master_price['list_indiv_prices'])):
    first_non_none = 0
    last_non_none = 0
    while master_price['list_indiv_prices'][individual_index][first_non_none] is None:
      first_non_none += 1
    while master_price['list_indiv_prices'][individual_index][::-1][last_non_none] is None:
      last_non_none += 1
    last_non_none= len(master_price['list_indiv_prices'][individual_index]) - last_non_none
    if None in master_price['list_indiv_prices'][individual_index][first_non_none:last_non_none]:
      list_dilettante.append(individual_index)
  return list_dilettante

raw_data_folder = machine_path + raw_data_folders[1]
file_extension = 'ga.txt'
start_date = date(2011,9,4)
end_date = date(2012,5,14)
id_str = 'id_station'
price_str = 'prix'
date_str = 'date'
key_dico = {'commune' : 'city_station', 'nom_station' :'name_station', 'marque':'brand_station'}
master_test = build_master(raw_data_folder, file_extension, start_date, end_date, id_str, price_str, date_str, key_dico)
master_test = fill_holes(master_test, 5)
dilettante = analyse_remaining_holes(master_test)

# enc_stock_json(master_test, machine_path + r'\data_prices\current_master_price')

"""
raw_data_files = [r'',
                  r'',
                  r'\20120515_gas_prices',
                  r'\20120917_gas_prices',
                  r'\20130122_diesel_gas_prices',
                  r'\20130121_essence_gas_prices']
data_test = []
for index in range(2,6):
  data_test.append(dec_json(machine_path + raw_data_folders[index] + raw_data_files[index]))
for elt in data_test:
  type(data_test)
  try:
    elt[elt.keys()[0]]
  except:
    elt[0]

the first two are particular
the second two are dictionnaries: convert to lists + rename dico keys (?)
the two last are list of list: convert to list of dicos (?)
"""