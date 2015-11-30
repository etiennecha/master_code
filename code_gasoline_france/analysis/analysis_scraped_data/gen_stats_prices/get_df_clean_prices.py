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
                             encoding = 'utf-8')
df_margin_chge.set_index('id_station', inplace = True)

# Restrict DF PRICES to stations present in info (and kept e.g. not highway)
set_keep_ids = set(df_prices_ttc.columns).intersection(set(df_info.index))
df_prices_ht = df_prices_ht[list(set_keep_ids)]
df_prices_ttc = df_prices_ttc[list(set_keep_ids)]

# Chose before or after tax
df_prices = df_prices_ttc

## Set to nan stations with too few prices
#set_nan_ids = set_keep_ids.intersection(\
#                 df_station_stats.index[(df_station_stats['nb_chge'] < 5)|\
#                                        (df_station_stats['pct_chge'] < 0.03)])
#df_prices_ht[list(set_nan_ids)] = np.nan
#df_prices_ttc[list(set_nan_ids)] = np.nan

## ############
## CLEAN PRICES
## ############

## BUILD DF BRANDS (OLD METHOD)
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

## BUILD DF IDS BASED ON BRANDS
## create one id by station and brand
## todo: take into account brand change dates based on price variations
#max_brand_day_ind = 2
#ls_se_ids = []
#for id_station in df_prices_ht.columns:
#  se_temp = pd.Series(None, index = df_prices_ht.index)
#  i = 0
#  while (i < max_brand_day_ind) and\
#        (not pd.isnull(df_info.ix[id_station]['day_%s' %i])):
#    se_temp.ix[df_info.ix[id_station]['day_%s' %i]:] = '%s_%s' %(id_station, i)
#    i += 1
#  # need to overwrite first days if not active? (no price anyway... same for last?)
#  # se_temp.ix[df_info.ix[id_station]['end']:] = np.nan # todo: offset by one (+)
#  ls_se_ids.append(se_temp)
#df_ids = pd.concat(ls_se_ids, axis = 1, keys = df_prices_ht)

# BUILD DF IDS BASED ON PRICING CHANGES
lim_var = 0.02
ls_se_ids = []
for id_station in df_prices.columns:
  se_temp = pd.Series(id_station + '_0', index = df_prices.index)
  i = 0
  if (id_station in df_margin_chge.index) and\
     (np.abs(df_margin_chge.ix[id_station]['value']) >= lim_var):
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

# need dates as string for DictVectorizer
df_final['date'] = df_final['date'].apply(lambda x: x.strftime('%Y%m%d'))

pd_as_dicts = [dict(r.iteritems()) for _, r in df_final[['id', 'date']].iterrows()]
sparse_mat_id_dates = DictVectorizer(sparse=True).fit_transform(pd_as_dicts)
res = scipy.sparse.linalg.lsqr(sparse_mat_id_dates,
                               df_final['price'].values,
                               iter_lim = 100,
                               calc_var = True)

# caution: content of res[0] : sorted according to param names
# here: all dates in chronological order then 10000001_0, 10000005_0 etc.

y_hat = sparse_mat_id_dates * res[0]
df_final['yhat'] = y_hat
df_final['price_cl'] = df_final['price'] - df_final['yhat'] 
df_final['id'] = df_final['id'].str.slice(stop = -2) # set id back!
df_clean = df_final.set_index(['id', 'date'])
df_prices_cl = df_clean['price_cl'].unstack('id')
df_prices_cl.index = [pd.to_datetime(date) for date in df_prices_cl.index]
idx = pd.date_range('2011-09-04', '2013-06-04')
df_prices_cl = df_prices_cl.reindex(idx, fill_value = np.nan)

# OUTPUT FOR DISPERSION ANALYSIS
df_prices_cl.index.name = 'date'
df_prices_cl.to_csv(os.path.join(path_dir_built_csv,
                                 'df_cleaned_prices.csv'),
                    float_format='%.4f',
                    encoding='utf-8')

# TIME FE
se_mean_price = df_prices.mean(1)
se_mean_price_nonan = se_mean_price[~pd.isnull(se_mean_price)]
se_date_ind = se_mean_price_nonan.index
se_day_fe = pd.Series(res[0][:len(se_date_ind)], index = se_date_ind)
se_final_day_fe = se_day_fe.asfreq('1d')
se_final_day_fe.plot() # dunno why... no scale
plt.show()

# STATION FE
se_unique_ids = pd.concat(ls_se_ids, axis = 0, ignore_index = True)\
                  .drop_duplicates(take_last = False)
se_unique_ids.sort(inplace = True) # important step: res[0] sorted according to param names
se_id_fe = pd.Series(res[0][len(se_date_ind):], index = se_unique_ids)
df_id_fe = se_id_fe.reset_index(drop = False)
df_id_fe['id_station'] = df_id_fe['index'].str.slice(stop = -2) # set id back!
ind_ids_chge = df_margin_chge[df_margin_chge['value'].abs() >= lim_var].index
#print df_id_fe[df_id_fe['id'].isin(ind_ids_chge)][0:20].to_string()

# VAR IN STATION FE VS. MARGIN CHGE
ls_rows_chge = []
for id_station in ind_ids_chge:
  ls_rows_chge.append((id_station,
                       df_id_fe[df_id_fe['index'] ==\
                         '{:s}_0'.format(id_station)][0].iloc[0],
                       df_id_fe[df_id_fe['index'] ==\
                         '{:s}_1'.format(id_station)][0].iloc[0]))
df_fe_chge = pd.DataFrame(ls_rows_chge, columns = ['id_station', 'fe_0', 'fe_1'])
df_fe_chge['var'] = df_fe_chge['fe_1'] - df_fe_chge['fe_0']
df_margin_chge.reset_index(drop = False, inplace = True)
df_chge = pd.merge(df_fe_chge,
                   df_margin_chge,
                   how = 'left',
                   left_on = 'id_station',
                   right_on = 'id_station')

df_test = pd.concat([se_final_day_fe, se_mean_price],
                    keys = ['trend', 'mean_price'],
                    axis = 1)

## STD PARAMETERS
#res[-1][-10:] * res[3]**2 / (sparse_mat_id_dates.shape[0] - len(res[0]))
