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

zero_threshold = np.float64(1e-10)

def get_ls_price_changes_vs_competitors(ls_ls_competitors, master_price, series):
  """ TODO: Update / Deprecate ?
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
  ls_ls_results = []
  for indiv_ind, ls_competitors in enumerate(ls_ls_competitors):
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
        nb_chges_2 = ((ar_price_changes_2_ma != 0)).sum()
        # count changes at firm 1 with firm 2 also changing
        mask_2 = ar_price_changes_2 == 0 
        #boolean with True if change at firm 2/
        mask_2_c = ar_price_changes_2 != 0 
        #boolean with False (display) if change at firm 2
        ar_price_changes_1_ma_a = np.ma.masked_array(ar_price_changes_1_ma, mask = mask_2)
        nb_chges_1_if_2_a = ((ar_price_changes_1_ma_a != 0)).sum()
        # count changes at firm 1 with firm 2 changing the day before
        mask_2 = np.append(np.array(np.nan), ar_price_changes_2[:-1]) == 0 
        #boolean with True if change at firm 2/
        ar_price_changes_1_ma_h = np.ma.masked_array(ar_price_changes_1_ma, mask = mask_2)
        ar_price_changes_1_ma_h = np.ma.masked_array(ar_price_changes_1_ma_h, mask = mask_2_c)
        nb_chges_1_if_2_h = ((ar_price_changes_1_ma_h != 0)).sum()
        # count changes at firm 1 with firm 2 changing the day after
        mask_2 = np.append(ar_price_changes_2[1:], np.array(np.nan)) == 0 
        #boolean with True if change at firm 2/
        ar_price_changes_1_ma_d = np.ma.masked_array(ar_price_changes_1_ma, mask = mask_2)
        ar_price_changes_1_ma_d = np.ma.masked_array(ar_price_changes_1_ma_d, mask = mask_2_c)
        nb_chges_1_if_2_d = ((ar_price_changes_1_ma_d != 0)).sum()
        ls_results.append((competitor_id,
                           distance,
                           nb_chges_2, nb_chges_1_if_2_a, nb_chges_1_if_2_h, nb_chges_1_if_2_d))
    ls_ls_results.append(ls_results)
  return ls_ls_results

# ANALYSIS OF PAIR PRICE DISPERSION

def get_pair_price_dispersion(ls_prices_a, ls_prices_b):
  """
  Provides various stats about price dispersion (TODO: elaborate)
  TODO: fix ls_rr_durations: periods of rr must be standardized to one
  (Right now: a new streak is recorded if spread under rank reversal varies...)
  
  Parameters:
  -----------
  ls_prices_a, ls_prices_b: list of float and nan
  """
  ar_prices_a = np.array(ls_prices_a, dtype = np.float32)
  ar_prices_b = np.array(ls_prices_b, dtype = np.float32)
  ar_spread = ar_prices_b - ar_prices_a
  nb_days_spread = (~np.isnan(ar_spread)).sum()
  avg_abs_spread = scipy.stats.nanmean(np.abs(ar_spread))
  avg_spread = scipy.stats.nanmean(ar_spread)
  std_spread = scipy.stats.nanstd(ar_spread)
  nb_days_b_cheaper = (ar_spread < 0).sum()
  nb_days_a_cheaper = (ar_spread > 0).sum()
  rank_reversal = np.min([np.float32(nb_days_b_cheaper)/nb_days_spread,
                          np.float32(nb_days_a_cheaper)/nb_days_spread])
  if nb_days_b_cheaper > nb_days_a_cheaper:
    ar_rank_reversal = np.where(ar_spread <= 0, 0, ar_spread)
  else:
    ar_rank_reversal = np.where(ar_spread >= 0, 0, ar_spread)
  ls_tuples_rr = []
  for group in itertools.groupby(iter(range(len(ar_rank_reversal))),\
                                  lambda x: ar_rank_reversal[x] if ~np.isnan(ar_rank_reversal[x]) else None):
    ls_tuples_rr.append((group[0], list(group[1])))
  ls_rr_durations = [len(tuple_rr[1]) for tuple_rr in ls_tuples_rr if tuple_rr[0] and tuple_rr[0] != 0]
  return (nb_days_spread, avg_abs_spread, avg_spread, std_spread, rank_reversal,\
          ar_rank_reversal, ar_spread, ls_rr_durations)

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
      ls_prices_1 = master_price[series][master_price['ids'].index(id_1)]
      ls_prices_2 = master_price[series][master_price['ids'].index(id_2)]
      pair_pd_stats = get_pair_price_dispersion(ls_prices_1, ls_prices_2)
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
