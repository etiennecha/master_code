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

zero_threshold = np.float64(1e-10)

master_np_prices = np.array(master_price['diesel_price'], np.float64)
df_price = pd.DataFrame(master_np_prices.T, index = master_price['dates'], columns = master_price['ids'])
#df_price = pd.DataFrame(master_price['diesel_price'],
#                        columns = master_price['dates'],
#                        index = master_price['ids']).T

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
      se_prices_2 = se_prices_2 - avg_spread
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

# DF PPD WITH BRANDS (Merge may change order of pdd)
df_brands = df_brands.rename(columns={'id': 'id_1'})
df_ppd = pd.merge(df_ppd, df_brands, on='id_1')
df_brands = df_brands.rename(columns={'id_1': 'id_2'})
df_ppd = pd.merge(df_ppd, df_brands, on='id_2', suffixes=('_1', '_2'))

# ##################
# SOME STATS/GRAPHS
# ##################

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
x = np.linspace(min(df_all['pct_rr']), max(df_all['pct_rr']))
y = ecdf(x)
y_close = ecdf_close(x)
y_far = ecdf_far(x)
plt.step(x, y)
plt.step(x, y_close)
plt.step(x, y_far)
print ks_2samp(df_close['pct_rr'], df_far['pct_rr'])
print len(df_all['pct_rr']), len(df_close['pct_rr']), len(df_far['pct_rr'])

for df_temp, name_df in zip([df_all, df_close, df_far], ['all', 'close', 'far']):
  print '\n%s' %name_df
  print 'OIL/SUP', len(df_temp[((df_temp['brand_type_e_1'] == 'SUP') &\
                                (df_temp['brand_type_e_2'] == 'OIL')) |\
                               ((df_temp['brand_type_e_1'] == 'OIL') &\
                                (df_temp['brand_type_e_2'] == 'SUP'))]) / float(len(df_temp))
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

# ##############
# INVESTIGATIONS
# ##############

end, start = 0, 650

ppd_res = get_pair_price_dispersion(np.array(df_price['1500006'][end:start]),\
                                    np.array(df_price['1500003'][end:start]))[0:2]
print ppd_res[0], '\n', ppd_res[1:]

tfpc_res = get_stats_two_firm_price_chges(np.array(df_price['1500006'][end:start]),\
                                          np.array(df_price['1500003'][end:start]))
ls_tfpc_chges = ['nb_days_1', 'nb_days_2', 'nb_prices_1', 'nb_prices_2',
                 'nb_ctd_1', 'nb_ctd_2', 'nb_chges_1', 'nb_chges_2', 'nb_sim_chges',
                 'nb_1_fol', 'nb_2_fol']
print '\nAnalysis: two firm price changes'
print zip(ls_tfpc_chges, tfpc_res[:-2])
print tfpc_res[-2], '\n', tfpc_res[-1]

psp_res = get_two_firm_similar_prices(np.array(df_price['1500006'][end:start]),\
                                      np.array(df_price['1500003'][end:start]))
print '\nAnalysis: same price'
ls_psp = ['nb_day_spread', 'nb_same_price', 'sim_chge_same', 'nb_1_lead', 'nb_2_lead']
print zip(ls_psp, [psp_res[0], psp_res[1], psp_res[2], len(psp_res[3]), len(psp_res[4])])
print psp_res[3], '\n', psp_res[4], '\n', psp_res[5], '\n', psp_res[6]

"""
Caution: 
For same price analysis: Follower is the one to initiate change (matches other's price)
For price changes: if follower changes prices (to match) and then other moves: follower is considered to lead!
"""

#df_price[['1500006', '1500003']][end:start].plot()
print df_price[['1500006', '1500003']][130:150]

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
