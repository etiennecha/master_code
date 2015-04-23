#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import datetime
import time
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
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_graphs = os.path.join(path_dir_built_paper, 'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
ls_ls_markets = dec_json(path_ls_ls_markets)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

pd.options.display.float_format = '{:6,.4f}'.format
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
ls_ls_market_ids_temp = ls_ls_markets

## Example
#ls_ls_market_ids[0]
#ls_harmonized_series = [df_price[ls_ls_market_ids[0][0]]]
#for comp_id in ls_ls_market_ids[0][1:]:
#	ls_harmonized_series.append(df_price[comp_id] +\
#    (df_price[ls_ls_market_ids[0][0]] - df_price[comp_id]).median())
#df_market = pd.DataFrame(dict(zip(ls_ls_market_ids[0], ls_harmonized_series)))
#df_market['range'] = df_market.max(1) - df_market.min(1) + 1 # for graph
#df_market.plot()
#plt.show()

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
      # if np.abs((df_price[indiv_id] - df_price[comp_id]).median()) <= zero_threshold:
      if np.abs((df_price[indiv_id] - df_price[comp_id]).mean()) - 0.01 <= zero_threshold:
        ls_nd_comps.append(comp_id)
  return ls_nd_comps

ls_market = ls_ls_markets[0]
ls_beg_market_ids = ls_market
ls_group_nd_ids, ls_add_group_nd_ids = [ls_market[0]], [ls_market[0]]
ls_comp_ids = ls_market[1:]
while ls_add_group_nd_ids:
  ls_add_group_nd_ids = get_nd_comps(ls_add_group_nd_ids, ls_comp_ids, df_price)
  ls_group_nd_ids += ls_add_group_nd_ids
  ls_comp_ids = [temp_id for temp_id in ls_comp_ids if temp_id not in ls_add_group_nd_ids]

#for ls_market, (df_market, se_range) in zip(ls_ls_markets, ls_stable_market_dispersion):
#  if len(ls_market) >= 5:
#    path_temp = os.path.join(path_dir_graphs,
#                             'stable_markets',
#                             '%s' %len(ls_market))
#    if not os.path.exists(path_temp):
#      os.makedirs(path_temp)
#    df_market.plot()
#    plt.savefig(os.path.join(path_temp, ls_market[0]))

## display list of list
#ls_ls_ex = [[u'86100001', u'86100003', u'86100009', u'86100011'],
#            [u'86100005'], [u'86100012'], [u'86102001']]
#str_ex = "[" + "], [".join(["'" + "', '".join(ls_ex) + "'" for ls_ex in ls_ls_ex]) + "]"

plt.rcParams['figure.figsize'] = 16, 6
ls_ls_groups = []
for ls_market, (df_market, se_range) in zip(ls_ls_markets, ls_stable_market_dispersion):
  if len(ls_market) >= 5:
    #df_market.plot()
    #break
    ls_groups = []
    ls_beg_market_ids = ls_market
    while ls_beg_market_ids:
      ls_group_nd_ids, ls_add_group_nd_ids = [ls_beg_market_ids[0]], [ls_beg_market_ids[0]]
      ls_comp_ids = ls_beg_market_ids[1:]
      while ls_add_group_nd_ids:
        ls_add_group_nd_ids = get_nd_comps(ls_add_group_nd_ids, ls_comp_ids, df_price)
        ls_group_nd_ids += ls_add_group_nd_ids
        ls_comp_ids = [temp_id for temp_id in ls_comp_ids if temp_id not in ls_add_group_nd_ids]
      ls_beg_market_ids = [market_id for market_id in ls_beg_market_ids\
                              if market_id not in ls_group_nd_ids]
      ls_groups.append(ls_group_nd_ids)
    ls_ls_groups.append(ls_groups)
    path_temp = os.path.join(path_dir_graphs,
                             'stable_markets',
                             'groups_mean01',
                             '%s' %len(ls_groups))
    if not os.path.exists(path_temp):
      os.makedirs(path_temp)
    df_price[ls_market].plot()
    str_group = "[" + "], [".join(["'" + "', '".join(group) + "'"\
                                     for group in ls_groups]) + "]"
    plt.figtext(.02, .02, str_group)
    plt.subplots_adjust(bottom=0.2)
    plt.savefig(os.path.join(path_temp, ls_market[0]))
    plt.close()
