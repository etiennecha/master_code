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

##chromedriver = r'\\ulysse\users\echamayou\Etienne\Python\chromedriver'
##os.environ["webdriver.chrome.driver"] = chromedriver
#path_firefox = r'\\ulysse\users\echamayou\Etienne\MozillaFirefox\firefox.exe'
#ffbin = webdriver.firefox.firefox_binary.FirefoxBinary(path_firefox)
#driver = webdriver.Firefox(firefox_binary=ffbin)
##driver.get("http://www.python.org")
##assert "Python" in driver.title
##elem = driver.find_element_by_name("q")
##elem.send_keys("selenium")
##elem.send_keys(Keys.RETURN)
##assert "Google" in driver.title
##driver.close()
#driver.get('http://ameli-direct.ameli.fr/')
#driver.findElement().click();

# build urllib2 opener
cookie_jar = cookielib.LWPCookieJar()
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
opener.addheaders = [('User-agent',
                      'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.22'+\
                      '(KHTML, like Gecko) Chrome/25.0.1364.172 Safari/537.22')]
urllib2.install_opener(opener)

url = r'http://ameli-direct.ameli.fr'
response = urllib2.urlopen(url)
data = response.read()
soup = BeautifulSoup(data)
# href_search = soup.find('div', {'id':'buttonPS', 'class':'btnRadio'}).a['href']
href_search  = soup.find('form', {'action': re.compile('/recherche.*'), 'method' : 'post'})['action']

dict_search_params = {'type':'ps',
                      'ps_nom':'',
                      'es_nom':'',
                      'ps_profession':'ophtalmologiste',
                      'ps_profession_label':'Ophtalmologiste',
                      'es_specialite':'',
                      'es_specialite_label':'',
                      'ps_acte':'',
                      'ps_acte_label':'',
                      'es_actes_maladies':'',
                      'es_actes_maladies_label':'',
                      'ps_localisation':'75',
                      'submit_final':'',
                      'ps_secteur':'I_I',
                      'ps_carte_vitale':'2',
                      'ps_sexe':'2',
                      'es_type':'3'}

params = urllib.urlencode(dict_search_params)
req = urllib2.Request(url + href_search, data = params)
response = urllib2.urlopen(req)
data = response.read()
soup = BeautifulSoup(data)

url_redirection = response.geturl()
#dict_search_params = {'results_per_page': '0'}
#params = urllib.urlencode(dict_search_params)
#req = urllib2.Request(url_redirection, data = params)
# response = urllib2.urlopen(req)
response = urllib2.urlopen(url_redirection + '?results_per_page=0')
data = response.read()
soup = BeautifulSoup(data)

ls_ls_physicians = []
ls_blocs = soup.findAll('div', {'class' : 'liste-acte-item'})
for bloc in ls_blocs:
  # first part: link, name, phone
  bloc_titre = bloc.find('div', {'class' : 'medecin-item-titre'})
  indiv_href_name = bloc_titre.find('div', {'class' : 'medecin-item-nom-recherche'})
  href, ls_name = None, None
  if indiv_href_name:
    href = indiv_href_name.a['href']
    ls_name = indiv_href_name.a.findAll(text=True)
  prof_item = bloc_titre.find('div', {'class' : 'medecin-item-prof-recherche'}).findAll(text = True)
  tel_item = bloc_titre.find('div', {'class' : 'medecin-item-tel-recherche'}).findAll(text = True)
  # second part: address, ???, convetion
  bloc_desc = bloc.find('div', {'class' : 'medecin-item-desc-line'})
  indiv_address = bloc_desc.find('div', {'class' : 'medecin-item-nom-recherche'}).findAll(text = True)
  carte_vitale = bloc_desc.find('div', {'class' : 'medecin-item-prof-recherche'}).findAll(text = True)
  convention = bloc_desc.find('div', {'class' : 'medecin-item-tel-recherche'}).findAll(text = True)
  ls_results = [href,
                ls_name,
                prof_item,
                indiv_address,
                carte_vitale,
                convention]
  ls_results = ls_results[0:1] + [ls_to_clean(x) for x in ls_results[1:]]
  ls_ls_physicians.append(ls_results)

time.sleep(3)

path_physicians = r'\\ulysse\users\echamayou\Bureau\Etienne_work\Data\data_ameli'
#enc_json(ls_ls_physicians, path_physicians + r'\ls_ls_physicians')

dict_physicians = dec_json(path_physicians + r'\dict_physicians')
#dict_physicians = {}

# temp
#for i, ls_physician in enumerate(ls_ls_physicians):
#  if ' '.join(ls_physician[1]) == 'GUIGUI ALAIN':
#    ind_alain = i

for ls_physician in ls_ls_physicians:
  id_match = re.search('detaillee-(.*?)-', ls_physician[0])
  if id_match and id_match.group(1) not in dict_physicians:
    id_physician = id_match.group(1)
    response = urllib2.urlopen(url + ls_physician[0])
    data = response.read()
    soup = BeautifulSoup(data)
    bloc_info = soup.find('div', {'class' : 'infos'})
    ls_name_address = soup.find('div', {'class' : 'coordonnes coordonnesps'}).findAll(text=True)
    ls_name_address = ls_to_clean(ls_name_address)
    ls_other_places = soup.find('div', {'id' : 'fenetre_modale_autres_lieux'})
    if ls_other_places:
      ls_other_places = ls_other_places.findAll('li')
      ls_other_places = [[other_place.a['href'], other_place.a.string]\
                          for other_place in ls_other_places if other_place.a]
    ls_infos = [x.findAll(text= True) for x in bloc_info.findAll('p')]
    ls_blocs_actes = soup.findAll('div', {'class' :'liste-acte-item'})
    ls_all_actes = []
    for bloc_actes in ls_blocs_actes:
      for bloc_acte in bloc_actes.findAll('div', {'class' : 'acte-item'}):
        acte_title = bloc_acte.find('div', {'class' : 'consult-item-titre'})
        tarif_title = bloc_acte.find('div', {'class' : 'item-tarif-medecin-entete'})
        tarif_label = bloc_acte.findAll('div', {'class' : 'item-tarif-medecin-libelle'}) #findAll
        tarif_value = bloc_acte.findAll('div', {'class' : 'item-tarif-medecin-champ'}) # findAll
        rembt_title = bloc_acte.find('div', {'class' : re.compile('acte-item-tarif\s?')})
        # rembt_value = bloc_acte.find('div', {'class' : re.compile('acte-item-tarif-valeur\s?')})
        ls_acte = [acte_title, rembt_title, tarif_title]
        ls_acte = [ls_to_clean(elt.findAll(text=True)) if elt else [] for elt in ls_acte]
        ls_tarifs = [tarif_label, tarif_value]
        ls_tarifs = [[ls_to_clean(elt.findAll(text=True)) if elt else [] for elt in ls_blocs_tarifs]\
                      for ls_blocs_tarifs in ls_tarifs]
        ls_all_actes.append([ls_acte, ls_tarifs])
    dict_physicians[id_physician] = [ls_name_address,
                                     ls_other_places,
                                     ls_infos,
                                     ls_all_actes]
    time.sleep(2)

# enc_json(dict_physicians, path_physicians + r'\dict_physicians')
