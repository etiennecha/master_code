#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import *
import os, sys
import httplib
import urllib, urllib2
from bs4 import BeautifulSoup
import re
import json
import pandas as pd
from functions_generic_qlmc import *
import numpy as np

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_built = os.path.join(path_data,
                          'data_supermarkets',
                          'data_built',
                          'data_qlmc_2015')

path_built_csv = os.path.join(path_built,
                              'data_csv_201503')

path_built_lsa = os.path.join(path_data,
                              'data_supermarkets',
                              'data_built',
                              'data_lsa')

path_built_csv_lsa = os.path.join(path_built_lsa, 'data_csv')
path_built_json_lsa = os.path.join(path_built_lsa, 'data_json')
path_built_comp_csv_lsa = os.path.join(path_built_csv_lsa, '201407_competition')
path_built_comp_json_lsa = os.path.join(path_built_json_lsa, '201407_competition')

# ##############
# LOAD DATA
# ##############

# QLMC DATA

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str},
                        encoding = 'utf-8')

df_comp = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc_competitors.csv'),
                      encoding = 'utf-8')

# LSA DATA

df_lsa = pd.read_csv(os.path.join(path_built_csv_lsa,
                                  'df_lsa_active.csv'),
                     dtype = {u'id_lsa' : str,
                              u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'UTF-8')
# drop hard discount
df_lsa = df_lsa[df_lsa['type_alt'].isin(['H', 'S'])]

dict_ls_comp = dec_json(os.path.join(path_built_comp_json_lsa,
                                     'dict_ls_comp_hs.json'))

# ###################
# OVERVIEW DISTANCES
# ###################

ls_disp_dist = ['lec_id', 'comp_id',
                'lec_lat', 'lec_lng',
                'comp_lat', 'comp_lng',
                'dist']

# Overview of pair distance distribution
print u'\nOverview pair dist (km):'
print df_comp['dist'].describe()

# Overview of leclercs' competitors
print u'\nOverview market dist (km) around leclerc stores:'
df_leclerc_comp = df_comp[['lec_name', 'dist']]\
                    .groupby(['lec_name']).agg([len,
                                                min,
                                                max,
                                                np.mean,
                                                np.median])['dist']
ls_pctiles = [0.1, 0.25, 0.5, 0.75, 0.9]
print df_leclerc_comp.describe(percentiles = ls_pctiles)

## Latex output
#pd.set_option('float_format', '{:,.1f}'.format)
#print df_leclerc_comp.describe(percentiles = ls_pctiles).to_latex()
## print len(df_leclerc_comp[df_leclerc_comp['max'] > 30])
## print len(df_leclerc_comp[df_leclerc_comp['mmin'] > 30])
## print df_comp[df_comp['lec_name'] == u'CENTRE E.LECLERC LOUDÉAC'].to_string()

# ############################
# ANALYSE COMPETITORS VS. LSA
# ############################

# todo: count all within 30 km, more than 1000m2, and discard differentiated

## check enseigne to discard
#print df_lsa['enseigne'][df_lsa['surface'] >= 1000].value_counts().to_string()
ls_discard_enseigne = [u'ALDI',
                       u'LEADER PRICE',
                       u'DIA %',
                       u'FRANPRIX',
                       u'LIDL',
                       u'NETTO',
                       u'NORMA',
                       u'LE MUTANT', # Discount/small offer of national brands
                       u'G 20',
                       u'SIMPLY GALERIES GOURMANDES',
                       u"LE MARCHE D'A COTE",
                       u"EASY MARCHE",
                       u"LAFAYETTE GOURMET",
                       u"PRIXBAS",
                       u"MONOP STORE",
                       u"MAXI",
                       u"O' MARCHE FRAIS U",
                       u"GALERIES GOURMANDES",
                       u"COCCINELLE EXPRESS",
                       u"MONOP'",
                       u"SPAR",
                       u"EUROPRIX"]

df_lsa = df_lsa[~df_lsa['enseigne'].isin(ls_discard_enseigne)]

df_lsa.loc[df_lsa['enseigne'] == 'MARKET',
           'enseigne'] = 'CARREFOUR MARKET'

ls_enseignes_compa = ['INTERMARCHE SUPER',
                      'SUPER U',
                      'CARREFOUR',
                      'CARREFOUR MARKET',
                      'AUCHAN',
                      'GEANT CASINO',
                      'CASINO',
                      'CORA',
                      'HYPER U',
                      'SIMPLY MARKET',
                      'HYPER U']

df_stores.set_index('store_id', inplace = True)
df_lsa.set_index('id_lsa', inplace = True)

dict_lec_comp = {}
for row_i, row in df_comp.iterrows():
  lec_lsa_id = df_stores.ix[row['lec_id']]['id_lsa']
  comp_lsa_id = df_stores.ix[row['comp_id']]['id_lsa']
  if not pd.isnull(lec_lsa_id) and not pd.isnull(comp_lsa_id):
    dict_lec_comp.setdefault(lec_lsa_id, []).append((comp_lsa_id, row['dist']))

# Example:
lsd0 = ['enseigne', 'adresse1', 'ville', 'surface']

lec_lsa_id_ex = dict_lec_comp.keys()[0]

print u'\nCompetitors picked by Leclerc:'
print df_lsa.ix[[x[0] for x in dict_lec_comp[lec_lsa_id_ex]]][lsd0].to_string()

print u'\nAll competitors (25 km) LSA:'
print df_lsa.ix[[x[0] for x in dict_ls_comp[lec_lsa_id_ex]]][lsd0].to_string()

# Loop: for each leclerc:
# - look if missing store of 1000m2 or more within radius by leclerc
# - if missing: look if there is already a store of enseigne (/group) brand closer

dict_lec_comp_2 = {}
dict_dict_missing = {'missing_comp' : {},
                     'missing_store' : {},
                     'missing_store_larger' : {}}
for lec_lsa_id, ls_lec_comp in dict_lec_comp.items():
  ls_lec_comp = sorted(ls_lec_comp, key = lambda x: x[1])
  qlmc_max_dist = ls_lec_comp[-1][1]
  lec_surface = df_lsa.ix[lec_lsa_id]['surface']
  
  ls_qlmc_comp_lsa_ids = [x[0] for x in ls_lec_comp]
  ls_qlmc_temp = [(x, df_lsa.ix[x]['enseigne'], df_lsa.ix[x]['groupe'], df_lsa.ix[x]['surface'])\
                    for x in ls_qlmc_comp_lsa_ids]
  
  ls_lsa_comp_lsa_ids = [x[0] for x in dict_ls_comp[lec_lsa_id]]
  ls_lsa_comp_lsa_ids_dist = [x[0] for x in dict_ls_comp[lec_lsa_id]\
                               if x[1] <= qlmc_max_dist]
  ls_lsa_temp = [(x, df_lsa.ix[x]['enseigne'], df_lsa.ix[x]['groupe'], df_lsa.ix[x]['surface'])\
                   for x in ls_lsa_comp_lsa_ids_dist if x in df_lsa.index]
  # need to add check that stores still here when restricting df_lsa
  dict_lec_comp_2[lec_lsa_id] = ls_lsa_temp
  # loop with groupe and sizer criteria
  ls_missing, ls_missing_2, ls_missing_2_larger = [], [], []
  ls_enseignes, ls_groupes = [], []
  for id_lsa, enseigne, groupe, surface in ls_lsa_temp:
    if id_lsa in ls_qlmc_comp_lsa_ids:
      # could add size criterion by enseigne/groupe
      ls_enseignes.append(enseigne)
      ls_groupes.append(groupe)
    elif (groupe not in ls_groupes):
      ls_missing.append(id_lsa)
      ls_groupes.append(groupe)
      if id_lsa not in df_stores['id_lsa'].values:
        ls_missing_2.append(id_lsa)
        if surface >= lec_surface * 0.75:
          ls_missing_2_larger.append(id_lsa)
  dict_dict_missing['missing_comp'][lec_lsa_id] = ls_missing
  dict_dict_missing['missing_store'][lec_lsa_id] = ls_missing_2
  dict_dict_missing['missing_store_larger'][lec_lsa_id] = ls_missing_2_larger

# Could check later if store of same enseigne/groupe further but bigger
print u'\nCheck nb Leclerc store with missing stores:'

for x in ['missing_comp', 'missing_store', 'missing_store_larger']:
  ls_concerned = [lec_lsa_id for lec_lsa_id, ls_missing\
                     in dict_dict_missing[x].items()\
                       if ls_missing]
  print u'Nb lec w/ {:s}: {:d}'.format(x, len(ls_concerned))

# Example
lec_lsa_id_ex = ls_concerned[0]

for lec_lsa_id_ex in ls_concerned[0:50]:
  print u'\n' + '-'*20
  print df_lsa.ix[lec_lsa_id_ex][lsd0 + ['c_postal']].T.to_string()

  print u'\nCompetitors picked by Leclerc:'
  print df_lsa.ix[[x[0] for x in dict_lec_comp[lec_lsa_id_ex]]][lsd0].to_string()
  
  print u'\nLarge(r) competitors missing?'
  print df_lsa.ix[dict_dict_missing['missing_store'][lec_lsa_id_ex]][lsd0].to_string()

  print u'\nLarge(r) competitors missing and not in data?'
  print df_lsa.ix[dict_dict_missing['missing_store_larger'][lec_lsa_id_ex]][lsd0].to_string()
