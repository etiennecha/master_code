# -*- coding: cp1252 -*-

import json
import math
import urllib
import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.append(r'C:\Users\etna\Desktop\Code\Gasoline\scripts')
sys.path.append(r'\\ulysse\users\echamayou\Etienne\Python_mydocs\Scrapping_Gas\Current Version\scripts')
import ls as ls
import statsmodels.api as sm

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

machine_path = r'C:\Users\etna\Desktop\Code\Gasoline'
stata_files_path = r'C:\Users\etna\Desktop\Code\Gasoline\stata'

#machine_path = r'\\ulysse\users\echamayou\Etienne\Python_mydocs\Scrapping_Gas\development_version'
#stata_files_path = r'\\ulysse\users\echamayou\Etienne\Python_mydocs\Scrapping_Gas\stata\stata_python'

info_folder = r'\data_stations\data_info_stations_prix_carb'
price_folder = r'\data_prices'
geocoding_folder = r'\geolocalisation\geocoding'
brand_folder = r'\data_stations\brands'

master_info_gas_stations = dec_json(machine_path + info_folder + r'\current_master_info')
master_price_gas_stations = dec_json(machine_path + price_folder + r'\current_master_price')

cross_distances_dict = dec_json(machine_path + info_folder + r'\cross_distances_dict')
# cross_distances_matrix = np.load(machine_path + info_folder + r'\cross_distances_matrix.npy')
list_competitor_lists = dec_json(machine_path + info_folder + r'\list_competitor_lists')
list_competitor_pairs = dec_json(machine_path + info_folder + r'\list_competitor_pairs')

# GENERIC + CONVERSION MASTER PRICE TO FLOAT

def get_id(rank, master_price):
  return master_price['list_ids'][rank]

def get_rank(id, master_price):
  return master_price['dict_general_info'][id]['rank']

def get_id_list_field_results(id, field, master_price_gas_stations):
  j = 0
  list_field_results = []
  for i in range(0, len(master_price_gas_stations['list_dates'])):
    if j < len(master_price_gas_stations['dict_general_info'][id][field]) - 1:
      if master_price_gas_stations['dict_general_info'][id][field][j + 1][1] > i:
        list_field_results.append(master_price_gas_stations['dict_general_info'][id][field][j][0])
      else:
        j += 1
        list_field_results.append(master_price_gas_stations['dict_general_info'][id][field][j][0])
    else:
      while len(list_field_results) < len(master_price_gas_stations['list_dates']):
        list_field_results.append(master_price_gas_stations['dict_general_info'][id][field][j][0])
  return list_field_results

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

def unique(items):
  """
  keep only unique elements in a list
  """
  found = set()
  keep = []
  for item in items:
    if item not in found:
      found.add(item)
      keep.append(item)
  return keep

def convert_master_price_to_float(master_price):
  list_price_lists = []
  for list_price in master_price['list_indiv_prices']:
    list_price_float = []
    for price in list_price:
      try:
        list_price_float.append(float(price))
      except:
        list_price_float.append(None)
    list_price_lists.append(list_price_float)
  master_price['list_indiv_prices'] = list_price_lists

# DATA DISPLAY

def print_list_of_lists(list_of_lists, nb_columns):
  list_of_list_groups = [list_of_lists[i:i+nb_columns] for i in range(0, len(list_of_lists), nb_columns)]
  for list_items in list_of_list_groups:
    tuple_lists = zip(*list_items)
    col_width = max(len(item) for row in tuple_lists for item in row if item is not None) + 2
    for row in tuple_lists:
      row = tuple('.' if x is None else x for x in row)
      print "".join(item.ljust(col_width) for item in row)
    print '-'*100

def print_list_of_lists_from_ranks(list_of_ranks, master_price, nb_columns):
  list_of_id_groups = [list_of_ranks[i:i + nb_columns] for i in range(0, len(list_of_ranks), nb_columns)]
  list_of_lists = [master_price['list_indiv_prices'][i] for i in list_of_ranks]
  list_of_list_groups = [list_of_lists[i:i + nb_columns] for i in range(0, len(list_of_lists), nb_columns)]
  for k in range(0,len(list_of_list_groups)):
    id_list = list_of_id_groups[k]
    col_width_1 = max(len(str(id)) for id in id_list) + 2
    tuple_lists = zip(*list_of_list_groups[k])
    col_width_2 = max(len(str(item)) for row in tuple_lists for item in row if item is not None) + 2
    col_width = max(col_width_1, col_width_2)
    print "".join(str(item).rjust(col_width) for item in id_list)
    for row in tuple_lists:
      row = tuple('.' if x is None else x for x in row)
      print "".join(str(item).rjust(col_width) for item in row)
    print '-'*100

def print_dict_stat_des(dict_stat_des):
  for key, content in dict_stat_des.iteritems():
    print key, len(content)

def get_plot_prices(list_of_ranks, master_price):
  plt.figure()
  for rank in list_of_ranks:
    price_array = np.array([x if x not in [None, ' --'] else np.nan for x in master_price['list_indiv_prices'][rank]])
    price_array_ma = np.ma.masked_array(price_array, np.isnan(price_array))
    axis = np.array([i for i in range(0, len(master_price['list_indiv_prices'][rank]))])
    plt.plot(axis, price_array_ma, label='%s%s' %(get_id(rank, master_price), master_price['dict_general_info'][get_id(rank, master_price)]['brand_station'][0][0]))
    plt.legend(loc = 4)
  plt.show()

def get_plot_list_arrays(list_price_arrays):
  plt.figure()
  for price_array in list_price_arrays:
    axis = np.array([i for i in range(0, len(price_array))])
    plt.plot(axis, price_array, label='')
    plt.legend(loc = 4)
  plt.show()

# PRICE CHANGE VALUE AND FREQUENCY ANALYSIS FUNCTIONS

def get_station_price_change_frequency(id_1, master_price):
  """
  for an id: price change frequency and value stats
  """
  #TODO: duration (?)
  price_array_today = np.array([x if x not in [None, ' --'] else np.nan for x in master_price['list_indiv_prices'][get_rank(id_1, master_price)]][:-1])
  price_array_tomorrow = np.array([x if x not in [None, ' --'] else np.nan for x in master_price['list_indiv_prices'][get_rank(id_1, master_price)]][1:])
  changes = price_array_tomorrow - price_array_today
  nb_same_price = ((np.float64(0) == changes)).sum()
  nb_decrease = ((np.float64(0) > changes)).sum()
  nb_increase = ((np.float64(0) < changes)).sum()
  avg_decrease = np.mean(changes[np.float64(0) > changes])
  avg_increase = np.mean(changes[np.float64(0) < changes])
  return [id_1, nb_same_price, nb_decrease, nb_increase, avg_decrease, avg_increase]

def get_master_price_change_frequency(master_price):
  """
  for all ids in master: price change frequencies and values stats
  """
  list_price_change_frequency = []
  for id in master_price['list_ids']:
    list_price_change_frequency.append(get_station_price_change_frequency(id, master_price))
  return list_price_change_frequency

# PRICE DISPERSION ANALYSIS FUNCTIONS

def get_station_price_dispersion(id_1, cross_distances_dict, list_competitor_lists, master_price, km_bound):
  """
  for an id: price dispersion stats with each competitor within a given nb of km
  """
  price_array_1 = np.array([x if x not in [None, ' --'] else np.nan for x in master_price['list_indiv_prices'][get_rank(id_1, master_price)]])
  rank_competitor_list = cross_distances_dict['list_ids'].index(id_1)
  list_rank_reversals = []
  list_std_spread_ma = []
  list_spreads = []
  list_ids = [id_1]
  for (id_2, distance_competitor) in list_competitor_lists[rank_competitor_list]:
    if distance_competitor < km_bound:
      price_array_2 = np.array([x if x not in [None, ' --'] else np.nan for x in master_price['list_indiv_prices'][get_rank(id_2, master_price)]])
      spread = np.around(price_array_1 - price_array_2, decimals = 3)
      spread_ma = np.ma.masked_array(spread, np.isnan(spread))
      b_cheaper = ((np.float64(0) > spread_ma)).sum()
      a_cheaper = ((np.float64(0) < spread_ma)).sum()
      duration = np.ma.count(spread_ma)
      rank_reversals = np.min([np.float64(b_cheaper)/duration, np.float64(a_cheaper)/duration])
      std_spread_ma = np.std(spread_ma)
      list_rank_reversals.append(rank_reversals)
      list_std_spread_ma.append(std_spread_ma)
      list_ids.append(id_2)
      list_spreads.append(spread)
  return [list_ids, list_rank_reversals, list_std_spread_ma, list_spreads]

def get_master_pair_price_dispersion(list_competitor_pairs, master_price, km_bound):
  """
  price dispersion stats for each pair with distance smaller than a given bound
  """
  #TODO: add the average spread conditional on rank being reversed
  master_pair_price_dispersion = []
  list_pbms = []
  for ((id_1, id_2), distance) in list_competitor_pairs:
    if distance < km_bound:
      price_array_1 = np.array([x if x not in [None, ' --'] else np.nan for x in master_price['list_indiv_prices'][get_rank(id_1, master_price)]])
      price_array_2 = np.array([x if x not in [None, ' --'] else np.nan for x in master_price['list_indiv_prices'][get_rank(id_2, master_price)]])
      spread = np.around(price_array_1 - price_array_2, decimals = 3)
      spread_ma = np.ma.masked_array(spread, np.isnan(spread))
      b_cheaper = ((np.float64(0) > spread_ma)).sum()
      a_cheaper = ((np.float64(0) < spread_ma)).sum()
      duration = np.ma.count(spread_ma)
      rank_reversals = np.min([np.float64(b_cheaper)/duration, np.float64(a_cheaper)/duration])
      std_spread_ma = np.std(spread_ma)
      master_pair_price_dispersion.append(((id_1, id_2), distance, duration, rank_reversals, std_spread_ma))
  return master_pair_price_dispersion

def get_master_market_price_dispersion(cross_distances_dict, list_competitor_lists, master_price, km_bound):
  """
  price dispersion stats for each market (i.e. around each gas station) with distance smaller than a given bound
  """
  master_market_price_dispersion = []
  for id_1 in cross_distances_dict['list_ids']:
    rank_competitor_list = cross_distances_dict['list_ids'].index(id_1)
    if list_competitor_lists[rank_competitor_list] is not None:
      price_array_1 = np.array([x if x not in [None, ' --'] else np.nan for x in master_price['list_indiv_prices'][get_rank(id_1, master_price)]])
      price_array_1_ma = np.ma.masked_array(price_array_1, np.isnan(price_array_1))
      list_ids = [id_1]
      list_price_arrays = [price_array_1_ma]
      for (id_2, distance_competitor) in list_competitor_lists[rank_competitor_list]:
        if distance_competitor < km_bound:
          price_array_2 = np.array([x if x not in [None, ' --'] else np.nan for x in master_price['list_indiv_prices'][get_rank(id_2, master_price)]])
          price_array_2_ma = np.ma.masked_array(price_array_2, np.isnan(price_array_2))
          list_price_arrays.append(price_array_2_ma)
          list_ids.append(id_2)
      std_price_array = np.std(list_price_arrays, axis = 0)
      coeff_var_price_array = np.std(list_price_arrays, axis = 0)/np.mean(list_price_arrays, axis = 0)
      range_price_array = np.max(list_price_arrays, axis = 0) - np.min(list_price_arrays, axis = 0)
      gain_from_search_array = np.mean(list_price_arrays, axis = 0) - np.min(list_price_arrays, axis = 0)
      master_market_price_dispersion.append((list_ids, len(list_ids), std_price_array, coeff_var_price_array, range_price_array, gain_from_search_array))
  return master_market_price_dispersion

# ###############
# CODE EXECUTION
# ###############

convert_master_price_to_float(master_price_gas_stations)

# 1/ AVERAGE PRICE PER PERIOD

master_np_prices = np.array(master_price_gas_stations['list_indiv_prices'], dtype = np.float64)
matrix_np_prices_ma = np.ma.masked_array(master_np_prices, np.isnan(master_np_prices))
period_mean_prices = np.mean(matrix_np_prices_ma, axis = 0)
# get_plot_list_arrays([period_mean_prices, matrix_np_prices_ma[1,:], matrix_np_prices_ma[2,:], matrix_np_prices_ma[4,:]])

# 2/ ANALYSIS OF PRICE CHANGE FREQUENCIES AND VALUES

station_price_chges = get_station_price_change_frequency('1500007', master_price_gas_stations)
master_station_price_chges = get_master_price_change_frequency(master_price_gas_stations)

master_np_prices_chges = master_np_prices[:,:-1] - master_np_prices[:,1:]
list_pos_per_chges = [((np.float64(0) < master_np_prices_chges[:,i])).sum() for i in range(len(master_np_prices_chges[0,:]))]
list_neg_per_chges = [((np.float64(0) > master_np_prices_chges[:,i])).sum() for i in range(len(master_np_prices_chges[0,:]))]
recap_chges = np.vstack([list_pos_per_chges, list_neg_per_chges]).T
array_chges = recap_chges[:,0] + recap_chges[:,1]
# try to represent both on a graph...
plt.step([i for i in range(len(list_pos_per_chges[0:250]))], list_pos_per_chges[0:250])
plt.step([i for i in range(len(list_neg_per_chges[0:250]))], list_neg_per_chges[0:250])
plt.show()
plt.step([i for i in range(len(array_chges[0:250]))], array_chges[0:250])
plt.show()

# 3/ PRICE DISPERSION ANALYSIS
# Check pypeR (comparision sm.OLS vs. ls)

station_price_dispersion = get_station_price_dispersion('1500007', cross_distances_dict, list_competitor_lists, master_price_gas_stations, 5)
master_pair_price_dispersion = get_master_pair_price_dispersion(list_competitor_pairs, master_price_gas_stations, 5)
master_market_price_dispersion = get_master_market_price_dispersion(cross_distances_dict, list_competitor_lists, master_price_gas_stations, 5)


# 3/ A/ REGRESSION OF PAIR PRICE DISPERSION ON DISTANCE

max_pair_distance = 5
matrix_pair_pd = np.array([pd_tuple for pd_tuple in master_pair_price_dispersion if pd_tuple[1] < max_pair_distance])
# col 1: distance, col 3: rank reversals, col 4: spread std
matrix_pair_pd = np.array(np.vstack([matrix_pair_pd[:,1], matrix_pair_pd[:,3], matrix_pair_pd[:,4]]), dtype = np.float64).T
distance = np.vstack([matrix_pair_pd[:,0]]).T
rank_reversals = matrix_pair_pd[:,1]
spread_std = matrix_pair_pd[:,2]
distance = sm.add_constant(distance)
print '\n REGRESSIONS OF PAIR PRICE DISPERSION ON DISTANCE \n'
result_ppd_rank = sm.OLS(rank_reversals, distance, missing = "drop").fit()
print result_ppd_rank.summary(yname='rank_reversals', xname = ['constant', 'distance'])
result_ppd_std = sm.OLS(spread_std, distance, missing = "drop").fit()
print result_ppd_std.summary(yname='spread_std', xname = ['constant', 'distance'])

"""
# ALTERNATIVE IF NAN NOT AUTHORIZED
max_pair_distance = 5
matrix_pair_pd = np.array([pd_tuple for pd_tuple in master_pair_price_dispersion if pd_tuple[1] < max_pair_distance])
# col 1: distance, col 3: rank reversals, col 4: spread std
matrix_pair_pd = np.array(np.vstack([matrix_pair_pd[:,1], matrix_pair_pd[:,3], matrix_pair_pd[:,4]]), dtype = np.float64).T
matrix_pair_pd = np.ma.masked_array(matrix_pair_pd, np.isnan(matrix_pair_pd))
matrix_pair_pd = np.ma.compress_rows(matrix_pair_pd)
distance = np.vstack([matrix_pair_pd[:,0]]).T
rank_reversals = matrix_pair_pd[:,1]
spread_std = matrix_pair_pd[:,2]
print sm.OLS(rank_reversals, sm.add_constant(distance)).fit().summary()
print sm.OLS(rank_reversals, sm.add_constant(distance)).fit().summary()
"""

# header_master_pair_pd = 'distance, rank_reversals, spread_std'
# np.savetxt(stata_files_path + r'\master_pair_pd.txt', matrix_pair_pd, fmt = '%.5f', delimiter = ',', header = header_master_pair_pd)

# 3/ B/ REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE

matrix_master_pd = []
for market in master_market_price_dispersion:
  # create variable containing number of competitors for each period
  array_nb_competitors = np.ones(len(market[2])) * market[1]
  # col 2: std in prices, col 3: coeff var, col 4: range, col 5: gain from search
  matrix_master_pd.append(np.vstack([array_nb_competitors, period_mean_prices, market[2:]]).T)
matrix_master_pd = np.vstack(matrix_master_pd) 
# matrix_master_pd = np.array(matrix_master_pd, dtype = np.float64)

nb_competitors = np.vstack([matrix_master_pd[:,0]]).T
nb_competitors_and_price = np.vstack([matrix_master_pd[:,0], matrix_master_pd[:,1]]).T
std_prices = matrix_master_pd[:,2]
coeff_var_prices = matrix_master_pd[:,3]
range_prices = matrix_master_pd[:,4]
gain_search = matrix_master_pd[:,5]
print 'REGRESSIONS OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE'
print sm.OLS(std_prices, sm.add_constant(nb_competitors), missing = "drop").fit().summary(yname='std_prices', xname = ['constant', 'nb_competitors'])
print sm.OLS(std_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit().summary(yname='std_prices', xname = ['constant', 'nb_competitors', 'price'])
print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors), missing = "drop").fit().summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors'])
print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit().summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors', 'price'])
print sm.OLS(range_prices, sm.add_constant(nb_competitors), missing = "drop").fit().summary(yname='range_prices', xname = ['constant', 'nb_competitors'])
print sm.OLS(range_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit().summary(yname='range_prices', xname = ['constant', 'nb_competitors', 'price'])
print sm.OLS(gain_search, sm.add_constant(nb_competitors), missing = "drop").fit().summary(yname='gain_search', xname = ['constant', 'nb_competitors'])
print sm.OLS(gain_search, sm.add_constant(nb_competitors_and_price), missing = "drop").fit().summary(yname='gain_search', xname = ['constant', 'nb_competitors', 'price'])

"""
# ALTERNATIVE IF NAN NOT AUTHORIZED
matrix_master_pd = []
for individual in master_market_price_dispersion:
  array_nb_competitors = np.ones(len(individual[2])) * individual[1]
  temp_matrix_master_pd = np.vstack([array_nb_competitors, period_mean_prices, individual[2:]])
  if np.all(~np.isnan(temp_matrix_master_pd)):
    matrix_master_pd.append(temp_matrix_master_pd.T)
matrix_master_pd = np.vstack(matrix_master_pd)
# matrix_master_pd = np.array(matrix_master_pd, dtype = np.float64)
nb_competitors = np.vstack([matrix_master_pd[:,0]]).T
prices_and_nb_competitors = np.vstack([matrix_master_pd[:,0], matrix_master_pd[:,1]]).T
std_prices = matrix_master_pd[:,2]
coeff_var_prices = matrix_master_pd[:,3]
range_prices = matrix_master_pd[:,4]
gain_search = matrix_master_pd[:,5]
print sm.OLS(std_prices, sm.add_constant(nb_competitors)).fit().summary()
print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors)).fit().summary()
print sm.OLS(range_prices, sm.add_constant(nb_competitors)).fit().summary()
print sm.OLS(gain_search, sm.add_constant(nb_competitors)).fit().summary()
print sm.OLS(std_prices, sm.add_constant(prices_and_nb_competitors)).fit().summary()
print sm.OLS(coeff_var_prices, sm.add_constant(prices_and_nb_competitors)).fit().summary()
print sm.OLS(range_prices, sm.add_constant(prices_and_nb_competitors)).fit().summary()
print sm.OLS(gain_search, sm.add_constant(prices_and_nb_competitors)).fit().summary()
"""

# header_master_market_pd = 'nb_competitors, prices, std_prices, coeff_var_prices, range_prices, gain_search'
# np.savetxt(stata_files_path + r'\matrix_master_pd_5.txt', matrix_master_pd, fmt = '%.5f', delimiter = ',', header = header_master_market_pd)

# 3/ C/ CLEANING PRICES (NOW BRAND EFFECT ONLY)

dico_brands = dec_json(machine_path + brand_folder + r'\dico_brands')
for id, info in master_price_gas_stations['dict_general_info'].iteritems():
  if get_str_no_accent(info['brand_station'][0][0]).upper() not in dico_brands.keys():
    print id, info['brand_station'][0][0]

price_effect = {'AGIP' : 0,
                'AUCHAN': -.0639177,
                'AUTRE_DIS': .0543546,
                'AUTRE_GMS': -.0557188,
                'AUTRE_IND': -.0051177,
                'AVIA': .003345,
                'BP': .0056645,
                'BRETECHE': -.0031029,
                'CARREFOUR': -.0677206,
                'CASINO': -.0699135,
                'COLRUYT': -.0640661,
                'CORA': -.0621978,
                'DYNEFF': .0013379,
                'ELAN': .0492857,
                'ELF': -.0797696,
                'ESSO': -.0340026,
                'INDEPENDANT':  -.0163602,
                'LECLERC': -.0801179,
                'MOUSQUETAIRES':  -.0711393,
                'SHELL': .0346202,
                'SYSTEMEU': -.0763088,
                'TOTAL': .0208815,
                'TOTAL_ACCESS': -.0556952}

list_brands = []
list_coeffs = []
master_coeffs = []
for id in master_price_gas_stations['list_ids']:
  list_brands.append(dico_brands[get_str_no_accent(master_price_gas_stations['dict_general_info'][id]['brand_station'][0][0]).upper()][1])
for brand in list_brands:
  list_coeffs.append(price_effect[brand])
for coeff in list_coeffs:
  master_coeffs.append([coeff for i in range(len(master_price_gas_stations['list_indiv_prices'][0]))])
matrix_coeffs = np.array(master_coeffs, dtype = np.float64)
matrix_price_cont = master_np_prices - matrix_coeffs

# WARNING: prices replaced by cleaned prices in master:
master_price_gas_stations['list_indiv_prices'] = matrix_price_cont.tolist()

# 3/ D/ REGRESSION OF PAIR PRICE DISPERSION ON DISTANCE WITH CLEANED PRICES

master_pair_price_dispersion_cont = get_master_pair_price_dispersion(list_competitor_pairs, master_price_gas_stations, 5)
master_pair_price_dispersion_cont_print = np.array([elt[1:] for elt in master_pair_price_dispersion_cont])
# header_master_pair_pd_cont = 'distance, duration, rank_reversals, std_spread_ma'
# np.savetxt(stata_files_path + r'\master_pair_pd_cont.txt', master_pair_price_dispersion_cont_print, fmt = '%.5f', delimiter = ',', header = header_master_pair_pd_cont)

"""
# ALTERNATIVE IF NAN NOT AUTHORIZED
max_pair_distance = 5
matrix_pair_pd_cont = np.array([pd_tuple for pd_tuple in master_pair_price_dispersion_cont if pd_tuple[1] < max_pair_distance])
# col 1: distance, col 3: rank reversals, col 4: spread std
matrix_pair_pd_cont = np.array(np.vstack([matrix_pair_pd_cont[:,1], matrix_pair_pd_cont[:,3], matrix_pair_pd_cont[:,4]]), dtype = np.float64).T
matrix_pair_pd_cont = np.ma.masked_array(matrix_pair_pd_cont, np.isnan(matrix_pair_pd_cont))
matrix_pair_pd_cont = np.ma.compress_rows(matrix_pair_pd_cont)
distance = np.vstack([matrix_pair_pd_cont[:,0]]).T
rank_reversals = matrix_pair_pd_cont[:,1]
spread_std = matrix_pair_pd_cont[:,2]
print sm.OLS(rank_reversals, sm.add_constant(distance)).fit().summary()
print sm.OLS(rank_reversals, sm.add_constant(distance)).fit().summary()
"""

# 3/ E/ REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE WITH CLEANED PRICES

master_market_price_dispersion_cont = get_master_market_price_dispersion(cross_distances_dict, list_competitor_lists, master_price_gas_stations, 5)

matrix_master_pd_cont = []
for market in master_market_price_dispersion_cont:
  array_nb_competitors = np.ones(len(market[2])) * market[1]
  matrix_master_pd_cont.append(np.vstack([array_nb_competitors, period_mean_prices, market[2:]]).T)
matrix_master_pd_cont = np.vstack(matrix_master_pd_cont)
# header_master_market_pd = 'nb_competitors, mean_period_price, std_price, coeff_var_price, range_price, gain_from_search'
# np.savetxt(stata_files_path + r'\master_market_pd_cont_5.txt', matrix_master_pd_cont, fmt = '%.5f', delimiter = ',', header = header_master_market_pd)

nb_competitors = np.vstack([matrix_master_pd_cont[:,0]]).T
nb_competitors_and_price = np.vstack([matrix_master_pd_cont[:,0], matrix_master_pd_cont[:,1]]).T
std_prices = matrix_master_pd_cont[:,2]
coeff_var_prices = matrix_master_pd_cont[:,3]
range_prices = matrix_master_pd_cont[:,4]
gain_search = matrix_master_pd_cont[:,5]
print 'REGRESSIONS OF PAIR PRICE DISPERSION ON DISTANCE (CLEANED PRICES)'
print sm.OLS(std_prices, sm.add_constant(nb_competitors), missing = "drop").fit().summary(yname='std_prices', xname = ['constant', 'nb_competitors'])
print sm.OLS(std_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit().summary(yname='std_prices', xname = ['constant', 'nb_competitors', 'price'])
print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors), missing = "drop").fit().summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors'])
print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit().summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors', 'price'])
print sm.OLS(range_prices, sm.add_constant(nb_competitors), missing = "drop").fit().summary(yname='range_prices', xname = ['constant', 'nb_competitors'])
print sm.OLS(range_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit().summary(yname='range_prices', xname = ['constant', 'nb_competitors', 'price'])
print sm.OLS(gain_search, sm.add_constant(nb_competitors), missing = "drop").fit().summary(yname='gain_search', xname = ['constant', 'nb_competitors'])
print sm.OLS(gain_search, sm.add_constant(nb_competitors_and_price), missing = "drop").fit().summary(yname='gain_search', xname = ['constant', 'nb_competitors', 'price'])

"""
matrix_master_pd_cont = []
for market in master_market_price_dispersion_cont:
  array_nb_competitors = np.ones(len(market[2])) * market[1]
  temp_matrix_master_pd_cont = np.vstack([array_nb_competitors, period_mean_prices, market[2:]])
  if np.all(~np.isnan(temp_matrix_master_pd_cont)):
    matrix_master_pd_cont.append(temp_matrix_master_pd_cont.T)
matrix_master_pd_cont = np.vstack(matrix_master_pd_cont)
nb_competitors = np.vstack([matrix_master_pd_cont[:,0]]).T
prices_and_nb_competitors = np.vstack([matrix_master_pd_cont[:,0], matrix_master_pd_cont[:,1]]).T
std_prices = matrix_master_pd_cont[:,2]
coeff_var_prices = matrix_master_pd_cont[:,3]
range_prices = matrix_master_pd_cont[:,4]
gain_search = matrix_master_pd_cont[:,5]
print sm.OLS(std_prices, sm.add_constant(nb_competitors)).fit().summary()
print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors)).fit().summary()
print sm.OLS(range_prices, sm.add_constant(nb_competitors)).fit().summary()
print sm.OLS(gain_search, sm.add_constant(nb_competitors)).fit().summary()
print sm.OLS(std_prices, sm.add_constant(prices_and_nb_competitors)).fit().summary()
print sm.OLS(coeff_var_prices, sm.add_constant(prices_and_nb_competitors)).fit().summary()
print sm.OLS(range_prices, sm.add_constant(prices_and_nb_competitors)).fit().summary()
print sm.OLS(gain_search, sm.add_constant(prices_and_nb_competitors)).fit().summary()
"""

# 4/ CLEANING PRICES IN PYTHON

list_temp_ids = []
list_temp_periods = []
list_temp_brands = []
for i, id in enumerate(master_price_gas_stations['list_ids']):
  price_array = master_price_gas_stations['list_indiv_prices'][i]
  list_temp_ids.append([id for i in range(len(price_array))])
  list_temp_periods.append([i for i in range(len(price_array))])
  brand = dico_brands[get_str_no_accent(master_price_gas_stations['dict_general_info'][id]['brand_station'][0][0]).upper()][1]
  list_temp_brands.append([brand for i in range(len(price_array))])
array_ids = np.hstack(list_temp_ids).T
array_brands = np.hstack(list_temp_brands).T
array_prices = np.hstack(master_price_gas_stations['list_indiv_prices']).T
# master_array_test = np.vstack([array_brands, array_prices]).T

"""
# header_master_long = 'id, period, price, brand'
# np.savetxt(r'C:\Users\etna\Desktop\Stata_np_files\master_long.txt', master_long, fmt = '%s', delimiter = ',', header = header_master_long)

# ############################
# For more general regressions
# ############################

# Dummies for period fixed effect
nb_individuals = 5
nb_periods = 254
big_identity_matrix = np.vstack([np.matrix(np.identity(nb_periods, dtype = np.int32)) for i in range(0,nb_individuals)])[:,:-1]

# Dummies for characteristic fixed effect
# First with nb_periods considered as 1
list_categories = []
nb_categories = len(list_categories)
categories_zero_matrix = np.matrix(np.zeros((nb_individuals, nb_categories)))

for category in list_categories:
  for indivividual in list individuals:
    if .... [individual][category]

# Continuous dependent variable
# With nb periods considered as 1: just copy value for each individual
# Then duplicate for each indiv by nb of periods
"""