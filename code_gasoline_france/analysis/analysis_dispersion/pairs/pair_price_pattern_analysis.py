#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_built_disp = os.path.join(path_data,
                                   u'data_gasoline',
                                   u'data_built',
                                   u'data_scraped_2011_2014')
path_dir_built_disp_csv = os.path.join(path_dir_built_disp, u'data_csv')
path_dir_built_disp_graphs = os.path.join(path_dir_built_disp, u'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DATA
# ##############

# DF INFO

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str},
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

# DF PRICES

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# #########
# STATS DES
# #########

# Caution: some stations have null group / group_last (todo: update?)
# Could avoid including INDEPENDANT (maintained for now)

# Build dict of group station ids on first and last days 
dict_group_f_ids = {}
for group_name in df_info['group'][~df_info['group'].isnull()].unique():
  dict_group_f_ids[group_name] =\
      list(df_info.index[df_info['group'] == group_name])
dict_group_l_ids = {}
for group_name in df_info['group_last'][~df_info['group_last'].isnull()].unique():
  dict_group_l_ids[group_name] =\
      list(df_info.index[df_info['group_last'] == group_name])

# Overview of group price distributions on first & last days
for day, dict_group_ids in [[df_prices_ttc.index[0], dict_group_f_ids],
                            [df_prices_ttc.index[-1], dict_group_l_ids]]:
  ls_group_names, ls_se_group_prices = [], []
  for group_name, ls_group_ids in dict_group_ids.items():
    ls_group_names.append(group_name)
    ls_se_group_prices.append(df_prices_ttc[ls_group_ids].ix[day].describe())
  df_group_prices = pd.concat(ls_se_group_prices, axis = 1, keys = ls_group_names)
  df_group_prices = df_group_prices.T
  df_group_prices.sort('count', ascending = False, inplace = True)
  print()
  print(u'Group price distributions on day', day)
  print(df_group_prices.to_string())

# ################################
# HISTOGRAM FIRST DAY VS LAST DAY
# ################################

bins = np.linspace(1.00, 1.60, 61)
ls_days = [df_prices_ttc.index[0], df_prices_ttc.index[-1]]
ls_colors = ['b', 'g']
for day, color in zip(ls_days, ls_colors):
 plt.hist(df_prices_ttc.ix[day].values,
          bins = bins,
          alpha = 0.5,
          label = day.strftime('%Y-%m-%d'),
          color = color)
plt.legend()
plt.xlim(1.00, 1.60)
plt.show()

# ###########################################################
# HISTOGRAM GROUP TOTAL vs. GROUP MOUSQUETAIRES (FIRST DAY)
# ###########################################################

bins = np.linspace(1.00, 1.60, 61)
ls_brands = ['TOTAL', 'MOUSQUETAIRES']
ls_colors = ['b', 'g']
day = df_prices_ttc.index[0]
for brand, color in zip(ls_brands, ls_colors):
 plt.hist(df_prices_ttc[df_info[df_info['group'] ==\
                                  brand].index].ix[day].values,
          label = brand,
          bins = bins,
          alpha = 0.5,
          color = color)
plt.legend()
plt.xlim(1.20, 1.60)
plt.show()

## ####################################################
## HISTOGRAMS OF GROUP PRICE DISTRIBUTIONS ON FIRST DAY
## ####################################################
#
##print df_prices_ttc.iloc[0].min()
##print df_prices_ttc.iloc[0].max()
#dict_group_ids = dict_group_f_ids
#for group_name, ls_group_ids in dict_group_ids.items():
#  if len(ls_group_ids) >= 100:
#    bins = np.linspace(1.20, 1.60, 41)
#    plt.hist(df_prices_ttc.iloc[0].values,
#             bins, alpha=0.5, label='All', color = 'g')
#    plt.hist(df_prices_ttc[dict_group_ids[group_name]].iloc[0].values,
#             bins, alpha=0.5, label=group_name, color = 'b')
#    plt.xlim(1.20, 1.60)
#    plt.legend()
#    plt.show()

# Focus on groups with highest internal price dispersion
# TOTAL, ESSO, AVIA, AGIP
#
## ############
## GROUP TOTAL
## ############
#
## Group Total stacked on first day
#bins = np.linspace(1.10, 1.60, 51)
#ls_brands = ['ELF', 'ELAN', 'TOTAL']
#day = df_prices_ttc.index[0]
#ls_ls_values = [df_prices_ttc[df_info[df_info['brand_0'] ==\
#                                        brand].index].ix[day].values\
#                  for brand in ls_brands]
#ls_ls_values = [ar_prices[~np.isnan(ar_prices)] for ar_prices in ls_ls_values]
#n, bins, patches = plt.hist(ls_ls_values,
#                            bins = bins,
#                            histtype = 'bar',
#                            stacked = True,
#                            label = ls_brands,
#                            alpha = 0.5)
#plt.legend()
#plt.show()
#
## Group Total on first day w/ distinction for TOTAL => TOTAL ACCESS
#bins = np.linspace(1.10, 1.60, 51)
#ls_brands = ['TTA', 'ELF', 'ELAN', 'TOTAL']
#day = df_prices_ttc.index[0]
#ls_ls_values = [df_prices_ttc[df_info[(df_info['brand_0'] == 'TOTAL') &\
#                                      (df_info['brand_last'] == 'TOTAL_ACCESS')]\
#                                     .index].ix[day].values] +\
#               [df_prices_ttc[df_info[df_info['brand_0'] ==\
#                                        brand].index].ix[day].values\
#                  for brand in ls_brands[1:3]] +\
#               [df_prices_ttc[df_info[(df_info['brand_0'] == 'TOTAL') &\
#                                      (df_info['brand_last'] != 'TOTAL_ACCESS')]\
#                                     .index].ix[day].values]
#n, bins, patches = plt.hist(ls_ls_values,
#                            color = ['darkorange', 'b', 'g', 'r'],
#                            bins = bins,
#                            histtype = 'bar',
#                            stacked = True,
#                            label = ls_brands,
#                            alpha = 0.5)
#plt.legend()
#plt.show()
#
## Group Total stacked on last day
#bins = np.linspace(1.10, 1.60, 51)
#ls_brands = ['TOTAL_ACCESS', 'ELAN', 'TOTAL']
#day = df_prices_ttc.index[-1]
#ls_ls_values = [df_prices_ttc[df_info[df_info['brand_last'] ==\
#                                        brand].index].ix[day].values\
#                  for brand in ls_brands]
#ls_ls_values = [ar_prices[~np.isnan(ar_prices)] for ar_prices in ls_ls_values]
#n, bins, patches = plt.hist(ls_ls_values,
#                            color = ['darkorange', 'g', 'r'],
#                            bins = bins,
#                            histtype = 'bar',
#                            stacked = True,
#                            label = ls_brands,
#                            alpha = 0.5)
#plt.legend()
#plt.show()
#
## ############
## GROUP ESSO
## ############
#
## Group Total stacked on first day
#bins = np.linspace(1.10, 1.60, 51)
#ls_brands = ['ESSO EXPRESS', 'ESSO']
#day = df_prices_ttc.index[0]
#ls_ls_values = [df_prices_ttc[df_info[df_info['brand_0'] ==\
#                                        brand].index].ix[day].values\
#                  for brand in ls_brands]
#ls_ls_values = [ar_prices[~np.isnan(ar_prices)] for ar_prices in ls_ls_values]
#n, bins, patches = plt.hist(ls_ls_values,
#                            bins = bins,
#                            histtype = 'bar',
#                            stacked = True,
#                            label = ls_brands,
#                            alpha = 0.5)
#plt.legend()
#plt.show()
#
## Group Total on first day w/ distinction for TOTAL => TOTAL ACCESS
#bins = np.linspace(1.10, 1.60, 51)
#ls_brands = ['ESSO_EXPRESS', 'ESSO']
#day = df_prices_ttc.index[0]
#ls_ls_values = [df_prices_ttc[df_info[(df_info['brand_0'] == 'ESSO') &\
#                                      (df_info['brand_last'] == 'ESSO_EXPRESS')]\
#                                     .index].ix[day].values] +\
#               [df_prices_ttc[df_info[(df_info['brand_0'] == 'ESSO') &\
#                                      (df_info['brand_last'] != 'ESSO_EXPRESS')]\
#                                     .index].ix[day].values]
#n, bins, patches = plt.hist(ls_ls_values,
#                            bins = bins,
#                            histtype = 'bar',
#                            stacked = True,
#                            label = ls_brands,
#                            alpha = 0.5)
#plt.legend()
#plt.show()
#
## Group Total stacked on last day
#bins = np.linspace(1.10, 1.60, 51)
#ls_brands = ['ESSO_EXPRESS', 'ESSO']
#day = df_prices_ttc.index[-1]
#ls_ls_values = [df_prices_ttc[df_info[df_info['brand_last'] ==\
#                                        brand].index].ix[day].values\
#                  for brand in ls_brands]
#ls_ls_values = [ar_prices[~np.isnan(ar_prices)] for ar_prices in ls_ls_values]
#n, bins, patches = plt.hist(ls_ls_values,
#                            bins = bins,
#                            histtype = 'bar',
#                            stacked = True,
#                            label = ls_brands,
#                            alpha = 0.5)
#plt.legend()
#plt.show()
#
## ######
## AVIA
## ######
#
## first day
#bins = np.linspace(1.10, 1.60, 51)
#ls_brands = ['AGIP', 'AVIA']
#day = df_prices_ttc.index[0]
#ls_ls_values = [df_prices_ttc[df_info[df_info['brand_0'] ==\
#                                        brand].index].ix[day].values\
#                  for brand in ls_brands]
#ls_ls_values = [ar_prices[~np.isnan(ar_prices)] for ar_prices in ls_ls_values]
#n, bins, patches = plt.hist(ls_ls_values,
#                            bins = bins,
#                            histtype = 'bar',
#                            stacked = False,
#                            label = ls_brands,
#                            alpha = 0.5)
#plt.legend()
#plt.show()
#
## last day
#bins = np.linspace(1.10, 1.60, 51)
#ls_brands = ['AGIP', 'AVIA']
#day = df_prices_ttc.index[-1]
#ls_ls_values = [df_prices_ttc[df_info[df_info['brand_last'] ==\
#                                        brand].index].ix[day].values\
#                  for brand in ls_brands]
#ls_ls_values = [ar_prices[~np.isnan(ar_prices)] for ar_prices in ls_ls_values]
#n, bins, patches = plt.hist(ls_ls_values,
#                            bins = bins,
#                            histtype = 'bar',
#                            stacked = False,
#                            label = ls_brands,
#                            alpha = 0.5)
#plt.legend()
#plt.show()
