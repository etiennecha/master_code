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
import itertools
from generic_master_price import *

zero_threshold = np.float64(1e-10)

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

def compute_distance_ar(ar_lat_A, ar_lng_A, ar_lat_B, ar_lng_B):
  d_lat = np.radians(ar_lat_B - ar_lat_A)
  d_lng = np.radians(ar_lng_B - ar_lng_A)
  lat_1 = np.radians(ar_lat_A)
  lat_2 = np.radians(ar_lat_B)
  ar_a = np.sin(d_lat/2.0) * np.sin(d_lat/2.0) + \
           np.sin(d_lng/2.0) * np.sin(d_lng/2.0) * np.cos(lat_1) * np.cos(lat_2)
  ar_c = 2 * np.arctan2(np.sqrt(ar_a), np.sqrt(1-ar_a))
  ar_distance = 6371 * ar_c
  return np.round(ar_distance, 2)

def get_ls_ls_cross_distances(ls_gps):
  # Size can be lowered by filling only half the matrix
  ls_ls_cross_distances = [[np.nan for gps in ls_gps] for gps in ls_gps]
  for i, gps_i in enumerate(ls_gps):
    for j, gps_j in enumerate(ls_gps[i+1:], start = i+1):
      if gps_i and gps_j:
        distance_i_j = compute_distance(gps_i, gps_j)
        ls_ls_cross_distances[i][j] = distance_i_j
        ls_ls_cross_distances[j][i] = distance_i_j
  return ls_ls_cross_distances

# GENERIC

def get_ls_standardized_frequency(ls_to_count):
  """
  Returns frequency of 0, 1, 2, 3, 4, 5, 20 or less, more for a list of int
  """
  dict_val = dict((k, len(list(g))) for k, g in itertools.groupby(sorted(ls_to_count)))
  ls_len_rr = [0 for i in range(7)]
  for k, v in dict_val.items():
    if k <= 5:
      ls_len_rr[k-1] = v
    elif k <= 20:
      ls_len_rr[5] += v
    else:
      ls_len_rr[6] += v
  return ls_len_rr

def print_dict_stat_des(dict_stat_des):
  for key, content in dict_stat_des.iteritems():
    print key, len(content)

# ANALYIS OF PRICE CHANGES

def get_stats_price_chges(ar_prices, light = True):
  """
  Get descriptive stastistics about a station price changes
  TODO: check how to apply mean/median/quartiles etc to arrays (lambda etc)
   
  Parameters:
  -----------
  ar_prices: numpy array of float and np.nan
  light: True returns scalar stats only, else arrays too
  """
  nb_days = len(ar_prices[~np.isnan(ar_prices)])
  ar_nonan_chges = ar_prices[~np.isnan(ar_prices)][1:] - ar_prices[~np.isnan(ar_prices)][:-1]
  nb_prices = (np.abs(ar_nonan_chges) > zero_threshold).sum() + 1
  ar_chges = np.hstack([np.array([np.nan]), ar_prices[1:] - ar_prices[:-1]])
  nb_ctd = len(ar_chges[~np.isnan(ar_chges)])
  nb_chges = (np.abs(ar_chges) > zero_threshold).sum()
  nb_no_chge = (np.abs(ar_chges) < zero_threshold).sum()
  nb_neg_chges = (ar_chges < -zero_threshold).sum()
  nb_pos_chges = (ar_chges >  zero_threshold).sum()
  ar_neg_chge = ar_chges[ar_chges < -zero_threshold]
  ar_pos_chge = ar_chges[ar_chges >  zero_threshold]
  avg_neg_chge = np.mean(ar_neg_chge)
  avg_pos_chge = np.mean(ar_pos_chge)
  med_neg_chge = np.median(ar_neg_chge)
  med_pos_chge = np.median(ar_pos_chge)
  ls_scalars = [nb_days, nb_prices,
                nb_ctd, nb_no_chge, nb_chges, nb_neg_chges, nb_pos_chges,
                avg_neg_chge, avg_pos_chge, med_neg_chge, med_pos_chge]
  if light:
    return ls_scalars
  else:
    ls_ars = [ar_neg_chge, ar_pos_chge]
    return ls_scalars + ls_ars

def get_stats_two_firm_price_chges(ar_prices_1, ar_prices_2):
  """
  Counts simulatenous changes: A and B had changed before or none had changed
  Counts followed changes: A changes, B follows (checks B changes after)
  Counts following changes: B changes, A follows (checks 1 changes after)
  TODO: check also that B had not changed before A change for followed changes
  Reminder: must be cautious with nan (and get day indexes if possible...)
  
  Parameters:
  -----------
  ar_prices_1, ar_prices_2: two numpy arrays of float and np.nan
  """
  ar_prices_nonan_1 = ar_prices_1[~np.isnan(ar_prices_1)]
  ar_prices_nonan_2 = ar_prices_2[~np.isnan(ar_prices_2)]
  nb_days_1 = len(ar_prices_nonan_1)
  nb_days_2 = len(ar_prices_nonan_2)
  ar_nonan_chges_1 = ar_prices_nonan_1[1:] - ar_prices_nonan_1[:-1]
  ar_nonan_chges_2 = ar_prices_nonan_2[1:] - ar_prices_nonan_2[:-1]
  nb_prices_1 = (np.abs(ar_nonan_chges_1) > zero_threshold).sum() + 1
  nb_prices_2 = (np.abs(ar_nonan_chges_2) > zero_threshold).sum() + 1
  ar_chges_1 = ar_prices_1[1:] - ar_prices_1[:-1]
  ar_chges_2 = ar_prices_2[1:] - ar_prices_2[:-1]
  nb_ctd_1 = len(ar_chges_1[~np.isnan(ar_chges_1)])
  nb_ctd_2 = len(ar_chges_2[~np.isnan(ar_chges_2)])
  nb_chges_1 = (np.abs(ar_chges_1) > zero_threshold).sum() 
  nb_chges_2 = (np.abs(ar_chges_2) > zero_threshold).sum() 
  # Count simulatenous changes (following no chge at all or another sim chge)
  ar_dum_chges_1 = (np.abs(ar_chges_1) > zero_threshold)*1
  ar_dum_chges_2 = (np.abs(ar_chges_2) > zero_threshold)*1
  ar_sum_dum_chges = ar_dum_chges_1 + ar_dum_chges_2
  nb_sim_chges = 0 
  for i, sum_chge in enumerate(ar_sum_dum_chges[1:], start = 1):
    if sum_chge == 2 and (ar_sum_dum_chges[i-1] == 2 or\
                          ar_sum_dum_chges[i-1] == 0):
      nb_sim_chges +=1
  # Count followed changes:
  ls_day_ind_1_follows, ls_day_ind_2_follows = [], []
  for i, (dum_chge_1, dum_chge_2) in enumerate(zip(ar_dum_chges_1, ar_dum_chges_2)[1:], start= 1):
    if (dum_chge_1 == 1) and (ar_dum_chges_1[i-1] == 0) and (ar_dum_chges_2[i-1] == 1):
      ls_day_ind_1_follows.append(i)
    if (dum_chge_2 == 1) and (ar_dum_chges_2[i-1] == 0) and (ar_dum_chges_1[i-1] == 1):
      ls_day_ind_2_follows.append(i)
  # TODO: allow for output of intermediary arrays into pandas for visual check
  return [nb_days_1, nb_days_2, nb_prices_1, nb_prices_2,
          nb_ctd_1, nb_ctd_2, nb_chges_1, nb_chges_2, nb_sim_chges,
          len(ls_day_ind_1_follows), len(ls_day_ind_2_follows),
          ls_day_ind_1_follows, ls_day_ind_2_follows]

def get_two_firm_similar_prices(ar_price_1, ar_price_2):
  """
  Compare price series: rather for non differentiated sellers (same price level)
  """
  ar_spread = ar_price_1 - ar_price_2
  len_spread = len(ar_spread[~np.isnan(ar_spread)])
  len_same = len(ar_spread[np.abs(ar_spread) < zero_threshold])
  ls_chge_to_same = 0
  ls_1_lead, ls_2_lead = [], []
  ctd, ctd_1, ls_ctd_1, ls_ctd_2 = 0, False, [], []
  if len_spread and len_same:
    for i, (price_1, price_2, spread) in enumerate(zip(ar_price_1, ar_price_2, ar_spread)[1:], start = 1):
      if (np.abs(spread) < zero_threshold) and (np.abs(ar_spread[i-1]) > zero_threshold):
        if price_1 == ar_price_1[i-1]:
          ls_1_lead.append(i)
          ctd_1 = True
          ctd = 1
        elif price_2 == ar_price_2[i-1]:
          ls_2_lead.append(i)
          # print 'day', i
          ctd = 1
        else:
          ls_chge_to_same += 1
      elif (np.abs(spread) < zero_threshold) and (ctd > 0):
        ctd += 1
      elif (ctd > 0): #not np.isnan(np.abs(spread)) => cuts if nan...
        if ctd_1:
          ls_ctd_1.append(ctd)
        else:
          ls_ctd_2.append(ctd)
          # print 'length', ctd, i
        ctd, ctd_1 = 0, False
    if ctd != 0:
      if ctd_1:
        ls_ctd_1.append(ctd)
      else:
        ls_ctd_2.append(ctd)
  return (len_spread, len_same, ls_chge_to_same, ls_1_lead, ls_2_lead, ls_ctd_1, ls_ctd_2)

# ANALYSIS OF PAIR PRICE DISPERSION

def get_pair_price_dispersion(ar_prices_a, ar_prices_b, light = True):
  """
  Produces statistics accounting for price dispersions (TODO: elaborate)

  Parameters:
  -----------
  ar_prices_a, ar_prices_b: numpy arrays of float and np.nan
  """
  ar_spread = ar_prices_b - ar_prices_a
  nb_days_spread = (~np.isnan(ar_spread)).sum()
  nb_days_same_price = (np.abs(ar_spread) <= zero_threshold).sum()
  nb_days_b_cheaper = (ar_spread < -zero_threshold).sum()
  nb_days_a_cheaper = (ar_spread >  zero_threshold).sum()
  avg_spread = scipy.stats.nanmean(ar_spread)
  std_spread = scipy.stats.nanstd(ar_spread)
  avg_abs_spread = scipy.stats.nanmean(np.abs(ar_spread))
  if nb_days_b_cheaper > nb_days_a_cheaper:
    ar_spread_rr = np.where(ar_spread <=  zero_threshold, 0, ar_spread)
  else:
    ar_spread_rr = np.where(ar_spread >= -zero_threshold, 0, ar_spread)
  ar_abs_spread_rr = np.abs(ar_spread_rr) 
  ls_day_inds_rr = list(np.where(ar_abs_spread_rr > zero_threshold)[0])
  percent_rr = np.float64(len(ls_day_inds_rr))/nb_days_spread
  avg_abs_spread_rr = np.mean(ar_abs_spread_rr[ar_abs_spread_rr > zero_threshold])
  med_abs_spread_rr = np.median(ar_abs_spread_rr[ar_abs_spread_rr > zero_threshold])
  nb_rr_conservative = count_nb_rr_conservative(ar_abs_spread_rr)
  ls_scalars = [nb_days_spread, nb_days_same_price, nb_days_a_cheaper, nb_days_b_cheaper,
                nb_rr_conservative, percent_rr, avg_abs_spread_rr, med_abs_spread_rr,
                avg_abs_spread, avg_spread, std_spread]
  ls_arrays = [ar_spread, ar_spread_rr]
  ls_ls_lengths = [[], []]
  if not light:
    if percent_rr > zero_threshold:
      # ls_lengths_rr_naive = get_ls_lengths_rr_naive(ar_abs_spread_rr)
      ls_lengths_rr_strict = get_ls_lengths_rr_strict(ar_abs_spread_rr)
      ls_ls_lengths = [ls_lengths_rr_strict, []] # ls_lengths_rr_naive
  return [ls_scalars, ls_day_inds_rr, ls_arrays, ls_ls_lengths]

def count_nb_rr_conservative(ar_abs_spread_rr):
  """
  Counts nb of streaks of positive values in a non negative array:
  if np.nan in between positive values: only one streak is counted
  
  Parameters:
  -----------
  ar_abs_spread_rr: numpy array of non negative float and np.nan
  """
  ar_abs_spread_rr_nonan = ar_abs_spread_rr[~np.isnan(ar_abs_spread_rr)]
  nb_rank_reversals = 0
  if len(ar_abs_spread_rr_nonan) > 0 and ar_abs_spread_rr_nonan[0] > zero_threshold:
    nb_rank_reversals = 1
  for i, spread in enumerate(ar_abs_spread_rr_nonan[1:], start = 1):
    if spread > zero_threshold and ar_abs_spread_rr_nonan[i-1] < zero_threshold:
      nb_rank_reversals += 1
  return nb_rank_reversals

def get_ls_lengths_rr_naive(ar_abs_spread_rr):
  """ 
  Lists lengths of streaks of positive values in a non negative array:
  np.nan are considered as 0 except if in between positive values
  
  Parameters:
  -----------
  ar_abs_spread_rr: numpy array of non negative float and np.nan
  """
  ar_abs_spread_rr_nonan = ar_abs_spread_rr[~np.isnan(ar_abs_spread_rr)]
  ls_len_rr = []
  len_rr = 0
  for spread in ar_abs_spread_rr_nonan:
    if spread > zero_threshold:
      len_rr +=1
    elif spread < zero_threshold and len_rr != 0:
      ls_len_rr.append(len_rr)
      len_rr = 0
  if len_rr > 0:
    ls_len_rr.append(len_rr)
  return ls_len_rr

def get_ls_lengths_rr_strict(ar_abs_spread_rr):
  """ 
  Lists lengths of streaks of positive values in a non negative array:
  Streak is not recorded if adjacent to a np.nan
  Streak is not recorded if starts at beginning or ends at end of array

  Parameters:
  -----------
  A numpy array of float and np.nan
  """
  ls_len_full_rr = []
  len_rr = 0
  dum_nan = 0
  if np.isnan(ar_abs_spread_rr[0]):
    dum_nan = 1
  for i, spread in enumerate(ar_abs_spread_rr[1:], start = 1):
    if spread > zero_threshold and dum_nan == 0:
      len_rr +=1
    elif spread < zero_threshold:
      dum_nan = 0 
      if len_rr != 0:
        ls_len_full_rr.append(len_rr)
        len_rr = 0
    elif np.isnan(spread):
      len_rr = 0
      dum_nan = 1
  if ar_abs_spread_rr[0] > zero_threshold and ar_abs_spread_rr[1] > zero_threshold:
    ls_len_full_rr = ls_len_full_rr[1:]
  return ls_len_full_rr

# ANALYSIS OF MARKET PRICE DISPERSION

def get_ls_ls_distance_market_ids(ls_ids, ls_ls_competitors, km_bound):
  """
  Distance used to define markets
  ls_ls_competitors has same order as master price (necessary condition)
  ls_ls_competitors: list of (id, distance) for each competitor (within 10km)
  """
  ls_ls_distance_market_ids = []
  for indiv_id, ls_competitors in zip(ls_ids, ls_ls_competitors):
    if ls_competitors:
      ls_distance_market_ids = [indiv_id] +\
                               [comp_id for comp_id, distance\
                                  in ls_competitors if distance < km_bound]
      if len(ls_distance_market_ids) > 1:
        ls_ls_distance_market_ids.append(ls_distance_market_ids)
  return ls_ls_distance_market_ids

def get_ls_ls_distance_market_ids_restricted(ls_ids, ls_ls_competitors, km_bound, random_order = False):
  """
  Distance used to define markets
  ls_ls_competitors: list of (id, distance) for each competitor (within 10km)
  ls_ls_competitors has same order as master price
  If id in previous market: drop market 
  """
  ls_zip_ids_competitors = zip(ls_ids, ls_ls_competitors)
  if random_order:
    random.shuffle(ls_zip_ids_competitors)
  ls_ls_distance_market_ids = []
  ls_ids_covered = []
  for indiv_id, ls_competitors in ls_zip_ids_competitors:
    if ls_competitors:
      ls_distance_market_ids = [indiv_id] +\
                               [comp_id for comp_id, distance\
                                  in ls_competitors if distance < km_bound]
      if (len(ls_distance_market_ids) > 1) and\
         not (any(indiv_id in ls_ids_covered for indiv_id in ls_distance_market_ids)):
        ls_ls_distance_market_ids.append(ls_distance_market_ids)
        ls_ids_covered += ls_distance_market_ids
  return ls_ls_distance_market_ids
  
def get_market_price_dispersion(ls_market_ids, df_price):
  df_market_prices = df_price[ls_market_ids]
  se_nb_market_prices =(~np.isnan(df_market_prices)).sum(1)
  se_range = df_market_prices.max(1) - df_market_prices.min(1)
  se_std = df_market_prices.std(1)
  se_coeff_var = df_market_prices.std(1) / df_market_prices.mean(1)
  se_gain_from_search = df_market_prices.mean(1) - df_market_prices.min(1)
  return pd.DataFrame({'range' : se_range,
                       'cv'    : se_coeff_var,
                       'std'   : se_std,
                       'gfs'   : se_gain_from_search,
                       'nb_comp_t' : se_nb_market_prices,
                       'nb_comp'   : se_nb_market_prices.max()})

def get_ls_ls_market_price_dispersion(ls_ls_market_ids, master_price, series):
  # if numpy.version.version = '1.8' or above => switch from scipy to numpy
  # checks nb of prices (non nan) per period (must be 2 prices at least)
  ls_ls_market_pd = []
  for ls_market_ids in ls_ls_market_ids:
    list_market_prices = [master_price[series][master_price['ids'].index(indiv_id)]\
                            for indiv_id in ls_market_ids]
    arr_market_prices = np.array(list_market_prices, dtype = np.float32)
    arr_nb_market_prices = (~np.isnan(arr_market_prices)).sum(0)
    arr_bool_enough_market_prices = np.where(arr_nb_market_prices > 1, 1, np.nan)
    arr_market_prices = arr_bool_enough_market_prices * arr_market_prices
    range_price_array = scipy.nanmax(arr_market_prices, 0) -\
                          scipy.nanmin(arr_market_prices, axis = 0)
    std_price_array = scipy.stats.nanstd(arr_market_prices, 0)
    coeff_var_price_array = scipy.stats.nanstd(arr_market_prices, 0) /\
                              scipy.stats.nanmean(arr_market_prices, 0)
    gain_from_search_array = scipy.stats.nanmean(arr_market_prices, 0) -\
                               scipy.nanmin(arr_market_prices, axis = 0)
    ls_ls_market_pd.append((ls_market_ids,
                            len(ls_market_ids),
                            range_price_array,
                            std_price_array,
                            coeff_var_price_array,
                            gain_from_search_array))
  return ls_ls_market_price_dispersion
  
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
