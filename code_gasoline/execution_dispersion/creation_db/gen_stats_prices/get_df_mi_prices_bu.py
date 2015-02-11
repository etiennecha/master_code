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



## ASSEMBLE PRICES/BRANDS INTO ONE DF (MI?) PRICES
#
### Pbms with Memory
##df_prices_ht = df_prices_ht.T.stack(dropna = False)
##df_brands_1 = pd.DataFrame(ls_ls_ls_brands[0], master_price['ids'], ls_columns).stack(dropna = False)
##df_mi_agg = pd.DataFrame({'price_ht' : df_prices_ht, 'brand_1': df_brands_1})
##del(ls_ls_ls_brands, df_prices_ttc, df_prices_ht, df_brands_1)
##df_mi_agg.rename(index={0:'id', 1:'date'}, inplace = True)
#
#ls_all_prices = df_prices_ht.T.stack(dropna=False).values
#ls_all_ids = [id_indiv for id_indiv in master_price['ids'] for x in range(len(master_price['dates']))]
#ls_all_dates = [date for id_indiv in master_price['ids'] for date in master_price['dates']]
#ls_ls_all_brands = [[brand for ls_brands in ls_ls_brands for brand in ls_brands]\
#                      for ls_ls_brands in ls_ls_ls_brands]
#index = pd.MultiIndex.from_tuples(zip(ls_all_ids, ls_all_dates), names= ['id','date'])
#columns = ['price', 'brand_1', 'brand_2', 'brand_type']
#df_mi_prices = pd.DataFrame(zip(*[ls_all_prices] + ls_ls_all_brands),
#                            index = index,
#                            columns = columns)
#
## ############
## FINAL MERGE
## ############
## (check that) both df are sorted
#df_mi_prices = df_mi_prices.reset_index()
#df_final = df_mi_prices.join(df_info, on = 'id', lsuffix = '_a')
#
#path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')
#df_final.to_csv(os.path.join(path_dir_built_csv, 'price_panel_data.csv'),
#                float_format='%.4f',
#                encoding='utf-8')
#
## ############
## REGRESSIONS
## ############
#
## Restrict df_final...
#df_final['code_geo'][pd.isnull(df_final['code_geo'])] =  ''
#df_final = df_final[~(df_final['highway'] == 1) &\
#                    ~(df_final['code_geo'].str.startswith('2A')) &\
#                    ~(df_final['code_geo'].str.startswith('2B'))]

#http://nbviewer.ipython.org/urls/s3.amazonaws.com/datarobotblog/notebooks/multiple_regression_in_python.ipynb

## General price cleaning .. Memory error at work
#res01 = smf.ols('price ~ C(date) + C(id)', data = df_final, missing = 'drop').fit()

## Try with 2011 only... memory error at work too
#res02 = smf.ols('price ~ C(date) + C(id)',\
#                data = df_final[df_final['date'].str.startswith('2011')],\
#                missing = 'drop').fit()

# Subset dpt 92 (exclude null code_geo so far: should exclude only full series)
#df_final = df_final[~pd.isnull(df_final['code_geo'])]
#res03 = smf.ols('price ~ C(date) + C(id)',\
#                data = df_final[df_final['code_geo'].str.startswith('92')],\
#                missing = 'drop').fit()
#df_final['cleaned_price'] = np.nan
#df_final['cleaned_price'][(df_final['code_geo'].str.startswith('92')) &\
#                          (~pd.isnull(df_final['price']))] = res03.fittedvalues
# df_final[['price', 'cleaned_price']][df_final['id'] == '92160003'].plot()

# (check that) all ids are matched (generalize...)

## With Panel data
#df_mi_final = df_final.set_index(['id', 'date'])
#
#from patsy import dmatrices
#from panel import *
#import pprint
#f = 'price~brand_2'
#y, X = dmatrices(f, df_mi_final, return_type='dataframe')
#mod1 = PanelLM(y, X, method='pooling').fit()
#pprint.pprint(zip(X.columns, mod1.params, mod1.bse))

# FOR UPDATE...

## TODO: restrict size to begin with (time/location)
## pd_mi_final.ix['1500007',:] # based on id
## pd_mi_final[pd_mi_final['code_geo'].str.startswith('01', na=False)] # based on insee
## http://stackoverflow.com/questions/17242970/multi-index-sorting-in-pandas
#pd_mi_final_alt = pd_mi_final.swaplevel('id', 'date')
#pd_mi_final_alt = pd_mi_final_alt.sort()
#pd_mi_final_extract = pd_mi_final_alt.ix['20110904':'20111004']
  
# # EXAMPLE PANEL DATA REGRESSIONS
# from patsy import dmatrices
# f = 'price~brand_2'
# y, X = dmatrices(f, pd_mi_final_extract, return_type='dataframe')
# sys.path.append(r'W:\Bureau\Etienne_work\Code\code_gasoline\code_gasoline_db_analysis\code_panel_regressions')
# from panel import *
# mod1 = PanelLM(y, X, method='pooling').fit()
# mod2 = PanelLM(y, X, method='between').fit()
# mod3 = PanelLM(y, X.ix[:,1:], method='within').fit()
# mod4 = PanelLM(y, X.ix[:,1:], method='within', effects='time').fit()
# mod5 = PanelLM(y, X.ix[:,1:], method='within', effects='twoways').fit()
# mod6 = PanelLM(y, X, 'swar').fit()
# mn = ['OLS', 'Between', 'Within N', 'Within T', 'Within 2w', 'RE-SWAR']
# results = [mod1, mod2, mod3, mod4, mod5, mod6]
# # Base group: Agip
# # Equivalent to Stata FE is Within N (Within T: time effect...)
# for i, result in enumerate(results):
  # print mn[i]
  # if len(X.columns) == len(result.params):
    # pprint.pprint(zip(X.columns, result.params, result.bse))
  # else:
    # pprint.pprint(zip(X.columns[1:], result.params, result.bse))

# pprint.pprint(zip(map(lambda x: '{:<28}'.format(x[:25]), X.columns),
                  # map(lambda x: '{:8.3f}'.format(x), np.round(mod1.params,3).tolist()),
                  # map(lambda x: '{:8.3f}'.format(x), np.round(mod1.bse,3).tolist())))

## http://stackoverflow.com/questions/17242970/multi-index-sorting-in-pandas
  
# # EXAMPLE PANEL DATA REGRESSIONS
# from patsy import dmatrices
# f = 'price~brand_2'
# y, X = dmatrices(f, pd_mi_final_extract, return_type='dataframe')
# sys.path.append(r'W:\Bureau\Etienne_work\Code\code_gasoline\code_gasoline_db_analysis\code_panel_regressions')
# from panel import *
# mod1 = PanelLM(y, X, method='pooling').fit()
# mod2 = PanelLM(y, X, method='between').fit()
# mod3 = PanelLM(y, X.ix[:,1:], method='within').fit()
# mod4 = PanelLM(y, X.ix[:,1:], method='within', effects='time').fit()
# mod5 = PanelLM(y, X.ix[:,1:], method='within', effects='twoways').fit()
# mod6 = PanelLM(y, X, 'swar').fit()
# mn = ['OLS', 'Between', 'Within N', 'Within T', 'Within 2w', 'RE-SWAR']
# results = [mod1, mod2, mod3, mod4, mod5, mod6]
# # Base group: Agip
# # Equivalent to Stata FE is Within N (Within T: time effect...)
# for i, result in enumerate(results):
  # print mn[i]
  # if len(X.columns) == len(result.params):
    # pprint.pprint(zip(X.columns, result.params, result.bse))
  # else:
    # pprint.pprint(zip(X.columns[1:], result.params, result.bse))

# pprint.pprint(zip(map(lambda x: '{:<28}'.format(x[:25]), X.columns),
                  # map(lambda x: '{:8.3f}'.format(x), np.round(mod1.params,3).tolist()),
                  # map(lambda x: '{:8.3f}'.format(x), np.round(mod1.bse,3).tolist())))

# TODO: compute price_ht based on dpt... (add categorical variable in df_info)
