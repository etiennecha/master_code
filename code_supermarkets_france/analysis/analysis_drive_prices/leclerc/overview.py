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

print u'\nNb promo by nb of stores over time:'
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

# todo: nb new/old products, promo etc.
df_test = pd.pivot_table(df_prices,
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
se_day_beg_prod = df_dtest.apply(lambda x: (x==1).sum(), axis = 1)
se_day_end_prod = df_dtest.apply(lambda x: (x==-1).sum(), axis = 1)
df_dyna_prod = pd.concat([se_day_beg_prod, se_day_end_prod],
                          axis = 1,
                          keys = ['beg', 'end'])
df_dyna_prod['nb_prod'] = df_nb_prod[ls_stores[0]]
# not consistent... check what is wrong (nan?)

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
