#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *
import matplotlib.pyplot as plt

path_source = os.path.join(path_data,
                              u'data_supermarkets',
                              u'data_source',
                              u'data_drive',
                              u'data_carrefour')

path_source_csv = os.path.join(path_source,
                               u'data_csv')

path_built = os.path.join(path_data,
                          u'data_supermarkets',
                          u'data_built',
                          u'data_drive',
                          u'data_carrefour')

path_built_csv = os.path.join(path_built,
                              u'data_csv')

ls_file_names = ['df_carrefour_voisins_20130418_20131128.csv',
                 'df_carrefour_voisins_20131129_20141205.csv',
                 'df_carrefour_voisins_2015_ref.csv']

ls_df_master = []
for file_name in ls_file_names:
  ls_df_master.append(pd.read_csv(os.path.join(path_source_csv,
                                               file_name),
                      encoding = 'utf-8'))

# parse_dates = ['date']))
# parse_dates a bit slow and not really necessary

# For now: only period with promo
df_master_2013 = ls_df_master[1]
df_master_2015 = ls_df_master[2]

# ###################################
# FIX DATA & IMPORT BRANDS FROM 2015
# ###################################

# Assume "Prix Promo" is not legit promotion (pbm of data collect)
df_master_2013.loc[df_master_2013['promo'] == u'Prix Promo',
                   'promo'] = None

### UNIQUE PRODUCTS IN 2013-2014

ls_prod_id_cols = ['date', 'section', 'family', 'title', 'label']
df_dup_2013 = df_master_2013[(df_master_2013.duplicated(ls_prod_id_cols)) |\
                             (df_master_2013.duplicated(ls_prod_id_cols,
                                                        take_last = True))].copy()

# df_dup_2013.sort(ls_prod_id_cols, inplace = True)
# print len(df_dup_2013[~df_dup_2013['promo'].isnull()])
# print df_dup_2013[~df_dup_2013['promo'].isnull()][0:20].to_string()

df_unique_2013 = df_master_2013[~((df_master_2013.duplicated(ls_prod_id_cols)) |\
                                  (df_master_2013.duplicated(ls_prod_id_cols,
                                                             take_last = True)))].copy()

ls_dsd_cols = ls_prod_id_cols[1:] + ['unit']
df_dsd_2013 = df_unique_2013[ls_dsd_cols]\
                .drop_duplicates(ls_dsd_cols[:-1])

### UNIQUE PRODUCTS IN 2015

ls_prod_id_cols_2 = ['date', 'section', 'family', 'title', 'label', 'brand']
df_dup_2015 = df_master_2015[(df_master_2015.duplicated(ls_prod_id_cols_2)) |\
                             (df_master_2015.duplicated(ls_prod_id_cols_2,
                                                        take_last = True))].copy()
df_unique_2015 = df_master_2015[~((df_master_2015.duplicated(ls_prod_id_cols_2)) |\
                                  (df_master_2015.duplicated(ls_prod_id_cols_2,
                                                             take_last = True)))].copy()

ls_dsd_cols_2 = ls_prod_id_cols_2[1:] + ['unit']
df_dsd_2015 = df_unique_2015[ls_dsd_cols_2]\
                .drop_duplicates(ls_dsd_cols_2[:-1])

### IMPORT BRANDS FROM 2015 IN 2013-14

# CAUTION: 
# In df_dsd_2015: ('title', 'price_lab_1') non unique (several sub dpts)
# Hence need to drop duplicates before merging
df_dsd_2013 = pd.merge(df_dsd_2013,
                       df_dsd_2015[['title',
                                    'brand',
                                    'label']].drop_duplicates('title',
                                                              'label'),
                       left_on = ['title', 'label'],
                       right_on = ['title', 'label'],
                       how = 'left')
#df_dsd_2013.drop(['title_2'], axis = 1, inplace = True)
#df_dsd_2013.rename(columns = {'title' : 'title_2'}, inplace = True)

# print len(df_dsd_2013[~df_dsd_2013['title_1'].isnull()])
# 4974 among 16615...

# todo: propagate brand

### ADD PROMOTIONS BY PRODUCT TO df_dsd_2013

# add nb periods and nb promo
se_nb_per = df_unique_2013.groupby(ls_dsd_cols_2[:-2]).size()
se_nb_promo = df_unique_2013[~pd.isnull(df_unique_2013['promo'])]\
                .groupby(ls_dsd_cols_2[:-2]).size()

df_dsd_2013_add = pd.concat([se_nb_per, se_nb_promo],
                            axis = 1,
                            keys = ['nb_per', 'nb_promo'])
df_dsd_2013_add.loc[df_dsd_2013_add['nb_promo'].isnull(),
                    'nb_promo'] = 0
df_dsd_2013_add['nb_promo'] = df_dsd_2013_add['nb_promo'].astype(int)

df_dsd_2013_add.reset_index(inplace = True)

df_dsd_2013 = pd.merge(df_dsd_2013,
                       df_dsd_2013_add,
                       on = ls_dsd_cols_2[:-2],
                       how = 'left')

print u'\nNb products always in promo: {:d}'\
          .format(len(df_dsd_2013[df_dsd_2013['nb_per'] == df_dsd_2013['nb_promo']]))

print u'\nNb products with at least one promo: {:d}'\
          .format(len(df_dsd_2013[df_dsd_2013['nb_promo'] != 0]))

# ##################
# OUTPUT FINAL DATA
# ##################

df_master_2013.to_csv(os.path.join(path_built_csv,
                                 'df_master_voisins_2013_2014.csv'),
                      encoding = 'utf-8',
                      index = False)

df_dsd_2013.to_csv(os.path.join(path_built_csv,
                                'df_products_voisins_2013_2014.csv'),
                   encoding = 'utf-8',
                   index = False)

df_unique_2013.to_csv(os.path.join(path_built_csv,
                                   'df_prices_voisins_2013_2014.csv'),
                      encoding = 'utf-8',
                      index = False)

# ###################################
# DESCRIPTIVE STATISTICS (MOVE?)
# ###################################

pd.set_option('display.float_format', '{:,.2f}'.format)

### PROMOTIONS BY PRODUCT

print u'\nDesc promotions by products:'
print df_dsd_2013[['nb_per', 'nb_promo']].describe()

### PROMOTIONS BY PERIOD

#ls_title_suspect = df_master_2013[df_master_2013['promo'] == 'Prix Promo']\
#                     ['title'].unique().tolist()
#print df_dsd_2013[df_dsd_2013['title'].isin(ls_title_suspect)].to_string()

# print df_master_2013['promo'].value_counts()
se_daily_prod = df_master_2013.groupby('date').size()
se_daily_promo = df_master_2013[~df_master_2013['promo'].isnull()].groupby('date').size()
df_overview = pd.concat([se_daily_prod, se_daily_promo],
                        axis = 1,
                        keys = ['nb_prod', 'nb_promo'])

df_overview.index = pd.to_datetime(df_overview.index, format = '%Y%m%d')
index_overview = pd.date_range(start = df_overview.index[0],
                               end   = df_overview.index[-1], 
                               freq='D')
df_overview = df_overview.reindex(index_overview, fill_value = np.nan)
df_overview['pct_promo'] = df_overview['nb_promo'] / df_overview['nb_prod']

#df_overview['pct_promo'].plot()
#plt.show()

### PROMOTIONS BY BRAND

# Need to know how many promo per period have no identified brand
print u'\nNb promo with identified brand: {:d}'.format(\
        len(df_dsd_2013[(df_dsd_2013['nb_promo'] != 0) &\
                        (df_dsd_2013['brand'].isnull())]))

# Promo by brand in terms of products and promo days
se_brand_promo = df_dsd_2013[df_dsd_2013['nb_promo'] != 0]['brand'].value_counts()
se_brands = df_dsd_2013['brand'].value_counts()
se_brand_nb_per = df_dsd_2013[['brand', 'nb_per']].groupby('brand').sum()['nb_per']
se_brand_nb_promo = df_dsd_2013[['brand', 'nb_promo']].groupby('brand').sum()['nb_promo']

df_brand_promo = pd.concat([se_brands, se_brand_promo, se_brand_nb_per, se_brand_nb_promo],
                           axis = 1,
                           keys = ['nb_prods', 'nb_prod_w_promo', 'nb_days', 'nb_promo_days'])

for field in ['nb_prods', 'nb_prod_w_promo', 'nb_days', 'nb_promo_days']:
  df_brand_promo.loc[df_brand_promo[field].isnull(),
                     field] = 0
  df_brand_promo[field] = df_brand_promo[field].astype(int)

df_brand_promo['pct_prod_w_promo'] = df_brand_promo['nb_prod_w_promo'] /\
                                       df_brand_promo['nb_prods']

df_brand_promo['pct_promo_days'] = df_brand_promo['nb_promo_days'] /\
                                       df_brand_promo['nb_days']

df_brand_promo.sort('nb_prods', ascending = False, inplace = True)

# print df_brand_promo[0:20].to_string()

### DEPARTMENTS: NB PRODUCTS AND PROMO

# Nb products
df_dpt_nb_prod = df_master_2013.pivot_table(values='total_price',
                                            index='date',
                                            columns='section',
                                            aggfunc='count')
df_dpt_nb_prod.index = pd.to_datetime(df_dpt_nb_prod.index, format = '%Y%m%d')
df_dpt_nb_prod = df_dpt_nb_prod.reindex(index_overview, fill_value = np.nan)
#df_dpt_nb_prod.plot()
#plt.show()

# Nb promo
df_dpt_nb_promo = df_master_2013[~df_master_2013['promo'].isnull()]\
                    .pivot_table(values='total_price',
                                 index='date',
                                 columns='section',
                                 aggfunc='count')
df_dpt_nb_promo.index = pd.to_datetime(df_dpt_nb_promo.index, format = '%Y%m%d')
df_dpt_nb_promo = df_dpt_nb_promo.reindex(index_overview, fill_value = np.nan)

# Pct promo
df_dpt_pct_promo = df_dpt_nb_promo / df_dpt_nb_prod

# Plot pct and nb (todo: add vertical lines on mondays)
se_avg_dpt_nb_prod = df_dpt_nb_prod.mean()
se_avg_dpt_nb_prod.sort(ascending = False)
#df_dpt_pct_promo['weekday'] = df_dpt_pct_promo.index.weekday

#ls_col_disp = se_avg_dpt_nb_prod.index[4:6]
ls_col_disp = [u'Épicerie', u'Hygiène & Beauté', u'Boissons', u'Crèmerie']
ax = df_dpt_pct_promo[ls_col_disp][50:230].plot()
for date, dow in zip(df_dpt_pct_promo.index, df_dpt_pct_promo.index.weekday):
  if dow == 0: # dow is monday
    plt.axvline(date, color = 'k', linestyle = ':')
ax.grid('on', which='major', axis='x', linestyle = '--')
# ax.grid('off', axis='y')
plt.show()

#df_dpt_nb_promo[se_avg_dpt_nb_prod.index[0:2]][200:500].plot()
#plt.show()

### SUBDEPARTMENTS: NB PRODUCTS AND PROMO

# Nb products
df_subdpt_nb_prod = df_master_2013.pivot_table(values='total_price',
                                          index='date',
                                          columns=['section', 'family'],
                                          aggfunc='count')
df_subdpt_nb_prod.index = pd.to_datetime(df_subdpt_nb_prod.index, format = '%Y%m%d')
df_subdpt_nb_prod = df_subdpt_nb_prod.reindex(index_overview, fill_value = np.nan)

se_subdpt_max = df_subdpt_nb_prod.max()
df_subdpt_desc = df_subdpt_nb_prod.describe().T

#print df_subdpt_desc.to_string()

# looks like never more than 100
# did not go beyond first page for each subdpt
# check with other dpts
# then only got a sample of products... compare with more recent data then

print u"\nNb of subdpts with 100 products at least once: {:d} among {:d}"\
          .format(len(df_subdpt_desc[df_subdpt_desc['max'] == 100]),
                  len(df_subdpt_desc))

print u"\nNb of subdpts with 100 products Q75% days: {:d} among {:d}"\
          .format(len(df_subdpt_desc[df_subdpt_desc['75%'] == 100]),
                  len(df_subdpt_desc))

# Nb products: focus on one departement (drop?) 
df_sdpt_nb_prod = df_master_2013[df_master_2013['section'] == u'Maison & Entretien']\
                  .pivot_table(values='total_price',
                               index='date',
                               columns='family',
                               aggfunc='count')
df_sdpt_nb_prod.index = pd.to_datetime(df_sdpt_nb_prod.index, format = '%Y%m%d')
df_sdpt_nb_prod = df_sdpt_nb_prod.reindex(index_overview, fill_value = np.nan)
#df_sdpt_nb_prod.plot(ylim = (0,150))
#plt.show()

# Nb promo
df_subdpt_nb_promo = df_master_2013[~df_master_2013['promo'].isnull()]\
                       .pivot_table(values='total_price',
                                    index='date',
                                    columns=['section', 'family'],
                                    aggfunc='count')
df_subdpt_nb_promo.index = pd.to_datetime(df_subdpt_nb_promo.index, format = '%Y%m%d')
df_subdpt_nb_promo = df_subdpt_nb_promo.reindex(index_overview, fill_value = np.nan)
