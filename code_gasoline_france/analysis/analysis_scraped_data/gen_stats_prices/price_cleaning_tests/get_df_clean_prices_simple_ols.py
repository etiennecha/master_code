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
                                end_date - timedelta(days = 20)].index[1000:1100]
df_prices = df_prices[ind_keep_ids].ix[:end_date]

## ############
## CLEAN PRICES
## ############

# BUILD DF IDS BASED ON PRICING CHANGES
ls_se_ids = []
for id_station in df_prices.columns:
  se_temp = pd.Series(id_station + '_0', index = df_prices.index)
  if (id_station in df_margin_chge.index) and\
     (not pd.isnull(df_margin_chge.ix[id_station]['date'])):
    se_temp.ix[df_margin_chge.ix[id_station]['date']:] = '%s_1' %id_station
  ls_se_ids.append(se_temp)
df_ids = pd.concat(ls_se_ids, axis = 1, keys = df_prices.columns)

# BUILD DF FINAL FOR REGRESSION
ls_all_ids = [x for id_station in df_prices.columns\
                for x in df_ids[id_station].values]
ls_all_prices = [x for id_station in df_prices.columns\
                  for x in df_prices[id_station].values]
ls_all_dates = [x for id_station in df_prices.columns\
                  for x in df_prices.index]

df_final = pd.DataFrame(zip(ls_all_ids,
                            ls_all_dates,
                            ls_all_prices),
                        columns = ['id', 'date', 'price'])

# need each id to have at least on price a priori
df_final = df_final[~pd.isnull(df_final['price'])]
# temp: erase if no id (because no brand: need to fix beginning date)
df_final = df_final[~pd.isnull(df_final['id'])]

reg_res = smf.ols(formula = 'price ~ C(date) + C(id) - 1', data = df_final).fit()
print reg_res.summary()
