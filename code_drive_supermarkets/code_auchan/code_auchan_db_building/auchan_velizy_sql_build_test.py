import os
import json
import sqlite3
from datetime import date, timedelta
import datetime
import numpy as np

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
# structure of the data folder should be the same
folder_source_auchan_velizy_prices = r'\data_drive_supermarkets\data_auchan\data_source\data_json_auchan_velizy'
folder_built_auchan_velizy_sql = r'\data_drive_supermarkets\data_auchan\data_built\data_sql_auchan_velizy'

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

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
# Load json file
# #####################

#date = '20121210'
#master_dict = dec_json(path_data + folder_source_auchan_velizy_prices + r'\%s_auchan_velizy' %date)
master_dict = dec_json(path_data + folder_source_auchan_velizy_prices + r'\new_auchan_velizy_test_2')

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

# #####################
# Master formating
# #####################

for product in master_dict:
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

master_list = []
for product in master_dict:
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
                      product['available']])

conn = sqlite3.connect(path_data + folder_built_auchan_velizy_sql +r'\auchan_velizy_sql_test.db')
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
                                            available TEXT)")
cursor.executemany("INSERT INTO auchan_velizy VALUES (?,?,?,?,?,?,?,?,?,?,?)", master_list)
conn.commit()

list_department = []
for row in cursor.execute("SELECT DISTINCT department FROM auchan_velizy"):
  list_department.append(row[0])

list_sub_department = []
for row in cursor.execute("SELECT DISTINCT sub_department FROM auchan_velizy"):
  list_sub_department.append(row[0])

list_products = []
for row in cursor.execute("SELECT DISTINCT product_title FROM auchan_velizy"):
  list_products.append(row[0])

list_duplicates = []
for row in cursor.execute("SELECT x.product_title, x.sub_department FROM auchan_velizy x\
                           WHERE EXISTS(SELECT NULL FROM auchan_velizy t\
                                        WHERE t.product_title = x.product_title\
                                        GROUP BY t.product_title\
                                        HAVING COUNT(*) > 1)\
                           ORDER BY x.product_title"):
  list_duplicates.append(row)

list_all_info_cond = []
where_condition = (u'Sirops et concentr\xe9s',)
for row in cursor.execute("SELECT * FROM auchan_velizy WHERE sub_department = ?", where_condition):
  list_all_info_cond.append(row)

list_prices_cond = []
where_condition = (u'Sirops et concentr\xe9s',)
for row in cursor.execute("SELECT product_total_price FROM auchan_velizy WHERE sub_department = ?", where_condition):
  list_prices_cond.append(row[0])