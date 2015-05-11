﻿#!/usr/bin/python
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
    dict_fields.setdefault(product_key, []).append(dict_product.get('product_title',
                                                                    None))
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

# Check w/ title_2 (short) vs. title_1 (with brand)
# Check interest of adding format (price_lab_1)

print u'\nNb duplicates based on dpt, sub_dpt, title_2 (short):'
print len(df_period[df_period.duplicated(['department',
                                          'sub_department',
                                          'title_2'])])

print u'\nNb duplicates based on dpt, sub_dpt, title_1 (with brand):'
print len(df_period[df_period.duplicated(['department',
                                          'sub_department',
                                          'title_1'])])

print u'\nNb duplicates based on dpt, sub_dpt, title, unit:'
print len(df_period[df_period.duplicated(['department',
                                          'sub_department',
                                          'title_1',
                                          'price_lab_1'])])

# Restriction to non ambiguous rows

ls_fordup = ['department', 'sub_department', 'title_1', 'price_lab_1']

print u'\nNb of ambiguous rows:'
print len(df_period[(df_period.duplicated(ls_fordup)) |\
                    (df_period.duplicated(ls_fordup, take_last = True))])

print u'\nOverview of ambiguous rows:'
print df_period[(df_period.duplicated(ls_fordup)) |\
                (df_period.duplicated(ls_fordup, take_last = True))].to_string()

print u'\nNb rows with no ambiguity:'
print len(df_period[(~df_period.duplicated(ls_fordup)) &\
                    (~df_period.duplicated(ls_fordup, take_last = True))])

# Check that products with several dpt, sub_dpt have same price

df_loss = df_period[(df_period.duplicated(ls_fordup)) |\
                    (df_period.duplicated(ls_fordup, take_last = True))]

print df_loss[~df_loss['promo'].isnull()].to_string()

df_ok = df_period[(~df_period.duplicated(ls_fordup)) &\
                  (~df_period.duplicated(ls_fordup, take_last = True))].copy()

ls_fordup2 = ['title_1', 'price_lab_1']
df_ok_dup = df_ok[(df_ok.duplicated(ls_fordup2)) |\
                  (df_ok.duplicated(ls_fordup2, take_last = True))].copy()
df_ok_dup.sort(ls_fordup2, inplace = True)

print u'\nCheck if dup products across dpt sub_dpts have same price:'
print len(df_ok_dup[(~df_ok_dup.duplicated(['price_1'])) &\
                    (~df_ok_dup.duplicated(['price_1'], take_last = True))])

print u'\nNb rows with no ambiguity (incl price):'
print len(df_period[(~df_period.duplicated(ls_fordup + ['price_1'])) &\
                    (~df_period.duplicated(ls_fordup + ['price_1'], take_last = True))])

# ##############################
# OUTPUT NON AMBIGUOUS ROWS
# ##############################

# todo: promo field could be filled for first product only and rest same
# sort data so as to have non null promo field kept whenever data are dropped

df_prod_final = df_ok[['department',
                       'sub_department',
                       'title_1',
                       'price_lab_1']].drop_duplicates()

df_prices_final = df_ok[['title_1',
                         'title_2',
                         'price_lab_1',
                         'price_1',
                         'price_lab_2',
                         'price_2',
                         'promo']].drop_duplicates(['title_1', 'price_lab_1'])

# Add nb of dpt/sub_dpt in df_prices_final
se_nb_dsd = df_prod_final.groupby(['title_1', 'price_lab_1']).size()
df_nb_dsd = se_nb_dsd.reset_index()
df_nb_dsd.rename(columns = {0 : 'nb_dsd'}, inplace = True)
df_prices_final = pd.merge(df_prices_final,
                           df_nb_dsd,
                           on = ['title_1', 'price_lab_1'],
                           how = 'left')

# Check nb of promo lost while filtering data
# Can be that two different products with same name and format are on promotion
# Can be that product is listed once with a promotion once without (technical issue)
print u'\nNb of promo after treatment {:d}'.format(\
          df_prices_final[~df_prices_final['promo'].isnull()]['nb_dsd'].sum())

print u'\nNb of promo at beginning (total) {:d}'.format(\
          len(df_period[~df_period['promo'].isnull()]))

# Count promo by dpt and sub dpt (in general could be several period...)
# (actually kind of need to rebuild df_ok then...)
df_dsd_promo = df_ok[~df_ok['promo'].isnull()]\
                 .groupby(['department', 'sub_department']).size()
# todo: divide by nb of prods (float)... do with dpt and check over time
