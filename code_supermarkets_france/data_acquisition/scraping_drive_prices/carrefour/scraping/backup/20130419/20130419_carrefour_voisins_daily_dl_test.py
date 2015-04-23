# -*- coding: iso-8859-1 -*-
import cookielib
from cookielib import Cookie
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

def convert_to_str(list_object):
  converted_list_object = []
  if list_object != None:
    try:
      for element in list_object:
        converted_list_object.append(str(element).decode('utf-8'))
    except:
      print 'convert_to_str: pbm with', list_object
  return converted_list_object

#path = r'\\ulysse\users\echamayou\Etienne\Python_mydocs\Scrapping_Carrefour'
path = r'C:\Users\etna\Desktop\Code\Carrefour'
json_folder = r'\carrefour_voisins_json'

# build urllib2 opener
cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.22 (KHTML, like Gecko) Chrome/25.0.1364.172 Safari/537.22')]
urllib2.install_opener(opener)

# get list of stores
# page contaings gps coordinates of shops (drives)
drive_website_url = r'http://courses.carrefour.fr'
response = urllib2.urlopen(drive_website_url + r'/drive/accueil')
data = response.read()
soup = BeautifulSoup(data)

# go on store page
shop_blocs = soup.findAll('li', {'class' : 'shop'})
shop_voisin = soup.find('li', {'id' : 215, 'class' : 'shop'})
shop_voisin_href = shop_voisin.find('a')['href']

post_args = {'id' : 'drivePickingForm_176',
             'name' : 'drivePickingForm_176'}
req = urllib2.Request(drive_website_url + shop_voisin_href)
req.add_data(urllib.urlencode(post_args))
response_2 = urllib2.urlopen(req)
data_2 = response_2.read()
soup_2 = BeautifulSoup(data_2)

def makeCookie(name, value):
  return Cookie(
    version=0,
    name=name,
    value=value,
    port=None,
    port_specified=False,
    domain="courses.carrefour.fr",
    domain_specified=True,
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

cookie_jar.set_cookie(makeCookie("serviceDrive", "3"))
cookie_jar.set_cookie(makeCookie("storeDrive", "215"))
cookie_jar.set_cookie(makeCookie("browserSupportCheck", "checked"))
# pprint.pprint(cookie_jar.__dict__)

product_links = soup_2.findAll('a', {'class' : 'page', 'href' : re.compile('/drive/tous-les-rayons/*')})
master_departments = []
master_products = []
for product_link in product_links[1:]:
  if product_link.find('img', {'alt':''}):
    # a bit fragile
    department = product_link('span')[0].contents[1].strip()
  else:
    sub_department_link  = product_link['href']
    sub_departement = product_link('span')[0].string
    try:
      master_departments.append([department, sub_departement, sub_department_link])
      response_3 = urllib2.urlopen(drive_website_url + sub_department_link)
      data_3 = response_3.read()
      soup_3 = BeautifulSoup(data_3)
      product_lis = soup_3.findAll('li', {'class' : 'product'})
      for product_li in product_lis:
        product_title_1 = product_li.find('a', {'onclick' : 'javascript:return xt_click(this, "C", "1", "Product", "N");'})('span')[0].string
        product_title_2 = product_li.find('img', {'alt' : re.compile('.*')})['alt']
        main_price_caption = product_li.find('div', {'class': 'spec price'}).find('span', {'class' : 'caption'}).string.strip()
        main_price_bloc = product_li.find('div', {'class': 'spec price'}).find('span', {'class' : 'detail'}).contents
        main_price_unit = product_li.find('div', {'class': 'specs priceSpecs'}).find('span', {'class' : 'unit'}).string.strip()
        if product_li.find('div', {'class': 'spec unitPrice'}).find('div', {'class' : 'caption'}):
          sec_price_caption = product_li.find('div', {'class': 'spec unitPrice'}).find('div', {'class' : 'caption'}).string.strip()
        else:
          sec_price_caption = ''
        if product_li.find('div', {'class': 'spec unitPrice'}).find('div', {'class' : 'detail'}):
          sec_price_bloc = product_li.find('div', {'class': 'spec unitPrice'}).find('div', {'class' : 'detail'}).contents
        else:
          sec_price_bloc = ['','','']
        dict_products = {'product_title_1' : product_title_1,
                         'product_title_2' : product_title_2,
                         'main_price_caption' : main_price_caption,
                         'main_price_bloc' : main_price_bloc,
                         'main_price_unit': main_price_unit,
                         'sec_price_caption' : sec_price_caption,
                         'sec_price_bloc' : sec_price_bloc,
                         'sub_department' : sub_departement,
                         'department' : department}
        master_products.append(dict_products)
    except:
      print [department, sub_departement, sub_department_link]

#can't encode as such: convert list elements to unicode...
# 'sec_price_bloc'
# 'main_price_bloc'
for product in master_products:
  product['sec_price_bloc'] = [unicode(elt) for elt in product['sec_price_bloc']]
  product['main_price_bloc'] = [unicode(elt) for elt in product['main_price_bloc']]

today_date = date.today().strftime("%y%m%d")
enc_stock_json(master_products, path + json_folder + r'\20%s_carrefour_voisins' %today_date)
print today_date, len(master_products)
"""