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
                                      'df_repec_ideas_list.csv'),
                         encoding = 'utf-8')

path_author_info = os.path.join(path_source_json,
                                'ls_repec_ideas_author_info.json')
if not os.path.exists(path_author_info):
  ls_author_info = []
else:
  ls_author_info = dec_json(path_author_info)
ls_got_author_url = [x[0] for x in ls_author_info]

# author_url = df_authors.iloc[1]['url']
#author_url = '/e/pac16.html'

for row_i, row in df_authors[(df_authors['top_5'] == 1) &\
                             (~df_authors['url'].isin(ls_got_author_url))][0:500].iterrows():
  
  author_url = row['url']
  url = 'https://ideas.repec.org' + author_url
  response = urllib2.urlopen(url)
  data = response.read() #.decode('utf-8') # .decode('utf-8', 'ignore')
  
  soup = BeautifulSoup(data)
  
  # to extract:
  # - names : same?
  # - mail
  # - homepage
  # - affiliation
  # - paper list with dates => breaks... regex if want them
  
  bloc_pdetails = soup.find('div', {'class' : True,
                                    'id' : 'author-personal-details'})
  ls_pdetails = bloc_pdetails.findAll('tr')
  ls_pdetail_str = [x.text for x in ls_pdetails]
  # specific for mail extraction
  bloc_email = bloc_pdetails.find('span', {'data-liame2' : True})
  email = None
  if bloc_email:
    email = bloc_email['data-liame2']
  
  ls_affiliations = []
  bloc_affiliations = soup.find('div', {'class' : True,
                                        'id' : 'affiliation-body'})
  ls_bloc_affiliations = bloc_affiliations.findAll('div', {'class' : "panel col-xs-12"})
  for bloc_affiliation in ls_bloc_affiliations:
    aff_institution = bloc_affiliation.h4
    if aff_institution:
      aff_institution = u' '.join(aff_institution.findAll(text = True))
    
    # ls_aff_details = bloc_affiliation.findAll('span', {'class' : True})
    aff_institution_location = bloc_affiliation.find('span', {'class' : 'locationlabel'})
    aff_institution_url = bloc_affiliation.find('span', {'class' : 'homelabel'})
    aff_institution_edirc = bloc_affiliation.find('span', {'class' : 'handlelabel'})
    ls_aff_info = [aff_institution]
    for aff_temp in [aff_institution_location,
                     aff_institution_url,
                     aff_institution_edirc]:
      if aff_temp:
        ls_aff_info.append(aff_temp.text)
      else:
        ls_aff_info.append(None)
    ls_affiliations.append(ls_aff_info)
  
  ls_author_info.append((author_url,
                         ls_pdetail_str,
                         email,
                         ls_affiliations))

enc_json(ls_author_info,
         os.path.join(path_source_json,
                      'ls_repec_ideas_author_info.json'))

ls_rows_ai = []
for author_info in ls_author_info:
  formatted_email = None
  if author_info[2] and 'm7i7' in author_info[2]:
    formatted_email = '.'.join(json.loads(author_info[2])[::-1]).replace('.m7i7', '@')
  ls_rows_ai.append([author_info[0]] +\
                    list(author_info[1][:5]) +\
                    [formatted_email] +\
                    list(author_info[1][7:9]))

df_ai = pd.DataFrame(ls_rows_ai,
                     columns = ['author_url',
                                'first_name',
                                'middle_name',
                                'last_name',
                                'suffix',
                                'id',
                                'email',
                                'webpage',
                                'address'])

for col in ['first_name', 'middle_name', 'last_name',
            'suffix', 'webpage', 'address', 'id']:
  df_ai[col] = df_ai[col].str.strip()

for col, erase in [['first_name', 'First Name:'],
                   ['middle_name', 'Middle Name:'],
                   ['last_name', 'Last Name:'],
                   ['suffix', 'Suffix:'],
                   ['id', 'RePEc Short-ID:']]:
  df_ai[col] = df_ai[col].apply(lambda x: x.replace(erase, u''))

# max nb of institution... separate percent etc.
