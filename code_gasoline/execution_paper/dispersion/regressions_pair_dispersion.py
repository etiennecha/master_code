#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
#from statsmodels.distributions.empirical_distribution import ECDF
#from scipy.stats import ks_2samp

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')

path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_csv_insee_extract = os.path.join(path_dir_insee, 'data_extracts', 'data_insee_extract.csv')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)

zero_threshold = np.float64(1e-10)
pd.set_option('use_inf_as_null', True)
pd.options.display.float_format = '{:6,.4f}'.format

# DF PRICES
df_price = pd.DataFrame(master_price['diesel_price'], master_price['ids'], master_price['dates']).T

# DF CLEAN PRICES

## Prices cleaned with R / STATA
#path_csv_price_cl_R = os.path.join(path_dir_built_paper_csv, 'price_cleaned_R.csv')
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

df_price_cl = pd.read_csv(os.path.join(path_dir_built_csv, 'df_cleaned_prices.csv'),
                          index_col = 0,
                          parse_dates = True)

# ################
# BUILD DATAFRAME
# ################

km_bound = 5
diff_bound = 0.02

# TODO: iterate with various diff_bounds (high value: no cleaning of prices)

# DF PAIR PRICE DISPERSION
ls_ppd = []
for (indiv_id, comp_id), distance in ls_tuple_competitors:
  if distance <= km_bound: 
    se_prices_1 = df_price[indiv_id]
    se_prices_2 = df_price[comp_id]
    avg_spread = (se_prices_2 - se_prices_1).mean()
    if np.abs(avg_spread) > diff_bound:
      # se_prices_2 = se_prices_2 - avg_spread
      se_prices_1 = df_price_cl[indiv_id]
      se_prices_2 = df_price_cl[comp_id]
    ls_comp_pd = get_pair_price_dispersion(se_prices_1.as_matrix(),
                                           se_prices_2.as_matrix(), light = False)
    ls_comp_chges = get_stats_two_firm_price_chges(se_prices_1.as_matrix(),
                                                   se_prices_2.as_matrix())
    ls_ppd.append([indiv_id, comp_id, distance] +\
                  ls_comp_pd[0][:9] + [avg_spread] + ls_comp_pd[0][10:]+\
                  get_ls_standardized_frequency(ls_comp_pd[3][0]) +\
                  ls_comp_chges[:-2])
    #ls_ppd.append([indiv_id, comp_id, distance] + ls_comp_pd + ls_comp_chges[:-2])
#ls_ppd = [ppd[:3] + ppd[3] + get_ls_standardized_frequency(ppd[6][0]) for ppd in ls_ppd]

ls_scalars  = ['nb_spread', 'nb_same_price', 'nb_a_cheaper', 'nb_b_cheaper', 
               'nb_rr', 'pct_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr',
               'avg_abs_spread', 'avg_spread', 'std_spread']

ls_freq_std = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

ls_chges    = ['nb_days_1', 'nb_days_2', 'nb_prices_1', 'nb_prices_2',
               'nb_ctd_1', 'nb_ctd_2', 'nb_chges_1', 'nb_chges_2', 'nb_sim_chges',
               'nb_1_fol', 'nb_2_fol']

ls_columns  = ['id_1', 'id_2', 'distance'] + ls_scalars + ls_freq_std + ls_chges

df_ppd = pd.DataFrame(ls_ppd, columns = ls_columns)
df_ppd['pct_same_price'] = df_ppd['nb_same_price'] / df_ppd['nb_spread']
# Create same corner variables
df_ppd['sc_500'] = 0
df_ppd['sc_500'][df_ppd['distance'] <= 0.5] = 1
df_ppd['sc_750'] = 0
df_ppd['sc_750'][df_ppd['distance'] <= 0.75] = 1
df_ppd['sc_1000'] = 0
df_ppd['sc_1000'][df_ppd['distance'] <= 1] = 1

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

# DF INSEE
df_insee = pd.read_csv(path_csv_insee_extract, encoding = 'utf-8', dtype = str)
#df_insee = df_insee[['CODGEO', 'REG', 'DEP', 'STATUT_COM...?']]
#df_brands = pd.merge(df_brands, df_insee, right_column = 'codgeo', left_column = 'CODGEO')

# DF PPD WITH BRANDS (Merge may change order of pdd)
df_brands = df_brands.rename(columns={'id': 'id_1'})
df_ppd = pd.merge(df_ppd, df_brands, on='id_1')
df_brands = df_brands.rename(columns={'id_1': 'id_2'})
df_ppd = pd.merge(df_ppd, df_brands, on='id_2', suffixes=('_1', '_2'))

# CLEAN DF (avoid pbm with missing, inf which should be represented as missing etc.)
df_ppd = df_ppd[~(pd.isnull(df_ppd['std_spread']) | pd.isnull(df_ppd['pct_rr']))]
df_ppd = df_ppd[df_ppd['nb_spread'] > 60]
#df_ppd.replace([np.inf, -np.inf], np.nan).dropna(subset=["pct_rr", "std_spread"], how="all")
#df_ppd = df_ppd[(df_ppd['std_spread'] != np.inf) &\
#                (df_ppd['std_spread'] != -np.inf) &\
#                (df_ppd['pct_rr'] != np.inf) &\
#                (df_ppd['pct_rr'] ! -np.inf)]
df_ppd['abs_avg_spread'] = np.abs(df_ppd['avg_spread'])
### Need to avoid 0 in quantile regressions... pbmatic 
#df_ppd['pct_rr_nozero'] = df_ppd['pct_rr']
#df_ppd['pct_rr_nozero'][df_ppd['pct_rr'] == 0] = 0.00001
#df_ppd['std_spread_nozero'] = df_ppd['std_spread']
#df_ppd['std_spread_nozero'][df_ppd['std_spread'] == 0] = 0.00001
# TODO: check 0 rr => seems some duplicates

# RESTRICTIONS ON BRANDS / TYPES
# todo: loop for various cases
df_ppd = df_ppd[(df_ppd['brand_1_e_1'] != 'TOTAL_ACCESS') &\
                (df_ppd['brand_1_e_2'] != 'TOTAL_ACCESS') &\
                (df_ppd['brand_1_e_1'] != df_ppd['brand_1_e_2'])]
#df_ppd = df_ppd[(df_ppd['brand_type_e_1'] == 'OIL') & (df_ppd_reg['brand_type_e_2'] == 'OIL')]
#df_ppd = df_ppd[((df_ppd['brand_type_e_1'] == 'IND') & (df_ppd['brand_type_e_2'] == 'SUP'))|\
#                ((df_ppd['brand_type_e_1'] == 'SUP') & (df_ppd['brand_type_e_2'] == 'IND'))]

# DF NO DIFFERENTIATION VS. DIFFERENTIATION (CLEANED PRICES)
# todo: check that must be connected with criterion to clean prices...
df_ppd_nodiff = df_ppd[np.abs(df_ppd['avg_spread']) <= 0.02]
df_ppd_diff = df_ppd[np.abs(df_ppd['avg_spread']) > 0.02]
print len(df_ppd_nodiff), len(df_ppd_diff)

# ##################
# REGRESSION
# ##################

# REGRESSION FORMULAS AND PARAMETERS
ls_dist_ols_formulas = ['abs_avg_spread ~ distance',
                        'avg_abs_spread ~ distance',
                        'pct_rr ~ distance',
                        'std_spread ~ distance']

ls_sc_ols_formulas = ['abs_avg_spread ~ sc_500',
                      'avg_abs_spread ~ sc_500',
                      'pct_rr ~ sc_500',
                      'std_spread ~ sc_500']

# from statsmodels.regression.quantile_regression import QuantReg
ls_quantiles = [0.25, 0.5, 0.75, 0.9]

def get_df_ols_res(ls_ols_res, ls_index):
  ls_se_ols_res = []
  for reg_res in ls_ols_res:
    ls_reg_res = [reg_res.nobs, reg_res.rsquared, reg_res.rsquared_adj,
                reg_res.params, reg_res.bse, reg_res.tvalues]
    dict_reg_res = dict(zip(['NObs', 'R2', 'R2a'], ls_reg_res[:3]) +\
                        zip(['%s_be' %ind for ind in ls_reg_res[3].index], ls_reg_res[3].values)+\
                        zip(['%s_se' %ind for ind in ls_reg_res[4].index], ls_reg_res[4].values)+\
                        zip(['%s_t' %ind for ind in ls_reg_res[5].index], ls_reg_res[5].values))
    ls_se_ols_res.append(pd.Series(dict_reg_res))
  df_ols_res = pd.DataFrame(ls_se_ols_res, index = ls_index)
  return df_ols_res

#mod = smf.quantreg('pct_rr~distance', df_ppd_reg[~pd.isnull(df_ppd_reg['pct_rr'])])
#res = mod.fit(q=.5)
#print res.summary()
## Following: need to add constant to make it equivalent
#res_alt = QuantReg(df_ppd_reg['pct_rr_nozero'], df_ppd_reg['sc_500']).fit(0.5)
# So far: need to add "resid[resid == 0] = .000001" in quantreg line 171-3 to have it run

ls_df_reg_res = []
for df_ppd_reg in [df_ppd_nodiff, df_ppd_diff]:
  ls_dist_ols_res = [smf.ols(formula = str_formula, data = df_ppd_reg).fit()\
                       for str_formula in ls_dist_ols_formulas]
  ls_sc_ols_res   = [smf.ols(formula = str_formula, data = df_ppd_reg).fit()\
                       for str_formula in ls_sc_ols_formulas]
  ls_rr_qreg_res  = [smf.quantreg('pct_rr~sc_500', data = df_ppd_reg).fit(quantile)\
                       for quantile in ls_quantiles]
  ls_std_qreg_res = [smf.quantreg('std_spread~sc_500', data = df_ppd_reg).fit(quantile)\
                       for quantile in ls_quantiles]
  ls_ls_reg_res = [ls_dist_ols_res, ls_sc_ols_res, ls_rr_qreg_res, ls_std_qreg_res]
  ls_ls_index = [ls_dist_ols_formulas, ls_dist_ols_formulas, ls_quantiles, ls_quantiles]
  ls_df_reg_res.append([get_df_ols_res(ls_ols_res, ls_index)\
                          for ls_ols_res, ls_index in zip(ls_ls_reg_res, ls_ls_index)])

print 'Compare raw prices vs. prices not raw:'

print '\nOLS: Distance'
print ls_df_reg_res[0][0][['distance_be', 'distance_t', 'R2', 'NObs']].to_string()
print ls_df_reg_res[1][0][['distance_be', 'distance_t', 'R2', 'NObs']].to_string()

print '\nOLS: Same corner'
print ls_df_reg_res[0][1][['sc_500_be', 'sc_500_t', 'R2', 'NObs']].to_string()
print ls_df_reg_res[1][1][['sc_500_be', 'sc_500_t', 'R2', 'NObs']].to_string()

print '\nQR: Rank reversal (Check vs. R?)'
print ls_df_reg_res[0][2][['sc_500_be', 'sc_500_t', 'R2', 'NObs']].to_string()
print ls_df_reg_res[1][2][['sc_500_be', 'sc_500_t', 'R2', 'NObs']].to_string()

print '\nQR: Std spread (Check vs. R?)'
print ls_df_reg_res[0][3][['sc_500_be', 'sc_500_t', 'R2', 'NObs']].to_string()
print ls_df_reg_res[1][3][['sc_500_be', 'sc_500_t', 'R2', 'NObs']].to_string()

# check => https://groups.google.com/forum/?hl=fr#!topic/pystatsmodels/XnXu_k1h-gc

## Output data to csv to run quantile regressions in R
#path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')
#df_ppd.to_csv(os.path.join(path_dir_built_csv, 'data_ppd.csv'))

# ##############
# INVESTIGATIONS
# ##############

#end, start = 0, 650
#
#ppd_res = get_pair_price_dispersion(np.array(df_price['1500006'][end:start]),\
#                                    np.array(df_price['1500003'][end:start]))[0:2]
#print ppd_res[0], '\n', ppd_res[1:]
#
#tfpc_res = get_stats_two_firm_price_chges(np.array(df_price['1500006'][end:start]),\
#                                          np.array(df_price['1500003'][end:start]))
#ls_tfpc_chges = ['nb_days_1', 'nb_days_2', 'nb_prices_1', 'nb_prices_2',
#                 'nb_ctd_1', 'nb_ctd_2', 'nb_chges_1', 'nb_chges_2', 'nb_sim_chges',
#                 'nb_1_fol', 'nb_2_fol']
#print '\nAnalysis: two firm price changes'
#print zip(ls_tfpc_chges, tfpc_res[:-2])
#print tfpc_res[-2], '\n', tfpc_res[-1]
#
#psp_res = get_two_firm_similar_prices(np.array(df_price['1500006'][end:start]),\
#                                      np.array(df_price['1500003'][end:start]))
#print '\nAnalysis: same price'
#ls_psp = ['nb_day_spread', 'nb_same_price', 'sim_chge_same', 'nb_1_lead', 'nb_2_lead']
#print zip(ls_psp, [psp_res[0], psp_res[1], psp_res[2], len(psp_res[3]), len(psp_res[4])])
#print psp_res[3], '\n', psp_res[4], '\n', psp_res[5], '\n', psp_res[6]
#
#"""
#Caution: 
#For same price analysis: Follower is the one to initiate change (matches other's price)
#For price changes: if follower changes prices (to match) and then other moves: follower is considered to lead!
#"""
#
##df_price[['1500006', '1500003']][end:start].plot()
#print df_price[['1500006', '1500003']][130:150]

# ###########
# DEPRECATED
# ###########

# DF PAIR PRICE DISPERSION
#ls_pairs = []
#ls_ppd = []
#for indiv_id, ls_indiv_comp in zip(master_price['ids'], ls_ls_competitors):
#  indiv_ind_1 = master_price['ids'].index(indiv_id)
#  for (comp_id, distance) in ls_indiv_comp:
#    if (distance <= km_bound) and (comp_id, indiv_id) not in ls_pairs:
#      ls_pairs.append((indiv_id, comp_id))
#      indiv_ind_2 = master_price['ids'].index(comp_id)
#      #ls_comp_pd = get_pair_price_dispersion(df_price[indiv_id], df_price[comp_id], light = False)
#      ls_comp_pd = get_pair_price_dispersion(master_np_prices[indiv_ind_1],
#                                             master_np_prices[indiv_ind_2], 
#                                             light = False)
#      ls_comp_chges = get_stats_two_firm_price_chges(master_np_prices[indiv_ind_1],
#                                                     master_np_prices[indiv_ind_2])
#      ls_ppd.append([indiv_id, comp_id, distance] +\
#                    ls_comp_pd[0] +\
#                    get_ls_standardized_frequency(ls_comp_pd[3][0]) +\
#                    ls_comp_chges[:-2])
#      #ls_ppd.append([indiv_id, comp_id, distance] + ls_comp_pd + ls_comp_chges[:-2])

## DF PRICE CHGES
#ls_indiv_chges = []
#for indiv_ind, indiv_id in enumerate(master_price['ids']):
#  ls_indiv_chges.append(get_stats_price_chges(master_np_prices[indiv_ind], light = True))
#ls_columns = ['nb_all_chges', 'nb_valid', 'nb_no_chge', 'nb_chges', 'nb_neg_chges', 'nb_pos_chges',
#                'avg_neg_chge', 'avg_pos_chge', 'med_neg_chge', 'med_pos_chge']
#df_indiv_chges = pd.DataFrame(ls_indiv_chges, index = master_price['ids'], columns = ls_columns)
#df_brands = pd.merge(df_brands, df_indiv_chges, right_index = True, left_index = True)



## OLD: PAIR PRICE DISPERSION (PD & SMF)
#
#matrix_pair_pd = np.array([pd_tuple for pd_tuple in ls_pair_price_dispersion if pd_tuple[1] < km_bound])
## col 1: distance, (col 2: duration, col 4: avg_spread), col 5: std_spread, col 6: rank reversals
#matrix_pair_pd = np.array(np.vstack([matrix_pair_pd[:,1],
#                                     matrix_pair_pd[:,5], 
#                                     matrix_pair_pd[:,6]]), dtype = np.float32).T
#pd_pair_pd = pd.DataFrame(matrix_pair_pd, columns = ['distance', 'spread_std', 'rank_reversals'])
#pd_pair_pd = pd_pair_pd.dropna()

## OLD: REGRESSION OF PAIR PRICE DISPERSION ON DISTANCE (NO PD & SMF)

#distance = np.vstack([matrix_pair_pd[:,0]]).T
#spread_std = matrix_pair_pd[:,1]
#rank_reversals = matrix_pair_pd[:,2]
#print '\n REGRESSIONS OF PAIR PRICE DISPERSION ON DISTANCE \n'
#res_prr = sm.OLS(rank_reversals, sm.add_constant(distance), missing = "drop").fit()
#print res_prr.summary(yname='rank_reversals', xname = ['constant', 'distance'])
#res_sstd = sm.OLS(spread_std, sm.add_constant(distance), missing = "drop").fit()
#print res_sstd.summary(yname='spread_std', xname = ['constant', 'distance'])
