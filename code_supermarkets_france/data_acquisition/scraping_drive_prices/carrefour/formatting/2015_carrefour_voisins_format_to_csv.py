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
                                 u'data_json_carrefour_voisins')

path_price_built_csv = os.path.join(path_carrefour,
                                    u'data_built',
                                    u'data_csv_carrefour_voisins')

# ###########################
# CHECK ONE FILE WITH PANDAS
# ###########################

date_str = '20150503'
path_file = os.path.join(path_price_source,
                         '{:s}_carrefour_voisins'.format(date_str))
period_file = dec_json(path_file)

# Check fields for each product (with stats)
dict_fields = {}
for dict_product in period_file:
  for product_key in dict_product.keys():
    dict_fields.setdefault(product_key, []).append(dict_product.get('product_title', None))
for k,v in dict_fields.items():
  print k, len(v)

# ###################
# BUILD DF MASTER
# ###################

ls_loop = [[path_price_source, date(2015,5,3), date(2015,5,3)]]
ls_df_master = []
for path_temp, start_date, end_date in ls_loop:
  ls_dates = get_date_range(start_date, end_date)
  ls_df_products = []
  for date_str in ls_dates:
    path_file = os.path.join(path_temp,
                             '{:s}_carrefour_voisins'.format(date_str))
    if os.path.exists(path_file):
      period_file = dec_json(path_file)
       
      # Find all keys appearing in at least one product dictionary
      ls_all_fields = []
      for dict_product in period_file:
        ls_all_fields += dict_product.keys()
      ls_fields = list(set(ls_all_fields))
      
      # Build dataframe
      ls_rows_products = []
      for dict_product in period_file:
        row = [dict_product.get(field, 'None') for field in ls_fields]
        row = [' '.join(x) if isinstance(x, list) else x for x in row]
        row = [x if x else None for x in row]
        ls_rows_products.append(row)
      df_products = pd.DataFrame(ls_rows_products,
                                 columns = ls_fields)
      
      df_products['date'] = date_str
      ls_df_products.append(df_products)
  
  df_master = pd.concat(ls_df_products, axis = 0, ignore_index = True)
  ls_df_master.append(df_master)

## Not starting with price: promo?
#df_master.drop(['ls_unit_price', 'ls_reduction'],
#               axis = 1,
#               inplace = True)

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

df_master_2 = pd.concat([df_master[['date', 'department', 'sub_department',
                                    'ls_product_title', 'img_name']],
                        df_price],
                        axis = 1)

# FORMAT SIMPLE TEXT FIELDS

for field in ['department', 'sub_department', 'ls_product_title', 'img_name']:
  df_master_2[field] =\
     df_master_2[field].apply(lambda x: x.replace(u'\n', ' ')\
                                         .replace(u'&amp;', u'&').strip())

# CONVERT PRICES TO NUMERIC

df_master_2['price_1'] =\
   df_master_2['price_1'].apply(lambda x: x.replace(u' \u20ac ', u'.').strip())
df_master_2['price_1'] = df_master_2['price_1'].astype(float)

df_master_2['price_2'] =\
   df_master_2['price_2'].apply(lambda x: x.replace(u'\u20ac', u'')\
                                           .replace(u',', u'.')\
                                           .strip() if x else x)

df_master_2.loc[(df_master_2['price_2'] == '') |\
                (df_master_2['price_2'].str.contains(u'\u221e')),
                'price_2'] = None

df_master_2['price_2'] = df_master_2['price_2'].astype(float)

# FORMAT PROMO

df_master_2['promo'] =\
   df_master_2['promo'].apply(lambda x: x.replace(u'\r', u' ')\
                                         .replace(u'\n', u' ')\
                                         .strip() if x else x)
df_master_2['promo'] =\
   df_master_2['promo'].apply(lambda x: re.sub(u'Prix combiné\s*Soit les.*',
                                               '',
                                               x,
                                               re.DOTALL).strip()\
                                        if x else x)

df_master_2['promo'] =\
   df_master_2['promo'].apply(lambda x: re.sub(u'Ancien Prix.*',
                                               '',
                                               x,
                                               re.DOTALL).strip()\
                                        if x else x)

print u'\nView promo:'
#print df_master_2[~pd.isnull(df_master_2['promo'])]['promo'][0:500].to_string()
print df_master_2['promo'].value_counts()

# todo: check this promo vs promo field (some unexplained inconsistencies)

# Weird prix_2 to be checked later... not so many

print u'\nProduct total and unit price overview:'
print df_master_2[['price_1', 'price_2']].describe()

df_master_2.rename(columns = {'img_name' : 'title_1',
                              'ls_product_title' : 'title_2'},
                   inplace = True)

print u'\nOverview departments and sub_departments:'
df_2_dsd = df_master_2[['department', 'sub_department']].drop_duplicates()
df_2_dsd.sort(['department', 'sub_department'], inplace = True)
print df_2_dsd.to_string()

#df_master_2.to_csv(os.path.join(path_price_built_csv,
#                              'df_carrefour_voisins_{:s}_{:s}.csv'\
#                                 .format('20131129', '20141205')),
#                   encoding = 'utf-8',
#                   index = False)

## ######
## BACKUP
## ######
#  for field in ['product_title', 'department', 'sub_department']:
#    df_master_2[field] =\
#      df_master_2[field].apply(lambda x: x.strip()\
#                                          .replace(u'&amp;', u'&')\
#                                          .replace(u'&Agrave;', u'À')\
#                                          .replace(u'&ndash;', u'-')\
#                                          .replace(u'&OElig;', u'Œ')
#                               if x else x)
#

# ##############################
# CHECK DUPLICATES IN ONE PERIOD
# ##############################

df_master_int, date_ex = df_master_2, '20150503'

df_period = df_master_int[df_master_int['date'] == date_ex].copy()

print u'\nNb duplicates based on dpt, sub_dpt, title_1 (short):'
print len(df_period[df_period.duplicated(['department',
                                          'sub_department',
                                          'title_2'])])

print u'\nNb duplicates based on dpt, sub_dpt, title_2 (with brand):'
print len(df_period[df_period.duplicated(['department',
                                          'sub_department',
                                          'title_1'])])

print u'\nNb duplicates based on dpt, sub_dpt, title, unit:'
print len(df_period[df_period.duplicated(['department',
                                          'sub_department',
                                          'title_1',
                                          'price_lab_1'])])

print u'\nNb duplicates based on title, unit:'
print len(df_period[df_period.duplicated(['title_1', 'price_lab_1'])])


print u'\nNb with no dpt or sub_dpt'
print len(df_period[(df_period['department'].isnull()) |\
                    (df_period['sub_department'].isnull())])

print u'\nNb with no sub_dpt:'
print len(df_period[df_period['sub_department'].isnull()])

print u'\nNb unique products (title, unit):'
print len(df_period[['title_1', 'price_lab_1']].drop_duplicates())

print u'\nNb unique product (title, unit, price):'
print len(df_period[['title_1', 'price_lab_1', 'price_1']].drop_duplicates())

# VISUAL INSPECTION
ls_dup_titles_1 =\
   df_period['title_1'][df_period.duplicated(['department',
                                              'sub_department',
                                              'title_1',
                                              'price_lab_1'])].unique().tolist()
print u'\nInspect duplicates w/ same dep, sdep, title, format:'
print df_period[df_period['title_1'].isin(ls_dup_titles_1)].to_string()

# Duplicates due to one line for regular price and one for promo price
# Note sure if all duplicates are legit (carottes sachet in épicerie?)

## Check if no subdpt (None) are always duplicates?
#ls_prod_nosd = df_period['title_1'][df_period['sub_department'].isnull()]\
#                 .unique().tolist()
#print u'\nNb of prod with no sub_dpt: {:d}'.format(len(ls_prod_nosd))
#
#ls_prod_nosd_dup = df_period['title_1'][(df_period.duplicated(['title_1'])) &\
#                                        (df_period['title_1'].isin(ls_prod_nosd))]\
#                     .unique().tolist()

df_ttp = df_period[['title_1', 'price_1']].drop_duplicates()
ls_dup_ttp = df_ttp['title_1'][df_ttp.duplicated(['title_1'])].unique().tolist()

# print df_period[df_period['title_1'].isin(ls_dup_ttp)].to_string()

# Get all (unique) legit (product, dpt, subdpt)
# Too slow if want to run with df_master
ls_legit_pds = []
for x in df_period[['title_1', 'department', 'sub_department']].values:
  if tuple(x) not in ls_legit_pds:
    ls_legit_pds.append(tuple(x))

df_pds = df_master_int[['title_1', 'department', 'sub_department']].drop_duplicates()
df_pds.sort(['title_1', 'department', 'sub_department'], inplace = True)

# Check mapping
df_u_title_1 = df_period[['title_1']].drop_duplicates()
df_u_title_2 = df_period[['title_2']].drop_duplicates()
df_u_title_12 = df_period[['title_1', 'title_2']].drop_duplicates()
