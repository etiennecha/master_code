#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *
import itertools
import scipy
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import statsmodels.api as sm
import statsmodels.formula.api as smf
import time

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_built_graphs = os.path.join(path_dir_built_paper, 'data_graphs')
path_dir_brand_chges = os.path.join(path_dir_built_graphs, 'brand_changes')

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

ls_columns = [pd.to_datetime(date) for date in master_price['dates']]
df_price = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_columns).T

# #########################
# BRAND CHANGE DETECTION
# #########################

# todo: robustness of price control (no additivity...)
se_mean_price =  df_price.mean(1)
df_price_cl = df_price.apply(lambda x: x - se_mean_price)
window_limit = 20
beg_ind, end_ind = window_limit, len(df_price_cl) - window_limit
ls_se_mean_diffs = []
for day_ind in range(beg_ind, end_ind):
  ls_se_mean_diffs.append(df_price_cl[:day_ind].mean() - df_price_cl[day_ind:].mean())
df_mean_diffs = pd.DataFrame(dict(zip(df_price_cl.index[beg_ind:end_ind], ls_se_mean_diffs))).T
se_argmax = df_mean_diffs.apply(lambda x: x.abs()[~pd.isnull(x)].argmax()\
                                            if not all(pd.isnull(x)) else None)
ls_max = [df_mean_diffs[indiv_ind][day] if day else np.nan\
            for indiv_ind, day in zip(se_argmax.index, se_argmax.values)]
se_max = pd.Series(ls_max, index = se_argmax.index)
ls_candidates = se_max.index[np.abs(se_max) > 0.04] # consistency with numpy only method...

# Check if corresponds to a change in brand
# todo: exclude highly rigid prices

#dict_std_brands = {v[0]: v for k, v in dict_brands.items()}
dict_chge_brands = {}
for indiv_id, indiv_info in master_price['dict_info'].items():
  ls_brands = [brand_name for brand_name, brand_day_ind in indiv_info['brand']]
  if (len(ls_brands) > 1) and ('TOTAL ACCESS' in ls_brands):
    dict_chge_brands.setdefault('TA', []).append(indiv_id)
  elif (len(ls_brands) > 1) and ('ESSO EXPRESS' in ls_brands):
    dict_chge_brands.setdefault('EE', []).append(indiv_id)
  elif (len(ls_brands) > 1) and ('AVIA' in ls_brands):
    dict_chge_brands.setdefault('AV', []).append(indiv_id)
  elif len(ls_brands) > 1:
    dict_chge_brands.setdefault('OT', []).append(indiv_id)
  else:
    dict_chge_brands.setdefault('NO', []).append(indiv_id)

for chge in ['TA', 'EE', 'AV', 'OT', 'NO']:
  print chge, len([indiv_id for indiv_id in dict_chge_brands[chge] if indiv_id in ls_candidates])

## Plot prices which trigger detection vs. average price
## Either time or numeric index... string does not work for plot with vertical line
#df_price['avg_price'] = se_mean_price
#for chge, ls_chge_ids in dict_chge_brands.items():
#  path_dir_temp = os.path.join(path_dir_brand_chges, 'price_detection', chge)
#  if not os.path.exists(path_dir_temp):
#    os.makedirs(path_dir_temp)
#  ls_detected_chge_ids = [indiv_id for indiv_id in ls_chge_ids if indiv_id in ls_candidates]
#  for indiv_id in ls_detected_chge_ids:
#    ax = df_price[['avg_price', indiv_id]].plot(xlim = (df_price.index[0], df_price.index[-1]),
#                                                ylim=(1.2, 1.6))
#    ax.axvline(x = se_argmax[indiv_id], color='k', ls='dashed')
#    plt.savefig(os.path.join(path_dir_temp, 'chge_id_%s' %indiv_id))
#    plt.close()

# todo: Plot total access which do not trigger price detection
# toto: Check detected "other" => answer to total access etc?

## Draw TA station margin vs. competitors (upon margin chge detection)
# TODO: pbm of adding labels (e.g. id with brand + city as title)
path_dir_ta_comp_margins = os.path.join (path_dir_brand_chges, 'price_detection', 'TA_comp_margins')
for indiv_id in [indiv_id for indiv_id in dict_chge_brands['TA'] if indiv_id in ls_candidates]:
  indiv_ind = master_price['ids'].index(indiv_id)
  ls_ls_competitors[indiv_ind].sort(key=lambda x:x[1])
  ls_id_competitors = [indiv_id] + [id_competitor for (id_competitor, distance)\
                                    in ls_ls_competitors[indiv_ind][:5] if distance < 2]
  df_price_cl[ls_id_competitors].plot(xlim = (df_price_cl.index[0], df_price_cl.index[-1]),
                                      ylim=(-0.2, 0.2))
  plt.savefig(os.path.join(path_dir_ta_comp_margins, 'margins_id_%s' %indiv_id))
  plt.close()

# Change in margin with regressions? (margin: robustness checks?)
ls_ids_detected_ta = [indiv_id for indiv_id in dict_chge_brands['TA'] if indiv_id in ls_candidates]
indiv_id = ls_ids_detected_ta[0]

# Change in margin at competitors



#  legend_font_props = FontProperties()
#  legend_font_props.set_size('small')
#  handles, labels = ax.get_legend_handles_labels()
#  lgd = ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1, 0.5), prop = legend_font_props)
#  plt.savefig(path_data + folder_built_graphs + r'\total_access\price_vs_comp\price_comp_%s.png' %(indiv_ind),\
#                bbox_extra_artists=(lgd,), bbox_inches='tight')
#
#plt.clf()
#fig = plt.figure() 
#ax = fig.add_subplot(111)
#ax.plot(np_ar_mean_diffs[indiv_ind,:], label = '%s' %indiv_ind)
#ax.axvline(x = np_ar_diffs_argmaxs[indiv_ind],color='k',ls='dashed')
#if ls_ls_competitors[indiv_ind]:
#  for ind_competitor in ls_ind_competitors[:2]:
#    id_competitor = master_price['ids'][ind_competitor]
#    competitor_brands = [dict_brands[get_str_no_accent_up(brand)][0] for (brand, comp_day_ind)\
#                          in master_price['dict_info'][id_competitor]['brand']]
#    ax.plot(np_ar_mean_diffs[ind_competitor,:], label = '%s %s' %(ind_competitor,'-'.join(competitor_brands)))
#ax.set_title('%s-%s' %(master_price['dict_info'][master_price['ids'][indiv_ind]]['code_geo'],\
#                       master_price['dict_info'][master_price['ids'][indiv_ind]]['city']))
#legend_font_props = FontProperties()
#legend_font_props.set_size('small')
#handles, labels = ax.get_legend_handles_labels()
#lgd = ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1, 0.5), prop = legend_font_props)
#plt.savefig(path_data + folder_built_graphs + r'\total_access\mean_diff_vs_comp\md_comp_%s.png' %(indiv_ind),\
#                bbox_extra_artists=(lgd,), bbox_inches='tight')    
#
## todo: Correct brand info dates in generic_master_price
## todo: Single price variation then nan (or converse) in ind_1003 and others... => correct prices
## todo: Opposite price vars: 9106?
## 
## todo: Correct when chge detected improperly (or false positive):
## Bad period detection with 2923, 3098, 8300, 8887 => Can't fix easily (two changes...)
## Slight mistake in period detection 5551 (Dunno why)
## Exclude (border effect): 4760, 7323, 9010
## 
## todo: Correct when no chge detected
## Increase in price (back to prior policy?): 466
## Undetected: 9023, 8147 (not big)
## Price high for a Total Access: 7382, 4409 (late chges), 6265
## 
## todo: Deal with brand changes detected apart from total access
## Generally... false positive = get rid of those sensitive to one price 
## (Ideally: Window detection based on station's activity record...)
## Real chges (why?): 327,, 9888, 9841, 9744, 9735, 
## Ctd: 9414, 9161, 8909, 8689, 8292, 8247, 7475, 7094,
## Ctd: 6535, 6511, 6387, 6195, 6021, 5705, 5373, 4940,
## Ctd: 2927  3090, 2974, 2962, 2960, 2652,  2617, 2614
## (quite a few Agip, Avia...)



# #####################
# DEPRECATED
# #####################

## DETECT BRAND CHANGE: numpy only method
#start = time.clock()
#master_np_prices = np.array(master_price['diesel_price'], dtype = np.float32)
#matrix_np_prices_ma = np.ma.masked_array(master_np_prices, np.isnan(master_np_prices))
#ar_period_mean_prices = np.mean(matrix_np_prices_ma, axis = 0)
#window_limit = 20
#ls_mean_diffs = []
#matrix_np_prices_ma_cl = matrix_np_prices_ma - ar_period_mean_prices
#for i in range(window_limit, len(master_price['dates']) - window_limit):
#  ls_mean_diffs.append(np.nansum(matrix_np_prices_ma_cl[:,:i], axis = 1)/\
#                         np.sum(~np.isnan(matrix_np_prices_ma_cl[:,:i]), axis =1)-
#                       np.nansum(matrix_np_prices_ma_cl[:,i:], axis = 1)/\
#                         np.sum(~np.isnan(matrix_np_prices_ma_cl[:,i:]), axis =1))
#  ## CAUTION: scipy.stats.nanmea result vary as a function of # nan
#np_ar_mean_diffs = np.ma.array(ls_mean_diffs, fill_value=0).filled()
## Filling with np.nan generates pbm with argmax (lines full of nan)
#np_ar_mean_diffs = np_ar_mean_diffs.T
#np_ar_diffs_argmaxs = np.nanargmax(np.abs(np_ar_mean_diffs), axis = 1)
#np_ar_diffs_maxs = np.nanmax(np.abs(np_ar_mean_diffs), axis = 1)
#ls_candidates = np.where(np_ar_diffs_maxs > 0.04)[0].astype(int).tolist()
#print time.clock() - start

## todo: BRANDE CHGE DETECTION WITH REGRESSION
#ls_ls_results_reg = []
#for indiv_ind, indiv_id in enumerate(master_price['ids']):
#  ls_brands = [dict_brands[get_str_no_accent_up(brand)][0] for brand, period\
#                in master_price['dict_info'][indiv_id]['brand']]
#  ls_brands = [x[0] for x in itertools.groupby(ls_brands)]
#  if len(ls_brands) > 1 and 'TOTAL_ACCESS' in ls_brands:
#    ls_prices = master_price['diesel_price'][indiv_ind]
#    ar_margins = ar_period_mean_prices - np.array(ls_prices, dtype=np.float32)
#    ls_results_reg = []
#    for i in range(window_limit, len(ls_prices) - window_limit):
#      # regression
#      ls_dummy = [0 for j in range(i)] + [1 for j in range(len(ls_prices)-i)]
#      ar_dummy = np.array(ls_dummy, dtype=np.float32)
#      result = sm.OLS(ar_margins, ar_dummy, missing = 'drop').fit()
#      ls_results_reg.append(result)
#      # # mean difference
#    ls_ls_results_reg.append((indiv_ind, ar_margins, ls_results_reg))
#  ls_ls_r2a = [[result.rsquared_adj for result in ls_results_reg]\
#                  for indiv_ind, ar_margins, ls_results_reg in ls_results_reg]
#  ls_ls_margins = [ar_margins for indiv_ind, ar_margins, ls_results in ls_results_reg]
