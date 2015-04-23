#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import json, xlrd
import copy
import re
#import itertools
#from collections import Counter
import numpy as np
import matplotlib.pyplot as plt
import decimal
from decimal import *
import pandas as pd
import statsmodels.api as sm

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def get_num_str(price):
  """ Convert prices (string, french format) to float or nan"""
  try:
    price = float(price.replace(u',', u'.'))
  except:
    price = float('nan')
  return price

def get_num_ls_ls(ls_ls_prices):
  """ Converts list of list of prices (master_price) from string to float or nan"""
  return [[get_num_str(price) for price in ls_prices] for ls_prices in ls_ls_prices]

def fill_prices_using_dates(ls_ls_prices, ls_ls_dates, ls_master_dates):
  """
  Fills list of prices using next available price 
  if the latter was set on the current date (or previously)

  Verify: 
  ind_test = master_price['ids'].index('3410005')
  pd_df_temp = pd.DataFrame(zip(*[master_price['diesel_date'][ind_test],\
                                  master_price['diesel_price'][ind_test]]),\
                            index = master_price['dates'])
  print pd_df_temp.to_string()
  """
  dict_corrections = {}
  dict_errors = []
  for indiv_ind, ls_prices in enumerate(ls_ls_prices):
    for day_ind, price in enumerate(ls_prices):
      if price != price:
        relative_day = 0
        while (day_ind + relative_day < len(ls_master_dates)-1) and\
              (ls_ls_prices[indiv_ind][day_ind + relative_day] !=\
               ls_ls_prices[indiv_ind][day_ind + relative_day]):
          relative_day += 1
        next_valid_date = ls_ls_dates[indiv_ind][day_ind + relative_day]
        # if next_valid_date is not None (end of series full of None)
        if next_valid_date and next_valid_date != '--':
          try:
            # could have bad info in date (check with regex?)
            next_valid_date_int =  int(u'20%s%s%s' %(next_valid_date[6:],
                                                     next_valid_date[3:5],
                                                     next_valid_date[:2]))
            # next date must be the same or anterior to the current date
            if next_valid_date_int <= int(ls_master_dates[day_ind]):
              ls_ls_prices[indiv_ind][day_ind] = ls_ls_prices[indiv_ind][day_ind + relative_day]
              dict_corrections.setdefault(indiv_ind, []).append(day_ind)
          except:
            dict_errors.setdefault(indiv_ind, []).append(day_ind)
  return (ls_ls_prices, dict_corrections, dict_errors)

def fill_short_gaps(ls_ls_prices, lim):
  """
  Fills price series with last available price if len of missing spell below lim
  Beginning and end missing values are not filled
  """
  dict_corrections = {}
  for indiv_ind, ls_prices in enumerate(ls_ls_prices):
    day_ind = 0
    while (day_ind < len(ls_prices)) and (ls_prices[day_ind] != ls_prices[day_ind]):
      day_ind += 1
    while day_ind < len(ls_prices):
      if ls_prices[day_ind] != ls_prices[day_ind]:
        relative_day = 0
        while (day_ind + relative_day < len(ls_prices)) and\
              (ls_prices[day_ind + relative_day] != ls_prices[day_ind + relative_day]) :
          relative_day += 1
        if relative_day < lim and day_ind + relative_day != len(ls_prices):
          ls_ls_prices[indiv_ind] = ls_ls_prices[indiv_ind][:day_ind] +\
                                    [ls_ls_prices[indiv_ind][day_ind - 1] for x in range(relative_day)] +\
                                    ls_ls_prices[indiv_ind][day_ind + relative_day:]
          dict_corrections.setdefault(indiv_ind, []).append((day_ind - 1, day_ind + relative_day))
        day_ind += relative_day
      else:
        day_ind += 1
  return ls_ls_prices, dict_corrections

def get_abnormal_price_values(ls_ls_prices, lower_bound, upper_bound):
  """ Detects abnormal price levels based on provided upper/lower bounds """
  ls_abnormal_prices = []
  for indiv_ind, ls_prices in enumerate(ls_ls_prices):
    day_ind = 0
    while day_ind < len(ls_prices):
      if (ls_prices[day_ind] < lower_bound) or (ls_prices[day_ind] > upper_bound):
        relative_day = 0
        ls_day_inds = []
        while (day_ind + relative_day < len(ls_prices)) and\
              (ls_prices[day_ind] == ls_prices[day_ind + relative_day]):
          ls_day_inds.append(day_ind + relative_day)
          relative_day += 1
        ls_abnormal_prices.append((indiv_ind, ls_prices[day_ind], ls_day_inds))
        day_ind += relative_day
      else:
        day_ind += 1
  return ls_abnormal_prices

def format_ls_abnormal_prices(ls_abnormal_prices, ls_master_ids, ls_master_dates):
  """ Some formatting (may drop) """
  ls_abnormal_prices_formatted = []
  for indiv_ind, price, ls_day_inds in ls_abnormal_prices:
    indiv_id = ls_master_ids[indiv_ind]
    ls_day_dates = [ls_master_dates[day_ind] for day_ind in ls_day_inds]
    ls_abnormal_prices_formatted.append((indiv_ind, indiv_id, price, ls_day_inds, ls_day_dates))
  return ls_abnormal_prices_formatted

def expand_ls_price_corrections(ls_corrections, ls_master_dates):
  """  Format manual correction list """
  ls_corrections_expanded = []
  for id_indiv, price, ls_day_dates in ls_corrections:
    if len(ls_day_dates) == 1:
      ls_corrections_expanded.append([id_indiv, price, ls_day_dates])
    else:
      if ls_day_dates[0] in ls_master_dates and ls_day_dates[1] in ls_master_dates:
        start, end = ls_master_dates.index(ls_day_dates[0]), ls_master_dates.index(ls_day_dates[1])
        ls_day_dates_expanded = ls_master_dates[start:end + 1]
        ls_corrections_expanded.append([id_indiv, price, ls_day_dates_expanded])
      else:
        print 'Can not take into account correction', id_indiv, price, ls_day_dates
  return ls_corrections_expanded
  
def correct_abnormal_price_values(ls_corrections, ls_indiv_ids, ls_master_dates, ls_ls_prices):
  """ Correct mistakes found with get_abnormal_price_values """
  for (indiv_id, correct_price, ls_day_dates) in ls_corrections:
    if indiv_id in ls_indiv_ids:
      indiv_ind = ls_indiv_ids.index(indiv_id)
      for day_date in ls_day_dates:
        if day_date in ls_master_dates:
          day_ind = ls_master_dates.index(day_date)
          ls_ls_prices[indiv_ind][day_ind] = correct_price
  return ls_ls_prices

def correct_abnormal_price_variations(ls_ls_prices, var_lim):
  """ Correct apparent price mistakes """
  # todo: Inspect with pandas
  # todo: Check mistakes with sp95 and/or input forward vs. backward
  dict_suspects_opposit = {}
  dict_suspects_single = {}
  for indiv_ind, ls_prices in enumerate(ls_ls_prices):
    last_price_var = np.nan # check that
    last_price_day_ind = 0
    for day_ind, price in enumerate(ls_prices[1:], start=1):
      if np.abs(price - ls_ls_prices[indiv_ind][day_ind-1]) > var_lim:
        if (np.abs(last_price_var) > var_lim) and\
           (last_price_var*(price - ls_ls_prices[indiv_ind][day_ind-1]) < 0):
          for i in range(last_price_day_ind, day_ind):
            ls_ls_prices[indiv_ind][i] = ls_ls_prices[indiv_ind][last_price_day_ind - 1]
          dict_suspects_opposit.setdefault(indiv_ind, []).append((last_price_day_ind, day_ind))
        else:
          if np.isnan(last_price_var):
            for i in range(last_price_day_ind, day_ind):
              ls_ls_prices[indiv_ind][i] = np.nan
            dict_suspects_single.setdefault(indiv_ind, []).append((last_price_day_ind, day_ind))
          else:
            j = 0
            while (ls_ls_prices[indiv_ind][day_ind + j] == ls_ls_prices[indiv_ind][day_ind]) and\
                  day_ind + j < len(ls_ls_prices[indiv_ind]) - 1:
              j += 1
            if np.isnan(ls_ls_prices[indiv_ind][day_ind + j]):
              for i in range(day_ind, day_ind + j):
                ls_ls_prices[indiv_ind][i] = np.nan
              dict_suspects_single.setdefault(indiv_ind, []).append((day_ind, day_ind + j))
      if price != ls_ls_prices[indiv_ind][day_ind-1]:
        last_price_var = price -ls_ls_prices[indiv_ind][day_ind-1]
        last_price_day_ind = day_ind
  return dict_suspects_opposit, dict_suspects_single, ls_ls_prices

def get_price_durations(ls_ls_prices):
  ls_ls_price_durations = []
  for indiv_ind, ls_prices in enumerate(ls_ls_prices):
    ls_price_durations = [[ls_prices[0], [0]]]
    for day_ind, price in enumerate(ls_prices[1:], start = 1):
      if price != price:
        if ls_price_durations[-1][0] != ls_price_durations[-1][0]:
          ls_price_durations[-1][1].append(day_ind)
        else:
          ls_price_durations.append([price, [day_ind]])
      elif price == ls_price_durations[-1][0]:
        ls_price_durations[-1][1].append(day_ind)
      else:
        ls_price_durations.append([price, [day_ind]])
    ls_ls_price_durations.append(ls_price_durations)
  return ls_ls_price_durations

def correct_abnormal_price_durations(ls_ls_prices, ls_ls_price_durations, duration):
  dict_duration_corrections = {}
  for indiv_ind, ls_price_durations in enumerate(ls_ls_price_durations):
    for price, ls_day_inds in ls_price_durations:
      if price == price and len(ls_day_inds) > duration:
        ls_duration_pbm = []
        for day_ind in ls_day_inds[duration:]:
          ls_ls_prices[indiv_ind][day_ind] = float('nan')
          ls_duration_pbm.append(day_ind)
        dict_duration_corrections.setdefault(indiv_ind, []).append(ls_duration_pbm)
  return dict_duration_corrections, ls_ls_prices

def get_price_variations(ls_ls_price_durations):
  # Caution: tends to modify ls_day_ind in ls_ls_price_durations => copy
  ls_ls_price_durations_copy = copy.deepcopy(ls_ls_price_durations)
  ls_ls_price_variations = []
  for indiv_ind, ls_price_durations in enumerate(ls_ls_price_durations_copy):
    if len(ls_price_durations) > 1:
      ls_price_variations = []
      for price_ind, (price, ls_day_ind) in enumerate(ls_price_durations[1:], start = 1):
        price_variation = price - ls_price_durations[price_ind - 1][0]
        if price_variation == price_variation:
          tup_price_variation = [float(Decimal('%s' %np.round(price_variation, 3))), ls_day_ind]
        else:
          tup_price_variation = [price_variation, ls_day_ind]
        # regroup consecutive np.nan
        if (price_ind > 1) and\
           (tup_price_variation[0] != tup_price_variation[0]) and\
           (ls_price_variations[-1][0] != ls_price_variations[-1][0]):
          ls_price_variations[-1][1] += tup_price_variation[1]
        else:
          ls_price_variations.append(tup_price_variation)
      ls_ls_price_variations.append(ls_price_variations)
    else:
      ls_ls_price_variations.append([])
  return ls_ls_price_variations

def get_rid_missing_periods(ls_ls_prices, nb_missing):
  """ TODO: display array or info to allow to choose cut"""
  ar_ar_prices = np.array(ls_ls_prices, dtype=np.float32)
  ar_nb_valid_prices = np.ma.count(np.ma.masked_invalid(ar_ar_prices), axis = 0)
  ar_bad_periods = np.where(ar_nb_valid_prices < nb_missing)[0].astype(int).tolist()
  for period in ar_bad_periods:
    ar_ar_prices[:, period] = np.nan
  return [np.round(ls_prices, 3).tolist() for ls_prices in ar_ar_prices.tolist()]

def get_overview_reporting(ls_ls_prices, ls_ls_price_durations, ls_master_dates, ls_master_missing_dates):
  """ List of start end and missing within active periods"""
  ls_start_end = []
  ls_none = []
  ls_ls_dilettante = []
  ls_missing_day_ind = [ls_master_dates.index(str_date) for str_date in ls_master_missing_dates]
  for indiv_ind, ls_price_durations in enumerate(ls_ls_price_durations):
    ls_bad_reporting = []
    if len(ls_price_durations) == 1 and ls_price_durations[0][0] != ls_price_durations[0][0]: 
      start = None
      end = None
      ls_none.append(indiv_ind)
    else:
      ls_price_durations_cut = ls_price_durations
      if ls_price_durations_cut[0][0] != ls_price_durations_cut[0][0]:
        ls_price_durations_cut = ls_price_durations_cut[1:]
      if ls_price_durations_cut[-1][0] != ls_price_durations_cut[-1][0]:
        ls_price_durations_cut = ls_price_durations_cut[:-1]
      start = ls_price_durations_cut[0][1][0]
      end = ls_price_durations_cut[-1][1][-1]
      # find missing prices within valid price series (todo: make efficient)
      for (price, ls_day_ind) in ls_price_durations_cut:
        if price != price:
          for day_ind in ls_day_ind:
            if day_ind not in ls_missing_day_ind:
              ls_bad_reporting.append(day_ind)
    ls_start_end.append((start, end))
    ls_ls_dilettante.append(ls_bad_reporting)
  return ls_start_end, ls_none, ls_ls_dilettante

def get_overview_reporting_bis(ls_ls_prices, ls_master_dates, ls_master_missing_dates):
  """ List of start end and missing within active periods"""
  ls_start_end = []
  ls_nan = []
  dict_dilettante = {}
  ls_missing_day_ind = [ls_master_dates.index(str_date) for str_date in ls_master_missing_dates]
  for indiv_ind, ls_prices in enumerate(ls_ls_prices):
    ls_bad_reporting = []
    if any([not np.isnan(price) for price in ls_prices]):
      start_ind, end_ind = 0, len(ls_prices)-1
      while np.isnan(ls_prices[start_ind]):
        start_ind += 1
      while np.isnan(ls_prices[end_ind]):
        end_ind -=1
      ls_start_end.append((start_ind, end_ind))
      for day_ind, price in enumerate(ls_prices[start_ind:end_ind + 1], start = start_ind):
        if np.isnan(price) and day_ind not in ls_missing_day_ind:
          dict_dilettante.setdefault(indiv_ind, []).append(day_ind)
    else:
      ls_nan.append(indiv_ind)
      ls_start_end.append((None, None))
  return ls_start_end, ls_nan, dict_dilettante

def get_overview_turnover(ls_start_end, ls_master_dates, tolerance):
  start_ind_full, end_ind_full = 0, len(ls_master_dates) - 1
  ls_full_spell  = [indiv_ind for indiv_ind, (start_ind, end_ind) in enumerate(ls_start_end)\
                      if (start_ind is not None) and\
                         (start_ind <= start_ind_full + tolerance) and\
                         (end_ind >= end_ind_full - tolerance)]
  ls_short_spell = [indiv_ind for indiv_ind, (start_ind, end_ind) in enumerate(ls_start_end)\
                      if (start_ind is not None) and\
                         (start_ind > start_ind_full + tolerance) and\
                         (end_ind < end_ind_full - tolerance)]
  ls_late_start  = [indiv_ind for indiv_ind, (start_ind, end_ind) in enumerate(ls_start_end)\
                      if (start_ind is not None) and\
                         (start_ind > start_ind_full + tolerance) and\
                         (end_ind >= end_ind_full - tolerance)]
  ls_early_end   = [indiv_ind for indiv_ind, (start_ind, end_ind) in enumerate(ls_start_end)\
                      if (start_ind is not None) and\
                         (start_ind <= start_ind_full + tolerance) and\
                         (end_ind < end_ind_full - tolerance)]
  ls_turnover_keys = ['full', 'short', 'late_start', 'early_end']
  return dict(zip(ls_turnover_keys, [ls_full_spell, ls_short_spell, ls_late_start, ls_early_end]))

def get_sales(ls_ls_price_variations, length_lim):
  ls_ls_sales = []
  for indiv_ind, ls_price_variations in enumerate(ls_ls_price_variations):
    ls_sales = []
    if ls_price_variations:
      for var_ind, (var, list_day_ind) in enumerate(ls_price_variations[1:], start = 1):
        if (np.abs(var + ls_price_variations[var_ind - 1][0]) < np.float64(1e-10)) and\
           (len(ls_price_variations[var_ind - 1][1]) < length_lim):
          ls_sales.append(ls_price_variations[var_ind - 1])
    ls_ls_sales.append(ls_sales)
  return ls_ls_sales

def get_expanded_list(ls_to_expand, ls_expanded_length):
  """
  Reminder: list_to_expand is a list of lists: [(info, period),(info, period)...]
  Returns a list with field info per period: [info_per_1, info_per_2, info_per_3...]
  Starts with None if no info at beginning
  """
  ls_expanded = [None for i in range(ls_expanded_length)]
  if ls_to_expand:
    if ls_to_expand[0][1] != 0:
      ls_to_expand = [[None, 0]] + ls_to_expand
    i = 0
    while i != len(ls_to_expand):
      ls_expanded = ls_expanded[:ls_to_expand[i][1]] +\
                        [ls_to_expand[i][0] for x in ls_expanded[ls_to_expand[i][1]:]]
      i += 1
  return ls_expanded

def get_str_no_accent_up(str_to_format):
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
      str_to_format = str_to_format.replace(accented_char, char) 
      # str_to_format.encode('latin-1').replace(accented_char, char)
  return str_to_format.replace(u'&#039;', u' ').strip().upper()

def get_latest_info(indiv_id, field, master_info, non_null = False):
  if non_null:
    ls_info = [x for x in master_info[indiv_id][field] if x]
  else:
    ls_info = [x for x in master_info[indiv_id][field] if x is not None]
  if ls_info:
    return ls_info[-1]
  else:
    return None

def print_dict_stats_des(dict_stats_des, print_threshold = 3):
  print '\nPrinting some dict_stats_des: \n'
  for k, v in dict_stats_des.iteritems():
    if len(v) > 3:
      print k, len(v)
  print '\n'
  return
