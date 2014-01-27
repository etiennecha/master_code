import os
import json
import sqlite3
from datetime import date, timedelta
import datetime

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

path = r'C:\Users\etna\Desktop\Code\Auchan'
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

start_date = date(2013,1,7)
end_date = date(2013,4,9)
master_dates = date_range(start_date, end_date) 
master = []

for date in master_dates:
  day_count = master_dates.index(date)
  if os.path.exists(path + json_folder + r'\%s_auchan_velizy' %date):
    temp_period_master = dec_json(path + json_folder + r'\%s_auchan_velizy' %date)
    # not sure this step will be useful
    for temp_product in temp_period_master:
      temp_product['day'] = day_count
    master.append(temp_period_master)
  else:
    print date, 'is not available'

date = '20121210'
master_dict = dec_json(path + json_folder + r'\%s_auchan_velizy' %date)

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

"""
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
                                            available TEXT)")
cursor.executemany("INSERT INTO auchan_velizy VALUES (?,?,?,?,?,?,?,?,?,?,?)", master_list)
conn.commit()

list_products = []
for row in cursor.execute("SELECT DISTINCT product_title FROM auchan_velizy"):
  list_products.append(row[0])

list_duplicates = []
for row in cursor.execute("SELECT product_title, sub_department, COUNT(product_title) AS NumOccurrences FROM auchan_velizy GROUP BY product_title, sub_department HAVING (COUNT(product_title) > 1)"):
  list_duplicates.append(row)

list_duplicates_2 = []
for row in cursor.execute("SELECT x.product_title, x.sub_department FROM auchan_velizy x\
                           WHERE EXISTS(SELECT NULL FROM auchan_velizy t\
                                        WHERE t.product_title = x.product_title\
                                        GROUP BY t.product_title\
                                        HAVING COUNT(*) > 1)\
                           ORDER BY x.product_title"):
  list_duplicates_2.append(row)
"""