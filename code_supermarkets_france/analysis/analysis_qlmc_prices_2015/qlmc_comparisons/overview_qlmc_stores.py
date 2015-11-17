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
import matplotlib.pyplot as plt

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

# #########
# LOAD DATA
# #########

# QLMC DATA

df_stores = pd.read_csv(os.path.join(path_built_csv,
                                     'df_stores_final.csv'),
                        dtype = {'id_lsa' : str},
                        encoding = 'utf-8')

df_comp = pd.read_csv(os.path.join(path_built_csv,
                                   'df_qlmc_competitors.csv'),
                      encoding = 'utf-8')

# Fix gps problems (move later?)
ls_fix_gps = [['intermarche-super-le-portel',       (50.7093, 1.5789)], # too far
              ['casino-l-ile-rousse',               (42.6327, 8.9383)],
              ['centre-e-leclerc-lassigny',         (49.5898, 2.8531)],
              ['carrefour-market-chateau-gontier',  (47.8236, -0.7064)],
              ['casino-san-nicolao',                (42.3742, 9.5299)], # too close
              ['centre-e-leclerc-san-giuliano',     (42.2625, 9.5480)]]

for store_id, (store_lat, store_lng) in ls_fix_gps:
  df_stores.loc[df_stores['store_id'] == store_id,
                ['store_lat', 'store_lng']] = [store_lat, store_lng]

df_prices = pd.read_csv(os.path.join(path_built_csv,
                                     'df_prices.csv'),
                        encoding = 'utf-8')

df_prices = df_prices[~((df_prices['family'] == u'Traiteur') &\
                        (df_prices['product'] == u"DANIEL DESSAINT CRÊPES " +\
                                                 u"MOELLEUSE SUCRÉES X8 400G " +\
                                                 u"DANIEL DESSAINT"))]

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

## Check record dates (move)
#df_prices['date'] = pd.to_datetime(df_prices['date'], format = '%d/%m/%Y')
#print df_prices['date'].describe()
## From 2015-02-05 to 2015-03-17
#print len(df_prices[df_prices['date'] < '2015-02-17']) / float(len(df_prices))
## less than 2% obs lost to have only 1 month
#print len(df_prices[df_prices['date'] < '2015-03-01']) / float(len(df_prices))
## only 17% records before 2015-03-01

# ############################
# REPRESENTATION OF EACH CHAIN
# ############################

df_lsa.set_index('id_lsa', inplace = True)
df_stores.set_index('id_lsa', inplace = True)
df_stores = pd.merge(df_stores,
                     df_lsa[['enseigne', 'enseigne_alt', 'groupe', 'surface']],
                     left_index = True,
                     right_index = True,
                     how = 'left')

se_qlmc_chains = df_stores['enseigne'].value_counts()
# Exclude small nbs which correspond to small stores or small chains
se_qlmc_chains = se_qlmc_chains[se_qlmc_chains > 12]
se_lsa_chains = df_lsa[df_lsa['enseigne'].isin(se_qlmc_chains.index)]\
                      ['enseigne'].value_counts()

print u'\nRepresentation of chains (source: LSA):'
print se_qlmc_chains / se_lsa_chains * 100

# Check Leclerc not included
lsd_lsa = ['enseigne', 'adresse1', 'ville', 'c_postal',
           'surface', 'date_ouv', 'date_fer', 'date_reouv', 'ex_enseigne']

print u'\nLeclerc not covered in QLMC:'
print df_lsa[(df_lsa['enseigne'] == 'CENTRE E.LECLERC') &\
             (~df_lsa.index.isin(df_stores.index))][lsd_lsa].to_string()

# todo: check if not in my data or not on website at the time...
# not very important anyway

# #############################
# REPRESENTATION OF EACH REGION
# #############################

# todo: df w/ pop, nb stores, total surf, pop by store, pop by surface

# nb stores
se_qlmc_reg = df_lsa[df_lsa.index.isin(df_stores.index)]['region'].value_counts()
se_lsa_reg = df_lsa['region'].value_counts()
print u'\nRepresentation by region (nb stores):'
print se_qlmc_reg / se_lsa_reg * 100

# surface
se_qlmc_reg = df_lsa[df_lsa.index.isin(df_stores.index)][['region', 'surface']]\
                .groupby('region').agg(sum)
se_lsa_reg = df_lsa[['region', 'surface']].groupby('region').agg(sum)
print u'\nRepresentation by region (surface):'
print se_qlmc_reg / se_lsa_reg * 100

# could refine by adding: 
# Rural / City center / Suburb / Isolated city

# #######################
# OVERVIEW MISSING STORES
# #######################

ls_missing_stores = list(set(df_stores['store_id'])\
                          .difference(set(df_prices['store_id'].unique())))
print u'\nNb missing stores:', len(ls_missing_stores)

print u'\nNb missing stores by chain:'
print df_stores[df_stores['store_id'].isin(ls_missing_stores)]\
               ['enseigne'].value_counts()

print u'\nOverview of missing Leclerc:'
print df_stores[(df_stores['store_id'].isin(ls_missing_stores)) &\
                (df_stores['enseigne'] == 'CENTRE E.LECLERC')]\
                [['store_id', 'store_name']].to_string()

# ##########################
# NB PRODUCTS BY STORE
# ##########################

df_stores.reset_index(drop = False, inplace = True)
df_stores.set_index('store_id', inplace = True)
df_stores['nb_obs'] = df_prices['store_id'].value_counts()
#df_stores.loc[df_stores['nb_obs'].isnull(),
#              'nb_obs'] = 0

print u'\nOverview nb obs (products) by store:'
print df_stores['nb_obs'][df_stores['nb_obs'] != 0].describe()

print u'\nOverview stores with few obs:'
print df_stores[(df_stores['nb_obs'] < 400) &\
                (df_stores['nb_obs'] != 0)]\
               [['store_chain', 'nb_obs']].to_string()

print u'\nOverview nb obs (products) by store / chain:'
chain_field = 'enseigne'
ls_chains = list(df_stores[chain_field].unique())
ls_se_chain = []
for chain in ls_chains:
  se_chain_desc = df_stores[df_stores[chain_field] == chain]['nb_obs'].describe()
  # hide small chains
  if se_chain_desc.ix['count'] >= 5:
    ls_se_chain.append(se_chain_desc)
df_chain_prods = pd.concat(ls_se_chain,
                           axis = 1,
                           keys = ls_chains)

#df_chain_prods.drop([u"LES HALLES D'AUCHAN",
#                     u"MIGROS",
#                     u"RECORD"],
#                    axis = 1,
#                    inplace = True)

df_chain_prods = df_chain_prods.T
df_chain_prods.sort('count', ascending = False, inplace = True)
print df_chain_prods.fillna(0).astype(int).to_string()

# #########################
# NB PRODUCTS BY QLMC COMPA
# #########################

# size and drive may explain variations in product count
# todo (when building): add lsa_id, size and drive (for both, also distance?)

print u'\nOverview nb obs (products) by qlmc comparison / chain:'
chain_field = 'comp_chain'
ls_chains = list(df_comp[chain_field].unique())
ls_se_chain = []
for chain in ls_chains:
  se_chain_desc = df_comp[df_comp[chain_field] == chain]['qlmc_nb_obs'].describe()
  # hide small chains
  if se_chain_desc.ix['count'] >= 5:
    ls_se_chain.append(se_chain_desc)
df_compa_prods = pd.concat(ls_se_chain,
                           axis = 1,
                           keys = ls_chains)

df_compa_prods = df_compa_prods.T
df_compa_prods.sort('count', ascending = False, inplace = True)
print df_compa_prods.fillna(0).astype(int).to_string()

# check few obs store within large nb obs store
lsdcomp = ['lec_name', 'comp_name', 'qlmc_nb_obs', 'qlmc_pct_compa', 'qlmc_winner']
print df_comp[(df_comp['comp_chain'] == 'HYPER U') &\
              (df_comp['qlmc_nb_obs'] <= 1000)][lsdcomp].to_string()

df_comp[(df_comp['comp_chain'] == 'GEANT CASINO')].plot(kind = 'scatter',
                                                        x = 'qlmc_nb_obs',
                                                        y = 'qlmc_pct_compa')
plt.show()
