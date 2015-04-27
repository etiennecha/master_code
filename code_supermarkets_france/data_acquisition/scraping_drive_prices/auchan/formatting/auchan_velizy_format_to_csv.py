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

path_price_source = os.path.join(path_auchan,
                                 u'data_source',
                                 u'data_json_auchan_velizy')

path_price_bu_duplicates = os.path.join(path_price_source,
                                        u'bu_duplicates')

path_price_built_csv = os.path.join(path_auchan,
                                    u'data_built',
                                    u'data_csv_auchan_velizy')

## ###########################
## CHECK ONE FILE WITH PANDAS
## ###########################
#
#date_str = '20121122'
#path_file = os.path.join(path_price_bu_duplicates,
#                         '{:s}_auchan_velizy'.format(date_str))
#period_file = dec_json(path_file)
#
## Check fields for each product (with stats)
#dict_fields = {}
#for dict_product in period_file:
#  for product_key in dict_product.keys():
#    dict_fields.setdefault(product_key, []).append(dict_product.get('product_title', None))
#for k,v in dict_fields.items():
#  print k, len(v)

# ###################
# BUILD DF MASTER
# ###################

ls_loop = [[path_price_bu_duplicates, date(2012,11,22), date(2013,4,11)],
           [path_price_source, date(2013,4,11), date(2013,8,9)]]

for path_temp, start_date, end_date in ls_loop:
  ls_dates = get_date_range(start_date, end_date)
  ls_df_products = []
  for date_str in ls_dates:
    path_file = os.path.join(path_temp,
                             '{:s}_auchan_velizy'.format(date_str))
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
  
  # ################
  # CLEAN DF MASTER
  # ################
  
  def fix_unit_price(x):
    x = re.sub('&euro;$', '', x)
    x = x.replace(' <br /> ', ' ')
    return x
  
  df_master['product_unit_price'] =\
    df_master['product_unit_price'].apply(lambda x: fix_unit_price(x))
  
  # todo: split (later)
  #df_master['unit'] =\
  #   df_master['product_unit_price'].apply(lambda x: re.search('^(.*?): ', x).group(1))
  
  def fix_total_price(x):
    x = re.sub('<span>&euro;</span></sub>$', '', x)
    x = x.replace(' <sub>', '')
    return x
  
  df_master['product_total_price'] =\
    df_master['product_total_price'].apply(lambda x: fix_total_price(x))
  
  def fix_product_flag(x):
    x = re.sub('angle(\sflag_)?', '', x)
    return x
  
  df_master['product_flag'] =\
    df_master['product_flag'].apply(lambda x: fix_product_flag(x))
  
  def fix_product_promo(x):
    if x:
      x = x.replace(' <sup>%</sup>', '%')
      x = x.replace(' <sup>&euro;</sup>', 'euros')
    return x
  
  df_master['product_promo'] =\
    df_master['product_promo'].apply(lambda x: fix_product_promo(x))
  
  df_master['product_promo_vignette'] =\
    df_master['product_promo_vignette'].apply(lambda x: x.replace('&#8364;',
                                                                    'euros') if x else x)
  
  for field in ['product_title', 'department', 'sub_department']:
    df_master[field] =\
      df_master[field].apply(lambda x: x.strip()\
                                        .replace(u'&amp;', u'&')\
                                        .replace(u'&Agrave;', u'À')\
                                        .replace(u'&ndash;', u'-')\
                                        .replace(u'&OElig;', u'Œ')
                               if x else x)
  
  # Some harmonization in sub_department
  dict_repl_subdpt = {u'Idées apréritives' : u'Idées apéritives',
                      u'Hygiène intime - Incontinences' :\
                         u'Hygiène intime - Incontinence',
                      u'Lessive' : u'Lessives',
                      u'Shampoings' : u'Shampooings'}
  for old, new in dict_repl_subdpt.items():
    df_master.loc[df_master['sub_department'] == old,
                  'sub_department'] = new
  
  #ls_di = ['department', 'sub_department', 'product_title',
  #         'product_total_price', 'product_unit_price',
  #         'available', 'product_promo', 'product_promo_vignette']
  
  df_master.columns = [col.replace('product_', '') for col in df_master.columns]
  ls_di = ['department', 'sub_department', 'title',
           'total_price', 'unit_price',
           'available', 'promo', 'promo_vignette']
  
  print u'\nInspect dpt and subdpts:'
  print df_master[['department', 'sub_department']].drop_duplicates().to_string()
  
  print u'\nNo sub_department (top 20):'
  print df_master[ls_di][df_master['sub_department'].isnull()][0:20].to_string()
  
  print u'\nFilled sub_department (top 20):'
  print df_master[ls_di][~df_master['sub_department'].isnull()][0:20].to_string()

  df_master.to_csv(os.path.join(path_price_built_csv,
                                'df_auchan_velizy_{:s}_{:s}.csv'\
                                   .format(ls_dates[0], ls_dates[-1])),
                   encoding = 'utf-8',
                   index = False)

## ##############################
## CHECK DUPLICATES IN ONE PERIOD
## ##############################
#
#df_period = df_master[df_master['date'] == ls_dates[0]].copy()
#
#print u'\nNb duplicates based on dpt, sub_dpt, prod_title:'
#print len(df_period[df_period.duplicated(['department',
#                                          'sub_department',
#                                          'title'])])
#
#print u'\nNb duplicates based on prod_title:'
#print len(df_period[df_period.duplicated(['title'])])
#
#print u'\nNb with no dpt or sub_dpt'
#print len(df_period[(df_period['department'].isnull()) |\
#                    (df_period['sub_department'].isnull())])
#
#print u'\nNb with no sub_dpt:'
#print len(df_period[df_period['sub_department'].isnull()])
#
## VISUAL INSPECTION
#print u'\n', df_period[df_period.duplicated(['department',
#                                             'sub_department',
#                                             'title'])].to_string()
#
#print u'\n', df_period[df_period['title'] == 'carottes sachet 1kg'].to_string()
#
#print u'\'n', len(df_period[df_period.duplicated(['department',
#                                                  'title'])])
#
#print u'\n', len(df_period[df_period.duplicated(['department',
#                                                 'sub_department',
#                                                 'title'])])
#
## Duplicates due to one line for regular price and one for promo price
## Note sure if all duplicates are legit (carottes sachet in épicerie?)
#
## Check if no subdpt (None) are always duplicates?
#ls_prod_nosd = df_period['title'][df_period['sub_department'].isnull()]\
#                 .unique().tolist()
#print u'\nNb of prod with no sub_dpt: {:d}'.format(len(ls_prod_nosd))
#
#ls_prod_nosd_dup = df_period['title'][(df_period.duplicated(['title'])) &\
#                                      (df_period['title'].isin(ls_prod_nosd))]\
#                     .unique().tolist()
#print u'\nNb of prod with no sub_dpt and dup exists: {:d}'.format(len(ls_prod_nosd_dup))
## Seems ok to drop anytime no sub_dpt since duplicate exists
#
## Check if promo always imply two lines: reg and promo price (check in more recent df?)
## actually with df_period['flag']: even more promo
#ls_prod_promo = df_period['title'][(~df_period['promo_vignette'].isnull()) |
#                                   (~df_period['promo'].isnull())]\
#                  .unique().tolist()
#print u'\nNb of prod with promo: {:d}'.format(len(ls_prod_promo))
#
#ls_prod_promo_dup = df_period['title'][(df_period.duplicated(['title'])) &\
#                                      (df_period['title'].isin(ls_prod_promo))]\
#                      .unique().tolist()
#print u'\nNb of prod with no sub_dpt and dup exists: {:d}'.format(len(ls_prod_promo_dup))
## There is not always a duplicate but can drop if so (regular price is interesting tho)
## Caution: might be duplicates due to several dpts... not always reg and promo price
#
## todo: except for products with regular and promo price... check same price
#len(df_period['title'].unique())
#len(df_period[['title', 'total_price']].drop_duplicates())
#
#df_ttp = df_period[['title', 'total_price']].drop_duplicates()
#ls_dup_ttp = df_ttp['title'][df_ttp.duplicated(['title'])].unique().tolist()
#print df_period[df_period['title'].isin(ls_dup_ttp)].to_string()
#
## Get all (unique) legit (product, dpt, subdpt)
## Too slow if want to run with df_master
#ls_legit_pds = []
#for x in df_period[['title', 'department', 'sub_department']].values:
#  if tuple(x) not in ls_legit_pds:
#    ls_legit_pds.append(tuple(x))
#
#df_pds = df_master[['title', 'department', 'sub_department']].drop_duplicates()
#df_pds.sort(['title', 'department', 'sub_department'], inplace = True)
