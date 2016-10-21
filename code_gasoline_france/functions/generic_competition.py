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
from collections import Counter
from generic_master_price import *

def compute_distance(tup_gps_A, tup_gps_B):
  d_lat = math.radians(float(tup_gps_B[0]) - float(tup_gps_A[0]))
  d_lon = math.radians(float(tup_gps_B[1]) - float(tup_gps_A[1]))
  lat_1 = math.radians(float(tup_gps_A[0]))
  lat_2 = math.radians(float(tup_gps_B[0]))
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
  # returns a matrix, half of which is empty
  ls_ls_cross_distances = [[np.nan for gps in ls_gps] for gps in ls_gps]
  for i, gps_i in enumerate(ls_gps):
    for j, gps_j in enumerate(ls_gps[i+1:], start = i+1):
      if gps_i and gps_j:
        distance_i_j = compute_distance(gps_i, gps_j)
        ls_ls_cross_distances[i][j] = distance_i_j
        ls_ls_cross_distances[j][i] = distance_i_j
  return ls_ls_cross_distances

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

def get_stats_price_chges(ar_prices, light = True):
  """
  Get descriptive stastistics about a station price changes
  TODO: check how to apply mean/median/quartiles etc to arrays (lambda etc)
   
  Parameters:
  -----------
  ar_prices: numpy array of float and np.nan
  light: True returns scalar stats only, else arrays too
  """
  zero = np.float64(1e-10)
  nb_days = len(ar_prices[~np.isnan(ar_prices)])
  ar_nonan_chges = ar_prices[~np.isnan(ar_prices)][1:] - ar_prices[~np.isnan(ar_prices)][:-1]
  nb_prices = (np.abs(ar_nonan_chges) > zero).sum() + 1
  ar_chges = np.hstack([np.array([np.nan]), ar_prices[1:] - ar_prices[:-1]])
  nb_ctd = len(ar_chges[~np.isnan(ar_chges)])
  nb_no_chge = (np.abs(ar_chges) < zero).sum()
  nb_chges = (np.abs(ar_chges) > zero).sum()
  nb_neg_chges = (ar_chges < -zero).sum()
  nb_pos_chges = (ar_chges >  zero).sum()
  ar_neg_chges = ar_chges[ar_chges < -zero]
  ar_pos_chges = ar_chges[ar_chges >  zero]
  avg_neg_chge = np.mean(ar_neg_chges)
  avg_pos_chge = np.mean(ar_pos_chges)
  med_neg_chge = np.median(ar_neg_chges)
  med_pos_chge = np.median(ar_pos_chges)
  ls_scalars = [nb_days, nb_prices,
                nb_ctd, nb_no_chge, nb_chges, nb_neg_chges, nb_pos_chges,
                avg_neg_chge, avg_pos_chge, med_neg_chge, med_pos_chge]
  if light:
    ls_results = ls_scalars
  else:
    ls_results = ls_scalars + [ar_neg_chges, ar_pos_chges]
  return ls_results

def get_stats_two_firm_price_spread(ar_prices_1, ar_prices_2, par_round):
  ar_spread = ar_prices_1 - ar_prices_2
  nb_spread = len(ar_spread[~np.isnan(ar_spread)])
  if nb_spread != 0:
    mean_spread = scipy.stats.nanmean(ar_spread)
    mean_abs_spread = scipy.stats.nanmean(np.abs(ar_spread))
    std_spread = scipy.stats.nanstd(ar_spread)
    std_abs_spread = scipy.stats.nanstd(np.abs(ar_spread))
    # Two Most common spread
    ar_spread_nodec = (np.around(ar_spread, par_round) * np.power(10, par_round))
    dict_spread_vc = Counter(ar_spread_nodec[~pd.isnull(ar_spread_nodec)])
    ls_tup_spread_vc = sorted(dict_spread_vc.items(),
                              key = lambda tup: tup[1],
                              reverse = True)
    mc_spread = ls_tup_spread_vc[0][0] / np.power(10, par_round)
    freq_mc_spread = ls_tup_spread_vc[0][1] * 100 / float((~np.isnan(ar_spread)).sum())
    # Second most common spread
    smc_spread, freq_smc_spread = np.nan, np.nan
    if len(ls_tup_spread_vc) >= 2:
      smc_spread = ls_tup_spread_vc[1][0] / np.power(10, par_round)
      freq_smc_spread = ls_tup_spread_vc[1][1] * 100 / float((~np.isnan(ar_spread)).sum())
    # Third most common spread
    tmc_spread, freq_tmc_spread = np.nan, np.nan
    if len(ls_tup_spread_vc) >= 3:
      tmc_spread = ls_tup_spread_vc[2][0] / np.power(10, par_round)
      freq_tmc_spread = ls_tup_spread_vc[2][1] * 100 / float((~np.isnan(ar_spread)).sum())
    # Median spread 
    med_spread = np.median(ar_spread[~np.isnan(ar_spread)])
    freq_med_spread =  dict_spread_vc[np.round(med_spread, par_round) *\
                                        np.power(10, par_round)] /\
                         float((~np.isnan(ar_spread)).sum()) * 100
    ls_results = [nb_spread, 
                  mean_spread, mean_abs_spread,
                  std_spread, std_abs_spread,
                  mc_spread, freq_mc_spread,
                  smc_spread, freq_smc_spread,
                  tmc_spread, freq_tmc_spread,
                  med_spread, freq_med_spread]
  else:
    ls_results = [nb_spread] + [np.nan for i in range(10)]
  return ls_results

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
  zero = np.float64(1e-10)
  ar_chges_1 = ar_prices_1[1:] - ar_prices_1[:-1]
  ar_chges_2 = ar_prices_2[1:] - ar_prices_2[:-1]
  nb_ctd_1 = (~np.isnan(ar_chges_1)).sum()
  nb_ctd_2 = (~np.isnan(ar_chges_2)).sum()
  # Count successive days observed for both individuals
  nb_ctd_both = ((~np.isnan(ar_chges_1)) * (~np.isnan(ar_chges_2))).sum()
  nb_chges_1 = (np.abs(ar_chges_1) > zero).sum() 
  nb_chges_2 = (np.abs(ar_chges_2) > zero).sum() 
  # Count simulatenous changes (following no chge at all or another sim chge)
  ar_dum_chges_1 = (np.abs(ar_chges_1) > zero)*1
  ar_dum_chges_2 = (np.abs(ar_chges_2) > zero)*1
  ar_sum_dum_chges = ar_dum_chges_1 + ar_dum_chges_2
  nb_sim_chges = 0 
  for i, sum_chge in enumerate(ar_sum_dum_chges[1:], start = 1):
    if sum_chge == 2 and (ar_sum_dum_chges[i-1] == 2 or\
                          ar_sum_dum_chges[i-1] == 0):
      nb_sim_chges +=1
  # Count followed changes:
  ls_day_ind_1_follows, ls_day_ind_2_follows = [], []
  for i, (dum_chge_1, dum_chge_2) in enumerate(zip(ar_dum_chges_1, ar_dum_chges_2)[1:],
                                               start= 1):
    if (dum_chge_1 == 1) and (ar_dum_chges_1[i-1] == 0) and (ar_dum_chges_2[i-1] == 1):
      ls_day_ind_1_follows.append(i)
    if (dum_chge_2 == 1) and (ar_dum_chges_2[i-1] == 0) and (ar_dum_chges_1[i-1] == 1):
      ls_day_ind_2_follows.append(i)
  return [[nb_ctd_1, nb_ctd_2, nb_ctd_both,
           nb_chges_1, nb_chges_2, nb_sim_chges,
           len(ls_day_ind_1_follows), len(ls_day_ind_2_follows)],
          [ls_day_ind_1_follows, ls_day_ind_2_follows]]

def get_stats_two_firm_same_prices(ar_price_1, ar_price_2):
  """
  Compare price series: rather for non differentiated sellers (same price level)
  """
  zero = np.float64(1e-10)
  ar_spread = ar_price_1 - ar_price_2
  len_spread = len(ar_spread[~np.isnan(ar_spread)])
  len_same = len(ar_spread[np.abs(ar_spread) < zero])
  ls_chge_to_same = 0
  ls_1_lead, ls_2_lead = [], []
  ctd, ctd_1, ls_ctd_1, ls_ctd_2 = 0, False, [], []
  if len_spread and len_same:
    for i, (price_1, price_2, spread) in enumerate(zip(ar_price_1,
                                                       ar_price_2,
                                                       ar_spread)[1:], start = 1):
      # same today, not same yesterday (with change)
      if (np.abs(spread) < zero) and (np.abs(ar_spread[i-1]) > zero):
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
      # same today, same yesterday (with change)
      elif (np.abs(spread) < zero) and\
           (np.abs(ar_spread[i-1]) < zero) and\
           (price_1 != ar_price_1[i-1]):
        ls_chge_to_same += 1
      # same today (no change, continued)
      elif (np.abs(spread) < zero) and (ctd > 0):
        ctd += 1
      elif (ctd > 0): #not np.isnan(np.abs(spread)) => cuts if nan
        if ctd_1:
          ls_ctd_1.append(ctd)
        else:
          ls_ctd_2.append(ctd)
          # print 'length', ctd, i
        ctd, ctd_1 = 0, False
    # save ctd if series in progress on last day
    if ctd != 0:
      if ctd_1:
        ls_ctd_1.append(ctd)
      else:
        ls_ctd_2.append(ctd)
  return [[len_spread, len_same, ls_chge_to_same, len(ls_1_lead), len(ls_2_lead)],
          [ls_1_lead, ls_2_lead, ls_ctd_1, ls_ctd_2]]

def get_stats_two_firm_same_prices_ud(ar_price_1, ar_price_2):
  """
  Compare price series: rather for non differentiated sellers (same price level)
  """
  zero = np.float64(1e-10)
  ar_spread = ar_price_1 - ar_price_2
  len_spread = len(ar_spread[~np.isnan(ar_spread)])
  len_same = len(ar_spread[np.abs(ar_spread) < zero])
  ls_chge_to_same = 0
  ls_1_lead, ls_2_lead = [], []
  ls_1_lead_u, ls_2_lead_u = [], []
  ls_chge_to_same_u, ls_chge_to_same_d = 0, 0
  ctd, ctd_1, ls_ctd_1, ls_ctd_2 = 0, False, [], []
  if len_spread and len_same:
    for i, (price_1, price_2, spread) in enumerate(zip(ar_price_1,
                                                       ar_price_2,
                                                       ar_spread)[1:], start = 1):
      # same today, not same yesterday (with change)
      if (np.abs(spread) < zero) and (np.abs(ar_spread[i-1]) > zero):
        if price_1 == ar_price_1[i-1]:
          ls_1_lead.append(i)
          if price_2 > ar_price_2[i-1]:
            ls_1_lead_u.append(i)
          ctd_1 = True
          ctd = 1
        elif price_2 == ar_price_2[i-1]:
          ls_2_lead.append(i)
          if price_1 > ar_price_1[i-1]:
            ls_2_lead_u.append(i)
          # print 'day', i
          ctd = 1
        else:
          ls_chge_to_same += 1
          if (price_1 > ar_price_1[i-1]) and (price_2 > ar_price_2[i-1]):
            ls_chge_to_same_u += 1
          elif (price_1 < ar_price_1[i-1]) and (price_2 < ar_price_2[i-1]):
            pass
          else:
            ls_chge_to_same_d += 1
      # same today, same yesterday (with change)
      elif (np.abs(spread) < zero) and\
           (np.abs(ar_spread[i-1]) < zero) and\
           (price_1 != ar_price_1[i-1]):
        ls_chge_to_same += 1
        if price_1 > ar_price_1[i-1]:
          ls_chge_to_same_u += 1
      # same today (no change, continued)
      elif (np.abs(spread) < zero) and (ctd > 0):
        ctd += 1
      elif (ctd > 0): #not np.isnan(np.abs(spread)) => cuts if nan
        if ctd_1:
          ls_ctd_1.append(ctd)
        else:
          ls_ctd_2.append(ctd)
          # print 'length', ctd, i
        ctd, ctd_1 = 0, False
    # save ctd if series in progress on last day
    if ctd != 0:
      if ctd_1:
        ls_ctd_1.append(ctd)
      else:
        ls_ctd_2.append(ctd)
  return [[len_spread, len_same, ls_chge_to_same,
           len(ls_1_lead), len(ls_2_lead),
           len(ls_1_lead_u), len(ls_2_lead_u),
           ls_chge_to_same_u, ls_chge_to_same_d],
          [ls_1_lead, ls_2_lead, ls_ctd_1, ls_ctd_2, ls_1_lead_u, ls_2_lead_u]]

# ANALYSIS OF PAIR PRICE DISPERSION

def get_pair_price_dispersion(ar_prices_a, ar_prices_b, light = True):
  """
  Produces statistics accounting for price dispersions (TODO: elaborate)

  Parameters:
  -----------
  ar_prices_a, ar_prices_b: numpy arrays of float and np.nan
  """
  zero = np.float64(1e-10)
  ar_spread = ar_prices_b - ar_prices_a
  nb_days_spread = (~np.isnan(ar_spread)).sum()
  nb_days_same_price = (np.abs(ar_spread) <= zero).sum()
  nb_days_b_cheaper = (ar_spread < -zero).sum()
  nb_days_a_cheaper = (ar_spread >  zero).sum()
  avg_spread = scipy.stats.nanmean(ar_spread)
  std_spread = scipy.stats.nanstd(ar_spread)
  avg_abs_spread = scipy.stats.nanmean(np.abs(ar_spread))
  std_abs_spread = scipy.stats.nanstd(np.abs(ar_spread))
  if nb_days_b_cheaper > nb_days_a_cheaper:
    ar_spread_rr = np.where(ar_spread <=  zero, 0, ar_spread)
  else:
    ar_spread_rr = np.where(ar_spread >= -zero, 0, ar_spread)
  ar_abs_spread_rr = np.abs(ar_spread_rr) 
  ls_day_inds_rr = list(np.where(ar_abs_spread_rr > zero)[0])
  percent_rr = np.float64(len(ls_day_inds_rr))/nb_days_spread
  avg_abs_spread_rr = np.mean(ar_abs_spread_rr[ar_abs_spread_rr > zero])
  med_abs_spread_rr = np.median(ar_abs_spread_rr[ar_abs_spread_rr > zero])
  nb_rr_conservative = count_nb_rr_conservative(ar_abs_spread_rr)
  ls_scalars = [nb_days_spread, nb_days_same_price, nb_days_a_cheaper, nb_days_b_cheaper,
                nb_rr_conservative, percent_rr, avg_abs_spread_rr, med_abs_spread_rr,
                avg_abs_spread, avg_spread, std_spread, std_abs_spread]
  ls_arrays = [ar_spread, ar_spread_rr]
  ls_ls_lengths = [[], []]
  if not light:
    if percent_rr > zero:
      ls_lengths_rr_naive = get_ls_lengths_rr_naive(ar_abs_spread_rr)
      ls_lengths_rr_strict = get_ls_lengths_rr_strict(ar_abs_spread_rr)
      ls_ls_lengths = [ls_lengths_rr_strict, ls_lengths_rr_naive] # ls_lengths_rr_naive
  return [ls_scalars, ls_day_inds_rr, ls_arrays, ls_ls_lengths]

def count_nb_rr_conservative(ar_abs_spread_rr):
  """
  Counts nb of streaks of positive values in a non negative array:
  if np.nan in between positive values: only one streak is counted
  
  Parameters:
  -----------
  ar_abs_spread_rr: numpy array of non negative float and np.nan
  """
  zero = np.float64(1e-10)
  ar_abs_spread_rr_nonan = ar_abs_spread_rr[~np.isnan(ar_abs_spread_rr)]
  nb_rank_reversals = 0
  if (len(ar_abs_spread_rr_nonan) > 0) and\
     (ar_abs_spread_rr_nonan[0] > zero):
    nb_rank_reversals = 1
  for i, spread in enumerate(ar_abs_spread_rr_nonan[1:], start = 1):
    if spread > zero and ar_abs_spread_rr_nonan[i-1] < zero:
      nb_rank_reversals += 1
  return nb_rank_reversals

def get_ls_lengths_rr_naive(ar_abs_spread_rr):
  """ 
  Lists lengths of streaks of positive values in a non negative array:
  np.nan are considered as 0 except if in between positive values
  Streak is recorded also if starts at beginning or ends at end of array
  
  Parameters:
  -----------
  ar_abs_spread_rr: numpy array of non negative float and np.nan
  """
  zero = np.float64(1e-10)
  ar_abs_spread_rr_nonan = ar_abs_spread_rr[~np.isnan(ar_abs_spread_rr)]
  ls_len_rr = []
  len_rr = 0
  for spread in ar_abs_spread_rr_nonan:
    if spread > zero:
      len_rr +=1
    elif spread < zero and len_rr != 0:
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
  zero = np.float64(1e-10)
  ls_len_full_rr = []
  len_rr = 0
  dum_nan = 0
  if np.isnan(ar_abs_spread_rr[0]):
    dum_nan = 1
  for i, spread in enumerate(ar_abs_spread_rr[1:], start = 1):
    if spread > zero and dum_nan == 0:
      len_rr +=1
    elif spread < zero:
      dum_nan = 0 
      if len_rr != 0:
        ls_len_full_rr.append(len_rr)
        len_rr = 0
    elif np.isnan(spread):
      len_rr = 0
      dum_nan = 1
  if ar_abs_spread_rr[0] > zero and ar_abs_spread_rr[1] > zero:
    ls_len_full_rr = ls_len_full_rr[1:]
  return ls_len_full_rr

# ANALYSIS OF MARKET PRICE DISPERSION

def get_ls_ls_market_ids(dict_ls_comp, km_bound):
  """
  Distance used to define markets
  ls_ls_competitors has same order as master price (necessary condition)
  ls_ls_competitors: list of (id, distance) for each competitor (within 10km)
  """
  ls_ls_market_ids = []
  for indiv_id, ls_comp in dict_ls_comp.items():
    ls_market_ids = [indiv_id] +\
                    [comp_id for (comp_id, distance) in ls_comp if distance <= km_bound]
    if len(ls_market_ids) > 1:
      ls_ls_market_ids.append(ls_market_ids)
  return ls_ls_market_ids

def get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound, random_order = False):
  """
  Distance used to define markets
  ls_ls_competitors: list of (id, distance) for each competitor (within 10km)
  ls_ls_competitors has same order as master price
  If id in previous market: drop market 
  """
  ls_ids = dict_ls_comp.keys()
  if random_order:
    random.shuffle(ls_ids)
  ls_ls_market_ids, ls_ids_covered = [], []
  for indiv_id in ls_ids:
    ls_market_ids = [indiv_id] +\
                    [comp_id for (comp_id, distance) in dict_ls_comp[indiv_id]\
                             if distance < km_bound]
    if (len(ls_market_ids) > 1) and\
       (not any(indiv_id in ls_ids_covered for indiv_id in ls_market_ids)):
      ls_ls_market_ids.append(ls_market_ids)
      ls_ids_covered += ls_market_ids
  return ls_ls_market_ids
  
def get_market_price_dispersion(ls_market_ids, df_price, ddof = 0):
  """
  Consider whole population observed hence we measure actual std (ddof = 0)
  """
  df_market_prices = df_price[ls_market_ids]
  se_nb_market_prices =(~np.isnan(df_market_prices)).sum(1)
  se_range = df_market_prices.max(1) - df_market_prices.min(1)
  se_std = df_market_prices.std(1, ddof = ddof)
  se_coeff_var = df_market_prices.std(1, ddof = ddof) / df_market_prices.mean(1)
  se_gain_from_search = df_market_prices.mean(1) - df_market_prices.min(1)
  return pd.DataFrame({'range' : se_range,
                       'cv'    : se_coeff_var,
                       'std'   : se_std,
                       'gfs'   : se_gain_from_search,
                       'nb_comp_t' : se_nb_market_prices,
                       'nb_comp'   : se_nb_market_prices.max()})

#def get_ls_ls_market_price_dispersion(ls_ls_market_ids, master_price, series):
#  # if numpy.version.version = '1.8' or above => switch from scipy to numpy
#  # checks nb of prices (non nan) per period (must be 2 prices at least)
#  ls_ls_market_pd = []
#  for ls_market_ids in ls_ls_market_ids:
#    list_market_prices = [master_price[series][master_price['ids'].index(indiv_id)]\
#                            for indiv_id in ls_market_ids]
#    arr_market_prices = np.array(list_market_prices, dtype = np.float32)
#    arr_nb_market_prices = (~np.isnan(arr_market_prices)).sum(0)
#    arr_bool_enough_market_prices = np.where(arr_nb_market_prices > 1, 1, np.nan)
#    arr_market_prices = arr_bool_enough_market_prices * arr_market_prices
#    range_price_array = scipy.nanmax(arr_market_prices, 0) -\
#                          scipy.nanmin(arr_market_prices, axis = 0)
#    std_price_array = scipy.stats.nanstd(arr_market_prices, 0)
#    coeff_var_price_array = scipy.stats.nanstd(arr_market_prices, 0) /\
#                              scipy.stats.nanmean(arr_market_prices, 0)
#    gain_from_search_array = scipy.stats.nanmean(arr_market_prices, 0) -\
#                               scipy.nanmin(arr_market_prices, axis = 0)
#    ls_ls_market_pd.append((ls_market_ids,
#                            len(ls_market_ids),
#                            range_price_array,
#                            std_price_array,
#                            coeff_var_price_array,
#                            gain_from_search_array))
#  return ls_ls_market_price_dispersion
#  
#def get_fe_predicted_prices(list_ids, series):
#  dict_panel_data_master_temp = {}
#  for indiv_id in list_ids:
#    indiv_ind = master_price['ids'].index(id)
#    list_station_prices = master_price[series][indiv_ind]
#    list_station_brands = [dict_brands[get_str_no_accent_up(brand)][1] if brand else brand\
#                            for brand in get_field_as_list(id, 'brand', master_price)]
#    dict_station = {'price' : np.array(list_station_prices, dtype = np.float32),
#                    'brand' : np.array(list_station_brands),
#                    'id' : indiv_id}
#    dict_panel_data_master_temp[indiv_id] = pd.DataFrame(dict_station, index = master_price['dates'])
#  pd_pd_master_temp = pd.Panel(dict_panel_data_master_temp)
#  pd_pd_master_temp = pd_pd_master_temp.transpose('minor', 'items', 'major')
#  pd_mi_master_temp = pd_pd_master_temp.to_frame(filter_observations=False)
#  pd_mi_master_temp['price'] = pd_mi_master_temp['price'].astype(np.float32)
#  pd_mi_master_temp['date'] = pd_mi_master_temp.index.get_level_values(1)
#  res = smf.ols(formula = 'price ~ C(id) + C(date)', data = pd_mi_master_temp).fit()
#  pd_df_X = pd.DataFrame(pd_mi_master_temp[['id', 'date']], columns=["id", "date"])
#  ar_y_prediction = res.predict(pd_df_X)
#  # Need to cut ar_y_prediction in price arrays
#  # Here: Assumes all have same lengths
#  return np.reshape(ar_y_prediction, (len(list_ids), -1))

if __name__=="__main__":
  pass
