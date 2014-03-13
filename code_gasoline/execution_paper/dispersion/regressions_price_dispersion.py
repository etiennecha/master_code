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

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)

series = 'diesel_price'
km_bound = 5
zero_threshold = np.float64(1e-10)

master_np_prices = np.array(master_price['diesel_price'], np.float64)
df_price = pd.DataFrame(master_np_prices.T, index = master_price['dates'], columns = master_price['ids'])
#df_price = pd.DataFrame(master_price['diesel_price'],
#                        columns = master_price['dates'],
#                        index = master_price['ids']).T

# ################
# BUILD DATAFRAME
# ################

# DF PAIR PRICE DISPERSION
ls_ppd = []
for indiv_id, ls_indiv_comp in zip(master_price['ids'], ls_ls_competitors):
  indiv_ind_1 = master_price['ids'].index(indiv_id)
  for (comp_id, distance) in ls_indiv_comp:
    indiv_ind_2 = master_price['ids'].index(comp_id)
    if distance < km_bound:
      # ls_comp_pd = get_pair_price_dispersion(df_price[indiv_id], df_price[comp_id], light = False)
      ls_comp_pd = get_pair_price_dispersion(master_np_prices[indiv_ind_1],
                                             master_np_prices[indiv_ind_2], 
                                             light = False)
      ls_ppd.append([indiv_id, comp_id, distance] + ls_comp_pd)

ls_scalars = ['nb_spread', 'nb_same_price', 'nb_a_cheaper', 'nb_b_cheaper', 
                'nb_rr', 'pct_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr',
                'avg_abs_spread', 'avg_spread', 'std_spread']
ls_freq_std = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']
ls_chges = ['nb_days_1', 'nb_days_2', 'nb_prices_1', 'nb_prices_2',
            'nb_ctd_1', 'nb_ctd_2', 'nb_chges_1', 'nb_chges_2', 'nb_sim_chges',
            'nb_1_fol', 'nb_2_fol']
ls_columns = ['id_1', 'id_2', 'distance'] + ls_scalars + ls_freq_std
ls_ppd_light = [ppd[:3] + ppd[3] + get_ls_standardized_frequency(ppd[6][0]) for ppd in ls_ppd]
df_ppd = pd.DataFrame(ls_ppd_light, columns = ls_columns)
df_ppd['pct_same_price'] = df_ppd['nb_same_price'] / df_ppd['nb_spread']
pd.options.display.float_format = '{:6,.4f}'.format

# DF BRAND (LIGHT)
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

# MERGE DF BRANDS AND DF PAIR PD STATS (caution: changes order)
df_brands = df_brands.rename(columns={'id': 'id_1'})
df_ppd = pd.merge(df_ppd, df_brands, on='id_1')
df_brands = df_brands.rename(columns={'id_1': 'id_2'})
df_ppd = pd.merge(df_ppd, df_brands, on='id_2', suffixes=('_1', '_2'))

# ##################
# SOME STATS/GRAPHS
# ##################

# HISTOGRAM OF AVERAGE SPREADS
hist_test = plt.hist(np.abs(df_ppd['avg_spread'])[~pd.isnull(df_ppd['avg_spread'])].values, bins = 100)
for i in range(10):
  print i, len(df_ppd[np.abs(df_ppd['avg_spread']) > i * 10**(-2)]),\
        len(df_ppd[(np.abs(df_ppd['avg_spread']) > i * 10**(-2)) & (df_ppd['nb_rr'] > 10)])

df_ppd_nodiff = df_ppd[np.abs(df_ppd['avg_spread']) <= 0.02]
df_ppd_diff = df_ppd[np.abs(df_ppd['avg_spread']) > 0.02]
print len(df_ppd_nodiff), len(df_ppd_diff)

# SPREAD VS DISTANCE
print len(df_ppd_nodiff['pct_rr'][df_ppd_nodiff['pct_rr'] <= zero_threshold])
#hist_test = plt.hist(df_ppd_nodiff['pct_rr'][~pd.isnull(df_ppd_nodiff['pct_rr'])], bins = 50)
df_all = df_ppd_nodiff[(~pd.isnull(df_ppd_nodiff['pct_rr'])) & (df_ppd_nodiff['distance'] <= 3)]
df_close = df_ppd_nodiff[(~pd.isnull(df_ppd_nodiff['pct_rr'])) & (df_ppd_nodiff['distance'] <= 1)]
df_far = df_ppd_nodiff[(~pd.isnull(df_ppd_nodiff['pct_rr'])) & (df_ppd_nodiff['distance'] > 1)]
ecdf = ECDF(df_all['pct_rr'])
ecdf_close = ECDF(df_close['pct_rr'])
ecdf_far = ECDF(df_far['pct_rr'])
x = np.linspace(min(sample), max(sample))
y = ecdf(x)
y_close = ecdf_close(x)
y_far = ecdf_far(x)
plt.step(x, y)
plt.step(x, y_close)
plt.step(x, y_far)
print ks_2samp(df_close['pct_rr'], df_far['pct_rr'])
print len(sample), len(df_close), len(df_far)

for df_temp, name_df in zip([df_all, df_close, df_far], ['all', 'close', 'far']):
  print '\n%s' %name_df
  print 'OIL/SUP', len(df_temp[((df_temp['brand_type_e_1'] == 'SUP') & (df_temp['brand_type_e_2'] == 'OIL')) |\
                   ((df_temp['brand_type_e_1'] == 'OIL') & (df_temp['brand_type_e_2'] == 'SUP'))]) / float(len(df_temp))
  print 'SUP/SUP', len(df_temp[(df_temp['brand_type_e_1'] == 'SUP') &\
                               (df_temp['brand_type_e_2'] == 'SUP')]) / float(len(df_temp))
  print 'OIL/OIL', len(df_temp[(df_temp['brand_type_e_1'] == 'OIL') &\
                               (df_temp['brand_type_e_2'] == 'OIL')])/ float(len(df_temp))
  print 'IND/IND', len(df_temp[(df_temp['brand_type_e_1'] == 'IND') &\
                               (df_temp['brand_type_e_2'] == 'IND')])/ float(len(df_temp))

# ##################
# REGRESSION
# ##################

df_ppd_reg = df_ppd_nodiff
# TODO: LOOP AND STORE RESULTS FOR VARIOUS CASES!
df_ppd_reg = df_ppd_reg[(df_ppd_reg['brand_1_e_1'] != 'TOTAL_ACCESS') &\
                        (df_ppd_reg['brand_1_e_2'] != 'TOTAL_ACCESS') &\
                        (df_ppd_reg['brand_1_e_1'] != df_ppd_reg['brand_1_e_2'])]
# df_ppd_reg = df_ppd_reg[(df_ppd_reg['brand_type_e_1'] == 'OIL') & (df_ppd_reg['brand_type_e_2'] == 'OIL')]
df_ppd_reg = df_ppd_reg[((df_ppd_reg['brand_type_e_1'] == 'IND') & (df_ppd_reg['brand_type_e_2'] == 'SUP')) |\
                        ((df_ppd_reg['brand_type_e_1'] == 'SUP') & (df_ppd_reg['brand_type_e_2'] == 'IND'))]
df_ppd_reg['abs_avg_spread'] = np.abs(df_ppd_reg['avg_spread'])
# df_ppd_reg = df_ppd_reg[df_ppd_reg['abs_avg_spread'] <= 0.01]
print '\n', smf.ols(formula = 'abs_avg_spread ~ distance', data = df_ppd_reg).fit().summary()
print '\n', smf.ols(formula = 'avg_abs_spread ~ distance', data = df_ppd_reg).fit().summary()
print '\n', smf.ols(formula = 'pct_rr ~ distance', data = df_ppd_reg).fit().summary()
print '\n', smf.ols(formula = 'std_spread ~ distance', data = df_ppd_reg).fit().summary()



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
