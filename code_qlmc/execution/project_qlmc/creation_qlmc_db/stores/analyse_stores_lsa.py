#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import *
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
df_lsa_all = pd.read_excel(os.path.join(path_dir_source_lsa,
                                               '2014-07-30-export_CNRS_no1900.xlsx'),
                           sheetname = 'Feuil1')

# Exclude drive and hard discount for matching
df_lsa = df_lsa_all[(df_lsa_all['Type'] == 'H') |\
                    (df_lsa_all['Type'] == 'S') |\
                    (df_lsa_all['Type'] == 'MP')].copy()

# Convert dates to pandas friendly format
# Can not use np.datetime64() as missing value
for field in [u'DATE ouv', u'DATE ferm', u'DATE réouv',
              u'DATE chg enseigne', u'DATE chgt surf']:
  df_lsa[field] = df_lsa[field].apply(lambda x: x.replace(hour=0, minute=0,
                                                          second=0, microsecond=0)\
                                        if (type(x) is datetime.datetime) or\
                                           (type(x) is pd.Timestamp)
                                        else pd.tslib.NaT)

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
                       (df_lsa[u'DATE ouv'] < '2012-06')]
print df_lsa_opened[ls_disp_1].to_string()

# CLOSED (AND NOT REOPENED) STORES WITHIN QLMC DATA PERIOD
print u'\nStores closed over qlmc period'
df_lsa_closed = df_lsa[(df_lsa[u'DATE ferm'] > '2007-05') &\
                       (df_lsa[u'DATE ferm'] < '2012-06') &\
                       (pd.isnull(df_lsa[u'DATE réouv']))]
print df_lsa_closed[ls_disp_1].to_string()

# STORES WITH SIGNIFICANT BRAND CHANGES WITHIN QLMC DATA PERIOD
ls_disp_2 = [u'Ident', u'Enseigne', 'Ex enseigne',
             u'ADRESSE1', u'Ville', 'Code INSEE',
             u'DATE ouv', u'DATE chg enseigne']

print u'\nStores with "significant" brand changes over qlmc period'
#print df_lsa[ls_disp_2][(df_lsa['DATE chg enseigne'] > '2007-05') &\
#                        (df_lsa['DATE chg enseigne'] < '2012-06')].to_string()
df_lsa_chge = df_lsa[(df_lsa['DATE chg enseigne'] > '2007-05') &\
                     (df_lsa['DATE chg enseigne'] < '2012-06')]
df_lsa_chge = df_lsa_chge[~((df_lsa_chge['Ex enseigne'].str.contains('CHAMPION') |\
                             df_lsa_chge['Ex enseigne'].str.contains('SHOPI')) &\
                            (df_lsa_chge['Enseigne'].str.contains('CARREFOUR')))]
df_lsa_chge = df_lsa_chge[~((df_lsa_chge['Ex enseigne'].str.contains('INTERMARCHE') |\
                             df_lsa_chge['Ex enseigne'].str.contains('ECOMARCHE')) &\
                            (df_lsa_chge['Enseigne'].str.contains('INTERMARCHE')))]
df_lsa_chge = df_lsa_chge[~((df_lsa_chge['Ex enseigne'].str.contains('GEANT') |\
                             df_lsa_chge['Ex enseigne'].str.contains('CASINO')) &\
                            (df_lsa_chge['Enseigne'].str.contains('CASINO')))]
# not full: check with regular expression
df_lsa_chge = df_lsa_chge[~((df_lsa_chge['Ex enseigne'].str.contains('MARCHE U') |\
                             df_lsa_chge['Ex enseigne'].str.contains('SUPER U')) &\
                            (df_lsa_chge['Enseigne'].str.contains('U EXPRESS')))]
print df_lsa_chge[ls_disp_2].to_string()

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

## GENERAT COLUMNS BY PERIOD WITH CURRENT ENSEIGNE WHEN STORE IS ACTIVE
#ls_qlmc_dates = ['2007-05',
#                 '2007-08',
#                 '2008-01',
#                 '2008-04',
#                 '2009-03',
#                 '2009-09',
#                 '2010-03',
#                 '2010-10',
#                 '2011-01',
#                 '2011-04',
#                 '2011-10',
#                 '2012-01',
#                 '2012-06']
#
#for qlmc_date in ls_qlmc_dates:
#  df_lsa[qlmc_date] = df_lsa['Enseigne']
#  # Not opened yet (left untouched if DATE ouv is unknown)
#  df_lsa[qlmc_date][df_lsa[u'DATE ouv'] > qlmc_date] = None
#  # Closed and not reopened
#  df_lsa[qlmc_date][(df_lsa[u'DATE ferm'] < qlmc_date) &
#                    (pd.isnull(df_lsa[u'DATE réouv']))] = None
#  # Write previous enseigne if changed since then (check consistency if missing data)
#  df_lsa[qlmc_date][(qlmc_date > df_lsa[u'DATE ouv']) &\
#                    (qlmc_date < df_lsa[u'DATE chg enseigne'])] = df_lsa['Ex enseigne']
#
### FORMAT DATE AND OUTPUT TO EXCEL FILE
##for field in [u'DATE ouv', u'DATE ferm', u'DATE réouv',
##              u'DATE chg enseigne', u'DATE chgt surf']:
##  df_lsa[field][df_lsa[field] < '1900'] = pd.tslib.NaT
##  df_lsa[field] = df_lsa[field].apply(lambda x: x.date()\
##                                        if type(x) is pd.tslib.Timestamp\
##                                        else pd.tslib.NaT)
##
##writer = pd.ExcelWriter(os.path.join(path_dir_built_csv, 'LSA_enriched.xlsx'))
##df_lsa.to_excel(writer, index = False)
##writer.close()

# TODO: get ARDT for big cities thx to gps

## qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))

## INTEGRATE INSEE DATA FOR ANALYSIS
#df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_insee_areas.csv'))
#df_au_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_au_agg_final.csv'))
#df_uu_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_uu_agg_final.csv'))
#
## Add insee area codes to df_fra_stores
#df_lsa = pd.merge(df_insee_areas,
#                  df_lsa,
#                  left_on = 'CODGEO',
#                  right_on = 'Code INSEE',
#                  how = 'right')
#
## NB STORES BY AU IN A GIVEN PERIOD
#df_au_agg.index = df_au_agg['AU2010']
#ls_disp_au = ['AU2010', 'LIBAU2010', 'P10_POP', 'SUPERF', 'POPDENSITY10', 'QUAR2UC10',
#              'nb_stores', 'pop_by_store']
#
#se_au_vc = df_lsa['AU2010'][~pd.isnull(df_lsa['2010-03'])].value_counts()
#df_au_agg['nb_stores'] = se_au_vc
#df_au_agg['pop_by_store'] = df_au_agg['P10_POP'] / df_au_agg['nb_stores'] 
#
#print df_au_agg[ls_disp_au][0:10].to_string()
#
#
## Nb stores vs. population (# stores by head decreasing in population density?)
## exclude paris (+ todo: check with exclusion of au internationales)
#plt.scatter(df_au_agg['P10_POP'][df_au_agg['AU2010']!='001'],
#            df_au_agg['nb_stores'][df_au_agg['AU2010']!='001'])
#plt.show()
#
### Store density vs. pop density (# stores by head decreasing in population density?)
##plt.scatter(df_au_agg['POPDENSITY10'][df_au_agg['AU2010']!='001'],
##            df_au_agg['pop_by_store'][df_au_agg['AU2010']!='001'])
##plt.show()
#
## STORE SURFACE BY AU (todo: take period into account)
#df_au_agg['surf_vente_cum'] = df_lsa[['AU2010', 'Surf Vente']].groupby('AU2010').sum()
#df_au_agg['pop_by_surf_vente'] = df_au_agg['P10_POP'] / df_au_agg['surf_vente_cum']
#print df_au_agg[ls_disp_au + ['surf_vente_cum', 'pop_by_surf_vente']][0:10].to_string()


## NB STORES BY UU
#df_uu_agg.index = df_uu_agg['UU2010']
#ls_disp_uu = ['UU2010', 'LIBUU2010', 'P10_POP', 'SUPERF', 'POPDENSITY10', 'QUAR2UC10',
#              'nb_stores', 'pop_by_store']
#
#se_au_vc = df_fra_stores['UU2010'].value_counts()
#df_uu_agg['nb_stores'] = se_au_vc
#df_uu_agg['pop_by_store'] = df_uu_agg['P10_POP'] / df_uu_agg['nb_stores']
#
#df_uu_agg.sort('P10_POP', ascending=False, inplace=True)
#print df_uu_agg[ls_disp_uu][df_uu_agg['nb_stores'] >= 1][0:10].to_string()
#
### Nb stores vs. population (# stores by head decreasing in population density?)
### exclude paris (+ todo: check with exclusion of au internationales)
##plt.scatter(df_uu_agg['P10_POP'][df_uu_agg['AU2010']!='001'],
##            df_uu_agg['nb_stores'][df_uu_agg['AU2010']!='001'])
##plt.show()
##
### Store density vs. pop density (# stores by head decreasing in population density?)
##plt.scatter(df_uu_agg['POPDENSITY10'][df_uu_agg['AU2010']!='001'],
##            df_uu_agg['pop_by_store'][df_uu_agg['AU2010']!='001'])
##plt.show()
