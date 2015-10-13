#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from functions_generic_qlmc import *
from functions_geocoding import *
from functions_string import *
import os, sys
import re
import numpy as np
import datetime as datetime
import pandas as pd
import matplotlib.pyplot as plt
import pprint
#from mpl_toolkits.basemap import Basemap

path_dir_built = os.path.join(path_data,
                               'data_supermarkets',
                               'data_built',
                               'data_lsa')

path_dir_csv = os.path.join(path_dir_built,
                            'data_csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

df_lsa = pd.read_csv(os.path.join(path_dir_csv,
                                  'df_lsa.csv'),
                     dtype = {u'C_INSEE' : str,
                              u'C_INSEE_Ardt' : str,
                              u'C_Postal' : str,
                              u'SIREN' : str,
                              u'NIC' : str,
                              u'SIRET' : str},
                     parse_dates = [u'Date_Ouv', u'Date_Fer', u'Date_Reouv',
                                    u'Date_Chg_Enseigne', u'Date_Chg_Surface'],
                     encoding = 'UTF-8')

print u'Exclude Drive for QLMC study (at least for matching)'
df_lsa = df_lsa[(df_lsa['Type_Alt'] == 'H')|\
                (df_lsa['Type_Alt'] == 'S')].copy()

# ##################
# STATS DES
# ##################

# STORES OPENED WITHIN QLMC DATA PERIOD
lsd0 = [u'Ident', u'Enseigne', u'Adresse1', u'Ville', 'C_INSEE',
        u'Date_Ouv', u'Date_Fer', u'Date_Reouv']

# Stores opened
df_lsa_opened = df_lsa[(df_lsa[u'Date_Ouv'] > '2007-05') &\
                       (df_lsa[u'Date_Ouv'] < '2012-06')].copy()
print u'\nNb stores opened over qlmc period: {:d}'.format(len(df_lsa_opened))
print u'Overview:'
print df_lsa_opened[lsd0][0:20].to_string()

# Stores closed (could check if not reopened somewhat later)
df_lsa_closed = df_lsa[(df_lsa[u'Date_Fer'] > '2007-05') &\
                       (df_lsa[u'Date_Fer'] < '2012-06') &\
                       (pd.isnull(df_lsa[u'Date_Reouv']))].copy()
print u'\nNb stores closed over qlmc period: {:d}'.format(len(df_lsa_closed))
print u'Overview:'
print df_lsa_closed[lsd0][0:20].to_string()

# DUPLICATES BASED ON SIRET (Move?)

df_dup_siret = df_lsa[df_lsa.duplicated('SIRET', take_last = False) |\
                      df_lsa.duplicated('SIRET', take_last = True)].copy()
df_dup_siret.sort('SIRET', inplace = True)
print u'\nNb potential duplicates (SIRET): {:d}'.format(len(df_dup_siret))
print u'Overview:'
print df_dup_siret[lsd0][0:20].to_string()

# DUPLICATES BASED ON DATES (Move?)

# loop on closed store... search newly opened stores within same area (or same siret btw)
df_lsa_closed_a = df_lsa[(~pd.isnull(df_lsa[u'Date_Fer'])) &\
                         (pd.isnull(df_lsa[u'Date_Reouv']))].copy()
df_lsa_closed.sort(columns = ['C_INSEE', 'Date_Ouv'], inplace = True)
# Quite a few indec (siret) are NaN (see why) hence change index back to Ident
df_lsa_closed_a.reset_index(inplace = True)
df_lsa_closed_a.index = df_lsa_closed_a['Ident']
df_lsa.reset_index(inplace = True)
df_lsa.index = df_lsa['Ident']
# Look for store opened after store closed within same INSEE area
ls_suspects = []
for i, row_i in df_lsa_closed_a.iterrows():
  # print '\nFermeture:', row_i[u'DATE ferm']
  ls_open = []
  for j, row_j in df_lsa[df_lsa[u'C_INSEE'] == row_i['C_INSEE']].iterrows():
    td = row_j[u'Date_Ouv'] - row_i[u'Date_Fer']
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

# df_lsa[lsd0].ix[[20, 124704]]

print u'\nNb Stores with multiple lines: {:d}'.format(len(ls_s_noclosed_ind))
print u'Overview:'
print df_lsa[lsd0].ix[ls_s_noclosed_ind][0:20].to_string()

print u'\nNb Stores potentially closed and not replaced: {:d}'.format(len(ls_s_closed_ind))
print u'Overview:'
print df_lsa[lsd0].ix[ls_s_closed_ind][0:20].to_string()

print u'\nWeird lines: opened and closed on same date'
print u'Overview:'
print df_lsa[lsd0][df_lsa['Date_Ouv'] == df_lsa['Date_Fer']][0:20].to_string()

# ###############################
# GENERATE COLUMNS BY QLMC PERIOD
# ###############################

# todo: see if can better take into account real dates (ranges?)
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
  df_lsa['Enseigne_Alt_{:s}'.format(qlmc_date)] = df_lsa['Enseigne_Alt']
  # Not opened yet (left untouched if DATE ouv is unknown)
  df_lsa.loc[df_lsa[u'Date_Ouv'] > qlmc_date,
             'Enseigne_Alt_{:s}'.format(qlmc_date)] = None
  # Closed and not reopened in time
  df_lsa.loc[(df_lsa[u'Date_Fer'] < qlmc_date) &\
             ((pd.isnull(df_lsa[u'Date_Reouv'])) |
              (df_lsa[u'Date_Reouv'] > qlmc_date)),
             'Enseigne_Alt_{:s}'.format(qlmc_date)] = None
  # Write previous enseigne if changed since then (check consistency if missing data)
  df_lsa.loc[(qlmc_date >= df_lsa[u'Date_Ouv']) &\
             (qlmc_date <= df_lsa[u'Date_Chg_Enseigne']),
             'Enseigne_Alt_{:s}'.format(qlmc_date)] = df_lsa['Ex_Enseigne_Alt']

print u'\nNb active stores per period:'
for qlmc_date in ls_qlmc_dates:
  print qlmc_date, ':', len(df_lsa[~pd.isnull(df_lsa['Enseigne_Alt_{:s}'.format(qlmc_date)])])

## todo: closed and open vs previous
#len(df_lsa[~pd.isnull(df_lsa['Enseigne_Alt_2010-10']) &\
#           pd.isnull(df_lsa['Enseigne_Alt_2011-01'])])
#print df_lsa[~pd.isnull(df_lsa['Enseigne_Alt_2010-10']) &\
#             pd.isnull(df_lsa['Enseigne_Alt_2011-01'])][lsd0].to_string()

df_lsa.to_csv(os.path.join(path_dir_csv,
                           'df_lsa_for_qlmc.csv'),
              index = False,
              encoding = 'UTF-8')
