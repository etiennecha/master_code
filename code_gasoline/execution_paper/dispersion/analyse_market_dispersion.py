#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import datetime
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')
path_ls_ls_markets = os.path.join(path_dir_built_json, 'ls_ls_markets.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')

path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_graphs = os.path.join(path_dir_built_paper, 'data_graphs')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
ls_ls_markets = dec_json(path_ls_ls_markets)
dict_brands = dec_json(path_dict_brands)

series = 'diesel_price'
km_bound = 3
zero_threshold = np.float64(1e-10)

# DF PRICES
ls_dates = [pd.to_datetime(date) for date in master_price['dates']]
df_price = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_dates).T
se_mean_price = df_price.mean(1)

# DF CLEAN PRICES

## Prices cleaned with R / STATA
#path_csv_price_cl_R = os.path.join(path_dir_built_csv, 'price_cleaned_R.csv')
#df_prices_cl_R = pd.read_csv(path_csv_price_cl_R,
#                             dtype = {'id' : str,
#                                      'date' : str,
#                                      'price': np.float64,
#                                      'price.cl' : np.float64})
#df_prices_cl_R  = df_prices_cl_R.pivot(index='date', columns='id', values='price.cl')
#df_prices_cl_R.index = [pd.to_datetime(x) for x in df_prices_cl_R.index]
#idx = pd.date_range('2011-09-04', '2013-06-04')
#df_prices_cl_R = df_prices_cl_R.reindex(idx, fill_value=np.nan)
#df_prices_cl = df_prices_cl_R

# todo: add index mgt (date missing not a pbm here but will be for regressions)
df_price_cl = pd.read_csv(os.path.join(path_dir_built_csv, 'df_cleaned_prices.csv'),
                          index_col = 0,
                          parse_dates = True)
df_price_cl.index = [datetime.datetime.strftime(x, '%Y%m%d') for x in df_price_cl.index]

# ################
# BUILD DATAFRAME
# ################

# DF MARKET PRICE DISPERSION
ls_ls_market_ids = get_ls_ls_distance_market_ids(master_price['ids'],
                                                 ls_ls_competitors, km_bound)
ls_ls_market_ids_st = get_ls_ls_distance_market_ids_restricted(master_price['ids'],
                                                               ls_ls_competitors, km_bound)
ls_ls_market_ids_st_rd = get_ls_ls_distance_market_ids_restricted(master_price['ids'],
                                                                  ls_ls_competitors, km_bound, True)
ls_ls_markets = [ls_market for ls_market in ls_ls_markets if len(ls_market) > 2]

# Choose market definition for analysis
ls_ls_market_ids_temp = ls_ls_market_ids

# df_price vs. df_price_cl (check different cleaning ways...)
ls_df_market_dispersion = [get_market_price_dispersion(ls_market_ids, df_price)\
                             for ls_market_ids in ls_ls_market_ids_temp]

# Can loop to add mean price or add date column and then merge df mean price w/ concatd on date
# Pbm: cv is false (pbmatic division?)
ls_stats = ['range', 'gfs', 'std', 'cv', 'nb_comp']
ls_ls_market_stats = []
ls_market_ref_ids = []
for ls_market_id, df_market_dispersion in zip(ls_ls_market_ids_temp, ls_df_market_dispersion):
  df_market_dispersion = df_market_dispersion[(df_market_dispersion['nb_comp'] >= 3) &\
                                              (df_market_dispersion['nb_comp_t']/\
                                               df_market_dispersion['nb_comp'].astype(float)\
                                                 >= 2.0/3)]
  if len(df_market_dispersion) > 50:
    df_market_dispersion['id'] = ls_market_id[0]
    df_market_dispersion['price'] = se_mean_price
    df_market_dispersion['date'] = df_market_dispersion.index
    ls_ls_market_stats.append([df_market_dispersion[field].mean()\
                                for field in ls_stats] +\
                              [df_market_dispersion[field].std()\
                                for field in ls_stats])
    ls_market_ref_ids.append(ls_market_id[0])
ls_columns = ['avg_%s' %field for field in ls_stats]+\
             ['std_%s' %field for field in ls_stats]
df_market_stats = pd.DataFrame(ls_ls_market_stats, ls_market_ref_ids, ls_columns)

print 'Stats desc with distance', km_bound
print df_market_stats.describe()
# todo: restrict to the first 3 quartiles
nb_comp_lim = df_market_stats['avg_nb_comp'].quantile(0.75)
print df_market_stats[df_market_stats['avg_nb_comp'] <= nb_comp_lim].describe()
# print df_market_stats[['avg_range', 'avg_gfs', 'avg_std', 'avg_nb_comp']].describe().to_latex()

df_dispersion = pd.concat(ls_df_market_dispersion, ignore_index = True)

df_dispersion = df_dispersion[(df_dispersion['nb_comp_t'] >= 3) &\
                              (df_dispersion['nb_comp_t']/\
                               df_dispersion['nb_comp'].astype(float) >= 2.0/3)]

# PLOT ECDF OF CLEANED PRICES

#from statsmodels.distributions.empirical_distribution import ECDF
#
### All prices
##ls_market_ids = ls_ls_market_ids_temp[0]
##x = np.linspace(np.nanmin(df_price_cl[ls_market_ids]),\
##                np.nanmax(df_price_cl[ls_market_ids]), num=100)
##ax = plt.subplot()
##for indiv_id in ls_market_ids:
##  ecdf = ECDF(df_price_cl[indiv_id])
##  y = ecdf(x)
##  ax.step(x, y, label = indiv_id)
##plt.legend()
##plt.title('Cleaned prices CDFs')
#
## Excluding extreme values
#ls_market_ids = ls_ls_market_ids_temp[0]
#x = np.linspace(df_price_cl[ls_market_ids].quantile(0.95).max(),\
#                df_price_cl[ls_market_ids].quantile(0.05).min(), num=200)
#f, ax = plt.subplots()
#for indiv_id in ls_market_ids:
#  min_quant = df_price_cl[indiv_id].quantile(0.05)
#  max_quant = df_price_cl[indiv_id].quantile(0.95)
#  se_prices = df_price_cl[indiv_id][(df_price_cl[indiv_id] >= min_quant) &\
#                                    (df_price_cl[indiv_id] <= max_quant)]
#  print indiv_id, len(df_price_cl[indiv_id]), len(se_prices)
#  ecdf = ECDF(se_prices)
#  y = ecdf(x)
#  ax.step(x, y, label = indiv_id)
#plt.legend()
#plt.title('Cleaned prices CDFs')
#plt.show()

# TODO: regress support of distribution of cleaned prices and std on nb competitors

# Check median spread for no diff
ls_tuple_nodiff = []
for ((id_1, id_2), distance) in ls_tuple_competitors:
  if distance < km_bound and (df_price[id_1]-df_price[id_2]).median() == 0:
    ls_tuple_nodiff.append((id_1, id_2))
ls_ids_nodiff = [indiv_id for ls_indiv_ids in ls_tuple_nodiff for indiv_id in ls_indiv_ids]
ls_ids_nodiff = list(set(ls_ids_nodiff))

ls_ids_diff = [indiv_id for indiv_id in master_price['ids'] if indiv_id not in ls_ids_nodiff]

indiv_ind = master_price['ids'].index(ls_ids_diff[0])

# CHECK STABLE MARKETS

# Example
ls_ls_market_ids[0]
ls_harmonized_series = [df_price[ls_ls_market_ids[0][0]]]
for comp_id in ls_ls_market_ids[0][1:]:
	ls_harmonized_series.append(df_price[comp_id] +\
    (df_price[ls_ls_market_ids[0][0]] - df_price[comp_id]).median())
df_market = pd.DataFrame(dict(zip(ls_ls_market_ids[0], ls_harmonized_series)))
df_market['range'] = df_market.max(1) - df_market.min(1) + 1 # for graph
df_market.plot()
plt.show()

df_market['range'] = df_market[ls_ls_market_ids[0]].max(1) - df_market[ls_ls_market_ids[0]].min(1)

df_market['avg_price'] = df_market[ls_ls_market_ids[0]].mean(1)
print smf.ols('range ~ avg_price', missing = 'drop', data = df_market).fit().summary()

df_market['avg_price_var'] = df_market['avg_price'] - df_market['avg_price'].shift(1)
df_market['avg_price_var_abs'] = np.abs(df_market['avg_price_var'])
print smf.ols('range ~ avg_price + avg_price_var_abs',
              missing = 'drop', data = df_market).fit().summary()

df_market['avg_price_var_pos'] = 0
df_market['avg_price_var_pos'][df_market['avg_price_var'] > 0.0001] = df_market['avg_price_var']
df_market['avg_price_var_neg'] = 0
df_market['avg_price_var_neg'][df_market['avg_price_var'] < -0.0001] = df_market['avg_price_var']

print smf.ols('range ~ avg_price + avg_price_var_neg + avg_price_var_pos',
              missing = 'drop', data = df_market).fit().summary()

# todo: control for outliers...
# promo Intermarche: decrease in average price with increase in dispersion...
print smf.ols('range ~ avg_price + avg_price_var_neg + avg_price_var_pos',
              missing = 'drop', 
              data = df_market[df_market['range'] <= df_market['range'].quantile(0.95)]\
             ).fit().summary()

# Nb of times a station is min
ls_market_ids = ls_ls_market_ids[0]
ls_min_max = []
for indiv_id in ls_market_ids:
  nb_min = len(df_market[df_market[indiv_id] == df_market[ls_market_ids].min(1)])
  nb_max = len(df_market[df_market[indiv_id] == df_market[ls_market_ids].max(1)])
  ls_min_max.append((nb_min, nb_max))
# Count nb of time each is cheaper / least expensive... stuffs like that

# Loop
ls_stable_market_dispersion = []
for ls_market in ls_ls_markets:
  # stability of results vs. order of ids?
  ls_harmonized_series = [df_price[ls_market[0]]]
  for comp_id in ls_market[1:]:
  	ls_harmonized_series.append(df_price[comp_id] +\
      (df_price[ls_market[0]] - df_price[comp_id]).median())
  df_market = pd.DataFrame(dict(zip(ls_market, ls_harmonized_series)))
  ls_stable_market_dispersion.append([df_market, df_market.max(1) - df_market.min(1)])


def get_nd_comps(ls_indiv_ids, ls_comp_ids, df_price):
  # ls_indiv_ids are within non diff group, to be compared with ls_comp_ids
  # if any pair: 0 median spread: add to non diff group (to be added)
  ls_nd_comps = []
  for indiv_id in ls_indiv_ids:
    for comp_id in ls_comp_ids:
      if np.abs((df_price[indiv_id] - df_price[comp_id]).median()) <= zero_threshold:
        ls_nd_comps.append(comp_id)
  return ls_nd_comps

#ls_beg_market_ids = ls_market
#ls_group_nd_ids, ls_add_group_nd_ids = [ls_market[0]], [ls_market[0]]
#ls_comp_ids = ls_market[1:]
#while ls_add_group_nd_ids:
#  ls_add_group_nd_ids = get_nd_comps(ls_add_group_nd_ids, ls_comp_ids, df_price)
#  ls_group_nd_ids += ls_add_group_nd_ids
#  ls_comp_ids = [temp_id for temp_id in ls_comp_ids if temp_id not in ls_add_group_nd_ids]

#for ls_market, (df_market, se_range) in zip(ls_ls_markets, ls_stable_market_dispersion):
#  if len(ls_market) >= 5:
#    path_temp = os.path.join(path_dir_graphs,
#                             'stable_markets',
#                             '%s' %len(ls_market))
#    if not os.path.exists(path_temp):
#      os.makedirs(path_temp)
#    df_market.plot()
#    plt.savefig(os.path.join(path_temp, ls_market[0]))

# display list of list
ls_ls_ex = [[u'86100001', u'86100003', u'86100009', u'86100011'],
            [u'86100005'], [u'86100012'], [u'86102001']]
str_ex = "[" + "], [".join(["'" + "', '".join(ls_ex) + "'" for ls_ex in ls_ls_ex]) + "]"

#plt.rcParams['figure.figsize'] = 16, 6
#ls_ls_groups = []
#for ls_market, (df_market, se_range) in zip(ls_ls_markets, ls_stable_market_dispersion):
#  if len(ls_market) >= 5:
#    #df_market.plot()
#    #break
#    ls_groups = []
#    ls_beg_market_ids = ls_market
#    while ls_beg_market_ids:
#      ls_group_nd_ids, ls_add_group_nd_ids = [ls_beg_market_ids[0]], [ls_beg_market_ids[0]]
#      ls_comp_ids = ls_beg_market_ids[1:]
#      while ls_add_group_nd_ids:
#        ls_add_group_nd_ids = get_nd_comps(ls_add_group_nd_ids, ls_comp_ids, df_price)
#        ls_group_nd_ids += ls_add_group_nd_ids
#        ls_comp_ids = [temp_id for temp_id in ls_comp_ids if temp_id not in ls_add_group_nd_ids]
#      ls_beg_market_ids = [market_id for market_id in ls_beg_market_ids\
#                              if market_id not in ls_group_nd_ids]
#      ls_groups.append(ls_group_nd_ids)
#    ls_ls_groups.append(ls_groups)
#    path_temp = os.path.join(path_dir_graphs,
#                             'stable_markets',
#                             '%s' %len(ls_groups))
#    if not os.path.exists(path_temp):
#      os.makedirs(path_temp)
#    df_price[ls_market].plot()
#    str_group = "[" + "], [".join(["'" + "', '".join(group) + "'"\
#                                     for group in ls_groups]) + "]"
#    plt.figtext(.02, .02, str_group)
#    plt.subplots_adjust(bottom=0.2)
#    plt.savefig(os.path.join(path_temp, ls_market[0]))
#    plt.close()
