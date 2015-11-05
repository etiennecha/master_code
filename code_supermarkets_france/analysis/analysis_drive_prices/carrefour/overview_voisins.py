#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *
import matplotlib.pyplot as plt

path_built = os.path.join(path_data,
                           u'data_supermarkets',
                           u'data_built',
                           u'data_drive',
                           u'data_carrefour')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

ls_df_voisins_2013_2014 = ['df_master_voisins_2013_2014',
                            'df_prices_voisins_2013_2014',
                            'df_products_voisins_2013_2014']

dict_df = {}
for df_file_title in ls_df_voisins_2013_2014:
  dict_df[df_file_title] =\
    pd.read_csv(os.path.join(path_built_csv,
                             '{:s}.csv'.format(df_file_title)),
                dtype = {'date' : str},
                encoding = 'utf-8')

df_master   = dict_df['df_master_voisins_2013_2014']
df_prices   = dict_df['df_prices_voisins_2013_2014']
df_products = dict_df['df_products_voisins_2013_2014']

# ####################
# CHECK & FIX DATA
# ####################

## #############
## FIX dum_promo
#
## Create Boolean (todo: check distinction with loyalty)
#for df_temp in [df_master, df_prices]:
#  df_temp['dum_promo'] = False
#  df_temp.loc[(~df_temp['promo'].isnull()) &\
#              (~df_temp['promo'].str.contains(u'fidélité',
#                                              case = False,
#                                              na = False)),
#              'dum_promo'] = True
#  df_temp['dum_loyalty'] = False
#  df_temp.loc[(~df_temp['promo'].isnull()) &\
#              (df_temp['promo'].str.contains(u'fidélité',
#                                             case = False,
#                                             na = False)),
#              'dum_loyalty'] = True
#
## #######################
## FIX PRODUCT DUPLICATES
#
#
## DUP ON ('brand', 'title', 'label')
#ls_dup_cols_0 = ['date', 'store', 'brand', 'title', 'label']
#df_dup_0 = df_master[df_master.duplicated(ls_dup_cols_0, take_last = False) |\
#                     df_master.duplicated(ls_dup_cols_0, take_last = True)].copy()
#df_dup_0.sort(ls_dup_cols_0, inplace = True)
#
## DUP ON ('section', 'family', 'brand', 'title', 'label')
#ls_dup_cols_1 = ['date', 'store', 'section', 'family', 'brand', 'title', 'label']
#df_dup_1 = df_master[df_master.duplicated(ls_dup_cols_1, take_last = False) |\
#                     df_master.duplicated(ls_dup_cols_1, take_last = True)].copy()
#df_dup_1.sort(ls_dup_cols_1, inplace = True)
#
## DUP ON ('section', 'family', 'brand', 'title', 'label',
##         'total_price', 'unit_price', 'promo')
#ls_dup_cols_2 = ['date', 'store', 'section', 'family',
#                 'brand', 'title', 'label',
#                 'total_price', 'unit_price', 'promo']
#df_dup_2 = df_master[df_master.duplicated(ls_dup_cols_2, take_last = False) |\
#                     df_master.duplicated(ls_dup_cols_2, take_last = True)].copy()
#
## Solve issue:
## - drop dup_2 (last): same products listed several times
## - redo dup_1: those are problematic
#
#print u'\nNb rows w/ simple duplicates (all fields):', len(df_master)
#df_master.drop_duplicates(ls_dup_cols_2, inplace = True)
#
#print u'\nNb rows w/o simple duplicates (all fields):', len(df_master)
#
## DUP ON ('section', 'family', 'brand', 'title', 'label')
#df_dup_pbm = df_master[df_master.duplicated(ls_dup_cols_1, take_last = False) |\
#                       df_master.duplicated(ls_dup_cols_1, take_last = True)].copy()
#df_dup_pbm.sort(ls_dup_cols_1)
#print df_dup_pbm[0:20].to_string()
#
## Be conservative: drop these store/prods in all periods
#
#df_drop = df_dup_pbm[['store', 'brand', 'title', 'label']].drop_duplicates()
#
### Method: in (issue with with NaN and slow)
##for row_i, row in df_drop.iterrows():
##  df_master = df_master.loc[~((df_master['store'] == row['store']) &\
##                              (df_master['brand'] == row['brand']) &\
##                              (df_master['title'] == row['title']) &\
##                              (df_master['label'] == row['label'])),]
#
## Method: merge
#df_drop['drop'] = 1
#df_master = pd.merge(df_master,
#                     df_drop,
#                     on = ['store', 'brand', 'title', 'label'],
#                     how = 'left')
#
#df_dropped = df_master.loc[(df_master['drop'] == 1),].copy()
#df_master = df_master.loc[(df_master['drop'] != 1),]
#df_master.drop(['drop'],
#               axis = 1,
#               inplace = True)
#
#print u'\nNb rows w/o pbmatic duplicates:', len(df_master)
#
## Drop problematic duplicates (diff prices)
## todo: check impact on promotion/loyalty
#
## Build price and product dfs:
## - get df_prices with unique products
## - get df_products to keep track of product section(s)/family(ies)
## - may affect data if stores don't use same categories (comprehensive)
#
## Build df_prices_sc w/ prices in columns
## May not store but need id_product
## Could be brand title label concatenated but heavy
#
#df_prices = df_master[['store', 'date',
#                       'brand', 'title', 'label',
#                       'dum_promo', 'dum_loyalty',
#                       'promo', 'total_price', 'unit_price', 'unit']]\
#              .drop_duplicates(['store', 'date', 'brand', 'title', 'label'])
#
#df_products = df_master[['section', 'family', 'brand', 'title', 'label']].drop_duplicates()
#
## ###############
## STATS DES
## ###############
#
## #########
## PRODUCTS
## #########
#
## NB PRODUCTS BY DAY AND STORE
#print u'\nNb products by day and store:'
#df_nb_products = pd.pivot_table(df_prices,
#                                columns = 'store',
#                                index = 'date',
#                                aggfunc = 'size')
#print u'\n', df_nb_products.to_string()
#
## ################
## PROMO & LOYALTY
## ################
#
## todo: take into account availability?
#
## AGGREGATE
#
## pbm here: same products listed under several dpts
#
## NB PROMO BY DAY AND STORE
#print u'\nNb promo by day and store:'
#df_nb_promo = pd.pivot_table(df_prices[df_prices['dum_promo'] == True],
#                             columns = 'store',
#                             index = 'date',
#                             aggfunc = 'size')
#df_nb_promo.fillna(0, inplace = True)
#print u'\n', df_nb_promo.to_string()
#
## NB LOYALTY BY DAY AND STORE
#print u'\nNb loyalty promo by day and store:'
#df_nb_loyalty = pd.pivot_table(df_master[df_master['dum_loyalty'] == True],
#                             columns = 'store',
#                             index = 'date',
#                             aggfunc = 'size')
#df_nb_loyalty.fillna(0, inplace = True)
#print u'\n', df_nb_loyalty.to_string()
#
## PRODUCTS
#
## PROMO: NB OF STORES FOR EACH PROD
#print u'\nNb stores by prod promo:'
#df_prod_promo = pd.pivot_table(df_prices[df_prices['dum_promo'] == True],
#                               columns = 'store',
#                               index = ['date', 'brand', 'title', 'label'],
#                               aggfunc = 'size')
#df_prod_promo.fillna(0, inplace = True)
#df_prod_promo['nb_stores'] =\
#  df_prod_promo[df_prod_promo.columns].sum(1)
#df_prod_promo.reset_index(drop = False, inplace = True)
#
#df_prod_promo.sort(['nb_stores', 'date', 'brand', 'title', 'label'],
#                   ascending = False,
#                   inplace = True)
#
#print df_prod_promo[0:20].to_string()
## print df_prod_promo[df_prod_promo['nb_stores'] == 10].to_string()
#
## todo: nb shared promos by pairs (a bit like a corr table)
## for one store: nb promos unique or shared w/ one other, two etc.
## brands of promo products?
## no need for too much dynamic analysis => check other data
#
## ################
## STORE PRICE VARS
## ################
#
### too slow
##df_master['product'] = df_master.apply(\
##  lambda row: ' - '.join([y if not pd.isnull(y) else 'Vide'\
##                             for y in row[['brand', 'title', 'label']].values]),
##  axis = 1)
#
#df_master.loc[df_master['brand'].isnull(),
#              'brand'] = 'Sans marque'
#df_master.loc[df_master['label'].isnull(),
#              'label'] = 'Sans label'
#df_master['product'] = df_master['brand'] + ' _ ' +\
#                         df_master['title'] + ' _ '+\
#                           df_master['label']
#
## df_master_s = df_master[df_master['store'] == '91 - LES ULIS']
#df_master_s = df_master[df_master['store'] == '78 - VOISINS LE BRETONNEUX']
#
## Build df store products (idProduit not unique: several families)
#lsd_prod = ['product', 'brand', 'title', 'label', 'family', 'section']
#df_products_s = df_master_s[lsd_prod].drop_duplicates()
#
## Build df with product prices in columns
#df_prices_s = df_master_s.drop_duplicates(['date', 'product'])
#df_prices_sc = df_prices_s.pivot(index = 'date',
#                                 columns = 'product',
#                                 values = 'total_price')
#df_prices_sc.index= pd.to_datetime(df_prices_sc.index,
#                                   format = '%Y%m%d')
#index_dr = pd.date_range(df_prices_sc.index[0],
#                         df_prices_sc.index[-1],
#                         freq = 'D')
#df_prices_sc = df_prices_sc.reindex(index_dr)
#
#df_prices_scf = df_prices_sc.fillna(method = 'bfill',
#                                    axis = 'index')
#df_prices_scfd = df_prices_scf - df_prices_scf.shift(1)
#se_scfd_nb_chges = df_prices_scfd.apply(lambda x: (x.abs()>0).sum(),
#                                        axis = 0)
#
#ax = df_prices_scf[u"Ballantines 's _ " +\
#                   u"Whisky Finest Blended Scotch Whisky _ " +\
#                   u"la bouteille de 1 l"].plot()
#ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
#plt.show()
#
## Count promo days by product in df_master_s
#se_prod_promo_days = df_prices_s[df_prices_s['dum_promo']]\
#                       ['product'].value_counts()
#
## Caution: one line per ('section', 'family', 'product'):
#df_products_s.set_index('product', inplace = True)
#df_products_s['nb_chges'] = se_scfd_nb_chges
#df_products_s['nb_promo_days'] = se_prod_promo_days
#
#df_products_s.loc[df_products_s['nb_promo_days'].isnull(),
#                  'nb_promo_days'] = 0
#df_products_s.sort(['nb_promo_days'],
#                   ascending = False,
#                   inplace = True)
#print df_products_s[0:20].to_string(index = False)
