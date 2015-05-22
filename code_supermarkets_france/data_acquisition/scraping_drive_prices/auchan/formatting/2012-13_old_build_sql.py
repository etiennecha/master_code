#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
import json
import sqlite3
import datetime
from datetime import date, timedelta
#import gc

path_auchan = os.path.join(path_data,
                           u'data_drive_supermarkets',
                           u'data_auchan')

path_price_source = os.path.join(path_auchan,
                                 u'data_source',
                                 u'data_json_auchan_velizy')

path_built_sql = os.path.join(path_auchan,
                              u'data_built',
                              u'data_sql_auchan_velizy')

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def date_range(start_date, end_date):
  """
  creates a list of dates based on its arguments (beginning and end dates)
  """
  ls_dates = []
  for n in range((end_date + timedelta(1) - start_date).days):
    temp_date = start_date + timedelta(n)
    ls_dates.append(temp_date.strftime('%Y%m%d'))
  return ls_dates

def explore_key(ls_dict_product, field):
  """
  analysis of fields which are lists (still contain html btw)
  """
  dict_len = {}
  ls_ls_unique = []
  for dict_product in ls_dict_product:
    # Get all product content lengths for this field
    if len(dict_product[field]) not in dict_len.keys():
      dict_len[len(dict_product[field])] = 1
      ls_ls_unique.append([])
    else:
      dict_len[len(dict_product[field])] +=1
    # Get all unique product contents by position for this field
    while len(ls_ls_unique) < len(dict_product[field]):
      ls_ls_unique.append([])
    for i, elt in enumerate(dict_product[field]):
      if elt not in ls_ls_unique[i]:
        ls_ls_unique[i].append(elt)
  return [dict_len, ls_ls_unique]

# ##############
# Check one file
# ##############

date_str = '20121210'
path_file = os.path.join(path_price_source,
                         u'{:s}_auchan_velizy'.format(date_str))
ls_products_ex = dec_json(path_file)

product_title_ex = explore_key(ls_products_ex, 'product_title')
# product_title = always len 1
product_total_price_ex = explore_key(ls_products_ex, 'product_total_price')
# always len 2, int + decimals... unite
product_unit_price_ex = explore_key(ls_products_ex, 'product_unit_price')
# always len 3, drop middle => create unit column
product_promo_ex = explore_key(ls_products_ex, 'product_promo')
# len 0 or 2, beware: % reduction or price in euro => create col promo type
product_promo_vignette_ex = explore_key(ls_products_ex, 'product_promo_vignette')
# len 0 or 1, beware: % reduction or price in euro => create col promo type vig.

# #####################
# Load json files
# #####################

# LOAD ALL JSON FILES
start_date = date(2013, 1, 7)
end_date = date(2013, 2, 7) # was (2013, 4, 20)
ls_dates = date_range(start_date, end_date)
ls_ls_products = []
for day_count, date_str in enumerate(ls_dates):
  path_file = os.path.join(path_price_source,
                           u'{:s}_auchan_velizy'.format(date_str))
  if os.path.exists(path_file):
    ls_products = dec_json(path_file)
    for product in ls_products:
      product['day'] = day_count
    ls_ls_products.append(ls_products)
  else:
    print '{:s} not found'.format(path_file)

# Explore fields (todo: update)
ls_fields = [u'product_title',
            u'product_total_price',
            u'product_unit_price',
            u'product_promo',
            u'product_promo_vignette']
ls_dict_fields = []
for i, ls_products in enumerate(ls_ls_products):
  dict_fields = {}
  for field in ls_fields:
    dict_fields[field] = explore_key(ls_products, field)
  ls_dict_fields.append(dict_fields)
  if dict_fields['product_title'][0].keys() != [1] or \
     dict_fields['product_total_price'][0].keys() != [2] or \
     dict_fields['product_unit_price'][0].keys() !=  [3] or \
     dict_fields['product_promo'][0].keys() != [0,2] or \
     dict_fields['product_promo_vignette'][0].keys() != [0,1]:
       print 'Problem with field contents at period', i

# #####################
# Master formating
# #####################

ls_rows = []
for ls_products in ls_ls_products:
  for product in ls_products:
    # format fields
    product['product_total_price'] = ''.join(product['product_total_price']).\
                                               replace('<sub>','').\
                                               replace('<span>&euro;</span></sub>','').\
                                               replace(',','.')
    product['price_unit'] = product['product_unit_price'][0]
    product['product_unit_price'] = product['product_unit_price'][2].\
                                      replace('&euro;','').\
                                      replace(',','.')
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
    ls_rows.append([product['department'],
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
                    ls_dates[product['day']]])

# ##############
# OUTPUT TO SQL
# ##############

conn = sqlite3.connect(os.path.join(path_built_sql, 
                                    u'auchan_velizy_sql.db'))
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
cursor.executemany("INSERT INTO auchan_velizy VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", ls_rows)
cursor.execute("CREATE INDEX ProdPer ON auchan_velizy (product_title, period)")
conn.commit()

# #################
# SQL QUERIES
# #################

ls_department = []
for row in cursor.execute("SELECT DISTINCT department FROM auchan_velizy"):
  ls_department.append(row[0])

ls_sub_department = []
for row in cursor.execute("SELECT DISTINCT sub_department FROM auchan_velizy"):
  ls_sub_department.append(row[0])

ls_products = []
for row in cursor.execute("SELECT DISTINCT product_title FROM auchan_velizy"):
  ls_products.append(row[0])

ls_duplicates = []
for row in cursor.execute("SELECT x.product_title, x.sub_department FROM auchan_velizy x\
                           WHERE EXISTS(SELECT NULL FROM auchan_velizy t\
                                        WHERE t.product_title = x.product_title\
                                        GROUP BY t.product_title\
                                        HAVING COUNT(*) > 1)\
                           ORDER BY x.product_title"):
  ls_duplicates.append(row)

ls_all_info_cond = []
where_condition = (u'Sirops et concentr\xe9s',)
for row in cursor.execute("SELECT * FROM auchan_velizy WHERE sub_department = ?",
                          where_condition):
  ls_all_info_cond.append(row)

ls_prices_cond = []
where_condition = (u'Sirops et concentr\xe9s',)
for row in cursor.execute("SELECT product_total_price\
                           FROM auchan_velizy WHERE sub_department = ?",
                          where_condition):
  ls_prices_cond.append(row[0])

conn.close()
