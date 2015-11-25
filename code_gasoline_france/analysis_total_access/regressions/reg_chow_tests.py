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



# DF TOTAL ACCESS

df_ta = pd.read_csv(os.path.join(path_dir_built_ta_csv,
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
df_ta.set_index('id_station', inplace = True)

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

id_station = '11000014'
date_beg, date_end = df_ta.ix[id_station]\
                      [['date_min_total_ta', 'date_max_total_ta']].values

df_test = df_prices[[id_station]].copy()
df_test.rename(columns = {id_station : 'price'},
               inplace = True)
df_test['ref_price'] = se_mean_prices
df_test['resid'] = df_test['ref_price'] - df_test['price']
df_test['l1_resid'] = df_test['resid'].shift(1)
df_test['treatment'] = 0
df_test.loc[(df_test.index >= date_beg) &\
            (df_test.index <= date_end),
            'treatment'] = np.nan
df_test.loc[(df_test.index >= date_end),
            'treatment'] = 1
df_test['resid_2'] = df_test['resid'] * df_test['treatment']
df_test['ref_price_2'] = df_test['ref_price'] * df_test['treatment']

res0 = smf.ols('price ~ ref_price + treatment + l1_resid',
               data = df_test).fit()
print res0.summary()

res1 = smf.ols('price ~ ref_price + ref_price_2 + treatment + l1_resid',
              data = df_test).fit()
print res1.summary()

hyp = '(ref_price_2 = 0), (treatment =0)'
f_test = res1.f_test(hyp)
print f_test

## identification of ref_price_2 vs. treatment? => require both
## todo: nice graphs
#df_test.plot(kind = 'scatter', x = 'price', y = 'ref_price')

# loop on treatment_0 == 1
# store treatment / treatment & ref_price_2 (param & bse, R2?)
# check how many significant pos / negs? (compare w/ OLS DDs)

# pbm: high autocorr of residuals
res1.resid.autocorr()

# #########
# LOOP TEST
# #########

# todo: split by dpt and use dpt mean without total access as ref

ls_ids_nores = []
ls_rows_res = []
for id_station, row in df_ta[df_ta['treatment_0'] == 1].iterrows():
  try:
    date_beg, date_end = row[['date_min_total_ta', 'date_max_total_ta']].values
    df_station = df_prices[[id_station]].copy()
    df_station.rename(columns = {id_station : 'price'},
                   inplace = True)
    df_station['ref_price'] = se_mean_prices
    df_station['resid'] = df_station['ref_price'] - df_station['price']
    df_station['l1_resid'] = df_station['resid'].shift(1)
    df_station['treatment'] = 0
    df_station.loc[(df_station.index >= date_beg) &\
                (df_station.index <= date_end),
                'treatment'] = np.nan
    df_station.loc[(df_station.index >= date_end),
                'treatment'] = 1
    df_station['resid_2'] = df_station['resid'] * df_station['treatment']
    df_station['ref_price_2'] = df_station['ref_price'] * df_station['treatment']
    res0 = smf.ols('price ~ ref_price + treatment + l1_resid',
                   data = df_station).fit()
    #print res0.summary()
    res1 = smf.ols('price ~ ref_price + ref_price_2 + treatment + l1_resid',
                  data = df_station).fit()
    #print res1.summary()
    hyp = '(ref_price_2 = 0), (treatment =0)'
    f_test = res1.f_test(hyp)
    #print f_test
    ls_rows_res.append([id_station,
                        res0.params.ix['ref_price'],
                        res0.bse.ix['ref_price'],
                        res0.params.ix['treatment'],
                        res0.bse.ix['treatment'],
                        res0.tvalues.ix['treatment'],
                        res0.pvalues.ix['treatment'],
                        res0.rsquared,
                        res0.rsquared_adj,
                        res0.resid.autocorr(),
                        float(f_test.pvalue)])
  except:
    ls_ids_nores.append(id_station)

df_res = pd.DataFrame(ls_rows_res,
                      columns = ['id_station',
                                 'c_ref_price',
                                 'b_ref_price',
                                 'c_treatment',
                                 'b_treatment',
                                 't_treatment',
                                 'p_treatment',
                                 'r2',
                                 'r2a',
                                 'r_ac',
                                 'p_chow'])

print u'Nb w/ problematic R2 (excluded):',\
       len(df_res[(~np.isfinite(df_res['r2'])) |
                  (df_res['r2'] < 0)])
df_res = df_res[(np.isfinite(df_res['r2'])) &\
                (df_res['r2'] >= 0)]

print df_res.describe().to_string()

df_res_sig = df_res[df_res['p_treatment'] <= 0.05]

print u'\nOverview significant treatment:'
print df_res_sig['c_treatment'].describe()
print u'Nb above 1c:', len(df_res_sig[df_res_sig['c_treatment'] >= 0.01])
print u'Nb below -1c:', len(df_res_sig[df_res_sig['c_treatment'] <= -0.01])
