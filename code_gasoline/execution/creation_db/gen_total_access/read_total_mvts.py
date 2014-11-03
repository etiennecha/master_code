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
  pdf_file = subprocess.Popen([os.path.join(path_pdftotext, 'pdftotext.exe'),
                               #'-layout' ,
                               '-raw',
                               path_file,
                               '-'], stdout=PIPE)
  data = pdf_file.communicate()[0]
  return data

path_dir_raw_stations = os.path.join(path_data, 'data_gasoline', 'data_raw', 'data_stations')

#path_pdf_total_mvts = os.path.join(path_dir_raw_stations, 'data_other', 'mvts_stations_services.pdf') 
#str_pdf = read_pdftotext(path_pdf_total_mvts, path_dir)
#ls_pdf = str_pdf.split('\r\n')

# file obtained with pdftohtml and options -i -c -noframes
path_html_total_mvts = os.path.join(path_dir_raw_stations, 'data_other', 'mvts_stations_services.html')
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

df_final = pd.DataFrame(ls_ls_final[1:], columns = ls_ls_final[0])

#print df_final[ls_ls_final[0][:-2]].to_string()
# fix line 82: only mistake spotted so far
# Station report: exploitation: ' - ' probably gets many false positive.. regex with postal code..?
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

df_final_2 = pd.DataFrame(ls_ls_final_2[1:], columns = ls_ls_final_2[0])
