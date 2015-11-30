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

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

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

# DF TOTAL ACCESS

df_ta = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                           'df_total_access_5km_dist_order.csv'),
                              dtype = {'id_station' : str,
                                       'id_total_ta' : str},
                              encoding = 'utf-8',
                              parse_dates = ['start', 'end',
                                             'ta_date_beg',
                                             'ta_date_end',
                                             'date_min_total_ta',
                                             'date_max_total_ta',
                                             'date_min_elf_ta',
                                             'date_max_elf_ta'])
df_ta.set_index('id_station', inplace = True)

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_scraped_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices = df_prices_ht

# GET RID OF PROBLEMATIC STATIONS
df_ta = df_ta[df_ta['filter'] > 5]

# DEFINE PRICE CONTROL SERIES
ls_ids_control = df_ta[df_ta['treatment_0'] == 3].index
se_mean_prices = df_prices[ls_ids_control].mean(1)

## demean within station to avoid composition effect
#df_prices_cl = df_prices - df_prices.mean(0)
#se_mean_prices = df_prices_cl[ls_ids_control].mean(1)

# #########
# CHOW TEST
# #########

#id_station = '10600008'
#date_beg, date_end = df_ta.ix[id_station]\
#                      [['ta_date_beg', 'ta_date_end']].values

# todo: add check enough days before and after treatment

id_station = '5100004' # '11000014'
date_beg, date_end = df_ta.ix[id_station]\
                       [['date_min_total_ta', 'date_max_total_ta']].values

df_test = df_prices[[id_station]].copy()
df_test.rename(columns = {id_station : 'price'},
               inplace = True)
df_test['ref_price'] = se_mean_prices
df_test['resid'] = df_test['ref_price'] - df_test['price']
df_test['treatment'] = 0
df_test.loc[(df_test.index >= date_beg) &\
            (df_test.index <= date_end),
            'treatment'] = np.nan
df_test.loc[(df_test.index >= date_end),
            'treatment'] = 1
df_test['resid_2'] = df_test['resid'] * df_test['treatment']
df_test['ref_price_2'] = df_test['ref_price'] * df_test['treatment']
df_test['l1_resid'] = df_test['resid'].shift(1)
df_test['l1_resid_bt'] = df_test['resid'].shift(1) * (1 - df_test['treatment'])
df_test['l1_resid_at'] = df_test['resid'].shift(1) * df_test['treatment']

## keep only one price per week
#df_test['dow'] = df_test.index.weekday
#df_test = df_test[df_test['dow'] == 3]

rest0 = smf.ols('price ~ ref_price + treatment',
               data = df_test).fit(cov_type='HAC',
                                   cov_kwds={'maxlags':7})
print rest0.summary()
#rob_cov_hact0 = sm.stats.sandwich_covariance.cov_hac(rest0, nlags = 7)
#rob_bset0 = np.sqrt(np.diag(rob_cov_hact0))

rest1 = smf.ols('price ~ ref_price + ref_price_2 + treatment',
              data = df_test).fit(cov_type='HAC',
                                  cov_kwds={'maxlags':7})
print rest1.summary()

hyp = '(ref_price_2 = 0), (treatment =0)'
#rob_cov_hact1 = sm.stats.sandwich_covariance.cov_hac(rest1, nlags = 7)
#f_test = rest1.f_test(hyp, cov_p = rob_cov_hact1)
f_test = rest1.f_test(hyp)
print f_test

## identification of ref_price_2 vs. treatment? => require both
## todo: nice graphs
#df_test.plot(kind = 'scatter', x = 'price', y = 'ref_price')

# loop on treatment_0 == 1
# store treatment / treatment & ref_price_2 (param & bse, R2?)
# check how many significant pos / negs? (compare w/ OLS DDs)

# pbm: high autocorr of residuals
print u'Autocorr of residuals (1):', rest1.resid.autocorr()
# cannot include l1_resid: captures treatment when there is one
