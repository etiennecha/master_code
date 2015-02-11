#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_paper_dispersion')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

pd.set_option('float_format', '{:,.4f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ################
# LOAD DATA
# ################

# LOAD DICT LS COMP
dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# LOAD STABLE MARKETS
ls_dict_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                               'ls_dict_stable_markets.json'))
ls_robust_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                                 'ls_robust_stable_markets.json'))

# 0 is 3km, 1 is 4km, 2 is 5km
ls_stable_markets = [stable_market for nb_sellers, stable_markets\
                       in ls_dict_stable_markets[2].items()\
                          for stable_market in stable_markets]

# LOAD DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = True)
df_prices_cl.set_index('date', inplace = True)

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
                               'dpt' : str})
df_info.set_index('id_station', inplace = True)

# #########################
# GET DF MARKET DISPERSION
# #########################

# PARAMETERS

km_bound = 5
df_prices = df_prices_cl
# temp (stations with too few/rigid prices absent in df_prices_cl)
for id_station in df_info.index:
  if id_station not in df_prices.columns:
    df_prices[id_station] = np.nan

# GET MARKETS

ls_markets = get_ls_ls_market_ids(dict_ls_comp, km_bound)
ls_markets_st = get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound)
ls_markets_st_rd = get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound, True)

# GET MARKET DISPERSION

ls_markets_temp = ls_robust_stable_markets # Market definition chosen here (loop?)
ls_df_market_dispersion = [get_market_price_dispersion(market_ids, df_prices)\
                             for market_ids in ls_markets_temp]
se_mean_price = df_prices.mean(1)

# Can loop to add mean price or add date column and then merge df mean price w/ concatd on date
# Pbm: cv is false (pbmatic division?)
ls_stats = ['range', 'gfs', 'std', 'cv', 'nb_comp']
ls_ls_market_stats = []
ls_market_ref_ids = []
for ls_market_id, df_market_dispersion in zip(ls_markets_temp, ls_df_market_dispersion):
  df_md = df_market_dispersion[(df_market_dispersion['nb_comp'] >= 3) &\
                               (df_market_dispersion['nb_comp_t']/\
                                df_market_dispersion['nb_comp'].astype(float)\
                                  >= 2.0/3)].copy()
  if len(df_market_dispersion) > 50:
    df_md['id'] = ls_market_id[0]
    df_md['price'] = se_mean_price
    df_md['date'] = df_md.index
    ls_ls_market_stats.append([df_md[field].mean()\
                                for field in ls_stats] +\
                              [df_md[field].std()\
                                for field in ls_stats])
    ls_market_ref_ids.append(ls_market_id[0])
ls_columns = ['avg_%s' %field for field in ls_stats]+\
             ['std_%s' %field for field in ls_stats]
df_market_stats = pd.DataFrame(ls_ls_market_stats, ls_market_ref_ids, ls_columns)

print u'\nStats desc: all:'
print u'\n', df_market_stats.describe()

print u'\nStats des: restriction on nb of sellers:'
nb_comp_lim = df_market_stats['avg_nb_comp'].quantile(0.75)
print u'\n', df_market_stats[df_market_stats['avg_nb_comp'] <= nb_comp_lim].describe()

# print df_market_stats[['avg_range', 'avg_gfs', 'avg_std', 'avg_nb_comp']].describe().to_latex()

#df_dispersion = pd.concat(ls_df_market_dispersion, ignore_index = True)
#df_dispersion = df_dispersion[(df_dispersion['nb_comp_t'] >= 3) &\
#                              (df_dispersion['nb_comp_t']/\
#                               df_dispersion['nb_comp'].astype(float) >= 2.0/3)]

# ##############
# STATS DES
# ##############

## PLOT ECDF OF CLEANED PRICES
#
# Not necessarily at market level
#
#from statsmodels.distributions.empirical_distribution import ECDF
#
#ls_market_ids = ls_markets_temp[0]
#
## All prices
#x = np.linspace(np.nanmin(df_prices_cl[ls_market_ids]),\
#                np.nanmax(df_prices_cl[ls_market_ids]), num=100)
#ax = plt.subplot()
#for indiv_id in ls_market_ids:
#  ecdf = ECDF(df_prices_cl[indiv_id])
#  y = ecdf(x)
#  ax.step(x, y, label = indiv_id)
#plt.legend()
#plt.title('Cleaned prices CDFs')
#plt.show()
#
## Excluding extreme values
#x = np.linspace(df_prices_cl[ls_market_ids].quantile(0.95).max(),\
#                df_prices_cl[ls_market_ids].quantile(0.05).min(), num=200)
#f, ax = plt.subplots()
#for indiv_id in ls_market_ids:
#  min_quant = df_prices_cl[indiv_id].quantile(0.05)
#  max_quant = df_prices_cl[indiv_id].quantile(0.95)
#  se_prices = df_prices_cl[indiv_id][(df_prices_cl[indiv_id] >= min_quant) &\
#                                    (df_prices_cl[indiv_id] <= max_quant)]
#  print indiv_id, len(df_prices_cl[indiv_id]), len(se_prices)
#  ecdf = ECDF(se_prices)
#  y = ecdf(x)
#  ax.step(x, y, label = indiv_id)
#plt.legend()
#plt.title('Cleaned prices CDFs')
#plt.show()

## CASE STUDY FOR SPECIFIC MARKET

# todo: generalize? robust vs. global analysis

for x in ls_markets_temp:
  if len(x) == 5:
    ls_market = x
    break

# typically: pbm with a change in price policy
df_prices_ttc[ls_market].plot()
plt.show()

#ls_market.remove('9200003')

ls_df_market_stats = []
for df_pr in [df_prices_ttc, df_prices_cl]:
  df_mkt_prices = df_pr[ls_market].copy()
  df_mkt_stats = pd.concat([df_mkt_prices.max(1),
                            df_mkt_prices.min(1),
                            df_mkt_prices.mean(1),
                            df_mkt_prices.std(1, ddof = 0)],
                           keys = ['max', 'min', 'mean', 'std'],
                           axis = 1)
  df_mkt_stats['range'] = df_mkt_stats['max'] - df_mkt_stats['min']
  df_mkt_stats['cv'] = df_mkt_stats['std'] / df_mkt_stats['mean']
  ls_df_market_stats.append(df_mkt_stats)

df_market_stats = ls_df_market_stats[0]

print smf.ols('range ~ mean', missing = 'drop', data = df_market_stats).fit().summary()
df_market_stats['mean_price_var'] = df_market_stats['mean'] - df_market_stats['mean'].shift(1)
df_market_stats['mean_price_var_abs'] = np.abs(df_market_stats['mean_price_var'])

print smf.ols('range ~ mean_price_var',
              missing = 'drop',
              data = df_market_stats).fit().summary()

df_market_stats['mean_price_var_pos'] = 0
df_market_stats.loc[df_market_stats['mean_price_var'] > 1e-10,
                    'mean_price_var_pos'] = df_market_stats['mean_price_var']
df_market_stats['mean_price_var_neg'] = 0
df_market_stats.loc[df_market_stats['mean_price_var'] < -1e-10,
                    'mean_price_var_neg'] = df_market_stats['mean_price_var']

print smf.ols('range ~ mean + mean_price_var_neg + mean_price_var_pos',
              missing = 'drop',
              data = df_market_stats).fit().summary()

# todo: control for outliers...
# promo Intermarche: decrease in average price with increase in dispersion...
print smf.ols('range ~ mean + mean_price_var_neg + mean_price_var_pos',
              missing = 'drop',
              data = df_market_stats[df_market_stats['range'] <=\
                       df_market_stats['range'].quantile(0.95)]).fit().summary()

# Range when excluding extreme values
# (interpolation only on graph... should get rid of values for graph)
df_market_stats[df_market_stats['range'] <=\
                       df_market_stats['range'].quantile(0.9)]['range'].plot()
plt.show()

# IDEA TO DEAL WITH DIFFERENTIATION

# todo: look at avg/median spread between pairs to detect submarkets if can do
# example: need to restrict to before
df_market_before = df_prices_ttc[ls_market][150:300].copy()
df_market_after = df_prices_ttc[ls_market][-150:].copy()

#(df_market_before['9200003'] - df_market_before[u'9190001']).value_counts()

