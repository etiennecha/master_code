#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *

path_carrefour = os.path.join(path_data,
                           u'data_drive_supermarkets',
                           u'data_carrefour')

path_price_source = os.path.join(path_carrefour,
                                 u'data_source',
                                 u'data_json_carrefour')

path_price_built_csv = os.path.join(path_carrefour,
                                    u'data_built',
                                    u'data_csv_carrefour')

# ###########################
# CHECK ONE FILE WITH PANDAS
# ###########################

date_str = '20150505'
path_file = os.path.join(path_price_source,
                         '{:s}_dict_carrefour'.format(date_str))
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
                           '{:s}_dict_carrefour'.format(date_str))
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
        row = [dict_product.get(field, 'None') for field in ls_fields]
        row = [' '.join(x) if isinstance(x, list) else x for x in row]
        row = [store] + [x if x else None for x in row]
        ls_rows_products.append(row)
    df_products = pd.DataFrame(ls_rows_products,
                               columns = ['store'] + ls_fields)
    df_products['date'] = date_str
    ls_df_products.append(df_products)
df_master = pd.concat(ls_df_products, axis = 0, ignore_index = True)

# Not starting with price: promo?
df_master.drop(['ls_unit_price', 'ls_reduction'],
               axis = 1,
               inplace = True)

# ###################
# CLEAN DF MASTER
# ###################

df_master['ls_price'] =\
   df_master['ls_price'].apply(lambda x: re.sub(u'^Prix Promo :', u'', x).strip())

dict_len_1, dict_len_2 = {}, {}
for x in df_master['ls_price'].values:
	dict_len_1.setdefault(len(x.split('\n')), []).append(x)
	dict_len_2.setdefault(len(x.split('\n \n')), []).append(x)

# todo: analyse by length... find rules to split
# hypo on dict_len_2
# if len 1: price_1, price_lab_1 (1 \n, hence 1 part)
# if len 2: price 1, price_lab_1, price_2, price_lab_2 (4 \n hence 5 parts)
# 6 parts in dict_len_1 is a weird case...
# if len 3: promo and ... (6+ \n)
# In fact 6, 8 and 9 can be split on Prix promo: 

ls_price_rows = []
for bloc_price in df_master['ls_price'].values:
  promo, prix_1, prix_lab_1, prix_lab_2, prix_2 = [None for i in range(5)]
  if len(bloc_price.split(u'\n')) >= 8: # 8 or 9
    ls_split_1 = bloc_price.split(u'Prix Promo :')
    promo = ls_split_1[0]
    ls_split_2 = ls_split_1[1].split(u'\n \n')
    prix_1, prix_lab_1 = ls_split_2[0].split(u'\n')
    prix_lab_2, prix_2 = ls_split_2[1].split(u'\n')
  elif len(bloc_price.split(u'\n')) == 6:
    ls_split_1 = bloc_price.split(u'Prix Promo :')
    promo = ls_split_1[0]
    prix_1, prix_lab_1 = ls_split_1[1].split(u'\n')
  elif len(bloc_price.split(u'\n')) == 5:
    if not u'Prix Promo :' in bloc_price:
      ls_split_1 = bloc_price.split(u'\n \n')
      prix_1, prix_lab_1 = ls_split_1[0].split(u'\n')
      prix_lab_2, prix_2 = ls_split_1[1].split(u'\n')
    else:
      ls_split_1 = bloc_price.split(u'Prix Promo :')
      promo = ls_split_1[0]
      if u'\n \n' in ls_split_1[1]:
        ls_split_2 = ls_split_1[1].split(u'\n \n')
        prix_1, prix_lab_1 = ls_split_2[0].split(u'\n')
        prix_lab_2, prix_2 = ls_split_2[1].split(u'\n')
      else:
        prix_1, prix_lab_1 = ls_split_1[1].split(u'\n')
  elif len(bloc_price.split(u'\n')) == 2:
    if not 'Prix Promo :' in bloc_price:
      prix_1, prix_lab_1 = bloc_price.split(u'\n')
    else:
      ls_split_1 = bloc_price.split(u'Prix Promo :')
      promo = ls_split_1[0]
      prix_1, prix_lab_1 = ls_split_1[1].split(u'\n')
  ls_price_rows.append((promo, prix_1, prix_lab_1, prix_2, prix_lab_2))
# Check output and reintegrate in dataframe

df_price = pd.DataFrame(ls_price_rows,
                        columns = ['promo',
                                   'price_1', 'price_lab_1',
                                   'price_2', 'price_lab_2'])

df_master_bu = df_master.copy()

df_master = pd.concat([df_master[['store', 'date',
                                  'department', 'sub_department',
                                  'ls_product_title', 'img_name']],
                      df_price],
                      axis = 1)

# try to save memory (could drop also unused columns)
del(ls_price_rows)
del(df_price)

# FORMAT SIMPLE TEXT FIELDS

for field in ['department', 'sub_department', 'ls_product_title', 'img_name']:
  df_master[field] =\
     df_master[field].apply(lambda x: x.replace(u'\n', ' ')\
                                         .replace(u'&amp;', u'&').strip())

# CONVERT PRICES TO NUMERIC

df_master['price_1'] =\
   df_master['price_1'].apply(lambda x: x.replace(u' \u20ac ', u'.')\
                                         .replace(u'\xa0', u'')\
                                         .strip())
df_master['price_1'] = df_master['price_1'].astype(float)

df_master['price_2'] =\
   df_master['price_2'].apply(lambda x: x.replace(u'\u20ac', u'')\
                                           .replace(u',', u'.')\
                                           .strip() if x else x)

df_master.loc[(df_master['price_2'] == '') |\
                (df_master['price_2'].str.contains(u'\u221e')),
                'price_2'] = None

df_master['price_2'] = df_master['price_2'].astype(float)

# FORMAT PROMO

df_master['promo'] =\
   df_master['promo'].apply(lambda x: x.replace(u'\r', u' ')\
                                         .replace(u'\n', u' ')\
                                         .strip() if x else x)
df_master['promo'] =\
   df_master['promo'].apply(lambda x: re.sub(u'Prix combiné\s*Soit les.*',
                                               '',
                                               x,
                                               re.DOTALL).strip()\
                                        if x else x)

df_master['promo'] =\
   df_master['promo'].apply(lambda x: re.sub(u'Ancien Prix.*',
                                               '',
                                               x,
                                               re.DOTALL).strip()\
                                        if x else x)

df_master['promo'] =\
   df_master['promo'].apply(lambda x: re.sub(u'Remise Fidélité\s+soit.*',
                                             u'Remise Fidélité',
                                             x,
                                             re.DOTALL).strip()\
                                        if x else x)

# CREATE BRAND

df_master['brand'] =\
  df_master.apply(lambda row: row['img_name'].replace(row['ls_product_title'], '').strip()\
                                if not pd.isnull(row['img_name']) else None, axis = 1)

df_master.rename(columns = {u'ls_product_title' : u'title',
                            u'img_name'         : u'title_with_brand',
                            u'price_1'          : u'total_price',
                            u'price_2'          : u'unit_price',
                            u'price_lab_1'      : u'label',
                            u'price_lab_2'      : u'unit'},
                 inplace = True)

df_master.drop(labels = ['title_with_brand'], axis = 1, inplace = True)

## CHECK FORMATTING
#
#print u'\nView promo:'
##print df_master[~pd.isnull(df_master['promo'])]['promo'][0:500].to_string()
#print df_master['promo'].value_counts()
#
## todo: check this promo vs promo field (some unexplained inconsistencies)
#
## Weird unit_price to be checked later... not so many
#
#print u'\nProduct total and unit price overview:'
#print df_master[['total_price', 'unit_price']].describe()

## ########
## OUTPUT
## ########

ls_dup_id_cols = ['store', 'date', 'department', 'sub_department',
                  'title', 'brand', 'label']

df_master_nodup =\
  df_master[~((df_master.duplicated(ls_dup_id_cols)) |\
              (df_master.duplicated(ls_dup_id_cols,
                                    take_last = True)))]

ls_price_cols = ['store', 'date', 'title', 'brand', 'label',
                 'promo', 'total_price', 'unit_price', 'unit']

df_prices = df_master_nodup[ls_price_cols].drop_duplicates(ls_price_cols[:5])

ls_product_cols = ['department', 'sub_department', 'title', 'brand', 'label']

df_products = df_master_nodup[ls_product_cols].drop_duplicates()

dict_carrefour_2015 = {'df_master_carrefour_2015' : df_master,
                       'df_prices_carrefour_2015' : df_prices,
                       'df_products_carrefour_2015': df_products}

for file_title, df_file in dict_carrefour_2015.items():
  df_file.to_csv(os.path.join(path_price_built_csv,
                              '{:s}.csv'.format(file_title)),
                   encoding = 'utf-8',
                   float_format='%.2f',
                   index = False)

## ######
## BACKUP
## ######
#  for field in ['product_title', 'department', 'sub_department']:
#    df_master[field] =\
#      df_master[field].apply(lambda x: x.strip()\
#                                          .replace(u'&amp;', u'&')\
#                                          .replace(u'&Agrave;', u'À')\
#                                          .replace(u'&ndash;', u'-')\
#                                          .replace(u'&OElig;', u'Œ')
#                               if x else x)

## ##############################
## CHECK DUPLICATES IN ONE PERIOD
## ##############################
#
#df_master_int, date_ex = df_master, '20150505'
#
#df_period = df_master_int[(df_master_int['date'] == date_ex) &\
#                          (df_master_int['store'] == u'78 - VOISINS LE BRETONNEUX')]
#
## Check w/ title (short) vs. title, label, brand
#
#print u'\nNb duplicates based on dpt, sub_dpt, title (short):'
#print len(df_period[df_period.duplicated(['department',
#                                          'sub_department',
#                                          'title'])])
#
#print u'\nNb duplicates based on dpt, sub_dpt, title, label:'
#print len(df_period[df_period.duplicated(['department',
#                                          'sub_department',
#                                          'title',
#                                          'label'])])
#
#print u'\nNb duplicates based on dpt, sub_dpt, title, label, brand:'
#print len(df_period[df_period.duplicated(['department',
#                                          'sub_department',
#                                          'title',
#                                          'label',
#                                          'brand'])])
#
## Restriction to non ambiguous rows
#
#ls_fordup = ['department', 'sub_department', 'title', 'label', 'brand']
#
#print u'\nNb of ambiguous rows:'
#print len(df_period[(df_period.duplicated(ls_fordup)) |\
#                    (df_period.duplicated(ls_fordup, take_last = True))])
#
#print u'\nOverview of ambiguous rows:'
#print df_period[(df_period.duplicated(ls_fordup)) |\
#                (df_period.duplicated(ls_fordup, take_last = True))][0:20].to_string()
#
#print u'\nNb rows with no ambiguity:'
#print len(df_period[(~df_period.duplicated(ls_fordup)) &\
#                    (~df_period.duplicated(ls_fordup, take_last = True))])
#
## Check that products with several dpt, sub_dpt have same price
#
#df_loss = df_period[(df_period.duplicated(ls_fordup)) |\
#                    (df_period.duplicated(ls_fordup, take_last = True))]
#
#print df_loss[~df_loss['promo'].isnull()].to_string()
#
#df_ok = df_period[(~df_period.duplicated(ls_fordup)) &\
#                  (~df_period.duplicated(ls_fordup, take_last = True))].copy()
#
#ls_fordup2 = ['title', 'label', 'brand']
#df_ok_dup = df_ok[(df_ok.duplicated(ls_fordup2)) |\
#                  (df_ok.duplicated(ls_fordup2, take_last = True))].copy()
#df_ok_dup.sort(ls_fordup2, inplace = True)
#
#print u'\nCheck if dup products across dpt sub_dpts have same price:'
#print len(df_ok_dup[(~df_ok_dup.duplicated(['total_price'])) &\
#                    (~df_ok_dup.duplicated(['total_price'], take_last = True))])
#
#print u'\nNb rows with no ambiguity (incl price):'
#print len(df_period[(~df_period.duplicated(ls_fordup + ['total_price'])) &\
#                    (~df_period.duplicated(ls_fordup + ['total_price'], take_last = True))])

## ##############################
## ANALYSIS (MOVE)
## ##############################
#
## todo: promo field could be filled for first product only and rest same
## sort data so as to have non null promo field kept whenever data are dropped
#
## Add nb of dpt/sub_dpt in df_products_final
#se_nb_dsd = df_products.groupby(['title', 'label', 'brand']).size()
#df_nb_dsd = se_nb_dsd.reset_index()
#df_nb_dsd.rename(columns = {0 : 'nb_dsd'}, inplace = True)
#df_products_final = pd.merge(df_products,
#                             df_nb_dsd,
#                             on = ['title', 'label', 'brand'],
#                             how = 'left')
#
## Add nb of period and promo by products (todo)
