#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import cookielib
from cookielib import Cookie
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import re
import json
import string
from datetime import date
import time

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def enc_stock_json(database, chemin):
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

def html_unescape(text):
  text = text.replace(u'&gt;', '>').replace(u'&lt', '<')
  text = text.replace('<\/p>', '</p>').replace('<\/a>', '</a>')
  text = text.replace('<\/div>','</div>').replace('<\/span>','</span>')
  text = text.replace('<\/sub>','</sub>').replace('<\/sup>','</sup>')
  text = text.replace('<\/input>','</input>').replace('<\/form>','</form>')
  return text

def convert_to_str(list_beautifulsoup):
  # too restrictive... (breaks total price)
  list_of_string = []
  if list_beautifulsoup:
    for element in list_beautifulsoup:
      if isinstance(element, basestring):
        element = element.replace(r'\n','').replace(r'\t','')
        element = element.replace(r'<\/p>','').replace('</span>','')
        element = element.replace(r'<sub>','').replace('</sub>','')
        list_of_string.append(element.strip())
  return list_of_string

# build urllib2 opener
cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [('User-agent',
                      'Mozilla/5.0 (Windows NT 6.1; WOW64) '+\
                        'AppleWebKit/537.11 (KHTML, like Gecko) '+\
                        'Chrome/23.0.1271.64 Safari/537.11')]
urllib2.install_opener(opener)

if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
  path_data = r'W:\Bureau\Etienne_work\Data'
else:
  path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
# structure of the data folder should be the same
folder_drive_auchan = r'\data_drive_supermarkets\data_auchan'
folder_source_plaisir = r'\data_source\data_json_auchan_plaisir'

# Open welcome page and get list of stores
auchan_drive_website_url = r'http://www.auchandrive.fr'
response = urllib2.urlopen(auchan_drive_website_url)
data = response.read()
soup = BeautifulSoup(data)

list_drive_blocks = soup.findAll('li', {'class' : re.compile('dpt*')})
list_drive_url = []
for drive_block in list_drive_blocks:
  list_drive_url.append(drive_block('a')[0]['href'])

# Open a store page
cookie_jar.set_cookie(makeCookie('auchanCook','"935|"'))
plaisir_url_extension = soup.find('a', {'title' : u'D\xe9partement 78, Plaisir'})['href']
response_2 = urllib2.urlopen(auchan_drive_website_url + plaisir_url_extension)
data_2 = response_2.read()
soup_2 = BeautifulSoup(data_2)

list_dpt_blocks = soup_2.findAll('div', {'class' : 'item-content'})
list_dpt_titles = [dpt_block.find('p', {'class' : 'titre'}).string \
                       if dpt_block.find('p', {'class' : 'titre'}) else None \
                       for dpt_block in list_dpt_blocks]

dict_dpt_sub_dpt_urls = {}
for dpt_ind, dpt_title in enumerate(list_dpt_titles):
  if dpt_title:
    list_sub_dpt_blocks = list_dpt_blocks[dpt_ind].findAll('a', {'title' : re.compile('.*')})
    list_tuple_sub_dpts = [(sub_dpt_block['title'], sub_dpt_block['href'])\
                            for sub_dpt_block in list_sub_dpt_blocks\
                            if u'voir tous les produits' not in sub_dpt_block['title']\
                              and u'Solutions moins ch\xe8res' not in sub_dpt_block['title']]
    dict_dpt_sub_dpt_urls[dpt_title] = list_tuple_sub_dpts

# Open a store's sub dpt pages
# TODO: finish (affichePopinProduit + addProductToShoppingList2 blocks)

ls_ls_products = []
ls_ls_product_blocks = []

for dpt_title, list_tuple_sub_dpts in dict_dpt_sub_dpt_urls.items(): #  => u'Produits Frais'
  for (sub_dpt_title, sub_dpt_url) in list_tuple_sub_dpts: # => u'Boucherie'
    time.sleep(1)
    response_3 = urllib2.urlopen(auchan_drive_website_url + sub_dpt_url)
    data_3 = response_3.read()
    soup_3 = BeautifulSoup(data_3)
    # all results on page
    all_block = soup_3.find('a', {'id' : 'productsCountForm_2'})
    if all_block:
      all_products_url = all_block['href']
      all_products_param_re = re.search('t:ac=(.*)',all_block['href'])
      if all_products_param_re:
        all_products_param = all_products_param_re.group(1)
        dict_params = {'t%3Azoneid' : 'itemsList'}
        headers = {'Referer' : auchan_drive_website_url + sub_dpt_url,
                   'X-Requested-With' : 'XMLHttpRequest',
                   #'X-Prototype-Version' : '1.6.0.3',
                   'Content-type' : 'application/x-www-form-urlencoded; charset=UTF-8'}
        params = urllib.urlencode(dict_params)  
        req  = urllib2.Request(auchan_drive_website_url + all_products_url, params, headers)
        response_4 = urllib2.urlopen(req)
        data_4 = response_4.read().decode('utf-8')
        
        good_part = re.search('<!-- FIN PAGINATION -->(.*?)<!-- PAGINATION -->', data_4)
        html_candidate = good_part.group(1)
        
        # TODO: extraction from second block
        re_pat_1 = r"<a id='affichePopinProduit.*?<div class='clear'>"
        re_pat_2 = r"<a id='addProductToShoppingList2.*?<\\/div>\\n\\t\\t<\\/div>\\n\\t<\\/div>"
        list_product_blocks_1 = re.findall(re_pat_1, html_candidate)
        list_product_blocks_2 = re.findall(re_pat_2, html_candidate)
        
        if len(list_product_blocks_1) == len(list_product_blocks_2):
          for product_block_1, product_block_2 in zip(list_product_blocks_1, list_product_blocks_2):
            # TODO: keep product id (and check it's the same for both blocks)
            # block product txt info
            soup_product_1 = BeautifulSoup(html_unescape(product_block_1))
            ls_product_info_blocks = soup_product_1.findAll('p', {'class' : re.compile('.*')})
            ls_product_info = [(info['class'], info.findAll(text=True)) for info in ls_product_info_blocks]
            ls_product_info = [(
                                product_info[0], 
                                [elt.replace('\\n', '').replace('\\t', '') for elt in product_info[1]]
                               ) if product_info[1] else (product_info[0],[]) for product_info in ls_product_info ]
            # block vignettes / images
            soup_product_2 = BeautifulSoup(html_unescape(product_block_2))
            ls_product_img_blocks = soup_product_2.findAll('img', {'alt' : re.compile('.*')})
            if ls_product_img_blocks:
              ls_product_img_blocks = [img_block['alt'] for img_block in ls_product_img_blocks]
            ls_product_info += [('ls_imgs', ls_product_img_blocks),
                                ('dpt', dpt_title),
                                ('subdpt', sub_dpt_title)]
            ls_ls_products.append(dict(ls_product_info))
            ls_ls_product_blocks.append((soup_product_1, soup_product_2))
        else:
          print 'list_product_blocks_i: different sizes:', dpt_title, sub_dpt_title
      else:
        print 'all_products_param_re: None', dpt_title, sub_dpt_title
    else:
      print 'all_block: None', dpt_title, sub_dpt_title

# FOR PRODUCTION
today_date = date.today().strftime("%y%m%d")
enc_stock_json(ls_ls_products, path_data +\
                               folder_drive_auchan +\
                               folder_source_plaisir +\
                               r'\20%s_auchan_plaisir_new' %today_date)