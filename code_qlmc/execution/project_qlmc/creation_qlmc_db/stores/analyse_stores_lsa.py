#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import datetime as datetime
import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import pprint

path_dir_qlmc = os.path.join(path_data, 'data_qlmc')
path_dir_built_json = os.path.join(path_dir_qlmc, 'data_built' , 'data_json_qlmc')
path_dir_built_csv = os.path.join(path_dir_qlmc, 'data_built' , 'data_csv')

path_dir_source_lsa = os.path.join(path_dir_qlmc, 'data_source', 'data_lsa_xls')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

path_dir_built_hdf5 = os.path.join(path_dir_qlmc, 'data_built', 'data_hdf5')

# READ LSA EXCEL FILE
# need to work with _no1900 at CREST for now (older versions of numpy/pandas/xlrd...?)
df_lsa = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_lsa.csv'),
                     parse_dates = [u'DATE ouv',
                                    u'DATE ferm',
                                    u'DATE réouv',
                                    u'DATE chg enseigne',
                                    u'DATE chgt surf'],
                     encoding = 'UTF-8')

# Exclude drive and hard discount for matching
df_lsa = df_lsa[(df_lsa['Type_alt'] == 'H')|\
                (df_lsa['Type_alt'] == 'S')].copy()

# Some stats decs
print u'\nNb of dead stores'
print len(df_lsa[(~pd.isnull(df_lsa[u'DATE ferm'])) &\
                  (pd.isnull(df_lsa[u'DATE réouv']))])

print u'\nNb stores (dead or alive) with valid gps:'
print len(df_lsa[(~pd.isnull(df_lsa['Longitude'])) &\
                 (~pd.isnull(df_lsa['Latitude']))])

# STORES OPENED WITHIN QLMC DATA PERIOD
ls_disp_1 = [u'Ident', u'Enseigne', u'ADRESSE1', u'Ville', 'Code INSEE',
             u'DATE ouv', u'DATE ferm', u'DATE réouv']

print u'\nStores opened over qlmc period'
df_lsa_opened = df_lsa[(df_lsa[u'DATE ouv'] > '2007-05') &\
                       (df_lsa[u'DATE ouv'] < '2012-06')].copy()
print df_lsa_opened[ls_disp_1].to_string()

# CLOSED (AND NOT REOPENED) STORES WITHIN QLMC DATA PERIOD
print u'\nStores closed over qlmc period'
df_lsa_closed = df_lsa[(df_lsa[u'DATE ferm'] > '2007-05') &\
                       (df_lsa[u'DATE ferm'] < '2012-06') &\
                       (pd.isnull(df_lsa[u'DATE réouv']))].copy()
print df_lsa_closed[ls_disp_1].to_string()

# STORES WITH SIGNIFICANT BRAND CHANGES WITHIN QLMC DATA PERIOD
ls_disp_2 = [u'Ident', u'Enseigne', 'Ex enseigne',
             u'ADRESSE1', u'Ville', 'Code INSEE',
             u'DATE ouv', u'DATE chg enseigne']

print u'\nStores with group change over qlmc period'
print df_lsa[ls_disp_2][(df_lsa['DATE chg enseigne'] > '2007-05') &\
                        (df_lsa['DATE chg enseigne'] < '2012-06') &\
                        (df_lsa['Groupe'] != df_lsa['Ex groupe'])].to_string()

# todo: detect duplicates
# SIRET/SIREN
df_lsa[u'N°Siren'] = df_lsa[u'N°Siren'].apply(\
                       lambda x: u'{:09d}'.format(int(x)) if not pd.isnull(x)\
                                                          else None)
df_lsa[u'N°Siret'] = df_lsa[u'N°Siret'].apply(\
                       lambda x: u'{:05d}'.format(int(x)) if not pd.isnull(x)\
                                                          else None)
df_lsa[u'Siret'] = df_lsa[u'N°Siren'] + df_lsa[u'N°Siret']
se_siret_vc = df_lsa[u'Siret'].value_counts()
df_lsa.set_index(u'Siret', inplace = True)
df_lsa[u'dup'] = se_siret_vc

df_dup = df_lsa[df_lsa['dup'] == 2].copy()
df_dup.sort(inplace = True)
print df_dup[ls_disp_1].to_string()

# generate duplicate detection:
# loop on closed store... search newly opened stores within same area (or same siret btw)
df_lsa_closed_a = df_lsa[(~pd.isnull(df_lsa[u'DATE ferm'])) &\
                         (pd.isnull(df_lsa[u'DATE réouv']))].copy()
df_lsa_closed.sort(columns = ['Code INSEE', 'DATE ouv'], inplace = True)
# Quite a few indec (siret) are NaN (see why) hence change index back to Ident
df_lsa_closed_a['Siret'] = df_lsa_closed_a.index
df_lsa_closed_a.index = df_lsa_closed_a['Ident']
df_lsa['Siret'] = df_lsa.index
df_lsa.index = df_lsa['Ident']
# Look for store opened after store closed within same INSEE area
ls_suspects = []
for i, row_i in df_lsa_closed_a.iterrows():
  # print '\nFermeture:', row_i[u'DATE ferm']
  ls_open = []
  for j, row_j in df_lsa[df_lsa[u'Code INSEE'] == row_i['Code INSEE']].iterrows():
    td = row_j[u'DATE ouv'] - row_i[u'DATE ferm']
    # could drop second condition
    if (td >= datetime.timedelta(days=0)) and\
       (td <= datetime.timedelta(days=365)):
      #print 'Ouverture, :', row_i[u'DATE ouv'], 'Time delta:', td
      #print row_i[u'Enseigne'], row_i['ADRESSE1'], row_i['Siret']
      #print row_j[u'Enseigne'], row_j['ADRESSE1'], row_j['Siret']
      ls_open.append([row_j['Ident'], td])
  ls_suspects.append([row_i['Ident'], ls_open])

# Check chains and if stores closed after reconciliation
# Check results (can use index)
ls_s_noclosed_ind = []
ls_s_closed_ind = []
for row in ls_suspects:
  if row[1]:
    ls_s_noclosed_ind.append(row[0])
    for subrow in row[1]:
      ls_s_noclosed_ind.append(subrow[0])
  else:
    ls_s_closed_ind.append(row[0])

# df_lsa[ls_disp_1].ix[[20, 124704]]

print u'\nStores with multiple lines'
print df_lsa[ls_disp_1].ix[ls_s_noclosed_ind].to_string()

print u'\nStores potentially closed and not replaced'
print df_lsa[ls_disp_1].ix[ls_s_closed_ind].to_string()

# Inspect: new opening very same day
# Inspect: new opening later on (any date...)

# Check these weird lines
print u'\nWeird lines: opened and closed on same date'
print df_lsa[ls_disp_1][df_lsa['DATE ouv'] == df_lsa['DATE ferm']].to_string()

# todo: increase in store surface?
# todo: gps quality? missing data? distances? (google API)

# GENERAT COLUMNS BY PERIOD WITH CURRENT ENSEIGNE WHEN STORE IS ACTIVE
ls_qlmc_dates = ['2007-05',
                 '2007-08',
                 '2008-01',
                 '2008-04',
                 '2009-03',
                 '2009-09',
                 '2010-03',
                 '2010-10',
                 '2011-01',
                 '2011-04',
                 '2011-10',
                 '2012-01',
                 '2012-06']

for qlmc_date in ls_qlmc_dates:
  df_lsa[qlmc_date] = df_lsa['Enseigne']
  # Not opened yet (left untouched if DATE ouv is unknown)
  df_lsa.loc[df_lsa[u'DATE ouv'] > qlmc_date, qlmc_date] = None
  # Closed and not reopened
  df_lsa.loc[(df_lsa[u'DATE ferm'] < qlmc_date) &
             (pd.isnull(df_lsa[u'DATE réouv'])), qlmc_date] = None
  # Write previous enseigne if changed since then (check consistency if missing data)
  df_lsa.loc[(qlmc_date >= df_lsa[u'DATE ouv']) &\
             (qlmc_date < df_lsa[u'DATE chg enseigne']), qlmc_date] = df_lsa['Ex enseigne']

df_lsa.to_csv(os.path.join(path_dir_built_csv,
                           'df_lsa_for_qlmc.csv'),
              encoding = 'UTF-8')

## DEPRECATED (CSV PREFERED)

## FORMAT DATE AND OUTPUT TO EXCEL FILE
#for field in [u'DATE ouv', u'DATE ferm', u'DATE réouv',
#              u'DATE chg enseigne', u'DATE chgt surf']:
#  df_lsa[field][df_lsa[field] < '1900'] = pd.tslib.NaT
#  df_lsa[field] = df_lsa[field].apply(lambda x: x.date()\
#                                        if type(x) is pd.tslib.Timestamp\
#                                        else pd.tslib.NaT)
#
#writer = pd.ExcelWriter(os.path.join(path_dir_built_csv, 'LSA_enriched.xlsx'))
#df_lsa.to_excel(writer, index = False)
#writer.close()
