#!/usr/bin/python
# -*- coding: utf-8 -*-

import math
import itertools
import numpy as np
import scipy
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import patsy
import copy
import random
from generic_master_price import *

# COMPUTATION OF CROSS DISTANCES

def compute_distance(coordinates_A, coordinates_B):
  d_lat = math.radians(float(coordinates_B[0]) - float(coordinates_A[0]))
  d_lon = math.radians(float(coordinates_B[1]) - float(coordinates_A[1]))
  lat_1 = math.radians(float(coordinates_A[0]))
  lat_2 = math.radians(float(coordinates_B[0]))
  a = math.sin(d_lat/2.0) * math.sin(d_lat/2.0) + \
        math.sin(d_lon/2.0) * math.sin(d_lon/2.0) * math.cos(lat_1) * math.cos(lat_2)
  c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
  distance = 6371 * c
  return round(distance, 2)

def get_ls_ls_cross_distances(ls_gps):
  # Size can be lower if only half the matrix is returned
  ls_ls_cross_distances = [[np.nan for gps in ls_gps] for gps in ls_gps]
  for i, gps_i in enumerate(ls_gps):
    for j, gps_j in enumerate(ls_gps[i+1:], start = i+1):
      if gps_i and gps_j:
        distance_i_j = compute_distance(gps_i, gps_j)
        ls_ls_cross_distances[i][j] = distance_i_j
        ls_ls_cross_distances[j][i] = distance_i_j
  return ls_ls_cross_distances

# ANALYIS OF PRICE CHANGES

def get_station_price_change_frequency(indiv_ind, master_np_prices):
  """ DEPRECATED? """
  ar_chges = np.hstack([np.array([np.nan]), master_np_prices[indiv_ind,1:] - master_np_prices[indiv_ind,:-1]])
  nb_same_price = ((ar_chges == 0)).sum()
  nb_decrease = ((ar_chges < 0)).sum()
  nb_increase = ((ar_chges > 0)).sum()
  avg_decrease = scipy.stats.nanmean(ar_chges[ar_chges < 0])
  avg_increase = scipy.stats.nanmean(ar_chges[ar_chges > 0])
  return [nb_same_price, nb_decrease, nb_increase, avg_decrease, avg_increase]

def get_ls_price_change_frequency(master_np_prices):
  """ DEPRECATED? """
  for indiv_ind in range(len(master_np_prices)):
    ls_price_change_frequency.append(get_station_price_change_frequency(indiv_ind, master_np_prices))
  return ls_price_change_frequency

def get_ls_price_changes_vs_competitors(ls_ls_competitors, master_price, series):
  """
  Study price changes vs. competitors
  
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
  ls_ls_result = []
  for indiv_ind, ls_competitors in enumerate(list_list_competitors):
    ls_results = []
    if ls_competitors:
      ls_prices_1 = master_price[series][indiv_ind]
      ar_price_changes_1 = np.array(ls_prices_1[1:], dtype = np.float32) - \
                                      np.array(ls_prices_1[:-1], dtype = np.float32)
      ar_price_changes_1_ma = np.ma.masked_array(ar_price_changes_1, np.isnan(ar_price_changes_1))
      nb_chges_1 = ((ar_price_changes_1_ma != 0)).sum()
      ls_results.append(nb_chges_1)
      for competitor_id, distance in ls_competitors:
        competitor_ind = master_price['ids'].index(competitor_id)
        ls_prices_2 = master_price[series][competitor_ind]
        ar_price_changes_2 = np.array(ls_prices_2[1:], dtype = np.float32) - \
                                        np.array(ls_prices_2[:-1], dtype = np.float32)
        ar_price_changes_2_ma = np.ma.masked_array(ar_price_changes_2, np.isnan(ar_price_changes_2))
        nb_chges_2 = ((price_changes_2_ma != 0)).sum()
        # count changes at firm 1 with firm 2 also changing
        mask_2 = ar_price_changes_2 == 0 #boolean with True if change at firm 2/
        mask_2_c = ar_price_changes_2 != 0 #boolean with False (display) if change at firm 2
        ar_price_changes_1_ma_a = np.ma.masked_array(ar_price_changes_1_ma, mask = mask_2)
        nb_chges_1_if_2_a = ((ar_price_changes_1_ma_a != 0)).sum()
        # count changes at firm 1 with firm 2 changing the day before
        mask_2 = np.append(np.array(np.nan), ar_price_changes_2[:-1]) == 0 #boolean with True if change at firm 2/
        ar_price_changes_1_ma_h = np.ma.masked_array(ar_price_changes_1_ma, mask = mask_2)
        ar_price_changes_1_ma_h = np.ma.masked_array(ar_price_changes_1_ma_h, mask = mask_2_c)
        nb_chges_1_if_2_h = ((ar_price_changes_1_ma_h != 0)).sum()
        # count changes at firm 1 with firm 2 changing the day after
        mask_2 = np.append(ar_price_changes_2[1:], np.array(np.nan)) == 0 #boolean with True if change at firm 2/
        ar_price_changes_1_ma_d = np.ma.masked_array(ar_price_changes_1_ma, mask = mask_2)
        ar_price_changes_1_ma_d = np.ma.masked_array(ar_price_changes_1_ma_d, mask = mask_2_c)
        nb_chges_1_if_2_d = ((ar_price_changes_1_ma_d != 0)).sum()
        ls_results.append((competitor_id,
                           distance,
                           nb_chges_2, nb_chges_1_if_2_a, nb_chges_1_if_2_h, nb_chges_1_if_2_d))
    ls_ls_results.append(ls_results)
  return ls_ls_results

# ANALYSIS OF PAIR PRICE DISPERSION

def get_pair_price_dispersion(id_1, id_2, master_price, series):
  price_array_1 = np.array(master_price[series][master_price['ids'].index(id_1)], dtype = np.float32)
  price_array_2 = np.array(master_price[series][master_price['ids'].index(id_2)], dtype = np.float32)
  spread = price_array_1 - price_array_2
  duration = (~np.isnan(spread)).sum()
  avg_abs_spread = scipy.stats.nanmean(np.abs(spread))
  avg_spread = scipy.stats.nanmean(spread)
  std_spread = scipy.stats.nanstd(spread)
  b_cheaper = (spread < 0).sum()
  a_cheaper = (spread > 0).sum()
  rank_reversal = np.min([np.float32(b_cheaper)/duration, np.float32(a_cheaper)/duration])
  if b_cheaper > a_cheaper:
    ar_rank_reversal = np.where(spread <= 0, 0, spread)
  else:
    ar_rank_reversal = np.where(spread >= 0, 0, spread)
  list_tuples_rr = []
  for group in itertools.groupby(iter(range(len(ar_rank_reversal))),\
                                  lambda x: ar_rank_reversal[x] if ~np.isnan(ar_rank_reversal[x]) else None):
    list_tuples_rr.append((group[0], list(group[1])))
  list_rr_durations = [len(tuple_rr[1]) for tuple_rr in list_tuples_rr if tuple_rr[0] and tuple_rr[0] != 0]
  return (duration, avg_abs_spread, avg_spread, std_spread, rank_reversal, ar_rank_reversal, spread, list_rr_durations)

def get_station_price_dispersion(indiv_id, ls_ls_competitors, master_price, series, km_bound):
  """ for an id: price dispersion stats with each competitor within a given nb of km """
  dict_results = {}
  for (competitor_id, distance) in ls_ls_competitors[master_price['ids'].index(indiv_id)]:
    if distance < km_bound:
      pair_pd_stats = get_pair_price_dispersion(indiv_id, competitor_id, master_price, series)
      dict_results.setdefault('ids', []).append(competitor_id)
      dict_results.setdefault('duration', []).append(pair_pd_stats[0])
      dict_results.setdefault('avg_abs_spread', []).append(pair_pd_stats[1])
      dict_results.setdefault('avg_spread', []).append(pair_pd_stats[2])
      dict_results.setdefault('std_spread', []).append(pair_pd_stats[3])
      dict_results.setdefault('rank_reversal', []).append(pair_pd_stats[4])
      dict_results.setdefault('ar_rank_reversal', []).append(pair_pd_stats[5])
      dict_results.setdefault('spread', []).append(pair_pd_stats[6])
      dict_results.setdefault('list_rr_durations', []).append(pair_pd_stats[7])
  return dict_results

def get_ls_pair_price_dispersion(ls_tuple_competitors, master_price, series, km_bound):
  """ 
  Price dispersion stats for each pair with distance smaller than a given bound
  TODO: add the average spread conditional on rank being reversed
  """
  ls_pair_price_dispersion = []
  ls_pbms = []
  for ((id_1, id_2), distance) in ls_tuple_competitors:
    if distance < km_bound:
      pair_pd_stats = get_pair_price_dispersion(id_1, id_2, master_price, series)
      pair_price_dispersion = ((id_1,id_2), # 0 id pair
                               distance, # 1 distance
                               pair_pd_stats[0], # 2 duration
                               pair_pd_stats[1], # 3 avg_abs_spread
                               pair_pd_stats[2], # 4 avg_spread
                               pair_pd_stats[3], # 5 std_spread
                               pair_pd_stats[4], # 6 rank_reversal
                               pair_pd_stats[5], # 7 ar_rank_reversal
                               pair_pd_stats[6], # 8 spread
                               pair_pd_stats[7]) # 9 rr_durations
      ls_pair_price_dispersion.append(pair_price_dispersion)
  return ls_pair_price_dispersion

# ANALYSIS OF MARKET PRICE DISPERSION

def get_ls_ls_distance_market_ids(master_price, ls_ls_competitors, km_bound):
  """
  Distance used to define markets
  ls_ls_competitors has same order as master price (necessary condition)
  ls_ls_competitors: list of (id, distance) for each competitor (within 10km)
  """
  ls_ls_distance_market_ids = []
  for indiv_ind, ls_competitors in enumerate(ls_ls_competitors):
    indiv_id = master_price['ids'][indiv_ind]
    if ls_competitors: # and indiv_id not in ls_rejected_ids:
      ls_distance_market_ids = [indiv_id]
      for id_competitor, distance_competitor in ls_competitors:
        if id_competitor in master_price['ids']: # and id_competitor not in ls_rejected_ids:
          if distance_competitor < km_bound:
            ls_distance_market_ids.append(id_competitor)
        else:
          print id_competitor, 'not in master_price => check'
      if len(ls_distance_market_ids) > 1:
        ls_ls_distance_market_ids.append(ls_distance_market_ids)
  return ls_ls_distance_market_ids

def get_ls_ls_distance_market_ids_restricted(master_price, ls_ls_competitors, km_bound):
  """
  Distance used to define markets
  ls_ls_competitors: list of (id, distance) for each competitor (within 10km)
  ls_ls_competitors has same order as master price
  If id in previous market: drop market 
  TODO: design better algorithm (max nb of stations such that keep) OR:
  TODO: add possibility to randomize (beware: ls_ls_competitors' order matters)
  ls_id_and_ls_competitors_random = copy.deepcopy()
  random.shuffle(ls_id_and_ls_competitors_random)
  """
  ls_ls_distance_market_ids = []
  ls_ids_covered = []
  for indiv_ind, ls_competitors in enumerate(ls_ls_competitors):
    indiv_id = master_price['ids'][indiv_ind]
    if ls_competitors:
      ls_distance_market_ids = [indiv_id]
      for competitor_id, distance in ls_competitors:
        if competitor_id in master_price['ids']:
          if distance < km_bound:
            ls_distance_market_ids.append(competitor_id)
        else:
          print competitor_id, 'not in master_price => check'
      if (len(ls_distance_market_ids) > 1) and\
         (all(indiv_id not in ls_ids_covered for indiv_id in ls_distance_market_ids)):
        ls_ls_distance_market_ids.append(ls_distance_market_ids)
        ls_ids_covered += ls_distance_market_ids
  return ls_ls_distance_market_ids
  
def get_ls_ls_market_price_dispersion(ls_ls_market_ids, master_price, series):
  # if numpy.version.version = '1.8' or above => switch from scipy to numpy
  # checks nb of prices (non nan) per period (must be 2 prices at least)
  list_list_market_price_dispersion = []
  for ls_market_ids in ls_ls_market_ids:
    list_market_prices = [master_price[series][master_price['ids'].index(indiv_id)] for indiv_id in ls_market_ids]
    arr_market_prices = np.array(list_market_prices, dtype = np.float32)
    arr_nb_market_prices = (~np.isnan(arr_market_prices)).sum(0)
    arr_bool_enough_market_prices = np.where(arr_nb_market_prices > 1, 1, np.nan)
    arr_market_prices = arr_bool_enough_market_prices * arr_market_prices
    range_price_array = scipy.nanmax(arr_market_prices, 0) - scipy.nanmin(arr_market_prices, axis = 0)
    std_price_array = scipy.stats.nanstd(arr_market_prices, 0)
    coeff_var_price_array = scipy.stats.nanstd(arr_market_prices, 0) / scipy.stats.nanmean(arr_market_prices, 0)
    gain_from_search_array = scipy.stats.nanmean(arr_market_prices, 0) - scipy.nanmin(arr_market_prices, axis = 0)
    list_list_market_price_dispersion.append(( ls_market_ids,
                                               len(ls_market_ids),
                                               range_price_array,
                                               std_price_array,
                                               coeff_var_price_array,
                                               gain_from_search_array ))
  return list_list_market_price_dispersion
  
def get_fe_predicted_prices(list_ids, series):
  dict_panel_data_master_temp = {}
  for indiv_id in list_ids:
    indiv_ind = master_price['ids'].index(id)
    list_station_prices = master_price[series][indiv_ind]
    list_station_brands = [dict_brands[get_str_no_accent_up(brand)][1] if brand else brand\
                            for brand in get_field_as_list(id, 'brand', master_price)]
    dict_station = {'price' : np.array(list_station_prices, dtype = np.float32),
                    'brand' : np.array(list_station_brands),
                    'id' : indiv_id}
    dict_panel_data_master_temp[indiv_id] = pd.DataFrame(dict_station, index = master_price['dates'])
  pd_pd_master_temp = pd.Panel(dict_panel_data_master_temp)
  pd_pd_master_temp = pd_pd_master_temp.transpose('minor', 'items', 'major')
  pd_mi_master_temp = pd_pd_master_temp.to_frame(filter_observations=False)
  pd_mi_master_temp['price'] = pd_mi_master_temp['price'].astype(np.float32)
  pd_mi_master_temp['date'] = pd_mi_master_temp.index.get_level_values(1)
  res = smf.ols(formula = 'price ~ C(id) + C(date)', data = pd_mi_master_temp).fit()
  pd_df_X = pd.DataFrame(pd_mi_master_temp[['id', 'date']], columns=["id", "date"])
  ar_y_prediction = res.predict(pd_df_X)
  # Need to cut ar_y_prediction in price arrays
  # Here: Assumes all have same lengths
  return np.reshape(ar_y_prediction, (len(list_ids), -1))

# DATA DISPLAY

def print_dict_stat_des(dict_stat_des):
  for key, content in dict_stat_des.iteritems():
    print key, len(content)

def get_plot_prices(list_of_ids, master_price, series, path_save=None):
  list_list_prices = []
  for some_id in list_of_ids:
    list_list_prices.append(master_price[series][master_price['ids'].index(some_id)])
  pd_df_temp = pd.DataFrame(zip(*list_list_prices), index=master_price['dates'], columns=list_of_ids, dtype=np.float32)
  plt.figure()
  pd_df_temp.plot()
  fig = plt.gcf()
  fig.set_size_inches(18.5,10.5)
  if path_save: 
    plt.savefig(path_save)
  else:
    plt.show()
  return

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
  return 

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  folder_source_brand = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'
  folder_built_graphs = r'\data_gasoline\data_built\data_graphs'
  
  master_price = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')
  master_info = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_info_diesel')
  
  dict_brands = dec_json(path_data + folder_source_brand + r'\dict_brands')
  
  ls_ls_competitors = dec_json(path_data + folder_built_master_json + r'\master_diesel\ls_ls_competitors')
  ls_tuple_competitors = dec_json(path_data + folder_built_master_json + r'\master_diesel\ls_tuple_competitors')
  
  series = 'diesel_price'
  km_bound = 5
  
  # ########################
  # AVERAGE PRICE PER PERIOD
  # ########################
  
  master_np_prices = np.array(master_price['diesel_price'], dtype = np.float32)
  matrix_np_prices_ma = np.ma.masked_array(master_np_prices, np.isnan(master_np_prices))
  ar_nb_valid_prices = np.ma.count(matrix_np_prices_ma, axis = 0) # would be safer to count nan..
  ar_period_mean_prices = np.mean(matrix_np_prices_ma, axis = 0)
  
  # ###########################
  # ANALYSIS OF PRICE CHANGES
  # ###########################
  
  import timeit
  print 'Starting price changes block'
  start_time = timeit.default_timer()
  
  # At station level: can be done in matrix with numpy (only duration cannot)
  station_price_chges = get_station_price_change_frequency(0, master_np_prices)
  # ls_price_change_frequency =  get_list_price_change_frequency(master_price, series)
  
  # ls_price_chges_competition = get_list_price_changes_vs_competitors(list_list_competitors, master_price, series)
  
  elapsed = timeit.default_timer() - start_time
  print elapsed
    
  # #########################
  # PRICE DISPERSION ANALYSIS
  # #########################
  
  print 'Starting price dispersion block'
  start_time = timeit.default_timer() 
  
  station_price_dispersion = get_station_price_dispersion('1500007',
                                                          ls_ls_competitors, 
                                                          master_price, 
                                                          series,
                                                          km_bound)
  
  ls_pair_price_dispersion = get_ls_pair_price_dispersion(ls_tuple_competitors,
                                                          master_price,
                                                          series,
                                                          km_bound)
                                                                
  # ls_ls_market_ids = get_ls_ls_distance_market_ids(master_price, ls_ls_competitors, km_bound)
  # ls_ls_market_price_dispersion = get_ls_ls_market_price_dispersion(ls_ls_market_ids, master_price, series)
  
  # ls_ls_market_ids_res = get_ls_ls_distance_market_ids_restricted(master_price, ls_ls_competitors, km_bound)
  # ls_lis_market_pd_res = get_ls_ls_market_price_dispersion(ls_ls_m_ids_res, master_price, series)
  
  # # get_plot_ls_arrays(ls_ls_market_price_dispersion[0][2:], ['range', 'std', 'cvar', 'gs'])
  
  elapsed = timeit.default_timer() - start_time
  print elapsed
  
  # INFO STATION DATAFRAME
  
  # TODO: keep all brands...
  ls_ls_info_pd_df = []
  for indiv_id, indiv_info in master_price['dict_info'].items():
    ls_brands = [x[0] for x in itertools.groupby([get_str_no_accent_up(brand[0]) for brand in indiv_info['brand']])]
    bo_brand_change = 0
    if len(ls_brands) > 1:
      bo_brand_change = 1
    if ls_brands:
      ls_info_pd_df = [indiv_id,
                      ls_brands[-1],
                      dict_brands[ls_brands[-1]][1],
                      dict_brands[ls_brands[-1]][2],
                      bo_brand_change]
    else:
      ls_info_pd_df = [indiv_id,
                      None,
                      None,
                      None,
                      bo_brand_change]
    ls_ls_info_pd_df.append(ls_info_pd_df)
  pd_df_info = pd.DataFrame(ls_ls_info_pd_df, columns = ['id', 'brand_a', 'brand_b', 'brand_type', 'brand_chge'])
  
  # PAIR PRICE DISPERSION DATAFRAME  
  
  # TODO: Check that no pbm with missing periods
  ls_columns = ['id_1',
                'id_2',
                'distance',
                'duration',
                'avg_abs_spread',
                'avg_spread',
                'std_spread',
                'rank_reversal',
                'nb_rank_reversals',
                'nb_rank_reversals_res']
  ls_ls_pair_pd_df = [list(row[0]) + list(row[1:7]) + [len(row[9])] + [len([x for x in row[9] if x > 1])]\
                        for row in ls_pair_price_dispersion]
  pd_df_pair_pd = pd.DataFrame(ls_ls_pair_pd_df, columns = ls_columns)
  
  pd_df_info = pd_df_info.rename(columns={'id': 'id_1'})
  pd_df_pair_pd = pd.merge(pd_df_pair_pd, pd_df_info, on='id_1')
  pd_df_info = pd_df_info.rename(columns={'id_1': 'id_2'})
  pd_df_pair_pd = pd.merge(pd_df_pair_pd, pd_df_info, on='id_2', suffixes=('_1', '_2'))
  
  # Need to add info: brand changes? same brand? brand? location?
  # Is it worth building another dataset with
  ls_bertrand_candidates_ixs = np.where((pd_df_pair_pd['avg_abs_spread']<0.01) &\
                                        (np.abs(pd_df_pair_pd['avg_spread'])<0.01) &\
                                        (pd_df_pair_pd['brand_a_1'] != pd_df_pair_pd['brand_a_2']))[0]
  
  ls_mixed_candidates_ixs = np.where((pd_df_pair_pd['rank_reversal']>0.4) &\
                                     (pd_df_pair_pd['nb_rank_reversals']>20) &\
                                     (pd_df_pair_pd['brand_a_1'] != pd_df_pair_pd['brand_a_2']))[0]
  
  ls_mixed_bertrand_ixs = [elt for elt in ls_bertrand_candidates_ixs if elt in ls_mixed_candidates_ixs]
  
  # Investigate close competitors
  
  pd_df_tough_competition = pd_df_pair_pd[(pd_df_pair_pd['avg_abs_spread'] < 0.01) &\
                                          (pd_df_pair_pd['rank_reversal'] >= 0.2)]
  ls_tup_ids_tough_competition = zip(pd_df_tough_competition['id_1'], pd_df_tough_competition['id_2'])
  # for indiv_id_1, indiv_id_2 in ls_tup_ids_tough_competition:
    # indiv_ind_1 = master_price['ids'].index(indiv_id_1)
    # indiv_ind_2 = master_price['ids'].index(indiv_id_2)
    # brand_1 = master_price['dict_info'][indiv_id_1]['brand'][0][0]
    # brand_2 = master_price['dict_info'][indiv_id_2]['brand'][0][0]
    # plt.clf()
    # fig = plt.figure() 
    # ax = fig.add_subplot(111)
    # ax.plot(ar_period_mean_prices)
    # ax.plot(matrix_np_prices_ma[indiv_ind_1,:], label = '%s %s' %(indiv_id_1,brand_1))
    # ax.plot(matrix_np_prices_ma[indiv_ind_2,:], label = '%s %s' %(indiv_id_2,brand_2))
    # ax.set_xlim([0,len(master_price['dates'])]) 
    # ax.set_ylim([1.2, 1.6])
    # handles, labels = ax.get_legend_handles_labels()
    # ax.legend(handles, labels)
    # plt.savefig(path_data + folder_built_graphs + r'\tough_competition\tough_%s-%s' %(indiv_id_1, indiv_id_2),
                # dpi = 500)
  
  pd_df_suspect =  pd_df_pair_pd[(pd_df_pair_pd['avg_abs_spread'] < 0.01) &\
                                 (pd_df_pair_pd['rank_reversal'] < 0.1) &\
                                 (pd_df_pair_pd['brand_a_1'] != pd_df_pair_pd['brand_a_2']) &\
                                 (pd_df_pair_pd['duration'] > 30)]
  ls_tup_ids_suspects = zip(pd_df_suspect['id_1'], pd_df_suspect['id_2'])
  # print pd_df_suspect[['id_1','id_2','brand_a_1', 'brand_a_2', 'rank_reversal', 'nb_rank_reversals', 'duration']].head(n=20).to_string()
  for indiv_id_1, indiv_id_2 in ls_tup_ids_suspects[0:50]:
    indiv_ind_1 = master_price['ids'].index(indiv_id_1)
    indiv_ind_2 = master_price['ids'].index(indiv_id_2)
    brand_1 = master_price['dict_info'][indiv_id_1]['brand'][0][0]
    brand_2 = master_price['dict_info'][indiv_id_2]['brand'][0][0]
    plt.clf()
    fig = plt.figure() 
    ax = fig.add_subplot(111)
    ax.plot(ar_period_mean_prices)
    ax.plot(matrix_np_prices_ma[indiv_ind_1,:], label = '%s %s' %(indiv_id_1,brand_1))
    ax.plot(matrix_np_prices_ma[indiv_ind_2,:], label = '%s %s' %(indiv_id_2,brand_2))
    ax.set_xlim([0,len(master_price['dates'])]) 
    ax.set_ylim([1.2, 1.6])
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles, labels)
    plt.savefig(path_data + folder_built_graphs + r'\suspect\tough_%s-%s' %(indiv_id_1, indiv_id_2),
                dpi = 300)
  
  pd_df_high_diff = pd_df_pair_pd[(pd_df_pair_pd['rank_reversal'] == 0) &\
                                  (pd_df_pair_pd['duration'] > 30)]
  # print pd_df_high_diff[['id_1','id_2','brand_a_1', 'brand_a_2', 'avg_spread', 'std_spread', 'duration']].head(n=30).to_string()
  
  pd_df_high_diff_comp = pd_df_pair_pd[(pd_df_pair_pd['rank_reversal'] == 0) &\
                                       (pd_df_pair_pd['std_spread'] < 0.01) &\
                                       (pd_df_pair_pd['duration'] > 30)]
  
  # 1/ MIXED STRATEGY EQUILIBRIUM COMPETITION CANDIDATES
  
  # A/ Based on zero average spread vs. zero average absolute spread => performs poorly (brand changes + rigid prices)
  # PROBLEM: Not very robust to deterministic changes: brand, pricing policy...
  
  # B/ Based on number of rank reversals essentially (seems more robust)
  # Check average distance and average (abs val) spread (1, 3, 4)
  # PROBLEM: May insist too much on frictions (need in-depth value/duration analysis...)
  
  # C/ Try to hit the right balance between frequency, length and rank reversal value (always the same?)
  
  # D/ Check with graphs...
  
  # for pair_xs in ls_mixed_bertrand_ixs[0:100]:
    # pair = [pd_df_pair_pd.ix[pair_xs]['id_1'], pd_df_pair_pd.ix[pair_xs]['id_2']]
    # path_save = path_data + r'\data_gasoline\data_built\data_graphs\mixed\Mixing_Pairs_%s.png' %''.join(pair)
    # get_plot_prices(pair, master_price, series, path_save)
  
  # 2/ BERTRAND COMPETITION CANDIDATES
  
  # A/ Based on low average spread in value and absolute value
  # Still a lot of rank reversal per gas station => see average average length
  
  # B/ Try to minimize rank reversals or at least those which have short duration (frictions!)
  # PROBLEM: CAN WE REALLY DISTINGUISH BERTRAND (?) WITH FRICTION VS. RANK REVERSALS (MIXED)
  
  # C/ Check with graphs...
  
  # for pair_xs in ls_bertrand_candidates_ixs[0:100]:
    # pair = [pd_df_pair_pd.ix[pair_xs]['id_1'], pd_df_pair_pd.ix[pair_xs]['id_2']]
    # path_save = path_data + r'\data_gasoline\data_built\data_graphs\bertrand\Bertrand_Pairs_%s.png' %''.join(pair[0])
    # get_plot_prices(pair[0], master_price, series, path_save)
  
  # 2/ PAIR PRICE DISPERSION: STATS DES
  
  # TODO: Check that no pbm with missing periods
  # Pairs with brand changes removed, not same brand, not highway (TODO)
  
  # pd_df_pair_pd = pd_df_pair_pd[(pd_df_pair_pd['brand_chge_1'] == 0) & (pd_df_pair_pd['brand_chge_2'] == 0)]
  pd_df_pair_pd = pd_df_pair_pd[(pd_df_pair_pd['brand_chge_1'] == 0) &\
                                (pd_df_pair_pd['brand_chge_2'] == 0) &\
                                (pd_df_pair_pd['duration'] > 30) &\
                                (pd_df_pair_pd['brand_a_1'] != pd_df_pair_pd['brand_a_2'])]
  
  print 'Number of pairs:', len(pd_df_pair_pd)
  print 'Percentage without rank reversal',\
          round(len(pd_df_pair_pd[pd_df_pair_pd['rank_reversal']==0])/float(len(pd_df_pair_pd)),3)*100
  
  pd_df_pair_pd_rr = pd_df_pair_pd[pd_df_pair_pd['nb_rank_reversals'] > 20]
  # TODO: exclude same brand stations (?)
  print 'Number of pairs with more than 20 rank reversal:', len(pd_df_pair_pd_rr)
  print 'Average average spread (more than 20 rank reversal):', pd_df_pair_pd_rr['avg_spread'].mean()
  print 'Average abs average spread (more than 20 rank reversal):', pd_df_pair_pd_rr['avg_abs_spread'].mean()
  
  # Check 0 distance... => graphs (mistake or not?)
  
  print pd_df_pair_pd[['id_1','id_2', 'brand_a_1', 'brand_a_2', 'nb_rank_reversals']]\
          [(pd_df_pair_pd['distance'] == 0)].to_string()
  
  pd_df_pair_pd['nb_rank_reversals_res'][(pd_df_pair_pd['distance'] > 0.0001) &\
                                         (pd_df_pair_pd['distance'] <= 0.5)].mean()
  
  pd_df_pair_pd['nb_rank_reversals_res'][(pd_df_pair_pd['distance'] > 0.5) &\
                                         (pd_df_pair_pd['distance'] < 1)].mean()
  
  pd_df_pair_pd['nb_rank_reversals_res'][(pd_df_pair_pd['distance'] > 0.5) &\
                                         (pd_df_pair_pd['distance'] < 3)].mean()
  
  # Percentage and avg value of spread cond on rank reversal of rank reversal per period
  ls_ls_spread_if_rank_reversal = [pair[7] for pair in ls_pair_price_dispersion]
  pd_df_spread_if_rr = pd.DataFrame(ls_ls_spread_if_rank_reversal)
  ls_percent_period_rr = []
  ls_avg_spread_period_rr = []
  for i in pd_df_spread_if_rr.columns:
    nb_period_rr = pd_df_spread_if_rr[i][(pd_df_spread_if_rr[i] > 0) | (pd_df_spread_if_rr[i] < 0)].count()
    nb_period_valid = pd_df_spread_if_rr[i].count()
    sum_period_rr = np.abs(pd_df_spread_if_rr[i]).sum()
    # TODO: check ! (did only quick debug... should not rule out 0 rank reversal for a period?)
    if nb_period_valid != 0:
      ls_percent_period_rr.append(float(nb_period_rr)/nb_period_valid)
    else:
      ls_percent_period_rr.append(np.nan)
    if nb_period_rr != 0:
      ls_avg_spread_period_rr.append(float(sum_period_rr)/nb_period_rr)
    else:
      ls_avg_spread_period_rr.append(np.nan)
  print '\Rank reversals per period (% of pairs):\n', np.around(ls_percent_period_rr, 1)
  print '\nAverage spread if rank reversal per period:\n', np.around(ls_avg_spread_period_rr, 3)
  
  # TODO: deal with classical temporal series problems...
  list_temp_a = [np.array(ls_percent_period_rr, dtype=np.float32),
                 np.array(ls_avg_spread_period_rr, dtype=np.float32),
                 ar_period_mean_prices.filled(np.nan)-1.3]
  list_temp_b = ['pct_rank_reversals', 'avg_reversal_spread', 'mean_price']
  pd_df_pair_rr = pd.DataFrame(np.array(list_temp_a, dtype=np.float32).T, columns = list_temp_b)
  pd_df_pair_rr['mean_price_d1'] = pd_df_pair_rr['mean_price'].diff()
  pd_df_pair_rr['mean_price_d1_abs'] = np.abs(pd_df_pair_rr['mean_price_d1'])
  pd_df_pair_rr[['mean_price', 'mean_price_d1','mean_price_d1_abs']].corr()
  print smf.ols(formula = 'pct_rank_reversals ~ mean_price_d1_abs', data = pd_df_pair_rr, missing = 'drop').fit().summary()
  pd_df_pair_rr['pct_rank_reversals_s1'] = pd_df_pair_rr['pct_rank_reversals'].shift(1)
  print smf.ols(formula = 'pct_rank_reversals ~ pct_rank_reversals_s1', data = pd_df_pair_rr, missing = 'drop').fit().summary()
  print smf.ols(formula = 'pct_rank_reversals ~ pct_rank_reversals_s1 + mean_price_d1_abs',\
                  data = pd_df_pair_rr, missing = 'drop').fit().summary()
  pd_df_pair_rr['pct_rank_reversals_d1'] = pd_df_pair_rr['pct_rank_reversals'].diff()
  print smf.ols(formula = 'pct_rank_reversals_d1 ~ mean_price_d1_abs', data = pd_df_pair_rr, missing = 'drop').fit().summary()
  # pd_df_pair_rr[['pct_rank_reversals','mean_price_d1']].plot()
  # plt.show()
  
  # TODO: look for asymmetry of rank reversal reaction to price!
  
  # pd_df_test_1 = pd.read_csv(path_data + folder_built_csv + r'/master_price_output.csv', dtype = str)
  # pd_df_test_1 = pd_df_test_1.set_index(['major', 'minor'])
  # pd_pd_prices = pd_df_test_1.to_panel()
  # pd_pd_prices['price'].mean(axis =0)
  # pd_pd_prices['price'][pd_pd_prices['brand_1'] == 'TOTAL_ACCESS'].mean(axis=0)
