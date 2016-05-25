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

# Visit website
website_url = u'http://vins-champagnes.carrefour.fr/'
response = urllib2.urlopen(website_url)
data = response.read()
soup = BeautifulSoup(data)
# header_nav = soup.find('ul', {'id' : 'header_new_nav'})

# Seems enough to loop on this page (for France at least)

dict_info = {}
dict_prices = {}

for i in range(1, 37):
  ref_page_url = u'http://vins-champagnes.carrefour.fr/' +\
                 u'catalogue-region.php?id=87&langue=fr&monnaie=eur&pays=fr' +\
                 u'&pageID={:d}#accestop'.format(i)
  response = urllib2.urlopen(ref_page_url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  # Need to collect and reconcile two blocks for each bottle
  # Both contain url of fiche-produit => stored in two dicts to avoid mistakes
  ls_bloc_prod_info = soup.findAll('div', {'class' : 'box_listing_1col'})
  ls_bloc_prod_price = soup.findAll('div', {'class' : 'box_listing_choix_conditionnement'})
  
  # Extract info for each product
  
  ls_info_txt_fields = ['box_listing_nom_produit',
                        'box_fiche_produit_type_vin_txt',
                        'box_listing_descriptif',
                        'box_fiche_produit_type_vin_txt']
  
  for bloc_prod_info in ls_bloc_prod_info:
  
    bloc_name = bloc_prod_info.find('div', {'class' : 'box_listing_nom_produit'})
    href = None
    if bloc_name and bloc_name.a:
      href = bloc_name.a['href']
  
    # List of txt fields
    ls_prod_info = []
    for info_txt_field in ls_info_txt_fields:
      bloc_info_temp = bloc_prod_info.find('div', {'class' : info_txt_field})
      ls_prod_info.append([info_txt_field, extract_bs_text(bloc_info_temp)])
    
    # list (to be processed later)
    bloc_situation = bloc_prod_info.find('ul', {'class' : 'box_listing_situation'})
    ls_situation = []
    if bloc_situation:
      ls_situation = [extract_bs_text(field) for field in bloc_situation.findAll('li')]
    ls_prod_info.append(['situation', ls_situation])
    
    # span... not sure, text might be enough
    bloc_info_cl = bloc_prod_info.find('span', {'class' : 'box_listing_cl'})
    info_cl = extract_bs_text(bloc_info_cl)
    ls_prod_info.append(['info_cl', info_cl])
  
    dict_info[href] = ls_prod_info
  
  # Extract prices for each product
  
  ls_price_txt_fields = ['box_conditionnement_lot',
                         'box_conditionnement_prix']
  
  for bloc_prod_price in ls_bloc_prod_price:
    
    href = None
    bloc_btn_panier = bloc_prod_price.find('a', {'class' : 'btn_panier_etape_rouge_conteneur',
                                                 'href' : True})
    if bloc_btn_panier: 
      href = bloc_btn_panier['href']
    
    ls_prod_prices = []
    ls_price_blocs = bloc_prod_price.findAll('div', {'class' : 'box_conditionnement'})
    for price_bloc in ls_price_blocs:
      ls_prices = [[price_txt_field,
                    extract_bs_text(price_bloc.find('div', {'class' : price_txt_field}))]\
                      for price_txt_field in ls_price_txt_fields]
      # span prix unitaire
      price_field = 'box_conditionnement_prix_unitaire'
      bloc_pu = price_bloc.find('div', {'class' : price_field})
      price_pu = [price_field, None]
      if bloc_pu:
        price_pu = [price_field, ' '.join(bloc_pu.findAll(text = True))]
      ls_prices.append(price_pu)                     
      ls_prod_prices.append(ls_prices)
                          
    dict_prices[href] = ls_prod_prices

path_current_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
enc_json(dict_prices,
         os.path.join(path_current_dir, u'dict_carrefour_prelim_prices.json'))
enc_json(dict_info,
         os.path.join(path_currentçdir, u'dict_carrefour_prelim_info.json'))
