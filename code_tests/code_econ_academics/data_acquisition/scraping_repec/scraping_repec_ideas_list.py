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

path_built = os.path.join(path_data,
                          'data_econ_academics',
                          'data_built')
path_built_csv = os.path.join(path_built, 'data_csv')

url = 'https://ideas.repec.org/i/eall.html'
response = urllib2.urlopen(url)
data = response.read().decode('utf-8') # .decode('utf-8', 'ignore')

## breaks for some reason
#soup = BeautifulSoup(data)
#ls_authors = []
#for bloc in soup.findAll('td'):
#  bloc_href = bloc.find('a', {'href' : True})
#  if bloc_href  and bloc_href.text:
#    ls_authors.append((bloc_href['href'],
#                       bloc.find('a', {'href' : True}).text))

ls_author_blocs = re.findall('<A HREF=("/[a-z]{1}/.*?)</TD>',
                             data,
                             flags = re.DOTALL)

# adhoc...
ls_author_blocs = ls_author_blocs[3:]

ls_author_rows = []
for author in ls_author_blocs:
  top_5 = 0
  if '<B>' in author:
    author = author.replace('<B>', '').replace('</B>', '')
    top_5 = 1
  tup_0 = author.split('</A>')
  tup_1 = tup_0[0].split('>')
  url = tup_1[0]
  author = tup_1[1].strip()
  nb_items = tup_0[1].strip()
  ls_author_rows.append((author.strip(), url, nb_items, top_5))

df_authors = pd.DataFrame(ls_author_rows,
                          columns = ['author', 'url', 'nb_items', 'top_5'])
df_authors['url'] = df_authors['url'].str.replace('"', '')

#df_authors['nb_items'] = df_authors['nb_items'].str.replace('(', '')\
#                                       .str.replace(')', '')
#df_authors.loc[df_authors['nb_items'] == ' 100 <FONT COLOR="#ff0000">?</FONT> ',
#               'nb_items'] = None
#df_authors.loc[df_authors['nb_items'] == '', 'nb_items'] = None

def get_nb_items(x):
  re_nb_items = re.search(u'\(([0-9]*)\)', x)
  if re_nb_items:
    return re_nb_items.group(1)
  else:
    return None

df_authors['nb_items'] =\
  df_authors['nb_items'].apply(lambda x: get_nb_items(x) if x else x)

df_authors['author_id'] =\
  df_authors['url'].apply(lambda x: re.search(u'/[a-z]{1}/(.*?)\.html', x).group(1))

df_authors.to_csv(os.path.join(path_built_csv,
                               'df_repec_ideas_list.csv'),
                  index = False,
                  encoding = 'utf-8')

#df_authors.to_csv(os.path.join(path_built_csv,
#                               u'df_excel_repec_ideas_list.csv'),
#                index = False,
#                encoding = 'latin-1',
#                sep = ';',
#                escapechar = '\\',
#                quoting = 1)
