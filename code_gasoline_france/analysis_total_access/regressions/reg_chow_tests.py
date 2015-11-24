#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_built_scraped = os.path.join(path_data,
                                      u'data_gasoline',
                                      u'data_built',
                                      u'data_scraped_2011_2014')

path_dir_built_scraped_csv = os.path.join(path_dir_built_scraped,
                                          u'data_csv')

path_dir_built_ta = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_total_access')

path_dir_built_ta_json = os.path.join(path_dir_built_ta, 
                                      'data_json')

path_dir_built_ta_csv = os.path.join(path_dir_built_ta, 
                                     'data_csv')

# #########
# LOAD DATA
# #########

# DF STATION INFO

df_info = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
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
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
df_info.set_index('id_station', inplace = True)
df_info = df_info[df_info['highway'] != 1]

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices = df_prices_ttc

se_mean_prices = df_prices.mean(1)

# DF TOTAL ACCESS

df_total_access = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                           'df_total_access.csv'),
                              dtype = {'id_station' : str},
                              encoding = 'utf-8',
                              parse_dates = ['start', 'end',
                                             'ta_date_beg',
                                             'ta_date_end',
                                             'date_min_total_ta',
                                             'date_max_total_ta',
                                             'date_min_elf_ta',
                                             'date_max_elf_ta'])
df_total_access.set_index('id_station', inplace = True)

# #########
# CHOW TEST
# #########

id_station = '10600008'
date_beg, date_end = df_total_access.ix[id_station]\
                      [['ta_date_beg', 'ta_date_end']].values

df_test = df_prices[[id_station]].copy()
df_test.rename(columns = {id_station : 'price'},
               inplace = True)
df_test['nat_price'] = se_mean_prices
df_test['resid'] = df_test['nat_price'] - df_test['price']
df_test['treatment'] = 0
df_test.loc[(df_test.index >= date_beg) &\
            (df_test.index <= date_end),
            'treatment'] = np.nan
df_test.loc[(df_test.index >= date_end),
            'treatment'] = 1
df_test['resid_2'] = df_test['resid'] * df_test['treatment']
df_test['nat_price_2'] = df_test['nat_price'] * df_test['treatment']

res = smf.ols('price ~ nat_price + treatment',
              data = df_test).fit()
print res.summary()

res = smf.ols('price ~ nat_price + nat_price_2 + treatment',
              data = df_test).fit()
print res.summary()

# identification of nat_price_2 vs. treatment?
# show graph
