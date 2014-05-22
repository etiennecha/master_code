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
path_ls_ids_final = os.path.join(path_dir_built_json, 'ls_ids_final.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')
path_ls_ls_markets = os.path.join(path_dir_built_json, 'ls_ls_markets.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')

path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ids_final = dec_json(path_ls_ids_final)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
ls_ls_markets = dec_json(path_ls_ls_markets)
dict_brands = dec_json(path_dict_brands)

series = 'diesel_price'
km_bound = 3
zero_threshold = np.float64(1e-10)

# DF PRICES

#master_np_prices = np.array(master_price['diesel_price'], np.float64)
#df_price = pd.DataFrame(master_np_prices.T, master_price['dates'], master_price['ids'])
ls_dates = [pd.to_datetime(date) for date in master_price['dates']]
df_price = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_dates).T
df_price[[x for x in df_price.columns if x not in ls_ids_final]] = np.nan 
se_mean_price = df_price.mean(1)

# DF CLEAN PRICES

# First approximate way
# df_price_cl = df_price.apply(lambda x: x - (x - se_mean_price).mean())

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
#df_price_cl = df_prices_cl_R

df_price_cl = pd.read_csv(os.path.join(path_dir_built_csv, 'df_cleaned_prices.csv'),
                          index_col = 0,
                          parse_dates = True)
df_price_cl[[x for x in df_price_cl.columns if x not in ls_ids_final]] = np.nan 

# ################
# BUILD DATAFRAME
# ################

# DF BRANDS
dict_std_brands = {v[0]: v for k, v in dict_brands.items()}
ls_brands = []
for indiv_id in master_price['ids']:
  indiv_dict_info = master_price['dict_info'][indiv_id]
  brand_1_b = indiv_dict_info['brand_std'][0][0]
  brand_2_b = dict_std_brands[indiv_dict_info['brand_std'][0][0]][1]
  brand_type_b = dict_std_brands[indiv_dict_info['brand_std'][0][0]][2]
  brand_1_e = indiv_dict_info['brand_std'][-1][0]
  brand_2_e = dict_std_brands[indiv_dict_info['brand_std'][-1][0]][1]
  brand_type_e = dict_std_brands[indiv_dict_info['brand_std'][-1][0]][2]
  ls_brands.append([brand_1_b, brand_2_b, brand_type_b,
                    brand_1_e, brand_2_e, brand_type_e])
ls_columns = ['brand_1_b', 'brand_2_b', 'brand_type_b', 'brand_1_e', 'brand_2_e', 'brand_type_e']
df_brands = pd.DataFrame(ls_brands, index = master_price['ids'], columns = ls_columns)
df_brands['id'] = df_brands.index

# DF MARKET PRICE DISPERSION
ls_ls_market_ids = get_ls_ls_distance_market_ids(master_price['ids'],\
                                                 ls_ls_competitors, km_bound)
ls_ls_market_ids_st = get_ls_ls_distance_market_ids_restricted(master_price['ids'],\
                                                               ls_ls_competitors, km_bound)
ls_ls_market_ids_st_rd = get_ls_ls_distance_market_ids_restricted(master_price['ids'],\
                                                                  ls_ls_competitors, km_bound, True)
ls_ls_markets = [ls_market for ls_market in ls_ls_markets if len(ls_market) > 2]

ls_ls_market_ids_temp = ls_ls_markets # [0:6000]

ls_df_market_dispersion = [get_market_price_dispersion(ls_market_ids, df_price_cl) for\
                             ls_market_ids in ls_ls_market_ids_temp]
# Check why prices is Nan: should not be the case

# Can loop to add mean price or add date column and then merge df mean price w/ concatenated on date
# todo: add max nb of firms and keep only if enough
ls_total_price_vs_dispersion = []
for ls_market_id, df_market_dispersion in zip(ls_ls_market_ids_temp, ls_df_market_dispersion):
  df_market_dispersion['id'] = ls_market_id[0]
  df_market_dispersion['price'] = se_mean_price
  df_market_dispersion['price_chge'] = se_mean_price - se_mean_price.shift(1)
  df_market_dispersion['date'] = df_market_dispersion.index
  for indiv_id in ls_market_id:
    # todo: work on mean if several + other stations ?    
    if df_brands['brand_1_b'][indiv_id] == 'TOTAL':
      ls_total_price_vs_dispersion.append([indiv_id,
                                           (df_price[indiv_id] - se_mean_price).mean(),
                                           df_market_dispersion['std'].mean(),
                                           df_market_dispersion['range'].quantile(0.9),
                                           df_market_dispersion['nb_comp'].mean()])
      break
df_dispersion = pd.concat(ls_df_market_dispersion, ignore_index = True)

# Get rid of cases with too few competitors
df_dispersion = df_dispersion[(df_dispersion['nb_comp_t'] >= 3) &\
                              (df_dispersion['nb_comp'] >= 3) &\
                              (df_dispersion['nb_comp'] == df_dispersion['nb_comp_t'])]

# Get rid of nan... otherwise pbm to compute clustered standard errors (todo: one liner) 
df_dispersion = df_dispersion[(~pd.isnull(df_dispersion['gfs'])) &\
                              (~pd.isnull(df_dispersion['std'])) &\
                              (~pd.isnull(df_dispersion['cv'])) &\
                              (~pd.isnull(df_dispersion['range'])) &\
                              (~pd.isnull(df_dispersion['nb_comp']))]

# Ouput for R regressions
#path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')
#df_dispersion.to_csv(os.path.join(path_dir_built_csv, 'data_test.csv'))

# #############################################
# REGRESSIONS: DISPERSION VS. NB COMP / COST
# #############################################

# Need to run clustered regressions
ls_formulas = ['gfs ~ nb_comp',
               'gfs ~ nb_comp + price',
               'std ~ nb_comp',
               'std ~ nb_comp + price',
               'cv  ~ nb_comp',
               'cv  ~ nb_comp + price',
               'range ~ nb_comp',
               'range ~ nb_comp + price']

ls_ls_reg_res = []
ls_reg_series = []
for str_formula in ls_formulas:
  #print '\n', smf.ols(formula = str_formula, data = df_dispersion).fit().summary()
  reg_res = smf.ols(formula = str_formula, data = df_dispersion).fit()
  cl_std_errors =  sm.stats.sandwich_covariance.cov_cluster_2groups(\
                     reg_res,
                     [date.strftime('%Y%m%d') for date in df_dispersion['date']],
                     [indiv_id for indiv_id in df_dispersion['id']])
  ar_cl_std_errors = np.array([np.sqrt(cl_std_errors[0][i, i])\
                                 for i in range(len(str_formula.split('+')) + 1)])
  print str_formula
  print ar_cl_std_errors
  ar_cl_t_values = reg_res.params / ar_cl_std_errors
  #ls_reg_res = [reg_res.nobs, reg_res.rsquared, reg_res.rsquared_adj,
  #              reg_res.params, reg_res.bse, reg_res.tvalues,
  #              ar_cl_std_errors, ar_cl_t_values]
  #ls_ls_reg_res.append(ls_reg_res)
  ls_columns = ['N', 'R2', 'R2a'] +\
               ['B_%s' %x for x in reg_res.params.index.values.tolist()] +\
               ['B_%s_t' %x for x in reg_res.tvalues.index.values.tolist()] +\
               ['B_%s_tc' %x for x in reg_res.tvalues.index.values.tolist()]
  ls_values =  [reg_res.nobs, reg_res.rsquared, reg_res.rsquared_adj] +\
               reg_res.params.values.tolist() +\
               reg_res.tvalues.values.tolist() +\
               ar_cl_t_values.tolist()
  ls_reg_series.append(pd.Series(ls_values, ls_columns))

pd.options.display.float_format = '{:6,.4f}'.format
df_results = pd.DataFrame(ls_reg_series,
                          [formula[:formula.index('~')-1] for formula in ls_formulas])
df_results['N'] = df_results['N'].apply(lambda x: int(x))
print df_results.to_string()

# Check regressions with price variations: get rid of nan
df_dispersion = df_dispersion[(~pd.isnull(df_dispersion['price_chge']))]
str_formula = 'gfs ~ nb_comp + price + price_chge'
reg_res = smf.ols(formula = str_formula, data = df_dispersion).fit()
cl_std_errors =  sm.stats.sandwich_covariance.cov_cluster_2groups(\
                   reg_res,
                   [date.strftime('%Y%m%d') for date in df_dispersion['date']],
                   [indiv_id for indiv_id in df_dispersion['id']])
ar_cl_std_errors = np.array([np.sqrt(cl_std_errors[0][i, i])\
                               for i in range(len(str_formula.split('+')) + 1)])
ar_cl_t_values = reg_res.params / ar_cl_std_errors

# #############################################
# REGRESSIONS: PRICE LEVEL VS. DISPERSION
# #############################################

#ls_columns = ['id_total', 'price_proxy', 'std', 'range', 'nbcomp']
#df_total_dispersion = pd.DataFrame(ls_total_price_vs_dispersion, columns = ls_columns)
#
#print smf.ols(formula = 'price_proxy ~ std + nbcomp', data = df_total_dispersion).fit().summary()
#df_total_dispersion = df_total_dispersion[df_total_dispersion['nbcomp'] >= 3]
#print smf.ols(formula = 'price_proxy ~ std + nbcomp', data = df_total_dispersion).fit().summary()

# #############
# DEPRECATED
# #############

## REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICES
#
#ls_ls_market_ids = get_ls_ls_distance_market_ids(master_price, ls_ls_competitors, km_bound)
#ls_ls_market_price_dispersion = get_ls_ls_market_price_dispersion(ls_ls_market_ids, master_price, series)
#
#ls_ls_m_ids_res = get_ls_ls_distance_market_ids_restricted(master_price, ls_ls_competitors, km_bound)
#ls_ls_mpd_res = get_ls_ls_market_price_dispersion(ls_ls_m_ids_res, master_price, series)
#  
## print 'Starting sample market price dispersion with cleaned prices'
## ls_ls_mpd_res_clean = get_ls_ls_market_price_dispersion(ls_ls_m_ids_res[0:10],
#                                                                # master_price,
#                                                                # series,
#                                                                # clean = True)
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
#print '\nMarket price dispersion: regressions \n'
#print smf.ols(formula = 'std_prices ~  nb_competitors', data = pd_master_pd).fit().summary()
#print smf.ols(formula = 'std_prices ~ nb_competitors + price', data = pd_master_pd).fit().summary()
#print smf.ols(formula = 'coeff_var_prices ~  nb_competitors', data = pd_master_pd).fit().summary()
#print smf.ols(formula = 'coeff_var_prices ~ nb_competitors + price', data = pd_master_pd).fit().summary()
#print smf.ols(formula = 'range_prices ~  nb_competitors', data = pd_master_pd).fit().summary()
#print smf.ols(formula = 'range_prices ~ nb_competitors + price', data = pd_master_pd).fit().summary()
#print smf.ols(formula = 'gain_search ~  nb_competitors', data = pd_master_pd).fit().summary()
#print smf.ols(formula = 'gain_search ~ nb_competitors + price', data = pd_master_pd).fit().summary()

# # REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE (NO PD & SMF)

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
