#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
import os, sys
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf
import numpy as np
from sklearn import metrics, ensemble, neighbors
from patsy import dmatrix, demo_data, ContrastMatrix, Poly

pd.set_option('float_format', '{:10,.0f}'.format)
pd.set_option('display.max_colwidth', 25)

format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

path_kaggle = os.path.join(path_data,
                          'data_kaggle',
                          '201712_restaurant')

# modeling
# https://www.kaggle.com/c/recruit-restaurant-visitor-forecasting/discussion/45882

"""
TODO:
- total nb of persons in area per day of week ?
- total nb of persons in genre per day of week?
- limit history used to compute averages / min / max
  (min/max per day of week?)
=> try implementing store by store estimation?
=> how to use power of joint estimation?
=> split method for recent / old restaurants
   (volatility? which ones to focus on?)
"""

# ##########
# LOAD DATA
# ##########

# data description
# https://www.kaggle.com/c/recruit-restaurant-visitor-forecasting/data

# todo: fetch weather data
ls_load = [['air_reserve', ['reserve_datetime', 'visit_datetime']],
           ['air_store_info', []],
           ['air_visit_data', ['visit_date']],
           ['hpg_reserve', ['reserve_datetime', 'visit_datetime']],
           ['hpg_store_info', []],
           ['store_id_relation', []],
           ['date_info', ['calendar_date']],
           ['sample_submission', []]]

dict_dfs = {}
for alias, date_cols in ls_load:
  dict_dfs[alias] = pd.read_csv(os.path.join(path_kaggle, alias +'.csv.zip'),
                                parse_dates = date_cols)

df_calendar = dict_dfs['date_info'].copy()
df_calendar['week'] = df_calendar['calendar_date'].dt.week

# specific holiday
df_calendar['holiday_flg2'] = 0
df_calendar.loc[(((df_calendar['calendar_date'] >= '2016-05-03') &
                  (df_calendar['calendar_date'] <= '2016-05-05')) |
                 ((df_calendar['calendar_date'] >= '2017-05-03') &
                  (df_calendar['calendar_date'] <= '2017-05-05'))),
                'holiday_flg2'] = 1

df_air_visits = dict_dfs['air_visit_data'].copy()
df_air_visits = df_air_visits.merge(df_calendar,
                                    left_on = 'visit_date',
                                    right_on = 'calendar_date',
                                    how = 'left')

df_sample = dict_dfs['sample_submission'].copy()
df_sample['air_store_id'] = df_sample['id'].str.slice(stop = -11)
df_sample['visit_date'] = pd.to_datetime(df_sample['id'].str.slice(start = -10),
                                         format = '%Y-%m-%d')
df_sample = df_sample.merge(df_calendar,
                            left_on = 'visit_date',
                            right_on = 'calendar_date',
                            how = 'left')

# ##################
# STORES TO FORECAST
# ##################

# Submission uses air_store_id => all are in air_store_info
# Are hpg data really useful?
ls_sample_store_id = df_sample['air_store_id'].drop_duplicates().tolist()
ls_sample_dates = df_sample['visit_date'].drop_duplicates().tolist()
print()
print('Nb dates to predict: {:}'.format(len(ls_sample_dates)))
print('Nb stores to predict: {:}'.format(len(ls_sample_store_id)))

# ######################
# MERGE AIR AND HPG DATA
# ######################

"""
Store data:
- only 150 lines in store_id_relation air
- hpg and air use different area_name / genre_name
"""

# Check air_store_info
print()
print('air_store_info')
print(dict_dfs['air_store_info'][['air_store_id',
                                  'air_genre_name',
                                  'air_area_name']].nunique())
# todo: check latitude / longitude (and areas)
# todo: 

df_stores = pd.merge(dict_dfs['air_store_info'],
                     dict_dfs['store_id_relation'],
                     on = 'air_store_id',
                     how = 'outer')
df_stores = pd.merge(df_stores,
                     dict_dfs['hpg_store_info'],
                     on = 'hpg_store_id',
                     how = 'outer')

df_stores.loc[df_stores['latitude_x'].isnull(), 'latitude_x'] = df_stores['latitude_y']
df_stores.loc[df_stores['longitude_x'].isnull(), 'longitude_x'] = df_stores['longitude_y']
df_stores.drop(['latitude_y', 'longitude_y'], axis = 1, inplace = True)
df_stores.rename(columns = {'latitude_x' : 'lat',
                            'longitude_x' : 'lng'}, inplace = True)

df_stores0 = (df_stores[(~df_stores['air_store_id'].isnull()) &
                        (~df_stores['hpg_store_id'].isnull())])

# #############
# FOCUS ON AREA
# #############

df_stores_a = df_stores[df_stores['air_area_name'] == df_stores['air_area_name'].iloc[0]]
ls_air_id_a = df_stores_a['air_store_id'].tolist()

df_visits_a = df_air_visits[df_air_visits['air_store_id'].isin(ls_air_id_a)].copy()

dfw = df_visits_a.pivot(index = 'visit_date', columns = 'air_store_id', values = 'visitors')
dfw = dfw[ls_air_id_a]

# just for display
dfw.columns = [x for x in range(len(dfw.columns))]

# ###########
# REGRESSION
# ###########

"""
How much history for each store to forecast
=> many: 
"""

df_air_store_stats = (df_air_visits.groupby('air_store_id')
                                   .agg({'visit_date': [min, max, 'count'],
                                         'visitors': [min, max, 'mean', 'median', 'std']}))
df_air_store_stats.columns = ['_'.join(map(str, i)) for i in df_air_store_stats.columns]

print()
print('Stats des: visit data of stores to forecast:')
print(df_air_store_stats.ix[ls_sample_store_id].describe().to_string())

# try:
# ISO week FE, Day of week FE, Store FE
# Additive and separative
#visisors = a*FE iso sem * b*FE jour sem * c*FE mag
#ln(visitors) = a*FE iso sem + b*FE jour sem + c*FE mag [todo: check validity?]
# Zone specific ISO week FE
# Holiday?

# => check store stability over time
# => wanna estimate FE based on most recent / stable data

df_visits_f = df_air_visits[df_air_visits['air_store_id'].isin(ls_sample_store_id)].copy()
df_visits_f['ln_visitors'] = np.log(df_visits_f['visitors'])

#print()
#model0 = smf.ols('visitors ~ C(air_store_id) + C(week) + C(day_of_week) + holiday_flg',
#                 data = df_visits_f).fit()

df_sample.set_index('air_store_id', inplace = True)
for x in ['min', 'max', 'mean']:
  df_visits_f['{:s}_vis'.format(x)] = (df_visits_f.groupby('air_store_id')
                                                  ['ln_visitors'].transform(x))
  df_sample['{:s}_vis'.format(x)] = (df_visits_f.groupby('air_store_id')
                                                ['ln_visitors'].agg(x))
df_sample.reset_index(inplace = True, drop = False)

df_sample.set_index(['air_store_id', 'day_of_week'], inplace = True)
df_visits_f['mean_dow_vis'] = (df_visits_f.groupby(['air_store_id', 'day_of_week'])
                                          ['ln_visitors'].transform('mean'))
df_sample['mean_dow_vis'] = (df_visits_f.groupby(['air_store_id', 'day_of_week'])
                                        ['ln_visitors'].agg('mean'))
df_sample.reset_index(inplace = True, drop = False)
# not always available...
df_sample.loc[df_sample['mean_dow_vis'].isnull(), 'mean_dow_vis'] = df_sample['mean_vis']

# Need same FE definition for (out of sample) predictions
# => prepare X for both first and cut => known / forecast
ls_expl_vars = ['air_store_id', 'week', 'day_of_week', 'holiday_flg', 'holiday_flg2',
                'mean_vis', 'max_vis', 'min_vis', 'mean_dow_vis']
dfX0 = df_visits_f[ls_expl_vars]
dfX1 = df_sample[ls_expl_vars]
dfX = pd.concat([dfX0, dfX1], ignore_index = True)

dfX = dfX.merge(df_stores[['air_store_id', 'air_genre_name', 'air_area_name']],
                on = 'air_store_id',
                how = 'left')

X = dmatrix('C(week) + C(air_genre_name) + C(air_area_name) + holiday_flg +  holiday_flg2 + '
            'min_vis + max_vis + mean_vis + mean_dow_vis', dfX)

X0 = X[:len(dfX0)]
X1 = X[len(dfX0):]
print()
print('Explanatory variables ready')

print()

#model0 = sm.OLS(np.log1p(df_visits_f['visitors']), X0).fit()

#from xgboost import XGBRegressor
#model0 = XGBRegressor()
#model0.fit(X0, np.log1p(df_visits_f['visitors'].values), verbose=False)

model0 = sm.OLS(np.log1p(df_visits_f['visitors'].values), X0).fit()

#model1 = ensemble.GradientBoostingRegressor(learning_rate=0.2, random_state=3)
#model1.fit(X0, np.log(df_visits_f['visitors'].values))

## read
#http://thedataconnoisseur.com/2017-12-03-predicting-housing-prices/
#https://machinelearningmastery.com/develop-first-xgboost-model-python-scikit-learn/
#https://datascience.stackexchange.com/questions/10943/why-is-xgboost-so-much-faster-than-sklearn-gradientboostingclassifier

# => should not build dummies a priori?

## cat var specification not fit? (or estimation to cumbersome?)
#model2= neighbors.KNeighborsRegressor(n_jobs=-1, n_neighbors=4)
#model2.fit(X0, np.log(df_visits_f['visitors']))

def RMSLE(y, pred):
    return metrics.mean_squared_error(y, pred)**0.5

# In sample RMSE
explained = model0.predict(X0)
df_visits_f['visitors_pred'] = np.expm1(explained) # round?
df_visits_f.loc[df_visits_f['visitors_pred'] < 0, 'visitors_pred'] = 0
print('Current RMSE: ', RMSLE(np.log1p(df_visits_f['visitors'].values),
                              np.log1p(df_visits_f['visitors_pred'].values)))

forecast = model0.predict(X1)
df_sample['visitors'] = forecast # round?
#del(res) # heavy on laptop
# caution: cannot have negative numbers of visitors
df_sample.loc[df_sample['visitors'] < 0, 'visitors'] = 0
df_sample[['id', 'visitors']].to_csv(os.path.join(path_kaggle, 'naive_forecast.csv'),
                                     index = False)

# todo:
# one computation per area (leikely enough except if not enough history for weeks..)
