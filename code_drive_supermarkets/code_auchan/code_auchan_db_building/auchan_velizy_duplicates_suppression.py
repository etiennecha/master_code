import os
import json
import sqlite3
import datetime
from datetime import date, timedelta

# path_data: data folder at different locations at CREST vs. HOME
# could do the same for path_code if necessary (import etc).
if os.path.exists(r'W:/Bureau/Etienne_work/Data'):
  path_data = r'W:/Bureau/Etienne_work/Data'
elif os.path.exists(r'C:/Users/etna/Desktop/Etienne_work/Data'):
  path_data = r'C:/Users/etna/Desktop/Etienne_work/Data'
else:
  path_data = r'/mnt/Data'
# structure of the data folder should be the same
folder_source_auchan_velizy_prices_bu_duplicates = r'/data_drive_supermarkets/data_auchan/data_source/data_json_auchan_velizy/bu_duplicates'
folder_source_auchan_velizy_prices = r'/data_drive_supermarkets/data_auchan/data_source/data_json_auchan_velizy'

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
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
    product['product_unit_price'] = product['product_unit_price'][2].replace('&euro;','').replace(',','.')
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
ref_file = dec_json(path_data + folder_source_auchan_velizy_prices + r'/20130411_auchan_velizy')

# Explore duplicates from reference file
set_subdpt_ref = set([product['sub_department'] for product in ref_file]) # compare set with other files
# One more dpt in ref (recent one) vs. old: produits du monde disappeared (?)
list_prod_ref = [product['product_title'][0] for product in ref_file]
set_prod_ref = set(list_prod_ref)
print 'Products in reference period: list vs set number', len(list_prod_ref),'vs' , len(set_prod_ref)
dict_prod_ref = {}
for product in ref_file:
  dict_prod_ref.setdefault(product['product_title'][0], [])
  dict_prod_ref[product['product_title'][0]].append(product['sub_department'])
"""
for product in get_list_no_duplicates(list_prod_ref):
	if len(dict_prod_ref[product])!=1:
		print [subdpt.strip() for subdpt in dict_prod_ref[product] if subdpt],'        ', product
"""
# A lot of duplicates remain which are natural duplicates and not mistakes as in old files
# Keep them and consider the various sub-dpt/dpt as an info of the product
# We are back to a list (products) of list (daily prices) structure
# CAUTION: sales info (even price???) could be inconsistent for the same products in different sub-dpts???

# Get list of (product, sub_department)
list_prod_subdpt_ref = [(product['product_title'][0], product['sub_department']) for product in ref_file]

# #################################################################
# 2: Loop over files w/ duplicates
#    Suppress if product in list but not (product, sub_department)
# #################################################################

start_date = date(2012,11,22)
end_date = date(2013,4,10)
# can't use till 2013,05,13 (last avail. date) due to MemoryError
master_dates = date_range(start_date, end_date)
for date_str in master_dates:
  if os.path.exists(path_data + folder_source_auchan_velizy_prices_bu_duplicates + r'/%s_auchan_velizy' %date_str):
    period_file = dec_json(path_data + folder_source_auchan_velizy_prices_bu_duplicates + r'/%s_auchan_velizy' %date_str)

    # Get rid of irrelevant duplicates for products still listed after scraping script correction
    # Get rid of products with 'None' as sub-dpt    
    list_prod_before = [product['product_title'][0] for product in period_file]
    set_prod_before = set(list_prod_before) 
    print 'Products in dupl period before: list vs set number', len(list_prod_before),'vs' , len(set_prod_before)
    clean_period_file = [product for product in period_file if ((product['product_title'][0], product['sub_department']) in list_prod_subdpt_ref or product['product_title'][0] not in list_prod_ref) and product['sub_department']]
    list_prod_after= [product['product_title'][0] for product in clean_period_file]
    set_prod_after= set(list_prod_after)
    print 'Products in dupl period after: list vs set number', len(list_prod_after),'vs' , len(set_prod_after)
    
    # Check results (in particular products no more listed in ref files)
    dict_prod_period_after = {}
    for product in clean_period_file:
      dict_prod_period_after.setdefault(product['product_title'][0], [])
      dict_prod_period_after[product['product_title'][0]].append(product['sub_department'])
    
    # Idea: find those products which wrongly belong to several sub-dpts
    # Look for a mapping between wrong multi-sub-dpt belonging and the right classification
    # Check if this mapping can be use (bijection?) to suppress some irrelevant duplicates
    # Mapping is contained in dict_sets_differences
    dict_prod_period = {}
    for product in period_file:
      dict_prod_period.setdefault(product['product_title'][0], [])
      dict_prod_period[product['product_title'][0]].append(product['sub_department'])
    dict_sets_differences = {}
    for product, list_sub_departments in dict_prod_period.iteritems():
      if product in set_prod_ref:
      # product in recent and old
        set_prod_period_string = ';;;'.join([elt.strip() for elt in list(set(list_sub_departments)) if elt])
        if not dict_sets_differences.get(set_prod_period_string):
          # product (old) not read so far: in dict key are old categories, contents are recent (thus correct) categories
          dict_sets_differences[set_prod_period_string] = [elt.strip() for elt in list(set(dict_prod_ref[product])) if elt]
        else:
          # product (old) is present more than once
          if dict_sets_differences[set_prod_period_string] != [elt.strip() for elt in list(set(dict_prod_ref[product])) if elt]:
            # different new category association for this product
            # turns out intersection is empty only once so keep it in general:
            list_sub_1 = dict_sets_differences[set_prod_period_string]
            list_sub_2 = [elt.strip() for elt in list(set(dict_prod_ref[product])) if elt]
            if [x for x in list_sub_1 if x in list_sub_2]:
              dict_sets_differences[set_prod_period_string] = [x for x in list_sub_1 if x in list_sub_2]
            """
            print 'Diff', product,'---->', ' -- '.join([elt.strip() for elt in list(set(list_sub_departments)) if elt])
            print '1:', ' -- '.join(list_sub_1)
            print '2:', ' -- '.join(list_sub_2)
            print 'intersection', [x for x in list_sub_1 if x in list_sub_2], '\n'
            """

    # Apply mapping
    c = 0
    for product, list_sub_departments in dict_prod_period_after.iteritems():
      if dict_sets_differences.get(';;;'.join([elt.strip() for elt in list(set(list_sub_departments)) if elt])):
        dict_prod_period_after[product] = dict_sets_differences[';;;'.join([elt.strip() for elt in list(set(list_sub_departments)) if elt])]
        c+=1
      dict_prod_period_after[product] = list(set([elt.strip() for elt in dict_prod_period_after[product]]))
    """
    # Check: doesn't look bad
    for product in get_list_no_duplicates(list_prod_after):
	    if len(dict_prod_period_after[product])!=1:
		print [subdpt.strip() for subdpt in dict_prod_period_after[product] if subdpt],'        ', product
    """
    
    # Now get tuples and keep only (product, sub_dpt) if part of it
    list_clean_tuples = []
    for product, list_sub_departments in dict_prod_period_after.iteritems():
      for sub_department in list_sub_departments:
        list_clean_tuples.append((product, sub_department))
    clean_period_final_file = [product for product in clean_period_file if product['sub_department'] and (product['product_title'][0], product['sub_department'].strip()) in list_clean_tuples]
    print len(clean_period_final_file), 'number of observations after cleaning'
    enc_stock_json(clean_period_final_file, path_data + folder_source_auchan_velizy_prices + r'/%s_auchan_velizy' %date_str)
  else:
    print date_str, 'is not available'