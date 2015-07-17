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

dict_df = {}
for df_file_title in ls_df_leclerc_2015:
  dict_df[df_file_title] =\
    pd.read_csv(os.path.join(path_price_built_csv,
                             '{:s}.csv'.format(df_file_title)),
                dtype = {'date' : str,
                         'idProduit': str},
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

# Caution: when promo: real price is in 'promo'

# Restriction to one store

df_prices['listed_price'] = df_prices['total_price']
df_prices.loc[df_prices['promo'] != 0,
              'listed_price'] = df_prices['promo']

# Work on regular prices for now
df_store_listed_prices = df_prices[['date', 'idProduit', 'listed_price']]\
                           [df_prices['store'] == 'Clermont Ferrand']

df_prices_cols = df_store_listed_prices.pivot(values = 'listed_price',
                                              columns = 'idProduit',
                                              index = 'date')

df_prices_cols.index = pd.to_datetime(df_prices_cols.index, format = '%Y%m%d')

# Count nb price chges by day and products
# pbm: num to nan, nan to num? (missing days? products?)
 
df_prices_cols =\
  df_prices_cols.apply(lambda x: x.str.rstrip(u'\u20ac')).astype(float)

df_prices_cols_diff = df_prices_cols.shift(1) - df_prices_cols

se_prod_nb_chges = df_prices_cols_diff.apply(lambda x: len(x[x.abs() > 1e-05]),
                                            axis = 0)

se_day_nb_chges = df_prices_cols_diff.apply(lambda x: len(x[x.abs() > 1e-05]),
                                           axis = 1)

print se_day_nb_chges.to_string()
