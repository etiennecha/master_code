#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *

path_auchan = os.path.join(path_data,
                           u'data_drive_supermarkets',
                           u'data_auchan')

path_price_json_auchan = os.path.join(path_auchan,
                                      u'data_source',
                                      u'data_json_auchan')

# or directly to built if can be formatted easily?
path_price_source_csv = os.path.join(path_auchan,
                                     u'data_source',
                                     u'data_csv_auchan')

# ################
# CHECK ONE FILE
# ################

date_str = '20150506'
path_file = os.path.join(path_price_json_auchan,
                         '{:s}_dict_auchan'.format(date_str))
dict_period = dec_json(path_file)

# Check fields for each product (with stats)
dict_fields = {}
for store, ls_dict_stores in dict_period.items():
  for dict_product in ls_dict_stores:
    for product_key in dict_product.keys():
      dict_fields.setdefault(product_key, []).append(dict_product.get('product_title',
                                                                    None))
for k,v in dict_fields.items():
  print k, len(v)

ls_fields = dict_fields.keys()

# ##################
# BUILD DF MASTER
# ##################

# Need to consider period with same fields
ls_fields = dict_fields.keys()
start_date = date(2015,5,6)
end_date = date(2015,5,18)
ls_dates = get_date_range(start_date, end_date)
ls_df_products = []
for date_str in ls_dates:
  path_file = os.path.join(path_price_json_auchan,
                           '{:s}_dict_auchan'.format(date_str))
  if os.path.exists(path_file):
    dict_period = dec_json(path_file)
    # Build dataframe
    ls_rows_products = []
    for store, ls_dict_stores in dict_period.items():
      for dict_product in ls_dict_stores:
        row = [dict_product.get(field, 'None') for field in ls_fields]
        # Need to be able to deal with a list such as [None, None]
        row = [u' '.join([y for y in x if y])\
                 if isinstance(x, list) else x for x in row]
        row = [store] + [x if x else None for x in row]
        ls_rows_products.append(row)
    df_products = pd.DataFrame(ls_rows_products,
                               columns = ['store'] + ls_fields)
    df_products['date'] = date_str
    ls_df_products.append(df_products)
df_master = pd.concat(ls_df_products, axis = 0, ignore_index = True)

# ##################
# FORMAT DF MASTER
# ##################
