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
                          u'data_leclerc')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

ls_df_leclerc_2015 = ['df_master_leclerc_2015',
                      'df_prices_leclerc_2015',
                      'df_products_leclerc_2015']

ls_disp_prod = ['idProduit', 'title', 'label']

dict_df = {}
for df_file_title in ls_df_leclerc_2015:
  dict_df[df_file_title] =\
    pd.read_csv(os.path.join(path_built_csv,
                             '{:s}.csv'.format(df_file_title)),
                dtype = {'date' : str},
                encoding = 'utf-8')

df_master = dict_df['df_master_leclerc_2015']
df_prices = dict_df['df_prices_leclerc_2015']
df_products = dict_df['df_products_leclerc_2015']

# ######
# TEMP
# ######

print u'\nNb rows with nan a. everywhere {:d}'.format(\
       len(df_master[pd.isnull(df_master['label']) &\
                     pd.isnull(df_master['total_price'])]))

df_master = df_master[~(pd.isnull(df_master['label']) &\
                        pd.isnull(df_master['total_price']))]

ls_dup_cols_0 = ['store', 'date', 'idProduit']
df_dup_0 = df_master[df_master.duplicated(ls_dup_cols_0, take_last = False) |
                     df_master.duplicated(ls_dup_cols_0, take_last = True)].copy()
df_dup_0.sort(ls_dup_cols_0, inplace = True)

ls_dup_cols_1 = ['store', 'date', 'idProduit', 'unit_price']
df_dup_1 = df_master[df_master.duplicated(ls_dup_cols_1, take_last = False) |
                     df_master.duplicated(ls_dup_cols_1, take_last = True)].copy()

ls_dup_pbms = list(set(df_dup_0.index).difference(set(df_dup_1.index)))
ls_id_prod_pbms = df_master.ix[ls_dup_pbms]['idProduit'].unique().tolist()
df_pbms = df_master[df_master['idProduit'].isin(ls_id_prod_pbms)].copy()
df_pbms.sort(['store', 'date', 'idProduit'], inplace = True)
# print df_pbms[0:100].to_string() # many with nan almost everywhere in row

# Pbm : label is not one-to-one with idProduit
df_u_idP = df_master.drop_duplicates(['idProduit'])
ls_dup_idP = ['brand', 'title', 'label']
df_amb_prod = df_u_idP[df_u_idP.duplicated(ls_dup_idP, take_last = True) |\
                       df_u_idP.duplicated(ls_dup_idP, take_last = False)].copy()
df_amb_prod.sort(['brand', 'title', 'label'], inplace = True)
print df_amb_prod[0:10].to_string()

ls_drop_idP = df_amb_prod['idProduit'].unique().tolist()
df_master = df_master[~df_master['idProduit'].isin(ls_drop_idP)]

# lib_promo can be dropped (same as dum_promo)
df_prices = df_master[['date', 'store', 'idProduit',
                       'brand', 'title', 'label', 'stock',
                       'total_price', 'unit_price', 'unit',
                       'promo', 'promo_per_unit', # those are prices
                       'dum_promo', 'lib_0', 'loyalty']]\
              .drop_duplicates(['store', 'date', 'idProduit'])

df_products = df_master[['section', 'family',
                         'brand', 'title', 'label',
                         'idProduit',
                         'idRayon', 'idFamille', 'idSousFamille']]\
                .drop_duplicates()

ls_stores = df_master['store'].unique().tolist()

# ########################
# GENERAL OVERVIEW: STATIC
# ########################

# NB PRODUCTS

print u'\nNb products by nb of stores over time:'
df_nb_prod = pd.pivot_table(df_prices,
                            columns = 'store',
                            index = 'date',
                            aggfunc = 'size')
df_nb_prod.fillna(0, inplace = True)
df_nb_prod.index = pd.to_datetime(df_nb_prod.index, format = '%Y%m%d')
print df_nb_prod.to_string()

# NB PROMO

print u'\nNb promo by nb of stores over time:'
df_nb_promo = pd.pivot_table(df_prices[df_prices['dum_promo'] == True],
                          columns = 'store',
                          index = 'date',
                          aggfunc = 'size')
df_nb_promo.fillna(0, inplace = True)
df_nb_promo.index = pd.to_datetime(df_nb_promo.index, format = '%Y%m%d')
print df_nb_promo.to_string()

# NB LOYALTY PRODUCTS

print u'\nNb loyalty promo by store over time:'
df_nb_loyalty = pd.pivot_table(df_prices[~df_prices['loyalty'].isnull()],
                               columns = 'store',
                               index = 'date',
                               aggfunc = 'size')
df_nb_loyalty.fillna(0, inplace = True)
df_nb_loyalty.index = pd.to_datetime(df_nb_loyalty.index, format = '%Y%m%d')
print df_nb_loyalty.to_string()

# ###################
# PRODUCT COMPARISON
# ###################

# for each prod: check if appears at least once in each store?
df_store_products = df_prices[['store', 'idProduit']].drop_duplicates()
se_nb_prod = df_store_products.groupby('idProduit').agg('size')

df_products.set_index('idProduit', inplace = True)
df_products['nb_stores'] = se_nb_prod

# Stores carrying unique products?
print df_store_products['store']\
        [df_prices['idProduit'].isin(se_nb_prod[se_nb_prod == 1].index)].value_counts()

# ###################
# PRICE COMPARISON
# ###################

df_day_prices =\
  df_prices[df_prices['date'] == '20150507'].pivot_table(index = 'idProduit',
                                                         columns = 'store',
                                                         values = 'total_price')

# stats des: ref price etc.
se_day_count = df_day_prices.count(1)
se_day_min, se_day_max = df_day_prices.min(1), df_day_prices.max(1)
df_su_day_prices = pd.concat([se_day_count, se_day_min, se_day_max],
                             axis = 1,
                             keys = ['count', 'min', 'max'])
df_su_day_prices['spread'] = df_su_day_prices['max'] - df_su_day_prices['min']

# todo: take nb of products into account
print len(df_su_day_prices[df_su_day_prices['spread'] < 1e-5])

print len(df_su_day_prices[(df_su_day_prices['count'] >= 4)])

print len(df_su_day_prices[(df_su_day_prices['count'] >= 4) &\
                           (df_su_day_prices['spread'] < 1e-5)])

# ###################
# PROMO COMPARISON
# ###################

df_prod_promo = pd.pivot_table(df_prices[df_prices['dum_promo'] == True],
                               columns = 'store',
                               index = ['date', 'idProduit', 'title', 'label'],
                               aggfunc = 'size')
df_prod_promo.fillna(0, inplace = True)
df_prod_promo['nb_stores'] = df_prod_promo[ls_stores].sum(1)
df_prod_promo.reset_index(drop = False, inplace = True)

print u'\nTop promo (by nb of stores) on first day:'
df_prod_promo.sort(['date', 'nb_stores'], ascending = False, inplace = True)
print df_prod_promo[df_prod_promo['date'] == '20150507']\
        [ls_disp_prod + ['nb_stores']][0:10].to_string()

print u'\nNb stores concerned by each product in promo per day'
df_promo_nb_stores = pd.pivot_table(df_prod_promo,
                                    columns = 'nb_stores',
                                    index = 'date',
                                    aggfunc = 'size')
df_promo_nb_stores.fillna(0, inplace = True)
print df_promo_nb_stores.to_string()

# Add display of nb of promo by store (both at the same time)
# 

# ###################
# LOYALTY COMPARISON
# ###################

df_prod_loyalty = pd.pivot_table(df_prices[~df_prices['loyalty'].isnull()],
                                 columns = 'store',
                                 index = ['date', 'idProduit', 'title', 'label'],
                                 aggfunc = 'size')
df_prod_loyalty.fillna(0, inplace = True)
df_prod_loyalty['nb_stores'] = df_prod_loyalty[ls_stores].sum(1)
df_prod_loyalty.reset_index(drop = False, inplace = True)

print u'\nTop loyalty promo (by nb of stores) on first day:'
df_prod_loyalty.sort(['date', 'nb_stores'], ascending = False, inplace = True)
print df_prod_loyalty[df_prod_loyalty['date'] == '20150507']\
        [ls_disp_prod + ['nb_stores']][0:10].to_string()

print u'\nNb stores concerned by each product in loyalty per day'
df_loyalty_nb_stores = pd.pivot_table(df_prod_loyalty,
                                      columns = 'nb_stores',
                                      index = 'date',
                                      aggfunc = 'size')
df_loyalty_nb_stores.fillna(0, inplace = True)
print df_loyalty_nb_stores.to_string()
