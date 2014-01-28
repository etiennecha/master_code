# -*- coding: iso-8859-1 -*-
import cookielib
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import re
import json
import string
from datetime import date

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

json_folder = r'\\ulysse\users\echamayou\Etienne\Python_mydocs\Scrapping_Auchan\auchan_velizy_json'

# build urllib2 opener
cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11')]
urllib2.install_opener(opener)

# get list of stores (useless in this script)
auchan_drive_website_url = 'http://www.auchandrive.fr'
response = urllib2.urlopen(auchan_drive_website_url)
data = response.read()
soup = BeautifulSoup(data)
lis = soup.findAll('li', {'class' : re.compile('dpt*')})
list_drive_url = []
for li in lis:
  list_drive_url.append(li('a')[0]['href'])
  # nom du drive: li('a')[0].string

# store page
drive_url = "http://www.auchandrive.fr/magasin/magasin.jsp?idMag=935"
response_2 = urllib2.urlopen(drive_url)
data_2 = response_2.read()
soup_2 = BeautifulSoup(data_2)

departments = soup_2.findAll('li', {'class' : 'HeaderNavOnglet  slider'})
list_sub_department_urls = []

# all departments within the store (collect URLs)
for department in departments:
  sub_departments = department.findAll('span', {'onclick' : re.compile('document.location.href=.*')})
  for sub_department in sub_departments:
    match_url = re.search(r'document.location.href=\'(.*)\'', sub_department['onclick'])
    if match_url:
      list_sub_department_urls.append((department('h2')[0].string, sub_department.string, match_url.group(1)))

"""
response_x = urllib2.urlopen('http://www.auchandrive.fr/magasin/rayon.jsp?channelId=479&ssChannelId=562')
data_x = response_x.read()
response_4 = urllib2.urlopen('http://www.auchandrive.fr/magasin/chargementListArticles.jsp?sort=viewNumOrdre&order=ascending&pageNum=1&channelId=479&ssChannelId=562&tous=&nbDisplay=0')
data_4 = response_4.read()
soup_4 = BeautifulSoup(data_4)
"""

# visit sub-departments
list_products = []
for (department, sub_department_title, sub_department_url) in list_sub_department_urls:
  match_sub_department_id =  re.search(r'/magasin/rayon.jsp\?channelId=(.*)', sub_department_url)
  if match_sub_department_id:
    sub_department_id = match_sub_department_id.group(1)
    # the x query may not be necessary at all
    # response_x = urllib2.urlopen('http://www.auchandrive.fr/magasin/rayon.jsp?channelId=%s' %sub_department_id)
    # data_x = response_x.read()
    if '&tous=tous' in sub_department_id:
      response_3 = urllib2.urlopen('http://www.auchandrive.fr/magasin/chargementListArticles.jsp?sort=viewNumOrdre&order=ascending&pageNum=1&channelId=%s&nbDisplay=0' %sub_department_id)
    else:
      response_3 = urllib2.urlopen('http://www.auchandrive.fr/magasin/chargementListArticles.jsp?sort=viewNumOrdre&order=ascending&pageNum=1&channelId=%s&tous=&nbDisplay=0' %sub_department_id)
    data_3 = response_3.read()
    soup_3 = BeautifulSoup(data_3)
    product_blocs = soup_3.findAll("div", { "class" : "vignette" })
    na_product_blocs = soup_3.findAll("div", { "class" : "vignette produitNonDispo" })
    product_rayon_title = convert_to_str(soup_3.find("h2", { "class" : "titleRayon" }))[0].replace('\n','')
    for product_bloc in product_blocs:
      product_title = product_bloc.find("p", {"class" : "labelProduit"})
      product_unit_price = product_bloc.find("p", {"class" : "prixUnitaire"})
      product_total_price = product_bloc.find("p", {"class" : "prixTotal"})
      product_flag = product_bloc.find("div", {"class" : re.compile("angle*")})['class']
      product_promo = product_bloc.find("p", {"class" : "promoProduit"})
      product_promo_vignette = product_bloc.find("p", {"class" : "vignetteLibellePromo"})
      list_products.append({'department' : department,
                            'sub_department' : sub_department_title,
                            'rayon_title' : product_rayon_title,
                            'product_flag' : product_flag,
                            'product_title' : convert_to_str(product_title.contents),
                            'product_unit_price' : convert_to_str(product_unit_price.contents),
                            'product_total_price' : convert_to_str(product_total_price.contents),
                            'product_promo' : convert_to_str(product_promo),
                            'product_promo_vignette' : convert_to_str(product_promo_vignette),
                            'available' : 'yes'})
    for product_bloc in na_product_blocs:
      product_title = product_bloc.find("p", {"class" : "labelProduit"})
      product_unit_price = product_bloc.find("p", {"class" : "prixUnitaire"})
      product_total_price = product_bloc.find("p", {"class" : "prixTotal"})
      product_flag = product_bloc.find("div", {"class" : re.compile("angle*")})['class']
      product_promo = product_bloc.find("p", {"class" : "promoProduit"})
      product_promo_vignette = product_bloc.find("p", {"class" : "vignetteLibellePromo"})
      list_products.append({'department' : department,
                            'sub_department' : sub_department_title,
                            'rayon_title' : product_rayon_title,
                            'product_flag' : product_flag,
                            'product_title' : convert_to_str(product_title.contents),
                            'product_unit_price' : convert_to_str(product_unit_price.contents),
                            'product_total_price' : convert_to_str(product_total_price.contents),
                            'product_promo' : convert_to_str(product_promo),
                            'product_promo_vignette' : convert_to_str(product_promo_vignette),
                            'available' : 'no'})
  else:
    print 'pbm', department, sub_department_title, sub_department_url

"""
print len(list_products)
enc_stock_json(list_products, json_folder + r'\new_auchan_velizy_test_2')
"""