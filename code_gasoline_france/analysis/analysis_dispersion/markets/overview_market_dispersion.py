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
# pbm with chging discounters btw...
# (check with describe / hist if ok over time...)
# GEN LOW PRICE AND HIGH PRICE MARKETS
# todo check 95230007
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

# paper regressions: 0, 1, 6, 7
# todo: before and after govt intervention?

# #############
# LOAD DATA
# #############

dict_df_md = {}
ls_titles, dict_stats_des = [], {}
for x in [0, 1, 3, 4, 6, 7, 8, 9, 10, 11]:
  title = ls_loop_markets[x][0]
  ls_titles.append(title)
  df_md = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                   'df_market_dispersion_{:s}.csv'.format(title)),
                      encoding = 'utf-8',
                      parse_dates = ['date'],
                      dtype = {'id' : str})
  
  ## Restrict to one day per week: robustness checks
  #df_md.set_index('date', inplace = True)
  #df_md['dow'] = df_md.index.dayofweek
  #df_md.reset_index(drop = False, inplace = True)
  #df_md = df_md[df_md['dow'] == 4] # Friday
  
  ## Not necessary... can hide later
  #if 'Residuals' in title:
  #  df_md.drop(['cv'], axis = 1, inplace = True)
  
  dict_df_md[title] = df_md

# ###############
# STATS DES
# ###############

lsd_agg = ['Nb obs',
           'Nb markets',
           'nb_comp',
           'nb_comp_t',
           'range',
           'std',
           'gfs']

# Stats des by market def / price (general)
ls_titles, ls_se_mean, ls_se_std, = [], [], []
for x in [0, 1, 3, 4, 6, 7, 8, 9, 10, 11]:
  title = ls_loop_markets[x][0]
  df_md = dict_df_md[title]
  nb_obs = len(df_md)
  se_mean = df_md[lsd_agg[2:]].mean()
  se_mean.ix['Nb obs'] = nb_obs
  se_mean.ix['Nb markets'] = len(df_md['id'].unique())
  se_std = df_md[lsd_agg[2:]].std()
  se_std.ix['Nb obs'] = nb_obs
  se_std.ix['Nb markets'] = len(df_md['id'].unique())
  ls_titles.append(title)
  ls_se_mean.append(se_mean)
  ls_se_std.append(se_std)

df_mean = pd.concat(ls_se_mean,
                     axis = 1,
                     keys = ls_titles)

df_std = pd.concat(ls_se_std,
                     axis = 1,
                     keys = ls_titles)

print('Stats overall')
print()
print('mean')
print(df_mean.ix[lsd_agg].to_string())
print()
print('std')
print(df_std.ix[lsd_agg].to_string())

# Stats des by market def / price and market

ls_titles_2 = []
dict_stats_des = {}
for x in [0, 1, 3, 4, 6, 7, 8, 9, 10, 11]:
  title = ls_loop_markets[x][0]
  df_md = dict_df_md[title]
  # Stats des: groupby id to compute mean/std for each
  df_md_mean = df_md.groupby('id').agg('mean')
  ## Not taking market first: keep df_md
  #df_md_mean = df_md
  df_md_mean_desc = df_md_mean.describe()
  for stat in ['mean', 'std']:
    # caution: starts by taking mean for each market
    se_agg_stat = df_md_mean_desc.ix[stat]
    se_agg_stat.ix['Nb markets'] = len(df_md_mean)
    se_agg_stat.ix['Nb obs'] = len(df_md)
    dict_stats_des.setdefault(stat, []).append(se_agg_stat)
  ls_titles_2.append(title)

print()
print('Stats: by market')
for stat in ['mean', 'std']:
  print()
  print(stat)
  df_stat = pd.concat(dict_stats_des[stat],
                      axis = 1,
                      keys = ls_titles_2)
  print(df_stat.ix[lsd_agg].to_string())

#print(se_agg_mean[lsd_agg].to_string())

## MARKET STATS BY TYPE
#
## todo: add check for margin change?
#ls_rows_su_sm = []
#for ls_ids in ls_stable_markets:
#  df_ids = df_info.ix[ls_ids]
#  ls_ids_high = df_ids[df_ids['type_last'] == 'HIGH'].index
#  ls_ids_low = df_ids[df_ids['type_last'] == 'LOW'].index
#  ls_rows_su_sm.append((len(ls_ids), len(ls_ids_high), len(ls_ids_low)))
#
#df_su_sm = pd.DataFrame(ls_rows_su_sm,
#                        columns = ['nb_tot', 'nb_high', 'nb_low'])
#
## todo overview and fix
## e.g
## df_prices_ttc[ls_stable_markets[74]].plot()
## df_prices_ttc['43210002'].ix['2013-02':'2013-07'].plot()
## df_prices_ttc['43210002'].ix['2013-03-18':'2013-06'] = np.nan
