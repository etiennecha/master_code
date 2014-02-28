#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *

path_dir_built_json = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_json_gasoline')
path_diesel_price = os.path.join(path_dir_built_json, 'master_diesel', 'master_price_diesel')
path_info = os.path.join(path_dir_built_json, 'master_diesel', 'master_info_diesel')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'master_diesel', 'ls_ls_competitors')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'master_diesel', 'ls_tuple_competitors')

path_dir_source_stations = os.path.join(path_data, 'data_gasoline', 'data_source', 'data_stations')
path_dict_brands = os.path.join(path_dir_source_stations, 'data_brands', 'dict_brands')

path_dict_dpts_regions = os.path.join(path_data, 'data_insee', 'Regions_departements', 'dict_dpts_regions')

path_dir_built_csv = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_csv_gasoline')
path_csv_insee_data = os.path.join(path_dir_built_csv, 'master_insee_output.csv') 

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

series = 'diesel_price'
km_bound = 5

# AVERAGE PRICE PER PERIOD  
master_np_prices = np.array(master_price[series], dtype = np.float32)
matrix_np_prices_ma = np.ma.masked_array(master_np_prices, np.isnan(master_np_prices))
period_mean_prices = np.mean(matrix_np_prices_ma, axis = 0)
period_mean_prices = period_mean_prices.filled(np.nan)

# #########################
# PRICE DISPERSION ANALYSIS
# #########################

print 'Starting price dispersion block'

station_price_dispersion = get_station_price_dispersion('1500007',
                                                        ls_ls_competitors, 
                                                        master_price, 
                                                        series,
                                                        km_bound)

ls_pair_price_dispersion = get_ls_pair_price_dispersion(ls_tuple_competitors,
                                                            master_price,
                                                            series,
                                                            km_bound)

ls_ls_market_ids = get_ls_ls_distance_market_ids(master_price, ls_ls_competitors, km_bound)
ls_ls_market_price_dispersion = get_ls_ls_market_price_dispersion(ls_ls_market_ids, master_price, series)

ls_ls_m_ids_res = get_ls_ls_distance_market_ids_restricted(master_price, ls_ls_competitors, km_bound)
ls_ls_mpd_res = get_ls_ls_market_price_dispersion(ls_ls_m_ids_res, master_price, series)
  
# print 'Starting sample market price dispersion with cleaned prices'
# ls_ls_mpd_res_clean = get_ls_ls_market_price_dispersion(ls_ls_m_ids_res[0:10],
                                                                # master_price,
                                                                # series,
                                                                # clean = True)

# TODO: other definitions of market based on insee criteria
# TODO: robustess to price corrections

# REGRESSION OF PAIR PRICE DISPERSION ON DISTANCE

# TODO: COMPREHENSIVE PANDAS DF FOR ANALYSIS (TO BE DONE ELSEWHERE)...

matrix_pair_pd = np.array([pd_tuple for pd_tuple in ls_pair_price_dispersion if pd_tuple[1] < km_bound])
# col 1: distance, (col 2: duration, col 4: avg_spread), col 5: std_spread, col 6: rank reversals
matrix_pair_pd = np.array(np.vstack([matrix_pair_pd[:,1],
                                     matrix_pair_pd[:,5], 
                                     matrix_pair_pd[:,6]]), dtype = np.float32).T
pd_pair_pd = pd.DataFrame(matrix_pair_pd, columns = ['distance','spread_std', 'rank_reversals'])
pd_pair_pd = pd_pair_pd.dropna()
print '\nPair price dispersion : regressions \n'
print smf.ols(formula = 'rank_reversals ~ distance', data = pd_pair_pd).fit().summary()
print smf.ols(formula = 'spread_std ~ distance', data = pd_pair_pd).fit().summary()
# TODO: dummies / quantile regs... + regs on subsets of data

# REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICES

matrix_master_pd = []
for market in ls_ls_market_price_dispersion:
  # create variable containing number of competitors for each period
  array_nb_competitors = np.ones(len(market[2])) * market[1]
  matrix_master_pd.append(np.vstack([array_nb_competitors, period_mean_prices, market[2:]]).T)
matrix_master_pd = np.vstack(matrix_master_pd)
# matrix_master_pd = np.array(matrix_master_pd, dtype = np.float64)

ls_column_labels = ['nb_competitors', 'price', 'std_prices', 'coeff_var_prices', 'range_prices', 'gain_search']
pd_master_pd = pd.DataFrame(matrix_master_pd, columns = ls_column_labels)
pd_master_pd = pd_master_pd.dropna()
print '\nMarket price dispersion: regressions \n'
print smf.ols(formula = 'std_prices ~  nb_competitors', data = pd_master_pd).fit().summary()
print smf.ols(formula = 'std_prices ~ nb_competitors + price', data = pd_master_pd).fit().summary()
print smf.ols(formula = 'coeff_var_prices ~  nb_competitors', data = pd_master_pd).fit().summary()
print smf.ols(formula = 'coeff_var_prices ~ nb_competitors + price', data = pd_master_pd).fit().summary()
print smf.ols(formula = 'range_prices ~  nb_competitors', data = pd_master_pd).fit().summary()
print smf.ols(formula = 'range_prices ~ nb_competitors + price', data = pd_master_pd).fit().summary()
print smf.ols(formula = 'gain_search ~  nb_competitors', data = pd_master_pd).fit().summary()
print smf.ols(formula = 'gain_search ~ nb_competitors + price', data = pd_master_pd).fit().summary()




# # REGRESSIONS WITHOUT PANDAS & SM FORMULAS

# # REGRESSION OF PAIR PRICE DISPERSION ON DISTANCE

# distance = np.vstack([matrix_pair_pd[:,0]]).T
# spread_std = matrix_pair_pd[:,1]
# rank_reversals = matrix_pair_pd[:,2]
# print '\n REGRESSIONS OF PAIR PRICE DISPERSION ON DISTANCE \n'
# res_prr = sm.OLS(rank_reversals, sm.add_constant(distance), missing = "drop").fit()
# print res_prr.summary(yname='rank_reversals', xname = ['constant', 'distance'])
# res_sstd = sm.OLS(spread_std, sm.add_constant(distance), missing = "drop").fit()
# print res_sstd.summary(yname='spread_std', xname = ['constant', 'distance'])

# # REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE

# nb_competitors = np.vstack([matrix_master_pd[:,0]]).T
# nb_competitors_and_price = np.vstack([matrix_master_pd[:,0], matrix_master_pd[:,1]]).T
# range_prices = matrix_master_pd[:,2]
# std_prices = matrix_master_pd[:,3]
# coeff_var_prices = matrix_master_pd[:,4]
# gain_search = matrix_master_pd[:,5]
# print '\n REGRESSIONS OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE \n'

# res_mstd_1 = sm.OLS(std_prices, sm.add_constant(nb_competitors), missing = "drop").fit()
# print res_mstd_1.summary(yname='std_prices', xname = ['constant', 'nb_competitors'])

# res_mstd_2 = sm.OLS(std_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()
# print res_mstd_2.summary(yname='std_prices', xname = ['constant', 'nb_competitors', 'price'])

# res_cvar_1 = sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors), missing = "drop").fit()
# print res_cvar_1.summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors'])

# res_cvar_2 = sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()
# print res_cvar_2.summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors', 'price'])

# res_rp_1 = sm.OLS(range_prices, sm.add_constant(nb_competitors), missing = "drop").fit()
# print res_rp_1.summary(yname='range_prices', xname = ['constant', 'nb_competitors'])

# res_rp_2 = sm.OLS(range_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()
# print res_rp_2.summary(yname='range_prices', xname = ['constant', 'nb_competitors', 'price'])

# res_gs_1 = sm.OLS(gain_search, sm.add_constant(nb_competitors), missing = "drop").fit()
# print res_gs_1.summary(yname='gain_search', xname = ['constant', 'nb_competitors'])

# res_gs_2 = sm.OLS(gain_search, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()
# print res_gs_2.summary(yname='gain_search', xname = ['constant', 'nb_competitors', 'price'])
