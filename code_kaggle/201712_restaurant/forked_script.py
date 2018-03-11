"""
Contributions from:
DSEverything - Mean Mix - Math, Geo, Harmonic (LB 0.493) 
https://www.kaggle.com/dongxu027/mean-mix-math-geo-harmonic-lb-0-493
JdPaletto - Surprised Yet? - Part2 - (LB: 0.503)
https://www.kaggle.com/jdpaletto/surprised-yet-part2-lb-0-503
hklee - weighted mean comparisons, LB 0.497, 1ST
https://www.kaggle.com/zeemeen/weighted-mean-comparisons-lb-0-497-1st

Also all comments for changes, encouragement, and forked scripts rock

Keep the Surprise Going
"""

import add_to_path
from add_to_path import path_data
import os, sys
import glob, re
import numpy as np
import pandas as pd
from sklearn import *
from datetime import datetime

path_kaggle = os.path.join(path_data,
                          'data_kaggle',
                          '201712_restaurant')

data = {
    'tra': pd.read_csv(os.path.join(path_kaggle, 'air_visit_data.csv.zip')),
    'as' : pd.read_csv(os.path.join(path_kaggle, 'air_store_info.csv.zip')),
    'hs' : pd.read_csv(os.path.join(path_kaggle, 'hpg_store_info.csv.zip')),
    'ar' : pd.read_csv(os.path.join(path_kaggle, 'air_reserve.csv.zip')),
    'hr' : pd.read_csv(os.path.join(path_kaggle, 'hpg_reserve.csv.zip')),
    'id' : pd.read_csv(os.path.join(path_kaggle, 'store_id_relation.csv.zip')),
    'tes': pd.read_csv(os.path.join(path_kaggle, 'sample_submission.csv.zip')),
    'hol': pd.read_csv(os.path.join(path_kaggle, 'date_info.csv.zip')).rename(
             columns={'calendar_date':'visit_date'})
    }

data['hr'] = pd.merge(data['hr'], data['id'], how='inner', on=['hpg_store_id'])

# RESERVATIONS PER DATE: NB AND DELAY
for df in ['ar','hr']:
    data[df]['visit_datetime'] = pd.to_datetime(data[df]['visit_datetime']).dt.date
    data[df]['reserve_datetime'] = pd.to_datetime(data[df]['reserve_datetime']).dt.date
    data[df]['reserve_datetime_diff'] = data[df].apply(
                                          lambda r: (r['visit_datetime'] - r['reserve_datetime']).days, axis=1)
    temp0 = (data[df].rename(columns = {'visit_datetime' : 'visit_date'})
                     .groupby(['air_store_id', 'visit_date'])
                     .agg({'reserve_datetime_diff' : ['sum', 'mean'],
                           'reserve_visitors' : ['sum', 'mean']}))
    temp0.columns = ['_'.join(col).strip() for col in temp0.columns.values]
    temp0.reset_index(drop = False, inplace = True)
    temp0.rename(columns = {'reserve_datetime_diff_sum' : 'rs1',
                            'reserve_visitors_sum' : 'rv1',
                            'reserve_datetime_diff_mean' : 'rs2',
                            'reserve_visitors_mean' : 'rv2'}, inplace = True)
    data[df] = temp0

data['tes']['visit_date'] = data['tes']['id'].map(lambda x: str(x).split('_')[2])
data['tes']['air_store_id'] = data['tes']['id'].map(lambda x: '_'.join(x.split('_')[:2]))

for alias in ['tra', 'tes']:
  data[alias]['visit_date'] = pd.to_datetime(data[alias]['visit_date'])
  data[alias]['dow'] = data[alias]['visit_date'].dt.dayofweek
  data[alias]['year'] = data[alias]['visit_date'].dt.year
  data[alias]['month'] = data[alias]['visit_date'].dt.month
  data[alias]['visit_date'] = data[alias]['visit_date'].dt.date

# DF WITH STATS BY STORE / DAY OF WEEK
unique_stores = data['tes']['air_store_id'].unique()
stores = pd.concat([pd.DataFrame({'air_store_id': unique_stores,
                                  'dow': [i]*len(unique_stores)}) for i in range(7)],
                   axis=0, ignore_index=True).reset_index(drop=True)
store_dow_stats = (data['tra'].groupby(['air_store_id','dow'])['visitors']
                              .agg(['min', 'mean', 'median', 'max', 'count'])
                              .reset_index(drop = False))
stores = pd.merge(stores, store_dow_stats, how='left', on=['air_store_id','dow'])
stores = pd.merge(stores, data['as'], how='left', on=['air_store_id'])

lbl = preprocessing.LabelEncoder()

## LENGTH OF GENRE/AREA CONTENT?
#stores['air_genre_name'] = stores['air_genre_name'].map(lambda x: str(str(x).replace('/',' ')))
#stores['air_area_name'] = stores['air_area_name'].map(lambda x: str(str(x).replace('-',' ')))
#for i in range(10):
#    stores['air_genre_name'+str(i)] = (
#      lbl.fit_transform(stores['air_genre_name'].map(lambda x: str(str(x).split(' ')[i])
#                                                               if len(str(x).split(' '))>i else '')))
#    stores['air_area_name'+str(i)] = (
#      lbl.fit_transform(stores['air_area_name'].map(lambda x: str(str(x).split(' ')[i])
#                                                              if len(str(x).split(' '))>i else '')))
stores['air_genre_name'] = lbl.fit_transform(stores['air_genre_name'])
stores['air_area_name'] = lbl.fit_transform(stores['air_area_name'])

data['hol']['visit_date'] = pd.to_datetime(data['hol']['visit_date'])
data['hol']['day_of_week'] = lbl.fit_transform(data['hol']['day_of_week'])
data['hol']['visit_date'] = data['hol']['visit_date'].dt.date
train = pd.merge(data['tra'], data['hol'], how='left', on=['visit_date']) 
test = pd.merge(data['tes'], data['hol'], how='left', on=['visit_date']) 

train = pd.merge(train, stores, how='left', on=['air_store_id','dow']) 
test = pd.merge(test, stores, how='left', on=['air_store_id','dow'])

for df in ['ar','hr']:
    train = pd.merge(train, data[df], how='left', on=['air_store_id','visit_date']) 
    test = pd.merge(test, data[df], how='left', on=['air_store_id','visit_date'])

#train['id'] = train.apply(lambda r: '_'.join([str(r['air_store_id']), str(r['visit_date'])]), axis=1)
#
#train['total_reserv_sum'] = train['rv1_x'] + train['rv1_y']
#train['total_reserv_mean'] = (train['rv2_x'] + train['rv2_y']) / 2
#train['total_reserv_dt_diff_mean'] = (train['rs2_x'] + train['rs2_y']) / 2
#
#test['total_reserv_sum'] = test['rv1_x'] + test['rv1_y']
#test['total_reserv_mean'] = (test['rv2_x'] + test['rv2_y']) / 2
#test['total_reserv_dt_diff_mean'] = (test['rs2_x'] + test['rs2_y']) / 2

## DATE => how is it treated in GBR / KN?
#train['date_int'] = train['visit_date'].apply(lambda x: x.strftime('%Y%m%d')).astype(int)
#test['date_int'] = test['visit_date'].apply(lambda x: x.strftime('%Y%m%d')).astype(int)
## GPS coord?
#train['var_max_lat'] = train['latitude'].max() - train['latitude']
#train['var_max_long'] = train['longitude'].max() - train['longitude']
#test['var_max_lat'] = test['latitude'].max() - test['latitude']
#test['var_max_long'] = test['longitude'].max() - test['longitude']
#train['lon_plus_lat'] = train['longitude'] + train['latitude'] 
#test['lon_plus_lat'] = test['longitude'] + test['latitude']

ls_drop_cols = ['rv1_x', 'rv2_x', 'rs1_x', 'rs2_x',
                'rv1_y', 'rv2_y', 'rs1_y', 'rs2_y',
                'latitude', 'longitude']
train.drop(ls_drop_cols, axis = 1, inplace = True)
test.drop(ls_drop_cols, axis = 1, inplace = True)

lbl = preprocessing.LabelEncoder()
train['air_store_id2'] = lbl.fit_transform(train['air_store_id'])
test['air_store_id2'] = lbl.transform(test['air_store_id'])

col = [c for c in train if c not in ['id', 'air_store_id', 'visit_date','visitors']]
train = train.fillna(-1)
test = test.fillna(-1)

def RMSLE(y, pred):
    return metrics.mean_squared_error(y, pred)**0.5
    
model1 = ensemble.GradientBoostingRegressor(learning_rate=0.2, random_state=3)
model2 = neighbors.KNeighborsRegressor(n_jobs=-1, n_neighbors=4)
model1.fit(train[col], np.log1p(train['visitors'].values))
model2.fit(train[col], np.log1p(train['visitors'].values))
print('RMSE GradientBoostingRegressor: ', RMSLE(np.log1p(train['visitors'].values),
                                                model1.predict(train[col])))
print('RMSE KNeighborsRegressor: ', RMSLE(np.log1p(train['visitors'].values),
                                          model2.predict(train[col])))
#test['visitors'] = (model1.predict(test[col]) + model2.predict(test[col])) / 2
test['visitors'] = model2.predict(test[col])
test['visitors'] = np.expm1(test['visitors']).clip(lower=0.)
sub1 = test[['id','visitors']].copy()
#del train; del data;

sub1[['id', 'visitors']].to_csv(os.path.join(path_kaggle, 'naive_forecast2.csv'),
                                index = False)

from xgboost import XGBRegressor
model3 = XGBRegressor()
model3.fit(train[col], np.log1p(train['visitors'].values), verbose=False)
print('XGBRegressor: ', RMSLE(np.log1p(train['visitors'].values),
                              model3.predict(train[col])))

## from hklee
## https://www.kaggle.com/zeemeen/weighted-mean-comparisons-lb-0-497-1st/code
#dfs = { re.search('/([^/\.]*)\.csv', fn).group(1):
#    pd.read_csv(fn)for fn in glob.glob('../input/*.csv')}
#
#for k, v in dfs.items(): locals()[k] = v
#
#wkend_holidays = date_info.apply(
#    (lambda x:(x.day_of_week=='Sunday' or x.day_of_week=='Saturday') and x.holiday_flg==1), axis=1)
#date_info.loc[wkend_holidays, 'holiday_flg'] = 0
#date_info['weight'] = ((date_info.index + 1) / len(date_info)) ** 5  
#
#visit_data = air_visit_data.merge(date_info, left_on='visit_date', right_on='calendar_date', how='left')
#visit_data.drop('calendar_date', axis=1, inplace=True)
#visit_data['visitors'] = visit_data.visitors.map(pd.np.log1p)
#
#wmean = lambda x:( (x.weight * x.visitors).sum() / x.weight.sum() )
#visitors = visit_data.groupby(['air_store_id', 'day_of_week', 'holiday_flg']).apply(wmean).reset_index()
#visitors.rename(columns={0:'visitors'}, inplace=True) # cumbersome, should be better ways.
#
#sample_submission['air_store_id'] = sample_submission.id.map(lambda x: '_'.join(x.split('_')[:-1]))
#sample_submission['calendar_date'] = sample_submission.id.map(lambda x: x.split('_')[2])
#sample_submission.drop('visitors', axis=1, inplace=True)
#sample_submission = sample_submission.merge(date_info, on='calendar_date', how='left')
#sample_submission = sample_submission.merge(visitors, on=[
#    'air_store_id', 'day_of_week', 'holiday_flg'], how='left')
#
#missings = sample_submission.visitors.isnull()
#sample_submission.loc[missings, 'visitors'] = sample_submission[missings].merge(
#    visitors[visitors.holiday_flg==0], on=('air_store_id', 'day_of_week'), 
#    how='left')['visitors_y'].values
#
#missings = sample_submission.visitors.isnull()
#sample_submission.loc[missings, 'visitors'] = sample_submission[missings].merge(
#    visitors[['air_store_id', 'visitors']].groupby('air_store_id').mean().reset_index(), 
#    on='air_store_id', how='left')['visitors_y'].values
#
#sample_submission['visitors'] = sample_submission.visitors.map(pd.np.expm1)
#sub2 = sample_submission[['id', 'visitors']].copy()
#sub_merge = pd.merge(sub1, sub2, on='id', how='inner')
#
#sub_merge['visitors'] = (sub_merge['visitors_x'] + sub_merge['visitors_y']* 1.1)/2
#sub_merge[['id', 'visitors']].to_csv('submission.csv', index=False)
