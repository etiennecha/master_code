#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import urllib, urllib2
import cookielib
from cookielib import Cookie
from BeautifulSoup import BeautifulSoup
import gscholar
import time

if os.path.exists(r'W:\Bureau'):
  path_work =  r'W:\Bureau\Etienne_work'
else:
  path_work = r'C:\Users\etna\Dropbox'

path_reading_group = path_work + r'\Reading_group'
path_code = path_work + r'\Code\Etienne_repos\code_google_scholar'

list_papers = [f for f in os.listdir(path_reading_group)\
                if os.path.isfile(path_reading_group + r'\%s' %f)]
list_papers = list_papers[:-2] # exclude two files...
# txt_file = open(path_code + r'\list_papers_reading_group.txt', 'w')
# txt_file.write('\n'.join(list_papers))
# txt_file.close()

str_all_bibtex = ''
list_not_found = []
for paper in list_papers:
  print paper
  paper_bibtex = gscholar.query(paper.split('_')[2].rstrip('.pdf'), 4)
  if paper_bibtex:
    str_all_bibtex += '%s\n' %paper_bibtex[0]
  else:
    list_not_found.append(paper)
  time.sleep(0.5)

# with open(path_code + r'\file_bibtex.txt', 'w') as fichier:
  # fichier.write(str_bibtex)

  
# # ############
# # DEPRECATED
# # ############
  
# # build urllib2 opener
# cookie_jar = cookielib.LWPCookieJar()
# opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookie_jar))
# opener.addheaders = [('User-agent',
                      # 'Mozilla/5.0 (Windows NT 6.1; WOW64) '+\
                        # 'AppleWebKit/537.11 (KHTML, like Gecko) '+\
                        # 'Chrome/23.0.1271.64 Safari/537.11')]
# urllib2.install_opener(opener)

# UA = 'Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.2.9) Gecko/20100913 Firefox/3.6.9'

# # no author
# title_search = urllib.quote(list_papers[10].split('_')[2].rstrip('.pdf'))
# url_search = u'http://scholar.google.com/scholar?hl=en&q=%s&btnG=Search&as_subj=eng&as_std=1,5&as_ylo=&as_vis=0' %title_search
# req = urllib2.Request(url=url_search, headers={'User-Agent': UA})
# response = urllib2.urlopen(req)

# soup = BeautifulSoup(response.read())
# list_0 = soup.findAll('h3', {'class': 'gs_rt'})
# list_1 = soup.findAll('div', {'class': 'gs_ri'})