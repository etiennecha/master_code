#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *
import matplotlib.pyplot as plt

pd.set_option('display.float_format', '{:,.2f}'.format)

path_built = os.path.join(path_data,
                           u'data_supermarkets',
                           u'data_built',
                           u'data_drive',
                           u'data_carrefour')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

ls_df_voisins_2013_2014 = ['df_master_voisins_2013-14_nam',
                           'df_prices_voisins_2013-14_nam',
                           'df_products_voisins_2013-14_nam']

dict_df = {}
for df_file_title in ls_df_voisins_2013_2014:
  dict_df[df_file_title] =\
    pd.read_csv(os.path.join(path_built_csv,
                             '{:s}.csv'.format(df_file_title)),
                dtype = {'date' : str},
                encoding = 'utf-8')

df_master   = dict_df['df_master_voisins_2013-14_nam']
df_prices   = dict_df['df_prices_voisins_2013-14_nam']
df_products = dict_df['df_products_voisins_2013-14_nam']

# ##################
# FIX PROMO (MOVE?)
# ##################

# Create Boolean (todo: check distinction with loyalty)
for df_temp in [df_master, df_prices]:
  # create promo dummy
  df_temp['dum_promo'] = False
  df_temp.loc[(~df_temp['promo'].isnull()) &\
              (~df_temp['promo'].str.contains(u'fidélité',
                                              case = False,
                                              na = False)),
              'dum_promo'] = True
  # create loyalty dummy
  df_temp['dum_loyalty'] = False
  df_temp.loc[(~df_temp['promo'].isnull()) &\
              (df_temp['promo'].str.contains(u'fidélité',
                                             case = False,
                                             na = False)),
              'dum_loyalty'] = True
  # create loyalty field, fill if must be and then erase promo
  df_temp['loyalty'] = None
  df_temp.loc[df_temp['dum_loyalty'],
              'loyalty'] = df_temp['promo']
  df_temp.loc[df_temp['dum_loyalty'],
              'promo'] = None

# ################
# STORE PRICE VARS
# ################

## too slow
#df_master['product'] = df_master.apply(\
#  lambda row: ' - '.join([y if not pd.isnull(y) else 'Vide'\
#                             for y in row[['brand', 'title', 'label']].values]),
#  axis = 1)

df_master.loc[df_master['brand'].isnull(),
              'brand'] = 'Sans marque'
df_master.loc[df_master['label'].isnull(),
              'label'] = 'Sans label'
df_master['product'] = df_master['brand'] + ' _ ' +\
                         df_master['title'] + ' _ '+\
                           df_master['label']

df_master_s = df_master

# Build df store products (idProduit not unique: several families)
lsd_prod = ['product', 'brand', 'title', 'label', 'family', 'section']
df_products_s = df_master_s[lsd_prod].drop_duplicates()

# Build df with product prices in columns
df_prices_s = df_master_s.drop_duplicates(['date', 'product'])
df_prices_sc = df_prices_s.pivot(index = 'date',
                                 columns = 'product',
                                 values = 'total_price')
df_prices_sc.index= pd.to_datetime(df_prices_sc.index,
                                   format = '%Y%m%d')
index_dr = pd.date_range(df_prices_sc.index[0],
                         df_prices_sc.index[-1],
                         freq = 'D')
df_prices_sc = df_prices_sc.reindex(index_dr)

df_prices_scf = df_prices_sc.fillna(method = 'bfill',
                                    axis = 'index')
df_prices_scfd = df_prices_scf - df_prices_scf.shift(1)
se_scfd_nb_chges = df_prices_scfd.apply(lambda x: (x.abs()>0).sum(),
                                        axis = 0)

# Count promo days by product in df_master_s
se_prod_promo_days = df_prices_s[df_prices_s['dum_promo']]\
                       ['product'].value_counts()

# Caution: one line per ('section', 'family', 'product'):
df_products_s.set_index('product', inplace = True)
df_products_s['nb_chges'] = se_scfd_nb_chges
df_products_s['nb_promo_days'] = se_prod_promo_days

df_products_s.loc[df_products_s['nb_promo_days'].isnull(),
                  'nb_promo_days'] = 0
df_products_s.sort(['nb_promo_days'],
                   ascending = False,
                   inplace = True)

print df_products_s[0:20].to_string(index = False)

ax = df_prices_sc[u"Badoit _ " +\
                  u"Eau gazeuse finement pétillante _ " +\
                  u"les 6 bouteilles de 1 l"].plot()
ax.yaxis.set_major_formatter(plt.FormatStrFormatter('%.2f'))
plt.show()

print df_products_s.describe().to_string()

df_products_s.sort(['nb_chges'],
                   ascending = False,
                   inplace = True)
print df_products_s[0:100].to_string(index = False)

ax = df_prices_sc[u"1664 _ " +\
                  u"Bière blonde _ " +\
                  u"les 12 bouteilles de 25cl"].plot()
plt.show()

# todo: apply promotion detections: inverse price movements
# todo: use promo info (if any?)
