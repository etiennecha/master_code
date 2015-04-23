# -*- coding: iso-8859-1 -*-
import cookielib
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import re
import json
import string
from datetime import date
import pprint

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def convert_to_str(element):
  return str(element).decode('utf-8')

json_folder = 'W:\\Etienne\\Python_mydocs\\Scrapping_Auchan\\auchan_velizy'

master = dec_json('%s\\new_auchan_velizy_test' %(json_folder))

# #########
# FUNCTIONS
# #########

def get_list_products(master_list_products):
  """
  function to get a list of unique products and print doubles
  problem: there are typically a lot of doubles and triples
  """
  print 'Elements found twice or more'
  list_products = []
  for elt in master_list_products:
    if elt['product_title'] not in list_products:
      list_products.append(elt['product_title'])
    else:
      print elt['product_title'], elt['sub_department']
  print 'End of Elements found twice or more'
  return(list_products)

def single_and_count(master_list_products, field):
  """
  function to single out field occurences and count them
  e.g. field = 'department'
  """
  dico_occurences = {}
  for product in master_list_products:
    if product[field] in dico_occurences.keys():
      dico_occurences[product[field]] += 1
    else:
      dico_occurences[product[field]] = 1
  return dico_occurences

def get_product_sample(master_list_products, dico_criteria):
  """
  function to get a subsample of products based on several criteria (kind of similar to SQL extraction, to be improved)
  e.g. dico_criteria = {'sub_department':'Insecticides'}
  """
  product_sample = []
  for product in master_list_products:
    match = 1
    for field, criterion in dico_criteria.iteritems():
      if product[field] != criterion:
        match = 0
    if match == 1:
      product_sample.append(product)
  return product_sample

def print_list_info(master_list_products, list_info):
  """
  function to print product information based on several criteria
  e.g. list_info = ['product_title']
  """
  product_sample = []
  for product in master_list_products:
    list_print = [product[info] for info in list_info]
    try:
      print ''.join(list_print)
    except:
      print list_print

# ################
# DATA EXPLORATION
# ################

# unique field occurences
# problem: it is false so far since there are doubles/triples (same product wrongly registered in several rayons)
master_fields = ['department', 'sub_department','rayon_title', 'product_flag', 'available']
fields_summary = []
for elt in master_fields:
  fields_summary.append(single_and_count(master, elt))

# example of products registered 3 times in database
product_sample_double = get_product_sample(master, {'product_title' : [u'Vitroclean 200ml']})

# list of unique products (dirty job, first product/rayons kept when doubles/triples)
master_unique = []
temp_unique_list = []
for elt in master:
  if elt['product_title'] not in temp_unique_list:
    master_unique.append(elt)
    temp_unique_list.append(elt['product_title'])

# count products with special offers (unique, relying on dirty job)
master_sales_unique = []
for elt in master_unique:
  if elt['product_promo'] != [] or elt['product_promo_vignette'] != []:
    master_sales_unique.append(elt)
print 'there are', len(master_sales_unique), 'products on sales (unique) out of', len(master_unique), \
      'hence', round(float(len(master_sales_unique))/float(len(master_unique)),2), '%'
sales_unique_summary = [single_and_count(master_sales_unique,x) for x in master_fields]
pprint.pprint(sales_unique_summary[0])

# count products with special offers (non unique)
master_sales = []
for elt in master:
  if elt['product_promo'] != [] or elt['product_promo_vignette'] != []:
    master_sales.append(elt)
print 'there are', len(master_sales), 'products on sales (non unique) out of', len(master), \
      'hence', round(float(len(master_sales))/float(len(master)),2), '%'
sales_summary = [single_and_count(master_sales,x) for x in master_fields]
pprint.pprint(sales_summary[0])

# print both sales product lists to see...
list_info = ['department' ,'sub_department', 'product_title']
print_list_info(master_sales_unique, list_info)
print_list_info(master_sales, list_info)

"""
Problem with subdepartments remains to be identified and corrected:

[{u'available': u'yes',
  u'department': u'Produits Frais',
  u'product_flag': u'angle ',
  u'product_promo': [],
  u'product_promo_vignette': [],
  u'product_title': [u'Jacquet pain hamburger g\xe9ant x4 -330g'],
  u'product_total_price': [u'1,', u'<sub>45<span>&euro;</span></sub>'],
  u'product_unit_price': [u'Prix/K:', u'<br />', u'4,39&euro;'],
  u'sub_department': u'Boulangerie'},
 {u'available': u'yes',
  u'department': u'Produits Frais',
  u'product_flag': u'angle ',
  u'product_promo': [],
  u'product_promo_vignette': [],
  u'product_title': [u'Jacquet pain hamburger g\xe9ant x4 -330g'],
  u'product_total_price': [u'1,', u'<sub>45<span>&euro;</span></sub>'],
  u'product_unit_price': [u'Prix/K:', u'<br />', u'4,39&euro;'],
  u'sub_department': u'P\xe2tisserie'},
 {u'available': u'yes',
  u'department': u'\xe9picerie',
  u'product_flag': u'angle ',
  u'product_promo': [],
  u'product_promo_vignette': [],
  u'product_title': [u'Jacquet pain hamburger g\xe9ant x4 -330g'],
  u'product_total_price': [u'1,', u'<sub>45<span>&euro;</span></sub>'],
  u'product_unit_price': [u'Prix/K:', u'<br />', u'4,39&euro;'],
  u'sub_department': u'Laits en poudre et concentr\xe9s                            '},
 {u'available': u'yes',
  u'department': u'\xe9picerie',
  u'product_flag': u'angle ',
  u'product_promo': [],
  u'product_promo_vignette': [],
  u'product_title': [u'Jacquet pain hamburger g\xe9ant x4 -330g'],
  u'product_total_price': [u'1,', u'<sub>45<span>&euro;</span></sub>'],
  u'product_unit_price': [u'Prix/K:', u'<br />', u'4,39&euro;'],
  u'sub_department': u'Pains &ndash; Viennoiseries &ndash; Biscottes'}]

"""