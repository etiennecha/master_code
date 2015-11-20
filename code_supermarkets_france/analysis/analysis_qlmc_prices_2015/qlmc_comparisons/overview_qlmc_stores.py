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

pd.set_option('float_format', '{:,.3f}'.format)

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

df_lsa = df_lsa[df_lsa['type_alt'].isin(['H', 'S'])]

# Create enseigne_qlmc (national chains) in df_lsa

ls_keep_enseigne_lsa_to_qlmc = ['AUCHAN',
                                'CARREFOUR',
                                'CARREFOUR MARKET',
                                'CASINO',
                                'CORA',
                                'SIMPLY MARKET']

ls_ls_enseigne_lsa_to_qlmc = [[['CENTRE E.LECLERC'], 'LECLERC'],
                              [['GEANT CASINO'], 'GEANT'],
                              [['HYPER CASINO'], 'CASINO'],
                              [['INTERMARCHE SUPER',
                                'INTERMARCHE HYPER',
                                'INTERMARCHE CONTACT'], 'INTERMARCHE'],
                              [['HYPER U',
                                'SUPER U',
                                'U EXPRESS'], 'SYSTEME U'],
                              [['MARKET'], 'CARREFOUR MARKET'],
                              [["LES HALLES D'AUCHAN"], 'AUCHAN']]

df_lsa['enseigne_qlmc'] = None
df_lsa.loc[df_lsa['enseigne'].isin(ls_keep_enseigne_lsa_to_qlmc),
           'enseigne_qlmc'] = df_lsa['enseigne']
for ls_enseigne_lsa_to_qlmc in ls_ls_enseigne_lsa_to_qlmc:
  df_lsa.loc[df_lsa['enseigne'].isin(ls_enseigne_lsa_to_qlmc[0]),
             'enseigne_qlmc'] = ls_enseigne_lsa_to_qlmc[1]

## Check numbers vs. numbers in Methodology to ensure consistency
#print u'\nNb stores of QLMC national chains:'
#print df_lsa['enseigne_qlmc'].value_counts().sort_index()

# ######################################
# LECLERC AND COMP LISTED VS. COLLECTED
# ######################################

## Check that df_stores contains all stores in df_comp (i.e. from website): ok
#ls_stores_in_comp = list(df_comp['lec_id'].unique()) +\
#                      list(df_comp['comp_id'].unique())
ls_got_leclerc_ids = list(df_prices[df_prices['store_chain'] == 'LECLERC']['store_id'].unique())
ls_got_comp_ids = list(df_prices[df_prices['store_chain'] != 'LECLERC']['store_id'].unique())
ls_got_stores = ls_got_leclerc_ids + ls_got_comp_ids

ls_leclerc_ids = list(df_stores[df_stores['store_chain'] == 'LECLERC']['store_id'])
ls_comp_ids = list(df_stores[df_stores['store_chain'] != 'LECLERC']['store_id'])
ls_stores = ls_leclerc_ids + ls_comp_ids

# Check if missing comp_ids are competitors of missing leclerc_ids
ls_missing_leclerc_ids = list(set(ls_leclerc_ids).difference(set(ls_got_leclerc_ids)))
ls_missing_comp_ids = list(set(ls_comp_ids).difference(set(ls_got_comp_ids)))
# 51: missing

ls_missing_lec_comp_ids = df_comp[df_comp['lec_id'].isin(ls_missing_leclerc_ids)]['comp_id'].unique()
# 52: some of them I still have because of other stores

ls_really_comp = df_comp[df_comp['lec_id'].isin(ls_got_leclerc_ids)]['comp_id'].unique()
# 1,811 competitors for the 561 Leclerc for which I have price data
ls_really_missing = list(set(ls_missing_comp_ids).difference(set(ls_missing_lec_comp_ids)))
# 36 out of 1,811: not in price data

# ############################
# REPRESENTATION OF EACH CHAIN
# ############################

chain_field = 'enseigne_qlmc'

## add enseigne_qlmc to df_stores (todo: check correspondence w/ store_chain)
## looks ok
#for x in df_stores['enseigne_qlmc'].unique():
#  print u'\n', x
#  print df_stores[df_stores['enseigne_qlmc'] == x]['store_chain'].value_counts()
#print df_stores[df_stores['enseigne_qlmc'].isnull()].to_string()

df_lsa.set_index('id_lsa', inplace = True)
df_stores.set_index('id_lsa', inplace = True)
df_stores = pd.merge(df_stores,
                     df_lsa[['enseigne', 'enseigne_qlmc', 'groupe', 'surface']],
                     left_index = True,
                     right_index = True,
                     how = 'left')

se_qlmc_chains = df_stores['enseigne_qlmc'].value_counts()
# Exclude small nbs which correspond to small stores or small chains
se_qlmc_chains = se_qlmc_chains[se_qlmc_chains > 12]
se_lsa_chains = df_lsa[df_lsa['enseigne_qlmc'].isin(se_qlmc_chains.index)]\
                      ['enseigne_qlmc'].value_counts()
se_coverage_chains = se_qlmc_chains / se_lsa_chains * 100

print u'\nRepresentation of chains (source: LSA):'
df_rep_chains = pd.concat([se_lsa_chains,
                           se_qlmc_chains,
                           se_coverage_chains],
                          axis = 1,
                          keys = ['Nb stores LSA',
                                  'Nb stores QLMC',
                                  'Coverage (%)'])
print df_rep_chains.to_string(float_format = format_float_int)

# print df_rep_chains.to_latex(float_format = format_float_int)

# #############################
# REPRESENTATION OF EACH REGION
# #############################

# todo: df w/ pop, nb stores, total surf, pop by store, pop by surface

# nb stores
se_qlmc_reg_nb = df_lsa[df_lsa.index.isin(df_stores.index)]['region'].value_counts()
se_lsa_reg_nb = df_lsa['region'].value_counts()
se_coverage_reg_nb = se_qlmc_reg_nb / se_lsa_reg_nb * 100
# surface
se_qlmc_reg_surface = df_lsa[df_lsa.index.isin(df_stores.index)][['region', 'surface']]\
                .groupby('region').agg(sum)['surface']
se_lsa_reg_surface = df_lsa[['region', 'surface']].groupby('region').agg(sum)['surface']
se_coverage_reg_surface = se_qlmc_reg_surface / se_lsa_reg_surface * 100

print u'\nRepresentation by region:'
df_rep_reg = pd.concat([se_qlmc_reg_nb,
                        se_lsa_reg_nb,
                        se_coverage_reg_nb,
                        se_qlmc_reg_surface / 1000.0,
                        se_lsa_reg_surface / 1000.0,
                        se_coverage_reg_surface],
                       axis = 1,
                       keys = ['Nb stores LSA',
                               'Nb stores QLMC',
                               'Nb coverage (%)',
                               'Cum surface LSA (th m2)',
                               'Cum surface QLMC (th m2)',
                               'Cum surf coverage (%)'])
print df_rep_reg.to_string(float_format = format_float_int)

# could refine by adding: 
# Rural / City center / Suburb / Isolated city

# ##########################
# LECLERC NOT IN QLMC
# ##########################

# LECLERC EXPRESS not covered on website (generally smaller)

lsd_lsa = ['enseigne', 'adresse1', 'ville', 'c_postal',
           'surface', 'date_ouv', 'date_fer', 'date_reouv', 'ex_enseigne']

print u'\nLeclerc not covered in QLMC:'
print df_lsa[(df_lsa['enseigne'] == 'CENTRE E.LECLERC') &\
             (~df_lsa.index.isin(df_stores.index))][lsd_lsa].to_string()

# Some are not present in my data but are now listed on website
# What about then? check in methodo's list of stores

# #############################
# OVERVIEW STORES NOT COLLECTED
# #############################

ls_not_collected_ids = list(set(df_stores['store_id'])\
                          .difference(set(df_prices['store_id'].unique())))
print u'\nNb stores on website but not collected:', len(ls_not_collected_ids)

print u'\nNb stores on website but not collected by chain:'
print df_stores[df_stores['store_id'].isin(ls_not_collected_ids)]\
               ['enseigne'].value_counts()

print u'\nOverview of Leclerc on website but not collected:'
print df_stores[(df_stores['store_id'].isin(ls_not_collected_ids)) &\
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

print u'\nOverview stores with few obs (<= 400):'
print df_stores[(df_stores['nb_obs'] < 400) &\
                (df_stores['nb_obs'] != 0)]\
               [['enseigne_qlmc', 'nb_obs']].to_string()

print u'\nOverview nb obs (products) by store / chain:'
chain_field = 'enseigne_qlmc'
ls_chains = list(df_stores[chain_field][~df_stores[chain_field].isnull()].unique())
ls_se_chain = []
for chain in ls_chains:
  se_chain_desc = df_stores[df_stores[chain_field] == chain]['nb_obs'].describe()
  ls_se_chain.append(se_chain_desc)
df_chain_prods = pd.concat(ls_se_chain,
                           axis = 1,
                           keys = ls_chains)
df_chain_prods = df_chain_prods.T
df_chain_prods.sort('count', ascending = False, inplace = True)
print df_chain_prods.fillna(0).astype(int).to_string()

# #########################
# NB PRODUCTS BY QLMC COMPA
# #########################

# Create qlmc_chain in df_comp
df_comp['qlmc_comp_chain'] = df_comp['comp_chain']
for ls_enseigne_lsa_to_qlmc in ls_ls_enseigne_lsa_to_qlmc:
  df_comp.loc[df_comp['comp_chain'].isin(ls_enseigne_lsa_to_qlmc[0]),
              'qlmc_comp_chain'] = ls_enseigne_lsa_to_qlmc[1]

# todo: standardize chains

# size and drive may explain variations in product count
# todo (when building): add lsa_id, size and drive (for both, also distance?)

print u'\nOverview nb obs (products) by qlmc comparison / chain:'
chain_field = 'qlmc_comp_chain'
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

print u'\nOverview comp hyper u w/ few products:'
print df_comp[(df_comp['comp_chain'] == 'HYPER U') &\
              (df_comp['qlmc_nb_obs'] <= 1000)][lsdcomp].to_string()

# High diff w/ Carrefour
print df_comp[(df_comp['comp_chain'] == 'CARREFOUR') &\
              (df_comp['qlmc_pct_compa'] >= 30)][lsdcomp].to_string()

df_comp[(df_comp['comp_chain'] == 'GEANT CASINO')].plot(kind = 'scatter',
                                                        x = 'qlmc_nb_obs',
                                                        y = 'qlmc_pct_compa')
plt.show()
