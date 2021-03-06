﻿#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *

path_source = os.path.join(path_data,
                              u'data_supermarkets',
                              u'data_source',
                              u'data_drive',
                              u'data_carrefour')

path_source_json_voisins = os.path.join(path_source,
                                        u'data_json_voisins')

path_source_csv = os.path.join(path_source,
                               u'data_csv')

# ###########################
# CHECK ONE FILE WITH PANDAS
# ###########################

date_str = '20131129'
path_file = os.path.join(path_source_json_voisins,
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

# provided exact dates of beginning/end (not similar to list)
#ls_loop = [[path_source_json_voisins, date(2013,4,18), date(2013,11,28)],
#           [path_source_json_voisins, date(2013,11,29), date(2013,12,18)],
#           [path_source_json_voisins, date(2014,1,11), date(2014,12,05)]]

ls_loop = [[path_source_json_voisins, date(2013,4,18), date(2013,11,28)],
           [path_source_json_voisins, date(2013,11,29), date(2014,12,5)]]

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
  
      ## Output dataframe
      #df_products.to_csv(os.path.join(path_price_source_csv,
      #                                '{:s}_auchan_velizy'.format(date_str)),
      #                   index = False,
      #                   encoding = 'utf-8')
  
  df_master = pd.concat(ls_df_products, axis = 0, ignore_index = True)
  ls_df_master.append(df_master)

# ###################
# CLEAN FIRST PERIOD
# ###################

# Look if way to get some promo info (price cuts etc...)
# Promo probably essentially missing though
# Do some regular expression research for promo in various fields? 
# sec_price_caption, main_price_caption

df_master_1 = ls_df_master[0]

df_master_1.rename(columns = {'department' : 'section',
                              'sub_department': 'family'},
                   inplace = True)

# main_price_bloc

df_master_1['product_title_1'] = df_master_1['product_title_1'].apply(lambda x: x.strip())

df_master_1['main_price_bloc'] =\
   df_master_1['main_price_bloc'].apply(\
      lambda x: x.replace(u' <span class="currency">\u20ac</span>', u'')\
                 .replace(u' <span class="decimal">', u',')\
                 .replace(u'</span>', u'')\
                 .replace(u',', u'.')\
                 .strip())
df_master_1['main_price_bloc'] = df_master_1['main_price_bloc'].astype(float)

# sec_price_bloc

df_master_1['sec_price_bloc'] =\
   df_master_1['sec_price_bloc'].apply(lambda x: x.replace(\
                                         u'<span class="currency">\u20ac</span>', u'')\
                                                  .replace(u',', u'.')\
                                                  .strip())

df_master_1.loc[(df_master_1['sec_price_bloc'] == '') |\
                (df_master_1['sec_price_bloc'].str.contains(u'\u221e')),
                'sec_price_bloc'] = None

df_master_1['sec_price_bloc'] = df_master_1['sec_price_bloc'].astype(float)


## Audit pbms
#ls_ok, ls_pbm = [], []
#for x in df_master_1['sec_price_bloc'].values:
#  if x:
#    try:
#      ls_ok.append(float(x))
#    except:
#      ls_pbm.append(x)
#len(df_master_1[df_master_1['main_price_bloc'].str.contains(u'\u221e')])
## print df_master_1[df_master_1['sec_price_bloc'].str.contains(u'\u221e')][0:10].to_string()

#print df_master_1['main_price_caption'].value_counts()
## All lines: u'Prix Promo :' hence no qualitative info
#
#print len(df_master_1[df_master_1['product_title_1'] != df_master_1['product_title_2']])
## All lines: product_title_1 and product_title_2 always equal

df_master_1.drop(['product_title_2', 'main_price_caption'],
                 axis = 1,
                 inplace = True)

df_master_1.rename(columns = {'product_title_1'  : 'title',
                              'main_price_unit'  : 'label',
                              'main_price_bloc'  : 'total_price',
                              'sec_price_bloc'   : 'unit_price',
                              'sec_price_caption': 'unit'},
                   inplace = True)

ls_fields = [u'section', u'family', u'title']
for field in ls_fields:
  df_master_1[field] =\
     df_master_1[field].apply(lambda x: x.replace(u'&amp;', u'&').strip())

print u'\n Check first lines'
print df_master_1[0:10].to_string()

print df_master_1[['total_price', 'unit_price']].describe()

#print u'\n Check weird prices'
#pbm_title = u'Colle universelle instantanée, ultra gel - Super glue-3'
## print df_master_1[df_master_1['title'] == pbm_title][0:10].to_string()
#pbm_title_2 = u'Gousses de vanille, plus longues, plus charnues'
## print df_master_1[df_master_1['title'] == pbm_title_2][0:10].to_string()
## ok: 4.2 / 3.0  * 1000 = 1400

print u'\nTodo: fix (extract displayed)'
print df_master_1[df_master_1['unit_price'] <= 0.01][0:10].to_string()

df_1_dsd = df_master_1[['section', 'family']].drop_duplicates()
print df_1_dsd.to_string()

## Vins: 99 unique, no Millesime, very little information
#print u'\nVins'
#print len(df_master_1[df_master_1['family'] == u'La cave à vin'])
#pd.set_option('display.max_colwidth', 80)
#print df_master_1[df_master_1['family'] == u'La cave à vin'][0:100][['title']]\
#        .drop_duplicates().to_string(index = False)

df_master_1.to_csv(os.path.join(path_source_csv,
                                'df_carrefour_voisins_{:s}_{:s}.csv'\
                                   .format('20130418', '20131128')),
                   encoding = 'utf-8',
                   index = False)

# ####################
# CLEAN SECOND PERIOD
# ####################

# ls_unit_price and ls_reduction are always empty
# ls_block_promo: 2839 non null out of 125635 lines (i.e; 0.02%... small)
# Interestingly: ls_regular_price include "Prix Promo" so maybe info before?

df_master_2 = ls_df_master[1]

# Not starting with price: promo?
df_master_2.drop(['ls_unit_price', 'ls_reduction'],
                 axis = 1,
                 inplace = True)

df_master_2['ls_block_price'] =\
   df_master_2['ls_block_price'].apply(lambda x: re.sub(u'^Prix Promo :', u'', x).strip())

dict_len_1, dict_len_2 = {}, {}
for x in df_master_2['ls_block_price'].values:
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
for bloc_price in df_master_2['ls_block_price'].values:
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

df_m2_block_price = pd.DataFrame(ls_price_rows,
                                 columns = ['promo',
                                            'price_1', 'price_lab_1',
                                            'price_2', 'price_lab_2'])

df_master_2_bu = df_master_2.copy()

df_master_2 = pd.concat([df_master_2[['date', 'department', 'subdepartment',
                                      'product_title', 'ls_block_promo',
                                      'ls_format', 'ls_regular_price']],
                        df_m2_block_price],
                        axis = 1)

print len(df_master_2_bu[~pd.isnull(df_master_2_bu['ls_block_promo'])])
print len(df_master_2_bu[~df_master_2_bu['ls_block_price'].str.match(u'^[0-9]')])
print df_master_2_bu[~df_master_2_bu['ls_block_price'].str.match(u'^[0-9]')][0:10].to_string()
# No match is good indicator but there are a bit more ('Prix Promo' to be added back !?)

# count promo first day (looks ok)
print len(df_master_2_bu[(~pd.isnull(df_master_2_bu['ls_block_promo'])) &\
                         (df_master_2_bu['date'] == '20131129')])

# Fix promo (check valid)
df_master_2.loc[(pd.isnull(df_master_2['promo'])) &\
                (~pd.isnull(df_master_2['ls_block_promo'])),
                'promo'] = 'Prix Promo'

# Check validity of price_lab_1 (vs. ls_format), price_1 (vs ls_regular + euro sum?) 
# Same for price_2 ...

#df_master_2['ls_format'] =\
#   df_master_2['ls_format'].apply(lambda x: x.rstrip(u'\n').lstrip(u'\n').strip())
#print len(df_master_2[df_master_2['ls_format'] != df_master_2['price_lab_1']])

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

# weird prix_2 to be checked later... not so many
print df_master_2[['price_1', 'price_2']].describe()

df_master_2.drop(['ls_regular_price', 'ls_format', 'ls_block_promo'],
              axis = 1,
              inplace = True)

df_master_2.rename(columns = {'product_title' : 'title',
                              'department' : 'section',
                              'subdepartment' : 'family'},
                   inplace = True)

ls_fields = [u'section', u'family', u'title']
for field in ls_fields:
  df_master_2[field] =\
     df_master_2[field].apply(lambda x: x.replace(u'&amp;', u'&').strip())

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

df_master_2['promo'] =\
   df_master_2['promo'].apply(lambda x: re.sub(u'Remise Fidélité\s+soit.*',
                                               u'Remise Fidélité',
                                               x,
                                               re.DOTALL).strip()\
                                        if x else x)

df_master_2.rename(columns = {u'ls_product_title' : u'title',
                            u'price_1'          : u'total_price',
                            u'price_2'          : u'unit_price',
                            u'price_lab_1'      : u'label',
                            u'price_lab_2'      : u'unit'},
                   inplace = True)

df_master_2.to_csv(os.path.join(path_source_csv,
                                'df_carrefour_voisins_{:s}_{:s}.csv'\
                                   .format('20131129', '20141205')),
                   encoding = 'utf-8',
                   index = False)

## ######
## BACKUP
## ######
#  for field in ['product_title', 'department', 'family']:
#    df_master_2[field] =\
#      df_master_2[field].apply(lambda x: x.strip()\
#                                          .replace(u'&amp;', u'&')\
#                                          .replace(u'&Agrave;', u'À')\
#                                          .replace(u'&ndash;', u'-')\
#                                          .replace(u'&OElig;', u'Œ')
#                               if x else x)

# ##############################
# CHECK DUPLICATES IN ONE PERIOD
# ##############################

df_master, date_ex = df_master_1, '20130418'

df_period = df_master[df_master['date'] == date_ex].copy()

print u'\nNb duplicates based on dpt, sub_dpt, title, unit:'
print len(df_period[df_period.duplicated(['section',
                                          'family',
                                          'title',
                                          'label'])])

print u'\nNb duplicates based on title, unit:'
print len(df_period[df_period.duplicated(['title', 'label'])])

print u'\nNb with no dpt or sub_dpt'
print len(df_period[(df_period['section'].isnull()) |\
                    (df_period['family'].isnull())])

print u'\nNb with no sub_dpt:'
print len(df_period[df_period['family'].isnull()])
