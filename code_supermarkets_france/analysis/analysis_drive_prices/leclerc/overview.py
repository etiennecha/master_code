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

# #########################
# GENERAL OVERVIEW: DYNAMIC
# #########################

df_temp = df_prices[~df_prices['loyalty'].isnull()] # df_prices[df_prices['dum_promo'] == True]
df_nb_temp = df_nb_loyalty # df_nb_promo

# todo: nb new/old products, promo etc.
df_test = pd.pivot_table(df_temp,
                         columns = 'date',
                         index = ['store', 'idProduit'],
                         aggfunc = 'size')

df_test.fillna(0, inplace = True)
df_test.reset_index(drop = False, inplace = True)
df_test = df_test[df_test['store'] == ls_stores[0]]
df_test.drop(labels = ['store'], axis = 1, inplace = True)
df_test.set_index('idProduit', inplace = True)
df_test = df_test.T
df_test.index = pd.to_datetime(df_test.index, format = '%Y%m%d')

df_dtest = df_test.shift(1) - df_test
se_day_beg_prod = df_dtest.apply(lambda x: (x==-1).sum(), axis = 1)
se_day_end_prod = df_dtest.apply(lambda x: (x==1).sum(), axis = 1)
df_dyna_prod = pd.concat([se_day_beg_prod, se_day_end_prod],
                          axis = 1,
                          keys = ['beg', 'end'])
df_dyna_prod['nb_prod'] = df_nb_temp[ls_stores[0]]
# seems beg/end are inversed... check what is wrong (nan?)

print u'\nOverview of promo strat of store {:s}'.format(ls_stores[0])
print df_dyna_prod.to_string()

# ###################
# BY PRODUCT
# ###################

# PROMO
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

# LOYALTY
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

# Check products with highest nb of stores

print u'\nProd with highest nb of promo on 20150526:'
print df_prod_promo[(df_prod_promo['date'] == '20150526') &\
                    (df_prod_promo['nb_stores'] == 6)][ls_disp_prod].to_string()

print u'\nProd with highest nb of loyaty promo on 20150514:'
print df_prod_loyalty[(df_prod_loyalty['date'] == '20150514') &\
                      (df_prod_loyalty['nb_stores'] == 6)][ls_disp_prod].to_string()

#print df_prices[(df_prices[u'store'] == "Bois d'Arcy") &\
#                (df_prices[u'idProduit'] == 2582)][['total_price', 'promo']]

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
df_dstock = df_stock - df_stock.shift(1)

# nb positive variations by row
df_dstock.index = pd.to_datetime(df_dstock.index, format = '%Y%m%d')

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
print pd.concat(ls_se_dpts,
                axis = 1,
                keys = df_dstock.index).fillna(0).T.to_string()

# ###############################
# PRICE VARIATIONS (STORE LEVEL)
# ###############################

# Price var not related to promo
df_store_prices = df_prices[df_prices['store'] == ls_stores[0]].copy()
df_total_price = df_store_prices.pivot(index = 'date',
                                 columns = 'idProduit',

                                 values = 'total_price')
df_dtotal_price = df_total_price - df_total_price.shift(1)

df_dtotal_price.index = pd.to_datetime(df_dtotal_price.index, format = '%Y%m%d')

print u'\nNb price chges per period:'
se_pos_vars = df_dtotal_price.apply(lambda x: (x>0).sum(), axis = 1)
se_neg_vars = df_dtotal_price.apply(lambda x: (x<0).sum(), axis = 1)
df_total_price_vars = pd.concat([se_pos_vars, se_neg_vars],
                                axis = 1,
                                keys = ['pos', 'neg'])
print df_total_price_vars.to_string()

# coordination among stores? which output?
# size of price variations? inverse variations? no connection to promo/loyalty?

print u'\nNb price chges per product over the period:'
se_prod_vars = df_dtotal_price.apply(lambda x: (x.abs()>0).sum(), axis = 0)
print se_prod_vars.describe()

#se_prod_vars.sort(ascending = False)

df_prod_temp = df_products.copy()
df_prod_temp.set_index('idProduit', inplace = True)
df_prod_temp['nb_price_vars'] = se_prod_vars
df_prod_temp.sort('nb_price_vars', ascending = False, inplace = True)
print df_prod_temp[0:100].to_string()

# Exemple (todo: fill index + put stock on right axis)
df_store_prices['date'] = pd.to_datetime(df_store_prices['date'], format = '%Y%m%d')
df_product = df_store_prices[['total_price', 'promo', 'stock', 'date']]\
               [df_store_prices['idProduit'] == 34305] # 40204
df_product.set_index('date', inplace = True)
index = pd.date_range(start = df_product.index[0],
                      end   = df_product.index[-1], 
                      freq = 'D')
df_product = df_product.reindex(index = index)

import matplotlib.pyplot as plt

fig = plt.figure()
ax1 = fig.add_subplot(111)
line_1 = ax1.plot(df_product.index,
                  df_product['total_price'].values,
                  ls='-', c='b', label='Product price (euros)')
ax2 = ax1.twinx()
line_2 = ax2.plot(df_product.index,
                  df_product['stock'].values,
                  ls='-', c= 'g',
                  label=r'Product stock')

lns = line_1 + line_2
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, loc=0)

#ax1.grid()
##ax1.set_title(r"Add title here")
#ax1.set_ylabel(r"French retail diesel (euros/l)")
#ax2.set_ylabel(r"Rotterdam wholesale diesel (euros/l)")
#plt.tight_layout()
plt.show()
