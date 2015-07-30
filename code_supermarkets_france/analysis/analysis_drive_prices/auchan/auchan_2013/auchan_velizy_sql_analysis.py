#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
import json
import sqlite3
from datetime import date, timedelta
import datetime
import numpy as np
import numpy.ma as ma
import matplotlib.pyplot as plt
import pprint
from collections import Counter

path_auchan = os.path.join(path_data,
                           u'data_drive_supermarkets',
                           u'data_auchan')

path_built_sql = os.path.join(path_auchan,
                              u'data_built',
                              u'data_sql_auchan_velizy')

def dec_json(file_path):
  """Reads a json file."""
  with open(file_path, 'r') as file:
    return json.loads(file.read())

def enc_json(file_to_encode, file_path):
  """Saves a file in json."""
  with open(file_path, 'w') as file:
    json.dump(file_to_encode, file)

def get_relative_frequency(dict_absolute_frequency):
  """Return relative frequency in dict"""
  nb_observations = 0
  for k, v in dict_absolute_frequency.iteritems():
    nb_observations += v
  dict_relative_frequency = {}
  for k, v in dict_absolute_frequency.iteritems():
    dict_relative_frequency[k] = np.round([v/float(nb_observations)],
                                          decimals = 2) # need [] else does not work
  return dict_relative_frequency

# TODO: fix period

# ###############################
# LOAD SQL DATABASE AND DESCRIBE
# ###############################

conn = sqlite3.connect(os.path.join(path_built_sql, 
                                    u'auchan_velizy_sql.db'))
cursor = conn.cursor()

# see tables in sql master
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print 'Tables in sql database', cursor.fetchall()

# see column infos of a table
cursor.execute("PRAGMA table_info(auchan_velizy)")
print 'Columns in table:', cursor.fetchall()

# see number of records in a table
cursor.execute("SELECT COUNT(*) FROM auchan_velizy")
print 'Nb of records in table:', cursor.fetchall()[0][0]

# ###############
# DUPLICATE ISSUE
# ###############

# todo:
# Numerous (unjustified) duplicates until script changed on april 11, 2013 (not in db so far)
# Since then, duplicates are products that are listed twice or more by auchan (legit)
# Deal with products belonging to different dpts/sub-depts using clean date data
# Check how many doubles this leaves (can be dealt with manually?)
# Not easy for products which are no more listed as of april 11, 2013

## For now assume period 50 is date of script change but april 11 not in the db (too small)
## "INNER JOIN" is intersection
## Could/Should include records where products not present in the second half thereafter
## Seems very slow (even though the SELECT request is fast enough... weird?)
## Could replace CREATE TABLE by SELECT INTO
#cursor.execute("CREATE TABLE auchan_velizy_test AS\
#                            SELECT * FROM auchan_velizy table1 INNER JOIN \
#                                  (SELECT product_title, sub_department FROM \
#                                     auchan_velizy WHERE period >= 50) table2 \
#                             ON table1.product_title = table2.product_title \
#                                AND table1.sub_department = table2.sub_department")

# ###############
# PRICE ANALYSIS
# ###############

list_sub_departments = [row[0] for row\
                          in cursor.execute("SELECT DISTINCT sub_department \
                                               FROM auchan_velizy")]
list_products = [row[0] for row\
                   in cursor.execute("SELECT DISTINCT product_title \
                                        FROM auchan_velizy")]

where_condition = (list_products[0],)
# get the prices at all (available) periods of a given product (avoids duplicates, slow)
list_prices_cond = [row for row\
                      in cursor.execute("SELECT product_total_price, period FROM auchan_velizy \
                                           WHERE product_title = ? AND rowid IN \
												                     (SELECT MIN(rowid) FROM auchan_velizy t \
												                      GROUP BY product_title, period)",
                                        where_condition)]

# alternative, seems faster (?)
list_prices_cond_2 = [row for row\
                        in cursor.execute("SELECT DISTINCT product_total_price, period \
                                             FROM auchan_velizy WHERE product_title = ? \
                                               ORDER BY MAX(period) ASC",
                                          where_condition)]

# COMPUTE PRICE STATS WITHIN A DPT/SUBDPT (3 STEPS)
# 1/ extract prices 
dict_stats_des = {}
for sub_department in list_sub_departments[0:1]:
  cond_sub_department = (sub_department,)
  list_products_cond = [row[0] for row\
                          in cursor.execute("SELECT DISTINCT product_title \
                                             FROM auchan_velizy \
                                             WHERE sub_department = ? ",
                                            cond_sub_department)]
  list_list_prices_cond = []
  for product in list_products_cond:
    prod_condition = (product,)
    list_prices_cond_temp = [row for row\
                               in cursor.execute("SELECT DISTINCT product_total_price, period\
                                                  FROM auchan_velizy WHERE product_title = ?\
                                                  ORDER BY period ASC",
                                                 prod_condition)]
    list_list_prices_cond.append(list_prices_cond_temp)
  # 2/ create price arrays: fills with np.nan when period price is missing
  # TODO : try to improve performance
  list_price_series = []
  for list_product_prices in list_list_prices_cond:
    dico_period_prices = {}
    for (price, period) in list_product_prices:
      dico_period_prices[period] = price
    price_series = [dico_period_prices.get(i, np.nan) for i in range(104)] # must give nb of periods
    list_price_series.append(price_series)
  # 3/ compute price stats
  dict_price_stats = {'ls_means':[],
                      'ls_ranges':[],
                      'ls_nb_changes':[],
                      'ls_mean_change_abs':[]}
  for price_series in list_price_series:
    # TODO: exclude price_series where too many values are missing
    price_changes_series = np.array(price_series[1:]) - np.array(price_series[:-1])
    price_changes_series_abs = np.abs(price_changes_series)
    price_series = ma.masked_invalid(price_series)
    price_changes_series_abs = ma.masked_invalid(ma.masked_invalid(price_changes_series_abs))
    dict_price_stats['ls_means'].append(np.mean(price_series))
    dict_price_stats['ls_ranges'].append(np.max(price_series)-np.min(price_series))
    dict_price_stats['ls_nb_changes'].append(\
        len(price_changes_series_abs[price_changes_series_abs>0]))
    dict_price_stats['ls_mean_change_abs'].append(\
        np.mean(price_changes_series_abs[price_changes_series_abs>0]))
  dict_stats_des[sub_department] = dict_price_stats
  # print sub_department
  # pprint.pprint(get_relative_frequency(dict(Counter(dict_price_stats['list_nb_changes']))))

# todo:
# Split stat des work betweek SQL/Python
# Global stats on price last digits, price change timing/frequency/magnitude
# Graph price series of volatile prices (withing subdpt or dpt first...)
# Account for price changes: brand, product characteristics... etc (to be created: regex etc.)

## ALTERNATIVELY FOR 1/ AND 2/
## get list of (title, price, period) tuples ranked in title, period ascending order (on sub_dpt_cond)
#list_products_periods = [row for row\
#    in cursor.execute("SELECT DISTINCT product_title, product_total_price, period\
#                         FROM auchan_velizy WHERE product_title IN\
#                         (SELECT product_title FROM auchan_velizy \
#                          WHERE sub_department = ?)\
#                         ORDER BY product_title, period ASC", cond_sub_department)]
## generate list of product titles and price lists directly
## if product disappears, product price list is shorter (thus does not require assumed length)
#list_product_titles = []
#list_list_product_prices = []
#for (title, price, period) in list_products_periods:
#  if title not in list_product_titles:
#    if list_product_titles:
#      list_list_product_prices.append(list_product_prices)
#    list_product_titles.append(title)
#    list_product_prices = []
#    while period > len(list_product_prices):
#      list_product_prices.append(np.nan)
#    list_product_prices.append(price)
#  else:
#    while period > len(list_product_prices):
#      list_product_prices.append(np.nan)
#    list_product_prices.append(price)
#list_list_product_prices.append(list_product_prices)# last product price list must be added

## DEPRECATED OR REMINDERS
## SQL REMINDER
## get distinct values of a column
#list_products = []
#for row in cursor.execute("SELECT DISTINCT product_title FROM auchan_velizy"):
#  list_products.append(row[0])
## count distinct values in a column
#cursor.execute("SELECT COUNT(DISTINCT product_title) FROM auchan_velizy")
#print cursor.fetchall()[0][0]
#
#list_duplicates_2 = []
#for row in cursor.execute("SELECT x.product_title, x.sub_department FROM auchan_velizy x\
#                           WHERE EXISTS(SELECT NULL FROM auchan_velizy t\
#                                        WHERE t.product_title = x.product_title\
#                                        AND t.period = x.period\
#                                        GROUP BY t.product_title\
#                                        HAVING COUNT(*) > 1)\
#                           ORDER BY x.product_title"):
#  list_duplicates_2.append(row)
#
#list_duplicates = []
#for row in cursor.execute("SELECT product_title, sub_department, \
#                             COUNT(product_title) AS NumOccurrences FROM auchan_velizy \
#                             GROUP BY product_title, sub_department HAVING (COUNT(product_title) > 1)"):
#  list_duplicates.append(row)
