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

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_lsa')

path_built_csv = os.path.join(path_built,
                            'data_csv')

path_insee = os.path.join(path_data, 'data_insee')
path_insee_match = os.path.join(path_insee, 'match_insee_codes')
path_insee_extracts = os.path.join(path_insee, 'data_extracts')

df_lsa = pd.read_csv(os.path.join(path_built_csv,
                                  'df_lsa.csv'),
                     dtype = {u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_Postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'UTF-8')

print u'Exclude Drive for QLMC study (at least for matching)'
df_lsa = df_lsa[(df_lsa['type_alt'] == 'H')|\
                (df_lsa['type_alt'] == 'S')].copy()

# ##################
# STATS DES
# ##################

# STORES OPENED WITHIN QLMC DATA PERIOD
lsd0 = [u'id_lsa', u'enseigne', u'adresse1', u'ville', 'c_insee',
        u'date_ouv', u'date_fer', u'date_reouv']

# Stores opened
df_lsa_opened = df_lsa[(df_lsa[u'date_ouv'] > '2007-05') &\
                       (df_lsa[u'date_ouv'] < '2012-06')].copy()
print u'\nNb stores opened over qlmc period: {:d}'.format(len(df_lsa_opened))
print u'Overview:'
print df_lsa_opened[lsd0][0:20].to_string()

# Stores closed (could check if not reopened somewhat later)
df_lsa_closed = df_lsa[(df_lsa[u'date_fer'] > '2007-05') &\
                       (df_lsa[u'date_fer'] < '2012-06') &\
                       (pd.isnull(df_lsa[u'date_reouv']))].copy()
print u'\nNb stores closed over qlmc period: {:d}'.format(len(df_lsa_closed))
print u'Overview:'
print df_lsa_closed[lsd0][0:20].to_string()

# DUPLICATES BASED ON SIRET (Move?)

df_dup_siret = df_lsa[df_lsa.duplicated('c_siret', take_last = False) |\
                      df_lsa.duplicated('c_siret', take_last = True)].copy()
df_dup_siret.sort('c_siret', inplace = True)
print u'\nNb potential duplicates (c_siret): {:d}'.format(len(df_dup_siret))
print u'Overview:'
print df_dup_siret[lsd0][0:20].to_string()

# DUPLICATES BASED ON DATES (Move?)

# loop on closed store... search newly opened stores within same area (or same siret btw)
df_lsa_closed_a = df_lsa[(~pd.isnull(df_lsa[u'date_fer'])) &\
                         (pd.isnull(df_lsa[u'date_reouv']))].copy()
df_lsa_closed.sort(columns = ['c_insee', 'date_ouv'], inplace = True)
# Quite a few indec (siret) are NaN (see why) hence change index back to Ident
df_lsa_closed_a.reset_index(inplace = True)
df_lsa_closed_a.index = df_lsa_closed_a['id_lsa']
df_lsa.reset_index(inplace = True)
df_lsa.index = df_lsa['id_lsa']
# Look for store opened after store closed within same INSEE area
ls_suspects = []
for i, row_i in df_lsa_closed_a.iterrows():
  # print '\nFermeture:', row_i[u'DATE ferm']
  ls_open = []
  for j, row_j in df_lsa[df_lsa[u'c_insee'] == row_i['c_insee']].iterrows():
    td = row_j[u'date_ouv'] - row_i[u'date_fer']
    # could drop second condition
    if (td >= datetime.timedelta(days=0)) and\
       (td <= datetime.timedelta(days=365)):
      #print 'Ouverture, :', row_i[u'DATE ouv'], 'Time delta:', td
      #print row_i[u'Enseigne'], row_i['ADRESSE1'], row_i['Siret']
      #print row_j[u'Enseigne'], row_j['ADRESSE1'], row_j['Siret']
      ls_open.append([row_j['id_lsa'], td])
  ls_suspects.append([row_i['id_lsa'], ls_open])

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
print df_lsa[lsd0][df_lsa['date_ouv'] == df_lsa['date_fer']][0:20].to_string()

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
  df_lsa['enseigne_alt_{:s}'.format(qlmc_date)] = df_lsa['enseigne_alt']
  # Not opened yet (left untouched if DATE ouv is unknown)
  df_lsa.loc[df_lsa[u'date_ouv'] > qlmc_date,
             'enseigne_alt_{:s}'.format(qlmc_date)] = None
  # Closed and not reopened in time
  df_lsa.loc[(df_lsa[u'date_fer'] < qlmc_date) &\
             ((pd.isnull(df_lsa[u'date_reouv'])) |
              (df_lsa[u'date_reouv'] > qlmc_date)),
             'enseigne_alt_{:s}'.format(qlmc_date)] = None
  # Write previous enseigne if chhgde since then (check consistency if missing data)
  df_lsa.loc[(qlmc_date >= df_lsa[u'date_ouv']) &\
             (qlmc_date <= df_lsa[u'date_chg_enseigne']),
             'enseigne_alt_{:s}'.format(qlmc_date)] = df_lsa['ex_enseigne_alt']

print u'\nNb active stores per period:'
for qlmc_date in ls_qlmc_dates:
  print qlmc_date, ':',\
        len(df_lsa[~pd.isnull(df_lsa['enseigne_alt_{:s}'.format(qlmc_date)])])

## todo: closed and open vs previous
#len(df_lsa[~pd.isnull(df_lsa['enseigne_alt_2010-10']) &\
#           pd.isnull(df_lsa['enseigne_alt_2011-01'])])
#print df_lsa[~pd.isnull(df_lsa['enseigne_alt_2010-10']) &\
#             pd.isnull(df_lsa['enseigne_alt_2011-01'])][lsd0].to_string()

df_lsa.to_csv(os.path.join(path_built_csv,
                           'df_lsa_for_qlmc.csv'),
              index = False,
              encoding = 'UTF-8')
