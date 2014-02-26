#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

path_dir_built_json = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_json_gasoline')
path_diesel_price = os.path.join(path_dir_built_json, 'master_diesel', 'master_price_diesel')
path_info = os.path.join(path_dir_built_json, 'master_diesel', 'master_info_diesel')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'master_diesel', 'ls_ls_competitors')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'master_diesel', 'ls_tuple_competitors')

path_dir_source_stations = os.path.join(path_data, 'data_gasoline', 'data_source', 'data_stations')
path_dict_brands = os.path.join(path_dir_source_stations, 'data_brands', 'dict_brands')

path_dict_dpts_regions = os.path.join(path_data, 'data_insee', 'Regions_departements', 'dict_dpts_regions')

path_dir_built_csv = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_csv_gasoline')
path_csv_insee_data = os.path.join(path_dir_built_csv, 'master_insee_output.csv') 

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

ar_prices_a = np.array([1, 1, 2, np.nan, 2, 3, 1], np.float32)
ar_prices_b = np.array([0, 2, 2, np.nan, 1, 4, 4], np.float32)

zero_threshold = 0.00001

def get_pair_price_dispersion_bis(ar_prices_a, ar_prices_b, light = True):
  """
  Produces statistics accounting for price dispersions (TODO: elaborate)

  Parameters:
  -----------
  ar_prices_a, ar_prices_b: numpy arrays of float and np.nan
  """
  ar_spread = ar_prices_b - ar_prices_a
  nb_days_spread = (~np.isnan(ar_spread)).sum()
  avg_abs_spread = scipy.stats.nanmean(np.abs(ar_spread))
  avg_spread = scipy.stats.nanmean(ar_spread)
  std_spread = scipy.stats.nanstd(ar_spread)
  nb_days_b_cheaper = (ar_spread < -zero_threshold).sum()
  nb_days_a_cheaper = (ar_spread >  zero_threshold).sum()
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
  ls_scalars = [avg_abs_spread, avg_spread, std_spread, nb_days_spread,
                percent_rr, avg_abs_spread_rr, med_abs_spread_rr, nb_rr_conservative]
  ls_arrays = [ar_spread, ar_spread_rr]
  if light:
    return [ls_scalars, ls_day_inds_rr, ls_arrays]
  else: 
    ls_lengths_rr_naive = get_ls_lengths_rr_naive(ar_abs_spread_rr)
    ls_lengths_rr_strict = get_ls_lengths_rr_strict(ar_abs_spread_rr)
    ls_ls_lengths = [ls_lengths_rr_naive, ls_lengths_rr_strict]
    return [ls_scalars, ls_arrays, ls_ls_lengths]

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
  if ar_abs_spread_rr[0] > zero_threshold:
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

series = 'diesel_price'
km_bound = 5

# AVERAGE PRICE PER PERIOD  

start = time.clock()
master_np_prices = np.array(master_price[series], np.float64)
matrix_np_prices_ma = np.ma.masked_array(master_np_prices, np.isnan(master_np_prices))
period_mean_prices = np.mean(matrix_np_prices_ma, axis = 0)
period_mean_prices = period_mean_prices.filled(np.nan)

ls_pair_price_dispersion_bis = []
for ((indiv_id_1, indiv_id_2), distance) in ls_tuple_competitors:
  # could check presence btw...
  indiv_ind_1 = master_price['ids'].index(indiv_id_1)
  indiv_ind_2 = master_price['ids'].index(indiv_id_2)
  if distance < km_bound:
    ls_pair_price_dispersion_bis.append(get_pair_price_dispersion_bis(master_np_prices[indiv_ind_1],
                                                                      master_np_prices[indiv_ind_2]),
                                                                      light = False))
print time.clock() - start

# #########################
# PRICE DISPERSION ANALYSIS
# #########################

print 'Starting price dispersion block'

#station_price_dispersion = get_station_price_dispersion('1500007',
#                                                        ls_ls_competitors, 
#                                                        master_price, 
#                                                        series,
#                                                        km_bound)
#
#ls_pair_price_dispersion = get_ls_pair_price_dispersion(ls_tuple_competitors,
#                                                            master_price,
#                                                            series,
#                                                            km_bound)
#
#ls_ls_market_ids = get_ls_ls_distance_market_ids(master_price, ls_ls_competitors, km_bound)
#ls_ls_market_price_dispersion = get_ls_ls_market_price_dispersion(ls_ls_market_ids, master_price, series)
#
#ls_ls_m_ids_res = get_ls_ls_distance_market_ids_restricted(master_price, ls_ls_competitors, km_bound)
#ls_ls_mpd_res = get_ls_ls_market_price_dispersion(ls_ls_m_ids_res, master_price, series)
#  
## print 'Starting sample market price dispersion with cleaned prices'
## ls_ls_mpd_res_clean = get_ls_ls_market_price_dispersion(ls_ls_m_ids_res[0:10],
#                                                                # master_price,
#                                                                # series,
#                                                                # clean = True)
#
## PAIR PRICE DISPERSION
#
#matrix_pair_pd = np.array([pd_tuple for pd_tuple in ls_pair_price_dispersion if pd_tuple[1] < km_bound])
## col 1: distance, (col 2: duration, col 4: avg_spread), col 5: std_spread, col 6: rank reversals
#matrix_pair_pd = np.array(np.vstack([matrix_pair_pd[:,1],
#                                     matrix_pair_pd[:,5], 
#                                     matrix_pair_pd[:,6]]), dtype = np.float32).T
#pd_pair_pd = pd.DataFrame(matrix_pair_pd, columns = ['distance', 'spread_std', 'rank_reversals'])
#pd_pair_pd = pd_pair_pd.dropna()
#
## MARKET PRICE DISPERSION
#
#matrix_master_pd = []
#for market in ls_ls_market_price_dispersion:
#  # create variable containing number of competitors for each period
#  array_nb_competitors = np.ones(len(market[2])) * market[1]
#  matrix_master_pd.append(np.vstack([array_nb_competitors, period_mean_prices, market[2:]]).T)
#matrix_master_pd = np.vstack(matrix_master_pd)
## matrix_master_pd = np.array(matrix_master_pd, dtype = np.float64)
#
#ls_column_labels = ['nb_competitors', 'price', 'std_prices', 'coeff_var_prices', 'range_prices', 'gain_search']
#pd_master_pd = pd.DataFrame(matrix_master_pd, columns = ls_column_labels)
#pd_master_pd = pd_master_pd.dropna()
