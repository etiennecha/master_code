#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
import json
import datetime
from datetime import date, timedelta
import re
import pandas as pd
import pprint

path_auchan = os.path.join(path_data,
                           u'data_drive_supermarkets',
                           u'data_auchan')

path_price_source = os.path.join(path_auchan,
                                 u'data_source',
                                 u'data_json_auchan_velizy')

path_price_bu_duplicates = os.path.join(path_price_source,
                                        u'bu_duplicates')

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
  list_dates = []
  for n in range((end_date + timedelta(1) - start_date).days):
    temp_date = start_date + timedelta(n)
    list_dates.append(temp_date.strftime('%Y%m%d'))
  return list_dates

def get_list_no_duplicates(list_with_duplicates):
  """ difference with set is that it keeps order"""
  set_elts = set([])
  list_no_duplicates = []
  for elt in list_with_duplicates:
    if elt not in set_elts:
      list_no_duplicates.append(elt)
      set_elts.add(elt)
  return list_no_duplicates

def get_formatted_file(master_period):
  for product in master_period:
    product['product_total_price'] = ''.join(product['product_total_price']).replace('<sub>','')\
                                       .replace('<span>&euro;</span></sub>','').replace(',','.')
    product['price_unit'] = product['product_unit_price'][0]
    product['product_unit_price'] = product['product_unit_price'][2].replace('&euro;','')\
                                      .replace(',','.')
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
  return master_period

# ##########################################################################
# 1: Load file w/o duplicates
#    Extract list of (product, sub_department)
# ##########################################################################

# Could loop over some files w/o duplicates in case some products disappear/reappear
ref_file = dec_json(os.path.join(path_price_source,
                                 u'20130411_auchan_velizy'))

# Explore duplicates from reference file
set_subdpt_ref = set([product['sub_department'] for product in ref_file])
# todo: compare this set with other files
# One more dpt in ref (recent one) vs. old: produits du monde disappeared (?)
ls_prod_ref = [product['product_title'][0] for product in ref_file]
set_prod_ref = set(ls_prod_ref)
print 'Nb products in reference period: {:d}'.format(len(ls_prod_ref))
print 'Nb uniques products in reference period: {:d}'.format(len(set_prod_ref))

dict_prod_ref_sds = {}
for product in ref_file:
  dict_prod_ref_sds.setdefault(product['product_title'][0], []).append(product['sub_department'])

#for product in get_list_no_duplicates(list_prod_ref):
#  if len(dict_prod_ref[product])!=1:
#    print [subdpt.strip() for subdpt in dict_prod_ref[product] if subdpt],'   ', product

# A lot of duplicates remain which are natural duplicates and not mistakes as in old files
# Keep them and consider the various sub-dpt/dpt as an info of the product
# We are back to a list (products) of list (daily prices) structure
# check if promo (and price?) are consistent for the same product in different sub-dpts???

# Get list of (product, sub_department)
ls_legit_dup_prod_subdpt = [(product['product_title'][0],
                             product['sub_department']) for product in ref_file]

# #################################################################
# 2: Loop over files w/ duplicates
#    Suppress if product in list but not (product, sub_department)
# #################################################################

start_date = date(2012,11,22)
end_date = date(2013,4,10)
# can't use till 2013,05,13 (last avail. date) due to MemoryError
ls_dates = date_range(start_date, end_date)

for date_str in ls_dates:
  print u'\nOpening file: {:s}_auchan_velizy'.format(date_str)
  path_file = os.path.join(path_price_bu_duplicates,
                           '{:s}_auchan_velizy'.format(date_str))
  if os.path.exists(path_file):
    # Check nb of product title duplicates (legit or not legit...)
    ls_products = dec_json(path_file)
    ls_prod_titles_raw = [product['product_title'][0] for product in ls_products]
    set_prod_titles_raw = set(ls_prod_titles_raw) 
    print 'Nb products in period: {:d}'.format(len(ls_prod_titles_raw))
    print 'Nb uniques products in period: {:d}'.format(len(set_prod_titles_raw))
    
    # Filter 1: based on legit duplicates found in reference files
    # Get rid of irrelevant duplicates for products still listed after scraping script correction
    # Get rid of products with 'None' as sub-dpt (not sure if should btw)
    ls_products_1 = [product for product in ls_products\
                       if (((product['product_title'][0],
                            product['sub_department']) in ls_legit_dup_prod_subdpt) or\
                          (product['product_title'][0] not in ls_prod_ref)) and\
                          product['sub_department']]
    ls_prod_titles_1 = [product['product_title'][0] for product in ls_products_1]
    set_prod_after = set(ls_prod_titles_1)
    print 'Nb products after first filter {:d}'.format(len(ls_prod_titles_1))
    
    # Check results (in particular products no more listed in ref files)
    dict_prod_1_sds = {}
    for product in ls_products_1:
      dict_prod_1_sds.setdefault(product['product_title'][0], []).append(product['sub_department'])
    
    # Idea: find those products which wrongly belong to several sub-dpts
    # Look for a mapping between wrong multi-sub-dpt belonging and the right classification
    # Check if this mapping can be use (bijection?) to suppress some irrelevant duplicates
    # Mapping is contained in dict_sets_differences
    dict_prod_sds = {}
    for product in ls_products:
      dict_prod_sds.setdefault(product['product_title'][0], []).append(product['sub_department'])
    dict_sets_differences = {}
    for product, ls_prod_sds in dict_prod_sds.items():
      if product in set_prod_ref:
      # product in recent and old
        tup_prod_sds = tuple([elt.strip() for elt in list(set(ls_prod_sds)) if elt])
        if not dict_sets_differences.get(tup_prod_sds):
          # product (old) not read so far: in dict key are old categories...
          # ... contents are recent (thus correct) categories
          dict_sets_differences[tup_prod_sds] =\
            [elt.strip() for elt in list(set(dict_prod_ref_sds[product])) if elt]
        else:
          # product (old) is present more than once
          if dict_sets_differences[tup_prod_sds] !=\
               [elt.strip() for elt in list(set(dict_prod_ref_sds[product])) if elt]:
            # different new category association for this product
            # turns out intersection is empty only once so keep it in general:
            list_sub_1 = dict_sets_differences[tup_prod_sds]
            list_sub_2 = [elt.strip() for elt in list(set(dict_prod_ref_sds[product])) if elt]
            if [x for x in list_sub_1 if x in list_sub_2]:
              dict_sets_differences[tup_prod_sds] = [x for x in list_sub_1 if x in list_sub_2]

            # Three or more sub_dpts
            for k,v in dict_sets_differences.items()[20:40]:
              if len(k) >= 3:
                print u'\n'
                print k
                print v

    # Apply mapping: update dict_prod_1_sds
    c = 0
    for product, ls_prod_sds in dict_prod_1_sds.items():
      tup_prod_sds = tuple([elt.strip() for elt in list(set(ls_prod_sds)) if elt])
      if dict_sets_differences.get(tup_prod_sds):
        dict_prod_1_sds[product] =\
            dict_sets_differences[tup_prod_sds]
        c+=1
      dict_prod_1_sds[product] = list(set([elt.strip() for elt in dict_prod_1_sds[product] if elt]))
    ## Check: doesn't look bad
    #for product in get_list_no_duplicates(list_prod_after):
	  #  if len(dict_prod_period_after[product])!=1:
		#print [subdpt.strip() for subdpt in dict_prod_period_after[product] if subdpt],'        ', product
    
    # Now get list of legit (product, sub_department)
    ls_clean_tuples = []
    for product, ls_prod_sds in dict_prod_1_sds.items():
      for sd in ls_prod_sds:
        ls_clean_tuples.append((product, sd))

    # Keep only products if legit (product, sub_department)
    ls_products_2 = [product for product in ls_products_1\
                       if (product['product_title'][0], product['sub_department'].strip()) in ls_clean_tuples]

    print 'Nb products after second filter {:d}'.format(len(ls_products_2))
    # enc_json(ls_products_2, path_data + folder_source_auchan_velizy_prices + r'/%s_auchan_velizy' %date_str)
  
    # Temp
    break
  
  else:
    print date_str, 'is not available'

## #################################
## INVESTIGATION: NEW WAY TO PROCEED
## #################################
#
## READ ONE FILE WITH PANDAS
#path_file = os.path.join(path_price_bu_duplicates,
#                         '{:s}_auchan_velizy'.format(ls_dates[0]))
#period_file = dec_json(path_file)
#
### Check fields for each product (with stats)
##dict_fields = {}
##for dict_product in period_file:
##  for product_key in dict_product.keys():
##    dict_fields.setdefault(product_key, []).append(dict_product.get('product_title', None))
##for k,v in dict_fields.items():
##  print k, len(v)
#
## Get fields for each product (short)
#ls_all_fields = []
#for dict_product in period_file:
#  ls_all_fields += dict_product.keys()
#ls_fields = list(set(ls_all_fields))
#
#ls_rows_products = []
#for dict_product in period_file:
#  row = [dict_product.get(field, 'None') for field in ls_fields]
#  row = [' '.join(x) if isinstance(x, list) else x for x in row]
#  row = [x if x else None for x in row]
#  ls_rows_products.append(row)
#
#df_products = pd.DataFrame(ls_rows_products,
#                           columns = ls_fields)
#
#print u'\nNb duplicates based on dpt, sub_dpt, prod_title:'
#print len(df_products[df_products.duplicated(['department',
#                                              'sub_department',
#                                              'product_title'])])
#
#print u'\nNb duplicates based on prod_title:'
#print len(df_products[df_products.duplicated(['product_title'])])
#
#print u'\nNb with no dpt or sub_dpt'
#print len(df_products[(df_products['department'].isnull()) |\
#                      (df_products['sub_department'].isnull())])
#
#print u'\nNb with no sub_dpt:'
#print len(df_products[df_products['sub_department'].isnull()])
#
## Perform some cleaning
#
#def fix_unit_price(x):
#  x = re.sub('&euro;$', '', x)
#  x = x.replace(' <br /> ', ' ')
#  return x
#
#df_products['product_unit_price'] =\
#  df_products['product_unit_price'].apply(lambda x: fix_unit_price(x))
#
## todo: split (later)
##df_products['unit'] =\
##   df_products['product_unit_price'].apply(lambda x: re.search('^(.*?): ', x).group(1))
#
#def fix_total_price(x):
#  x = re.sub('<span>&euro;</span></sub>$', '', x)
#  x = x.replace(' <sub>', '')
#  return x
#
#df_products['product_total_price'] =\
#  df_products['product_total_price'].apply(lambda x: fix_total_price(x))
#
#def fix_product_flag(x):
#  x = re.sub('angle(\sflag_)?', '', x)
#  return x
#
#df_products['product_flag'] =\
#  df_products['product_flag'].apply(lambda x: fix_product_flag(x))
#
#def fix_product_promo(x):
#  if x:
#    x = x.replace(' <sup>%</sup>', '%')
#    x = x.replace(' <sup>&euro;</sup>', 'euros')
#  return x
#
#df_products['product_promo'] =\
#  df_products['product_promo'].apply(lambda x: fix_product_promo(x))
#
#df_products['product_promo_vignette'] =\
#  df_products['product_promo_vignette'].apply(lambda x: x.replace('&#8364;',
#                                                                  'euros') if x else x)
#
## Check products without sub_department
#
##ls_di = ['department', 'sub_department', 'product_title',
##         'product_total_price', 'product_unit_price',
##         'available', 'product_promo', 'product_promo_vignette']
#
#df_products.columns = [col.replace('product_', '') for col in df_products.columns]
#ls_di = ['department', 'sub_department', 'title',
#         'total_price', 'unit_price',
#         'available', 'promo', 'promo_vignette']
#
#print u'\nNo sub_department:'
#print df_products[ls_di][df_products['sub_department'].isnull()].to_string()
#
#print u'\nFilled sub_department:'
#print df_products[ls_di][~df_products['sub_department'].isnull()][0:20].to_string()
#
## Check potential problem
#print u'\nCheck potential problem:'
#for x in period_file:
#  if x['product_title'][0] == u'Auchan Mieux Vivre Bio ail filet 3 têtes 250g':
#    pprint.pprint(x)
#    break
