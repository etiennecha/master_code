#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import add_to_path
from add_to_path import path_data, path_dir
import os, sys
import subprocess
from subprocess import PIPE, Popen
from BeautifulSoup import BeautifulSoup
import re
import pandas as pd
from matching_insee import *

path_dir_total = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_source',
                              u'data_total')
path_dir_total_raw = os.path.join(path_dir_total, 'data_total_raw')
path_dir_total_csv = os.path.join(path_dir_total, 'data_total_csv')

#def read_pdftotext(path_file, path_pdftotext):
#  pdf_file = subprocess.Popen([os.path.join(path_pdftotext,
#                                            'pdftotext.exe'),
#                               #'-layout' ,
#                               '-raw',
#                               path_file,
#                               '-'], stdout=PIPE)
#  data = pdf_file.communicate()[0]
#  return data
#
#path_pdf_total_mvts = os.path.join(path_dir_raw_stations,
#                                   'data_other',
#                                   'mvts_stations_services.pdf') 
#str_pdf = read_pdftotext(path_pdf_total_mvts, path_dir)
#ls_pdf = str_pdf.split('\r\n')

# #######################
# READ HTML FILE
# #######################

# HTML file obtained with pdftohtml and options -i -c -noframes
path_html_total_mvts = os.path.join(path_dir_total_raw,
                                    u'20140407_mvts_stations_total.html')
html_file = open(path_html_total_mvts, 'r').read()
soup = BeautifulSoup(html_file)

ls_pages = soup.findAll('div', {'style' : "position:relative;width:892;height:1262;"})
# up to 60: similar format a priori, then check

# FERMETURES

print u'\nReading fermetures'

ls_rows = []
for page_ind, page in enumerate(ls_pages[0:61]):
  ls_rows += [(page_ind, row)\
                for row in page.findAll('div',
                                        {'style' : re.compile('position:absolute.*')})]

#page_1 = soup.find('div', {'style' : "position:relative;width:892;height:1262;"})
#ls_rows_1 = page_1.findAll('div', {'style' : re.compile('position:absolute.*')})

# A bit of a fragile assumption (detailed below)
ls_ls_results = []
ls_results = []
for (page_ind, row) in ls_rows:
  col_ind = int(re.search('left:([0-9]*)$', row['style']).group(1))
  row_ind = int(re.search('top:([0-9]*);left', row['style']).group(1))
  str_row = row.find('span', {'class' : True}).findAll(text = True)
  # assume no new row start after page break without first column filled
  if ls_results and col_ind != 47 and row_ind == 2:
    print page_ind, col_ind, row_ind, str_row
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

print u'\nReading ouvertures'

ls_rows = []
for page_ind, page in enumerate(ls_pages[61:], start = 61):
  ls_rows += [(page_ind, row)\
                for row in page.findAll('div',
                                        {'style' : re.compile('position:absolute.*')})]

# todo: print page break inds and correct manually
ls_ls_results = []
ls_results = []
for (page_ind, row) in ls_rows:
  col_ind = int(re.search('left:([0-9]*)$', row['style']).group(1))
  row_ind = int(re.search('top:([0-9]*);left', row['style']).group(1))
  str_row = row.find('span', {'class' : True}).findAll(text = True)
  if ls_results and col_ind != 58 and row_ind == 2:
    print page_ind, col_ind, row_ind, str_row
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

def adhoc_fix(ls_fix, str_to_fix):
  for (old, new) in ls_fix:
    str_to_fix = str_to_fix.replace(old, new)
  return str_to_fix

def adhoc_date_fix(some_date):
  if re.match(u'^[0-9]{2}/[0-9]{2}/[0-9]{4}$', some_date):
    pass
  elif re.match(u'^[0-9]{2}/[0-9]{2}/[0-9]{2}$', some_date):
    some_date = some_date[0:6] + '20' + some_date[6:]
    print u'Fixed:', some_date
  else:
    some_date = None
  return some_date

# LOAD CLASS matching_insee
path_dir_match_insee = os.path.join(path_data, u'data_insee', 'match_insee_codes')
path_df_corr = os.path.join(path_dir_match_insee, 'df_corr_gas.csv')
matching_insee = MatchingINSEE(path_df_corr)

# LOAD df_insee_com (to control if insee_codes still in use)
path_dir_insee_extracts = os.path.join(path_data, u'data_insee', u'data_extracts')
df_insee_com = pd.read_csv(os.path.join(path_dir_insee_extracts,
                                        u'df_communes.csv'),
                           encoding = 'utf-8',
                           dtype = str)

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
               ('CLERMONT-FER RAND', 'CLERMONT-FERRAND'),
               ('SAINT-GREGOIR E', 'SAINT-GREGOIRE'),
               ('SOUFFELWEYER SHEIM', 'SOUFFELWEYERSHEIM'),
               ('LE PLESSIS-BELLEV ILLE', 'LE PLESSIS-BELLEVILLE'),
               ('CHAUDENEY S/MOSELLE', 'CHAUDENEY SUR MOSELLE'),
               ('CHAMPIGNY S/MARNB', 'CHAMPIGNY SUR MARNE'),
               ("CHAMPAGNE AU MT D'OR", "CHAMPAGNE AU MONT D'OR"),
               ('MONTAIGUT COMBRAILLE', 'MONTAIGUT EN COMBRAILLE'),
               ('LONGEVILLE ST AVOLD', 'LONGEVILLE LES ST AVOLD'),
               ('PONT D ISERE', 'PONT DE L ISERE'),
               ('ROISSY C DE GAULLE', 'ROISSY EN FRANCE'),
               ('CHATILLON SUR BAGNEUX', 'CHATILLON'),
               ('MONTREUIL SUR MER', 'MONTREUIL'),
               ('ORLEANS LA SOURCE', 'LA SOURCE')] # ORLEANS

df_fer['Ville'] = df_fer['Ville'].apply(lambda x: adhoc_fix(ls_city_fix, x))

# remove cedex
print '\nInspecting Cedex:'
print df_fer[['Ville', 'CP']][df_fer['Ville'].str.contains('cedex',
                                                           case = False)].to_string()

# mistake in zip (found during insee matchin)
df_fer.loc[(df_fer['CP'] == '92570') &\
           (df_fer['Ville'] == 'CHAUMONTEL'), 'CP'] = '95270'

# following enough here because nothing after cedex
df_fer['Ville'] = df_fer['Ville'].apply(\
                    lambda x: re.sub(u'cedex', u'', x, flags = re.IGNORECASE).strip())

# DATES

print u'\nFix dates:'
for date_field in [u'Date fermeture', u'Date ouverture']:
  df_fer[date_field] = df_fer[date_field].apply(lambda x: adhoc_date_fix(x))

# DUPLICATES

print u'\nNb duplicates:', len(df_fer[df_fer.duplicated()])
df_fer = df_fer.drop_duplicates()


# DISPLAY

pd.set_option('display.max_colwidth', 30)
ls_disp_fer =['Type station', 'Type fermeture', 'Date fermeture',
               'Date ouverture', 'Station', 'CP', 'Ville']

#print df_fer[ls_disp_ferm].to_string()

#print df_fer['Type station'].value_counts()
#print df_fer['Type fermeture'].value_counts()

df_fer['Type station'] = df_fer['Type station'].apply(lambda x: x.lower())
df_fer['Type fermeture'] = df_fer['Type fermeture'].apply(\
                               lambda x: x.lower().replace(u'è', u'e'))

df_fer_access = df_fer[(df_fer['Type station'].str.contains('access')) |\
                       (df_fer['Type fermeture'].str.contains('access'))].copy()

df_fer_noaccess = df_fer[(~df_fer['Type station'].str.contains('access')) &\
                         (~df_fer['Type fermeture'].str.contains('access'))].copy()

## Check no access
#print df_ferm_noaccess[ls_disp_ferm].to_string()

print '\nNb fermetures Access', len(df_fer_access)
print df_fer_access[ls_disp_fer].to_string()

# Remaining station duplicates
dup_stations = df_fer_access['Station'][df_fer.duplicated('Station')].unique()
df_fer_access.sort(['Station', 'Date ouverture'], inplace = True)
print df_fer_access[df_fer_access['Station'].isin(dup_stations)][ls_disp_fer].to_string()

# INSEE MATCHING

ls_fer_matched = []
for row_i, row in df_fer.iterrows():
  match = matching_insee.match_city(row['Ville'], row['CP'][:-3], row['CP'])
  ls_fer_matched.append(match)

dict_fer_res = {}
for i, match in enumerate(ls_fer_matched):
  dict_fer_res.setdefault(match[1], []).append(i)

print '\nINSEE Matching overview:'
for k,v in dict_fer_res.items():
	print k, len(v)

##df_ferm
#print df_fer[ls_disp_fer].iloc[dict_fer_res['no_match']].to_string()
# fixed manually

## PRELIMINARY VERSION (NO CHECK ON VALIDITY)
#
#df_fer_ma_insee = pd.DataFrame([x[0][0] for x in ls_fer_matched],
#                               index = df_fer.index,
#                               columns = ['i_city', 'i_zip', 'insee_code'])

# Check if several results
ls_fer_multim = [i for i, match in enumerate(ls_fer_matched) if len(match[0]) > 1]

ls_rows_fer_insee = []
for ls_match in ls_fer_matched:
  # first match if several (check city name)
  row_fer_insee = [ls_match[0][0][0]] +\
                   list(refine_insee_code(df_insee_com['CODGEO'].values,
                                          ls_match[0][0][2]))
  ls_rows_fer_insee.append(row_fer_insee)

df_fer_ma_insee = pd.DataFrame(ls_rows_fer_insee,
                               index = df_fer.index,
                               columns = ['city', 'ci_1', 'ci_ardt_1'])

df_fer_final = pd.merge(df_fer,
                        df_fer_ma_insee,
                        left_index = True,
                        right_index = True,
                        how = 'left')

ls_disp_fer_ci = ls_disp_fer + ['city', 'ci_ardt_1']
print df_fer_final[ls_disp_fer_ci][pd.isnull(df_fer_final['ci_1'])].to_string()
#print df_fer_final[ls_disp_fer_ci].iloc[dict_fer_res['dpt_city_match']].to_string()
##print df_fer_final[ls_disp_fer_ci].iloc[dict_fer_res['dpt_city_in_match(es)']].to_string()

df_fer_access_final =\
    df_fer_final[(df_fer_final['Type station'].str.contains('access',
                                                            case = False)) |\
                 (df_fer_final['Type fermeture'].str.contains('access',
                                                              case = False))]

pd.set_option('display.max_colwidth', 27)
#print df_fer_access_final[ls_disp_fer_ci].to_string()
#print df_fer_access_final[ls_disp_fer_ci]\
#        [df_fer_access_final['Date ouverture'] == '13/12/2013'].to_string()

df_fer_final.to_csv(os.path.join(path_dir_total_csv,
                                 'df_total_fer_20140407.csv'),
                    encoding = 'UTF-8',
                    index = False)

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
               ('PERPIGNAN CHAPELLE ARMENTIERE S', 'PERPIGNAN CHAPELLE ARMENTIERES'),
               ('VALENCIENN ES', 'VALENCIENNES'),
               ('CARCASSON NE', 'CARCASSONNE'),
               ('BALLAINVILLI ERS', 'BALLAINVILLIERS'),
               ('CHATELLERA ULT', 'CHATELLERAULT'),
               ('LOUVECIENN ES', 'LOUVECIENNES'),
               ('RAMBOUILLE T', 'RAMBOUILLET'),
               ('PONTCHATEA U', 'PONTCHATEAU'),
               ('FONBEAUZAR D', 'FONBEAUZARD'),
               ('L HERBERGEM ENT', 'L HERBERGEMENT'),
               ('AIX-LES-BAIN S', 'AIX-LES-BAINS'),
               ('Roissy C de Gaulle', 'ROISSY'), # from now: insee matching
               ('CHAUMONT ARRAS', 'CHAUMONT'), # line pbm => ARRAS
               ('BEAUMONT S/OISE', 'BEAUMONT SUR OISE'),
               ("PONT L'ABBE GRANDPUITS", "PONT L'ABBE"), # line pbm => GRANDPUITS
               ("CHAMPAGNE AU MT D'OR", "CHAMPAGNE AU MONT D'OR"),
               ('REZE LES NANTES', 'REZE'), # add in corr?
               ('CHATOU ARTIGUES', 'CHATOU'), # line pbm => ARTIGUES
               ('PERPIGNAN CHAPELLE ARMENTIERES', 'PERPIGNAN'), # line pbm => CHAPPELLE...
               ('LONGEVILLE ST AVOLD', 'LONGEVILLE LES ST AVOLD'),
               ('MARSEILLE ARRAS', 'MARSEILLE'), # line pbm => ARRAS
               ('TRESSES BEAUCAIRE', 'TRESSES'), # line pbm => BAUCAIRE
               ('LUNEVLLE', 'LUNEVILLE'), # mistake
               ('RAILLENCOURT ST OLLE',  'RAILLENCOURT STE OLLE'), # mistake
               ('ANGOULEME SECLIN', 'ANGOULEME'), # line pbm => SECLIN
               ('AIX-LES-BAINS GOLFE JUAN', 'AIX-LES-BAINS')] # line pbm => GOLFE JUAN

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
df_ouv = df_ouv.drop_duplicates()

# DATES

print u'\nFix dates:'
df_ouv['Date'] = df_ouv['Date'].apply(lambda x: adhoc_date_fix(x))

# DISPLAY

print u'\nNb ouvetures Access:',\
      len(df_ouv[df_ouv['Type Station'].str.contains('access',
                                                     case = False)])
# df_ouv['Type Station'] = df_ouv['Type Station'].apply(lambda x: x.lower())
print df_ouv.to_string()

# INSEE MATCHING

# df_ouv:
# on page breaks: lines merged though they should not (hence two communes)
# todo: avoid merging and try to fill info when only city is available

# INSEE MATCHING

ls_ouv_matched = []
for row_i, row in df_ouv.iterrows():
  match = matching_insee.match_city(row['Ville'], row['CP'][:-3], row['CP'])
  ls_ouv_matched.append(match)

dict_ouv_res = {}
for i, match in enumerate(ls_ouv_matched):
  dict_ouv_res.setdefault(match[1], []).append(i)

print '\nINSEE Matching overview:'
for k,v in dict_ouv_res.items():
	print k, len(v)

##df_ouv
#print df_ouv.iloc[dict_ouv_res['no_match']].to_string()
# fixed manually

## PRELIMINARY VERSION (NO CHECK ON VALIDITY)
#
#df_ouv_ma_insee = pd.DataFrame([x[0][0] for x in ls_ouv_matched],
#                               index = df_ouv.index,
#                               columns = ['i_city', 'i_zip', 'insee_code'])

# CHECK INSEE CODES STILL IN USE + DISAMB BIG CITY ARDTS


# Check if several results
ls_ouv_multim = [i for i, match in enumerate(ls_ouv_matched) if len(match[0]) > 1]

ls_rows_ouv_insee = []
for ls_match in ls_ouv_matched:
  # first match if several (check city name)
  row_ouv_insee = [ls_match[0][0][0]] +\
                   list(refine_insee_code(df_insee_com['CODGEO'].values,
                                          ls_match[0][0][2]))
  ls_rows_ouv_insee.append(row_ouv_insee)

df_ouv_ma_insee = pd.DataFrame(ls_rows_ouv_insee,
                               index = df_ouv.index,
                               columns = ['city', 'ci_1', 'ci_ardt_1'])

df_ouv_final = pd.merge(df_ouv,
                        df_ouv_ma_insee,
                        left_index = True,
                        right_index = True,
                        how = 'left')

print df_ouv_final[pd.isnull(df_ouv_final['ci_1'])].to_string()
#print df_ouv_final.iloc[dict_ouv_res['dpt_city_in_match(es)']].to_string()
#print df_ouv_final.iloc[dict_ouv_res['dpt_city_match']].to_string()

# a lot have not label and may be Total Access?
df_ouv_access_final =\
   df_ouv_final[(df_ouv_final['Type Station'].str.contains('access',
                                                           case = False))]

df_ouv_final.to_csv(os.path.join(path_dir_total_csv,
                                 'df_total_ouv_20140407.csv'),
                    encoding = 'UTF-8',
                    index = False)
