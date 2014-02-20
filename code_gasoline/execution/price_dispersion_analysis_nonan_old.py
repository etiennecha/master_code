import os, sys
import json
import math
import numpy as np
import scipy
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import patsy
# import statsmodels.formula.api as smf
# import patsy
import copy
import random

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

# GENERIC

def get_id(rank, master_price):
  return master_price['ids'][rank]

def get_rank(id, master_price):
  return master_price['ids'].index(id)

def get_field_as_list(id, field, master_price):
  """
  Returns a list with field info per period: [info_per_1, info_per_2, info_per_3...]
  Reminder: Field info is a list of lists: [(info, period),(info, period)...]
  Starts with None if no info at beginning
  """
  field_index = 0
  if not master_price['dict_info'][id][field]:
    # fill with None if no info at all for the field
    list_result = [None for i in range(len(master_price['dates']))]
  else:
    period_index = master_price['dict_info'][id][field][field_index][1]
    # initiate list_result, fill with None if no info at beginning
    if period_index == 0:
      list_result = []
    else:
      list_result = [None for i in range(period_index)]
    # fill list_results with relevant field info
    while period_index < len(master_price['dates']):
      if field_index < len(master_price['dict_info'][id][field]) - 1:
        # before the last change: compare periods
        if period_index < master_price['dict_info'][id][field][field_index + 1][1]:
          list_result.append(master_price['dict_info'][id][field][field_index][0])
        else:
          field_index += 1
          list_result.append(master_price['dict_info'][id][field][field_index][0])
      else:
        # after the last change: fill with last info given
        list_result.append(master_price['dict_info'][id][field][-1][0])
      period_index += 1
  return list_result

def get_id_list_field_results(id, field, master_price):
  """
  DEPRECATED: anticipates on first info given if no info at beginning
  Returns a list with field info per period: [info_per_1, info_per_2, info_per_3...]
  Reminder: Field info is a list of lists: [(info, period),(info, period)...]
  """
  j = 0
  field_info = master_price['dict_info'][id][field]
  field_info_length = len(master_price['dates'])
  list_result = []
  for i in range(field_info_length):
    if j < len(field_info) - 1:
      if field_info[j + 1][1] <= i:
        j += 1        
      list_result.append(field_info[j][0])
    else:
      while len(list_result) < field_info_length:
        if field_info[j]:
          list_result.append(field_info[j][0])
        else:
          list_result.append(None)
  return list_result

def get_str_no_accent(line):
  """Suppresses some accents/weird chars from a unicode str"""
  accents = {u'a': [u'à', u'ã', u'á', u'â', u'\xc2'],
             u'c': [u'ç', u'\xe7'],
             u'e': [u'é', u'è', u'ê', u'ë', u'É', u'\xca', u'\xc8', u'\xe8', u'\xe9', u'\xc9'],
             u'i': [u'î', u'ï', u'\xcf', u'\xce'],
             u'o': [u'ô', u'ö'],
             u'u': [u'ù', u'ü', u'û'],
             u' ': [u'\xb0'] }
  for (char, accented_chars) in accents.iteritems():
    for accented_char in accented_chars:
      line = line.replace(accented_char, char) #line.encode('latin-1').replace(accented_char, char)
  line = line.replace('&#039;',' ')
  return line.rstrip().lstrip()

def unique(list_of_items):
  """Keeps only unique elements in a list"""
  found = set()
  keep = []
  for item in list_of_items:
    if item not in found:
      found.add(item)
      keep.append(item)
  return keep

# DATA DISPLAY

def print_dict_stat_des(dict_stat_des):
  for key, content in dict_stat_des.iteritems():
    print key, len(content)

def print_list_of_lists(list_of_lists, nb_columns):
  list_of_list_groups = [list_of_lists[i:i+nb_columns] for i\
                          in range(0, len(list_of_lists), nb_columns)]
  for list_items in list_of_list_groups:
    tuple_lists = zip(*list_items)
    col_width = max(len(item) for row\
                      in tuple_lists for item in row if item is not None) + 2
    for row in tuple_lists:
      row = tuple('.' if x is None else x for x in row)
      print "".join(item.ljust(col_width) for item in row)
    print '-' * 100

def print_list_of_lists_from_ranks(list_of_ranks, master_price, series, nb_columns):
  list_of_id_groups = [list_of_ranks[i:i + nb_columns] for i\
                        in range(0, len(list_of_ranks), nb_columns)]
  list_of_lists = [master_price[series][i] for i in list_of_ranks]
  list_of_list_groups = [list_of_lists[i:i + nb_columns] for i\
                          in range(0, len(list_of_lists), nb_columns)]
  for k in range(len(list_of_list_groups)):
    id_list = list_of_id_groups[k]
    col_width_1 = max(len(str(id)) for id in id_list) + 2
    tuple_lists = zip(*list_of_list_groups[k])
    col_width_2 = max(len(str(item)) for row\
                        in tuple_lists for item in row if item is not None) + 2
    col_width = max(col_width_1, col_width_2)
    print "".join(str(item).rjust(col_width) for item in id_list)
    for row in tuple_lists:
      row = tuple('.' if x is None else x for x in row)
      print "".join(str(item).rjust(col_width) for item in row)
    print '-' * 100

def get_plot_prices(list_of_ranks, master_price, series):
  # legend very ad hoc right now...
  plt.figure()
  for rank in list_of_ranks:
    price_array = np.array(master_price[series][rank])
    price_array_ma = np.ma.masked_array(price_array, np.isnan(price_array))
    axis = np.array([i for i in range(len(master_price[series][rank]))])
    plt.plot(axis, price_array_ma, label='%s%s' %(get_id(rank, master_price), \
                               master_price['dict_info'][get_id(rank, master_price)]['brand_station'][0][0]))
    plt.legend(loc = 4)
  plt.show()

def get_plot_list_arrays(list_price_arrays, list_labels = None):
  plt.figure()
  for price_index, price_array in enumerate(list_price_arrays):
    axis = np.array([i for i in range(len(price_array))])
    if list_labels:
      plt.plot(axis, price_array, label=list_labels[price_index])
    else:
      plt.plot(axis, price_array, label='')
    plt.legend(loc = 4)
  plt.show()

# PRICE CHANGE VALUE AND FREQUENCY ANALYSIS FUNCTIONS

def get_station_price_change_frequency(id_1, master_price, series):
  """
  for an id: price change frequency and value stats
  #TODO: add duration (how?)
  #TODO: not accurate if there np.nan between valid prices => replace np.nan just for this
  # http://stackoverflow.com/questions/6518811/interpolate-nan-values-in-a-numpy-array not what I want though
  """
  list_prices = master_price[series][get_rank(id_1, master_price)]
  price_array_today = np.array(list_prices[:-1], dtype = np.float32)
  price_array_tomorrow = np.array(list_prices[1:], dtype = np.float32)
  changes = price_array_tomorrow - price_array_today
  nb_same_price = ((np.float32(0) == changes)).sum()
  nb_decrease = ((np.float32(0) > changes)).sum()
  nb_increase = ((np.float32(0) < changes)).sum()
  avg_decrease = np.mean(changes[np.float32(0) > changes])
  avg_increase = np.mean(changes[np.float32(0) < changes])
  return [id_1, nb_same_price, nb_decrease, nb_increase, avg_decrease, avg_increase]

def get_master_price_change_frequency(master_price, series):
  """ for all ids in master: price change frequencies and values stats """
  list_price_change_frequency = []
  for id in master_price['ids']:
    list_price_change_frequency.append(get_station_price_change_frequency(id, master_price, series))
  return list_price_change_frequency

def get_master_price_changes_vs_competitors(cross_distances_dict, list_competitor_lists, master_price, series):
  master_result = []
  # Reminder: master_price_gas_stations['list_ids'] is cross_distances_dict['list_ids'] hence same index
  for station_index, station_id in enumerate(cross_distances_dict['list_ids']):
    list_result = []
    if list_competitor_lists[station_index]:
      list_prices_1 = master_price[series][station_index]
      price_changes_1 = np.array(list_prices_1[1:], dtype = np.float32) - \
                                    np.array(list_prices_1[:-1], dtype = np.float32)
      price_changes_1_ma = np.ma.masked_array(price_changes_1, np.isnan(price_changes_1))
      nb_chges_1 = ((np.float32(0) != price_changes_1_ma)).sum()
      list_result.append(nb_chges_1)
      for (competitor_id, distance) in list_competitor_lists[station_index]:
        competitor_index = get_rank(competitor_id, master_price)
        list_prices_2 = master_price[series][competitor_index]
        price_changes_2 = np.array(list_prices_2[1:], dtype = np.float32) - \
                                          np.array(list_prices_2[:-1], dtype = np.float32)
        price_changes_2_ma = np.ma.masked_array(price_changes_2, np.isnan(price_changes_2))
        nb_chges_2 = ((np.float32(0) != price_changes_2_ma)).sum()
        # count changes at firm 1 with firm 2 also changing
        mask_2 = price_changes_2 == 0 #boolean with True if change at firm 2/
        mask_2_c = price_changes_2 != 0 #boolean with False (display) if change at firm 2
        price_changes_1_ma_a = np.ma.masked_array(price_changes_1_ma, mask = mask_2)
        nb_chges_1_if_2_a = ((np.float32(0) != price_changes_1_ma_a)).sum()
        # count changes at firm 1 with firm 2 changing the day before
        mask_2 = np.append(np.array(np.nan), price_changes_2[:-1]) == 0 #boolean with True if change at firm 2/
        price_changes_1_ma_h = np.ma.masked_array(price_changes_1_ma, mask = mask_2)
        price_changes_1_ma_h = np.ma.masked_array(price_changes_1_ma_h, mask = mask_2_c)
        nb_chges_1_if_2_h = ((np.float32(0) != price_changes_1_ma_h)).sum()  
        # count changes at firm 1 with firm 2 changing the day after
        mask_2 = np.append(price_changes_2[1:], np.array(np.nan)) == 0 #boolean with True if change at firm 2/
        price_changes_1_ma_d = np.ma.masked_array(price_changes_1_ma, mask = mask_2)
        price_changes_1_ma_d = np.ma.masked_array(price_changes_1_ma_d, mask = mask_2_c)
        nb_chges_1_if_2_d = ((np.float32(0) != price_changes_1_ma_d)).sum()
        list_result.append((competitor_id, nb_chges_2, nb_chges_1_if_2_a, nb_chges_1_if_2_h, nb_chges_1_if_2_d))
    master_result.append(list_result)
  """
  prices_1 = [0, 0, 2, 2, 3, 0, 0, 0, 0, 2, 3, 4]
  prices_2 = [0, 0, 0, 2, 3, 2, 0, 0, 2, 2, 3, 5]
  price_changes_1 = np.array(prices_1[1:]) - np.array(prices_1[:-1])
  price_changes_2 = np.array(prices_2[1:]) - np.array(prices_2[:-1])
  # count changes at firm 1 with firm 2 also changing
  mask_2 = price_changes_2 == 0 #boolean with True (hide) if change at firm 2
  mask_2_c = price_changes_2 != 0 #boolean with False (display) if change at firm 2
  price_changes_1_ma_a = np.ma.masked_array(price_changes_1, mask = mask_2)
  nb_chges_1_if_2_a = ((np.float32(0) != price_changes_1_ma_a)).sum()
  # count changes at firm 1 with firm 2 changing the day before and not the same day
  mask_2 = np.append(np.array(np.nan), price_changes_2[:-1]) == 0 #boolean with True if change at firm 2
  price_changes_1_ma_h = np.ma.masked_array(price_changes_1, mask = mask_2)
  price_changes_1_ma_h = np.ma.masked_array(price_changes_1_ma_h, mask = mask_2_c)
  nb_chges_1_if_2_h = ((np.float32(0) != price_changes_1_ma_h)).sum()  
  # count changes at firm 1 with firm 2 changing the day after and not the same day
  mask_2 = np.append(price_changes_2[1:], np.array(np.nan)) == 0 #boolean with True if change at firm 2
  price_changes_1_ma_d = np.ma.masked_array(price_changes_1, mask = mask_2)
  price_changes_1_ma_d = np.ma.masked_array(price_changes_1_ma_d, mask = mask_2_c)
  nb_chges_1_if_2_d = ((np.float32(0) != price_changes_1_ma_d)).sum()
  """
  return master_result

# PRICE DISPERSION ANALYSIS FUNCTIONS

def get_station_price_dispersion(id_1, cross_distances_dict, list_competitor_lists, master_price, series, km_bound):
  """
  for an id: price dispersion stats with each competitor within a given nb of km
  """
  price_array_1 = np.array(master_price[series][get_rank(id_1, master_price)], dtype = np.float32)
  rank_competitor_list = cross_distances_dict['list_ids'].index(id_1)
  list_rank_reversals = []
  list_std_spread_ma = []
  list_spreads = []
  list_ids = [id_1]
  for (id_2, distance_competitor) in list_competitor_lists[rank_competitor_list]:
    if distance_competitor < km_bound:
      price_array_2 = np.array(master_price[series][get_rank(id_2, master_price)], dtype = np.float32)
      spread = np.around(price_array_1 - price_array_2, decimals = 3)
      spread_ma = np.ma.masked_array(spread, np.isnan(spread))
      b_cheaper = ((np.float32(0) > spread_ma)).sum()
      a_cheaper = ((np.float32(0) < spread_ma)).sum()
      duration = np.ma.count(spread_ma)
      rank_reversals = np.min([np.float32(b_cheaper)/duration, np.float32(a_cheaper)/duration])
      std_spread_ma = np.std(spread_ma)
      list_rank_reversals.append(rank_reversals)
      list_std_spread_ma.append(std_spread_ma)
      list_ids.append(id_2)
      list_spreads.append(spread)
  return [list_ids, list_rank_reversals, list_std_spread_ma, list_spreads]

def get_master_pair_price_dispersion(list_competitor_pairs, master_price, series, km_bound):
  """
  price dispersion stats for each pair with distance smaller than a given bound
  """
  #TODO: add the average spread conditional on rank being reversed
  master_pair_price_dispersion = []
  list_pbms = []
  for ((id_1, id_2), distance) in list_competitor_pairs:
    if distance < km_bound:
      price_array_1 = np.array(master_price[series][get_rank(id_1, master_price)], dtype = np.float32)
      price_array_2 = np.array(master_price[series][get_rank(id_2, master_price)], dtype = np.float32)
      spread = np.around(price_array_1 - price_array_2, decimals = 3)
      spread_ma = np.ma.masked_array(spread, np.isnan(spread))
      b_cheaper = ((np.float32(0) > spread_ma)).sum()
      a_cheaper = ((np.float32(0) < spread_ma)).sum()
      if b_cheaper > a_cheaper:
        rank_reversal_ma = np.where(spread_ma <= 0, 0 , spread_ma)
      else:
        rank_reversal_ma = np.where(spread_ma >= 0, 0, spread_ma)
      duration = np.ma.count(spread_ma)
      rank_reversals = np.min([np.float32(b_cheaper)/duration, np.float32(a_cheaper)/duration])
      std_spread_ma = np.std(spread_ma)
      master_pair_price_dispersion.append(((id_1, id_2), distance, duration, \
                                            rank_reversals, std_spread_ma, spread_ma, rank_reversal_ma))
  return master_pair_price_dispersion

def get_rank_reversal_overview(master_pair_price_dispersion, min_rr_criterion):
  pair_rank_reversals = np.array([pair[6] for pair in master_pair_price_dispersion if pair[3] >= min_rr_criterion])
  list_rr_per = [((np.float32(0) != pair_rank_reversals[:,i])).sum() for i in range(len(pair_rank_reversals[0,:]))]
  print np.around(np.array(list_rr_per)/float(len(pair_rank_reversals)), 2)
  list_rrsv_per = [np.sum(np.abs(pair_rank_reversals[:,i]))/((np.float32(0) != pair_rank_reversals[:,i])).sum()\
                                                                       for i in range(len(pair_rank_reversals[0,:]))]
  return (pair_rank_reversals, list_rr_per, np.array(list_rr_per)/float(len(pair_rank_reversals)), list_rrsv_per)

def get_master_market_price_dispersion(list_ids, cross_distances_dict, list_competitor_lists, master_price, series, km_bound):
  """
  price dispersion stats for each market (i.e. around each gas station) with distance smaller than a given bound
  list_ids must contain only ids which are in cross_distances_dict['list_ids']
  they can be shuffled => random.shuffle(list_ids)
  """
  master_market_price_dispersion = []
  for id_1 in list_ids:
    rank_competitor_list = cross_distances_dict['list_ids'].index(id_1)
    if list_competitor_lists[rank_competitor_list]:
      price_array_1 = np.array(master_price[series][get_rank(id_1, master_price)], dtype = np.float32)
      price_array_1_ma = np.ma.masked_array(price_array_1, np.isnan(price_array_1))
      list_ids = [id_1]
      list_price_arrays = [price_array_1_ma]
      for (id_2, distance_competitor) in list_competitor_lists[rank_competitor_list]:
        if distance_competitor < km_bound:
          price_array_2 = np.array(master_price[series][get_rank(id_2, master_price)], dtype = np.float32)
          price_array_2_ma = np.ma.masked_array(price_array_2, np.isnan(price_array_2))
          list_price_arrays.append(price_array_2_ma)
          list_ids.append(id_2)
      std_price_array = np.std(list_price_arrays, axis = 0)
      coeff_var_price_array = np.std(list_price_arrays, axis = 0)/np.mean(list_price_arrays, axis = 0)
      range_price_array = np.max(list_price_arrays, axis = 0) - np.min(list_price_arrays, axis = 0)
      gain_from_search_array = np.mean(list_price_arrays, axis = 0) - np.min(list_price_arrays, axis = 0)
      master_market_price_dispersion.append((list_ids, len(list_ids), range_price_array, std_price_array, \
                                              coeff_var_price_array, gain_from_search_array))
  return master_market_price_dispersion
  
def get_master_market_price_dispersion_restricted(list_ids, cross_distances_dict, list_competitor_lists, master_price, series, km_bound):
  """
  price dispersion stats for each market (i.e. around each gas station) with distance smaller than a given bound
  list_ids must contain only ids which are in cross_distances_dict['list_ids']
  they can be shuffled => random.shuffle(list_ids)
  """
  master_market_price_dispersion = []
  list_ids_covered = []
  for id_1 in list_ids:
    rank_competitor_list = cross_distances_dict['list_ids'].index(id_1)
    if list_competitor_lists[rank_competitor_list]:
      # TODO: unfortunately it is None and not [] if no competitor => correct that
      list_ids_submarket = [id_1] + [comp[0] for comp in list_competitor_lists[rank_competitor_list]]
      if not any(id_temp in list_ids_covered for id_temp in list_ids_submarket):
        # competitor ids: [comp[0] for comp in list_competitor_lists[rank_competitor_list]]
        # check that no gas station ever drawn before... else drop
        price_array_1 = np.array(master_price[series][get_rank(id_1, master_price)], dtype = np.float32)
        price_array_1_ma = np.ma.masked_array(price_array_1, np.isnan(price_array_1))
        list_ids = [id_1]
        list_price_arrays = [price_array_1_ma]
        for (id_2, distance_competitor) in list_competitor_lists[rank_competitor_list]:
          if distance_competitor < km_bound:
            price_array_2 = np.array(master_price[series][get_rank(id_2, master_price)], dtype = np.float32)
            price_array_2_ma = np.ma.masked_array(price_array_2, np.isnan(price_array_2))
            list_price_arrays.append(price_array_2_ma)
            list_ids.append(id_2)
        if len(list_ids) > 1:
          """
          # np.nan contaminates mean if used on list of arrays (with axis = 0)
          range_price_array = np.max(list_price_arrays, axis = 0) - np.min(list_price_arrays, axis = 0)
          std_price_array = np.std(list_price_arrays, axis = 0)
          coeff_var_price_array = np.std(list_price_arrays, axis = 0)/np.mean(list_price_arrays, axis = 0)
          gain_from_search_array = np.mean(list_price_arrays, axis = 0) - np.min(list_price_arrays, axis = 0)
          """
          # np.nan does not contaminate... so if 2 stations and one is np.nan: no price dispersion...
          range_price_array = scipy.nanmax(list_price_arrays, axis = 0) - scipy.nanmin(list_price_arrays, axis = 0)
          std_price_array = scipy.stats.nanstd(list_price_arrays, axis = 0)
          coeff_var_price_array = scipy.stats.nanstd(list_price_arrays, axis = 0) / \
                                                      scipy.stats.nanmean(list_price_arrays, axis = 0)
          gain_from_search_array = scipy.stats.nanmean(list_price_arrays, axis = 0) - \
                                                        scipy.nanmin(list_price_arrays, axis = 0)
          master_market_price_dispersion.append((list_ids, len(list_ids), range_price_array, \
                                                  std_price_array, coeff_var_price_array, gain_from_search_array))
          list_ids_covered += list_ids
  return master_market_price_dispersion

if __name__=="__main__":
  # path_data: data folder at different locations at CREST vs. HOME
  # could do the same for path_code if necessary (import etc).
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  # structure of the data folder should be the same
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline\master_diesel'
  folder_source_brand = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'

  # ###############
  # CODE EXECUTION
  # ###############

  master_price_gas_stations = dec_json(path_data + folder_built_master_json + r'\master_price_diesel')
  master_info_gas_stations = dec_json(path_data + folder_built_master_json + r'\master_info')
  cross_distances_dict = dec_json(path_data + folder_built_master_json + r'\cross_distances_dict')
  # cross_distances_matrix = np.load(path_data + folder_built_master_json + r'\cross_distances_matrix.npy')
  list_competitor_lists = dec_json(path_data + folder_built_master_json + r'\list_competitor_lists')
  list_competitor_pairs = dec_json(path_data + folder_built_master_json + r'\list_competitor_pairs')

  # AVERAGE PRICE PER PERIOD

  master_np_prices = np.array(master_price_gas_stations['diesel_price'], dtype = np.float32)
  matrix_np_prices_ma = np.ma.masked_array(master_np_prices, np.isnan(master_np_prices))
  period_mean_prices = np.mean(matrix_np_prices_ma, axis = 0)
  period_mean_prices = period_mean_prices.filled(np.nan)
  # get_plot_list_arrays([period_mean_prices, matrix_np_prices_ma[1,:], matrix_np_prices_ma[2,:], matrix_np_prices_ma[4,:]])
  
  # ANALYSIS OF PRICE CHANGE FREQUENCIES AND VALUES
  
  """
  station_price_chges = get_station_price_change_frequency('1500007', master_price_gas_stations,\
                                                                       'diesel_price')

  master_station_price_chges = get_master_price_change_frequency(master_price_gas_stations,\
                                                                  'diesel_price')

  master_chges_competition = get_master_price_changes_vs_competitors(cross_distances_dict,\
                                                                      list_competitor_lists,\
                                                                      master_price_gas_stations,\
                                                                      'diesel_price')
  
  master_np_prices_chges = master_np_prices[:,:-1] - master_np_prices[:,1:]
  matrix_np_prices_chges_ma = np.ma.masked_array(master_np_prices_chges, np.isnan(master_np_prices_chges))

  period_pos_chges = [matrix_np_prices_chges_ma[:,i][matrix_np_prices_chges_ma[:,i] > 0] for i in\
                                                      range(len(matrix_np_prices_chges_ma[0,:]))]
  period_nb_pos_chges = [len(array_chges) for array_chges in period_pos_chges]
  period_avg_pos_chge = np.around([np.mean(array_chges) for array_chges in period_pos_chges], 3)

  period_neg_chges = [matrix_np_prices_chges_ma[:,i][matrix_np_prices_chges_ma[:,i] < 0] for i in\
                                                      range(len(matrix_np_prices_chges_ma[0,:]))]
  period_nb_neg_chges = [len(array_chges) for array_chges in period_neg_chges]
  period_avg_neg_chge = np.around([np.mean(array_chges) for array_chges in period_neg_chges], 3)

  recap_nb_chges = np.vstack([period_nb_pos_chges, -np.array(period_nb_neg_chges)]).T # to see better on graph
  recap_avg_chge = np.vstack([period_avg_pos_chge, period_avg_neg_chge]).T

  all_chges = matrix_np_prices_chges_ma[matrix_np_prices_chges_ma != 0]
  n, bins, patches = plt.hist(all_chges, 50, normed=1, facecolor='g', alpha=0.75)

  plt.step([i for i in range(len(recap_avg_chge[0:250]))], recap_avg_chge[0:250])
  plt.show()
  plt.step([i for i in range(len(recap_nb_chges[0:250]))], recap_nb_chges[0:250]) 
  plt.show()
  """
  
  # PRICE DISPERSION ANALYSIS
  
  station_price_dispersion = get_station_price_dispersion('1500007',\
                                                          cross_distances_dict,\
                                                          list_competitor_lists,\
                                                          master_price_gas_stations,\
                                                          'diesel_price',\
                                                          5)
                                                          
  master_pair_price_dispersion = get_master_pair_price_dispersion(list_competitor_pairs,\
                                                                  master_price_gas_stations,\
                                                                  'diesel_price',\
                                                                  5)

  """
  master_pair_price_dispersion_active = [elt for elt in master_pair_price_dispersion \ 
                                          if tuple(set(elt[0])) in tuple_active_competitors]
  rank_reversals_active = [elt[3] for elt in master_pair_price_dispersion_active]
  hist, bins = np.histogram(rank_reversals_active,bins = 10)
  np.around(hist/float(len(rank_reversals_active)), 2)
  """
  master_market_price_dispersion = get_master_market_price_dispersion(cross_distances_dict['list_ids'],\
                                                                      cross_distances_dict,\
                                                                      list_competitor_lists,\
                                                                      master_price_gas_stations,\
                                                                      'diesel_price',\
                                                                      5)
                                                                      
  master_market_price_dispersion = [market for market in master_market_price_dispersion if market[1] > 1]
  # get_plot_list_arrays(master_market_price_dispersion[0][2:], ['range', 'std', 'cvar', 'gs'])
  """
  master_market_price_dispersion_st = get_master_market_price_dispersion_restricted(cross_distances_dict['list_ids'], \
                                         cross_distances_dict, list_competitor_lists, master_price_gas_stations, 5)
  master_market_price_dispersion_st = [market for market in master_market_price_dispersion_st if market[1] > 1]                                       
  list_ids_random = copy.deepcopy(cross_distances_dict['list_ids'])
  random.shuffle(list_ids_random)
  master_market_price_dispersion_str = get_master_market_price_dispersion_restricted(list_ids_random,\
                                        cross_distances_dict, list_competitor_lists, master_price_gas_stations, 5)
  master_market_price_dispersion_str = [market for market in master_market_price_dispersion_str if market[1] > 1]
  # get_plot_list_arrays(master_market_price_dispersion_st[0][2:], ['range', 'std', 'cvar', 'gs'])
  """
  
  # master_pair: percentage of rank reversal per period
  mat_pair_spread = np.array([pair[6] for pair in master_pair_price_dispersion])
  mat_pair_spread_ma = np.ma.masked_array(mat_pair_spread, np.isnan(mat_pair_spread))
  mat_pair_spread_abs = np.abs(mat_pair_spread)
  list_pair_period_rank_reversal_number = [((np.float32(0) < mat_pair_spread_abs[:, i])).sum()\
                                            for i in range(len(mat_pair_spread_abs[0, :]))]
  list_pair_period_total_number = [len(mat_pair_spread_abs[:, i][~np.isnan(mat_pair_spread_abs[:, i])])\
                                    for i in range(len(mat_pair_spread_abs[0, :]))]
  arr_pair_rank_reversal_percent = np.array(list_pair_period_rank_reversal_number, dtype = np.float32)/\
                                    np.array(list_pair_period_total_number, dtype = np.float32)
  print np.around(arr_pair_rank_reversal_percent, 2)
  
  # master_pair: avg value of spread under rank reversal
  list_pair_period_cum_rank_reversal_spread = [np.sum(mat_pair_spread_abs[:,i][~np.isnan(mat_pair_spread_abs[:, i])])\
                                                for i in range(len(mat_pair_spread_abs[0,:]))]
  arr_rank_reversal_avg_value = np.array(list_pair_period_cum_rank_reversal_spread) /\
                                  np.array(list_pair_period_rank_reversal_number)
  print np.around(arr_rank_reversal_avg_value, 3)
  
  # master pair: distance to average spread (between pair of stations) per period
  # Obvious pbm: distance to spread is higher when price high ?
  list_pair_period_spread_dist_to_avg = [mat_pair_spread[i,:] - np.mean(mat_pair_spread_ma[i,:])\
                                          for i in range(len(mat_pair_spread))]
  mat_pair_period_spread_dist_to_avg_abs = np.abs(np.array(list_pair_period_spread_dist_to_avg))
  mat_pair_period_spread_dist_to_avg_abs_ma =  np.ma.masked_array(mat_pair_period_spread_dist_to_avg_abs,\
                                                                    np.isnan(mat_pair_period_spread_dist_to_avg_abs))
  arr_pair_period_rel_cum_dist = np.sum(mat_pair_period_spread_dist_to_avg_abs_ma, axis = 0)/\
                                    np.array(list_pair_period_total_number)
  arr_pair_period_rel_cum_dist = arr_pair_period_rel_cum_dist.filled(np.nan)
  
  # master_pair: summary graphs
  """
  arr_period_mean_price_chge = np.hstack(([np.nan], period_mean_prices[1:]-period_mean_prices[:-1]))
  
  get_plot_list_arrays([arr_pair_period_rel_cum_dist, arr_period_mean_price_chge],\
                       ['per_rel_cum_dist_to_avg_spread', 'mean_price_chge'])
  
  get_plot_list_arrays([arr_pair_rank_reversal_percent, arr_rank_reversal_avg_value,\
                          period_mean_prices-1.3, arr_period_mean_price_chge],\
                       ['pct_rank_reversals', 'avg_reversal_spread',\
                       'mean_price', 'mean_price_chge'])
  """
                       
  # master_pair: correlations between price change and spread / rank reversals
  # TODO: with pd/sm
  
  # WITH NAN NOT AUTHORIZED (i.e. "old" version of statsmodels)
  
  # REGRESSION OF PAIR PRICE DISPERSION ON DISTANCE (NAN NOT AUTHORIZED)
  max_pair_distance = 5
  matrix_pair_pd = np.array([pd_tuple for pd_tuple in master_pair_price_dispersion if pd_tuple[1] < max_pair_distance])
  # col 1: distance, col 3: rank reversals, col 4: spread std
  matrix_pair_pd = np.array(np.vstack([matrix_pair_pd[:,1], matrix_pair_pd[:,3], matrix_pair_pd[:,4]]), dtype = np.float64).T
  matrix_pair_pd = np.ma.masked_array(matrix_pair_pd, np.isnan(matrix_pair_pd))
  matrix_pair_pd = np.ma.compress_rows(matrix_pair_pd)
  distance = np.vstack([matrix_pair_pd[:,0]]).T
  rank_reversals = matrix_pair_pd[:,1]
  spread_std = matrix_pair_pd[:,2]
  print '\n REGRESSIONS OF PAIR PRICE DISPERSION ON DISTANCE \n'
  print sm.OLS(rank_reversals, sm.add_constant(distance)).fit().summary(yname='rank_reversals', xname = ['constant', 'distance'])
  print sm.OLS(spread_std, sm.add_constant(distance)).fit().summary(yname='spread_std', xname = ['constant', 'distance'])
  # header_master_pair_pd = 'distance, rank_reversals, spread_std'
  # np.savetxt(path_data + folder_built_csv + r'\master_pair_pd.txt', matrix_pair_pd, fmt = '%.5f', delimiter = ',', header = header_master_pair_pd)

  # REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE (NAN NOT AUTHORIZED)
  matrix_master_pd = []
  for individual in master_market_price_dispersion:
    array_nb_competitors = np.ones(len(individual[2])) * individual[1]
    temp_matrix_master_pd = np.vstack([array_nb_competitors, period_mean_prices, individual[2:]])
    if np.all(~np.isnan(temp_matrix_master_pd)):
      matrix_master_pd.append(temp_matrix_master_pd.T)
  matrix_master_pd = np.vstack(matrix_master_pd)
  # matrix_master_pd = np.array(matrix_master_pd, dtype = np.float64)
  nb_competitors = np.vstack([matrix_master_pd[:,0]]).T
  nb_competitors_and_price = np.vstack([matrix_master_pd[:,0], matrix_master_pd[:,1]]).T
  range_prices = matrix_master_pd[:,2]
  std_prices = matrix_master_pd[:,3]
  coeff_var_prices = matrix_master_pd[:,4]
  gain_search = matrix_master_pd[:,5]
  print '\n REGRESSIONS OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE \n'
  print sm.OLS(std_prices, sm.add_constant(nb_competitors)).fit()\
                .summary(yname='std_prices', xname = ['constant', 'nb_competitors'])
  print sm.OLS(std_prices, sm.add_constant(nb_competitors_and_price)).fit()\
                .summary(yname='std_prices', xname = ['constant', 'nb_competitors', 'price'])
  print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors)).fit()\
                .summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors'])
  print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors_and_price)).fit()\
                .summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors', 'price'])
  print sm.OLS(range_prices, sm.add_constant(nb_competitors)).fit()\
                .summary(yname='range_prices', xname = ['constant', 'nb_competitors'])
  print sm.OLS(range_prices, sm.add_constant(nb_competitors_and_price)).fit()\
                .summary(yname='range_prices', xname = ['constant', 'nb_competitors', 'price'])
  print sm.OLS(gain_search, sm.add_constant(nb_competitors)).fit()\
                .summary(yname='gain_search', xname = ['constant', 'nb_competitors'])
  print sm.OLS(gain_search, sm.add_constant(nb_competitors_and_price)).fit()\
                .summary(yname='gain_search', xname = ['constant', 'nb_competitors', 'price'])
  # header_master_market_pd = 'nb_competitors, prices, std_prices, coeff_var_prices, range_prices, gain_search'
  # np.savetxt(path_data + folder_built_csv + r'\matrix_master_pd_5.txt', matrix_master_pd, fmt = '%.5f', delimiter = ',', header = header_master_market_pd)

  # CLEANING PRICES (NOW BRAND EFFECT ONLY, NAN NOT AUTHORIZED)
  dict_brands = dec_json(path_data + folder_source_brand + r'\dict_brands')
  for id, info in master_price_gas_stations['dict_general_info'].iteritems():
    if get_str_no_accent(info['brand_station'][0][0]).upper() not in dict_brands.keys():
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
    list_brands.append(dict_brands[get_str_no_accent(master_price_gas_stations['dict_general_info'][id]['brand_station'][0][0]).upper()][1])
  for brand in list_brands:
    list_coeffs.append(price_effect[brand])
  for coeff in list_coeffs:
    master_coeffs.append([coeff for i in range(len(master_price_gas_stations['diesel_price'][0]))])
  matrix_coeffs = np.array(master_coeffs, dtype = np.float64)
  matrix_price_cont = master_np_prices - matrix_coeffs
  master_price_gas_stations['diesel_price'] = matrix_price_cont.tolist()

  # REGRESSION OF PAIR PRICE DISPERSION ON DISTANCE WITH CLEANED PRICES
  master_pair_price_dispersion_cont = get_master_pair_price_dispersion(list_competitor_pairs, master_price_gas_stations, 5)
  max_pair_distance = 5
  matrix_pair_pd_cont = np.array([pd_tuple for pd_tuple in master_pair_price_dispersion_cont if pd_tuple[1] < max_pair_distance])
  # col 1: distance, col 3: rank reversals, col 4: spread std
  matrix_pair_pd_cont = np.array(np.vstack([matrix_pair_pd_cont[:,1], matrix_pair_pd_cont[:,3], matrix_pair_pd_cont[:,4]]), dtype = np.float64).T
  matrix_pair_pd_cont = np.ma.masked_array(matrix_pair_pd_cont, np.isnan(matrix_pair_pd_cont))
  matrix_pair_pd_cont = np.ma.compress_rows(matrix_pair_pd_cont)
  distance = np.vstack([matrix_pair_pd_cont[:,0]]).T
  rank_reversals = matrix_pair_pd_cont[:,1]
  spread_std = matrix_pair_pd_cont[:,2]
  print sm.OLS(rank_reversals, sm.add_constant(distance)).fit().summary(yname='rank_reversals', xname = ['constant', 'distance'])
  print sm.OLS(spread_std, sm.add_constant(distance)).fit().summary(yname='spread_std', xname = ['constant', 'distance'])

  # REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE WITH CLEANED PRICES (NAN NOT AUTHORIZED)
  master_market_price_dispersion_cont = get_master_market_price_dispersion(cross_distances_dict['list_ids'], cross_distances_dict, list_competitor_lists, master_price_gas_stations, 5)
  matrix_master_pd_cont = []
  for market in master_market_price_dispersion_cont:
    array_nb_competitors = np.ones(len(market[2])) * market[1]
    temp_matrix_master_pd_cont = np.vstack([array_nb_competitors, period_mean_prices, market[2:]])
    if np.all(~np.isnan(temp_matrix_master_pd_cont)):
      matrix_master_pd_cont.append(temp_matrix_master_pd_cont.T)
  matrix_master_pd_cont = np.vstack(matrix_master_pd_cont)
  nb_competitors = np.vstack([matrix_master_pd_cont[:,0]]).T
  nb_competitors_and_price = np.vstack([matrix_master_pd_cont[:,0], matrix_master_pd_cont[:,1]]).T
  range_prices = matrix_master_pd[:,2]
  std_prices = matrix_master_pd[:,3]
  coeff_var_prices = matrix_master_pd[:,4]
  gain_search = matrix_master_pd[:,5]
  print 'REGRESSIONS OF PAIR PRICE DISPERSION ON DISTANCE (CLEANED PRICES)'
  print sm.OLS(std_prices, sm.add_constant(nb_competitors)).fit()\
                .summary(yname='std_prices', xname = ['constant', 'nb_competitors'])
  print sm.OLS(std_prices, sm.add_constant(nb_competitors_and_price)).fit()\
                .summary(yname='std_prices', xname = ['constant', 'nb_competitors', 'price'])
  print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors)).fit()\
                .summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors'])
  print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors_and_price)).fit()\
                .summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors', 'price'])
  print sm.OLS(range_prices, sm.add_constant(nb_competitors)).fit()\
                .summary(yname='range_prices', xname = ['constant', 'nb_competitors'])
  print sm.OLS(range_prices, sm.add_constant(nb_competitors_and_price)).fit()\
                .summary(yname='range_prices', xname = ['constant', 'nb_competitors', 'price'])
  print sm.OLS(gain_search, sm.add_constant(nb_competitors)).fit()\
                .summary(yname='gain_search', xname = ['constant', 'nb_competitors'])
  print sm.OLS(gain_search, sm.add_constant(nb_competitors_and_price)).fit()\
                .summary(yname='gain_search', xname = ['constant', 'nb_competitors', 'price'])