#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *

path_leclerc = os.path.join(path_data,
                            u'data_drive_supermarkets',
                            u'data_leclerc')

path_price_source = os.path.join(path_leclerc,
                                 u'data_source',
                                 u'data_json_leclerc')

path_price_built_csv = os.path.join(path_leclerc,
                                    u'data_built',
                                    u'data_csv_leclerc')

# ###########################
# CHECK ONE FILE WITH PANDAS
# ###########################

date_str = '20150508'
path_file = os.path.join(path_price_source,
                         '{:s}_dict_leclerc'.format(date_str))
dict_period = dec_json(path_file)

# Check fields for each product (with stats)
dict_fields = {}
for store, ls_dict_stores in dict_period.items():
  for dict_product in ls_dict_stores:
    for product_key in dict_product[u'objElement'].keys():
      dict_fields.setdefault(product_key, []).append(dict_product.get('sIdUnique',
                                                                      None))
for k,v in dict_fields.items():
  print k, len(v)

# Need to consider period with same fields
ls_fields = dict_fields.keys()

# ###################
# BUILD DF MASTER
# ###################

path_temp = path_price_source
start_date, end_date = date(2015,5,5), date(2015,5,18)
ls_dates = get_date_range(start_date, end_date)
ls_df_products = []
for date_str in ls_dates:
  path_file = os.path.join(path_temp,
                           '{:s}_dict_leclerc'.format(date_str))
  if os.path.exists(path_file):
    dict_period = dec_json(path_file)
     
    ## Find all keys appearing in at least one product dictionary
    #ls_all_fields = []
    #for dict_product in period_file:
    #  ls_all_fields += dict_product.keys()
    #ls_fields = list(set(ls_all_fields))
    
    # Build dataframe
    ls_rows_products = []
    for store, ls_dict_stores in dict_period.items():
      for dict_product in ls_dict_stores:
        row = [dict_product[u'objElement'].get(field, 'None') for field in ls_fields]
        row = [' '.join(x) if isinstance(x, list) else x for x in row]
        row = [store] + [x if x else None for x in row]
        ls_rows_products.append(row)
    df_products = pd.DataFrame(ls_rows_products,
                               columns = ['store'] + ls_fields)
    df_products['date'] = date_str
    ls_df_products.append(df_products)
df_master = pd.concat(ls_df_products, axis = 0, ignore_index = True)
