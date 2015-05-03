#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
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

def dec_json(path_data):
  with open(path_data, 'r') as f:
    return json.loads(f.read())

def enc_json(data, path_data):
  with open(path_data, 'w') as f:
    json.dump(data, f)

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

def extract_bs_text(soup_bloc, ls_text = True):
  if soup_bloc and ls_text:
    return soup_bloc.findAll(text = True)
  elif not soup_bloc and ls_text:
    return []
  elif soup_bloc and not ls_text:
    return soup_bloc.text
  elif not soup_bloc and not ls_text:
    return None

def parse_product_page(soup_products):
  ls_dict_products = []
  # Parse products
  ls_prod_blocs = soup_products.findAll('div', {'class' : 'vignette-box'})
  # print len(ls_prod_blocs_1)
  for bloc_prod in ls_prod_blocs:
    # product availability, product promo
    prod_available_dum = 'yes'
    if bloc_prod.find('div', {'class' : 'vignette vignette-indispo'}):
      prod_available_dum = 'no'
    prod_promo_dum = 'no'
    if bloc_prod.find('div', {'class' : 'vignette-content promo'}):
      prod_promo_dum = 'yes'
    # product visuel
    bloc_prod_visuel = bloc_prod.find('div', {'class' : 'visuel-produit'})
    prod_img = None
    if bloc_prod_visuel and bloc_prod_visuel.find('img', {'alt' : True}):
      prod_img = bloc_prod_visuel.find('img', {'alt' : True})['alt']
    # product info
    bloc_prod_info = bloc_prod.find('div', {'class' : 'infos-produit'})
    bloc_prod_name = bloc_prod_info.find('p', {'class' : re.compile('libelle-produit.*')})
    prod_name = extract_bs_text(bloc_prod_name, ls_text = False)
    # does not accept several promo
    bloc_prod_promo =\
        bloc_prod_info.find('p', {'class' : re.compile('operation-produit.*')})
    prod_promo = [None, None]
    if bloc_prod_promo:
      prod_promo = [bloc_prod_promo['class'], # not sure why get list
                    extract_bs_text(bloc_prod_promo, ls_text = False)]
    # product price
    bloc_prod_price = bloc_prod.find('div', {'class' : 'infos-prix'})
    bloc_prod_total_price = bloc_prod_price.find('p', {'class' : 'prix-produit'})
    prod_total_price = extract_bs_text(bloc_prod_total_price)
    bloc_prod_unit_price = bloc_prod_price.find('p', {'class' : 'prix-unitaire'})
    prod_unit_price = extract_bs_text(bloc_prod_unit_price)
    # todo: add pictos
    dict_product = {'dpt' : dpt_title,
                    'sub_dpt' : sub_dpt_title,
                    'dum_available' : prod_available_dum,
                    'dum_promo' : prod_promo_dum,
                    'img' : prod_img,
                    'name' : prod_name,
                    'promo' : prod_promo,
                    'total_price' : prod_total_price,
                    'unit_price' : prod_unit_price}
    ls_dict_products.append(dict_product)
  return ls_dict_products

# build urllib2 opener
cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [('User-agent',
                      'Mozilla/5.0 (Windows NT 6.1; WOW64) '+\
                        'AppleWebKit/537.11 (KHTML, like Gecko) '+\
                        'Chrome/23.0.1271.64 Safari/537.11')]
urllib2.install_opener(opener)

# WELCOME PAGE: GET LIST OF STORES
website_url = r'http://www.auchandrive.fr'
response = urllib2.urlopen(website_url)
data = response.read()
soup = BeautifulSoup(data)

bloc_stores = soup.find('div', {'class' : 'zoneRight right float'})
bloc_li_stores = bloc_stores.find('div', {'id' : 'liste_drives'})
ls_bloc_stores = bloc_li_stores.findAll('li')

# Browse dict store markers (json)
dict_json_stores = json.loads(bloc_stores.script.text\
                                                .lstrip(u'var shopList = ')\
                                                .rstrip(u';'))
ls_dict_stores = dict_json_stores['markers']

# VELIZY DRIVE PAGE: GET DPTS AND SUB DPT LINKS
for dict_store in ls_dict_stores:
  if dict_store[u'Ville'] == u'VELIZY Cedex':
    velizy_url_extension = dict_store[u'UrlEntreeMagasin']
    break

cookie_jar.set_cookie(makeCookie('auchanCook','"935|"'))
response_2 = urllib2.urlopen(website_url + velizy_url_extension)
data_2 = response_2.read()
soup_2 = BeautifulSoup(data_2)

ls_dpt_blocs = soup_2.findAll('div', {'class' : 'item-content'})
dict_dpt_sub_dpts = {}
for dpt_bloc in ls_dpt_blocs:
  dpt_title = extract_bs_text(dpt_bloc.find('p', {'class' : 'titre'}),
                              ls_text = False)
  if dpt_title:
    ls_sub_dpt_blocs = dpt_bloc.findAll('a', {'class' : 'linkImage',
                                              'href' : True})
    ls_sub_dpts = []
    for sub_dpt_bloc in ls_sub_dpt_blocs:
      sub_dpt_href = sub_dpt_bloc['href']
      sub_dpt_title = None
      sub_dpt_img = sub_dpt_bloc.find('img', {'alt' : True})
      if sub_dpt_img:
        sub_dpt_title = sub_dpt_img['alt']
      ls_sub_dpts.append((sub_dpt_title, sub_dpt_href))
    dict_dpt_sub_dpts[dpt_title] = ls_sub_dpts

# SCRAP SUB DPT PAGES
## todo: finish (affichePopinProduit + addProductToShoppingList2 blocks)
#sub_dpt_title  = u'Cr\xe8merie'
#sub_dpt_href = u'/drive/Velizy-935/Produits-Frais-R3686962/Cremerie-3686963/'

ls_dict_products = []
for dpt_title, ls_sub_dpts in dict_dpt_sub_dpts.items():
  for (sub_dpt_title, sub_dpt_href) in ls_sub_dpts:
    time.sleep(1)
    
    response_3 = urllib2.urlopen(website_url + sub_dpt_href)
    data_3 = response_3.read()
    soup_3 = BeautifulSoup(data_3)
    
    bloc_main = soup_3.find('div', {'id' : 'central-container'}) # include all prods
    bloc_itemsList = soup_3.find('div', {'class' : 'itemsList t-zone'}) # similar
    bloc_titreCategorie = soup_3.find('div', {'class' : 'titreCategorie'}) # only forms
    
    # Display 100 items per page (appears to work)
    bloc_pagination = bloc_titreCategorie.find('div', {'class' : 'limite-pagination'})
    pagi_href = None
    if bloc_pagination:
      ls_pagi_blocs = bloc_pagination.findAll('li')
      if ls_pagi_blocs and ls_pagi_blocs[-1].find('a', {'href' : True}):
        pagi_href = ls_pagi_blocs[-1].a['href']
        # add in POST: t:zoneid = itemsList
    if pagi_href:
      dict_params = {'t%3Azoneid' : 'itemsList'}
      headers = {'Referer' : website_url + sub_dpt_href,
                 'X-Requested-With' : 'XMLHttpRequest',
                 #'X-Prototype-Version' : '1.6.0.3',
                 'Content-type' : 'application/x-www-form-urlencoded; charset=UTF-8'}
      params = urllib.urlencode(dict_params)  
      req  = urllib2.Request(website_url + pagi_href, params, headers)
      response_4 = urllib2.urlopen(req)
      data_4 = response_4.read()
      # soup_4 = BeautifulSoup(data_4)
      json_content = json.loads(data_4)
      soup_products = BeautifulSoup(json_content['zones']['itemsList'])
      ls_dict_products += parse_product_page(soup_products)

      # loop over pages
      #print json_content['inits'][0]['linkZone'][0]
      ls_pages_toloop = []
      for dict_elt in json_content['inits'][0]['linkZone']:
        url_temp = dict_elt.get('url', '')
        page_url_match  = re.match(u'/drive/rayon.productlist.pagination.topage/([0-9]*?)\?',
                                   url_temp)
        if page_url_match:
          if page_url_match.group(1) != '1':
            ls_pages_toloop.append(dict_elt)
        else:
          break
      for dict_page in ls_pages_toloop:
        page_href = dict_page['url']
        dict_params = {u'zoneId' : u'forceAjax'}
        params = urllib.urlencode(dict_params)  
        req  = urllib2.Request(website_url + page_href, params, headers)
        response_4 = urllib2.urlopen(req)
        data_4 = response_4.read()
        json_content = json.loads(data_4)
        soup_products = BeautifulSoup(json_content['zones']['itemsList'])
        ls_dict_products += parse_product_page(soup_products)
    else:
      print u'\nDisp 100 items per page did not work:', sub_dpt_title
      good_part = re.search(u'<!-- FIN PAGINATION -->(.*?)<!-- PAGINATION -->', data_3, re.DOTALL)
      html_candidate = good_part.group(1)
      soup_products = BeautifulSoup(html_candidate)
      ls_dict_products += parse_product_page(soup_products)

# INSPECT PROMO CONTENTS
# hard to be comprehensive enough in parsing

dict_promo_types = {}
for dict_product in ls_dict_products:
  if dict_product['promo'][0]:
    dict_promo_types.setdefault(dict_product['promo'][0][-1], []).append(dict_product['promo'][1])

for dict_product in ls_dict_products:
  if dict_product['dum_promo'] and not dict_product['promo'][0]:
    print dict_product
    break

## structure of the data folder should be the same
#path_auchan = os.path.join(path_data,
#                           u'data_drive_supermarkets',
#                           u'data_auchan')
#
#today_date = date.today().strftime("%Y%m%d")
#
#enc_json(ls_dict_products,
#         os.path.join(path_auchan,
#                      u'data_source',
#                      u'data_json_auchan_velizy',
#                      u'{:s}_auchan_velizy'.format(today_date))
#
#print today_date, len(ls_ls_products)
