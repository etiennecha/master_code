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

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_built_graphs = os.path.join(path_dir_built_paper, 'data_graphs')
path_dir_brand_chges = os.path.join(path_dir_built_graphs, 'brand_changes')
path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

path_dir_rotterdam = os.path.join(path_data, 'data_gasoline', 'data_source', 'data_rotterdam')
path_dir_reuters = os.path.join(path_dir_rotterdam, 'data_reuters')
path_xls_reuters_diesel = os.path.join(path_dir_reuters, 'diesel_data_to_import.xls')
path_xml_ecb = os.path.join(path_dir_rotterdam, 'usd.xml')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

## DF PRICES (TTC)
#ls_dates = [pd.to_datetime(date) for date in master_price['dates']]
#df_prices_ttc = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_dates).T
#
## DF PRICES (HT)
#df_prices_ht = df_prices_ttc / 1.196 - 0.4419
##df_prices_ht = pd.DataFrame.copy(df_prices_ttc)
##df_prices_ht = df_prices_ht / 1.196 - 0.4419
#
## PrixHT = PrixTTC / 1.196 - 0.4419 
## 2011: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,17899.html
## 2012: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,26979.html
## 2013: http://www.developpement-durable.gouv.fr/La-fiscalite-des-produits,31455.html
#ls_tax_11 = [(1,7,26,38,42,69,73,74,75,77,78,91,92,93,94,95,4,5,6,13,83,84), # PrixHT + 0.0135
#              (16,17,79,86)] # PrixHT + 0.0250
#ls_tax_12 = [(1,7,26,38,42,69,73,74), # PrixHT + 0.0135
#              (16,17,79,86)] # PrixHT + 0.0250
#
#df_prices_ht_2011 = df_prices_ht.ix[:'2011-12-31']
#for indiv_id in df_prices_ht_2011.columns:
#  if indiv_id[:-6] in ls_tax_11[0]:
#    df_prices_ht_2011[indiv_id] = df_prices_ht_2011[indiv_id].apply(lambda x: x + 0.0135)
#  elif indiv_id[:-6] in ls_tax_11[1]:
#    df_prices_ht_2011[indiv_id] = df_prices_ht_2011[indiv_id].apply(lambda x: x + 0.0250)
#
#df_prices_ht_2012 = df_prices_ht.ix['2012-01-01':]
#for indiv_id in df_prices_ht_2012.columns:
#  if indiv_id[:-6] in ls_tax_12[0]:
#    df_prices_ht_2012[indiv_id] = df_prices_ht_2012[indiv_id].apply(lambda x: x + 0.0135)
#  elif indiv_id[:-6] in ls_tax_12[1]:
#    df_prices_ht_2012[indiv_id] = df_prices_ht_2012[indiv_id].apply(lambda x: x + 0.0250)
#
#df_prices_ht.ix['2012-08-31':'2012-11-30'] = df_prices_ht.ix['2012-08-31':'2012-11-30'] + 0.03
#df_prices_ht.ix['2012-12-01':'2012-12-11'] = df_prices_ht.ix['2012-12-11':'2012-12-11'] + 0.02
#df_prices_ht.ix['2012-12-11':'2012-12-21'] = df_prices_ht.ix['2012-12-11':'2012-12-21'] + 0.015
#df_prices_ht.ix['2012-12-21':'2013-01-11'] = df_prices_ht.ix['2012-12-21':'2013-01-11'] + 0.01

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
