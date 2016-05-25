#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import cookielib
from cookielib import Cookie
import urllib, urllib2
from bs4 import BeautifulSoup
import re
import json
import string
from datetime import date
import time

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def makeCookie(name, value):
  return Cookie(
    version=0,
    name=name,
    value=value,
    port=None,
    port_specified=False,
    domain="",
    domain_specified=False,
    domain_initial_dot=False,
    path="/",
    path_specified=True,
    secure=False,
    expires=None,
    discard=False,
    comment=None,
    comment_url=None,
    rest=None
   )

def extract_bs_text(bs_bloc):
  if bs_bloc:
    return bs_bloc.text
  else:
    return None

# Build urllib2 opener
cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [('User-agent',
                      'Mozilla/5.0 (Windows NT 6.1; WOW64) '+\
                        'AppleWebKit/537.11 (KHTML, like Gecko) '+\
                        'Chrome/23.0.1271.64 Safari/537.11')]
urllib2.install_opener(opener)

dict_bottle_rows = {}

for i in range(11):
  
  # Get list of bottle urls
  
  auchan_drive_website_url = u'http://www.auchan.fr/vin/c-7378053?' +\
                             u'q=%3Aranking1_double&page={:d}&show=NINETY_SIX'.format(i)
  response = urllib2.urlopen(auchan_drive_website_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  #ls_blocs_0 = soup.findAll('div', {'class' : 'span-20 productContainer last'})
  #ls_blocs_1 = soup.findAll('div', {'class' : 'product span-5 first'})
  #ls_blocs_2 = soup.findAll('div', {'class' : 'prod_grid span-5'})
  ls_blocs_3 = soup.findAll('', {'class' : 'productMainLink', 'href' : True})
  
  # Loop on bottle urls
  
  for bloc_bottle in ls_blocs_3:
    bottle_url_extension =  bloc_bottle['href']
    auchan_drive_website_url = u'http://www.auchan.fr' + bottle_url_extension
    response = urllib2.urlopen(auchan_drive_website_url)
    data = response.read()
    soup = BeautifulSoup(data)
    
    # Product title
    bloc_title = soup.find('div',
                           {'class' : 'span-11 push-1 productDescription last '}).h1
    title = extract_bs_text(bloc_title)
    ls_prod_rows = [['title', title]]
    
    # Product price
    bloc_prices = soup.find('div', {'class' : 'price_container'})
    bloc_total_price = bloc_prices.find('span', {'class': 'hideMF',
                                                 'itemprop' : 'price'})
    total_price = extract_bs_text(bloc_total_price)
    bloc_price_per_unit = bloc_prices.find('ul', {'class': 'pricePerUnit'})
    ls_ppu = []
    if bloc_price_per_unit:
      ls_ppu = [extract_bs_text(elt) for elt in bloc_price_per_unit.findAll('li')]
    # Old price if promotion
    bloc_old_price = bloc_prices.find('del', {'class' : 'pb',
                                              'id' : 'oldPriceValue'})
    old_price = extract_bs_text(bloc_old_price)
  
    ls_prod_rows += [['total_price', total_price],
                     ['price_per_unit', ls_ppu],
                     ['old_price' , old_price]]
    
    # Product description
    bloc_prod_tab = soup.find('div', {'class' : 'prod_tab',
                                      'id' : 'ProductDescriptionTabComponent'})
    prod_desc = None 
    if bloc_prod_tab:
      bloc_prod_desc = bloc_prod_tab.find('div', {'class' : 'productDescription'})
      prod_desc = extract_bs_text(bloc_prod_desc)
    
    ls_prod_rows.append(['prod_description', prod_desc])
    
    # Table Description / Caracteristiques
    bloc_table = soup.find('div', {'class' : 'prod_tab',
                                   'id' : 'ProductTechnicalTabComponent'})
    if bloc_table:
      ls_bloc_fields = bloc_table.findAll('li')
      for bloc_field in ls_bloc_fields:
        bloc_title = bloc_field.find('span',
                                     {'class': re.compile('highlightTitle.*')})
        bloc_content = bloc_field.find('div',
                                       {'class': re.compile('highlightDescription.*')})
        title = extract_bs_text(bloc_title)
        content = extract_bs_text(bloc_content)
        ls_prod_rows.append([title,content])
  
    dict_bottle_rows[bottle_url_extension] =  ls_prod_rows

path_current_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
#enc_json(dict_bottle_rows,
#         os.path.join(path_current_dir,
#                      u'dict_auchan_wine.json'))

# Caution: forgot ls_ppu in first pass hence could have info from previous if missing
# Results of first past kep in dict_bottle_rows_first_try.json
