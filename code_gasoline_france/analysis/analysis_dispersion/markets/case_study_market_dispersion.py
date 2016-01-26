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

# ##############
# STATS DES
# ##############

# PLOT ECDF OF CLEANED PRICES

# Not necessarily at market level

from statsmodels.distributions.empirical_distribution import ECDF

ls_market_ids = ls_markets_temp[0]

# All prices
x = np.linspace(np.nanmin(df_prices_cl[ls_market_ids]),\
                np.nanmax(df_prices_cl[ls_market_ids]), num=100)
ax = plt.subplot()
for indiv_id in ls_market_ids:
  ecdf = ECDF(df_prices_cl[indiv_id])
  y = ecdf(x)
  ax.step(x, y, label = indiv_id)
plt.legend()
plt.title('Cleaned prices CDFs')
plt.show()

# Excluding extreme values
x = np.linspace(df_prices_cl[ls_market_ids].quantile(0.95).max(),\
                df_prices_cl[ls_market_ids].quantile(0.05).min(), num=200)
f, ax = plt.subplots()
for indiv_id in ls_market_ids:
  min_quant = df_prices_cl[indiv_id].quantile(0.05)
  max_quant = df_prices_cl[indiv_id].quantile(0.95)
  se_prices = df_prices_cl[indiv_id][(df_prices_cl[indiv_id] >= min_quant) &\
                                    (df_prices_cl[indiv_id] <= max_quant)]
  print(indiv_id, len(df_prices_cl[indiv_id]), len(se_prices))
  ecdf = ECDF(se_prices)
  y = ecdf(x)
  ax.step(x, y, label = indiv_id)
plt.legend()
plt.title('Cleaned prices CDFs')
plt.show()

# CASE STUDY FOR SPECIFIC MARKET

# todo: generalize? robust vs. global analysis

for x in ls_markets_temp:
  if len(x) == 5:
    ls_market_ids = x
    break

# typically: pbm with a change in price policy
df_prices_ttc[ls_market_ids].plot()
plt.show()

#ls_market.remove('9200003')

ls_df_market_stats = []
for df_pr in [df_prices_ttc, df_prices_cl]:
  df_mkt_prices = df_pr[ls_market_ids].copy()
  df_md = pd.concat([df_mkt_prices.max(1),
                     df_mkt_prices.min(1),
                     df_mkt_prices.mean(1),
                     df_mkt_prices.std(1, ddof = 0)],
                    keys = ['max', 'min', 'mean', 'std'],
                    axis = 1)
  df_md['range'] = df_md['max'] - df_md['min']
  df_md['cv'] = df_md['std'] / df_md['mean']
  ls_mc_dates = [df_margin_chge['date'].ix[id_station] for id_station in ls_market_ids\
                   if id_station in df_margin_chge.index]
  if ls_mc_dates:
    ls_mc_dates.sort()
    df_md = df_md[:ls_mc_dates[0]]
  ls_df_market_stats.append(df_md)

df_market_stats = ls_df_market_stats[0]

print(smf.ols('range ~ mean', missing = 'drop', data = df_market_stats).fit().summary())
df_market_stats['mean_price_var'] = df_market_stats['mean'] - df_market_stats['mean'].shift(1)
df_market_stats['mean_price_var_abs'] = np.abs(df_market_stats['mean_price_var'])

print(smf.ols('range ~ mean_price_var',
              missing = 'drop',
              data = df_market_stats).fit().summary())

df_market_stats['mean_price_var_pos'] = 0
df_market_stats.loc[df_market_stats['mean_price_var'] > 1e-10,
                    'mean_price_var_pos'] = df_market_stats['mean_price_var']
df_market_stats['mean_price_var_neg'] = 0
df_market_stats.loc[df_market_stats['mean_price_var'] < -1e-10,
                    'mean_price_var_neg'] = df_market_stats['mean_price_var']

print(smf.ols('range ~ mean + mean_price_var_neg + mean_price_var_pos',
              missing = 'drop',
              data = df_market_stats).fit().summary())

# todo: control for outliers...
# promo Intermarche: decrease in average price with increase in dispersion...
print(smf.ols('range ~ mean + mean_price_var_neg + mean_price_var_pos',
              missing = 'drop',
              data = df_market_stats[df_market_stats['range'] <=\
                       df_market_stats['range'].quantile(0.95)]).fit().summary())

# Range when excluding extreme values
# (interpolation only on graph... should get rid of values for graph)
df_market_stats[df_market_stats['range'] <=\
                       df_market_stats['range'].quantile(0.9)]['range'].plot()
plt.show()

# IDEA TO DEAL WITH DIFFERENTIATION

# todo: look at avg/median spread between pairs to detect submarkets if can do
# example: need to restrict to before
df_market_before = df_prices_ttc[ls_market_ids][150:300].copy()
df_market_after = df_prices_ttc[ls_market_ids][-150:].copy()

#(df_market_before['9200003'] - df_market_before[u'9190001']).value_counts()
