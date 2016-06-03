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

url = 'https://genealogy.repec.org/list.html'
response = urllib2.urlopen(url)
data = response.read() # .decode('utf-8', 'ignore')

## breaks for some reason
#soup = BeautifulSoup(data[start:])
#ls_authors = []
#for bloc in soup.findAll('td'):
#  bloc_href = bloc.find('a', {'href' : True})
#  if bloc_href  and bloc_href.text:
#    ls_authors.append((bloc_href['href'],
#                       bloc.find('a', {'href' : True}).text))

ls_author_blocs = re.findall('<A HREF=("/pages.*?)</TD>',
                             data,
                             flags = re.DOTALL)

ls_author_rows = []
for author in ls_author_blocs:
  tup_0 = author.split('</A>')
  tup_1 = tup_0[0].split('>') # if second part empty: not author
  if tup_1[1]:
    url, author = tup_1
    year = tup_0[1]
    ls_author_rows.append((author, year, url))

df_authors = pd.DataFrame(ls_author_rows,
                          columns = ['author', 'year', 'url'])
df_authors['year'] = df_authors['year'].str.replace('(', '')\
                                       .str.replace(')', '')
df_authors.loc[df_authors['year'] == ' ', 'year'] = None
df_authors['url'] = df_authors['url'].str.replace('"', '')

#df_authors.to_csv(os.path.join(path_built_csv,
#                               'df_repec_genealogy_list.csv'),
#                  index = False,
#                  encoding = 'utf-8')
