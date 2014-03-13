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

## #################################
## PAIR PRICE DISPERSION: RAW PRICES
## #################################
#
## COMPUTE PAIR PRICE DISPERSION
#start = time.clock()
#ls_pair_price_dispersion = []
#ls_pair_competitors = []
#for ((indiv_id_1, indiv_id_2), distance) in ls_tuple_competitors:
#  # could check presence btw...
#  indiv_ind_1 = master_price['ids'].index(indiv_id_1)
#  indiv_ind_2 = master_price['ids'].index(indiv_id_2)
#  if distance < km_bound:
#    ls_pair_competitors.append(((indiv_id_1, indiv_id_2), distance))
#    ls_pair_price_dispersion.append(get_pair_price_dispersion(master_np_prices[indiv_ind_1],
#                                                              master_np_prices[indiv_ind_2],
#                                                              light = False))
#print 'Pair price dispersion:', time.clock() - start
#
## DF PAIR PD STATS
#ls_ppd_for_df = [elt[0] for elt in ls_pair_price_dispersion]
#ls_columns = ['avg_abs_spread', 'avg_spread', 'std_spread', 'nb_days_spread',
#              'percent_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr', 'nb_rr_conservative']
#df_ppd = pd.DataFrame(ls_ppd_for_df, columns = ls_columns)
#ls_max_len_rr = [np.max(elt[3][0]) if elt[3][0] else 0 for elt in ls_pair_price_dispersion]
#df_ppd['max_len_rr'] = ls_max_len_rr
#df_ppd['id_1'] = [comp[0][0] for comp in ls_pair_competitors]
#df_ppd['id_2'] = [comp[0][1] for comp in ls_pair_competitors]
#
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
df_ppd_brands = pd.merge(df_ppd, df_brands, on='id_1')
df_brands = df_brands.rename(columns={'id_1': 'id_2'})
df_ppd_brands = pd.merge(df_ppd_brands, df_brands, on='id_2', suffixes=('_1', '_2'))

df_ppd_brands = df_ppd_brands.rename(columns={'nb_rr_conservative': 'nb_rr'})
#
#ls_view_1 =['id_1', 'id_2', 'brand_1_e_1', 'brand_1_e_2', 
#            'nb_days_spread', 'avg_abs_spread', 'avg_spread', 'std_spread', 
#            'percent_rr', 'max_len_rr', 'avg_abs_spread_rr', 'nb_rr']
#print df_ppd_brands[ls_view_1][(np.abs(df_ppd_brands['avg_spread']) < 0.01) &\
#                               (df_ppd_brands['avg_abs_spread'] > 0.01)][0:50].to_string()
#
## Find suspect rank reversal
#print 'Station with max length rank reversal:', np.argmax(df_ppd['max_len_rr'])
#
## DF All
#print '\nDF All'
#print '% no rr', len(df_ppd_brands[df_ppd_brands['percent_rr'] <= zero_threshold])/\
#        float(len(df_ppd_brands))
#print '% rr avg', df_ppd_brands['percent_rr'].mean()
#print '% rr, no 0 ', df_ppd_brands['percent_rr'][df_ppd_brands['percent_rr'] > zero_threshold].mean()
#print 'max len rr avg',  df_ppd_brands['max_len_rr'].mean()
#print 'id, no 0', df_ppd_brands['max_len_rr'][df_ppd_brands['percent_rr'] >= zero_threshold].mean()
#
## DF Total Access
#print '\nDF Total Access'
#df_ppd_ta = df_ppd_brands[(df_ppd_brands['brand_2_e_2'] == 'TOTAL_ACCESS')|\
#                          (df_ppd_brands['brand_2_e_1'] == 'TOTAL_ACCESS')]
#print '% no rr', len(df_ppd_ta[df_ppd_ta['percent_rr'] <= zero_threshold])/\
#        float(len(df_ppd_ta))
#print '% rr avg', df_ppd_ta['percent_rr'].mean()
#print '% rr, no 0 ', df_ppd_ta['percent_rr'][df_ppd_ta['percent_rr'] > zero_threshold].mean()
#print 'max len rr avg',  df_ppd_ta['max_len_rr'].mean()
#print 'id, no 0', df_ppd_ta['max_len_rr'][df_ppd_ta['percent_rr'] >= zero_threshold].mean()
#
## DF No Total Access
#print '\nNo Total Access'
#df_ppd_nota = df_ppd_brands[(df_ppd_brands['brand_2_e_2'] != 'TOTAL_ACCESS')&\
#                            (df_ppd_brands['brand_2_e_1'] != 'TOTAL_ACCESS')]
#print '% no rr', len(df_ppd_nota[df_ppd_nota['percent_rr'] <= zero_threshold])/\
#        float(len(df_ppd_nota))
#print '% rr avg', df_ppd_nota['percent_rr'].mean()
#print '% rr, no 0 ', df_ppd_nota['percent_rr'][df_ppd_nota['percent_rr'] > zero_threshold].mean()
#print 'max len rr avg avg', df_ppd_nota['percent_rr'].mean()
#print 'id, no 0', df_ppd_nota['percent_rr'][df_ppd_nota['percent_rr'] > zero_threshold].mean()
#
## Other restrictions
#df_ppd_st = df_ppd_nota[df_ppd_nota['brand_type_e_1'] ==\
#                          df_ppd_nota['brand_type_e_2']]
#
#df_ppd_sup = df_ppd_nota[(df_ppd_nota['brand_type_e_1'] == 'SUP') &\
#                         (df_ppd_nota['brand_type_e_2'] == 'SUP')]
#
#df_ppd_oil = df_ppd_nota[(df_ppd_nota['brand_type_e_1'] == 'OIL') &\
#                         (df_ppd_nota['brand_type_e_2'] == 'OIL')]
#
## res = smf.ols('avg_spread~percent_rr', df_ppd_st, missing = 'drop').fit()
## res.summary()
#
## DF PAIR PD TEMPORAL
## (could start from simple spread and apply function to mask to each column...)
#
##ls_rr_spread = [pair_pd[2][1] for tup_comp, pair_pd\
##                  in zip(ls_pair_competitors, ls_pair_price_dispersion)] #if tup_comp[1] <= 3
#
#ls_rr_spread = []
#ls_ta_inds = []
#ls_nota_inds = []
#ls_rr_ta_day = []
#for i, (p_comp, p_pd) in enumerate(zip(ls_pair_competitors, ls_pair_price_dispersion)):
#  ls_rr_spread.append(p_pd[2][1])
#  if (df_brands['brand_1_e'][p_comp[0][0]] == 'TOTAL_ACCESS') or\
#     (df_brands['brand_1_e'][p_comp[0][1]] == 'TOTAL_ACCESS'):
#    ls_ta_inds.append(i)
#    if 639 in p_pd[1]: # to check...
#      ls_rr_ta_day.append(i)
#  else:
#    ls_nota_inds.append(i)
#
#df_rr_spread = pd.DataFrame(np.array(ls_rr_spread, np.float32))
#
## DF PAIR PD TEMPORAL (ALL PAIRS)
#ls_rr_temp = []
#for day_ind in df_rr_spread.columns:
#  nb_valid = len(df_rr_spread[day_ind][~pd.isnull(df_rr_spread[day_ind])])
#  se_rr = np.abs(df_rr_spread[day_ind][np.abs(df_rr_spread[day_ind]) >  zero_threshold])
#  nb_rr = len(se_rr)
#  med_rr = np.median(se_rr)
#  avg_rr = np.mean(se_rr)
#  ls_rr_temp.append([nb_valid, nb_rr, med_rr, avg_rr])
#ls_columns = ['nb_valid', 'nb_rr', 'med_rr', 'avg_rr']
#df_rr_temp = pd.DataFrame(ls_rr_temp, master_price['dates'], ls_columns)
#df_rr_temp['pct_rr'] = df_rr_temp['nb_rr'] / df_rr_temp['nb_valid']
#
## DF PAIR PD TEMPORAL TA
#df_rr_spread_ta = df_rr_spread.ix[ls_ta_inds]
#
#ls_rr_temp = []
#for day_ind in df_rr_spread_ta.columns:
#  nb_valid = len(df_rr_spread_ta[day_ind][~pd.isnull(df_rr_spread_ta[day_ind])])
#  se_rr = np.abs(df_rr_spread_ta[day_ind][np.abs(df_rr_spread_ta[day_ind]) >  zero_threshold])
#  nb_rr = len(se_rr)
#  med_rr = np.median(se_rr)
#  avg_rr = np.mean(se_rr)
#  ls_rr_temp.append([nb_valid, nb_rr, med_rr, avg_rr])
#ls_columns = ['nb_valid', 'nb_rr', 'med_rr', 'avg_rr']
#df_rr_temp_ta = pd.DataFrame(ls_rr_temp, master_price['dates'], ls_columns)
#df_rr_temp_ta['pct_rr'] = df_rr_temp_ta['nb_rr']/ df_rr_temp_ta['nb_valid']
#
## DF PAIR PD TEMPORAL NO TA
#df_rr_spread_nota = df_rr_spread.ix[ls_nota_inds]
#
#ls_rr_temp = []
#for day_ind in df_rr_spread_nota.columns:
#  nb_valid = len(df_rr_spread_nota[day_ind][~pd.isnull(df_rr_spread_nota[day_ind])])
#  se_rr = np.abs(df_rr_spread_nota[day_ind][np.abs(df_rr_spread_nota[day_ind]) >  zero_threshold])
#  nb_rr = len(se_rr)
#  med_rr = np.median(se_rr)
#  avg_rr = np.mean(se_rr)
#  ls_rr_temp.append([nb_valid, nb_rr, med_rr, avg_rr])
#ls_columns = ['nb_valid', 'nb_rr', 'med_rr', 'avg_rr']
#df_rr_temp_nota = pd.DataFrame(ls_rr_temp, master_price['dates'], ls_columns)
#df_rr_temp_nota['pct_rr'] = df_rr_temp_nota['nb_rr']/ df_rr_temp_nota['nb_valid']
#
## TODO: plot vs. margin !
#
#plt.plot(df_rr_temp['pct_rr'])
#plt.plot(df_rr_temp_nota['pct_rr'])
#plt.plot(df_rr_temp_ta['pct_rr'])
#plt.show()

# TODO: WITH CONTROL FOR PRICE
# TODO: VS. COST LEVEL

# ########################################
# PAIR PRICE DISPERSION: NORMALIZED PRICES
# ########################################

## COMPUTE PAIR PRICE DISPERSION
#start = time.clock()
#ls_pair_price_dispersion = []
#ls_pair_competitors = []
#for ((indiv_id_1, indiv_id_2), distance) in ls_tuple_competitors:
#  # could check presence btw...
#  indiv_ind_1 = master_price['ids'].index(indiv_id_1)
#  indiv_ind_2 = master_price['ids'].index(indiv_id_2)
#  if distance < km_bound:
#    ls_pair_competitors.append(((indiv_id_1, indiv_id_2), distance))
#    ar_price_1 = master_np_prices[indiv_ind_1]
#    ar_price_2 = master_np_prices[indiv_ind_2]
#    ar_diff = ar_price_1 - ar_price_2
#    ar_price_1_norm = ar_price_1 - ar_diff[~np.isnan(ar_diff)].mean()
#    ls_pair_price_dispersion.append(get_pair_price_dispersion(ar_price_1_norm,
#                                                              ar_price_2,
#                                                              light = False))
#print 'Pair price dispersion:', time.clock() - start
#
#def get_plot_normalized(ar_price_1, ar_price2):
#  # TODO: see if orient towards pandas or not
#  ar_diff = ar_price_1 - ar_price_2
#  ar_price_1_norm = ar_price_1 - ar_diff[~np.isnan(ar_diff)].mean()
#  plt.plot(ar_price_1_norm)
#  plt.plot(ar_price_2)
#  plt.plot(ar_price_1)
#  plt.show()
#  return
#
## DF PAIR PD STATS
#ls_ppd_for_df = [elt[0] for elt in ls_pair_price_dispersion]
#ls_columns = ['avg_abs_spread', 'avg_spread', 'std_spread', 'nb_days_spread',
#              'percent_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr', 'nb_rr_conservative']
#df_ppd = pd.DataFrame(ls_ppd_for_df, columns = ls_columns)
#ls_max_len_rr = [np.max(elt[3][0]) if elt[3][0] else 0 for elt in ls_pair_price_dispersion]
#df_ppd['max_len_rr'] = ls_max_len_rr
#df_ppd['id_1'] = [comp[0][0] for comp in ls_pair_competitors]
#df_ppd['id_2'] = [comp[0][1] for comp in ls_pair_competitors]
#
#df_brands = df_brands.rename(columns={'id_2': 'id_1'})
#df_ppd_brands = pd.merge(df_ppd, df_brands, on='id_1')
#df_brands = df_brands.rename(columns={'id_1': 'id_2'})
#df_ppd_brands = pd.merge(df_ppd_brands, df_brands, on='id_2', suffixes=('_1', '_2'))
#
#df_ppd_brands = df_ppd_brands.rename(columns={'nb_rr_conservative': 'nb_rr'})
#
#plt.hist(np.array(df_ppd_brands['avg_abs_spread'][~pd.isnull(df_ppd_brands['avg_abs_spread'])]), bins = 100)
#plt.hist(np.array(df_ppd_brands['max_len_rr'][~pd.isnull(df_ppd_brands['max_len_rr'])]), bins = 100)
#plt.hist(np.array(df_ppd_brands['nb_rr'][~pd.isnull(df_ppd_brands['nb_rr'])]), bins = 100)
#
### Change in price policy => high avg_abs_spread with low nb_rr => clear cut: exlude!
##print df_ppd_brands[ls_view_1][df_ppd_brands['avg_abs_spread'] > 0.03].to_string()
#print df_ppd_brands[ls_view_1][(df_ppd_brands['avg_abs_spread'] < 0.02) & \
#                               (df_ppd_brands['nb_rr'] > 30)].to_string()
#get_plot_normalized(np.array(df_price['95190001']), np.array(df_price['95500005']))

# ##################################
# PAIR PD: LOOK FOR REAL COMPETITORS 
# ##################################

km_bound = 20
ls_ls_indiv_pd = []
for indiv_id, ls_indiv_comp in zip(master_price['ids'], ls_ls_competitors):
  ls_indiv_pd = []
  indiv_ind_1 = master_price['ids'].index(indiv_id)
  for (comp_id, distance) in ls_indiv_comp:
    indiv_ind_2 = master_price['ids'].index(comp_id)
    if distance < km_bound:
      ls_comp_pd = get_pair_price_dispersion(master_np_prices[indiv_ind_1],
                                             master_np_prices[indiv_ind_2],
                                             light = False)
      if (ls_comp_pd[0][3] > 100) and (ls_comp_pd[0][1] < 0.2) and (ls_comp_pd[0][7] > 5):
        ls_indiv_pd.append([comp_id,
                            distance,
                            [ls_comp_pd[0], ls_comp_pd[1], ls_comp_pd[3]]])
  ls_ls_indiv_pd.append(ls_indiv_pd)

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
