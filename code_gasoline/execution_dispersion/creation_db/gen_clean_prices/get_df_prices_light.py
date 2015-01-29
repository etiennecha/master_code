#!/usr/bin/python
# -*- coding: utf-8 -*-
import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *
from BeautifulSoup import BeautifulSoup
import xlrd
import itertools
import scipy
import pandas as pd
import patsy
import statsmodels.api as sm
import statsmodels.formula.api as smf
import time

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_paper_dispersion')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

# ###############
# LOAD DATA
# ###############

# LOAD DF INFO AND PRICES

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

# Get rid of highway
df_info = df_info[df_info['highway'] != 1]

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

## DF CLEAN PRICES (ID split upon brand change)

# todo: refactor to make shorter
ls_ls_ids = []
for indiv_id in master_price['ids']:
  ls_brands = get_expanded_list(master_price['dict_info'][indiv_id]['brand_std'],
                                len(master_price['dates']))
  i = 0 
  ls_ids = ['%s%s' %(indiv_id, i)]
  j = 1
  while len(ls_ids) < len(master_price['dates']):
    if ls_brands[j] != ls_brands[j-1]:
      i+=1
    ls_ids.append('%s%s' %(indiv_id, i))
    j+=1
  ls_ls_ids.append(ls_ids)

ls_all_ids = [indiv_id for ls_ids in ls_ls_ids for indiv_id in ls_ids]
ls_all_prices = [price for ls_prices in master_price['diesel_price'] for price in ls_prices]
ls_all_dates = [date for indiv_id in master_price['ids'] for date in master_price['dates']]
df_final = pd.DataFrame(zip(ls_all_ids, ls_all_dates, ls_all_prices), columns = ['id', 'date', 'price'])
# todo: drop highway/corsica?

## OUTPUT FOR EXTERNAL PRICE CLEANING
#df_final.to_csv(os.path.join(path_dir_built_csv, 'price_panel_data_light.csv'),
#                float_format='%.4f',
#                encoding='utf-8')

# PRICE CLEANING

from sklearn.feature_extraction import DictVectorizer

df_final = df_final[~pd.isnull(df_final['price'])]
pd_as_dicts = [dict(r.iteritems()) for _, r in df_final[['id', 'date']].iterrows()]
sparse_mat_id_dates = DictVectorizer(sparse=True).fit_transform(pd_as_dicts)
res = scipy.sparse.linalg.lsqr(sparse_mat_id_dates, df_final['price'].values, iter_lim = 100)

y_hat = sparse_mat_id_dates * res[0]
df_final['yhat'] = y_hat
df_final['price_cl'] = df_final['price'] - df_final['yhat'] 
df_final['id'] = df_final['id'].str.slice(stop = -1) # set id back!
df_clean = df_final.set_index(['id', 'date'])
df_prices_cl = df_clean['price_cl'].unstack('id')
df_prices_cl.index = [pd.to_datetime(date) for date in df_prices_cl.index]
idx = pd.date_range('2011-09-04', '2013-06-04')
df_prices_cl = df_prices_cl.reindex(idx, fill_value = np.nan)

## OUTPUT FOR DISPERSION ANALYSIS
#df_prices_cl.index.name = 'date'
#df_prices_cl.to_csv(os.path.join(path_dir_built_csv, 'df_cleaned_prices.csv'),
#                    float_format='%.4f',
#                    encoding='utf-8')

## READ RESULTS FROM EXTERNAL PRICE CLEANING
## Consistency checked for R (one series...)
#
## READ CLEANED PRICES R
#path_csv_price_cl_R = os.path.join(path_dir_built_csv, 'price_cleaned_light_R.csv')
#df_prices_cl_R = pd.read_csv(path_csv_price_cl_R,
#                             dtype = {'id' : str,
#                                      'date' : str,
#                                      'price': np.float64,
#                                      'price.cl' : np.float64})
#df_prices_cl_R['id'] = df_prices_cl_R['id'].str.slice(stop = -1) # set id back!
#df_prices_cl_R  = df_prices_cl_R.pivot(index='date', columns='id', values='price.cl')
#df_prices_cl_R.index = [pd.to_datetime(x) for x in df_prices_cl_R.index]
#idx = pd.date_range('2011-09-04', '2013-06-04')
#df_prices_cl_R = df_prices_cl_R.reindex(idx, fill_value=np.nan)
#
## READ CLEANED PRICES STATA
#path_csv_price_cl_stata = os.path.join(path_dir_built_paper_csv, 'price_cleaned_stata.csv')
#df_prices_cl_stata = pd.read_csv(path_csv_price_cl_stata,
#                                 dtype = {'id' : str,
#                                          'date' : str,
#                                          'price': np.float64,
#                                          'price_cl' : np.float64})
#df_prices_cl_stata['id'] = df_prices_cl_stata['id'].str.slice(stop = -1) # set id back!
#df_prices_cl_stata  = df_prices_cl_stata.pivot(index='date', columns='id', values='price_cl')
#df_prices_cl_stata.index = [pd.to_datetime(x) for x in df_prices_cl_stata.index]
#idx = pd.date_range('2011-09-04', '2013-06-04')
#df_prices_cl_stata = df_prices_cl_stata.reindex(idx, fill_value=np.nan)
