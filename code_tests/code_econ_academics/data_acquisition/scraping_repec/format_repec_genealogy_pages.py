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
                         dtype = {'year' : str},
                         encoding = 'utf-8')

ls_author_info = dec_json(os.path.join(path_source_json,
                                       'ls_repec_genealogy_author_info.json'))

# ####################
# FORMAT AUTHOR INFO
# ####################

ls_info_rows = []
for author_url, grad, advisor, students in ls_author_info:
  # grad
  soup_grad = BeautifulSoup(grad).a
  grad_url, grad_institution, grad_year = None, None, None
  if soup_grad:
    grad_url = soup_grad['href']
    grad_institution = soup_grad.text
    grad_year = unicode(soup_grad.next_sibling)
  # check if year can be fetched... and insitution if not edirc?
  else:
    re_year = re.search('(in [0-9]{4,4}\.)$', grad)
    if re_year:
      grad_year = re_year.group(1)
  # advisor (todo: add short id extraction)
  soup_advisor = BeautifulSoup(advisor)
  ls_advisors = []
  for advisor in soup_advisor.findAll('li'):
    advisor_name = advisor.text
    advisor_href = advisor.find('a', {'href' : True}) # take first only
    if advisor_href:
      advisor_href = advisor_href['href']
    ls_advisors += [advisor_name, advisor_href]
  ## old advisor treatment
  #ls_advisor_names = [x.text for x in soup_advisor.findAll('li')]
  #ls_ls_advisor_urls = [[x['href'] for x in li.findAll('a', {'href' : True})]\
  #                         for li in soup_advisor.findAll('li')]
  #nb_advisors = len(ls_advisor_names)
  #str_advisor_names = '; '.join(ls_advisor_names)

  ls_info_rows.append([author_url,
                        grad_url,
                        grad_institution,
                        grad_year] +\
                       ls_advisors)

ls_advisor_cols = ['advisor_1', 'advisor_url_1', 'advisor_2', 'advisor_url_2']

df_info = pd.DataFrame(ls_info_rows,
                        columns = ['url',
                                   'grad_url',
                                   'grad_institution',
                                   'grad_year',
                                   'advisor_1',
                                   'advisor_url_1',
                                   'advisor_2',
                                   'advisor_url_2'])

def get_author_id(x):
  re_sid = re.search('/pages/(.*?)\.html', x)
  # breaks if re_sid does not match (on purpose)
  return re_sid.group(1)

def clean_advisor(x):
  ls_erase = ['RePEc Genealogy', 'EconPapers', 'IDEAS']
  for erase in ls_erase:
     x =  x.replace(erase, '')
  return re.sub('\((?:,\s){0,3}\)\s?', '', x).strip()

def get_institution_id(x):
  re_edirec = re.search('edirc\.repec\.org/data/(.*?)\.html', x)
  # breaks if re_sid does not match (on purpose)
  return re_edirec.group(1)

def get_grad_year(x):
  re_year = re.search('in ([0-9]{4,4}).', x)
  # breaks if re_year does not match (on purpose)
  return re_year.group(1)

for advisor_col in ['advisor_1', 'advisor_2']:
  df_info[advisor_col] =\
    df_info[advisor_col].apply(lambda x: clean_advisor(x) if x else x)
  df_info[advisor_col] =\
    df_info[advisor_col].apply(lambda x: x.replace(u'  ', u' ') if x else x)

for get_id_col in ['url', 'advisor_url_1', 'advisor_url_2']:
  df_info[get_id_col] =\
    df_info[get_id_col].apply(lambda x: get_author_id(x) if x else x)

df_info['grad_url'] =\
  df_info['grad_url'].apply(lambda x: get_institution_id(x) if x else x)

df_info['grad_year'] =\
  df_info['grad_year'].apply(lambda x: get_grad_year(x) if x else x)

df_info.loc[df_info['advisor_1'] == u'No advisor listed, help complete this page.',
             'advisor_1'] = None

# #####################################
# MERGE WITH DF FROM LIST TO HAVE NAMES
# #####################################

# could use name from extracted info (same?)

df_authors['url'] =\
  df_authors['url'].apply(lambda x: get_author_id(x) if x else x)

df_authors['year'] =\
  df_authors['year'].apply(lambda x: x.strip() if not pd.isnull(x) else x)

df_authors['author'] =\
  df_authors['author'].apply(lambda x: x.strip())

df_final = pd.merge(df_authors,
                    df_info,
                    on = ['url'],
                    how = 'outer')

# Check years are consistent between list and author page
df_check_year = df_final[(~((df_final['year'].isnull()) &\
                            (df_final['grad_year'].isnull()))) &\
                         (df_final['year'] != df_final['grad_year'])]
print u''
print u'Nb inconsistencies in grad year to check:', len(df_check_year)

# Check if institution extracted even if not registered (does it happen?)
df_check_inst = df_final[(df_final['grad_institution'].isnull()) &\
                         (~df_final['grad_year'].isnull())]
print u''
print u'Nb grad year but not institution extracted (/listed?)', len(df_check_inst)

## could build dict first from ls_author_info with (cleaned) url as keys...
#for url in df_check_inst['url'].values[0:100]:
#  for x in ls_author_info:
#    # in is not perfectly precise hence some have institution: not right entry
#    if url in x[0]:
#      print ''
#      print x[0], x[1]
#      break
## looks like everything was extracted
## website most likely requires to register institution on edirc to list it

# #######################
# EXTRACT STUDENTS
# #######################

# first li level: institution
# second li lelvel: students

## check example: Daron Acemoglu
#for x in ls_author_info:
#  if x[0] == '/pages/pac16.html':
#    #print x
#    break
#soup_students = BeautifulSoup(x[3])
#print soup_students.findAll('li')

# need to extract student year too
ls_student_rows = []
for author_url, grad, advisor, students in ls_author_info:
  soup_students = BeautifulSoup(students)
  # li can be either institution (with students within) or students
  for li in soup_students.findAll('li'):
    lia = li.find('a', {'href' : True})
    if lia and 'edirc' in lia['href']:
      student_institution = lia.text
      student_institution_url = lia['href']
      ls_student_lis = li.findAll('li')
      for student_li in ls_student_lis:
        student_name = student_li.text
        student_url = student_li.find('a', {'href' : True}) # take first
        if student_url:
          student_url = student_url['href']
        ls_student_rows.append((author_url,
                                student_institution,
                                student_institution_url,
                                student_name,
                                student_url))
    elif re.match(u'At unknown department:', li.text):
      student_institution = None
      student_institution_url = None
      ls_student_lis = li.findAll('li')
      for student_li in ls_student_lis:
        student_name = student_li.text
        student_url = student_li.find('a', {'href' : True}) # take first
        if student_url:
          student_url = student_url['href']
        ls_student_rows.append((author_url,
                                student_institution,
                                student_institution_url,
                                student_name,
                                student_url))

df_students = pd.DataFrame(ls_student_rows,
                           columns = ['author_url',
                                      'student_institution',
                                      'student_institution_url',
                                      'student_name',
                                      'student_url'])

for advisor_col in ['student_name']:
  df_students[advisor_col] =\
    df_students[advisor_col].apply(lambda x: clean_advisor(x) if x else x)
  df_students[advisor_col] =\
    df_students[advisor_col].apply(lambda x: x.replace(u'  ', u' ') if x else x)

for get_id_col in ['author_url', 'student_url']:
  df_students[get_id_col] =\
    df_students[get_id_col].apply(lambda x: get_author_id(x) if x else x)

df_students['student_institution_url'] =\
  df_students['student_institution_url'].apply(lambda x: get_institution_id(x) if x else x)

def get_student_year(x):
  re_year = re.search('^((?:[0-9]{4,4})|(?:Year\?))', x)
  # breaks if re_year does not match (on purpose)
  return re_year.group(1)

def erase_student_year(x):
  return re.sub('^((?:[0-9]{4,4})|(?:Year\?))', u'', x).strip()

df_students['student_year'] =\
  df_students['student_name'].apply(lambda x: get_student_year(x) if x else x)

df_students['student_name'] =\
  df_students['student_name'].apply(lambda x: erase_student_year(x) if x else x)

df_students.loc[df_students['student_year'] == 'Year?',
                'student_year'] = None

# #######
# OUTPUT
# #######

#for x in df_final['grad_institution'].values:
#  if not pd.isnull(x):
#  try:
#    ok = x.encode('latin-1')
#  except:
#    x

# adhoc encoding fix: erase characters not available in latin-1
for old, new in [(u'\u0130', u'I'),
                 (u'\u015f', u's'),
                 (u'\u011f', u'g'),
                 (u'\u0101', u'a'),
                 (u'\u012b', u'i'),
                 (u'\ufffd', u'?'), # replacement char... several could be fixed?
                 (u'\u0142', u'l'),
                 (u'\u0105', u'a'),
                 (u'\u0131', u'i'),
                 (u'\u015e', u's'),
                 (u'\u0163', u't'),
                 (u'\u0144', u'n'),
                 (u'\u0115', u'e'),
                 (u'\u0160', u's'),
                 (u'\u0148', u'n'),
                 (u'\u011b', u'e')]:
  df_final['grad_institution'] = df_final['grad_institution'].str.replace(old, new)
  df_final['advisor_1'] = df_final['advisor_1'].str.replace(old, new)
  df_final['advisor_2'] = df_final['advisor_2'].str.replace(old, new)

  df_students['student_institution'] = df_students['student_institution'].str.replace(old, new)
  df_students['student_name'] = df_students['student_name'].str.replace(old, new)

# AUTHOR INFO

df_final.drop('year', axis = 1, inplace = True)
df_final.rename(columns = {'url': 'author_id',
                           'grad_url' : 'grad_institution_id',
                           'advisor_url_1' : 'advisor_id_1',
                           'advisor_url_2' : 'advisor_id_2'},
                inplace = True)

# standard csv
df_final.to_csv(os.path.join(path_built_csv,
                             u'repec_genealogy.csv'),
                index = False,
                encoding = 'utf-8')

# excel csv
df_final.to_csv(os.path.join(path_built_csv,
                             u'excel_repec_genealogy.csv'),
                index = False,
                encoding = 'latin-1',
                sep = ';',
                escapechar = '\\',
                quoting = 1)

# AUTHOR STUDENTS

df_students.rename(columns = {'author_url': 'author_id',
                              'student_institution_url' : 'student_institution_id',
                              'student_url' : 'student_id'},
                   inplace = True)

# standard csv
df_students.to_csv(os.path.join(path_built_csv,
                             u'repec_genealogy_students.csv'),
                index = False,
                encoding = 'utf-8')

# excel csv
df_students.to_csv(os.path.join(path_built_csv,
                             u'excel_repec_genealogy_students.csv'),
                index = False,
                encoding = 'latin-1',
                sep = ';',
                escapechar = '\\',
                quoting = 1)
