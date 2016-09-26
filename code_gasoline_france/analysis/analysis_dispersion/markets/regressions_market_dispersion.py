#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built, u'data_json')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_built_dis = os.path.join(path_data,
                                  u'data_gasoline',
                                  u'data_built',
                                  u'data_dispersion')
path_dir_built_dis_csv = os.path.join(path_dir_built_dis, u'data_csv')
path_dir_built_dis_json = os.path.join(path_dir_built_dis, u'data_json')

path_dir_built_other = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_other')
path_dir_built_other_csv = os.path.join(path_dir_built_other, 'data_csv')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ################
# LOAD DATA
# ################

# DF INFO
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
                               'dpt' : str})
df_info.set_index('id_station', inplace = True)

# DF STATION STATS
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# DF MARGIN CHGE
df_margin_chge = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_margin_chge.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_margin_chge.set_index('id_station', inplace = True)

# COMPETITORS
dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# STABLE MARKETS
ls_dict_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                               'ls_dict_stable_markets.json'))
ls_robust_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                                 'ls_robust_stable_markets.json'))
# 0 is 3km, 1 is 4km, 2 is 5km
ls_stable_markets = [stable_market for nb_sellers, stable_markets\
                       in ls_dict_stable_markets[2].items()\
                          for stable_market in stable_markets]

# DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

# FILTER DATA
# exclude stations with insufficient (quality) price data
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'Corse')].index)))
#df_info = df_info.ix[ls_keep_ids]
#df_station_stats = df_station_stats.ix[ls_keep_ids]
#df_prices_ttc = df_prices_ttc[ls_keep_ids]
#df_prices_ht = df_prices_ht[ls_keep_ids]
#df_prices_cl = df_prices_cl[ls_keep_ids]

ls_drop_ids = list(set(df_prices_ttc.columns).difference(set(ls_keep_ids)))
df_prices_ttc[ls_drop_ids] = np.nan
df_prices_ht[ls_drop_ids] = np.nan
# highway stations may not be in df_prices_cl (no pbm here)
ls_drop_ids_nhw =\
  list(set(ls_drop_ids).difference(set(df_info[df_info['highway'] == 1].index)))
df_prices_cl[ls_drop_ids_nhw] = np.nan

# GEN LOW PRICE AND HIGH PRICE MARKETS
ls_discounter = ['ELF', 'ESSO_EXPRESS', 'TOTAL_ACCESS']
df_info.loc[df_info['brand_last'].isin(ls_discounter),
             'group_type_last'] = 'DIS'
df_info.loc[(df_info['brand_0'].isin(ls_discounter)) |\
            (df_info['brand_last'] == 'ESSO_EXPRESS'),
             'group_type'] = 'DIS'
# should exclude margin chge stations?

df_info['type_last'] = 'HIGH'
df_info.loc[(df_info['brand_last'].isin(ls_discounter)) |\
            (df_info['group_type_last'] == 'SUP'),
            'type_last'] = 'LOW'
df_info['type'] = 'HIGH'
df_info.loc[(df_info['brand_0'].isin(ls_discounter)) |\
            (df_info['brand_last'] == 'ESSO_EXPRESS') |\
            (df_info['group_type'] == 'SUP'),
            'type'] = 'LOW'

set_low_ids = set(df_info[(df_info['type'] == 'LOW') & (df_info['type_last'] == 'LOW')].index)
set_high_ids = set(df_info[(df_info['type'] == 'HIGH') & (df_info['type_last'] == 'HIGH')].index)
dict_ls_comp_low, dict_ls_comp_high = {}, {}
for k, v in dict_ls_comp.items():
  if k in set_low_ids:
    dict_ls_comp_low[k] = [(id_comp, dist) for id_comp, dist in v if id_comp in set_low_ids]
  elif k in set_high_ids:
    dict_ls_comp_high[k] = [(id_comp, dist) for id_comp, dist in v if id_comp in set_high_ids]
# could gain efficiency by restricting distance first and using set intersections

# GET MARKETS
dict_markets = {}
for km_bound in [1, 3, 5]:
  dict_markets['All_{:d}km'.format(km_bound)] =\
      get_ls_ls_market_ids(dict_ls_comp, km_bound)
  dict_markets['Restricted_{:d}km'.format(km_bound)] =\
      get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound)
  dict_markets['Restricted_{:d}km_random'.format(km_bound)] =\
      get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound, True)
  dict_markets['Low_{:d}km'.format(km_bound)] =\
      get_ls_ls_market_ids(dict_ls_comp_low, km_bound)
  dict_markets['High_{:d}km'.format(km_bound)] =\
      get_ls_ls_market_ids(dict_ls_comp_high, km_bound)

# GET MARKET DISPERSION
ls_loop_markets = [('3km_Raw_prices', df_prices_ttc, dict_markets['All_3km']),
                   ('3km_Residuals', df_prices_cl, dict_markets['All_3km']),
                   ('1km_Residuals', df_prices_cl, dict_markets['All_1km']),
                   ('5km_Raw_prices', df_prices_ttc, dict_markets['All_5km']),
                   ('5km_Residuals', df_prices_cl, dict_markets['All_5km']),
                   ('3km_Rest_Residuals', df_prices_cl, dict_markets['Restricted_3km']),
                   ('Stable_Markets_Raw_prices', df_prices_ttc, ls_stable_markets),
                   ('Stable_Markets_Residuals', df_prices_cl, ls_stable_markets),
                   ('Low_3km', df_prices_ttc, dict_markets['Low_3km']),
                   ('High_3km', df_prices_ttc, dict_markets['High_3km']),
                   ('Low_3km_Residuals', df_prices_cl, dict_markets['Low_3km']),
                   ('High_3km_Residuals', df_prices_cl, dict_markets['High_3km'])]

# DROP MARKETS WITH MARGIN CHGE (CENTER OR IN)
margin_chge_bound = 0.03
ls_ids_margin_chge =\
  df_margin_chge[df_margin_chge['value'].abs() >= margin_chge_bound].index
dict_ls_comp_3km = {x : [y[0] for y in ls_y if y[1] <= 3]\
                        for x, ls_y in dict_ls_comp.items()}
ls_drop_3km = [x for x, ls_y in dict_ls_comp_3km.items()\
                 if set(ls_y).intersection(set(ls_ids_margin_chge))]
ls_drop_3km = list(set(ls_drop_3km).union(ls_ids_margin_chge))

## Can avoid generating markets every time
#dict_df_mds = {}
#for title, df_prices, ls_markets_temp in ls_loop_markets:
#  dict_df_mds[title] =\
#    pd.read_csv(os.path.join(path_dir_built_dis_csv,
#                             'df_market_dispersion_{:s}.csv'.format(title)),
#                encoding = 'utf-8',
#                parse_dates = ['date'],
#                dtype = {'id' : str})
#df_md = dict_df_mds[ls_loop_markets[5][0]].copy()

# paper regressions: 0, 1, 6, 7, 8, 9 (or 10, 11?)
title = ls_loop_markets[-1][0]
print(title)
df_md = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                 'df_market_dispersion_{:s}.csv'.format(title)),
                    encoding = 'utf-8',
                    parse_dates = ['date'],
                    dtype = {'id' : str})

## Restrict to one or two day(s) per week: robustness checks
#df_md.set_index('date', inplace = True)
#df_md['dow'] = df_md.index.dayofweek
#df_md.reset_index(drop = False, inplace = True)
#df_md = df_md[(df_md['dow'] == 2) |(df_md['dow'] == 4)] # Friday

# need to get rid of nan to be able to cluster
df_md = df_md[~df_md['cost'].isnull()]
df_md['str_date'] = df_md['date'].apply(lambda x: x.strftime('%Y%m%d'))
df_md['int_date'] = df_md['str_date'].astype(int)
df_md['int_id'] = df_md['id'].astype(int)

# drop if margin chge around
df_md = df_md[~df_md['id'].isin(ls_drop_3km)]

# loop on each period
for title_temp, df_temp in [['All', df_md],
                            ['Before', df_md[df_md['date'] <= '2012-07-01']],
                            ['After', df_md[df_md['date'] >= '2013-02-01']]]:
  
  df_temp = df_temp.copy()
  df_temp['trend']= range(len(df_temp))

  print()
  print('-'*60)
  print(title_temp)
  print()
  print('Range')
  res_range = smf.ols('range ~ cost + nb_comp + trend',
                 data = df_temp).fit()
  res_range = res_range.get_robustcov_results(cov_type = 'cluster',
                                              groups = df_temp[['int_id', 'int_date']].values,
                                              use_correction = True)
  print(res_range.summary())

  #cov2g_range =\
  #  sm.stats.sandwich_covariance.cov_cluster_2groups(res_range,
  #                                                   df_temp['int_id'],
  #                                                   group2 = df_temp['int_date'])
  #var_range = np.sqrt(np.diagonal(cov2g_range[0]))
  #tval_range = (res_range.params / var_range).values
  #pval_range = scipy.stats.t.sf(np.abs(tval_range), res_range.nobs - 1)*2
  ## todo: check computation of p values
  #print('var  : ' + ' '.join(['{:7.4f};'.format(x) for x in var_range]))
  #print('t-val: ' + ' '.join(['{:7.4f};'.format(x) for x in tval_range]))
  #print('p-val: ' + ' '.join(['{:7.4f};'.format(x) for x in pval_range]))
  
  print()
  print('Std')
  res_std = smf.ols('std ~ cost + nb_comp + trend',
                 data = df_temp).fit()
  res_std = res_std.get_robustcov_results(cov_type = 'cluster',
                                          groups = df_temp[['int_id', 'int_date']].values,
                                          use_correction = True)
  print(res_std.summary())
  
  #cov2g_std =\
  #  sm.stats.sandwich_covariance.cov_cluster_2groups(res_std,
  #                                                   df_temp['int_id'],
  #                                                   group2 = df_temp['int_date'])
  #var_std = np.sqrt(np.diagonal(cov2g_std[0]))
  #tval_std = (res_std.params / var_std).values
  #pval_std = scipy.stats.t.sf(np.abs(tval_std), res_std.nobs - 1)*2
  ## todo: check computation of p values
  #print('var  : ' +  ' '.join(['{:7.4f};'.format(x) for x in var_std]))
  #print('t-val: ' + ' '.join(['{:7.4f};'.format(x) for x in tval_std]))
  #print('p-val: ' + ' '.join(['{:7.4f};'.format(x) for x in pval_std]))


# toco: check if loss of signif. on cost using friday only due to insuff vars in cost?
# todo: check if there are markets with supermarkets / no supermarkets?
