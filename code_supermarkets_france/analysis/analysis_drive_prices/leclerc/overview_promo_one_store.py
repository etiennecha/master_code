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

ls_drop = ['store', 'date']

# Restriction to one store (and one day for now)
df_sub_master = df_master[(df_master['store'] == 'Clermont Ferrand') &\
                          (df_master['date'] == '20150508')].drop(ls_drop,
                                                                  axis = 1)

df_sub_prices = df_prices[(df_prices['store'] == 'Clermont Ferrand') &\
                          (df_prices['date'] == '20150508')].drop(ls_drop,
                                                                  axis = 1)

# Todo: compare df_master vs df_prices to count promo
print u'\nCount promo in df_sub_prices:'
print df_sub_prices['dum_promo'].value_counts()
#print len(df_sub_prices[df_sub_prices['promo'] != u'0.00 \u20ac'])
#print df_sub_prices[(df_sub_prices['dum_promo'] != True) &\
#                    (df_sub_prices['promo'] != u'0.00 \u20ac')].to_string()

print u'\nCount promo in df_sub_master:'
print len(df_sub_master[df_sub_master['dum_promo'] == True])
print len(df_sub_master[df_sub_master['dum_promo'] == True]['idProduit'].unique())

print df_sub_prices[df_sub_prices['dum_promo'] == True].to_string()
