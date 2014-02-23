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
  Fills list of prices using next available price if the later was set on the current date (or previously)

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
  # TODO: Inspect with pandas
  # TODO: Check mistakes with sp95 and/or input forward vs. backward
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
      # find missing prices within valid price series (TODO: make it efficient...)
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
  ls_short_spell = [indiv_ind for indiv_ind, (start_ind, end_ind) in enumerate(ls_start_end)
                      if (start_ind is not None) and\
                         (start_ind > start_ind_full + tolerance) and\
                         (end_ind < end_ind_full - tolerance)]
  ls_late_start  = [indiv_ind for indiv_ind, (start_ind, end_ind) in enumerate(ls_start_end)
                      if (start_ind is not None) and\
                         (start_ind > start_ind_full + tolerance) and\
                         (end_ind >= end_ind_full - tolerance)]
  ls_early_end   = [indiv_ind for indiv_ind, (start_ind, end_ind) in enumerate(ls_start_end)
                      if (start_ind is not None) and\
                         (start_ind <= start_ind_full + tolerance) and\
                         (end_ind < end_ind_full - tolerance)]
  ls_turnover_keys = ['full', 'short', 'late_start', 'early_end']
  return dict(zip(ls_turnover_keys, [ls_full_spell, ls_short_spell, ls_late_start, ls_early_end]))

def get_sales(ls_ls_price_variations, length_lim):
  """ 
  TODO: improve... (e.g. capture pairs? and time limit?)
  TODO: represent both price value and price variation on a graph
  TODO: show continuity of short inverse variations (promotions) towards longer...
  """
  dict_sales = {}
  for indiv_ind, ls_price_variations in enumerate(ls_ls_price_variations):
    if ls_price_variations:
      for var_ind, (var, list_day_ind) in enumerate(ls_price_variations[1:], start = 1):
        if (np.abs(var + ls_price_variations[var_ind - 1][0]) < 0.00001) and\
           (len(ls_price_variations[var_ind - 1][1]) < length_lim):
          dict_sales.setdefault(indiv_ind, []).append(ls_price_variations[var_ind - 1])
  return dict_sales

def get_expanded_list(list_to_expand, list_expanded_length):
  """
  Reminder: list_to_expand is a list of lists: [(info, period),(info, period)...]
  Returns a list with field info per period: [info_per_1, info_per_2, info_per_3...]
  Starts with None if no info at beginning
  """
  list_expanded = [None for i in range(list_expanded_length)]
  if list_to_expand:
    if list_to_expand[0][1] != 0:
      list_to_expand = [[None, 0]] + list_to_expand
    i = 0
    while i != len(list_to_expand):
      list_expanded = list_expanded[:list_to_expand[i][1]] +\
                        [list_to_expand[i][0] for x in list_expanded[list_to_expand[i][1]:]]
      i += 1
  return list_expanded

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

def get_latest_info(id, field, master_info):
  list_info = [x for x in master_info[id][field]]
  if list_info:
    return list_info[-1]
  else:
    return None

def print_dict_stats_des(dict_stats_des, print_threshold = 3):
  print '\nPrinting some dict_stats_des: \n'
  for k, v in dict_stats_des.iteritems():
    if len(v) > 3:
      print k, len(v)
  print '\n'
  return

if __name__=="__main__":
  
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  
  # ##############
  # DIESEL MASTER
  # ##############
   
  master_price = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_price_diesel_raw')
  master_price['diesel_price'] = get_num_ls_ls(master_price['diesel_price'])
  master_price_bu = copy.deepcopy(master_price['diesel_price'])
  ls_start_end_bu, ls_nan_bu, dict_dilettante_bu = get_overview_reporting_bis(master_price['diesel_price'],
                                                                              master_price['dates'], 
                                                                              master_price['missing_dates'])
  master_price['diesel_price'], dict_corrections, dict_errors =\
                                                    fill_prices_using_dates(master_price['diesel_price'],
                                                                            master_price['diesel_date'],
                                                                            master_price['dates'])
  master_price['diesel_price'], dict_corrections_gaps = fill_short_gaps(master_price['diesel_price'], 5)
  ls_abnormal_prices = get_abnormal_price_values(master_price['diesel_price'], 1.0, 2.0)
  ls_abnormal_price_values = format_ls_abnormal_prices(ls_abnormal_prices,
                                                       master_price['ids'],
                                                       master_price['dates'])
  # for indiv_ind, indiv_id, price, ls_day_inds, ls_day_dates in ls_abnormal_price_values:
    # print indiv_ind, ls_day_inds, (indiv_id, price, ls_day_dates)
  
  # Over period '20110904/20120514, following corrections (seems valid => 20121204)
  ls_corrections_diesel =  [(u'2400008' , 1.56 , [u'20120216', u'20120219']), # 0.156
                            (u'11000008', 1.46 , [u'20130219']),              #0.146
                            (u'19300004', 1.45 , [u'20110913', u'20110925']), #0.145
                            (u'22290002', 0.85 , [u'20111104', u'20111107']), #no chge..
                            (u'41100002', 1.41 , [u'20130417', u'20130419']), #0.141
                            (u'42800002', 1.5  , [u'20120319']),              #0.001
                            (u'45650001', 1.4  , [u'20121013', u'20121014']), #0.014
                            (u'47000001', 1.5  , [u'20111119', u'20111120']), #0.001
                            (u'49160003', 1.51 , [u'20121121', u'20121122']), #0.151
                            (u'57160005', 1.55 , [u'20120314']),              #0.155
                            (u'57210001', 1.48 , [u'20121023', u'20121028']), #0.148
                            (u'83510003', 1.492, [u'20120724', u'20120729']), #0.001 unsure
                            (u'86170003', 1.378, [u'20111016', u'20111017']), #0.013
                            (u'93440003', 1.49 , [u'20120914', u'20120916']), #0.149
                            (u'93561001', 1.45 , [u'20111129'])] #0.145
  
  ls_corrections_diesel_e = expand_ls_price_corrections(ls_corrections_diesel, master_price['dates'])
  
  master_price['diesel_price'] = correct_abnormal_price_values(ls_corrections_diesel_e,
                                                               master_price['ids'],
                                                               master_price['dates'],
                                                               master_price['diesel_price'])
  dict_opposit, dict_single, master_price['diesel_price'] =\
    correct_abnormal_price_variations(master_price['diesel_price'], 0.1)
  
  ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
  ls_duration_corrections, master_price['diesel_price'] =\
    correct_abnormal_price_durations(master_price['diesel_price'], ls_ls_price_durations, 60)
  # Stats des after modifications
  ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
  ls_ls_price_variations = get_price_variations(ls_ls_price_durations)
  ls_start_end, ls_nan, dict_dilettante = get_overview_reporting_bis(master_price['diesel_price'],
                                                                     master_price['dates'],
                                                                     master_price['missing_dates'])
  # Get rid of periods with too few observations 
  master_price['diesel_price'] = get_rid_missing_periods(master_price['diesel_price'], 8000)
   
  # enc_json(master_price, path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')
   
  # MOVE TO PRICE ANALYSIS
  dict_sales = get_sales(ls_ls_price_variations, 3)
  ls_sales = [(k, len(v)) for k, v in dict_sales.items()] 
  ls_sales = sorted(ls_sales, key=lambda x: x[1], reverse = True)
  # Analysis of periods of sales: seems some are particularly concerned (uncertainty) 

  # ##############
  # GAS MASTER
  # ##############
  
  # master_price = dec_json(path_data + folder_built_master_json + r'\master_gas\master_price_gas_raw')
  # # master_price_bu_sp95 = copy.deepcopy(master_price['sp95_price'])
  # # master_price_bu_e10 = copy.deepcopy(master_price['e10_price'])
  # master_price['sp95_price'] = get_num_ls_ls(master_price['sp95_price'])
  # master_price['e10_price'] = get_num_ls_ls(master_price['e10_price'])
  
  # master_price['sp95_price'], ls_cors_sp95, ls_ers_sp95 = fill_prices_using_dates(master_price['sp95_price'],
                                                                                   # master_price['sp95_date'],
                                                                                   # master_price['dates'])
  # master_price['e10_price'], ls_cors_e10, ls_ers_e10 = fill_prices_using_dates(master_price['e10_price'],
                                                                               # master_price['e10_date'],
                                                                               # master_price['dates'])
  
  # master_price['sp95_price'], ls_cors_gaps_sp95 = fill_short_gaps(master_price['sp95_price'], 5)
  # ls_abnormal_prices_sp95 = get_abnormal_price_values(master_price['sp95_price'], 1.0, 2.0)
  
  # master_price['e10_price'], ls_cors_gaps_sp95 = fill_short_gaps(master_price['e10_price'], 5)
  # ls_abnormal_prices_e10 = get_abnormal_price_values(master_price['e10_price'], 1.0, 2.0)
  
  # # for ind_indiv, price, ls_day_inds in ls_abnormal_prices_sp95:  
    # # print master_price['ids'][ind_indiv], price, [master_price['dates'][x] for x in ls_day_inds]
  
  # # for ind_indiv, price, ls_day_inds in ls_abnormal_prices_e10:  
    # # print master_price['ids'][ind_indiv], price, [master_price['dates'][x] for x in ls_day_inds]
  
  # ls_corrections_sp95 = [(u'20250002', 1.65 , [u'20120725', u'20120731']),
                         # (u'31190001', float('nan'), [u'20111122', u'20111127']),
                         # (u'36200003', float('nan'), [u'20130122', u'20130207']),
                         # (u'38450001', 1.58 , [u'20120618', u'20120628']),
                         # (u'43800001', 1.59 , [u'20120608', u'20120611']),
                         # (u'47000001', 1.58 , [u'20120103', u'20120105']),
                         # (u'51340002', float('nan'), [u'20110904', u'20111127']),
                         # (u'51340002', float('nan'), [u'20111109', u'20111114']),
                         # (u'51340002', float('nan'), [u'20111127']),
                         # (u'56380001', 1.65 , [u'20120325']),
                         # (u'58160003', 1.61 , [u'20120426', '20120502']),
                         # (u'61170001', 1.63 , [u'20120427']),
                         # (u'63700001', 1.6  , [u'20120513', u'20120515']),
                         # (u'65190001', 1.69 , [u'20120720', u'20120724']),
                         # (u'69360008', float('nan'), [u'20110904', u'20111114']), # weird... drop station?
                         # (u'71500001', 1.63 , [u'20120905', u'20120912']),
                         # (u'71000002', float('nan'), [u'20110904', u'20111019']), # weird... drop station?
                         # (u'71700003', float('nan'), [u'20110904', u'20111114']), # weird... drop station?
                         # (u'79400004', float('nan'), [u'20120615', u'20120619']), # check: expensive period?
                         # (u'83390005', 1.53 , [u'20130429', u'20130506']),
                         # (u'84240001', 1.54 , [u'20110928', u'20110929']),
                         # (u'85350001', 2.066, [u'20120331', u'20120420']),
                         # (u'85350001', 2.055, [u'20120421', u'20120512']),
                         # (u'85350001', 2.043, [u'20120727', u'20120803']),
                         # (u'85350001', 2.093, [u'20120727', u'20120803']),
                         # (u'85350001', 2.043, [u'20120804', u'20120809']),
                         # (u'85350001', 2.043, [u'20120810', u'20120812']),
                         # (u'85350001', 2.121, [u'20120823', u'20120830']),
                         # (u'85350001', 2.085, [u'20120831', u'20120910']),
                         # (u'85350001', 2.025, [u'20120911', u'20120930']),
                         # (u'85350001', 2.04 , [u'20130216', u'20130324']),
                         # (u'85350001', 2.023, [u'20130325', u'20130417']),
                         # (u'85350001', 2.003, [u'20130507', u'20130526'])]
  
  # ls_corrections_e10 =  [(u'1390004' , 1.65 , [u'20130121', u'20130122']),
                         # (u'6300005' , 1.54 , [u'20121003']),
                         # (u'6260001' , 1.62 , [u'20130410']),
                         # (u'7160002' , float('nan'), [u'20110904', u'20111130']),
                         # (u'37800002', 1.53 , [u'20121030']),
                         # (u'44600001', 0.999, [u'20110904', u'20111114']),
                         # (u'44600001', 0.999, [u'20110927', u'20110929']),
                         # (u'51100031', 1.54 , [u'20120811', u'20120811']),
                         # (u'57210001', 1.66 , [u'20120524', u'20120605']),
                         # (u'62220001', 1.56 , [u'20120703']),
                         # (u'75015007', float('nan'), [u'20110904', u'20111129'])]
  
  # # TODO (?): change correction function
  # ls_corrections_sp95_e = expand_ls_price_corrections(ls_corrections_sp95, master_price['dates'])
  # ls_corrections_e10_e = expand_ls_price_corrections(ls_corrections_e10, master_price['dates'])
  
  # master_price['sp95_price'] =  correct_abnormal_price_values(ls_corrections_sp95_e,
                                                              # master_price['ids'],
                                                              # master_price['dates'],
                                                              # master_price['sp95_price'])
                                                                  
  # master_price['e10_price'] =   correct_abnormal_price_values(ls_corrections_e10_e,
                                                              # master_price['ids'],
                                                              # master_price['dates'],
                                                              # master_price['e10_price'])
                                                                  
  # ls_suspects_sp95, ls_suspects_single_sp95, master_price['sp95_price'] =\
    # correct_abnormal_price_variations(master_price['sp95_price'], 0.1)
  
  # ls_suspects_e10, ls_suspects_single_e10, master_price['e10_price'] =\
    # correct_abnormal_price_variations_nan(master_price['e10_price'], 0.1)
  
  # ls_ls_price_durations_sp95 = get_price_durations(master_price['sp95_price'])
  # ls_duration_corrections_sp95, master_price['sp95_price'] =\
    # correct_abnormal_price_durations(master_price['sp95_price'], ls_ls_price_durations_sp95, 30)
  
  # ls_ls_price_durations_e10 = get_price_durations(master_price['e10_price'])
  # ls_duration_corrections_sp95, master_price['e10_price'] =\
    # correct_abnormal_price_durations(master_price['e10_price'], ls_ls_price_durations_sp95, 30)
  
  # # Stats des after modifications
  
  # ls_ls_price_durations_sp95 = get_price_durations(master_price['sp95_price'])
  # ls_ls_price_variations_sp95 = get_price_variations(ls_ls_price_durations_sp95)
  # ls_start_end_sp95, ls_none_sp95, ls_ls_dilettante_sp95 =\
                    # get_overview_reporting(master_price['sp95_price'],
                                           # ls_ls_price_durations_sp95,
                                           # master_price['dates'],
                                           # master_price['missing_dates'])
  
  # ls_ls_price_durations_e10 = get_price_durations(master_price['e10_price'])
  # ls_ls_price_variations_e10 = get_price_variations(ls_ls_price_durations_e10)
  # ls_start_end_e10, ls_none_e10, ls_ls_dilettante_e10 =\
                    # get_overview_reporting(master_price['e10_price'],
                                           # ls_ls_price_durations_e10,
                                           # master_price['dates'],
                                           # master_price['missing_dates'])
  
  # master_price['e10_price'] = get_rid_missing_periods(master_price['e10_price'], 2700)
  # master_price['sp95_price'] = get_rid_missing_periods(master_price['sp95_price'], 5500)
  
  # TODO: read http://www.leparisien.fr/economie/pourquoi-le-sans-plomb-98-coute-t-il-plus-cher-que-le-sp95-01-05-2012-1979493.php
  
  # # enc_json(master_price, path_data + folder_built_master_json + r'/master_gas/master_price_gas')
