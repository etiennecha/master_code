#!/usr/bin/python
# -*- coding: utf-8 -*-
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import pandas as pd
import patsy
import scipy
import statsmodels.api as sm
import statsmodels.formula.api as smf
from sklearn.feature_extraction import DictVectorizer

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_paper_dispersion')

path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

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

# Restrict DF PRICES to stations present in info (and kept e.g. not highway)
df_prices_ht = df_prices_ht[[x for x in df_prices_ht.columns if x in df_info.index]]
df_prices_ttc = df_prices_ttc[[x for x in df_prices_ttc.columns if x in df_info.index]]

## BUILDF DF BRANDS (COMPLY WITH OLD METHOD)
#max_brand_day_ind = 2
#ls_se_brands = []
#for id_station in df_info.index:
#  se_temp = pd.Series(None, index = df_prices_ht.index)
#  i = 0
#  while (i < max_brand_day_ind) and\
#        (not pd.isnull(df_info.ix[id_station]['day_%s' %i])):
#    se_temp.ix[df_info.ix[id_station]['day_%s' %i]:] =\
#       df_info.ix[id_station]['brand_%s' %i]
#    i += 1
#  # need to overwrite first days if not active? (no price anyway... same for last?)
#  # se_temp.ix[df_info.ix[id_station]['end']:] = np.nan # todo: offset by one (+)
#  ls_se_brands.append(se_temp)
#df_brands = pd.concat(ls_se_brands, axis = 1, keys = df_info.index)

## ############
## CLEAN PRICES
## ############

# BUILDF DF IDS

# create one id by station and brand
# todo: take into account brand change dates based on price variations

max_brand_day_ind = 2
ls_se_ids = []
for id_station in df_prices_ht.columns:
  se_temp = pd.Series(None, index = df_prices_ht.index)
  i = 0
  while (i < max_brand_day_ind) and\
        (not pd.isnull(df_info.ix[id_station]['day_%s' %i])):
    se_temp.ix[df_info.ix[id_station]['day_%s' %i]:] = '%s_%s' %(id_station, i)
    i += 1
  # need to overwrite first days if not active? (no price anyway... same for last?)
  # se_temp.ix[df_info.ix[id_station]['end']:] = np.nan # todo: offset by one (+)
  ls_se_ids.append(se_temp)

df_ids = pd.concat(ls_se_ids, axis = 1, keys = df_info.index)

# build DF FINAL for cleaning

ls_all_ids = [x for id_station in df_prices_ht.columns for x in df_ids[id_station].values]
ls_all_prices = [x for id_station in df_prices_ht.columns for x in df_prices_ht[id_station].values]
ls_all_dates = [x for id_station in df_prices_ht.columns for x in df_prices_ht.index]

df_final = pd.DataFrame(zip(ls_all_ids,
                            ls_all_dates,
                            ls_all_prices),
                        columns = ['id', 'date', 'price'])
df_final = df_final[~pd.isnull(df_final['price'])]

# temp: erase if no id (because no brand: need to fix beginning date)
df_final = df_final[~pd.isnull(df_final['id'])]

# need dates as string for DictVectorizer
df_final['date'] = df_final['date'].apply(lambda x: x.strftime('%Y%m%d'))

pd_as_dicts = [dict(r.iteritems()) for _, r in df_final[['id', 'date']].iterrows()]
sparse_mat_id_dates = DictVectorizer(sparse=True).fit_transform(pd_as_dicts)
res = scipy.sparse.linalg.lsqr(sparse_mat_id_dates,
                               df_final['price'].values,
                               iter_lim = 100)

y_hat = sparse_mat_id_dates * res[0]
df_final['yhat'] = y_hat
df_final['price_cl'] = df_final['price'] - df_final['yhat'] 
df_final['id'] = df_final['id'].str.slice(stop = -2) # set id back!
df_clean = df_final.set_index(['id', 'date'])
df_prices_cl = df_clean['price_cl'].unstack('id')
df_prices_cl.index = [pd.to_datetime(date) for date in df_prices_cl.index]
idx = pd.date_range('2011-09-04', '2013-06-04')
df_prices_cl = df_prices_cl.reindex(idx, fill_value = np.nan)

### OUTPUT FOR DISPERSION ANALYSIS
##df_prices_cl.index.name = 'date'
##df_prices_cl.to_csv(os.path.join(path_dir_built_csv,
##                                 'df_cleaned_prices.csv'),
##                    float_format='%.4f',
##                    encoding='utf-8')
