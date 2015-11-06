#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
import json
from datetime import date, timedelta
import datetime
import numpy as np
import pprint
import itertools
import pandas as pd
import matplotlib.pyplot as plt

path_built = os.path.join(path_data,
                          u'data_supermarkets',
                          u'data_built',
                          u'data_drive',
                          u'data_auchan')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

# #########
# LOAD DATA
# #########

dict_df_velizy = {}
for x in ['master', 'prices', 'products']:
  ls_parse_dates = []
  if x in ['master', 'prices']:
    ls_parse_dates = ['date']
  dict_df_velizy['df_{:s}'.format(x)] =\
      pd.read_csv(os.path.join(path_built_csv,
                               'df_{:s}_auchan_velizy_2012-13.csv'.format(x)),
                  parse_dates = ls_parse_dates,
                  dtype = {'available' : str,
                           'pictos' : str,
                           'promo' : str,
                           'promo_vignette' : str},
                  encoding = 'utf-8')

df_master_velizy = dict_df_velizy['df_master']
df_prices_velizy = dict_df_velizy['df_prices']
df_products_velizy = dict_df_velizy['df_products']

dict_df_2013 = {}
for x in ['master', 'prices', 'products']:
  ls_parse_dates = []
  if x in ['master', 'prices']:
    ls_parse_dates = ['date']
  dict_df_2013['df_{:s}'.format(x)] =\
      pd.read_csv(os.path.join(path_built_csv,
                               'df_{:s}_auchan_2013.csv'.format(x)),
                  parse_dates = ls_parse_dates,
                  dtype = {'available' : str,
                           'pictos' : str,
                           'promo' : str,
                           'promo_vignette' : str},
                  encoding = 'utf-8')

df_master = dict_df_2013['df_master']
df_prices = dict_df_2013['df_prices']
df_products = dict_df_2013['df_products']

# ##################
# FIX PROMO/LOYALTY
# ##################

for x in ['promo_vignette', 'promo']:
  print u'Nb non null', x, ':', len(df_master[~df_master[x].isnull()])

# Issue:
# before 2013-05-13: promo content is in 'promo' & 'promo_vignette' (got all info?)
# after 2013-05-13 (and break): promo content in 'promo_vignette' and not ok

# todo: before 2013-05-13
# check if flag promo 1-to-1 w/ promo
# stats des on promo types etc.

# todo: after 2013-05-13
# flag promo for promo without numerical content?
# check if credible given nb...
# a priori cannot distinguish between loyalty or not (?)
# broad stats des?

# Check: no promo_vignette after 2013-05-13: ok
print df_master[(~df_master['promo_vignette'].isnull()) &\
                (df_master['date'] > '2013-05-13')][0:10].to_string()

# Check: diff between promo, promo_vignette and flag == promo
len(df_master[((~df_master['promo_vignette'].isnull()) |\
               (~df_master['promo'].isnull())) &\
              (df_master['date'] <= '2013-05-13')])
len(df_master[(df_master['flag'] == 'promo') &\
              (df_master['date'] <= '2013-05-13')])
# about 1000 diff...
print df_master[(df_master['flag'] == 'promo') &\
                (df_master['date'] <= '2013-05-13') &\
                (df_master['promo_vignette'].isnull()) &\
                (df_master['promo'].isnull())][0:10].to_string()
# unsure about those
print df_master[(df_master['store'] == 'velizy') &\
                (df_master['title'] == u'Auchan crêpes jambon fromage x2 -200g')].to_string()
# some appear to be specific promotion products
# for some... no evidence (e.g. Ricard pastis 45° -1l)
# can do conservative guess without them

# for now: drop amb periods
df_master = df_master.loc[df_master['date'] <= '2013-05-13',].copy()

# unsure about this... approx for now
for df_temp in [df_master, df_prices]:
  df_temp['dum_promo'] = False
  df_temp.loc[(~df_temp['promo_vignette'].isnull()),
              'dum_promo'] = True
  df_temp['dum_loyalty'] = False
  df_temp.loc[(~df_temp['promo'].isnull()),
              'dum_loyalty'] = True
  df_temp.rename(columns = {'promo' : 'loyalty',
                            'promo_vignette' : 'promo'},
                 inplace = True)

# #########################################
# FIX DUPLICATES AND UNIDENTIFIED PRODUCTS
# #########################################

# DUP ON ('brand', 'title', 'label')
ls_dup_cols_0 = ['date', 'store', 'title']
df_dup_0 = df_master[df_master.duplicated(ls_dup_cols_0, take_last = False) |\
                     df_master.duplicated(ls_dup_cols_0, take_last = True)].copy()
df_dup_0.sort(ls_dup_cols_0, inplace = True)

ls_dup_cols_1 = ['date', 'store', 'section', 'family', 'title']
df_dup_1 = df_master[df_master.duplicated(ls_dup_cols_1, take_last = False) |\
                     df_master.duplicated(ls_dup_cols_1, take_last = True)].copy()
df_dup_1.sort(ls_dup_cols_1, inplace = True)

ls_dup_cols_2 = ['date', 'store', 'section', 'family',
                 'title', 'total_price', 'unit_price', 'promo']
df_dup_2 = df_master[df_master.duplicated(ls_dup_cols_2, take_last = False) |\
                     df_master.duplicated(ls_dup_cols_2, take_last = True)].copy()

# Solve issue:
# - drop dup_2 (last): same products listed several times
# - redo dup_1: those are problematic

print u'\nNb rows w/ simple duplicates (all fields):', len(df_master)
df_master.drop_duplicates(ls_dup_cols_2, inplace = True)

print u'\nNb rows w/o simple duplicates (all fields):', len(df_master)

# DUP ON ('section', 'family', 'brand', 'title', 'label')
df_dup_pbm = df_master[df_master.duplicated(ls_dup_cols_1, take_last = False) |\
                       df_master.duplicated(ls_dup_cols_1, take_last = True)].copy()
df_dup_pbm.sort(ls_dup_cols_1)
print df_dup_pbm[0:20].to_string()

# Be conservative: drop these store/prods in all periods

df_drop = df_dup_pbm[['store', 'title']].drop_duplicates()

df_drop['drop'] = 1
df_master = pd.merge(df_master,
                     df_drop,
                     on = ['store', 'title'],
                     how = 'left')

df_dropped = df_master.loc[(df_master['drop'] == 1),].copy()
df_master = df_master.loc[(df_master['drop'] != 1),]
df_master.drop(['drop'],
               axis = 1,
               inplace = True)

print u'\nNb rows w/o pbmatic duplicates:', len(df_master)

# ################
# STORE PRICE VARS
# ################

# todo: move to building phase
df_master.rename(columns = {'title': 'product'},
                 inplace = True)
df_master_s = df_master

# Build df store products (idProduit not unique: several families)
lsd_prod = ['product', 'family', 'section']
df_products_s = df_master_s[lsd_prod].drop_duplicates()

# Build df with product prices in columns
df_prices_s = df_master_s.drop_duplicates(['date', 'product'])
df_prices_sc = df_prices_s.pivot(index = 'date',
                                 columns = 'product',
                                 values = 'total_price')
df_prices_sc.index= pd.to_datetime(df_prices_sc.index,
                                   format = '%Y%m%d')
index_dr = pd.date_range(df_prices_sc.index[0],
                         df_prices_sc.index[-1],
                         freq = 'D')
df_prices_sc = df_prices_sc.reindex(index_dr)

df_prices_scf = df_prices_sc.fillna(method = 'bfill',
                                    axis = 'index')
df_prices_scfd = df_prices_scf - df_prices_scf.shift(1)
se_scfd_nb_chges = df_prices_scfd.apply(lambda x: (x.abs()>0).sum(),
                                        axis = 0)
# Count promo days by product in df_master_s
se_prod_promo_days = df_prices_s[df_prices_s['dum_promo']]\
                       ['product'].value_counts()

# Caution: one line per ('section', 'family', 'product'):
df_products_s.set_index('product', inplace = True)
df_products_s['nb_chges'] = se_scfd_nb_chges
df_products_s['nb_promo_days'] = se_prod_promo_days

df_products_s.loc[df_products_s['nb_promo_days'].isnull(),
                  'nb_promo_days'] = 0

print u'\nOverview top nb price chges:'
df_products_s.sort(['nb_chges'],
                   ascending = False,
                   inplace = True)
print df_products_s[0:20].to_string()

print u'\nOverview top nb promo days:'
df_products_s.sort(['nb_promo_days'],
                   ascending = False,
                   inplace = True)
print df_products_s[0:20].to_string()

# Plot product price series
ax = df_prices_scf[u"Président coulommiers 350g"].plot()
ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
plt.show()

# ###################
# NB PROD / NB PROMO
# ###################

se_nb_prod = df_prices_s.groupby('date').agg('count')['dum_promo']
se_nb_promo = df_prices_s[df_prices_s['dum_promo'] == True]\
                         .groupby('date').agg('count')['dum_promo']
se_nb_loyalty = df_prices_s[df_prices_s['dum_loyalty'] == True]\
                         .groupby('date').agg('count')['dum_promo']
df_su_s = pd.concat([se_nb_prod, se_nb_promo, se_nb_loyalty],
                    axis = 1,
                    keys = ['nb_prod', 'nb_promo'])
# Promo nb drops and loylaty increases... check if pbm?
