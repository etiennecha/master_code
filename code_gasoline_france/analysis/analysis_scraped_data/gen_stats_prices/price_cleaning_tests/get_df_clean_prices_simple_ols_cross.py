#!/usr/bin/python
# -*- coding: utf-8 -*-
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import pandas as pd
from datetime import timedelta
import patsy
import scipy
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.feature_extraction import DictVectorizer

path_dir_built_scraped = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_scraped_2011_2014')

path_dir_built_csv = os.path.join(path_dir_built_scraped, 'data_csv')

# ###############
# LOAD DATA
# ###############

# LOAD DF INFO

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
df_info = df_info[df_info['highway'] != 1]

# LOAD DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

## LOAD DF PRICE STATS
#
#df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
#                                            'df_station_stats.csv'),
#                               dtype = {'id_station' : str},
#                               encoding = 'utf-8')
#df_station_stats.set_index('id_station', inplace = True)

# LOAD DF MARGIN CHGE

df_margin_chge = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_margin_chge.csv'),
                             dtype = {'id_station' : str},
                             parse_dates = ['date'],
                             encoding = 'utf-8')
df_margin_chge.set_index('id_station', inplace = True)

# Restrict DF PRICES to stations present in info (and kept e.g. not highway)
set_keep_ids = set(df_prices_ttc.columns).intersection(set(df_info.index))
df_prices_ht = df_prices_ht[list(set_keep_ids)]
df_prices_ttc = df_prices_ttc[list(set_keep_ids)]

# Chose before or after tax
df_prices = df_prices_ht
df_prices = df_prices * 100

## Set to nan stations with too few prices
#set_nan_ids = set_keep_ids.intersection(\
#                 df_station_stats.index[(df_station_stats['nb_chge'] < 5)|\
#                                        (df_station_stats['pct_chge'] < 0.03)])
#df_prices_ht[list(set_nan_ids)] = np.nan
#df_prices_ttc[list(set_nan_ids)] = np.nan

# Keep only 100 stations and 100 periods
end_date = df_prices_ht.index[500]
ind_keep_ids = df_margin_chge[df_margin_chge['date'] <=\
                                end_date - timedelta(days = 20)].index[:100]
df_prices = df_prices[ind_keep_ids].ix[:end_date]
### keep only one day in week
#df_prices = df_prices.loc[df_prices.index.weekday == 2]

## ############
## CLEAN PRICES
## ############

# BUILD DF IDS BASED ON PRICING CHANGES
ls_se_ids, ls_se_chge = [], []
for id_station in df_prices.columns:
  se_id_temp = pd.Series(id_station, index = df_prices.index)
  ls_se_ids.append(se_id_temp)
  se_chge_temp = pd.Series(0, index = df_prices.index)
  if (id_station in df_margin_chge.index) and\
     (not pd.isnull(df_margin_chge.ix[id_station]['date'])):
    se_chge_temp.ix[df_margin_chge.ix[id_station]['date']:] = 1
  ls_se_chge.append(se_chge_temp)

df_ids = pd.concat(ls_se_ids, axis = 1, keys = df_prices.columns)
df_chge_dum = pd.concat(ls_se_chge, axis = 1, keys = df_prices.columns)

# BUILD DF FINAL FOR REGRESSION
ls_all_ids = [x for id_station in df_prices.columns\
                for x in df_ids[id_station].values]
ls_all_chge_dum = [x for id_station in df_prices.columns\
                     for x in df_chge_dum[id_station].values]
ls_all_prices = [x for id_station in df_prices.columns\
                  for x in df_prices[id_station].values]
ls_all_dates = [x for id_station in df_prices.columns\
                  for x in df_prices.index]

df_final = pd.DataFrame(zip(ls_all_ids,
                            ls_all_chge_dum,
                            ls_all_dates,
                            ls_all_prices),
                        columns = ['id', 'chge_dum', 'date', 'price'])

# need each id to have at least on price a priori
df_final = df_final[~pd.isnull(df_final['price'])]
# temp: erase if no id (because no brand: need to fix beginning date)
df_final = df_final[~pd.isnull(df_final['id'])]

reg_res = smf.ols(formula = 'price ~ C(date) + C(id) + C(id):C(chge_dum) - 1', data = df_final).fit()
print reg_res.summary()

#reg_res_rob_cov = reg_res.get_robustcov_results(cov_type = 'HC3')
#cl_cov_mat = sm.stats.sandwich_covariance.cov_cluster(reg_res, df_final['date'].values)
## 2 groups: need int groups.. not sure how can do this correctly (maybe size pbms..)
## ftp://ftp.nwrc.ars.usda.gov/public/UofIMetData/Python27/Lib/site-packages/statsmodels/examples/ex_sandwich3.py
#df_final['date_cat'] = df_final['date'].astype('category')
#df_final['date_int'] = df_final['date_cat'].astype(int)
#cl_cov_mat_2 = sm.stats.sandwich_covariance.cov_cluster_2groups(reg_res,
#                                                                df_final['date_int'],
#                                                                df_final['id'].astype(int))
#cov01, covg, covt = cl_cov_mat_2
#bse_0 = sm.stats.sandwich_covariance.se_cov(covg) # time ?
#bse_1 = sm.stats.sandwich_covariance.se_cov(covt) # retailer ?
#bse_01 = sm.stats.sandwich_covariance.se_cov(cov01) # time and retailer? 

#cl_std_errors =  sm.stats.sandwich_covariance.cov_cluster_2groups(\
#                   reg_res,
#                   [date.strftime('%Y%m%d') for date in df_dispersion['date']],
#                   [indiv_id for indiv_id in df_dispersion['id']])
#ar_cl_std_errors = np.array([np.sqrt(cl_std_errors[0][i, i])\
#                               for i in range(len(str_formula.split('+')) + 1)])
#print str_formula
#print ar_cl_std_errors
#ar_cl_t_values = reg_res.params / ar_cl_std_errors
