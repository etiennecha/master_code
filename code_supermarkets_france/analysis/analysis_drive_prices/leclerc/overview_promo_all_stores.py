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

## RESTRICTION TO ONE DAY
#
#df_sub_master = df_master[(df_master['date'] == '20150508')]
#df_sub_prices = df_prices[(df_prices['date'] == '20150508')]
#
## PROMO
#df_promo = pd.pivot_table(df_sub_prices[df_sub_prices['dum_promo'] == True],
#                          columns = 'store',
#                          index = ['title', 'label'],
#                          aggfunc = 'size')
#df_promo.fillna(0, inplace = True)
#df_promo['nb_stores'] = df_promo.sum(1)
#df_promo.sort('nb_stores', ascending = False, inplace = True)
## could check if not promo because product not available or not offered
#print df_promo.to_string()
#
## LOYALTY
#df_loyalty = pd.pivot_table(df_sub_prices[~df_sub_prices['loyalty'].isnull()],
#                            columns = 'store',
#                            index = ['title', 'label'],
#                            aggfunc = 'size')
#df_loyalty.fillna(0, inplace = True)
#df_loyalty['nb_stores'] = df_loyalty.sum(1)
#df_loyalty.sort('nb_stores', ascending = False, inplace = True)
## could check if not loyalty because product not available or not offered
##print df_loyalty.to_string()

# ALL DAYS: FOCUS ON NB OF STORES FOR EACH PROD

# PROMO

df_promo = pd.pivot_table(df_prices[df_prices['dum_promo'] == True],
                            columns = 'store',
                            index = ['date', 'idProduit', 'title', 'label'],
                            aggfunc = 'size')
df_promo.fillna(0, inplace = True)
df_promo['nb_stores'] = df_promo[df_prices['store'].unique().tolist()].sum(1)
df_promo.reset_index(drop = False, inplace = True)

print u'\nTop promo (by nb of stores) on first day:'
df_promo.sort(['date', 'nb_stores'], ascending = False, inplace = True)
print df_promo[df_promo['date'] == '20150507'][ls_disp_prod][0:10].to_string()

print u'\nPromo by nb of stores over time:'
df_promo_su = pd.pivot_table(df_promo,
                               columns = 'nb_stores',
                               index = 'date',
                               aggfunc = 'size')
df_promo_su.fillna(0, inplace = True)
print df_promo_su.to_string()

# LOYALTY

df_loyalty = pd.pivot_table(df_prices[~df_prices['loyalty'].isnull()],
                          columns = 'store',
                          index = ['date', 'idProduit', 'title', 'label'],
                          aggfunc = 'size')
df_loyalty.fillna(0, inplace = True)
df_loyalty['nb_stores'] = df_loyalty[df_prices['store'].unique().tolist()].sum(1)
df_loyalty.reset_index(drop = False, inplace = True)

print u'\nTop loyalty promo (by nb of stores) on first day:'
df_loyalty.sort(['date', 'nb_stores'], ascending = False, inplace = True)
print df_loyalty[df_loyalty['date'] == '20150507'][ls_disp_prod][0:10].to_string()

print u'\nLoyalty promo by nb of stores over time:'
df_loyalty_su = pd.pivot_table(df_loyalty,
                               columns = 'nb_stores',
                               index = 'date',
                               aggfunc = 'size')
df_loyalty_su.fillna(0, inplace = True)
print df_loyalty_su.to_string()

# Check products with highest nb of stores

print u'\nProd with highest nb of promo on 20150526:'
print df_promo[(df_promo['date'] == '20150526') &\
               (df_promo['nb_stores'] == 6)][ls_disp_prod].to_string()

print u'\nProd with highest nb of loyaty promo on 20150514:'
print df_loyalty[(df_loyalty['date'] == '20150514') &\
                 (df_loyalty['nb_stores'] == 6)][ls_disp_prod].to_string()

#print df_prices[(df_prices[u'store'] == "Bois d'Arcy") &\
#                (df_prices[u'idProduit'] == 2582)][['total_price', 'promo']]
