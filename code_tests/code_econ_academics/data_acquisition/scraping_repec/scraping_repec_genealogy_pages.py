#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import httplib, urllib2
import urllib
import cookielib
from cookielib import Cookie
from bs4 import BeautifulSoup
import re
import pandas as pd
import json

def dec_json(path_f):
  with open(path_f, 'r') as f:
    return json.loads(f.read())

def enc_json(data, path_f):
  with open(path_f, 'w') as f:
    json.dump(data, f)

path_source = os.path.join(path_data,
                           'data_econ_academics',
                           'data_source')
path_source_json = os.path.join(path_source, 'data_json')

path_built = os.path.join(path_data,
                          'data_econ_academics',
                          'data_built')
path_built_csv = os.path.join(path_built, 'data_csv')

df_authors = pd.read_csv(os.path.join(path_built_csv,
                                      'df_repec_genealogy_list.csv'),
                         encoding = 'utf-8')

ls_author_info_rows = []

for row_i, row in df_authors[(~df_authors['year'].isnull()) &\
                             (~df_authors['url'].isnull())].iterrows():
  #author_url = df_authors.iloc[1]['url']
  author_url = row['url']
  url = 'https://genealogy.repec.org' + author_url
  response = urllib2.urlopen(url)
  data = response.read() # .decode('utf-8', 'ignore')
  
  #soup = BeautifulSoup(data)
  #main = soup.find('div', {'id' : 'main'})
  #ls_h2_blocs = soup.findAll('h2')
  
  str_grad = re.search('<H2>Graduate studies</H2>(.*?)<H2>', data, re.DOTALL).group(1)
  str_advisor = re.search('<H2>Advisor</H2>(.*?)<H2>', data, re.DOTALL).group(1)
  str_students = re.search('<H2>Students</H2>(.*?)</div>', data, re.DOTALL).group(1)
  
  ls_author_info_rows.append((author_url,
                              str_grad,
                              str_advisor,
                              str_students))

enc_json(ls_author_info_rows,
         os.path.join(path_source_json,
                      'ls_repec_genealogy_author_info.json'))

#ls_final_rows = []
#for author_url, grad, advisor, students in ls_author_info_rows:
#  # grad
#  soup_grad = BeautifulSoup(grad).a
#  if soup_grad:
#    grad_url = soup_grad['href']
#    grad_institution = soup_grad.text
#    grad_year = unicode(soup_grad.next_sibling)
#  # advisor (todo: add short id extraction)
#  soup_advisor = BeautifulSoup(advisor)
#  ls_advisor_names = [x.text for x in soup_advisor.findAll('li')]
#  ls_ls_advisor_urls = [[x['href'] for x in li.findAll('a', {'href' : True})]\
#                           for li in soup_advisor.findAll('li')]
#  nb_advisors = len(ls_advisor_names)
#  str_advisor_names = '; '.join(ls_advisor_names)
#
#  ls_final_rows.append((author_url,
#                        grad_url,
#                        grad_institution,
#                        grad_year,
#                        nb_advisors,
#                        str_advisor_names))
#
#df_final = pd.DataFrame(ls_final_rows,
#                        columns = ['url',
#                                   'grad_url',
#                                   'grad_institution',
#                                   'gear_year',
#                                   'nb_advisors',
#                                   'str_advisor_names'])
#def clean_advisor(x):
#  ls_erase = ['RePEc Genealogy', 'EconPapers', 'IDEAS']
#  for erase in ls_erase:
#     x =  x.replace(erase, '')
#  return re.sub('\((?:,\s){0,3}\)\s?', '', x).strip()
#
#df_final['str_advisor_names'] =\
#  df_final['str_advisor_names'].apply(lambda x: clean_advisor(x))
