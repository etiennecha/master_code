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

df_master = dict_df['df_master_auchan_2015']
df_prices = dict_df['df_prices_auchan_2015']
df_products = dict_df['df_products_auchan_2015']

# TODO: check for duplicates

# temp fix ?
df_prices.loc[df_prices['dum_promo'] == 'yes', 'dum_promo'] = True
df_prices.loc[df_prices['dum_promo'] == 'no', 'dum_promo'] = False

# #########
# OVERVIEW
# #########

# can drop 20150506 which has more store (unique occurence)
df_overview = pd.pivot_table(df_master[df_master['date'] != '20150506'],
                             columns = 'store',
                             index = 'date',
                             aggfunc = 'size')
print df_overview.to_string()

# #########
# PROMO
# #########

# ALL DAYS: FOCUS ON NB OF STORES FOR EACH PROD

df_promo = pd.pivot_table(df_prices[df_prices['dum_promo'] == True],
                            columns = 'store',
                            index = ['date', 'title'],
                            aggfunc = 'size')
df_promo.fillna(0, inplace = True)
df_promo['nb_stores'] = df_promo[df_prices['store'].unique().tolist()].sum(1)
df_promo.reset_index(drop = False, inplace = True)
