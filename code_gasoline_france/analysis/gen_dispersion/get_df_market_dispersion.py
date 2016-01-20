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
                          parse_dates = True)
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

# #########################
# GET DF MARKET DISPERSION
# #########################

# PARAMETERS

df_prices = df_prices_cl
km_bound = 5

#ls_markets = get_ls_ls_market_ids(dict_ls_comp, km_bound)
#ls_markets_st = get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound)
#ls_markets_st_rd = get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound, True)

# GET MARKETS
dict_markets = {}
for km_bound in [1, 3, 5]:
  dict_markets['All_{:d}km'.format(km_bound)] =\
      get_ls_ls_market_ids(dict_ls_comp, km_bound)
  dict_markets['Restricted_{:d}km'.format(km_bound)] =\
      get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound)
  dict_markets['Restricted_{:d}km_random'.format(km_bound)] =\
      get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound, True)

# GET MARKET DISPERSION

ls_loop_markets = [('3 km - Raw prices', df_prices_ttc, dict_markets['All_3km']),
                   ('3 km - Residuals', df_prices_cl, dict_markets['All_3km']),
                   ('1 km - Residuals', df_prices_cl, dict_markets['All_1km']),
                   ('5 km - Residuals', df_prices_cl, dict_markets['All_5km']),
                   ('3 km Rest. - Residuals', df_prices_cl, dict_markets['Restricted_3km']),
                   ('Isolated markets - Residuals', df_prices_cl, ls_stable_markets)]

# for each market:
# market desc: (max) nb firms, mean nb firms observed,
# dispersion: mean- range / gfs / std / gfs
# finally: display mean and std over all markets
# alternatively: Tappata approach : mean over all market-days, not markets

ls_df_market_stats, ls_se_disp_mean, ls_se_disp_std = [], [], []
for title, df_prices, ls_markets_temp in ls_loop_markets:
  
  
  # Euros to cent
  df_prices = df_prices * 100

  # ls_markets_temp = ls_markets_st # Market definition chosen here (loop?)
  ls_df_market_dispersion = [get_market_price_dispersion(market_ids, df_prices)\
                               for market_ids in ls_markets_temp]
  se_mean_price = df_prices.mean(1)
  
  # cv useless when using residual prices (div by almost 0)
  ls_stats = ['range', 'gfs', 'std', 'cv', 'nb_comp', 'nb_comp_t']
  ls_ls_market_stats = []
  ls_market_ref_ids = []
  for ls_market_ids, df_market_dispersion in zip(ls_markets_temp, ls_df_market_dispersion):
    df_md = df_market_dispersion[(df_market_dispersion['nb_comp'] >= 3) &\
                                 (df_market_dispersion['nb_comp_t']/\
                                  df_market_dispersion['nb_comp'].astype(float)\
                                    >= 2.0/3)].copy()
    if len(df_md) > 90:
      df_md['id'] = ls_market_ids[0]
      df_md['price'] = se_mean_price
      df_md['date'] = df_md.index
      ls_ls_market_stats.append([df_md[field].mean()\
                                  for field in ls_stats] +\
                                [df_md[field].std()\
                                  for field in ls_stats] +\
                                [len(df_md)])
      ls_market_ref_ids.append(ls_market_ids[0])
  # Market stats draft
  ls_columns = ['avg_%s' %field for field in ls_stats]+\
               ['std_%s' %field for field in ls_stats]+\
               ['nb_obs']
  df_market_stats = pd.DataFrame(ls_ls_market_stats, ls_market_ref_ids, ls_columns)
  ls_df_market_stats.append(df_market_stats)
  
  #print()
  #print(title)
  # print(df_market_stats.describe())
  #
  #print u'\nStats des: restriction on nb of sellers:'
  #nb_comp_lim = df_market_stats['avg_nb_comp'].quantile(0.75)
  #print u'\n', df_market_stats[df_market_stats['avg_nb_comp'] <= nb_comp_lim].describe()
  #
  #df_dispersion = pd.concat(ls_df_market_dispersion, ignore_index = True)
  #df_dispersion = df_dispersion[(df_dispersion['nb_comp_t'] >= 3) &\
  #                              (df_dispersion['nb_comp_t']/\
  #                               df_dispersion['nb_comp'].astype(float) >= 2.0/3)]

  ls_se_disp_mean.append(df_market_stats[['avg_nb_comp',
                                          'avg_nb_comp_t',
                                          'avg_range',
                                          'avg_std',
                                          'avg_gfs']].median())
  ls_se_disp_std.append(df_market_stats[['avg_nb_comp',
                                         'avg_nb_comp_t',
                                         'avg_range',
                                         'avg_std',
                                         'avg_gfs']].std())
 
dict_df_disp = {}
for title, ls_se_disp_temp in [('Mean', ls_se_disp_mean),
                               ('Std',  ls_se_disp_std)]:
  df_disp_temp = pd.concat(ls_se_disp_temp,
                           axis = 1,
                           keys = [x[0] for x in ls_loop_markets])
  df_disp_temp.rename(index = {'avg_nb_comp' : 'Nb sellers (total)',
                               'avg_nb_comp_t' : 'Nb sellers (observed)',
                               'avg_range' : 'Range',
                               'avg_std' : 'Std',
                               'avg_gfs' : 'Gain from search'},
                      inplace = True)
  df_disp_temp.ix['Nb markets'] =\
    [len(df_market_stats) for df_market_stats in ls_df_market_stats]
  df_disp_temp.ix['Nb obs'] =\
    [df_market_stats['nb_obs'].sum() for df_market_stats in ls_df_market_stats]

  # todo: add total nb obs? need to save it in market stats

  dict_df_disp[title] = df_disp_temp
  
  print()
  print(title)
  print(df_disp_temp.to_string())

# #########
# OUPUT
# #########

## CSV
#
#df_ppd.to_csv(os.path.join(path_dir_built_csv,
#                           'df_pair_raw_price_dispersion.csv'),
#              encoding = 'utf-8',
#              index = False)
#
#df_rr.to_csv(os.path.join(path_dir_built_csv,
#                           'df_rank_reversals.csv'),
#              float_format= '%.3f',
#              encoding = 'utf-8',
#              index = 'pair_index')
#
## JSON
#
#enc_json(dict_rr_lengths, os.path.join(path_dir_built_json,
#                                       'dict_rr_lengths.json'))