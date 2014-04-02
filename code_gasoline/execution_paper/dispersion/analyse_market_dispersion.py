#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')

path_dir_built_paper_csv = os.path.join(path_dir_built_paper, 'data_csv')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)

series = 'diesel_price'
km_bound = 5
zero_threshold = np.float64(1e-10)

# DF PRICES
df_price = pd.DataFrame(master_price['diesel_price'], master_price['ids'], master_price['dates']).T

# DF CLEAN PRICES

# Prices cleaned with R / STATA
path_csv_price_cl_R = os.path.join(path_dir_built_paper_csv, 'price_cleaned_R.csv')
df_prices_cl_R = pd.read_csv(path_csv_price_cl_R,
                             dtype = {'id' : str,
                                      'date' : str,
                                      'price': np.float64,
                                      'price.cl' : np.float64})
df_prices_cl_R  = df_prices_cl_R.pivot(index='date', columns='id', values='price.cl')
df_prices_cl_R.index = [pd.to_datetime(x) for x in df_prices_cl_R.index]
idx = pd.date_range('2011-09-04', '2013-06-04')
df_prices_cl_R = df_prices_cl_R.reindex(idx, fill_value=np.nan)
df_prices_cl = df_prices_cl_R

se_mean_price = df_price.mean(1)

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

ls_ls_market_ids_temp = ls_ls_market_ids

ls_df_market_dispersion = [get_market_price_dispersion(ls_market_ids, df_prices_cl)\
                             for ls_market_ids in ls_ls_market_ids_temp]

# Can loop to add mean price or add date column and then merge df mean price with concatenated on date
# TODO: add max nb of firms and keep only if enough
# Pbm: cv is false (pbmatic division?)
ls_stats = ['range', 'gfs', 'std', 'cv', 'nb_comp']
ls_ls_market_stats = []
ls_market_ref_ids = []
for ls_market_id, df_market_dispersion in zip(ls_ls_market_ids_temp, ls_df_market_dispersion):
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

df_dispersion = pd.concat(ls_df_market_dispersion, ignore_index = True)

#df_dispersion = df_dispersion[(df_dispersion['nb_comp_t'] >= 3) &\
#                              (df_dispersion['nb_comp'] >= 3) &\
#                              (df_dispersion['nb_comp'] == df_dispersion['nb_comp_t'])]
