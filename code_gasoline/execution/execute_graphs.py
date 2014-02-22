import os, sys
import json
import itertools
import math
import copy
import random
import pprint
import numpy as np
import scipy
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import patsy
import xlrd
from generic_master_price import *

# PRICE CHANGE VALUE AND FREQUENCY ANALYSIS FUNCTIONS

if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  folder_source_brand = r'\data_gasoline\data_source\data_stations\data_brands'
  master_price = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')
  master_info = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_info_diesel')
  ls_ls_competitors = dec_json(path_data + folder_built_master_json + r'\master_diesel\list_list_competitors')
  list_tuple_competitors = dec_json(path_data + folder_built_master_json + r'\master_diesel\list_tuple_competitors')
  
  dict_brands = dec_json(path_data + folder_source_brand + r'\dict_brands')
  
  folder_dpts_regions = r'\data_insee\Regions_departements'
  dict_dpts_regions = dec_json(path_data + folder_dpts_regions + r'\dict_dpts_regions')
  
  folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'
  
  # GET AVERAGE PRICE
  master_np_prices = np.array(master_price['diesel_price'], dtype = np.float32)
  matrix_np_prices_ma = np.ma.masked_array(master_np_prices, np.isnan(master_np_prices))
  ar_nb_valid_prices = np.ma.count(matrix_np_prices_ma, axis = 0) # would be safer to count nan..
  ar_period_mean_prices = np.mean(matrix_np_prices_ma, axis = 0)
  
  # #########################
  # BRAND CHANGE DETECTION
  # #########################
  
  # window_limit = 20
  # ls_mean_diffs = []
  # matrix_np_prices_ma_cl = matrix_np_prices_ma - ar_period_mean_prices
  # for i in range(window_limit, len(master_price['dates']) - window_limit):
    # ls_mean_diffs.append(np.nansum(matrix_np_prices_ma_cl[:,:i], axis = 1)/\
                          # np.sum(~np.isnan(matrix_np_prices_ma_cl[:,:i]), axis =1)-
                         # np.nansum(matrix_np_prices_ma_cl[:,i:], axis = 1)/\
                           # np.sum(~np.isnan(matrix_np_prices_ma_cl[:,i:]), axis =1))
    # # # CAUTION: stats.nanmean first compute with 0 instead of nan then adjusts : imprecision...
    # # scipy.stats.nanmean(matrix_np_prices_ma_cl[:,:i], axis= 1) -\
                          # # scipy.stats.nanmean(matrix_np_prices_ma_cl[:,i:], axis= 1))
  # np_ar_mean_diffs = np.ma.array(ls_mean_diffs, fill_value=0).filled()
  # # fill with np.nan generates pbm with argmax

  # np_ar_mean_diffs = np_ar_mean_diffs.T
  # np_ar_diffs_maxs = np.nanmax(np.abs(np_ar_mean_diffs), axis = 1)
  # np_ar_diffs_argmaxs = np.nanargmax(np.abs(np_ar_mean_diffs), axis = 1)
  # ls_candidates = np.where(np_ar_diffs_maxs > 0.04)[0].astype(int).tolist()
  # # Check if corresponds to a change in brand (TODO: exclude highly rigid prices)
  
  # ls_total_access_chges = []
  # ls_total_access_no_chges = []
  # for indiv_ind, indiv_id in enumerate(master_price['ids']):
    # ls_brands = [dict_brands[get_str_no_accent_up(brand)][0] for brand, period\
                  # in master_price['dict_info'][indiv_id]['brand']]
    # ls_brands = [x[0] for x in itertools.groupby(ls_brands)]
    # if len(ls_brands) > 1 and 'TOTAL_ACCESS' in ls_brands:
      # if indiv_ind in ls_candidates:
        # ls_total_access_chges.append(indiv_ind)
      # else:
        # ls_total_access_no_chges.append(indiv_ind)
  
  folder_built_graphs = r'\data_gasoline\data_built\data_graphs'
  # for indiv_ind in ls_total_access_chges:
    # indiv_id = master_price['ids'][indiv_ind]
    # plt.clf()
    # fig = plt.figure() 
    # ax = fig.add_subplot(111)
    # ax.plot(ar_period_mean_prices)
    # ax.plot(matrix_np_prices_ma[indiv_ind,:])
    # ax.axvline(x = np_ar_diffs_argmaxs[indiv_ind] + window_limit,color='k',ls='dashed')
    # ax.set_xlim([0,len(master_price['dates'])]) 
    # ax.set_ylim([1.2, 1.6]) 
    # plt.savefig(path_data + folder_built_graphs + r'\total_access\mean_diff\chge_ind_%s_id_%s' %(indiv_ind, indiv_id))
  
  # for indiv_ind in ls_total_access_no_chges:
    # indiv_id = master_price['ids'][indiv_ind]
    # plt.clf()
    # plt.plot(ar_period_mean_prices)
    # plt.plot(matrix_np_prices_ma[indiv_ind,:])
    # plt.savefig(path_data + folder_built_graphs + r'\total_access\mean_diff\nochge_ind_%s_id_%s' %(indiv_ind, indiv_id))
  
  # for indiv_ind in ls_candidates:
    # if indiv_ind not in ls_total_access_chges:
      # indiv_id = master_price['ids'][indiv_ind]
      # plt.clf()
      # plt.plot(ar_period_mean_prices)
      # plt.plot(matrix_np_prices_ma[indiv_ind,:])
      # plt.axvline(x = np_ar_diffs_argmaxs[indiv_ind] + window_limit, color='k',ls='dashed')
      # plt.title('-'.join([x[0] for x in master_price['dict_info'][indiv_id]['brand']]))
      # plt.savefig(path_data + folder_built_graphs + r'\total_access\not_ta\ind_%s_id_%s' %(indiv_ind, indiv_id))
  
    # draw station price series vs. competitors
    # TODO: make it relative to avg price and limit nb of competitors on graph (criteria?)
  
  # for indiv_ind in ls_total_access_chges:
    # plt.clf()
    # fig = plt.figure() 
    # ax = fig.add_subplot(111)
    # ax.plot(ar_period_mean_prices)
    # ax.plot(matrix_np_prices_ma[indiv_ind,:], label = '%s' %indiv_ind)
    # ax.axvline(x = np_ar_diffs_argmaxs[indiv_ind] + window_limit,color='k',ls='dashed')
    # if ls_ls_competitors[indiv_ind]:
      # ls_ls_competitors[indiv_ind].sort(key=lambda x:x[1])
      # ls_id_competitors = [id_competitor for (id_competitor, distance)\
                            # in ls_ls_competitors[indiv_ind][:5] if distance < 2]
      # ls_ind_competitors = [master_price['ids'].index(id_competitor) for id_competitor\
                              # in ls_id_competitors if id_competitor in master_price['ids']]
      # for ind_competitor in ls_ind_competitors[:2]:
        # id_competitor = master_price['ids'][ind_competitor]
        # competitor_brands = [dict_brands[get_str_no_accent_up(brand)][0] for (brand, comp_day_ind)\
                              # in master_price['dict_info'][id_competitor]['brand']]
        # ax.plot(matrix_np_prices_ma[ind_competitor,:], label = '%s %s' %(ind_competitor,'-'.join(competitor_brands)))
    # ax.set_xlim([0, len(master_price['dates'])])
    # ax.set_ylim([1.2, 1.6])
    # ax.set_title('%s-%s' %(master_price['dict_info'][master_price['ids'][indiv_ind]]['code_geo'],\
                           # master_price['dict_info'][master_price['ids'][indiv_ind]]['city']))
    # legend_font_props = FontProperties()
    # legend_font_props.set_size('small')
    # handles, labels = ax.get_legend_handles_labels()
    # lgd = ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1, 0.5), prop = legend_font_props)
    # plt.savefig(path_data + folder_built_graphs + r'\total_access\price_vs_comp\price_comp_%s.png' %(indiv_ind),\
                  # bbox_extra_artists=(lgd,), bbox_inches='tight')
    
    # plt.clf()
    # fig = plt.figure() 
    # ax = fig.add_subplot(111)
    # ax.plot(np_ar_mean_diffs[indiv_ind,:], label = '%s' %indiv_ind)
    # ax.axvline(x = np_ar_diffs_argmaxs[indiv_ind],color='k',ls='dashed')
    # if ls_ls_competitors[indiv_ind]:
      # for ind_competitor in ls_ind_competitors[:2]:
        # id_competitor = master_price['ids'][ind_competitor]
        # competitor_brands = [dict_brands[get_str_no_accent_up(brand)][0] for (brand, comp_day_ind)\
                              # in master_price['dict_info'][id_competitor]['brand']]
        # ax.plot(np_ar_mean_diffs[ind_competitor,:], label = '%s %s' %(ind_competitor,'-'.join(competitor_brands)))
    # ax.set_title('%s-%s' %(master_price['dict_info'][master_price['ids'][indiv_ind]]['code_geo'],\
                           # master_price['dict_info'][master_price['ids'][indiv_ind]]['city']))
    # legend_font_props = FontProperties()
    # legend_font_props.set_size('small')
    # handles, labels = ax.get_legend_handles_labels()
    # lgd = ax.legend(handles, labels, loc='center left', bbox_to_anchor=(1, 0.5), prop = legend_font_props)
    # plt.savefig(path_data + folder_built_graphs + r'\total_access\mean_diff_vs_comp\md_comp_%s.png' %(indiv_ind),\
                  # bbox_extra_artists=(lgd,), bbox_inches='tight')    
  
  # TODO: Correct brand info dates in generic_master_price
  # TODO: Single price variation then nan (or converse) in ind_1003 and others... => correct prices
  # TODO: Opposite price vars: 9106?
  
  # TODO: Correct when chge detected improperly (or false positive):
  # Bad period detection with 2923, 3098, 8300, 8887 => Can't fix easily (two changes...)
  # Slight mistake in period detection 5551 (Dunno why)
  # Exclude (border effect): 4760, 7323, 9010
  
  # TODO: Correct when no chge detected
  # Increase in price (back to prior policy?): 466
  # Undetected: 9023, 8147 (not big)
  # Price high for a Total Access: 7382, 4409 (late chges), 6265
  
  # TODO: Deal with brand changes detected apart from total access
  # Generally... false positive = get rid of those sensitive to one price 
  # (Ideally: Window detection based on station's activity record...)
  # Real chges (why?): 327,, 9888, 9841, 9744, 9735, 
  # Ctd: 9414, 9161, 8909, 8689, 8292, 8247, 7475, 7094,
  # Ctd: 6535, 6511, 6387, 6195, 6021, 5705, 5373, 4940,
  # Ctd: 2927  3090, 2974, 2962, 2960, 2652,  2617, 2614
  # (quite a few Agip, Avia...)
  
  # TODO: BRANDE CHGE DETECTION WITH REGRESSION
  # ls_ls_results_reg = []
  # for indiv_ind, indiv_id in enumerate(master_price['ids']):
    # ls_brands = [dict_brands[get_str_no_accent_up(brand)][0] for brand, period\
                  # in master_price['dict_info'][indiv_id]['brand']]
    # ls_brands = [x[0] for x in itertools.groupby(ls_brands)]
    # if len(ls_brands) > 1 and 'TOTAL_ACCESS' in ls_brands:
      # ls_prices = master_price['diesel_price'][indiv_ind]
      # ar_margins = ar_period_mean_prices - np.array(ls_prices, dtype=np.float32)
      # ls_results_reg = []
      # for i in range(window_limit, len(ls_prices) - window_limit):
        # # regression
        # ls_dummy = [0 for j in range(i)] + [1 for j in range(len(ls_prices)-i)]
        # ar_dummy = np.array(ls_dummy, dtype=np.float32)
        # result = sm.OLS(ar_margins, ar_dummy, missing = 'drop').fit()
        # ls_results_reg.append(result)
        # # # mean difference
      # ls_ls_results_reg.append((indiv_ind, ar_margins, ls_results_reg))
  # # ls_ls_r2a = [[result.rsquared_adj for result in ls_results_reg]\
                  # # for indiv_ind, ar_margins, ls_results_reg in ls_results_reg]
  # # ls_ls_margins = [ar_margins for indiv_ind, ar_margins, ls_results in ls_results_reg]