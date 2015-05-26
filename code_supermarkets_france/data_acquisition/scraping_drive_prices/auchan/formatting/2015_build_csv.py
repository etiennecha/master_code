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

# no need for intermediate csv
path_price_built_csv = os.path.join(path_auchan,
                                    u'data_built',
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

print u'\nStats des on fields for ref file:'
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

for field in ['name', 'unit_price']:
  df_master[field] = df_master[field].apply(lambda x: x.replace(u'\n', u'')\
                                                       .replace(u'\t', u'')\
                                                       .strip())

# FORMAT UNIT PRICE

#for x in df_master['unit_price'].values:
#  if u'\u20ac' not in x:
#    print x
#    break

df_master['price_2'], df_master['price_lab_2'] =\
  zip(*df_master['unit_price'].apply(lambda x: [x.strip() for x in x.split(u'\u20ac')]))

df_master['price_2'] =\
  df_master['price_2'].apply(lambda x: x.replace(u',', u'.')\
                                        .strip()).astype(float)
df_master['unit_price'] = df_master['price_2']
df_master['unit'] = df_master['price_lab_2']
df_master.drop(labels = ['price_2', 'price_lab_2'], axis = 1, inplace = True)

dict_replace_unit = {u'/ kg' : u'Prix/kg',
                     u'/ l'  : u'Prix/l',
                     u'/ m'  : u'Prix/mtr',
                     u'/ pce': u'Prix/pce'}
df_master['unit'] =\
  df_master['unit'].apply(lambda x: dict_replace_unit.get(x)\
                                      if x and x in dict_replace_unit else x)

print u'\nOverview unit:'
print df_master['unit'].value_counts()

# FORMAT TOTAL PRICES
df_master['total_price'] =\
  df_master['total_price'].apply(lambda x: x.replace(u' ,', u'.')\
                                            .replace(u'\u20ac', u'')\
                                            .strip()).astype(float)

# FORMAT PROMO => todo 
# e.g. u"[u'operation-produit', u'operation-produit-waaoh'] \n30%\n"

for x in df_master['promo']:
  if x and not '[' in x:
    print x
    break

df_master['promo_vignette'], df_master['promo'] =\
  zip(*df_master['promo'].apply(lambda x: [x.strip() for x in x.split(u']')] if x else [None, None]))

# FORMAT PROMO VIGNETTE

def format_promo_vignette(pro_vi):
  pro_vi = json.loads(pro_vi.replace(u"u'", u'"').replace(u"'", u'"'))
  pro_vi = [y.replace('operation-produit', 'op').strip() for y in pro_vi]
  return ' '.join(pro_vi)
  return pro_vi

df_master['promo_vignette'] =\
  df_master['promo_vignette'].apply(lambda x: format_promo_vignette(x + u"]") if x else None)

print u'\nStats des on promo_vignette:'
print df_master['promo_vignette'].value_counts()

## promo long vs. not long? (really time?)
## check wahoo vs. not
## meaning of operation-produit but not promo ?

# print len(df_master[df_master['sub_dpt'].isnull()])

#print df_master[(df_master['dum_promo'] == 'yes') &\
#                (df_master['promo_vignette'].isnull())][0:20].to_string()

# ##################
# OUTPUT DF MASTER
# ##################

# check product identification by img
# a priori includes price hence not interesting

df_master.rename(columns = {'dpt' : 'department',
                            'sub_dpt' : 'sub_department',
                            'name' : 'title'},
                 inplace = True)

ls_dup_id_cols = ['store', 'date', 'department', 'sub_department', 'title']

df_master_nodup =\
  df_master[~((df_master.duplicated(ls_dup_id_cols)) |\
              (df_master.duplicated(ls_dup_id_cols,
                                    take_last = True)))]

ls_price_cols = ['store', 'date', 'title',
                 'dum_available',
                 'dum_promo', 'promo_vignette', 'promo',
                 'total_price', 'unit_price', 'unit']

df_prices = df_master_nodup[ls_price_cols].drop_duplicates(['date', 'store', 'title'])

df_products = df_master_nodup[['department', 'sub_department', 'title']].drop_duplicates()

# OUTPUT

dict_auchan_2015 = {'df_master_auchan_2015' : df_master,
                    'df_prices_auchan_2015' : df_prices,
                    'df_products_auchan_2015': df_products}

for file_title, df_file in dict_auchan_2015.items():
  df_file.to_csv(os.path.join(path_price_built_csv,
                              '{:s}.csv'.format(file_title)),
                   encoding = 'utf-8',
                   float_format='%.2f',
                   index = False)
