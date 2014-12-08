#!/usr/bin/python
# -*- coding: utf-8 -*-
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import matplotlib.pyplot as plt
from params import *

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    data_paper_folder)

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')

# ######################
# LOAD GAS STATION DATA
# ######################

#master_price_raw = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel_raw.json'))
#master_info_raw = dec_json(os.path.join(path_dir_built_json, 'master_info_raw.json'))

master_price = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel_fixed.json'))
master_info = dec_json(os.path.join(path_dir_built_json, 'master_info_fixed.json'))

# dict_brands = dec_json(os.path.join(path_dir_source, 'data_other', 'dict_brands.json'))

# todo: Work with master_price_raw or master_price ?
# todo: probably need intermediate stage (before duplicate reconciliation)

#ls_columns = [pd.to_datetime(date) for date in master_price['dates']]
#df_price = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_columns).T
#se_mean_price =  df_price.mean(1)

# #################
# DF PRICES
# #################

# DF PRICES TTC

ls_columns = [pd.to_datetime(date) for date in master_price['dates']]
df_prices_ttc = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_columns).T

# DF PRICES HT

# PrixHT = PrixTTC / 1.196 - 0.4419 
# 2011: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,17899.html
# 2012: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,26979.html
# 2013: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,31455.html

df_prices_ht = df_prices_ttc / 1.196 - 0.4419

ls_tax_11 = [(1,7,26,38,42,69,73,74,75,77,78,91,92,93,94,95,4,5,6,13,83,84), # PrixHT + 0.0135
              (16,17,79,86)] # PrixHT + 0.0250
ls_tax_11 = [map(lambda x: '{:d}'.format(x), ls_x) for ls_x in ls_tax_11]

ls_tax_12 = [(1,7,26,38,42,69,73,74), # PrixHT + 0.0135
              (16,17,79,86)] # PrixHT + 0.0250
ls_tax_12 = [map(lambda x: '{:d}'.format(x), ls_x) for ls_x in ls_tax_12]

# DIFFERENCES IN REGIONAL TICPE

## 2011
#df_prices_ht_2011 = df_prices_ht.ix[:'2011-12-31']
#for indiv_id in df_prices_ht_2011.columns:
#  if indiv_id[:-6] in ls_tax_11[0]:
#    df_prices_ht_2011[indiv_id] = df_prices_ht_2011[indiv_id].apply(lambda x: x + 0.0135)
#  elif indiv_id[:-6] in ls_tax_11[1]:
#    df_prices_ht_2011[indiv_id] = df_prices_ht_2011[indiv_id].apply(lambda x: x + 0.0250)
## 2012 onward
#df_prices_ht_2012 = df_prices_ht.ix['2012-01-01':]
#for indiv_id in df_prices_ht_2012.columns:
#  if indiv_id[:-6] in ls_tax_12[0]:
#    df_prices_ht_2012[indiv_id] = df_prices_ht_2012[indiv_id].apply(lambda x: x + 0.0135)
#  elif indiv_id[:-6] in ls_tax_12[1]:
#    df_prices_ht_2012[indiv_id] = df_prices_ht_2012[indiv_id].apply(lambda x: x + 0.0250)

# Alternative compliant (?) with newest pandas version
# 2011
ls_ids_2011_0 = [indiv_id for indiv_id in df_prices_ht.columns if indiv_id[:-6] in ls_tax_11[0]]
df_prices_ht.loc[:'2011-12-31', ls_ids_2011_0] =\
  df_prices_ht.loc[:'2011-12-31', ls_ids_2011_0] + 0.0135
ls_ids_2011_1 = [indiv_id for indiv_id in df_prices_ht.columns if indiv_id[:-6] in ls_tax_11[1]]
df_prices_ht.loc[:'2011-12-31', ls_ids_2011_1] =\
  df_prices_ht.loc[:'2011-12-31', ls_ids_2011_1] + 0.0250
# 2012 onward
ls_ids_2012_0 = [indiv_id for indiv_id in df_prices_ht.columns if indiv_id[:-6] in ls_tax_12[0]]
df_prices_ht.loc['2012-01-01':, ls_ids_2012_0] =\
  df_prices_ht.loc['2012-01-01':, ls_ids_2012_0] + 0.0135
ls_ids_2012_1 = [indiv_id for indiv_id in df_prices_ht.columns if indiv_id[:-6] in ls_tax_12[1]]
df_prices_ht.loc['2012-01-01':, ls_ids_2012_1] =\
  df_prices_ht.loc['2012-01-01':, ls_ids_2012_1] + 0.0250

# TEMPORARY TAX CUT BY GOVERNMENT

df_prices_ht.ix['2012-08-31':'2012-11-30'] = df_prices_ht.ix['2012-08-31':'2012-11-30'] + 0.03
df_prices_ht.ix['2012-12-01':'2012-12-11'] = df_prices_ht.ix['2012-12-01':'2012-12-11'] + 0.02
df_prices_ht.ix['2012-12-11':'2012-12-21'] = df_prices_ht.ix['2012-12-11':'2012-12-21'] + 0.015
df_prices_ht.ix['2012-12-21':'2013-01-11'] = df_prices_ht.ix['2012-12-21':'2013-01-11'] + 0.01

# OUTPUT TO CSV

# todo: check results under excel

df_prices_ttc.to_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc.csv'),
                     index_label = 'date',
                     float_format= '%.3f',
                     encoding = 'utf-8')

df_prices_ht.to_csv(os.path.join(path_dir_built_csv, 'df_prices_ht.csv'),
                    index_label = 'date',
                    float_format= '%.3f',
                    encoding = 'utf-8')
