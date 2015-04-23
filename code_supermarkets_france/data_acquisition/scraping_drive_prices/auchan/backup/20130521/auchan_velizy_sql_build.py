import os
import json
import sqlite3
import datetime
from datetime import date, timedelta
import numpy as np
import matplotlib.pyplot as plt
import numpy.ma as ma

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

path = r'C:\Users\etna\Desktop\Code\Auchan'
# path = r'\\ulysse\users\echamayou\Etienne\Python_mydocs\Scrapping_Auchan'
json_folder = r'\auchan_velizy_json'
sql_folder = r'\auchan_velizy_sql'

def date_range(start_date, end_date):
  """
  creates a list of dates based on its arguments (beginning and end dates)
  """
  list_dates = []
  for n in range((end_date + timedelta(1) - start_date).days):
    temp_date = start_date + timedelta(n)
    list_dates.append(temp_date.strftime('%Y%m%d'))
  return list_dates

def explore_key(list_of_dicts, key):
  """
  problem: some fields are lists and still contain html code... extract info in clean way
  may add a field for price units... (Prix/K, Prix/L etc)
  """
  dict_len = {}
  list_lists_unique = []
  for dict_obs in list_of_dicts:
    if len(dict_obs[key]) not in dict_len.keys():
      dict_len[len(dict_obs[key])] = 1
      list_lists_unique.append([])
    else:
      dict_len[len(dict_obs[key])] +=1
    while len(list_lists_unique) < len(dict_obs[key]):
      list_lists_unique.append([])
    for i in range(len(dict_obs[key])):
      if dict_obs[key][i] not in list_lists_unique[i]:
        list_lists_unique[i].append(dict_obs[key][i])
  return [dict_len, list_lists_unique]

# #####################
# Load json files
# #####################

# an example
date_ex = '20121210'
master_dict = dec_json(path + json_folder + r'\%s_auchan_velizy' %date_ex)

# loading all json files
master = []
start_date = date(2013,1,7)
end_date = date(2013,4,11)
master_dates = date_range(start_date, end_date)
for date_str in master_dates:
  day_count = master_dates.index(date_str)
  if os.path.exists(path + json_folder + r'\%s_auchan_velizy' %date_str):
    temp_period_master = dec_json(path + json_folder + r'\%s_auchan_velizy' %date_str)
    # not sure this step will be useful
    for temp_product in temp_period_master:
      temp_product['day'] = day_count
    master.append(temp_period_master)
  else:
    print date_str, 'is not available'

# #####################
# Check field contents
# #####################

product_title = explore_key(master_dict, 'product_title')
# product_title = always length 1
product_total_price = explore_key(master_dict, 'product_total_price')
# always length 2, int + decimals... unite
product_unit_price = explore_key(master_dict, 'product_unit_price')
# always lenth 3, drop middle => create unit column
product_promo = explore_key(master_dict, 'product_promo')
# length 0 or 2, beware: can be a % reduction or the price in euro => create column promo type
product_promo_vignette = explore_key(master_dict, 'product_promo_vignette')
# length 0 or 1, beware: can be a % reduction or the price in euro => create column promo type

#TODO: for i, e in enumerate(master):
for i in range(len(master)):
  product_title = explore_key(master[i], 'product_title')
  product_total_price = explore_key(master[i], 'product_total_price')
  product_unit_price = explore_key(master[i], 'product_unit_price')
  product_promo = explore_key(master[i], 'product_promo')
  product_promo_vignette = explore_key(master[i], 'product_promo_vignette')
  if product_title[0].keys() != [1] or \
     product_total_price[0].keys() != [2] or \
     product_unit_price[0].keys() !=  [3] or \
     product_promo[0].keys() != [0,2] or \
     product_promo_vignette[0].keys() != [0,1]:
       print 'Problem with field contents at period', i
# This is a preliminary version: should be able to compare results across periods (e.g. price units)

# #####################
# Master formating
# #####################

master_list = []
for i in range(len(master)):
  for product in master[i]:
    # format fields
    product['product_total_price'] = ''.join(product['product_total_price']).replace('<sub>','').replace('<span>&euro;</span></sub>','').replace(',','.')
    product['price_unit'] = product['product_unit_price'][0]
    product['product_unit_price'] = product['product_unit_price'][2].replace('&euro;','').replace(',','.')
    product['product_title'] = product['product_title'][0]
    if len(product['product_promo']) == 0:
      product['product_promo_amount'] = '0'
      product['product_promo_type'] = ''
    else:
      product['product_promo_amount'] = product['product_promo'][0].replace(',','.')
      product['product_promo_type'] = product['product_promo'][1]
    del product['product_promo']
    if len(product['product_promo_vignette']) == 0:
      product['product_promo_vignette'] = ''
    else:
      product['product_promo_vignette'] = product['product_promo_vignette'][0]
    # create list of list for sql conversion
    master_list.append([product['department'],
                      product['sub_department'],
                      product['product_title'],
                      float(product['product_total_price']),
                      float(product['product_unit_price']),
                      product['price_unit'],
                      product['product_flag'],
                      float(product['product_promo_amount']),
                      product['product_promo_type'],
                      product['product_promo_vignette'],
                      product['available'],
                      i])

conn = sqlite3.connect(path + sql_folder +r'\auchan_velizy_sql.db')
cursor = conn.cursor()
cursor.execute("DROP TABLE IF EXISTS auchan_velizy")
cursor.execute("CREATE TABLE auchan_velizy (department TEXT,\
                                            sub_department TEXT,\
                                            product_title TEXT,\
                                            product_total_price REAL,\
                                            product_unit_price REAL,\
                                            price_unit TEXT,\
                                            product_flag TEXT,\
                                            product_promo_amount REAL,\
                                            product_promo_type TEXT,\
                                            product_promo_vignette TEXT,\
                                            available TEXT,\
                                            period INTEGER)")
cursor.executemany("INSERT INTO auchan_velizy VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", master_list)
cursor.execute("CREATE INDEX ProdPer ON auchan_velizy (product_title, period)")
conn.commit()

# Analysis:
# To be moved to another script

list_sub_departments = [row[0] for row in cursor.execute("SELECT DISTINCT sub_department FROM auchan_velizy")]
list_products = [row[0] for row in cursor.execute("SELECT DISTINCT product_title FROM auchan_velizy")]

where_condition = (list_products[0],)

# get the prices at all (available) periods of a given product (avoids duplicates)
list_prices_cond = []
for row in cursor.execute("SELECT product_total_price, period FROM auchan_velizy WHERE product_title = ?\
                           AND rowid IN (SELECT MIN(rowid) FROM auchan_velizy t GROUP BY product_title, period)", where_condition):
  list_prices_cond.append(row)

# alternative, seems faster (?)
list_prices_cond_2 = [row for row in cursor.execute("SELECT DISTINCT product_total_price, period FROM auchan_velizy WHERE product_title = ? ORDER BY period ASC", where_condition)]

# loop on product of a department/sub-department
# compute range, number of changes, min increase, max increase
list_products_cond = []
cond_sub_department = (list_sub_departments[9],)
for row in cursor.execute("SELECT DISTINCT product_title FROM auchan_velizy WHERE sub_department = ? ", cond_sub_department):
  list_products_cond.append(row[0])
list_list_prices_cond = []
for elt in list_products_cond:
  prod_condition = (elt,)
  list_prices_cond_temp = []
  for row in cursor.execute("SELECT DISTINCT product_total_price, period FROM auchan_velizy WHERE product_title = ? ORDER BY period ASC", prod_condition):
    list_prices_cond_temp.append(row)
  list_list_prices_cond.append(list_prices_cond_temp)

period_length = len(master_dates)

list_price_series = []
for list_product_prices in list_list_prices_cond:
  dico_period_prices = {}
  for price, period in list_product_prices:
    dico_period_prices[period] = price
  price_series = []
  for i in range(period_length):
    price_series.append(dico_period_prices.get(i, np.nan))
  list_price_series.append(price_series)

dict_price_stats = {'list_means':[], 'list_ranges':[], 'list_nb_changes':[], 'list_mean_change_abs':[]}
for price_series in list_price_series:
  # add: exlude price_series where too many values are missing
  price_changes_series = np.array(price_series[1:]) - np.array(price_series[:-1])
  price_changes_series_abs = np.abs(price_changes_series)
  price_series = ma.masked_invalid(price_series)
  price_changes_series_abs = ma.masked_invalid(price_changes_series_abs)
  dict_price_stats['list_means'].append(np.mean(price_series))
  dict_price_stats['list_ranges'].append(np.max(price_series)-np.min(price_series))
  dict_price_stats['list_nb_changes'].append(len(price_changes_series_abs[price_changes_series_abs>0]))
  dict_price_stats['list_mean_change_abs'].append(np.mean(price_changes_series_abs[price_changes_series_abs>0]))

"""
# was used to analyse duplicates... since script change on april 10 or 11 (2013), should be essentially correct
# correct means that duplicates are products that are listed twice or more by auchan... not a script error
list_duplicates = []
for row in cursor.execute("SELECT x.product_title, x.sub_department FROM auchan_velizy x\
                           WHERE EXISTS(SELECT NULL FROM auchan_velizy t\
                                        WHERE t.product_title = x.product_title\
                                        GROUP BY t.product_title\
                                        HAVING COUNT(*) > 1)\
                           ORDER BY x.product_title"):
  list_duplicates.append(row)
"""