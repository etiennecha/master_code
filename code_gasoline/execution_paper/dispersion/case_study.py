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

# DF PRICES CLEANED
df_price_cl = pd.read_csv(os.path.join(path_dir_built_csv, 'df_cleaned_prices.csv'),
                          index_col = 0,
                          parse_dates = True)
# df_price_cl.index = [datetime.datetime.strftime(x, '%Y%m%d') for x in df_price_cl.index]

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

# EXAMPLE: AMBERIEU EN BUGEY
# compute spreads, leader follower, matched prices, rank reversals, market dispersion

# Raw prices
df_price[ls_ls_market_ids[0]][:'2012-06'].plot()
plt.show()

# Cleaned prices (residuals)
df_price_cl[ls_ls_market_ids[0]][:'2012-06'].plot()
plt.show()

# Cleaned prices: alternative way
ls_ls_market_ids[0]
ls_harmonized_series = [df_price[ls_ls_market_ids[0][0]]]
for comp_id in ls_ls_market_ids[0][1:]:
	ls_harmonized_series.append(df_price[comp_id] +\
    (df_price[ls_ls_market_ids[0][0]] - df_price[comp_id]).median())
df_market = pd.DataFrame(dict(zip(ls_ls_market_ids[0], ls_harmonized_series)))
# df_market['range'] = df_market.max(1) - df_market.min(1) + 1 # for graph
df_market[:'2012-06'].plot()
plt.show()

