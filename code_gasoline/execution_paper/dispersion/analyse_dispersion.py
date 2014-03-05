#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

zero_threshold = np.float64(1e-10)
series = 'diesel_price'
km_bound = 5

master_np_prices = np.array(master_price[series], np.float64)
df_price = pd.DataFrame(master_np_prices.T, master_price['dates'], columns=master_price['ids'])

# #####################
# PAIR PRICE DISPERSION
# #####################

start = time.clock()
ls_pair_price_dispersion = []
ls_pair_competitors = []
for ((indiv_id_1, indiv_id_2), distance) in ls_tuple_competitors:
  # could check presence btw...
  indiv_ind_1 = master_price['ids'].index(indiv_id_1)
  indiv_ind_2 = master_price['ids'].index(indiv_id_2)
  if distance < km_bound:
    ls_pair_competitors.append(((indiv_id_1, indiv_id_2), distance))
    ls_pair_price_dispersion.append(get_pair_price_dispersion(master_np_prices[indiv_ind_1],
                                                              master_np_prices[indiv_ind_2],
                                                              light = False))
print 'Pair price dispersion:', time.clock() - start

# DF PAIR PD STATS
ls_ppd_for_df = [elt[0] for elt in ls_pair_price_dispersion]
ls_columns = ['avg_abs_spread', 'avg_spread', 'std_spread', 'nb_days_spread',
              'percent_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr', 'nb_rr_conservative']
df_ppd = pd.DataFrame(ls_ppd_for_df, columns = ls_columns)

# No rank reversal => check differentiation
print 'No rank reversal', len(df_ppd[df_ppd['percent_rr'] <= zero_threshold])

# Too much rank reversal => check deterministic changes
ls_max_len_rr = [np.max(elt[3][0]) if elt[3][0] else 0 for elt in ls_pair_price_dispersion]
print 'Station with max length rank reversal', np.argmax(ls_max_len_rr)
df_ppd['max_len_rr'] = ls_max_len_rr

print 'Suspect rank reversals:', len(df_ppd[(df_ppd['nb_rr_conservative'] < 4)&\
                                            (df_ppd['max_len_rr'] > 30)])
# problem: continously reduce... where to stop? what is legit?

print 'Low number of rank reversals:', len(df_ppd[(df_ppd['nb_rr_conservative'] < 3) &\
                                          (df_ppd['nb_rr_conservative'] > 0)])

# DF PAIR PD TEMPORAL
# (could start from simple spread and apply function to mask to each column...)
ls_rr_spread = [pair_pd[2][1] for tup_comp, pair_pd\
                  in zip(ls_pair_competitors, ls_pair_price_dispersion)
                    if tup_comp[1] <= 3]
df_rr_spread = pd.DataFrame(np.array(ls_rr_spread, np.float32))

ls_rr_temp = []
for day_ind in df_rr_spread.columns:
  nb_valid = len(df_rr_spread[day_ind][~pd.isnull(df_rr_spread[day_ind])])
  se_rr = np.abs(df_rr_spread[day_ind][np.abs(df_rr_spread[day_ind]) >  zero_threshold])
  nb_rr = len(se_rr)
  med_rr = np.median(se_rr)
  avg_rr = np.mean(se_rr)
  ls_rr_temp.append([nb_valid, nb_rr, med_rr, avg_rr])
ls_columns = ['nb_valid', 'nb_rr', 'med_rr', 'avg_rr']
df_rr_temp = pd.DataFrame(ls_rr_temp, master_price['dates'], ls_columns)
df_rr_temp['pct_rr'] = df_rr_temp['nb_rr']/ df_rr_temp['nb_valid']

# TODO: plot vs. margin !

# #########################
# MARKET PRICE DISPERSION 
# #########################

#ls_ls_market_ids = get_ls_ls_distance_market_ids(master_price, ls_ls_competitors, km_bound)
#ls_ls_market_price_dispersion = get_ls_ls_market_price_dispersion(ls_ls_market_ids, master_price, series)
#
#ls_ls_m_ids_res = get_ls_ls_distance_market_ids_restricted(master_price, ls_ls_competitors, km_bound)
#ls_ls_mpd_res = get_ls_ls_market_price_dispersion(ls_ls_m_ids_res, master_price, series)

# print 'Starting sample market price dispersion with cleaned prices'
# ls_ls_mpd_res_clean = get_ls_ls_market_price_dispersion(ls_ls_m_ids_res[0:10],
                                                                # master_price,
                                                                # series,
                                                                # clean = True)
#
## PAIR PRICE DISPERSION
#
#matrix_pair_pd = np.array([pd_tuple for pd_tuple in ls_pair_price_dispersion if pd_tuple[1] < km_bound])
## col 1: distance, (col 2: duration, col 4: avg_spread), col 5: std_spread, col 6: rank reversals
#matrix_pair_pd = np.array(np.vstack([matrix_pair_pd[:,1],
#                                     matrix_pair_pd[:,5], 
#                                     matrix_pair_pd[:,6]]), dtype = np.float32).T
#pd_pair_pd = pd.DataFrame(matrix_pair_pd, columns = ['distance', 'spread_std', 'rank_reversals'])
#pd_pair_pd = pd_pair_pd.dropna()
#
## MARKET PRICE DISPERSION
#
#matrix_master_pd = []
#for market in ls_ls_market_price_dispersion:
#  # create variable containing number of competitors for each period
#  array_nb_competitors = np.ones(len(market[2])) * market[1]
#  matrix_master_pd.append(np.vstack([array_nb_competitors, period_mean_prices, market[2:]]).T)
#matrix_master_pd = np.vstack(matrix_master_pd)
## matrix_master_pd = np.array(matrix_master_pd, dtype = np.float64)
#
#ls_column_labels = ['nb_competitors', 'price', 'std_prices', 'coeff_var_prices', 'range_prices', 'gain_search']
#pd_master_pd = pd.DataFrame(matrix_master_pd, columns = ls_column_labels)
#pd_master_pd = pd_master_pd.dropna()
