#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *

path_leclerc = os.path.join(path_data,
                            u'data_supermarkets',
                            u'data_drive',
                            u'data_leclerc')

path_price_built_csv = os.path.join(path_leclerc,
                                    u'data_built',
                                    u'data_csv_leclerc')

ls_df_leclerc_2015 = ['df_master_leclerc_2015',
                      'df_prices_leclerc_2015',
                      'df_products_leclerc_2015']

ls_disp_prod = ['idProduit', 'title', 'label']

dict_df = {}
for df_file_title in ls_df_leclerc_2015:
  dict_df[df_file_title] =\
    pd.read_csv(os.path.join(path_price_built_csv,
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
df_amb_prod = df_u_idP[df_u_idP.duplicated(['brand', 'title', 'label'], take_last = True) |\
                       df_u_idP.duplicated(['brand', 'title', 'label'], take_last = False)].copy()
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

df_products = df_master[['department', 'sub_department',
                         'brand', 'title', 'label',
                         'idProduit',
                         'idRayon', 'idFamille', 'idSousFamille']]\
                .drop_duplicates()

ls_stores = df_master['store'].unique().tolist()

# ##############################
# PROMO AND STOCK (STORE LEVEL)
# ##############################

print u'\nPrint 10 promo rows:'
print df_prices[df_prices['dum_promo'] == True][0:10].to_string()

# During promo: 
# - total_price and unit_price remain unchanged
# - promo and promo_per_unit provide actual prices

print u'\nInspect given product at given store:'
print df_prices[(df_prices['store'] == 'Clermont Ferrand') &\
                (df_prices['idProduit'] == 39117)].to_string()

# Stock becomes NaN instead of 0 (no 0 in data)
# Product row can disappear (here after two days of no stock)
# When back: no promo at first but then again (maybe a mistake only for Drive?)

# Possibility to compute sales on one day when stock only decreases?
# Would then be interesting to scrap all stores during 7 days

# STOCK VARIATION FOR ONE STORE

df_store_prices = df_prices[df_prices['store'] == ls_stores[0]]
df_stock = df_store_prices.pivot(index = 'date',
                                 columns = 'idProduit',
                                 values = 'stock')
df_stock.fillna(0, inplace = True)
df_stock.index = pd.to_datetime(df_stock.index, format = '%Y%m%d')

df_dstock = df_stock - df_stock.shift(1)

print u'\nNb positive variations in stock:'
print df_dstock.apply(lambda x: (x>0).sum(), axis = 1)

print u'\nNb negative variations in stock:'
print df_dstock.apply(lambda x: (x<=0).sum(), axis = 1)

# todo: by rayon
ls_se_dpts = []
for ind in df_dstock.index:
  ls_ids = list(df_dstock.ix[ind][df_dstock.ix[ind] > 0].index)
  ls_se_dpts.append(df_products[df_products['idProduit'].isin(ls_ids)]\
                      ['department'].value_counts())

print u'\nOverview of stock positive variations by department'  
print pd.concat(ls_se_dpts,
                axis = 1,
                keys = df_dstock.index).fillna(0).T.to_string()

# TURNOVER ESTIMATES

# pbm: deal with positive variation?
# products w/ high number of positive variations?
# on 2015-05-24 & 25: no positive variations => use?

df_q_sold = df_dstock.copy()
df_q_sold[df_q_sold > 0] = np.nan
df_q_sold = df_q_sold.abs()

# how to fill? avg? avg of same week day? (how?) exclude promotions?
se_wd = df_q_sold.index.weekday
se_daily_quantity = df_q_sold[df_q_sold.index.weekday == 1].mean(0)

# Need a price dataframe (promotions?)
df_total_price = df_store_prices.pivot(index = 'date',
                                       columns = 'idProduit',
                                       values = 'total_price')
df_total_price.index = pd.to_datetime(df_total_price.index, format = '%Y%m%d')

# Multiply to get sales
df_sales = df_total_price.mul(df_q_sold, 1)

# Estimates of sales (before fill) by day
print df_sales.sum(1)
