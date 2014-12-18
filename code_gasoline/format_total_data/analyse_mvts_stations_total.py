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

# ad hoc lambda function to read total csv (dates?)
read_total_csv = lambda x: pd.read_csv(os.path.join(path_dir_total_csv,
                                                    x),
                                       encoding = 'UTF-8',
                                       dtype = {'CP' : str,
                                                'ci_1' : str,
                                                'ci_ardt_1': str})

# ##########
# FERMETURES
# ##########

# Load
df_fer_a = read_total_csv('df_total_fer_20140407.csv')
df_fer_b = read_total_csv('df_total_fer_20141208.csv')

# Merge and drop duplicates
df_fer_raw = pd.concat([df_fer_a, df_fer_b])
df_fer = df_fer_raw.drop_duplicates().copy()
df_fer.sort('Station', inplace = True)
ls_di_fer = ['Type station', 'Type fermeture', 'Date fermeture', 'Date ouverture',
             'Station', 'Adresse', 'CP', 'Ville']

# print df_fer[ls_di_fer].to_string()

# FORMAT "Type station" AND "Type fermeture"

def format_type_station(x):
  if (re.search('provisoire.*acce\s?ss?', x)) or (x == 'passage total access'):
    res = 'conv to total access'
  elif re.search('fermeture.*acce\s?ss?', x):
    res = 'ferm to total access'
  elif (u'définitive' in x) or (u'definitive' in x):
    res = 'ferm definitive'
  elif (re.search('provi\s?soire', x)) or (u'travaux' in x):
    res = 'ferm provisoire'
  elif x in ['ouverutre', 'ouerture', 'ouveerture', 'ouveture', 'ouvurture']:
    res = 'ouverture'
  else:
    res = x
  return res

df_fer.loc[~pd.isnull(df_fer['Type fermeture']), 'Type fermeture'] =\
    df_fer.loc[~pd.isnull(df_fer['Type fermeture']), 'Type fermeture'].apply(\
       lambda x: format_type_station(x))

print u'\nOverview of Type fermeture after normalization'
print df_fer['Type fermeture'].value_counts()
print df_fer[ls_di_fer][df_fer['Type fermeture'] == 'total access'].to_string()

# FIX AND FORMAT DATES

for field in ['Date fermeture', 'Date ouverture']:
  df_fer[field] = pd.to_datetime(df_fer[field],
                                 format = '%d/%m/%Y',
                                 coerce = True) # unsure

print u'\nCheck fermeture then ouverture',\
      len(df_fer[(~pd.isnull(df_fer['Date ouverture'])) &\
                 (~pd.isnull(df_fer['Date fermeture'])) &\
                 (df_fer['Date fermeture'] > df_fer['Date ouverture'])])

print df_fer[ls_di_fer][(~pd.isnull(df_fer['Date ouverture'])) &\
                        (~pd.isnull(df_fer['Date fermeture'])) &\
                        (df_fer['Date fermeture'] > df_fer['Date ouverture'])].to_string()

print u'\nCheck interval during which station closed'
df_fer['interval'] = df_fer['Date fermeture'] - df_fer['Date ouverture']
print df_fer['interval'].describe()

# OVERVIEW DUPLICATE STATIONS

# check if several rows for the same station (based on station name: some errors)
ls_dup_stations = list(df_fer['Station'][df_fer.duplicated('Station')].unique())
df_fer_dup = df_fer[df_fer['Station'].isin(ls_dup_stations)].copy()
df_fer_dup.sort('Station', inplace = True)
print df_fer_dup[ls_di_fer].to_string()

# ##########
# OUVERTURES
# ##########

# Load
df_ouv_a = read_total_csv('df_total_ouv_20140407.csv')
df_ouv_b = read_total_csv('df_total_ouv_20141208.csv')
