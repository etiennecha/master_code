#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *

path_leclerc = os.path.join(path_data,
                            u'data_drive_supermarkets',
                            u'data_leclerc')

path_price_built_csv = os.path.join(path_leclerc,
                                    u'data_built',
                                    u'data_csv_leclerc')

ls_df_leclerc_2015 = ['df_master_leclerc_2015',
                      'df_prices_leclerc_2015',
                      'df_products_leclerc_2015']

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

# RESTRICTION TO ONE DAY
df_sub_master = df_master[(df_master['date'] == '20150508')]
df_sub_prices = df_prices[(df_prices['date'] == '20150508')]

# PROMO
df_promo = pd.pivot_table(df_sub_prices[df_sub_prices['dum_promo'] == True],
                          columns = 'store',
                          index = ['title', 'label'],
                          aggfunc = 'size')
df_promo.fillna(0, inplace = True)
df_promo['nb_stores'] = df_promo.sum(1)
df_promo.sort('nb_stores', ascending = False, inplace = True)
# could check if not promo because product not available or not offered
print df_promo.to_string()

# LOYALTY
df_loyalty = pd.pivot_table(df_sub_prices[~df_sub_prices['loyalty'].isnull()],
                          columns = 'store',
                          index = ['title', 'label'],
                          aggfunc = 'size')
df_loyalty.fillna(0, inplace = True)
df_loyalty['nb_stores'] = df_loyalty.sum(1)
df_loyalty.sort('nb_stores', ascending = False, inplace = True)
# could check if not loyalty because product not available or not offered
#print df_loyalty.to_string()
