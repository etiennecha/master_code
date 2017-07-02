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
import pandas as pd
from mpl_toolkits.basemap import Basemap
import pprint

path_source = os.path.join(path_data,
                           'data_supermarkets',
                           'data_source',
                           'data_qlmc_2007-12')

path_source_csv = os.path.join(path_source,
                               'data_csv')

path_built_lsa_csv = os.path.join(path_data,
                                  'data_supermarkets',
                                  'data_built',
                                  'data_lsa',
                                  'data_csv')

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

# #############
# LOAD DATA
# #############

# LOAD QLMC STORES

df_stores = pd.read_csv(os.path.join(path_source_csv,
                                     'df_stores_w_municipality_and_lsa_id.csv'),
                        dtype = {'c_insee' : str},
                        encoding = 'utf-8')

df_stores.drop(['id_fra_stores',
                'id_fra_stores_2',
                'street_fra_stores'],
                axis = 1,
                inplace = True)

# INTERMARCHE          745 : keep => rgp in df_fra_stores
# AUCHAN               705 : keep => same in df_fra_stores
# SUPER U              610 : keep or SYSTEME U (HYPER U + SUPER U?) in df_fra_stores
# GEANT CASINO         581 : keep or CASINO
# LECLERC              540 : keep
# CARREFOUR MARKET     498 : keep or CARREFOUR
# CARREFOUR            472 : keep
# CORA                 416 : keep
# CHAMPION             341 : CARREFOUR MARKET OR CARREFOUR
# CENTRE E. LECLERC    144 : LECLERC
# HYPER U               64 : keep or SYSTEME U
# SYSTEME U             50 : keep
# E.LECLERC             49 : LECLERC
# GEANT                 49 : GEANT CASINO or?
# HYPER CHAMPION        20 : CARREFOUR AND CARREFOUR MARKET
# GEANT DISCOUNT         9 : GEANT CASINO or ?
# LECLERC EXPRESS        4 : LECLERC (check what it means)
# U EXPRESS              3 : keep or SYSTEME U?
# MARCHE U               2 : keep or SYSTEME U?
# CENTRE LECLERC         1 : LECLERC
# CARREFOUR CITY         1 : keep or CARREFOUR CITY?

# LOAD DF LSA

df_lsa = pd.read_csv(os.path.join(path_built_lsa_csv,
                                  'df_lsa_for_qlmc.csv'),
                     dtype = {u'c_insee' : str,
                              u'c_insee_ardt' : str,
                              u'c_postal' : str,
                              u'c_siren' : str,
                              u'c_nic' : str,
                              u'c_siret' : str},
                     parse_dates = [u'date_ouv', u'date_fer', u'date_reouv',
                                    u'date_chg_enseigne', u'date_chg_surface'],
                     encoding = 'utf-8')

# ####################
# FORMAT STORE CHAINS
# ####################


# todo: 
# - harmonize store_chain (vs enseigne / enseigne_alt from lsa?)
# - check several name for same store (id_lsa) within periods
# - check several names for same store (id_lsa) across periods

# DISPLAY ORIGINAL STORE CHAINS
print u'\nStore chains (qlmc classification) by period:'
df_chains = pd.pivot_table(data = df_stores[['period', 'store_chain', 'store']],
                           index = 'store_chain',
                           columns = 'period',
                           aggfunc = len,
                           fill_value = 0).astype(int)['store']
print df_chains.to_string()

# ADD HARMONIZED STORE CHAINS

#ls_sc_drop = ['CARREFOUR CITY',
#              'CARREFOUR CONTACT',
#              'CARREFOUR PLANET',
#              'GEANT DISCOUNT',
#              'HYPER CHAMPION',
#              'INTERMARCHE HYPER',
#              'LECLERC EXPRESS',
#              'MARCHE U',
#              'U EXPRESS']
#
#df_stores = df_qlmc[~df_stores['store_chain'].isin(ls_sc_drop)]

df_stores['store_chain_alt'] = df_stores['store_chain']

ls_sc_replace = [('CENTRE E. LECLERC', 'LECLERC'),
                 ('CENTRE LECLERC', 'LECLERC'),
                 ('E. LECLERC', 'LECLERC'),
                 ('E.LECLERC', 'LECLERC'),
                 ('GEANT', 'GEANT CASINO'),
                 ('SYSTEME U', 'SUPER U'), # default but improved below
                 ('INTERMARCHE HYPER', 'INTERMARCHE'),
                 ('INTERMARCHE SUPER', 'INTERMARCHE')]

for sc_old, sc_new in ls_sc_replace:
  df_stores.loc[df_stores['store_chain'] == sc_old,
              'store_chain_alt'] = sc_new

# SYSTEME U (todo: add check w/ lsa)
df_systemeu =  df_stores[(df_stores['period'] == 0) &\
                         (df_stores['store_chain'] == 'SYSTEME U')]
ls_hyperu_lsa_ids = []
for id_lsa in df_systemeu['id_lsa'].unique():
  if 'HYPER U' in df_stores[df_stores['id_lsa'] == id_lsa]['store_chain'].values:
    ls_hyperu_lsa_ids.append(id_lsa)
for id_lsa in ls_hyperu_lsa_ids:
  df_stores.loc[df_stores['id_lsa'] == id_lsa,
                'store_chain_alt'] = 'HYPER U'

df_stores['store_alt'] = df_stores['store_chain_alt'] + u' ' +\
                           df_stores['store_municipality']

# DISPLAY HARMONIZED STORE CHAINS
print u'\nStore chains (qlmc improved) by period:'
df_chains = pd.pivot_table(data = df_stores[['period', 'store_chain_alt', 'store']],
                           index = 'store_chain_alt',
                           columns = 'period',
                           aggfunc = len,
                           fill_value = 0).astype(int)['store']
print df_chains.to_string()
# todo: SYSTEME U: see if some HYPER U for consistency

# ###############################
# WITHIN PERIOD id_lsa DUPLICATES
# ###############################

print u'\nInspect within periods id_lsa duplicates:'
se_stores_dup = pd.pivot_table(data = df_stores[['period', 'id_lsa']],
                               index = ['period', 'id_lsa'],
                               aggfunc = len,
                               fill_value = 0).astype(int)
print se_stores_dup[se_stores_dup != 1]

for Period, id_lsa in se_stores_dup[se_stores_dup != 1].index:
  print df_stores[(df_stores['period'] == Period) &\
                  (df_stores['id_lsa'] == id_lsa)].to_string()

# ################################################
# ONE id_lsa & MULTIPLE store_alt
# ################################################

print u'\nInspect across periods store duplicates:'
se_stores_dup_ap =\
  pd.pivot_table(data = df_stores[['id_lsa', 'store_alt']].drop_duplicates(),
                 index = ['id_lsa'],
                 aggfunc = len,
                 fill_value = 0).astype(int)['store_alt']
print len(se_stores_dup_ap[se_stores_dup_ap > 1])

ind_dup_ap = se_stores_dup_ap[se_stores_dup_ap > 1].index

# a lot of stores are referred to in several ways
# try to keep longest "municipality" (often includes more details)
# beware: could imply havin instances w/ on store for several id_lsa?

dict_store_mun = {}
for row_i, row in df_stores.iterrows():
  mun = dict_store_mun.get(row['id_lsa'])
  if (not mun) or len(row['store_municipality']) > len(mun):
    dict_store_mun[row['id_lsa']] = row['store_municipality']

df_stores.loc[~df_stores['id_lsa'].isnull(),
              'store_alt'] =\
  df_stores.loc[~df_stores['id_lsa'].isnull()].\
    apply(lambda x : x['store_chain_alt'] +\
                     u' ' +\
                     dict_store_mun[x['id_lsa']],
          axis = 1)

# ###########################################
# ONE id_lsa & MULTIPLE store_alt - 
# ###########################################

# should occur only due to changes in chain names? (CHAMPION mostly)
# a priori: ok, no remedy

print u'\nInspect one id_lsa vs. multiple store_alt:'

se_stores_dup_ap =\
  pd.pivot_table(data = df_stores[['id_lsa', 'store_alt']].drop_duplicates(),
                 index = ['id_lsa'],
                 aggfunc = len,
                 fill_value = 0).astype(int)['store_alt']
print len(se_stores_dup_ap[se_stores_dup_ap > 1])
# all should be due to change in chains (essentially carrefour market)
ind_dups = se_stores_dup_ap[se_stores_dup_ap > 1].index
print df_stores[df_stores['id_lsa'].isin(ind_dups)]['store_chain'].value_counts()

# ###############################
# ONE store_alt & MULTIPLE id_lsa
# ###############################

# remedy: make name more precise

print u'\nInspect one store_alt vs. multiple id_lsa:'

dict_store_id_lsa = {}
for row_i, row in df_stores.iterrows():
  if not pd.isnull(row['id_lsa']):
    dict_store_id_lsa.setdefault(row['store_alt'], []).append(row['id_lsa'])


lsd_lsa = ['id_lsa',
           'adresse1',
           'c_postal',
           'ville',
           'enseigne',
           'ex_enseigne',
           'date_ouv',
           'date_fer',
           'date_reouv',
           'surface']

# print df_lsa[df_lsa['id_lsa'].isin([164405, 3523])][lsd_lsa].T.to_string()

for k,v in dict_store_id_lsa.items():
  if len(list(set(v))) != 1:
    print '\n' + '-'*20
    print df_stores[df_stores['store_alt'] == k].to_string()
    print df_lsa[df_lsa['id_lsa'].isin(v)][lsd_lsa].T.to_string()

# 14 have multiple id_lsas

# finally: check one store_alt w/ one id_lsa and unmatched store
set_pbms = set()
for row_i, row in df_stores.iterrows():
  # may need to chge if id_lsa read as string
  if not pd.isnull(row['id_lsa']):
    if np.isnan(np.min(df_stores[df_stores['store_alt'] == row['store_alt']]['id_lsa'].values)):
      set_pbms.add(row['store_alt'])
ls_pbms = list(set_pbms)

# LECLERC ST MAUR: maybe the same, another has opened... might have been called "CAP SUD"
# LECLERC CONFLANS STE HONORINE: ambiguity w/ a small Leclerc... can assumed it away?
# LECLERC WATTRELOS: ambiguity w/ a small Leclerc... can assumed it away?
# CHAMPION ST GERMAIN DU PUY: also CARREFOUR MARKET in this period so maybe the CONTACT

#print df_stores[df_stores['store_municipality'] == u'ST GERMAIN DU PUY'].to_string()
#print df_lsa[lsd_lsa][df_lsa['c_insee'] == '18213'].to_string()

# SUPER U LAVARDAC: probably the new one: check w/ date (2008-04-01)
# SUPER U LYON: should get rid of first matching... (store_chain SYSTEME U)

# df_stores[df_stores['store_alt'] == 'SUPER U LYON', 'id_lsa'] = np.nan

# SUPER U PASSY: closed right after probably but supposed to be closed already

# df_stores[df_stores['store_alt'] == 'SUPER U PASSY', 'id_lsa'] = 11480

# LECLERC LEVALLOIS PERRET: real ambiguity (prices? drop if no id_lsa)
# INTERMARCHE BERGERAC: real ambiguity (prices? drop if no id_lsa)
