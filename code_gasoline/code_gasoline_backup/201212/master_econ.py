import json
import os
import codecs
import string
import math
import datetime
import time
from datetime import date, timedelta
import sys
import scipy
from scipy import stats
import numpy as np
sys.path.append('C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\final_code')
from master_geocoding import *
import ls as ls

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

json_master_path = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\json_master'
master_1 = 'master_3'
master_and_missing_dates = dec_json('%s\\%s\\dates' %(json_master_path, master_1))
master_gas_stations_id_and_prices = dec_json('%s\\%s\\lists_gas_stations' %(json_master_path, master_1))
master_dico_gas_stations = dec_json('%s\\%s\\dico_gas_stations' %(json_master_path, master_1))
dico_gas_stations_rls = dec_json('%s\\%s\\dico_gas_stations_rls' %(json_master_path, master_1))
rotterdam_prices = dec_rotterdam('C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\masterpgmtest\\prix_rotterdam.txt')
dico_brands = dec_json('%s\\%s\\dico_brands' %(json_master_path, master_1))
master_dates = master_and_missing_dates[0]
missing_dates = master_and_missing_dates[1]
master_gas_stations_id = master_gas_stations_id_and_prices[0]
master_gas_stations_prices = master_gas_stations_id_and_prices[1]

# Check that the brand dictionnary matches all brands in the gas stations dico
list_of_brands = check_gas_stations_brands(master_dico_gas_stations, dico_brands)

# Create a float list of rotterdam prices
master_rotterdam_float = []
for date in master_dates:
  master_rotterdam_float.append(float(rotterdam_prices[date]))
    
# Make all price lists have the same length (complete with None) and create a float master
for price_list in master_gas_stations_prices:
  while len(price_list) < len(master_dates):
    price_list.append(None)
master_price_float = get_float_master(master_gas_stations_prices, master_dates)

# Price change frequency
stat_des_price_change = get_price_change_frequency(master_price_float)

# Geocoding stats desc
#stat_des_geocoding = stat_des_geocoding(master_dico_gas_stations)
#geocoding_consistency = check_coordinates_consistency(master_dico_gas_stations) 

# Work on competition using rls gps coordinates
# ATTENTION: It makes sense to "keep" rls last day to know the most precise nb of competitors
# Those ideas could yet be added in the general dictionnary
# ANYWAY: Need to ctrl for presence at a given date when building a competition variable
master_rls_ld = master_rls_ld_filtered(dico_gas_stations_rls)
#master_rls_ld_distances = compute_distances_in_rls_ld(master_rls_ld)

#master_rls_ld_pairs = get_list_pairs_ids_distances_rls_bound(master_rls_ld_distances, 10)
master_rls_ld_pairs = dec_json('%s\\%s\\master_rls_ld_pairs' %(json_master_path, master_1))
#master_rls_ld_rank_reversals = get_list_pair_rls_rank_reversals_bound(master_rls_ld_pairs, master_gas_stations_id, master_price_float)
master_rls_ld_rank_reversals = dec_json('%s\\%s\\master_rls_ld_rank_reversals' %(json_master_path, master_1))

#master_rls_ld_competition = get_close_competitors_rls(master_rls_ld_distances, master_gas_stations_id, 10)
master_rls_ld_competition = dec_json('%s\\%s\\master_rls_ld_competition' %(json_master_path, master_1))

#stat_des_comp_rls_1 = stat_des_competitors_rls(master_rls_ld, master_rls_ld_competition, master_gas_stations_id, 1)
#stat_des_comp_rls_3 = stat_des_competitors_rls(master_rls_ld, master_rls_ld_competition, master_gas_stations_id, 3)

master_nb_competitors_rls_ld = get_nb_competitors_within(master_rls_ld_competition, [0.3, 0.5, 0.7, 1, 2, 3, 4, 5])

# Work on competition with general master
#master_distances_general = compute_distances_general(master_dico_gas_stations, master_gas_stations_id)
#master_competition_general = get_close_competitors_general(master_distances_general, master_gas_stations_id, 10)
master_competition_general = dec_json('%s\\%s\\master_competition_general' %(json_master_path, master_1))
#master_pairs_general = get_list_pairs_ids_distances_general_bound(master_distances_general, master_gas_stations_id, 10)
master_pairs_general = dec_json('%s\\%s\\master_pairs_general' %(json_master_path, master_1))
#master_general_rank_reversals = get_list_pair_rls_rank_reversals_bound(master_pairs_general, master_gas_stations_id, master_price_float)
master_general_rank_reversals = dec_json('%s\\%s\\master_general_rank_reversals' %(json_master_path, master_1))

#stat_des_comp_general_1 = stat_des_competitors_general(master_competition_general, master_gas_stations_id, 1)
#stat_des_comp_general_3 = stat_des_competitors_general(master_competition_general, master_gas_stations_id, 3)

master_supermarket = get_master_supermarket(master_competition_general, master_gas_stations_id, master_dico_gas_stations, dico_brands)
master_nb_competitors_general = get_nb_competitors_within(master_competition_general, [0.3, 0.5, 0.7, 1, 2, 3, 4, 5])
list_asymmetry_results_1 = dec_json('%s\\%s\\list_asymmetry_results_1' %(json_master_path, master_1))
list_price_errors = dec_json('%s\\%s\\list_price_errors' %(json_master_path, master_1))

for id, details in master_dico_gas_stations.iteritems():
  if 'service_list' not in details.keys():
    details['service_list'] = [u'.' for x in range(0,20)]
  if 'highway' not in details.keys():
    details['highway'] = u'.'

# master_price_dispersion = get_master_price_dispersion(master_gas_stations_id, master_dico_gas_stations, master_rls_ld_competition, master_price_float, 3)
# master_price_dispersion = dec_json('%s\\%s\\master_price_dispersion' %(json_master_path, master_1))
# enc_stock_json(master_price_dispersion, '%s\\%s\\master_price_dispersion' %(json_master_path, master_1))

# master_price_dispersion_st = get_master_price_dispersion_strict(master_gas_stations_id, master_dico_gas_stations,master_rls_ld_competition, master_price_float, 3)
# master_price_dispersion_st = dec_json('%s\\%s\\master_price_dispersion_st' %(json_master_path, master_1))
# enc_stock_json(master_price_dispersion, '%s\\%s\\master_price_dispersion_st' %(json_master_path, master_1))


"""
old back up
list_string_asymmetry_l_1 = dec_json('%s\\%s\\list_string_asymmetry_l_1' %(json_master_path, master_1))
list_string_asymmetry_l_2 = dec_json('%s\\%s\\list_string_asymmetry_l_2' %(json_master_path, master_1))

for i in range(0,40):
	print i,stat_des_comp_rls_3[1][i],stat_des_comp_general_3[i]

# At station level (to be used in loop... when printing (?)

# Get a list of close supermarket ids and distances (de facto within 10 km)
close_supermarkets = get_station_closest_supermarket(master_gas_stations_id[990], master_rls_ld_competition, master_gas_stations_id, master_dico_gas_stations, dico_brands)

# Work with rls
enc_stock_json(master_rls_ld_pairs, '%s\\%s\\master_rls_ld_pairs' %(json_master_path, master_1))
enc_stock_json(master_rls_ld_rank_reversals, '%s\\%s\\master_rls_ld_rank_reversals' %(json_master_path, master_1))
enc_stock_json(master_rls_ld_competition, '%s\\%s\\master_rls_ld_competition' %(json_master_path, master_1))

# Work with general
enc_stock_json(master_competition_general, '%s\\%s\\master_competition_general' %(json_master_path, master_1))
enc_stock_json(master_pairs_general, '%s\\%s\\master_pairs_general' %(json_master_path, master_1))
enc_stock_json(master_general_rank_reversals, '%s\\%s\\master_general_rank_reversals' %(json_master_path, master_1))

path_print_1 = 'C:\\Users\\Etienne\\Desktop\\Programmation\\Python\\Scrapping_project_staser\\final_version\\final_stats_files\\rank_reversals.txt'
# print_rank_reversals(master_dico_gas_stations, rank_reversal_bound_3, path_print_1, dico_brands, master_gas_stations_id, master_gas_stations_prices, master_gas_stations_change_frequency, rls_ld_competitors, rls_ld_ids, list_distances_required)
"""

"""
Restrict to 209 periods:
master_rotterdam_float = [0:210]
master_price_float = [x[0:210] for x in masterprice_float]
"""

# Obtain long term coefficients, realize Bacon's test
list_time = [x for x in range(1,len(master_price_float[0])+1)]
list_bacon_results = []
list_of_errors = []
list_of_errors_sq =[]
list_borenstein_results = []
list_asymmetry_results = []

# would fail at borenstein level if first observation was not valid
for retail_price_array in master_price_float:
  
  try:
    retail_price_array = np.ma.masked_values(retail_price_array, None).filled(np.nan)
  except:
    pass
  A = np.vstack([master_rotterdam_float, list_time, np.ones(len(master_rotterdam_float))]).T
  m,t,c = np.linalg.lstsq(A,np.array(retail_price_array))[0]
  if np.isnan(c) or np.isnan(m):
    bacon_results = ['.', '.']
  else:
    bacon_results = [c, m]
  errors = []
  for price_index in range(0,len(retail_price_array)):
    errors.append(m * master_rotterdam_float[price_index] + t * list_time[price_index] + c - retail_price_array[price_index])
  errors_sq = [x*x for x in errors]
  list_of_errors.append(errors)
  list_of_errors_sq.append(errors_sq)
  try:
    B = np.vstack([errors[:-1], errors_sq[:-1]]).T
    d_price_array = np.array(retail_price_array[1:]) - np.array(retail_price_array[:-1])
    asym_result = ls.OLS(d_price_array, B)
    error_coefs = [round(x,3) for x in list(asym_result.coefs[0:2])]
    error_pvals = [round(x,3) for x in list(asym_result.pvals[0:2])]
    bacon_results += error_coefs + error_pvals
  except:
    bacon_results += ['.' for x in range(0,4)]
  list_bacon_results.append(bacon_results)
  
  try:
    nb_of_d = 1
    
    d_0_p_price_array = []
    d_0_n_price_array = []
    for d_price in d_price_array:
      if np.isnan(d_price):
        d_0_p_price_array.append(d_price)
        d_0_n_price_array.append(d_price)
      elif d_price >=0:
        d_0_p_price_array.append(d_price)
        d_0_n_price_array.append(0)
      elif d_price < 0:
        d_0_p_price_array.append(0)
        d_0_n_price_array.append(d_price)       
    
    d_0_master_rotterdam = np.array(master_rotterdam_float[1:]) - np.array(master_rotterdam_float[:-1])
    d_0_p_master_rotterdam = []
    d_0_n_master_rotterdam = []
    for d_price in d_0_master_rotterdam:
      if np.isnan(d_price):
        d_0_p_master_rotterdam.append(d_price)
        d_0_n_master_rotterdam.append(d_price)
      elif d_price >=0:
        d_0_p_master_rotterdam.append(d_price)
        d_0_n_master_rotterdam.append(0)
      elif d_price < 0:
        d_0_p_master_rotterdam.append(0)
        d_0_n_master_rotterdam.append(d_price)
        
    list_covariates = []
    for i in range(0,nb_of_d):
      list_covariates.append(d_0_n_price_array[0+i:i-nb_of_d])
      list_covariates.append(d_0_p_price_array[0+i:i-nb_of_d])
      list_covariates.append(d_0_n_master_rotterdam[0+i:i-nb_of_d])
      list_covariates.append(d_0_p_master_rotterdam[0+i:i-nb_of_d])
    list_covariates.append(d_0_n_master_rotterdam[nb_of_d:])
    list_covariates.append(d_0_p_master_rotterdam[nb_of_d:])
    list_covariates.reverse()
    list_covariates.append(errors[nb_of_d:-1])
    C = np.vstack(list_covariates).T
    d_0_price_array = d_price_array[nb_of_d:]
    asym_result_borenstein = ls.OLS(d_0_price_array, C, constant = 0)
    bor_coefs = [round(x,3) for x in list(asym_result_borenstein.coefs)]
    bor_ses = [round(x,3) for x in list(asym_result_borenstein.se)]
    bor_pvals = [round(x,3) for x in list(asym_result_borenstein.pvals)]
  except:
    bor_coefs = ['.' for x in range(0, len(asym_result_borenstein.coefs))]
    bor_ses = ['.' for x in range(0, len(asym_result_borenstein.se))]
    bor_pvals = ['.' for x in range(0, len(asym_result_borenstein.pvals))]
  borenstein_results = bor_coefs + bor_pvals
  list_borenstein_results.append(borenstein_results)
  list_asymmetry_results.append(bacon_results + borenstein_results)

enc_stock_json(list_asymmetry_results, '%s\\%s\\list_asymmetry_results_1' %(json_master_path, master_1))
enc_stock_json(list_of_errors, '%s\\%s\\list_price_errors' %(json_master_path, master_1))

"""
# test of ls.OLS to estimate Bacon's model
B = np.vstack([errors[:-1], errors_sq[:-1]]).T
d_price_array = np.array(retail_price_array[1:]) - np.array(retail_price_array[:-1])
asym_result = ls.OLS(d_price_array, B)

# test of ls.OLS to estimate Borenstein's model

retail_price_array = master_price_float[0]
d_price_array = np.array(retail_price_array[1:]) - np.array(retail_price_array[:-1])
errors = lt_adj_coefficients[2][0]
errors_sq = lt_adj_coefficients[3][0]

index_rls = rls_ld_ids.index(list_comp[0][0])
ids_competitors = rls_ld_competitors[0][8][index_rls]
list_of_interest = [list_comp[0][0]] + ids_competitors
get_plot_prices(list_of_interest, master_gas_stations_id, master_price_float, master_dico_gas_stations)

enc_stock_json(dico_brands, '%s\\%s\\dico_brands' %(json_master_path, master_1))
"""

# One master_union_rls (12 922): search correspondance between non matched ids (1612 vs. 3011 in rls)  [LONG TERM]
# One master_present_prices (9911): geocoding checked with rls, and my information only [MEDIUM TERM]
# One master_intersection_rls (8299): smallest set but best quality or comparison of competition variable [NOW]