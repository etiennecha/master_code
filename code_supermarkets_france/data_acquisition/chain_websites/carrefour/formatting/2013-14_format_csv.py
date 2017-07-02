#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *
import matplotlib.pyplot as plt

path_source = os.path.join(path_data,
                              u'data_supermarkets',
                              u'data_source',
                              u'data_drive',
                              u'data_carrefour')

path_source_csv = os.path.join(path_source,
                               u'data_csv')

path_built = os.path.join(path_data,
                          u'data_supermarkets',
                          u'data_built',
                          u'data_drive',
                          u'data_carrefour')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

ls_file_names = ['df_carrefour_voisins_20130418_20131128.csv',
                 'df_carrefour_voisins_20131129_20141205.csv',
                 'df_carrefour_voisins_2015_ref.csv']

ls_df_master = []
for file_name in ls_file_names:
  ls_df_master.append(pd.read_csv(os.path.join(path_source_csv,
                                               file_name),
                      encoding = 'utf-8'))

# parse_dates = ['date']))
# parse_dates a bit slow and not really necessary

# For now: only period with promo
df_master_2013 = ls_df_master[1]
df_master_2015 = ls_df_master[2]

# Assume "Prix Promo" is not legit promotion (pbm of data collect)
df_master_2013.loc[df_master_2013['promo'] == u'Prix Promo',
                   'promo'] = None

# ############################################
# DUPLICATES AND UNIQUE PRODUCTS IN 2013-2014
# ############################################

# Non identified: same title label within store/date/section/family

print u'\nNb rows 2013:', len(df_master_2013)

ls_prod_id_cols = ['date', 'section', 'family', 'title', 'label']
df_dup_2013 = df_master_2013[(df_master_2013.duplicated(ls_prod_id_cols)) |\
                             (df_master_2013.duplicated(ls_prod_id_cols,
                                                        take_last = True))].copy()

print 'Nb rows dup 2013:', len(df_dup_2013)
print 'Nb rows promo in dup 2013:', len(df_dup_2013[~df_dup_2013['promo'].isnull()])
print 'Overview promo dup 2013:'
df_dup_2013.sort(ls_prod_id_cols, inplace = True)
print df_dup_2013[~df_dup_2013['promo'].isnull()][0:20].to_string()

df_unique_2013 = df_master_2013[~((df_master_2013.duplicated(ls_prod_id_cols)) |\
                                  (df_master_2013.duplicated(ls_prod_id_cols,
                                                             take_last = True)))].copy()

# ############################################
# DUPLICATES AND UNIQUE PRODUCTS IN 2015
# ############################################

print u'\nNb rows 2015:', len(df_master_2015)

ls_prod_id_cols_2 = ['date', 'section', 'family', 'brand', 'title', 'label']

df_dup_2015 = df_master_2015[(df_master_2015.duplicated(ls_prod_id_cols_2)) |\
                             (df_master_2015.duplicated(ls_prod_id_cols_2,
                                                        take_last = True))].copy()

print 'Nb rows dup 2013 (brand included in identification):', len(df_dup_2015)

df_unique_2015 = df_master_2015[~((df_master_2015.duplicated(ls_prod_id_cols_2)) |\
                                  (df_master_2015.duplicated(ls_prod_id_cols_2,
                                                             take_last = True)))].copy()

# ########################################
# BRAND 1-TO-1 WITH TITLE, LABEL IN 2015?
# ########################################

# Fill no brand
# If same title and missing label for 2 prods: correctly identified as duplicates

df_master_2015.loc[df_master_2015['brand'].isnull(),
                   'brand'] = 'Sans marque'
df_uprod_2015 = df_master_2015[['brand', 'title', 'label']].drop_duplicates()
se_2015_bc = df_uprod_2015.groupby(['title', 'label']).agg(len)['brand']
df_uprod_2015.set_index(['title', 'label'], inplace = True)
df_uprod_2015['nb_brand'] = se_2015_bc
# only 42 with several brands
df_uprod_2015 = df_uprod_2015[df_uprod_2015['nb_brand'] == 1]
df_uprod_2015.reset_index(drop = False, inplace = True)

# ####################################
# IMPORT BRANDS FROM 2015 IN 2013-14
# ####################################

df_master_2013 = pd.merge(df_master_2013,
                          df_uprod_2015[['brand', 'title', 'label']],
                          on = ['title', 'label'],
                          how = 'left')

print u'\nPct brand found:', len(df_master_2013[~df_master_2013['brand'].isnull()]) /\
                               float(len(df_master_2013))

# todo: make sure 1-to-1 also in 2013?
# todo: use all days in 2015 to have more products
# todo: deal with pbm of non identified duplicates

df_dup_2013_2 = df_master_2013[(df_master_2013.duplicated(ls_prod_id_cols_2)) |\
                               (df_master_2013.duplicated(ls_prod_id_cols_2,
                                                          take_last = True))].copy()
# no chge vs before: normal

# ###########################
# CREATE NO AMBIGUITY VERSION
# ###########################

# assume if ambiguity: will be in all dpts
df_master_2013_nam = df_master_2013[~((df_master_2013.duplicated(ls_prod_id_cols)) |\
                                      (df_master_2013.duplicated(ls_prod_id_cols,
                                                                 take_last = True)))].copy()

# check if same (store, date, brand, title) can be listed with two different prices
ls_cols_check = ['date', 'brand', 'title', 'label', 'total_price']
df_check = df_master_2013_nam.drop_duplicates(ls_cols_check)
df_pbm = df_check[(df_check.duplicated(ls_cols_check[:-1])) |\
                  (df_check.duplicated(ls_cols_check[:-1],
                                       take_last = True))].copy()
df_pbm.sort(ls_cols_check[:-1], inplace = True)
print df_pbm[0:20].to_string()
# ok just 3 (title, label) to drop
for title, label in df_pbm[['title', 'label']].drop_duplicates().values:
  df_master_2013_nam =\
    df_master_2013_nam.loc[~((df_master_2013_nam['title'] == title) &\
                             (df_master_2013_nam['label'] == label)),]

# ##########################
# OUTPUT NO AMBIGUITY DATA
# ##########################

ls_cols_products = ['section', 'family', 'brand', 'title', 'label'] 
ls_cols_prices = ['brand', 'title', 'label', 'total_price', 'promo', 'unit', 'unit_price']

df_products_2013_nam =  df_master_2013_nam[ls_cols_products].drop_duplicates()
df_prices_2013_nam =  df_master_2013_nam[ls_cols_prices].drop_duplicates()

df_master_2013_nam.to_csv(os.path.join(path_built_csv,
                                       'df_master_voisins_2013-14_nam.csv'),
                          encoding = 'utf-8',
                          index = False)

df_products_2013_nam.to_csv(os.path.join(path_built_csv,
                                         'df_products_voisins_2013-14_nam.csv'),
                            encoding = 'utf-8',
                            index = False)

df_prices_2013_nam.to_csv(os.path.join(path_built_csv,
                                       'df_prices_voisins_2013-14_nam.csv'),
                          encoding = 'utf-8',
                          index = False)

# ###################
# OUTPUT ALL DATA
# ###################

df_products_2013 =  df_master_2013[ls_cols_products].drop_duplicates()
df_prices_2013 =  df_master_2013[ls_cols_prices].drop_duplicates()

df_master_2013.to_csv(os.path.join(path_built_csv,
                                 'df_master_voisins_2013-14.csv'),
                      encoding = 'utf-8',
                      index = False)

df_products_2013.to_csv(os.path.join(path_built_csv,
                                     'df_products_voisins_2013-14.csv'),
                        encoding = 'utf-8',
                        index = False)

df_prices_2013.to_csv(os.path.join(path_built_csv,
                                   'df_prices_voisins_2013-14.csv'),
                      encoding = 'utf-8',
                      index = False)
