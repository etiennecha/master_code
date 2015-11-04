#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *

path_built = os.path.join(path_data,
                           u'data_supermarkets',
                           u'data_built',
                           u'data_drive',
                           u'data_carrefour')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

ls_df_carrefour_2015 = ['df_master_carrefour_2015',
                        'df_prices_carrefour_2015',
                        'df_products_carrefour_2015']

dict_df = {}
for df_file_title in ls_df_carrefour_2015:
  dict_df[df_file_title] =\
    pd.read_csv(os.path.join(path_built_csv,
                             '{:s}.csv'.format(df_file_title)),
                dtype = {'date' : str},
                encoding = 'utf-8')

df_master   = dict_df['df_master_carrefour_2015']
df_prices   = dict_df['df_prices_carrefour_2015']
df_products = dict_df['df_products_carrefour_2015']

# ####################
# CHECK & FIX DATA
# ####################

# todo: move to data production

df_master = df_master[~df_master['date'].isin(['20150505', '20150506'])].copy()
df_prices = df_prices[~df_prices['date'].isin(['20150505', '20150506'])].copy()

# #############
# FIX dum_promo

# Create Boolean (todo: check distinction with loyalty)
for df_temp in [df_master, df_prices]:
  df_temp['dum_promo'] = False
  df_temp.loc[(~df_temp['promo'].isnull()) &\
              (~df_temp['promo'].str.contains(u'fidélité',
                                              case = False,
                                              na = False)),
              'dum_promo'] = True
  df_temp['dum_loyalty'] = False
  df_temp.loc[(~df_temp['promo'].isnull()) &\
              (df_temp['promo'].str.contains(u'fidélité',
                                             case = False,
                                             na = False)),
              'dum_loyalty'] = True

# #######################
# FIX PRODUCT DUPLICATES

# Need to uniquely identify products within date/store

# by title?
ls_dup_cols_0 = ['date', 'store', 'brand', 'title', 'label']
df_dup_0 = df_master[df_master.duplicated(ls_dup_cols_0, take_last = False) |\
                     df_master.duplicated(ls_dup_cols_0, take_last = True)].copy()
df_dup_0.sort(ls_dup_cols_0, inplace = True)

# by section/family/title?
ls_dup_cols_1 = ['date', 'store', 'section', 'family', 'brand', 'title', 'label']
df_dup_1 = df_master[df_master.duplicated(ls_dup_cols_1, take_last = False) |\
                     df_master.duplicated(ls_dup_cols_1, take_last = True)].copy()
df_dup_1.sort(ls_dup_cols_1, inplace = True)

print u'\nPct of rows involving duplicates (simple): {:.2f}'.format(\
        len(df_dup_1) / float(len(df_master)) * 100)

## drop simple duplicates (drop concerned products in all periods? stats des?)
#df_master = df_master[~(df_master.duplicated(ls_dup_cols_1, take_last = False) |\
#                        df_master.duplicated(ls_dup_cols_1, take_last = True))]
#
#df_prices = df_master[['store', 'date',
#                       'section', 'family', 'brand', 'title', 'label',
#                       'dum_promo', 'dum_loyalty', 'promo',
#                       'total_price', 'unit_price', 'unit']].copy()
#
#df_products = df_master[['section', 'family', 'title']].drop_duplicates()

# make sure same price/promo for all products with same title
ls_dup_cols_a = ['date', 'store', 'title', 'label']
df_dup_a = df_master[df_master.duplicated(ls_dup_cols_a, take_last = False) |\
                     df_master.duplicated(ls_dup_cols_a, take_last = True)].copy()

ls_dup_cols_b = ['date', 'store', 'brand', 'title', 'label',
                 'total_price', 'unit_price', 'promo']
df_dup_b = df_master[df_master.duplicated(ls_dup_cols_b, take_last = False) |\
                     df_master.duplicated(ls_dup_cols_b, take_last = True)].copy()

ls_ind_pbms = set(df_dup_a.index.tolist()).difference(set(df_dup_b.index.tolist()))
df_pbms = df_master.ix[ls_ind_pbms].copy()
df_pbms.sort(['date', 'store', 'brand', 'title', 'label'], inplace = True)

# best to drop all involved titles to avoid mismatching across periods
ls_title_pbms = df_pbms['title'].unique().tolist()

df_drop = df_master[df_master['title'].isin(ls_title_pbms)]
print u'\nPct of rows involving duplicates (extensive): {:.2f}'.format(\
        len(df_drop) / float(len(df_master)) * 100)

# drop duplicates (extensive) and get df_prices with unique products (by title)
# may bias data if stores don't use same categories (comprehensive though)
df_master = df_master[~df_master['title'].isin(ls_title_pbms)]

df_prices = df_master[['store', 'date',
                       'brand', 'title', 'label',
                       'dum_promo', 'dum_loyalty',
                       'promo', 'total_price', 'unit_price', 'unit']]\
              .drop_duplicates(['store', 'date', 'brand', 'title', 'label'])

df_products = df_master[['section', 'family', 'brand', 'title', 'label']].drop_duplicates()

# ###############
# STATS DES
# ###############

# #########
# PRODUCTS
# #########

# NB PRODUCTS BY DAY AND STORE
print u'\nNb products by day and store:'
df_nb_products = pd.pivot_table(df_prices,
                                columns = 'store',
                                index = 'date',
                                aggfunc = 'size')
print u'\n', df_nb_products.to_string()

# ################
# PROMO & LOYALTY
# ################

# todo: take into account availability?

# AGGREGATE

# pbm here: same products listed under several dpts

# NB PROMO BY DAY AND STORE
print u'\nNb promo by day and store:'
df_nb_promo = pd.pivot_table(df_prices[df_prices['dum_promo'] == True],
                             columns = 'store',
                             index = 'date',
                             aggfunc = 'size')
print u'\n', df_nb_promo.to_string()

# NB LOYALTY BY DAY AND STORE
print u'\nNb loyalty promo by day and store:'
df_nb_loyalty = pd.pivot_table(df_master[df_master['dum_loyalty'] == True],
                             columns = 'store',
                             index = 'date',
                             aggfunc = 'size')
print u'\n', df_nb_loyalty.to_string()

# PRODUCTS

# PROMO: NB OF STORES FOR EACH PROD
print u'\nNb stores by prod promo:'
df_prod_promo = pd.pivot_table(df_prices[df_prices['dum_promo'] == True],
                               columns = 'store',
                               index = ['date', 'brand', 'title', 'label'],
                               aggfunc = 'size')
df_prod_promo.fillna(0, inplace = True)
df_prod_promo['nb_stores'] =\
  df_prod_promo[df_prod_promo.columns].sum(1)
df_prod_promo.reset_index(drop = False, inplace = True)

df_prod_promo.sort(['nb_stores', 'date', 'brand', 'title', 'label'],
                   ascending = False,
                   inplace = True)

print df_prod_promo[0:20].to_string()
# print df_prod_promo[df_prod_promo['nb_stores'] == 10].to_string()
