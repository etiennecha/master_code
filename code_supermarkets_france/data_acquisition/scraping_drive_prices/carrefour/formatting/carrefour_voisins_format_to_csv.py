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

date_str = '20131129'
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

# provided exact dates of beginning/end (not similar to list)
#ls_loop = [[path_price_source, date(2013,4,18), date(2013,11,28)],
#           [path_price_source, date(2013,11,29), date(2013,12,18)],
#           [path_price_source, date(2014,1,11), date(2014,12,05)]]

ls_loop = [[path_price_source, date(2013,4,18), date(2013,11,28)],
           [path_price_source, date(2013,11,29), date(2014,12,5)]]

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
  
  df_master = pd.concat(ls_df_products, axis = 0)
  ls_df_master.append(df_master)

## ###################
## CLEAN FIRST PERIOD
## ###################
#
## Look if way to get some promo info (price cuts etc...)
## Promo probably essentially missing though
## Do some regular expression research for promo in various fields? 
## sec_price_caption, main_price_caption
#
#df_master_1 = ls_df_master[0]
#
## main_price_bloc
#
#df_master_1['product_title_1'] = df_master_1['product_title_1'].apply(lambda x: x.strip())
#
#df_master_1['main_price_bloc'] =\
#   df_master_1['main_price_bloc'].apply(\
#      lambda x: x.replace(u' <span class="currency">\u20ac</span>', u'')\
#                 .replace(u' <span class="decimal">', u',')\
#                 .replace(u'</span>', u'')\
#                 .replace(u',', u'.')\
#                 .strip())
#df_master_1['main_price_bloc'] = df_master_1['main_price_bloc'].astype(float)
#
## sec_price_bloc
#
#df_master_1['sec_price_bloc'] =\
#   df_master_1['sec_price_bloc'].apply(lambda x: x.replace(\
#                                         u'<span class="currency">\u20ac</span>', u'')\
#                                                  .replace(u',', u'.')\
#                                                  .strip())
#
#df_master_1.loc[(df_master_1['sec_price_bloc'] == '') |\
#                (df_master_1['sec_price_bloc'].str.contains(u'\u221e')),
#                'sec_price_bloc'] = None
#
#df_master_1['sec_price_bloc'] = df_master_1['sec_price_bloc'].astype(float)
#
#
### Audit pbms
##ls_ok, ls_pbm = [], []
##for x in df_master_1['sec_price_bloc'].values:
##  if x:
##    try:
##      ls_ok.append(float(x))
##    except:
##      ls_pbm.append(x)
##len(df_master_1[df_master_1['main_price_bloc'].str.contains(u'\u221e')])
### print df_master_1[df_master_1['sec_price_bloc'].str.contains(u'\u221e')][0:10].to_string()
#
##print df_master_1['main_price_caption'].value_counts()
### All lines: u'Prix Promo :' hence no qualitative info
##
##print len(df_master_1[df_master_1['product_title_1'] != df_master_1['product_title_2']])
### All lines: product_title_1 and product_title_2 always equal
#
#df_master_1.drop(['product_title_2', 'main_price_caption'],
#                 axis = 1,
#                 inplace = True)
#df_master_1.rename(columns = {'product_title_1' : 'title',
#                              'main_price_bloc' : 'price_1',
#                              'sec_price_bloc' : 'price_2',
#                              'sec_price_caption': 'price_lab_2'},
#                   inplace = True)
#
#ls_fields = [u'department', u'sub_department', u'title']
#for field in ls_fields:
#  df_master_1[field] =\
#     df_master_1[field].apply(lambda x: x.replace(u'&amp;', u'&').strip())
#
#print u'\n Check first lines'
#print df_master_1[0:10].to_string()
#
#print df_master_1[['price_1', 'price_2']].describe()
#
##print u'\n Check weird prices'
##pbm_title = u'Colle universelle instantanée, ultra gel - Super glue-3'
### print df_master_1[df_master_1['title'] == pbm_title][0:10].to_string()
##pbm_title_2 = u'Gousses de vanille, plus longues, plus charnues'
### print df_master_1[df_master_1['title'] == pbm_title_2][0:10].to_string()
### ok: 4.2 / 3.0  * 1000 = 1400
#
#print u'\nTodo: fix (extract displayed)'
#print df_master_1[df_master_1['price_2'] <= 0.01][0:10].to_string()
#
#df_1_dsd = df_master_1[['department', 'sub_department']].drop_duplicates()
#print df_1_dsd.to_string()
#
### Vins: 99 unique, no Millesime, very little information
##print u'\nVins'
##print len(df_master_1[df_master_1['sub_department'] == u'La cave à vin'])
##pd.set_option('display.max_colwidth', 80)
##print df_master_1[df_master_1['sub_department'] == u'La cave à vin'][0:100][['title']]\
##        .drop_duplicates().to_string(index = False)

# ####################
# CLEAN SECOND PERIOD
# ####################

# ls_unit_price and ls_reduction are always empty
# ls_block_promo: 2839 non null out of 125635 lines (i.e; 0.02%... small)
# Interestingly: ls_regular_price include "Prix Promo" so maybe info before?

df_period_2 = ls_df_master[1]

df_period_2['ls_block_price'] =\
   df_period_2['ls_block_price'].apply(lambda x: re.sub(u'^Prix Promo :', u'', x).strip())

# Not starting with price: promo?
print len(df_period_2[~pd.isnull(df_period_2['ls_block_promo'])])
print len(df_period_2[~df_period_2['ls_block_price'].str.match(u'^[0-9]')])
print df_period_2[~df_period_2['ls_block_price'].str.match(u'^[0-9]')][0:10].to_string()
# No match is good indicator but there are a bit more ('Prix Promo' to be added back !?)

# count promo first day (looks ok)
print len(df_period_2[(~pd.isnull(df_period_2['ls_block_promo'])) &\
                      (df_period_2['date'] == '20131129')])

## ######
## BACKUP
## ######
#  for field in ['product_title', 'department', 'sub_department']:
#    df_master[field] =\
#      df_master[field].apply(lambda x: x.strip()\
#                                        .replace(u'&amp;', u'&')\
#                                        .replace(u'&Agrave;', u'À')\
#                                        .replace(u'&ndash;', u'-')\
#                                        .replace(u'&OElig;', u'Œ')
#                               if x else x)
#
#  df_master.to_csv(os.path.join(path_price_built_csv,
#                                'df_auchan_velizy_{:s}_{:s}.csv'\
#                                   .format(ls_dates[0], ls_dates[-1])),
#                   encoding = 'utf-8',
#                   index = False)
#
### ##############################
### CHECK DUPLICATES IN ONE PERIOD
### ##############################
##
##df_period = df_master[df_master['date'] == ls_dates[0]].copy()
##
##print u'\nNb duplicates based on dpt, sub_dpt, prod_title:'
##print len(df_period[df_period.duplicated(['department',
##                                          'sub_department',
##                                          'title'])])
##
##print u'\nNb duplicates based on prod_title:'
##print len(df_period[df_period.duplicated(['title'])])
##
##print u'\nNb with no dpt or sub_dpt'
##print len(df_period[(df_period['department'].isnull()) |\
##                    (df_period['sub_department'].isnull())])
##
##print u'\nNb with no sub_dpt:'
##print len(df_period[df_period['sub_department'].isnull()])
##
### VISUAL INSPECTION
##print u'\n', df_period[df_period.duplicated(['department',
##                                             'sub_department',
##                                             'title'])].to_string()
##
##print u'\n', df_period[df_period['title'] == 'carottes sachet 1kg'].to_string()
##
##print u'\'n', len(df_period[df_period.duplicated(['department',
##                                                  'title'])])
##
##print u'\n', len(df_period[df_period.duplicated(['department',
##                                                 'sub_department',
##                                                 'title'])])
##
### Duplicates due to one line for regular price and one for promo price
### Note sure if all duplicates are legit (carottes sachet in épicerie?)
##
### Check if no subdpt (None) are always duplicates?
##ls_prod_nosd = df_period['title'][df_period['sub_department'].isnull()]\
##                 .unique().tolist()
##print u'\nNb of prod with no sub_dpt: {:d}'.format(len(ls_prod_nosd))
##
##ls_prod_nosd_dup = df_period['title'][(df_period.duplicated(['title'])) &\
##                                      (df_period['title'].isin(ls_prod_nosd))]\
##                     .unique().tolist()
##print u'\nNb of prod with no sub_dpt and dup exists: {:d}'.format(len(ls_prod_nosd_dup))
### Seems ok to drop anytime no sub_dpt since duplicate exists
##
### Check if promo always imply two lines: reg and promo price (check in more recent df?)
### actually with df_period['flag']: even more promo
##ls_prod_promo = df_period['title'][(~df_period['promo_vignette'].isnull()) |
##                                   (~df_period['promo'].isnull())]\
##                  .unique().tolist()
##print u'\nNb of prod with promo: {:d}'.format(len(ls_prod_promo))
##
##ls_prod_promo_dup = df_period['title'][(df_period.duplicated(['title'])) &\
##                                      (df_period['title'].isin(ls_prod_promo))]\
##                      .unique().tolist()
##print u'\nNb of prod with no sub_dpt and dup exists: {:d}'.format(len(ls_prod_promo_dup))
### There is not always a duplicate but can drop if so (regular price is interesting tho)
### Caution: might be duplicates due to several dpts... not always reg and promo price
##
### todo: except for products with regular and promo price... check same price
##len(df_period['title'].unique())
##len(df_period[['title', 'total_price']].drop_duplicates())
##
##df_ttp = df_period[['title', 'total_price']].drop_duplicates()
##ls_dup_ttp = df_ttp['title'][df_ttp.duplicated(['title'])].unique().tolist()
##print df_period[df_period['title'].isin(ls_dup_ttp)].to_string()
##
### Get all (unique) legit (product, dpt, subdpt)
### Too slow if want to run with df_master
##ls_legit_pds = []
##for x in df_period[['title', 'department', 'sub_department']].values:
##  if tuple(x) not in ls_legit_pds:
##    ls_legit_pds.append(tuple(x))
##
##df_pds = df_master[['title', 'department', 'sub_department']].drop_duplicates()
##df_pds.sort(['title', 'department', 'sub_department'], inplace = True)
