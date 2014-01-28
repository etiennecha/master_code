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

date = '121210'
master = dec_json('%s\\20%s_auchan_velizy' %(json_folder, date))

#
# FUNCTIONS
#

# STATS DES

# function to get a list of unique products
def get_list_products(master_list_products):
  print 'Elements found twice or more'
  list_products = []
  for elt in master_list_products:
    if elt['product_title'] not in list_products:
      list_products.append(elt['product_title'])
    """
    else:
      print elt['product_title'], elt['sub_department']
    """
  print 'End of Elements found twice or more'
  return(list_products)

# function to single out field occurences and count them
def single_and_count(master_list_products, field):
  dico_occurences = {}
  for product in master_list_products:
    if product[field] in dico_occurences.keys():
      dico_occurences[product[field]] += 1
    else:
      dico_occurences[product[field]] = 1
  return dico_occurences

# function to get a subsample of products based on several criteria (kind of similar to SQL extraction)
def get_product_sample(master_list_products, dico_criteria):
  # e.g. dico_criteria = {'sub_department':'Insecticides'}
  product_sample = []
  for product in master_list_products:
    match = 1
    for field, criterion in dico_criteria.iteritems():
      if product[field] != criterion:
        match = 0
    if match == 1:
      product_sample.append(product)
  return product_sample

#
# COOKING
#

# unique field occurences
master_fields = ['department', 'sub_department', 'product_flag', 'available']
fields_summary = []
for elt in master_fields:
  fields_summary.append(single_and_count(master, elt))

# list of products
list_unique_products = get_list_products(master)

# count products with special offers (CAUTION: SO FAR AFFECTED BY DOUBLES)
nb_sales = 0
for elt in master:
  if elt['product_promo'] != [] or elt['product_promo_vignette'] != []:
    nb_sales += 1
print 'there are', nb_sales, 'products on sales'

# product subsample
product_sample_test = get_product_sample(master, {'sub_department':'Insecticides'})

# example of double
product_sample_double = get_product_sample(master, {'product_title' : [u'Vitroclean 200ml']})

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