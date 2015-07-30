#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *

path_auchan = os.path.join(path_data,
                           u'data_supermarkets',
                           u'data_drive',
                           u'data_auchan')

path_price_built_csv = os.path.join(path_auchan,
                                    u'data_built',
                                    u'data_csv_auchan')

ls_df_auchan_2015 = ['df_master_auchan_2015',
                     'df_prices_auchan_2015',
                     'df_products_auchan_2015']

dict_df = {}
for df_file_title in ls_df_auchan_2015:
  dict_df[df_file_title] =\
    pd.read_csv(os.path.join(path_price_built_csv,
                             '{:s}.csv'.format(df_file_title)),
                dtype = {'date' : str},
                encoding = 'utf-8')

df_master   = dict_df['df_master_auchan_2015']
df_prices   = dict_df['df_prices_auchan_2015']
df_products = dict_df['df_products_auchan_2015']

# #####
# TEMP
# ######

# todo: move to data production

# #############
# FIX dum_promo

# Create Boolean
for df_temp in [df_master, df_prices]:
  df_temp.loc[df_temp['dum_promo'] == 'yes', 'dum_promo'] = True
  df_temp.loc[df_temp['dum_promo'] == 'no', 'dum_promo'] = False

# Check if dum_promo trustworthy
print u'\nNb true dum_promo and empty promo_vignette: {:d}'.format(\
        len(df_master[(df_master['dum_promo']) &\
                      (pd.isnull(df_master['promo_vignette']))]))

print u'\nNb false dum_promo and non empty promo_vignette: {:d}'.format(\
        len(df_master[(~df_master['dum_promo']) &\
                      (~pd.isnull(df_master['promo_vignette']))]))

# Set dum_promo to True if promo_vignette not empty
df_master.loc[(~df_master['dum_promo']) &\
              (~pd.isnull(df_master['promo_vignette'])),
              'dum_promo'] = True

# Separate loyalty and promo (how?)
df_master['dum_loyalty'] = False
df_master.loc[(df_master['promo_vignette'] == 'op op-waaoh'),
              'dum_loyalty'] = True
df_master.loc[df_master['promo_vignette'] == 'op op-waaoh',
              'dum_promo'] = False

# TODO: separate loyalty and promo in vignette, promo, img

# #######################
# FIX PRODUCT DUPLICATES

# Need to uniquely identify products within date/store

# by title?
ls_dup_cols_0 = ['date', 'store', 'title']
df_dup_0 = df_master[df_master.duplicated(ls_dup_cols_0, take_last = False) |\
                     df_master.duplicated(ls_dup_cols_0, take_last = True)].copy()
df_dup_0.sort(ls_dup_cols_0, inplace = True)

# by department/sub_department/title?
ls_dup_cols_1 = ['date', 'store', 'department', 'sub_department', 'title']
df_dup_1 = df_master[df_master.duplicated(ls_dup_cols_1, take_last = False) |\
                     df_master.duplicated(ls_dup_cols_1, take_last = True)].copy()
df_dup_1.sort(ls_dup_cols_1, inplace = True)

print u'\nPct of rows involving duplicates: {:.2f}'.format(\
        len(df_dup_1) / float(len(df_master)) * 100)

# drop duplicates (drop concerned products in all periods? stats des?)
df_master = df_master[~(df_master.duplicated(ls_dup_cols_1, take_last = False) |\
                        df_master.duplicated(ls_dup_cols_1, take_last = True))]

df_prices = df_master[['store', 'date',
                       'department', 'sub_department', 'title',
                       'dum_available', 'dum_promo', 'promo_vignette', 'promo',
                       'total_price', 'unit_price', 'unit']].copy()

df_products = df_master[['department', 'sub_department', 'title']].drop_duplicates()


# #########
# OVERVIEW
# #########

# Exclude first day (more stores but once only)
df_master = df_master[df_master['date'] != '20150506']

# NB PRODUCTS BY DAY AND STORE
# can drop 20150506 which has more store (unique occurence)
df_nb_products = pd.pivot_table(df_master,
                                columns = 'store',
                                index = 'date',
                                aggfunc = 'size')
print u'\n', df_nb_products.to_string()

# ################
# PROMO & LOYALTY
# ################

# todo: take into account availability?

# ###############
# AGGREGATE

# pbm here: same products listed under several dpts

# NB PROMO BY DAY AND STORE
df_nb_promo = pd.pivot_table(df_master[df_master['dum_promo'] == True],
                             columns = 'store',
                             index = 'date',
                             aggfunc = 'size')
print u'\n', df_nb_promo.to_string()

# NB PROMO BY DAY AND STORE
df_nb_loyalty = pd.pivot_table(df_master[df_master['dum_loyalty'] == True],
                             columns = 'store',
                             index = 'date',
                             aggfunc = 'size')
print u'\n', df_nb_loyalty.to_string()

# ################
# PRODUCTS

# PROMO: NB OF STORES FOR EACH PROD
df_prod_promo = pd.pivot_table(df_master[df_master['dum_promo'] == True],
                               columns = 'store',
                               index = ['date', 'title'],
                               aggfunc = 'size')
df_prod_promo.fillna(0, inplace = True)
df_prod_promo['nb_stores'] =\
  df_prod_promo[df_master['store'].unique().tolist()].sum(1)
df_prod_promo.reset_index(drop = False, inplace = True)
