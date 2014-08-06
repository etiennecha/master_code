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

ls_disp_1 = [u'Ident', u'Enseigne', u'ADRESSE1', u'Ville', 'Code INSEE',
             u'DATE ouv', u'DATE ferm', u'DATE réouv']

print u'\nRecently opened stores'
print df_lsa[ls_disp_1][df_lsa['DATE ouv'] > '2014-01-01'].to_string()

ls_disp_2 = [u'Ident', u'Enseigne', u'ADRESSE1', u'Ville', 'Code INSEE',
             u'DATE ouv', u'DATE chg enseigne', 'Ex enseigne']

print u'\nStores with enseigne change within studied period'
print df_lsa[ls_disp_2][('2009-09' > df_lsa[u'DATE ouv']) &\
                        ('2009-09' < df_lsa[u'DATE chg enseigne'])].to_string()

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
  df_lsa[qlmc_date][df_lsa[u'DATE ouv'] > qlmc_date] = None
  # Closed and not reopened
  df_lsa[qlmc_date][(df_lsa[u'DATE ferm'] < qlmc_date) &
                    (pd.isnull(df_lsa[u'DATE réouv']))] = None
  # Write previous enseigne if changed since then (check consistency if missing data)
  df_lsa[qlmc_date][(qlmc_date > df_lsa[u'DATE ouv']) &\
                    (qlmc_date < df_lsa[u'DATE chg enseigne'])] = df_lsa['Ex enseigne']

# FORMAT DATE AND OUTPUT TO EXCEL FILE
for field in [u'DATE ouv', u'DATE ferm', u'DATE réouv',
              u'DATE chg enseigne', u'DATE chgt surf']:
  df_lsa[field][df_lsa[field] < '1900'] = pd.tslib.NaT
  df_lsa[field] = df_lsa[field].apply(lambda x: x.date()\
                                        if type(x) is pd.tslib.Timestamp\
                                        else pd.tslib.NaT)

writer = pd.ExcelWriter(os.path.join(path_dir_built_csv, 'LSA_enriched.xlsx'))
df_lsa.to_excel(writer, index = False)
writer.close()

# TODO: get ARDT for big cities thx to gps

## qlmc_data = pd.HDFStore(os.path.join(path_dir_built_hdf5, 'qlmc_data.h5'))

# Load insee files
df_insee_areas = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_insee_areas.csv'))
df_au_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_au_agg_final.csv'))
df_uu_agg = pd.read_csv(os.path.join(path_dir_insee_extracts, 'df_uu_agg_final.csv'))

# Add insee area codes to df_fra_stores
df_lsa = pd.merge(df_insee_areas,
                  df_lsa,
                  left_on = 'CODGEO',
                  right_on = 'Code INSEE',
                  how = 'right')

# NB STORES BY AU IN A GIVEN PERIOD
df_au_agg.index = df_au_agg['AU2010']
ls_disp_au = ['AU2010', 'LIBAU2010', 'P10_POP', 'SUPERF', 'POPDENSITY10', 'QUAR2UC10',
              'nb_stores', 'pop_by_store']

se_au_vc = df_lsa['AU2010'][~pd.isnull(df_lsa['2010-03'])].value_counts()
df_au_agg['nb_stores'] = se_au_vc
df_au_agg['pop_by_store'] = df_au_agg['P10_POP'] / df_au_agg['nb_stores'] 

print df_au_agg[ls_disp_au][0:10].to_string()


# Nb stores vs. population (# stores by head decreasing in population density?)
# exclude paris (+ todo: check with exclusion of au internationales)
plt.scatter(df_au_agg['P10_POP'][df_au_agg['AU2010']!='001'],
            df_au_agg['nb_stores'][df_au_agg['AU2010']!='001'])
plt.show()


## Store density vs. pop density (# stores by head decreasing in population density?)
#plt.scatter(df_au_agg['POPDENSITY10'][df_au_agg['AU2010']!='001'],
#            df_au_agg['pop_by_store'][df_au_agg['AU2010']!='001'])
#plt.show()

# todo: take changes into account
df_au_agg['surf_vente_cum'] = df_lsa[['AU2010', 'Surf Vente']].groupby('AU2010').sum()
df_au_agg['pop_by_surf_vente'] = df_au_agg['P10_POP'] / df_au_agg['surf_vente_cum']
print df_au_agg[ls_disp_au + ['surf_vente_cum', 'pop_by_surf_vente']][0:10].to_string()


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
