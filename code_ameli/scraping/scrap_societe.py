#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import httplib, urllib2
import urllib
import cookielib
from cookielib import Cookie
from BeautifulSoup import BeautifulSoup
import string
import re
from datetime import date
import json
import time
#from selenium import webdriver
#from selenium.webdriver.common.keys import Keys

def ls_to_clean(ls_to_clean):
  ls_to_clean = map(lambda x: x.replace(u'&gt;', u'').replace(u'&nbsp;',u'').strip(), ls_to_clean)
  return [x for x in ls_to_clean if x]

def enc_json(database, chemin):
  with open(chemin, 'w') as fichier:
    json.dump(database, fichier)

def dec_json(chemin):
  with open(chemin, 'r') as fichier:
    return json.loads(fichier.read())

def get_societe_page(ls_name):
  name = '+'.join(['+'.join(elt.split()) for elt in ls_name])
  url = r'http://www.societe.com/cgi-bin/liste?nom=%s&dirig=&pre=&ape=&dep=75&imageField=' %name
  response = urllib2.urlopen(url)
  data = response.read()
  soup = BeautifulSoup(data)
  result_url = response.geturl()
  if soup.title and ls_name[0] in soup.title.string:
    ls_sector = [] 
    bloc_sector = soup.find('script', {'type' : 'text/javascript', 'language' : None, 'src' : None})
    if bloc_sector:
      ls_sector = bloc_sector.findAll(text=True)
    name, ls_address = None, []
    bloc_name_address = soup.find('div', {'id' : 'HeaderFiche'})
    if bloc_name_address:
      if bloc_name_address.h1:
        name = bloc_name_address.h1.string
      if bloc_name_address.find('div', {'id' : 'TextDeno'}):
        ls_address = bloc_name_address.find('div', {'id' : 'TextDeno'}).findAll('p')
        if ls_address:
          ls_address = [elt.string for elt in ls_address if elt and elt.string]
    ls_info = [] 
    bloc_info = soup.find('table', {'border' : '0', 'cellpadding' :'2', 'cellspacing':'5' ,'style' : 'font-size:11px;'})
    if bloc_info:
      ls_info = bloc_info.findAll('td', {'colspan' : None, 'id' : None})
      ls_info = [elt.string for elt in ls_info]
    return [name, ls_address, ls_sector, ls_info]
  else:
    return None

# build urllib2 opener
cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [('User-agent',
                      'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.22'+\
                      '(KHTML, like Gecko) Chrome/25.0.1364.172 Safari/537.22')]
urllib2.install_opener(opener)

# path_physicians = r'\\ulysse\users\echamayou\Bureau\Etienne_work\Data\data_ameli'
path_physicians = r'C:\Users\etna\Desktop\Etienne_work\Data\data_ameli'

ls_ls_physicians = dec_json(path_physicians + r'\ls_ls_ophtalmologiste_75')
dict_physicians = dec_json(path_physicians + r'\dict_ophtalmologiste_75')

dict_results = {}
ls_no_result = []

for id_physician, ls_physician in dict_physicians.items():
  ind_name = ls_physician[0].index(u'Médecin ophtalmologiste')
  ls_name = ls_physician[0][:ind_name]
  if len(ls_name) == 3:
    if id_physician not in dict_results and id_physician not in ls_no_result:
      doc_info = None
      ls_name = ls_name[1:][::-1]
      try:
        doc_info = get_societe_page(ls_name)
      except Exception, e:
        print 'Error with:', ls_name
        print e
        if len(ls_name[1].split()) > 1:
          for family_name in ls_name[1].split():
            ls_name = [ls_name[0], family_name]
            try:
              doc_info = get_societe_page(ls_name)
              print 'Youhou', ls_name
              break
            except:
              print 'Bouh', ls_name
              pass
      if doc_info:
        dict_results[id_physician] = doc_info
      else:
        ls_no_result.append(id_physician)
  time.sleep(2)

# enc_json(dict_results, path_physicians + r'\societe_dict_ophtalmo')
# enc_json(ls_no_result, path_physicians + r'\societe_ls_no_result_ophtalmo')

#TODO: "JEAN CLAUDE TIMSIT" => SEARCH "JEAN TIMSIT" (cut names too)
