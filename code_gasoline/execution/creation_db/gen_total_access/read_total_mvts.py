#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data, path_dir
import os, sys
import subprocess
from subprocess import PIPE, Popen
import re
import pandas as pd

def read_pdftotext(path_file, path_pdftotext):
  pdf_file = subprocess.Popen([os.path.join(path_pdftotext,
                                            'pdftotext.exe'),
                               #'-layout' ,
                               '-raw',
                               path_file,
                               '-'], stdout=PIPE)
  data = pdf_file.communicate()[0]
  return data

path_dir_raw_stations = os.path.join(path_data,
                                     'data_gasoline',
                                     'data_raw',
                                     'data_stations')

#path_pdf_total_mvts = os.path.join(path_dir_raw_stations, 'data_other', 'mvts_stations_services.pdf') 
#str_pdf = read_pdftotext(path_pdf_total_mvts, path_dir)
#ls_pdf = str_pdf.split('\r\n')

# file obtained with pdftohtml and options -i -c -noframes
path_html_total_mvts = os.path.join(path_dir_raw_stations,
                                    'data_other',
                                    'mvts_stations_services.html')
test = open(path_html_total_mvts, 'r').read()
from BeautifulSoup import BeautifulSoup
soup = BeautifulSoup(test)

ls_pages = soup.findAll('div', {'style' : "position:relative;width:892;height:1262;"})
# up to 60: similar format a priori, then check

# FERMETURES

ls_rows = []
for page in ls_pages[0:61]:
  ls_rows += page.findAll('div', {'style' : re.compile('position:absolute.*')})

#page_1 = soup.find('div', {'style' : "position:relative;width:892;height:1262;"})
#ls_rows_1 = page_1.findAll('div', {'style' : re.compile('position:absolute.*')})

# A bit of a fragile assumption (detailed below)
ls_ls_results = []
ls_results = []
for row in ls_rows:
  col_ind = int(re.search('left:([0-9]*)$', row['style']).group(1))
  row_ind = int(re.search('top:([0-9]*);left', row['style']).group(1))
  str_row = row.find('span', {'class' : True}).findAll(text = True)
  # assume no new row start after page break without first column filled
  if ls_results and col_ind != 47 and row_ind == 2:
    print col_ind, row_ind, str_row
    ls_results.append((col_ind, row_ind, str_row))
  elif ls_results and col_ind != ls_results[-1][0] and row_ind != ls_results[-1][1]:
    ls_ls_results.append(ls_results)
    ls_results = [(col_ind, row_ind, str_row)]
  else:
    ls_results.append((col_ind, row_ind, str_row))
ls_ls_results.append(ls_results)
ls_ls_results = ls_ls_results[1:]

# sort based on first elt and join (double join?)
ls_ind = [47, 120, 195, 269, 342, 407, 480, 521, 606]
dict_ind = {ind: i for i, ind in enumerate(ls_ind)}

ls_ls_final = []
for ls_results in ls_ls_results:
  ls_final = ['' for i in ls_ind]
  for col_ind_res, row_ind_res, ls_str_res in ls_results:
    ls_final[dict_ind[int(col_ind_res)]] += ' %s' %' '.join(ls_str_res)
    ls_final = [x.strip() for x in ls_final]
  ls_ls_final.append(ls_final)

df_fer = pd.DataFrame(ls_ls_final[1:], columns = ls_ls_final[0])

#print df_final[ls_ls_final[0][:-2]].to_string()
# fix line 82: only mistake spotted so far
# Station report: exploitation: ' - ' probably gets many false positive.. regex zip?
# Or go back to xml... (how to join?)

# OUVERTURES

ls_rows = []
for page in ls_pages[61:]:
  ls_rows += page.findAll('div', {'style' : re.compile('position:absolute.*')})

# TODO: print page break inds and correct manually
ls_ls_results = []
ls_results = []
for row in ls_rows:
  col_ind = int(re.search('left:([0-9]*)$', row['style']).group(1))
  row_ind = int(re.search('top:([0-9]*);left', row['style']).group(1))
  str_row = row.find('span', {'class' : True}).findAll(text = True)
  if ls_results and col_ind != 58 and row_ind == 2:
    print col_ind, row_ind, str_row
    ls_results.append((col_ind, row_ind, str_row))
  elif ls_results and col_ind != ls_results[-1][0] and row_ind != ls_results[-1][1]:
    ls_ls_results.append(ls_results)
    ls_results = [(col_ind, row_ind, str_row)]
  else:
    ls_results.append((col_ind, row_ind, str_row))
ls_ls_results.append(ls_results)
ls_ls_results = ls_ls_results[1:]

# sort based on first elt and join (double join?)
ls_ind = [58, 151, 259, 373, 523, 616]
dict_ind = {ind: i for i, ind in enumerate(ls_ind)}

ls_ls_final_2 = []
for ls_results in ls_ls_results:
  ls_final_2 = ['' for i in ls_ind]
  for col_ind_res, row_ind_res, ls_str_res in ls_results:
    ls_final_2[dict_ind[int(col_ind_res)]] += ' %s' %' '.join(ls_str_res)
    ls_final_2 = [x.strip() for x in ls_final_2]
  ls_ls_final_2.append(ls_final_2)

df_ouv = pd.DataFrame(ls_ls_final_2[1:], columns = ls_ls_final_2[0])

# #######################
# CHECK AND EXPLOIT DATA
# #######################

# FERMETURES
# ##########

print u'\nWorking on Fermetures:'

# CHECK ZIP CODES

# general case
print '\nFixing and inspecting zip codes:'
for row_i, row in df_fer.iterrows():
  if re.search(u'^[0-9]{1,2}\s?[0-9]{3}$', row['CP']):
    row['CP'] = row['CP'].replace(u' ', u'').rjust(5, '0')
  else:
    print row_i, row['CP']
# remediations (CAUTION: SPECIFIC TO THIS PDF FILE)
df_fer.loc[10, ['Station', 'Adresse', 'CP', 'Ville']] =\
  ['', '81 RUE DE SECLIN', '59710', 'AVELIN']
df_fer.loc[81, 'Station report'] = df_fer.loc[81, 'Ville']
df_fer.loc[81, 'Ville'] = 'ST MAXIMIN LA STE BAUME'
df_fer = df_fer.drop(82)

# FIX CITIES

# could check letters alone (or 2, 3), remove except for L (and D)
ls_city_fix = [('JOUARS PONTCHARTRAI N', 'JOUARS PONTCHARTRAIN'),
               ('CLERMONT-FER RAND', 'CLERMONT-FERRAND')]
def adhoc_fix(ls_fix, str_to_fix):
  for (old, new) in ls_fix:
    str_to_fix = str_to_fix.replace(old, new)
  return str_to_fix
df_fer['Ville'] = df_fer['Ville'].apply(lambda x: adhoc_fix(ls_city_fix, x))
# remove cedex
print '\nInspecting Cedex:'
print df_fer[['Ville', 'CP']][df_fer['Ville'].str.contains('cedex',
                                                           case = False)].to_string()

# DUPLICATES

print u'\nNb duplicates:', len(df_fer[df_fer.duplicated()])

# DISPLAY

pd.set_option('display.max_colwidth', 30)
ls_disp_ferm =['Type station', 'Type fermeture', 'Date fermeture',
               'Date ouverture', 'Station', 'CP', 'Ville']

#print df_fer[ls_disp_ferm].to_string()

#print df_fer['Type station'].value_counts()
#print df_fer['Type fermeture'].value_counts()

df_fer['Type station'] = df_fer['Type station'].apply(lambda x: x.lower())
df_fer['Type fermeture'] = df_fer['Type fermeture'].apply(\
                               lambda x: x.lower().replace(u'è', u'e'))

df_ferm_access = df_fer[(df_fer['Type station'].str.contains('access')) |\
                        (df_fer['Type fermeture'].str.contains('access'))]

df_ferm_noaccess = df_fer[(~df_fer['Type station'].str.contains('access')) &\
                          (~df_fer['Type fermeture'].str.contains('access'))]

## Check no access
#print df_ferm_noaccess[ls_disp_ferm].to_string()

print '\nNb fermetures Access', len(df_ferm_access)
print df_ferm_access[ls_disp_ferm].to_string()

# todo: extract (elsewhere), match insee, format date, match vs. gouv data

# OUVERTURES
# ##########

print u'\nWorking on Ouvertures:'

# seems to include similar info as in fermetures (not reopening?)
# todo: remove useless duplicate lines as much as possible

# CHECK ZIP CODES

# general case
for row_i, row in df_ouv.iterrows():
  if re.search(u'^[0-9]{1,2}\s?[0-9]{3}$', row['CP']):
    row['CP'] = row['CP'].replace(u' ', u'').rjust(5, '0')
  else:
    print row_i, row['CP']
# remediations
df_ouv = df_ouv[df_ouv['CP'] != '128300'] # duplicate line and mistake
df_ouv.loc[df_ouv['Ville'] == 'GONESSE', 'CP'] = '95500'

# FIX CITIES

# could check letters alone (or 2, 3), remove except for L (and D)
ls_city_fix = [('AIX-LES-BAIN S GOLFE JUAN', 'AIX-LES-BAINS GOLFE JUAN'), # might chge
               ('ROCQUENCO URT', 'ROCQUENCOURT'),
               ('GENNEVILLIE RS', 'GENNEVILLIERS'),
               ('GOUSSAINVIL LE', 'GOUSSAINVILLE'),
               ('BOULOGNE BILLANCOUR T', 'BOULOGNE BILLANCOURT'),
               ('BLANQUEFOR T', 'BLANQUEFORT'),
               ('NEUFCHATEA U', 'NEUFCHATEAU'),
               ('COULOMMIER S', 'COULOMMIERS'),
               ('RAILLENCOU RT ST OLLE', 'RAILLENCOURT ST OLLE'),
               ('ILLKIRCH GRAFFENSTA DEN', 'ILLKIRCH GRAFFENSTADEN'),
               ('WASSELONN E', 'WASSELONNE'),
               ('CLERMONT-F ERRAND', 'CLERMONT-FERRAND'),
               ('VANDOEUVR E LES NANCY', 'VANDOEUVRE LES NANCY'),
               ('ROQUEBRUN E CAP MARTIN', 'ROQUEBRUNE CAP MARTIN'),
               ('CHATEAUNEU F DU RHONE', 'CHATEAUNEUF DU RHONE'),
               ('CHATEAUROU X', 'CHATEAUROUX'),
               ('GROSTENQUI N', 'GROSTENQUIN'),
               ('VILLEURBANN E', 'VILLEURBANNE'),
               ('STRASBOUR G', 'STRASBOURG'),
               ('VILLEFRANCH E SUR SAONE', 'VILLEFRANCHE SUR SAONE'),
               ('MONTPELLIE R', 'MONTPELLIER'),
               ('CHASSENEUI L DU POITOU', 'CHASSENEUIL DU POITOU'),
               ('SCHILTIGHEI M', 'SCHILTIGHEIM'),
               ('VENDARGUE S', 'VENDARGUES'),
               ('PERPIGNAN CHAPELLE ARMENTIERE S', 'PERPIGNAN CHAPELLE ARMENTIERES')]
def adhoc_fix(ls_fix, str_to_fix):
  for (old, new) in ls_fix:
    str_to_fix = str_to_fix.replace(old, new)
  return str_to_fix
df_ouv['Ville'] = df_ouv['Ville'].apply(lambda x: adhoc_fix(ls_city_fix, x))
# remove cedex
print u'\nInspecting Cedex:'
print df_ouv[['Ville', 'CP']][df_ouv['Ville'].str.contains('cedex',
                                                           case = False)].to_string()
# following enough here because nothing after cedex
df_ouv['Ville'] = df_ouv['Ville'].apply(\
                    lambda x: re.sub(u'cedex', u'', x, flags = re.IGNORECASE).strip())

# DUPLICATES

print u'\nNb duplicates:', len(df_ouv[df_ouv.duplicated()])

# DISPLAY

print u'\nNb ouvetures Access:',\
      len(df_ouv[df_ouv['Type Station'].str.contains('access',
                                                             case = False)])
# df_ouv['Type Station'] = df_ouv['Type Station'].apply(lambda x: x.lower())
print df_ouv.to_string()
