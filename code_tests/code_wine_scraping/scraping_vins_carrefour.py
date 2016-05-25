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

path_current_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
dict_info = dec_json(os.path.join(path_current_dir,
                                  u'dict_carrefour_prelim_info.json'))

dict_bottle_rows = {}

for bottle_url_extension in dict_info.keys():
  # Visit website
  url = u'http://vins-champagnes.carrefour.fr/' + bottle_url_extension
  response = urllib2.urlopen(url)
  data = response.read()
  soup = BeautifulSoup(data)
  
  
  bloc_title = soup.find('div', {'class' : 'titre_fiche_produit'})
  title = extract_bs_text(bloc_title)
  
  bloc_qualif = soup.find('div', {'class' : 'box_fiche_produit_qualificatif'})
  qualif = extract_bs_text(bloc_qualif)
  
  # todo: extract from each.. pbm notes are images so cannot get them (?)
  ls_bloc_note_echos = soup.findAll('div', {'class' : 'box_fiche_produit_note_echos_content'})
  ls_bloc_degustation = soup.findAll('div', {'class' : 'box_fiche_produit_degustation_text'})
  
  # note_echos (indiff with degustation)
  ls_ls_ne = []
  for bloc_note_echos in ls_bloc_note_echos:
    ls_ne_bloc = bloc_note_echos.findAll('li')
    ls_ne = [ne_bloc.findAll(text = True) for ne_bloc in ls_ne_bloc]
    ls_ls_ne.append(ls_ne)
  
  # descriptif:
  bloc_desc = soup.find('div', {'class' : "content_center_fiche_produit_descriptif_center",
                                'id' : "desc_content_1"})
  desc = bloc_desc.findAll(text = True)
  
  ls_bottle = [['title', title],
               ['qualif', qualif],
               ['notes' , ls_ls_ne],
               ['desc', desc]]
  dict_bottle_rows[bottle_url_extension] = ls_bottle

# price and wine details already captured not included
# some medals info in desc => to be extracted with regex
# seems quite a lot of info in desc... to be extracted with regex

enc_json(dict_bottle_rows,
         os.path.join(path_current_dir,
                      u'dict_carrefour_wine.json'))
