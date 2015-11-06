#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
import json
from datetime import date, timedelta
import datetime
import numpy as np
import pprint
import itertools
import pandas as pd
import matplotlib.pyplot as plt

path_built = os.path.join(path_data,
                          u'data_supermarkets',
                          u'data_built',
                          u'data_drive',
                          u'data_auchan')

path_built_json = os.path.join(path_built,
                               'data_json_velizy')

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def explore_info_field(field, master):
  dict_description = {}
  for product, product_info in master['dict_info'].iteritems():
    if product_info[field]:
      for (info, info_ind) in product_info[field]:
        dict_description.setdefault(info, []).append(product)
  return dict_description

def get_field_as_list(id, field, master_price):
  """
  Returns a list with field info per period: [info_per_1, info_per_2, info_per_3...]
  Reminder: Field info is a list of lists: [(info, period),(info, period)...]
  Starts with None if no info at beginning
  """
  field_index = 0
  if not master_price['dict_info'][id][field]:
    # fill with None if no info at all for the field
    list_result = [None for i in range(len(master_price['ls_dates']))]
  else:
    period_index = master_price['dict_info'][id][field][field_index][1]
    # initiate list_result, fill with None if no info at beginning
    if period_index == 0:
      list_result = []
    else:
      list_result = [None for i in range(period_index)]
    # fill list_results with relevant field info
    while period_index < len(master_price['ls_dates']):
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

def analyse_price_series(list_price_series, master_price):
  """
  Detection of prices series with None within activity period
  Can be applied before and after censorship for too long prices
  """
  ls_start_end = []
  ls_none = []
  ls_ls_dilettante = []
  ls_missing_day_ind = [master_price['ls_dates'].index(date)\
                          for date in master_price['ls_missing_dates']]
  for indiv_index, price_series in enumerate(list_price_series):
    ls_price_durations = []
    ls_bad_reporting = []
    for group in itertools.groupby(iter(range(len(price_series))),
                                   lambda x: price_series[x]):
      ls_price_durations.append((group[0], list(group[1])))
    if len(ls_price_durations) == 1 and not ls_price_durations[0][0]:
      start = None
      end = None
      ls_none.append(indiv_index)
    else:
      if not ls_price_durations[0][0]:
        ls_price_durations = ls_price_durations[1:]
      if not ls_price_durations[-1][0]:
        ls_price_durations = ls_price_durations[:-1]
      start = ls_price_durations[0][1][0]
      end = ls_price_durations[-1][1][-1]
      for price, ls_day_ind in ls_price_durations:
        if not price:
          for day_ind in ls_day_ind:
            if day_ind not in ls_missing_day_ind:
              ls_bad_reporting.append(day_ind)
    ls_start_end.append((start, end))
    ls_ls_dilettante.append(ls_bad_reporting)
  return (ls_start_end, ls_none, ls_ls_dilettante)

master = dec_json(os.path.join(path_built_json, 'master'))
dict_dpt_subdpts = dec_json(os.path.join(path_built_json, 'dict_dpt_subdpts'))

# 1/ Question: products entered under 2 different names
# Analysis of price series: 5182 are present at beginning and end out of 10177...
# However: after examination, there doesn't seem to be duplicates...

dict_subdpt_products = {}
for product, product_info in master['dict_info'].iteritems():
  ls_product_subdpts = [subdpt for (ls_subdpts, ls_subdpts_ind)\
                                 in product_info['sub_department']\
                                   for subdpt in ls_subdpts]
  for subdpt in ls_product_subdpts:
    dict_subdpt_products.setdefault(subdpt, []).append(product)

for subdpt, ls_subdpt_products in dict_subdpt_products.iteritems():
  ls_subdpt_products.sort()
  # pprint.pprint(ls_subdpt_products)
  # print '\n'

# #########################
# PROMO FIELDS EXAMINATION
# #########################
  
# Get an idea of content of each field (dpt and subdpt aside as they are lists)
dict_promo_vignette = explore_info_field('product_promo_vignette', master)
dict_promo_type = explore_info_field('product_promo_type', master)
dict_promo_amount = explore_info_field('product_promo_amount', master)
dict_flag = explore_info_field('product_flag', master)

# Analysis of sales based on flag
ls_ls_angles = [get_field_as_list(product, 'product_flag', master)\
                  for product in master['ls_ids']]
ls_ls_promo = [[1 if angle == u'angle flag_promo' else 0 for angle in ls_angles]\
                 for ls_angles in ls_ls_angles]
ls_ls_promo = [[ls_ls_promo[i][j] if price else None for j, price in enumerate(ls_prices)]\
                for i, ls_prices in enumerate(master['ls_ls_prices'])]

# QUESTION: Amount and type promo always associated? YES
ls_ls_amounts = [get_field_as_list(product, 'product_promo_amount', master)\
                   for product in master['ls_ids']]
ls_ls_amounts = [[ls_ls_amounts[i][j] if price else None for j, price in enumerate(ls_prices)]\
                    for i, ls_prices in enumerate(master['ls_ls_prices'])]
ls_ls_types = [get_field_as_list(product, 'product_promo_type', master)\
                 for product in master['ls_ids']]
ls_ls_types = [[ls_ls_types[i][j] if price else None for j, price in enumerate(ls_prices)]\
                    for i, ls_prices in enumerate(master['ls_ls_prices'])]
#ls_amount_type_diffs =[]                    
#for i, ls_amounts in enumerate(ls_ls_amounts):
#  for j, amount in enumerate(ls_amounts):
#    if amount != u'0' and ls_ls_types[i][j] == u'':
#      ls_amount_type_diffs.append((i,j))
#    if amount == u'0' and ls_ls_types[i][j] != u'':
#      ls_amount_type_diffs.append((i,j))
#len(ls_amount_type_diffs) == 0 # hence no differences

# QUESTION: Vignette and type/amount always associated? NO (different kind of promo)
# Vignette may be empty while type/amount are not 
ls_ls_vignettes = [get_field_as_list(product, 'product_promo_vignette', master)\
                     for product in master['ls_ids']]
ls_ls_vignettes = [[ls_ls_vignettes[i][j] if price else None\
                      for j, price in enumerate(ls_prices)]\
                        for i, ls_prices in enumerate(master['ls_ls_prices'])]
ls_amount_vignette_diffs =[]  
for i, ls_amounts in enumerate(ls_ls_amounts):
  for j, amount in enumerate(ls_amounts):
    if amount != u'0' and ls_ls_vignettes[i][j] == u'':
      ls_amount_vignette_diffs.append((i,j))
    if amount == u'0' and ls_ls_vignettes[i][j] != u'':
      ls_amount_vignette_diffs.append((i,j))

# QUESTION: Vignette and type/amount never affect the same product? NO (successive promo)
ls_amount_products = [product for (amount, ls_products) in dict_promo_amount.iteritems()\
                        if amount and amount != u'0' for product in ls_products]
ls_amount_products = list(set(ls_amount_products))
ls_vignette_products = [product for (vignette, ls_vignettes) in dict_promo_vignette.iteritems()\
                          if vignette and vignette != u'0' for product in ls_vignettes]
ls_vignette_products = list(set(ls_vignette_products))
ls_vignette_amount = [elt for elt in ls_vignette_products if elt in ls_amount_products]

# QUESTION: Promo flag covers all promo? YES
ls_flag_vs_amount = []
for i, ls_amounts in enumerate(ls_ls_amounts):
  for j, amount in enumerate(ls_amounts):
    if amount and amount != u'0' and ls_ls_promo[i][j] != 1:
      ls_flag_vs_amount.append((i,j))
ls_flag_vs_vignette = []
for i, ls_vignettes in enumerate(ls_ls_vignettes):
  for j, vignette in enumerate(ls_vignettes):
    if vignette and vignette != u'' and ls_ls_promo[i][j] != 1:
      ls_flag_vs_vignette.append((i,j))

# #########################
# DESC. STATS ON PROMO 
# #########################

# todo: Clean text: dpt/sub-dpt/products...
dict_panel_data_master = {}
list_formatted_dates = ['%s/%s/%s' %(elt[:4], elt[4:6], elt[6:]) for elt in master['ls_dates']]
index_formatted_dates = pd.to_datetime(list_formatted_dates)
for i, id in enumerate(master['ls_ids']):
  ls_prices = master['ls_ls_prices'][i]
  ls_unit_prices = master['ls_ls_dates'][i]
  ls_promo = ls_ls_promo[i]
  ls_vignette = ls_ls_vignettes[i]
  ls_amount = ls_ls_amounts[i]
  ls_type = ls_ls_types[i]
  dict_product = {'ls_price' : np.array(ls_prices, dtype = np.float32),
                  'ls_unit_price' : np.array(ls_unit_prices, dtype = np.float32),
                  'ls_promo' : ls_promo,
                  'ls_vignette' : ls_vignette,
                  'ls_amount' : ls_amount,
                  'ls_type' : ls_type,
                  'dpt' : master['dict_info'][id]['department'][0][0][0],
                  'subdpt' : master['dict_info'][id]['sub_department'][0][0][0]}
  dict_panel_data_master[id] = pd.DataFrame(dict_product, index = index_formatted_dates)
pd_pd_master = pd.Panel(dict_panel_data_master)
pd_df_price = pd_pd_master.minor_xs('ls_price')

# todo: check why data type is lost when taking minor_xs etc.
# todo: check work with multiindex vs panel

# Promo in a given period
pd_df_promo_period = pd_pd_master.major_xs('2012-11-22')
pd_df_promo_period = pd_df_promo_period.T

print u'\nNb of promoted products (at least once):'
print len(pd_df_promo_period[pd_df_promo_period['ls_promo']==1])

print u'\nNb of promoted products (at least once) by dpt (top 20):'
print pd_df_promo_period['dpt'][pd_df_promo_period['ls_promo']==1].value_counts()

print u'\nNb of promoted products (at least once) by subdpt (top 20):'
print pd_df_promo_period['subdpt'][pd_df_promo_period['ls_promo']==1].value_counts()[0:20]

pd.set_option('display.max_columns', 10)
pd.set_option('display.width', 200)
#pd_df_promo_period = pd_df_promo_period[['dpt', 'subdpt','ls_promo']]
#print pd_df_promo_period[pd_df_promo_period['ls_promo']==1].\
#  sort(columns = ['dpt', 'subdpt']).to_string()

# Summary: nb of products by dpt over time
ls_df_dpt_products = []
for date_ind in pd_df_price.index:
  pd_df_period = pd_pd_master.major_xs(date_ind).T
  pd_df_period['ls_price'] = pd_df_period['ls_price'].astype(np.float32)
  ls_df_dpt_products.append(pd_df_period['dpt']\
                              [~np.isnan(pd_df_period['ls_price'])].value_counts())
pd_df_all_dpt_products = pd.concat(ls_df_dpt_products,
                                   axis=1,
                                   keys = pd_df_price.index).T
#pd_df_all_dpt_products.plot()
#plt.show()

# Summary: nb of products by subdpt over time
ls_df_subdpt_products = []
for date_ind in pd_df_price.index:
  pd_df_period = pd_pd_master.major_xs(date_ind).T
  pd_df_period['ls_price'] = pd_df_period['ls_price'].astype(np.float32)
  ls_df_subdpt_products.append(pd_df_period['subdpt']\
                                 [~np.isnan(pd_df_period['ls_price'])].value_counts())
pd_df_all_subdpt_products = pd.concat(ls_df_subdpt_products,
                                      axis=1,
                                      keys = pd_df_price.index).T
#pd_df_all_subdpt_products.plot()
#plt.show()

# Summary: nb of promo by dpt over time and display
ls_df_dpt_promo = []
for date_ind in pd_df_price.index:
  pd_df_period = pd_pd_master.major_xs(date_ind).T
  ls_df_dpt_promo.append(pd_df_period['dpt'][pd_df_period['ls_promo']==1].value_counts())
pd_df_all_dpt_promo = pd.concat(ls_df_dpt_promo, axis =1, keys = pd_df_price.index).T
#print pd_df_all_dpt_promo.to_string()
#pd_df_all_dpt_promo[[u'Produits Frais', u'boissons', u'épicerie',
#                     u'Surgelés',u'Fruits & Légumes']].plot()
#plt.show()
#pd_df_all_dpt_promo[[u'Bébé', u'Entretien', u'Hygiène & Beauté']].plot()
#plt.show()
#pd_df_all_dpt_promo.sum(axis=1).plot()
#plt.show()

# Summary: nb of promo by subdpt over time (long to build and rather useless)
ls_df_subdpt_promo = []
for date_ind in pd_df_price.index:
  pd_df_period = pd_pd_master.major_xs(date_ind).T
  ls_df_subdpt_promo.append(pd_df_period['subdpt'][pd_df_period['ls_promo']==1].value_counts())
pd_df_all_subdpt_promo = pd.concat(ls_df_subdpt_promo,
                                   axis =1,
                                   keys = pd_df_price.index).T
pd_df_all_subdpt_promo_sum = pd_df_all_subdpt_promo.sum()
pd_df_all_subdpt_promo_sum.sort(ascending=False)

print '\nNb of promo-day by subdpt'
print pd_df_all_subdpt_promo_sum[0:10]

pd_promo_percent = pd_df_all_subdpt_promo.sum()/pd_df_all_subdpt_products.sum()
pd_recap = pd.concat([pd_promo_percent,
                      pd_df_all_subdpt_promo.sum(),
                      pd_df_all_subdpt_products.sum()],axis=1, join='outer',
                     keys = ['percent', 'promo', 'tot'])

# ##################################
# SALES: TYPE/LENGTH/AMOUNT/PERIODS
# ##################################

ls_start_end, ls_none, ls_ls_dilettante = analyse_price_series(master['ls_ls_prices'], master)

# todo: type of sales, length of sales, significance of sales by dpt/subdpt
ls_ls_promo_nogap = [[1 if angle == u'angle flag_promo' else 0 for angle in ls_angles]\
                       for ls_angles in ls_ls_angles]
ls_ls_vignettes_nogap = [get_field_as_list(product, 'product_promo_vignette', master)\
                           for product in master['ls_ids']]
ls_ls_amounts_nogap = [get_field_as_list(product, 'product_promo_amount', master)\
                         for product in master['ls_ids']]

# 1/ Promo in terms of amount / types

# Make sure promo not counted while product no more reported (check if actually necessary)
# Take into account fact that promo may be censored
ls_ls_promo_durations = []
for i, ls_amounts in enumerate(ls_ls_amounts_nogap):
  ls_amounts = ls_amounts[:ls_start_end[i][1]+1]
  ls_promo_durations = []
  for group in itertools.groupby(iter(range(len(ls_amounts))),
                                 lambda x: ls_amounts[x]):
    ls_promo_durations.append((group[0], list(group[1])))
  ls_promo_durations = [(promo, ls_days) for (promo, ls_days)\
                          in ls_promo_durations if promo and promo != u'0']
  ls_ls_promo_durations.append(ls_promo_durations)

ls_ls_promo_amount_master = []
for i, ls_promo_duration in enumerate(ls_ls_promo_durations):
  ls_temp = []
  if ls_promo_duration:
    for (amount, ls_days) in ls_promo_duration:
      if ls_ls_types[i][ls_days[0]] == u'%':
        ls_temp.append(('percent',
                        float(amount)/100,
                        float(amount)/100*float(master['ls_ls_prices'][i][ls_days[0]]),
                        ls_days))
      elif ls_ls_types[i][ls_days[0]] == u'&euro;':
        ls_temp.append(('amount',
                        float(amount)/float(master['ls_ls_prices'][i][ls_days[0]]),
                        float(amount),
                        ls_days))
      else:
        print 'pbm', i
  ls_ls_promo_amount_master.append(ls_temp)

# todo: stats desc: length of sales (conditional on non censored), nb of sales, amount

# 2/ Vignettes
# Reminder: all occurences in dict_promo_vignette

ls_ls_promo_durations_2 = []
for i, ls_vignettes in enumerate(ls_ls_vignettes_nogap):
  ls_vignettes = ls_vignettes[:ls_start_end[i][1]+1]
  ls_promo_durations_2 = []
  for group in itertools.groupby(iter(range(len(ls_vignettes))), lambda x: ls_vignettes[x]):
    ls_promo_durations_2.append((group[0], list(group[1])))
  ls_promo_durations_2 = [(promo, ls_days) for (promo, ls_days)\
                            in ls_promo_durations_2 if promo]
  ls_ls_promo_durations_2.append(ls_promo_durations_2)

# todo: stats desc: length of sales (conditional on non censored), nb of sales, amount
# todo: distinguish: "remise", "=", "cagnott",n

# ############################
# Price variations (not sales)
# ############################

# todo: deal with gaps (some None in series: product non available...)

# Preliminary: nb price occurences per product
ls_ls_price_occurences = []
dict_nb_price_occurences = {}
for i, ls_prices in enumerate(master['ls_ls_prices']):
  ls_unique_prices = [price for price in list(set(ls_prices)) if price]
  ls_ls_price_occurences.append(ls_unique_prices)
  dict_nb_price_occurences.setdefault(len(ls_unique_prices), []).append(i)

print '\nNb products by nb of different prices:'
for k,v in dict_nb_price_occurences.iteritems():
  print k, len(v)

# todo: fill gaps...
# todo: distinguish those associated with sales vs. other

# todo: fill gaps if length < 5 (?) and prices before/after are equal 
# (product not available at drive but..)
# todo: gaps not filled: price durations before/after not very reliable
# (minor mistake overall?)

# todo: function to analyse price series: beginning, end, nb of prices, durations, chges
# todo: on one line by subdpt/dpt: nb items, nb sales, nb full spell, nb price chges
