#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os
from datetime import date, timedelta
from functions_generic_drive import *
import matplotlib.pyplot as plt

path_carrefour = os.path.join(path_data,
                           u'data_drive_supermarkets',
                           u'data_carrefour')

path_price_built_csv = os.path.join(path_carrefour,
                                    u'data_built',
                                    u'data_csv_carrefour_voisins')

ls_file_names = ['df_carrefour_voisins_20130418_20131128.csv',
                 'df_carrefour_voisins_20131129_20141205.csv',
                 'df_carrefour_voisins_2015_ref.csv']

ls_df_master = []
for file_name in ls_file_names:
  ls_df_master.append(pd.read_csv(os.path.join(path_price_built_csv,
                                               file_name),
                      encoding = 'utf-8'))
# parse_dates = ['date']))
# parse_dates a bit slow and not really necessary

# ################################
# NON UNIQUE PRODUCTS IN 2013-2014
# ################################

# for now.. only period with promo
df_master_2013 = ls_df_master[1]
df_master_2015 = ls_df_master[2]

# assume "Prix Promo" is not legit for now
df_master_2013.loc[df_master_2013['promo'] == u'Prix Promo',
                   'promo'] = None

ls_prod_id_cols = ['date', 'department', 'sub_department', 'title', 'price_lab_1']
df_dup_2013 = df_master_2013[(df_master_2013.duplicated(ls_prod_id_cols)) |\
                             (df_master_2013.duplicated(ls_prod_id_cols,
                                                        take_last = True))].copy()

# df_dup_2013.sort(ls_prod_id_cols, inplace = True)
# print len(df_dup_2013[~df_dup_2013['promo'].isnull()])
# print df_dup_2013[~df_dup_2013['promo'].isnull()][0:20].to_string()

df_unique_2013 = df_master_2013[~((df_master_2013.duplicated(ls_prod_id_cols)) |\
                                  (df_master_2013.duplicated(ls_prod_id_cols,
                                                             take_last = True)))].copy()

ls_dsd_cols = ls_prod_id_cols[1:] + ['price_lab_2']
df_dsd_2013 = df_unique_2013[ls_dsd_cols]\
                .drop_duplicates(ls_dsd_cols[:-1])

# ######################
# PROMOTIONS BY PRODUCT
# ######################

# add nb periods and nb promo
se_nb_per = df_unique_2013.groupby(ls_dsd_cols[:-1]).size()
se_nb_promo = df_unique_2013[~pd.isnull(df_unique_2013['promo'])]\
                .groupby(ls_dsd_cols[:-1]).size()

df_dsd_2013_add = pd.concat([se_nb_per, se_nb_promo],
                            axis = 1,
                            keys = ['nb_per', 'nb_promo'])
df_dsd_2013_add.loc[df_dsd_2013_add['nb_promo'].isnull(),
                    'nb_promo'] = 0
df_dsd_2013_add.reset_index(inplace = True)

df_dsd_2013 = pd.merge(df_dsd_2013,
                       df_dsd_2013_add,
                       on = ls_dsd_cols[:-1],
                       how = 'left')

print len(df_dsd_2013[df_dsd_2013['nb_per'] == df_dsd_2013['nb_promo']])
print len(df_dsd_2013[df_dsd_2013['nb_promo'] != 0])

# ####################
# PROMOTIONS BY PERIOD
# ####################

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
df_overview = df_overview.reindex(index_overview, fill_value = 0)

# ############################
# NB PRODUCTS BY DPT - SUBDPT
# ############################

# "Departement" => can check visually with series of nb by day

#se_daily_dpt = df_master_2013.groupby(['date', 'department']).size()
#df_daily_dpt = se_daily_dpt.reset_index()

df_daily_dpt = df_master_2013.pivot_table(values='price_1',
                                          index='date',
                                          cols='department',
                                          aggfunc='count')
df_daily_dpt.index = pd.to_datetime(df_daily_dpt.index, format = '%Y%m%d')
df_daily_dpt = df_daily_dpt.reindex(index_overview, fill_value = np.nan)

# "Sub-department" => see if any missing on some days

df_daily_sdpt = df_master_2013[df_master_2013['department'] == u'Maison & Entretien']\
                  .pivot_table(values='price_1',
                               index='date',
                               cols='sub_department',
                               aggfunc='count')
df_daily_sdpt.index = pd.to_datetime(df_daily_sdpt.index, format = '%Y%m%d')
df_daily_sdpt = df_daily_sdpt.reindex(index_overview, fill_value = np.nan)
df_daily_sdpt.plot(ylim = (0,150))

# looks like never more than 100
# hypothesis : did not go beyond first page for each subdpt
# check with other dpts
# then only got a sample of products... compare with more recent data then
