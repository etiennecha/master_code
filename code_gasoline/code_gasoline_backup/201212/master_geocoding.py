# -*- coding: cp1252 -*-

import math
import numpy as np
import matplotlib.pyplot as plt
import os,sys
import copy
import pprint
import string

def get_float_master(master_gas_stations_prices, master_dates):
  new_master_gas_stations_prices = []
  for price_list_ind in range(0,len(master_gas_stations_prices)):
    new_price_list = []
    # find first non none and last non none
    first_non_none = 0
    while master_gas_stations_prices[price_list_ind][first_non_none] is None:
      first_non_none +=1
    temp_last_non_none = 0
    while master_gas_stations_prices[price_list_ind][::-1][temp_last_non_none] is None:
      temp_last_non_none +=1
    last_non_none= len(master_gas_stations_prices[price_list_ind]) - temp_last_non_none
    # beginning: fill with None
    for index in range(0, first_non_none):
      new_price_list.append(None)
    # middle: replace missing
    nb_of_missing_replaced = 0
    for index in range(first_non_none, last_non_none):
      try:
        new_price_list.append(float(master_gas_stations_prices[price_list_ind][index]))
        temp_price = float(master_gas_stations_prices[price_list_ind][index])
      except:
        new_price_list.append(temp_price)
        nb_of_missing_replaced +=1
    # end: fill with None
    while len(new_price_list) < len(master_dates):
      new_price_list.append(None)
    # warning message for nb of missing values replaced
    if nb_of_missing_replaced < 6:
      new_master_gas_stations_prices.append(new_price_list)
    else:
      print 'too many missing values', price_list_ind, 'list of none added'
      new_master_gas_stations_prices.append([None for i in range(0, len(master_dates))])
  return new_master_gas_stations_prices

def get_str_no_accent(line):
  accents = { 'a': ['à', 'ã', 'á', 'â', '\xc2'], 
             'c': ['ç','\xe7'],
             'e': ['é', 'è', 'ê', 'ë', 'É', '\xca', '\xc8', '\xe8', '\xe9', '\xc9'], 
             'i': ['î', 'ï', '\xcf', '\xce'], 
             'o': ['ô', 'ö'], 
             'u': ['ù', 'ü', 'û'], 
             ' ': ['\xb0'] }
  for (char, accented_chars) in accents.iteritems():
    for accented_char in accented_chars:
     try:
       line = line.encode('latin-1').replace(accented_char, char)
     except:
       line = line.replace(accented_char, char)
  line = line.replace('&#039;',' ')
  return line.decode('latin-1').encode('UTF-8').rstrip().lstrip()

def suppr_accent(line):
 accents = { 'a': ['à', 'ã', 'á', 'â', '\xc2'], 
             'c': ['ç','\xe7'],
             'e': ['é', 'è', 'ê', 'ë', 'É', '\xca', '\xc8', '\xe8', '\xe9', '\xc9'], 
             'i': ['î', 'ï', '\xcf', '\xce'], 
             'o': ['ô', 'ö'], 
             'u': ['ù', 'ü', 'û'], 
             ' ': ['\xb0'] }
 for (char, accented_chars) in accents.iteritems():
  for accented_char in accented_chars:
   line = line.replace(accented_char, char)
 line = line.replace('&#039;',' ').replace('"','').replace('\r','')
 return line.rstrip().lstrip()
  
def dec_rotterdam(chemin):
  with open(chemin, 'r') as fichier:
    fichier_prix_rotterdam = fichier.read()
  dic = {}
  c = 0
  for elt in fichier_prix_rotterdam.split('\n'):
    list_date = elt.split(',')[0].split('/')
    date = list_date[2] + list_date[1] + list_date[0]
    dic[date] = elt.split(',')[1]
    c += 1
  return dic
  
def check_gas_stations_brands(master_dico_gas_stations, dico_brands):
  list_brands = []
  list_brands_noacc = []
  for id, content in master_dico_gas_stations.iteritems():
    for brand in content['brand_station']:
      if brand.rstrip().lstrip() not in list_brands:
        list_brands.append(brand.rstrip().lstrip())
      if get_str_no_accent(brand).upper() not in list_brands_noacc:
        list_brands_noacc.append(get_str_no_accent(brand).upper())
  for brand_noacc in list_brands_noacc:
    if brand_noacc not in dico_brands.keys():
      print 'attention: brand missing in dico:', piece
  return [list_brands, list_brands_noacc]
  
def compute_distance(coordinates_A, coordinates_B):
  d_lat = math.radians(coordinates_B[0]-coordinates_A[0])
  d_lon = math.radians(coordinates_B[1]-coordinates_A[1])
  lat_1 = math.radians(coordinates_A[0])
  lat_2 = math.radians(coordinates_B[0])
  a = math.sin(d_lat/2.0) * math.sin(d_lat/2.0) + math.sin(d_lon/2.0) * math.sin(d_lon/2.0) * math.cos(lat_1) * math.cos(lat_2);
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a));
  distance = 6371 * c
  return round(distance, 2)

def check_coordinates_consistency(master):
  print '\nConsistency checking between gps coordinates from Ronan and my geocoding results'
  score_order = {'ROOFTOP' : 4,
                 'RANGE_INTERPOLATED' : 3,
                 'GEOMETRIC_CENTER' : 2,
                 'APPROXIMATE' : 1,
                 'na' : 0}
  score_gaps =  {'ROOFTOP' : [], 
                 'RANGE_INTERPOLATED' : [],
                 'GEOMETRIC_CENTER' : [],
                 'APPROXIMATE' : []}
  list_geocoding_pbm = []
  info_geocoding_missing = 0
  for id, details in master.iteritems():
    try:  
      details['gps_coordinates_rls']
      if score_order[details['gps_coordinates_1'][2]] > score_order[details['gps_coordinates_2'][2]]:
        gps_coordinates_my = details['gps_coordinates_1'][0:2]
        score_my = details['gps_coordinates_1'][2]
      else:
        gps_coordinates_my = details['gps_coordinates_2'][0:2]
        score_my = details['gps_coordinates_2'][2]
      try:
        distance = compute_distance(gps_coordinates_my, details['gps_coordinates_rls'])
        score_gaps[score_my].append(distance)
        if distance > 10:
          list_geocoding_pbm.append([distance, id, details['street_station']])
      except:
        print 'dist not computed', id, gps_coordinates_my, details['gps_coordinates_rls']
    except:
      info_geocoding_missing += 1
  for elt in score_gaps.keys():
    print elt, len(score_gaps[elt]), np.mean(score_gaps[elt]), np.median(score_gaps[elt])
  print 'NOT ENOUGH INFO AVAILABLE', info_geocoding_missing
  return [score_gaps, list_geocoding_pbm]
  
def stat_des_geocoding(master):
  print '\nStats des on gps coordinates information in database'
  score_stats =  {'ROOFTOP' : [0,0], 
                  'RANGE_INTERPOLATED' : [0,0],
                  'GEOMETRIC_CENTER' : [0,0],
                  'APPROXIMATE' : [0,0],
                  'na': [0,0],
                  'NO_GOOGLE' : [0,0],
                  'RLS' : [0,0]}
  for id, details in master.iteritems():
    try:
      score_stats[details['gps_coordinates_1'][2]][0] +=1
    except:
      score_stats['NO_GOOGLE'][0] += 1
    try:
      score_stats[details['gps_coordinates_2'][2]][1] +=1
    except:
      score_stats['NO_GOOGLE'][1] += 1
    try:
      details['gps_coordinates_rls']
      score_stats['RLS'][0] += 1
    except:
      score_stats['RLS'][1] += 1
  pprint.pprint(score_stats)     
  return score_stats

def get_cross_distances(master_dico_gas_stations, master_gas_stations_id, master_gas_stations_prices):
  """
  Function which works with all current gas stations in the database
  Privilege order: rls, gps_coordinates_rls, gps_coordinates_2, gps_coordinates_1
  NOT ENOUGH RAM TO RUN (tested with 3000 though)
  """
  list_gps_valid = []
  list_distances = []
  for id in master_gas_stations_id:
    try:
      list_gps_valid.append(master_dico_gas_stations[id]['gps_coordinates_rls'])
    except:
      try:
        if master_dico_gas_stations[id]['gps_coordinates_2'][2] is not 'na':
          list_gps_valid.append(master_dico_gas_stations[id]['gps_coordinates_2'])
        else:
          try:
            list_gps_valid.append(master_dico_gas_stations[id]['gps_coordinates_1'])
          except:
            list_gps_valid.append([])
      except:
        list_gps_valid.append([])
  for coordinates_1 in list_gps_valid:
    temp_distance_list = []
    if coordinates_1 != []:
      for coordinates_2 in list_gps_valid:
        if coordinates_2 != []:
          temp_distance_list.append(compute_distance([coordinates_1[0], coordinates_1[1]],[coordinates_2[0], coordinates_2[1]]))
        else:
          temp_distance_list.append(None)
    list_distances.append(temp_distance_list)
  return list_distances

def master_filter_geocoding(master_dico_gas_stations, master_gas_stations_id):
  accepted_precision = ['ROOFTOP', 'RANGE_INTERPOLATED']
  list_gps_valid = []
  list_ids_valid = []
  for id in master_gas_stations_id:
    try:
      list_gps_valid.append(master_dico_gas_stations[id]['gps_coordinates_rls'])
    except:
      try:
        if master_dico_gas_stations[id]['gps_coordinates_2'][2] in accepted_precision:
          list_gps_valid.append(master_dico_gas_stations[id]['gps_coordinates_2'])
        else:
          try:
            if master_dico_gas_stations[id]['gps_coordinates_1'][2] in accepted_precision:
              list_gps_valid.append(master_dico_gas_stations[id]['gps_coordinates_1'])
            else:
              list_gps_valid.append([])
          except:
            list_gps_valid.append([])
      except:
        list_gps_valid.append([])
  return list_gps_valid
 
def master_rls_ld_filtered(master):
  new_master = {}
  for id, details in master.iteritems():
    if details['LastDay'] == '1':
      new_master[id] = details
  return new_master

def compute_distances_in_rls_ld(master):
  list_rls_ids = []
  list_rls_coordinates = []
  list_rls_distances = []
  for id, details in master.iteritems():
    try:
      list_rls_coordinates.append([details['gps_coordinates_rls'][0],details['gps_coordinates_rls'][1]])
      list_rls_ids.append(id)
    except:
      pass
  for coordinates_1 in list_rls_coordinates:
    temp_distance_list = []
    for coordinates_2 in list_rls_coordinates:
      temp_distance_list.append(compute_distance(coordinates_1,coordinates_2))
    list_rls_distances.append(temp_distance_list)
  return [list_rls_ids, list_rls_distances]

def compute_distances_general(master_dico_gas_stations, master_gas_stations_id):
  accepted_precision = ['ROOFTOP', 'RANGE_INTERPOLATED']
  list_gps_valid = []
  for id in master_gas_stations_id:
    try:
      list_gps_valid.append([master_dico_gas_stations[id]['gps_coordinates_rls'][0],master_dico_gas_stations[id]['gps_coordinates_rls'][1]])
    except:
      try:
        if master_dico_gas_stations[id]['gps_coordinates_2'][2] in accepted_precision:
          list_gps_valid.append([master_dico_gas_stations[id]['gps_coordinates_2'][0],master_dico_gas_stations[id]['gps_coordinates_2'][1]])
        else:
          try:
            if master_dico_gas_stations[id]['gps_coordinates_1'][2] in accepted_precision:
              list_gps_valid.append([master_dico_gas_stations[id]['gps_coordinates_1'][0],master_dico_gas_stations[id]['gps_coordinates_1'][1]])
            else:
              list_gps_valid.append([])
          except:
            list_gps_valid.append([])
      except:
        list_gps_valid.append([])
  list_cross_distances = []
  for coordinates_1 in list_gps_valid:
    temp_distance_list = []
    if coordinates_1 != []:
      for coordinates_2 in list_gps_valid:
        if coordinates_2 != []:
          temp_distance_list.append(compute_distance(coordinates_1,coordinates_2))
        else:
          temp_distance_list.append(None)       
    list_cross_distances.append(temp_distance_list)
  return list_cross_distances

def get_close_competitors_rls(master_distances, master_gas_stations_id, distance_bound):
  """
  Function currently adapted to work with the result of rls distance
  Assumes a master: [list_of_rls_ids, list of cross distances]
  Function yet returns list in "master order" with id and distances of competitors
  Would be good to add desc stats on missing competitors vs. rls last day
  """
  list_results = []
  for id_station in master_gas_stations_id:
    try:
      id_station_index = master_distances[0].index(id_station)
      station_competitors = []
      station_distances = []
      for competitor_index in range(0,len(master_distances[0])):
        if master_distances[1][id_station_index][competitor_index] < distance_bound and master_distances[0][competitor_index] != id_station:
          station_competitors.append(master_distances[0][competitor_index])
          station_distances.append(master_distances[1][id_station_index][competitor_index])
      list_results.append([station_competitors, station_distances])
    except:
      list_results.append([['na'],['na']])      
  return list_results

def get_close_competitors_general(master_distances_general, master_gas_stations_id, distance_bound):
  list_results = []
  for station_index in range(0,len(master_distances_general)):
    station_competitors = []
    station_distances = []
    if master_distances_general[station_index] == []:
      list_results.append([['na'],['na']])
    else:
      for distance_index in range(0,len(master_distances_general[station_index])):
          if master_distances_general[station_index][distance_index] is not None and \
             master_distances_general[station_index][distance_index] < distance_bound and \
             station_index != distance_index:
                station_competitors.append(master_gas_stations_id[distance_index])
                station_distances.append(master_distances_general[station_index][distance_index])          
      list_results.append([station_competitors, station_distances])
  return list_results

def get_nb_competitors_within(master_competition_general, list_distance_bounds):
  list_results = []
  for station_competitors in master_competition_general:
    station_competition = []
    if station_competitors != [['na'],['na']]:
      for distance_bound in list_distance_bounds:
        c_competitors = 0
        for distance, id in zip(station_competitors[1], station_competitors[0]):
          if distance < distance_bound:
            c_competitors += 1
        station_competition.append(c_competitors)
    else:
      station_competition = ['.' for x in range(0,len(list_distance_bounds))]
    list_results.append(station_competition)
  return list_results

def get_list_pairs_ids_distances_rls_bound(master, km_bound):
  """
  Function currently adapted to work with the result of rls distance
  Assumes a master: [list_of_rls_ids, list of cross distances]
  Function returns lists of id pairs and distances
  """
  list_pair_ids = []
  list_distances = []
  for index_1 in range(0,len(master[1])):
    for index_2 in range(index_1 + 1, len(master[1])):
      if master[1][index_1][index_2] < km_bound:
          list_distances.append(master[1][index_1][index_2])
          list_pair_ids.append([master[0][index_1], master[0][index_2]])
  return [list_pair_ids, list_distances]

def get_list_pairs_ids_distances_general_bound(master_distances_general, master_gas_stations_id, km_bound):
  list_pair_ids = []
  list_distances = []
  for index_1 in range(0,len(master_distances_general)):
    if master_distances_general[index_1] != []:
      for index_2 in range(index_1 + 1, len(master_distances_general)):
        if master_distances_general[index_1][index_2] is not None and \
           master_distances_general[index_1][index_2] < km_bound:
              list_distances.append(master_distances_general[index_1][index_2])
              list_pair_ids.append([master_gas_stations_id[index_1], master_gas_stations_id[index_2]])
  return [list_pair_ids, list_distances]

def get_list_pair_rls_rank_reversals_bound(master_pairs, master_gas_stations_id, master_price_float):
  """
  Also valid for the general case (just need a master_pairs = [list_id_pairs, list_distances_pairs]
  """
  list_pair_rank_reversals = []
  for index_station in range(0, len(master_pairs[0])):
    try:
      index_master_id_1 = master_gas_stations_id.index(master_pairs[0][index_station][0])
      index_master_id_2 = master_gas_stations_id.index(master_pairs[0][index_station][1])
      less_expensive = 0
      more_expensive = 0
      period_count = 0
      for index_period in range(0,len(master_price_float[index_master_id_1])):  
        if master_price_float[index_master_id_1][index_period] is not None and \
           master_price_float[index_master_id_2][index_period] is not None:
              if master_price_float[index_master_id_1][index_period] < master_price_float[index_master_id_2][index_period]:
                less_expensive += 1.0
              elif master_price_float[index_master_id_1][index_period] > master_price_float[index_master_id_2][index_period]:
                more_expensive += 1.0
              else:
                pass
              period_count += 1.0
      if period_count > 0:
        rank_reversal = min(less_expensive / period_count, more_expensive / period_count)
        list_pair_rank_reversals.append(round(rank_reversal,3))
      else:
        list_pair_rank_reversals.append('.')
    except:
      list_pair_rank_reversals.append('.')
  return list_pair_rank_reversals

def stat_des_competitors_rls(master_rls_ld, master_rls_ld_competition, master_gas_stations_id, bound_considered):
  print '\nStats des on competition in rls & stations still present in my data,', bound_considered, 'km bound'
  """
  stat des on gas station environment is well known (based on rls)
  """
  print len(master_rls_ld), 'gas stations present the last day in rls'
  print len([x for x in master_rls_ld_competition if x != [['na'], ['na']]]), 'gas stations rls ld still in my data'
  list_percent_competitors = []
  dico_stat_des_competitors = dict((x,0) for x in range(0,100))
  for station_competitors in master_rls_ld_competition:
    nb_competitors = 0.0
    nb_survivors = 0.0
    if station_competitors != [['na'],['na']]:
      for distance, id in zip(station_competitors[1], station_competitors[0]):
        if distance < bound_considered:
          nb_competitors += 1.0
          if id in master_gas_stations_id:
            nb_survivors += 1.0
      if nb_competitors == 0:
        list_percent_competitors.append(1)
      else:
        list_percent_competitors.append(nb_survivors/nb_competitors)
      dico_stat_des_competitors[nb_competitors] += 1
      # what really is, not what we have with prices...
    else:
      list_percent_competitors.append(None)
  print len([x for x in list_percent_competitors if x != None]), 'not None in stats about rls survivors (simple check)'
  print len([x for x in list_percent_competitors if x != None and x == 1.0]), 'stations will all competitors from rls'
  print len([x for x in list_percent_competitors if x != None and x > 0.7]), 'stations with >0.7% of competitors from rls'
  print np.mean([x for x in list_percent_competitors if x != None]), 'mean % competitors from rls in data'
  print np.median([x for x in list_percent_competitors if x != None]), 'median % competitors roms rls in data'
  return [list_percent_competitors, dico_stat_des_competitors]

def stat_des_competitors_general(master_competition_general, master_gas_stations_id, bound_considered):
  print len(master_gas_stations_id), 'gas stations present in my data'
  print len([x for x in master_competition_general if x != [['na'], ['na']]]), 'gas stations with gps coordinates'
  dico_stat_des_competitors = dict((x,0) for x in range(0,100))
  for station_competitors in master_competition_general:
    nb_competitors = 0
    if station_competitors != [['na'],['na']]:
      for distance, id in zip(station_competitors[1], station_competitors[0]):
        if distance < bound_considered:
          nb_competitors += 1
      dico_stat_des_competitors[nb_competitors] += 1
  return dico_stat_des_competitors

def get_price_change_frequency(master_price_float):
  list_of_results_final = []
  for pl_index in range(0,len(master_price_float)):
    first_valid = 0
    while master_price_float[pl_index][first_valid] is None \
    and first_valid < len(master_price_float[pl_index])-1:
      first_valid +=1
    last_valid = 0
    while master_price_float[pl_index][::-1][last_valid] is None \
    and last_valid < len(master_price_float[pl_index])-1:
      last_valid +=1
    if first_valid != len(master_price_float[pl_index])-1:
      last_index = len(master_price_float[pl_index]) - last_valid
    else:
    # case where it is full of None
      first_valid = 0
      last_index = len(master_price_float[pl_index]) - 1
    if None in master_price_float[pl_index][first_valid:last_index]:
      print pl_index
      list_of_results_final.append(['.' for x in range(0,24)])
    else:
      list_p_durations = []
      list_n_durations = []
      list_durations = []
      nb_n_changes = 0
      nb_p_changes = 0
      list_n_changes = []
      list_p_changes = []
      duration = 1
      pos_duration = 0
      for price in range(1, len(master_price_float[pl_index][first_valid:last_index])):
        val_price_chge = master_price_float[pl_index][first_valid:last_index][price] - master_price_float[pl_index][first_valid:last_index][price-1]
        if val_price_chge == 0:
          duration += 1
        else:
          list_durations.append(duration)
          if pos_duration == 1:
            list_p_durations.append(duration)
          else:
            list_n_durations.append(duration)
          pos_duration = 0
          duration = 1
          if val_price_chge > 0:
            nb_p_changes +=1
            list_p_changes.append(val_price_chge)
            pos_duration = 1
          elif val_price_chge < 0:
            nb_n_changes +=1
            list_n_changes.append(val_price_chge)
      nb_changes = nb_n_changes + nb_p_changes
      list_absv_changes = list_p_changes + [-x for x in list_n_changes]
      try:
        list_of_results_1 =  [len(master_price_float[pl_index][first_valid:last_index]), 
                              nb_changes, 
                              nb_n_changes, 
                              nb_p_changes,
                              round(np.median(list_n_changes),4),
                              round(np.mean(list_n_changes),4),
                              round(np.median(list_p_changes),4),
                              round(np.mean(list_p_changes),4),
                              round(np.median(list_durations),4),
                              round(np.mean(list_durations),4),
                              round(np.median(list_n_durations[1:]),4),
                              round(np.mean(list_n_durations[1:]),4), 
                              round(np.median(list_p_durations),4),
                              round(np.mean(list_p_durations),4)]
      except:
        list_of_results_1 = ['.' for x in range(0,14)]
      try:
        list_of_results_2 =  [round(np.min(list_n_changes),4),
                              round(np.max(list_n_changes),4),
                              round(np.min(list_p_changes),4),
                              round(np.max(list_p_changes),4),
                              np.min(list_durations),
                              np.max(list_durations),
                              np.min(list_n_durations[1:]),
                              np.max(list_n_durations[1:]),
                              np.min(list_p_durations),
                              np.max(list_p_durations)]
      except:
        list_of_results_2 = ['.' for x in range(0,10)]
      list_of_results_final.append(list_of_results_1+list_of_results_2)
  return list_of_results_final

def get_price_changes(id_gas_station, master_rls_ld_competition, master_gas_stations_id, master_price_float):
  index_master = master_gas_stations_id.index(id_gas_station)
  list_period_changes = []
  list_period_simultaneous_changes = []
  list_period_after_changes = []
  list_period_before_changes = []
  list_valid_competitors = []
  list_valid_competitors_distances = []
  nb_changes = 0
  # restrict list to competitors present in my data
  for id, distance in zip(master_rls_ld_competition[index_master][0], master_rls_ld_competition[index_master][1]) :
    try:
      index_competitor_master = master_gas_stations_id.index(id)
      if [a for a in master_price_float[index_competitor_master] if a is not None] != []:
        list_valid_competitors.append(id)
        list_valid_competitors_distances.append(distance)
    except:
      pass
  list_valid_competitors_distances, list_valid_competitors = zip(*sorted(zip(list_valid_competitors_distances, list_valid_competitors)))
  list_valid_competitors = list_valid_competitors[0:5] #works also if less than five
  list_valid_competitors_distances = list_valid_competitors_distances[0:5]
  list_simultaneous_changes = [0 for i in range(0,len(list_valid_competitors))]
  list_after_changes = [0 for i in range(0,len(list_valid_competitors))]
  list_before_changes = [0 for i in range(0,len(list_valid_competitors))]
  # loop on periods/competitors
  for period in range(1,len(master_price_float[index_master])):
    if master_price_float[index_master][period] is not None and \
       master_price_float[index_master][period - 1] is not None and \
       master_price_float[index_master][period] != master_price_float[index_master][period-1]:
        nb_changes += 1
        list_period_changes.append(period)
        for ind_competitor in range(0,len(list_valid_competitors)):
          # change at same period
          try:
            index_competitor_master =  master_gas_stations_id.index(list_valid_competitors[ind_competitor])
            if master_price_float[index_competitor_master][period] is not None and \
               master_price_float[index_competitor_master][period - 1] is not None and \
               master_price_float[index_competitor_master][period] != master_price_float[index_competitor_master][period-1]:
                  list_simultaneous_changes[ind_competitor] += 1
                  if period not in list_period_simultaneous_changes:
                    list_period_simultaneous_changes.append(period)
          except:
            pass
          # change at next period
          try:
            if master_price_float[index_competitor_master][period + 1] is not None and \
               master_price_float[index_competitor_master][period] is not None and \
               master_price_float[index_competitor_master][period + 1] != master_price_float[index_competitor_master][period]:
                  list_after_changes[ind_competitor] +=1
                  if period not in list_period_after_changes:
                    list_period_after_changes.append(period)
          except:
            pass
          # change at previous period
          try:
            if master_price_float[index_competitor_master][period - 1] is not None and \
               master_price_float[index_competitor_master][period - 2] is not None and \
               master_price_float[index_competitor_master][period - 1] != master_price_float[index_competitor_master][period - 2]:
                  list_before_changes[ind_competitor] +=1
                  if period not in list_period_before_changes:
                    list_period_before_changes.append(period)
          except:
            pass
  before = list_before_changes
  after = list_after_changes
  simultaneous = list_simultaneous_changes
  return [nb_changes, list_period_changes, before, simultaneous, after, list_valid_competitors, list_valid_competitors_distances]  

def get_pair_stations_stats(id_1, id_2, master_gas_stations_id, master_price_float):
  index_master_1 = master_gas_stations_id.index(id_1)
  index_master_2 = master_gas_stations_id.index(id_2)
  result = []
  try:
    list_tuple_prices = [(a, b) for a, b in zip(master_price_float[index_master_1], master_price_float[index_master_2]) if a is not None and b is not None]
    list_spread = [a-b for a,b in list_tuple_prices]
    list_abs_spread = [abs(a-b) for a, b in list_tuple_prices]
    avg_abs_spread = np.average(list_abs_spread)
    avg_spread = np.average(list_spread)
    std_spread = np.std(list_spread)
    a_cheaper = sum(x < 0 for x in list_spread)
    a_cheaper_spread = np.average([x for x in list_spread if x < 0])
    b_cheaper = sum(x > 0 for x in list_spread)
    b_cheaper_spread = np.average([x for x in list_spread if x > 0])
    draw = sum(x == 0 for x in list_spread)
    rank_reversals = min(sum(x > 0 for x in list_spread), sum(x < 0 for x in list_spread)) / float(len(list_spread))
    t = 0
    nb_rank_reversals = 0
    while list_spread[t] == 0:
      t +=1
    if list_spread[t] > 0:
      sign_indicator = 1
    else:
      sign_indicator = -1
    for spread in list_spread[t+1:]:
      if sign_indicator * spread < 0:
        nb_rank_reversals += 1
        if spread < 0:
          sign_indicator = -1
        if spread > 0:
          sign_indicator = 1
    inter_result = [avg_spread, std_spread, avg_abs_spread, a_cheaper, b_cheaper, a_cheaper_spread, b_cheaper_spread, draw, rank_reversals, nb_rank_reversals]
    for x in inter_result:
      if np.isnan(x):
        result.append('.')
      else:
        result.append(round(x,4))
  except:
    result = ['.' for x in range(0,10)]
  return result

def get_station_price_spread(id_gas_station, master_gas_stations_id, master_rls_ld_competition, master_price_float, km_bound):
  # deprecated?
  index_master = master_gas_stations_id.index(id_gas_station)
  if master_rls_ld_competition[index_master] != [['na'],['na']]:
    for distance, id in zip(master_rls_ld_competition[index_master][1], master_rls_ld_competition[index_master][0]):
      if distance < km_bound:
        try:
          index_competitor_master =  master_gas_stations_id.index(id)
          list_tuple_prices = [(a, b) for a, b in zip(master_price_float[index_master_1], master_price_float[index_master_2]) if a is not None and b is not None]
          list_spread = [a-b for a,b in list_tuple_prices]
          list_abs_spread = [abs(a-b) for a, b in list_tuple_prices]
          avg_abs_spread = np.average(list_abs_spread)
          avg_spread = np.average(list_spread)
          std_spread = np.std(list_spread)
          a_cheaper = sum(x < 0 for x in list_spread)
          a_cheaper_spread = np.average([x for x in list_spread if x < 0])
          b_cheaper = sum(x > 0 for x in list_spread)
          b_cheaper_spread = np.average([x for x in list_spread if x > 0])
          draw = sum(x == 0 for x in list_spread)
          rank_reversals = min(sum(x > 0 for x in list_spread), sum(x < 0 for x in list_spread)) / float(len(list_spread))
          result = [avg_spread, std_spread, avg_abs_spread, a_cheaper, b_cheaper, a_cheaper_spread, b_cheaper_spread, draw, rank_reversals]
        except:
          result = ['.' for x in range(0,9)]
      else:
        result = ['.' for x in range(0,9)]
      list_results.append(result)
  return

def get_master_price_dispersion(master_gas_stations_id, master_dico_gas_stations, master_rls_ld_competition, master_price_float, km_bound):
  list_results = []
  for index_master in range(0, len(master_rls_ld_competition)):
    if (master_rls_ld_competition[index_master] != [['na'],['na']]) and (master_dico_gas_stations[master_gas_stations_id[index_master]]['highway'] != 1):
      list_indexes = [index_master]
      for distance, id in zip(master_rls_ld_competition[index_master][1], master_rls_ld_competition[index_master][0]):
        if distance < km_bound:
            if (id in master_gas_stations_id) and (master_dico_gas_stations[id]['highway'] != 1):
              list_indexes.append(master_gas_stations_id.index(id))
      station_market_prices = zip(*[master_price_float[ind] for ind in list_indexes])
      nb_competitors = len(list_indexes)
      list_station_results = []
      for period_prices in station_market_prices:
        period_valid_prices = [x for x in period_prices if x is not None]
        if period_valid_prices != []:
          range_period = max(period_valid_prices) - min(period_valid_prices)
          std_period = np.std(period_valid_prices)
          gain_from_search_period = np.mean(period_valid_prices) - min(period_valid_prices)
          period_results = [master_gas_stations_id[index_master], nb_competitors, round(range_period,4), round(std_period,4), round(gain_from_search_period,4)]
        else:
          period_results = [master_gas_stations_id[index_master], '.', '.', '.', '.']
        list_station_results.append(period_results)
      list_results.append(list_station_results)
  return list_results

def get_master_price_dispersion_strict(master_gas_stations_id, master_dico_gas_stations, master_rls_ld_competition, master_price_float, km_bound):
  list_results = []
  global_list_indexes = []
  for index_master in range(0, len(master_rls_ld_competition)):
    if (master_rls_ld_competition[index_master] != [['na'],['na']]) and \
       (master_dico_gas_stations[master_gas_stations_id[index_master]]['highway'] != 1) and \
       (index_master not in global_list_indexes):
          list_indexes = [index_master]
          keep = 1
          for distance, id in zip(master_rls_ld_competition[index_master][1], master_rls_ld_competition[index_master][0]):
            if distance < km_bound:
              if (id in master_gas_stations_id) and \
                 (master_dico_gas_stations[id]['highway'] != 1):
                    list_indexes.append(master_gas_stations_id.index(id))
                    competitor_index = master_gas_stations_id.index(id)
                    if competitor_index in global_list_indexes:
                      keep = 0
          if keep == 1:
            global_list_indexes += list_indexes
            station_market_prices = zip(*[master_price_float[ind] for ind in list_indexes])
            nb_competitors = len(list_indexes)
            list_station_results = []
            for period_prices in station_market_prices:
              period_valid_prices = [x for x in period_prices if x is not None]
              if period_valid_prices != []:
                range_period = max(period_valid_prices) - min(period_valid_prices)
                std_period = np.std(period_valid_prices)
                gain_from_search_period = np.mean(period_valid_prices) - min(period_valid_prices)
                period_results = [master_gas_stations_id[index_master], nb_competitors, round(range_period,4), round(std_period,4), round(gain_from_search_period,4)]
              else:
                period_results = [master_gas_stations_id[index_master], '.', '.', '.', '.']
              list_station_results.append(period_results)
            list_results.append(list_station_results)
  return list_results

def get_station_closest_supermarket(id_gas_station, master_rls_ld_competition, master_gas_stations_id, master_dico_gas_stations, dico_brands):
  index_master = master_gas_stations_id.index(id_gas_station)
  competitors_list = master_rls_ld_competition[index_master]
  list_distances_supermarket = []
  list_ids_supermarket = []
  if master_rls_ld_competition[index_master] != [['na'],['na']]:
    for distance, id in zip(master_rls_ld_competition[index_master][1], master_rls_ld_competition[index_master][0]):
      try:
        if dico_brands[get_str_no_accent(master_dico_gas_stations[id]['brand_station'][0]).upper()][2] == 'SUP':
          list_distances_supermarket.append(distance)
          list_ids_supermarket.append(id)
      except:
        pass
    supermarkets = sorted(zip(list_distances_supermarket, list_ids_supermarket))
    try:
      result = [supermarkets[0][0], supermarkets[0][1]]
    except:
      result = ['.', '.']
  else:
    result = ['.', '.']
  return result
  
def get_master_supermarket(master_rls_ld_competition, master_gas_stations_id, master_dico_gas_stations, dico_brands):
  list_results = []
  for index_master in range(0,len(master_gas_stations_id)):   
    list_distances_supermarket = []
    list_ids_supermarket = []
    if master_rls_ld_competition[index_master] != [['na'],['na']]:
      for distance, id in zip(master_rls_ld_competition[index_master][1], master_rls_ld_competition[index_master][0]):
        try:
          if dico_brands[get_str_no_accent(master_dico_gas_stations[id]['brand_station'][0]).upper()][2] == 'SUP':
            list_distances_supermarket.append(distance)
            list_ids_supermarket.append(id)
        except:
          pass
      supermarkets = sorted(zip(list_distances_supermarket, list_ids_supermarket))
      try:
        result = [supermarkets[0][0], supermarkets[0][1]]
      except:
        result = ['.', '.']
    else:
      result = ['.', '.']
    list_results.append(result)
  return list_results

def print_long_data(file_path, master_dates, master_dico_gas_stations, master_gas_stations_id, master_price_float, dico_brands, rotterdam_prices, master_supermarket, master_nb_competitors, stat_des_price_change, list_price_errors):
  """
  long_file_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\final_stats_files\\long_data_test.txt'
  print_long_data(long_file_path, master_dates, master_dico_gas_stations, master_gas_stations_id, master_price_float, dico_brands, rotterdam_prices, master_supermarket, master_nb_competitors_general, stat_des_price_change, list_price_errors)
  """
  if os.path.exists(file_path):
    os.remove(file_path)
  fichier = open(file_path, 'a')
  header = 'id, period, date, price, duration, price_error, rotterdam, highway, supermarket, brand_1, brand_2, brand_type, nb_periods, nb_chges,'
  list_competition = ['nb_comp_%s_km_'%x for x in [0.3, 0.5, 0.7, 1, 2, 3, 4, 5]]
  list_services = ['ser_%s' %x for x in range(1,21)]
  header += ','.join(list_services + list_competition) + '\n'
  fichier.write(header.encode('utf-8'))
  for station_index in range(0,len(master_gas_stations_id)):
    id = master_gas_stations_id[station_index]
    station_brand_changes = copy.copy(master_dico_gas_stations[id]['brand_changes'])
    station_brand_changes.append(len(master_dates))
    for period_index in range(0,len(master_price_float[station_index])):
      i = 0
      while period_index >= station_brand_changes[i+1]:
        i += 1
      if master_price_float[station_index][period_index] is not None:
        if period_index == 0:
          duration = 1
        else:
          if (master_price_float[station_index][period_index-1] is None) or (master_price_float[station_index][period_index] != master_price_float[station_index][period_index-1]):
              duration = 1
          else:
            duration += 1
      else:
        duration = '.'
      station_brand = master_dico_gas_stations[id]['brand_station'][i]
      supermarket = master_supermarket[station_index][0]
      line_to_be_printed = '%s,%s,%s,%s,%s,%s,%s,%s,%s'  %(master_gas_stations_id[station_index], 
                                                           period_index, 
                                                           master_dates[period_index], 
                                                           master_price_float[station_index][period_index],
                                                           duration,
                                                           list_price_errors[station_index][period_index],
                                                           rotterdam_prices[master_dates[period_index]],
                                                           master_dico_gas_stations[id]['highway'],
                                                           supermarket)
      list_brands = [dico_brands[get_str_no_accent(station_brand).upper()][0], dico_brands[get_str_no_accent(station_brand).upper()][1], dico_brands[get_str_no_accent(station_brand).upper()][2]]
      price_stats = stat_des_price_change[station_index][0:2]
      services = master_dico_gas_stations[id]['service_list']
      competition = master_nb_competitors[station_index]
      line_to_be_printed += ',' + ','.join(list_brands + map(str,price_stats) + map(str, services) + map(str,competition)) + '\n'
      fichier.write(line_to_be_printed.encode('utf-8'))
  fichier.close()          

# to be added: presence of supermarket in the area, rural/city (code)  
def print_rank_reversals(master_pairs, master_rank_reversals, master_dico_gas_stations, file_path, dico_brands, master_gas_stations_id, stat_des_price_change, master_competition, master_nb_competitors, master_price_float):
  """
  rank_reversals_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\final_stats_files\\rank_reversals_test_2.txt'
  print_rank_reversals(master_pairs_general, master_general_rank_reversals, master_dico_gas_stations, rank_reversals_path, dico_brands, master_gas_stations_id, stat_des_price_change, master_competition_general, master_nb_competitors_general, master_price_float)
  """
  list_highway_gas_stations = []
  for k,v in master_dico_gas_stations.iteritems():
    try:
      if v['highway'] == 1:
        list_highway_gas_stations.append(k)
    except:
      pass
  if os.path.exists(file_path):
    os.remove(file_path)
  fichier = open(file_path, 'a')
  list_competition_1 = ['nb_comp_%s_km_1'%x for x in [0.3, 0.5, 0.7, 1, 2, 3, 4, 5]]
  list_competition_2 = ['nb_comp_%s_km_2'%x for x in [0.3, 0.5, 0.7, 1, 2, 3, 4, 5]]
  list_spread = ['avg_spread', 'std_spread', 'avg_abs_spread', 'a_cheaper', 'b_cheaper', 'a_cheaper_spread', 'b_cheaper_spread', 'draw', 'rank_reversals', 'nb_rank_reversals']
  header = 'pair, distance, brand_1, brand_2, brand_type_1, brand_type_2, supermarket_1, supermarket_2,' + \
           'nb_periods_1, nb_periods_2, nb_chges_1, nb_chges_2, rank_reversals_bu,' + \
           ','.join(list_competition_1) + ',' + ','.join(list_competition_2) + ',' + ','.join(list_spread) + '\n'
  fichier.write(header)
  for index in range(0, len(master_pairs[0])):
    id_1 = master_pairs[0][index][0]
    id_2 = master_pairs[0][index][1]
    if id_1 not in list_highway_gas_stations and id_2 not in list_highway_gas_stations:
      index_master_1 = master_gas_stations_id.index(id_1)
      index_master_2 = master_gas_stations_id.index(id_2)
      distance = master_pairs[1][index]
      brand_1 = dico_brands[get_str_no_accent(master_dico_gas_stations[id_1]['brand_station'][0]).upper()][1]
      brand_2 = dico_brands[get_str_no_accent(master_dico_gas_stations[id_2]['brand_station'][0]).upper()][1]
      brand_type_1 = dico_brands[get_str_no_accent(master_dico_gas_stations[id_1]['brand_station'][0]).upper()][2]
      brand_type_2 = dico_brands[get_str_no_accent(master_dico_gas_stations[id_2]['brand_station'][0]).upper()][2]
      supermarket_1 = get_station_closest_supermarket(id_1, master_competition, master_gas_stations_id, master_dico_gas_stations, dico_brands)[0]
      supermarket_2 = get_station_closest_supermarket(id_2, master_competition, master_gas_stations_id, master_dico_gas_stations, dico_brands)[0]
      nb_periods_1 = stat_des_price_change[index_master_1][0]
      nb_periods_2 = stat_des_price_change[index_master_2][0]
      nb_chges_1 = stat_des_price_change[index_master_1][1]
      nb_chges_2 = stat_des_price_change[index_master_2][1]
      rank_reversals = master_rank_reversals[index]
      competition_1 = master_nb_competitors[index_master_1]
      competition_2 = master_nb_competitors[index_master_2]
      spread = get_pair_stations_stats(id_1, id_2, master_gas_stations_id, master_price_float)
      station_str = '%s-%s,'%(id_1, id_2) + ','.join(map(str,[distance, brand_1, brand_2, brand_type_1, brand_type_2, \
                                                                supermarket_1, supermarket_2, nb_periods_1, nb_periods_2, \
                                                                nb_chges_1, nb_chges_2, rank_reversals]) + \
                                                                map(str,competition_1)+ map(str,competition_2) + \
                                                                map(str, spread)) + '\n'
      fichier.write(station_str)
  fichier.close()

def print_wide_data(file_path, master_dico_gas_stations, dico_brands, master_gas_stations_id, master_competition_general, master_competition, master_gas_stations_change_frequency, master_asymmetry, master_supermarket):
  """
  wide_file_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\final_stats_files\\wide_data_test.txt'
  print_wide_data(wide_file_path, master_dico_gas_stations, dico_brands, master_gas_stations_id, master_competition_general, master_nb_competitors_general, stat_des_price_change, list_asymmetry_results_1, master_supermarket)
  """
  if os.path.exists(file_path):
    os.remove(file_path)
  fichier = open(file_path, 'a')
  list_dico_str_information = ['name_station', 'street_station', 'city_station', 'TAU2010']
  list_dico_num_information = ['highway']
  list_other_information = ['brand', 'brand_type', 'dist_supermarket']
  list_services = ['ser_%s' %x for x in range(1,21)]
  list_competition = ['nb_comp_%s_km'%x for x in [0.3, 0.5, 0.7, 1, 2, 3, 4, 5]]
  list_change_frequency = ['nb_per', 'nb_chges', 'nb_n_chges', 'nb_p_chges',
                           'med_n_chges','avg_n_chges', 'med_p_chges','avg_p_chges',
                           'med_duration','avg_duration', 'med_n_duration', 'avg_n_duration',
                           'med_p_duration', 'avg_p_duration', 'min_n_chges', 'max_n_chges',
                           'min_p_chges', 'max_p_chges', 'min_duration', 'max_duration',
                           'min_n_duration', 'max_n_duration', 'min_p_duration', 'max_p_duration']
  list_asymmetry = ['bacon_c', 'bacon_m', 'bacon_coef_er', 'bacon_coef_ersq', 'bacon_pval_er', 'bacon_pval_ersq' ] + \
                   ['bor_c_%s'%x for x in range(0,(len(master_asymmetry[0])-6)/2)] +\
                   ['bor_p_%s'%x for x in range(0,(len(master_asymmetry[0])-6)/2)]
  header = 'id,' + ','.join(list_dico_str_information +\
                            list_dico_num_information +\
                            list_other_information +\
                            list_services +\
                            list_competition +\
                            list_change_frequency +\
                            list_asymmetry) + '\n'
  fichier.write(header)
  for id, details in master_dico_gas_stations.iteritems():
    gas_station_string = '%s,' %id
    for info_str in list_dico_str_information:
      if info_str in details.keys():
        detail = '%s'%details[info_str]
        gas_station_string += suppr_accent(string.replace(detail,',','').encode('latin-1')).decode('latin-1') + ','
      else:
        gas_station_string += 'na,'
    for info_num in list_dico_num_information:
      if info_num in details.keys():
        gas_station_string += '%s,'%details[info_num]
      else:
        gas_station_string += 'na,'
    brand = dico_brands[get_str_no_accent(details['brand_station'][0]).upper()][1]
    brand_type = dico_brands[get_str_no_accent(details['brand_station'][0]).upper()][2]
    supermarket = '%s' %master_supermarket[details['rank_station']][0]
    services = details['service_list']
    competition = master_competition[details['rank_station']]
    change_frequency = master_gas_stations_change_frequency[details['rank_station']]
    asymmetry = master_asymmetry[details['rank_station']]
    list_further_str = [brand, brand_type, supermarket] + map(str,services) + map(str,competition) + map(str,change_frequency) + map(str,asymmetry)
    gas_station_string += ','.join(list_further_str) +'\n'
    fichier.write(gas_station_string.encode('utf-8'))
  fichier.close()

def print_market_price_dispersion(file_path, master_gas_stations_id, master_rotterdam, master_price_dispersion):
  """
  dispersion_file_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\final_stats_files\\dispersion_data_test.txt'
  print_market_price_dispersion(dispersion_file_path, master_gas_stations_id, master_rotterdam_float, master_price_dispersion)
  dispersion_st_file_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\final_stats_files\\dispersion_st_data_test.txt'
  print_market_price_dispersion(dispersion_st_file_path, master_gas_stations_id, master_rotterdam_float, master_price_dispersion_st)
  
  """
  if os.path.exists(file_path):
    os.remove(file_path)
  fichier = open(file_path, 'a')
  header = 'id, nb_competitors, range, std, gain_from_search, rotterdam_price\n'
  fichier.write(header)
  for market_index in range(0,len(master_price_dispersion)):
    for period_index in range(0,len(master_price_dispersion[market_index])):
      market_string = ','.join(map(str, master_price_dispersion[market_index][period_index] + [master_rotterdam[period_index]])) + '\n'
      fichier.write(market_string.encode('utf-8'))
  fichier.close()

def get_plot_prices(list_ids, master_gas_stations_id, master_price_float, master_dico_gas_stations):
  plt.figure()
  for id in list_ids:
    try:
      index_gas_station = master_gas_stations_id.index(id)
      id_price_array = np.array(master_price_float[index_gas_station])
      id_price_array_ma = np.ma.masked_where(id_price_array is None, id_price_array)
      axis = np.array([i for i in range(0, len(master_price_float[index_gas_station]))]) 
      plt.plot(axis, id_price_array_ma, label='%s%s' %(id,master_dico_gas_stations[id]['brand_station'][0]))
      plt.legend(loc = 4)
    except:
      pass
  plt.show()

"""
test = get_price_changes(rls_ld_ids[0], rls_ld_ids, rls_ld_competitors, master_gas_stations_id, master_price_float, list_distances_required, 3)
list_total = []
for index in range(0,len(test[5])):
  list_total.append(test[2][1][index]+test[3][1][index]+test[4][1][index])
"""
  
# RANK REVERSAL ANALYSIS (in general, upper distance limit, then threshold)  
# check RN, RD etc.

# PRINT TO USE IN STAT SOFTWARES
# list of ids and overall unique elements to print for several lines
# list of periods / dates
# list of unique elements: prices (or price differences etc.)
# In general: sublist of gas stations/periods... want the rest to follow

"""
def compute_distances_in_rls_ld_smart(master):
  list_rls_ids =[]
  list_rls_coordinates = []
  list_rls_distances = []
  for id, details in master.iteritems():
    try:
      details['gps_coordinates_rls'] = [float(details['latDeg']), float(details['longDeg'])]
      list_rls_ids.append(id)
      list_rls_coordinates.append(details['gps_coordinates_rls'])
    except:
      details['gps_coordinates_rls'] = []
  for index_1 in range(1,len(list_rls_coordinates)):
    temp_distance_list = []
    for index_2 in range(index_1 + 1, list_rls_coordinates):
      temp_distance_list.append(compute_distance(list_rls_coordinates[index_1], list_rls_coordinates[index_2]))
    list_rls_distances.append(temp_distance_list)
  return [list_rls_ids, list_rls_distances]

def get_gas_station_distances(master_distances, gas_station_index):
  list_gas_station_distances = []
  if gas_station_index == 0:
    list_gas_station_distances = master_distances[1][gas_station_index]
  else:
    for index_1 in range(1, gas_station_index + 1):
      list_gas_station_distances.append(master_distances[index_1 - 1][gas_station_index])
    list_gas_station_distances.append(0)
    list_gas_station_distances += master_distances[gas_station_index]
  return(list_gas_station_distances)
"""