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
  
  # GET RID OF MISSING PERIODS AND GET AVERAGE PRICE
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
  # np_ar_mean_diffs = np.ma.array(ls_mean_diffs, fill_value=0).filled() # fill with np.nan generates pbm with argmax
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
  
  # #########################
  # SERVICES (for INFO FILE)
  # #########################
  
  ls_listed_services = [service for indiv_id, indiv_info in master_info.items()\
                          if indiv_info['services'][-1] for service in indiv_info['services'][-1]]
  ls_listed_services = list(set(ls_listed_services))
  for indiv_id, indiv_info in master_info.items():
    if indiv_info['services'][-1] is not None:
      ls_station_services = [0 for i in ls_listed_services]
      for service in indiv_info['services'][-1]:
        service_ind = ls_listed_services.index(service)
        ls_station_services[service_ind] = 1
    else:
      ls_station_services = [None for i in ls_listed_services]
    master_info[indiv_id]['list_service_dummies'] = ls_station_services
  
  # ######
  # BRANDS
  # ######
  
  ls_ls_ls_brands = []
  for i in range(3):
    ls_ls_brands =  [[[dict_brands[get_str_no_accent_up(brand)][i], period]\
                          for brand, period in master_price['dict_info'][id_indiv]['brand']]\
                            for id_indiv in master_price['ids']]
    ls_ls_brands = [get_expanded_list(ls_brands, len(master_price['dates'])) for ls_brands in ls_ls_brands]
    ls_ls_ls_brands.append(ls_ls_brands)
  
  # ###########################################
  # PRICE REGRESSION : ONE PERIOD CROSS SECTION
  # ###########################################
  
  # day_ind = 0
  # ls_prices = [ls_prices[day_ind] for ls_prices in master_price['diesel_price']]
  # ls_brands_std = [ls_brands[day_ind] for ls_brands in ls_ls_ls_brands[0]]
  # ls_brands_gpd = [ls_brands[day_ind] for ls_brands in ls_ls_ls_brands[1]]
  # ls_types      = [ls_brands[day_ind] for ls_brands in ls_ls_ls_brands[2]]
  # dict_period = {'price' : ls_prices,
                 # 'brand' : ls_brands_gpd,
                 # 'type'  : ls_types}
  # pd_period_prices = pd.DataFrame(dict_period, index = master_price['ids'])
  # pd_period_prices['dpt'] =  pd_period_prices.index.map(lambda x: x[:-6])
  
  # y,X = patsy.dmatrices('price ~ brand', pd_period_prices, return_type='dataframe')
  # print sm.OLS(y, X, missing = 'drop').fit().summary()
  # y,X = patsy.dmatrices('price ~ brand + C(dpt)', pd_period_prices, return_type='dataframe')
  # print sm.OLS(y, X, missing = 'drop').fit().summary()
  # # TODO: read https://patsy.readthedocs.org/en/v0.1.0/categorical-coding.html
  
  # # stats des on brands / price quantiles per brands
  # print pd_period_prices['brand'].describe()
  # print pd_period_prices['brand'].value_counts()
  
  # # generate figure with price histograms per brand (?)
  # ls_of_brands = np.unique(pd_period_prices['brand'])
  # # should take sqrt of list length rounded above to unit
  # fig, axes = plt.subplots(nrows=5, ncols=5)
  # list_axes = [j for i in axes for j in i][:len(ls_of_brands)]
  # # harmonize scales? (then need to impose categories)
  # for i, ax in enumerate(list_axes):
    # brand_prices = pd_period_prices['price'][pd_period_prices['brand'] == ls_of_brands[i]]
    # test = ax.set_title('%s-%s'%(ls_of_brands[i], len(brand_prices[~np.isnan(brand_prices)])), fontsize=8)
    # # if brand_prices[~np.isnan(brand_prices)].tolist():
    # if len(brand_prices[~np.isnan(brand_prices)]) > 20:
      # test = ax.hist(brand_prices[~np.isnan(brand_prices)], bins = 20)
  # plt.rcParams['font.size'] = 8
  # plt.tight_layout()
  # # plt.show()
  
  # #########################################
  # PRICE REGRESSIONS : ALL PERIOD PANEL DATA
  # #########################################
  
  # build pd_mi_prices (long form)
  ls_all_prices = [price for ls_prices in master_price['diesel_price'] for price in ls_prices]
  ls_all_ids = [id_indiv for id_indiv in master_price['ids'] for x in range(len(master_price['dates']))]
  ls_all_dates = [date for id_indiv in master_price['ids'] for date in master_price['dates']]
  ls_ls_all_brands = [[brand for ls_brands in ls_ls_brands for brand in ls_brands]\
                          for ls_ls_brands in ls_ls_ls_brands]
  index = pd.MultiIndex.from_tuples(zip(ls_all_ids, ls_all_dates), names= ['id','date'])
  columns = ['price', 'brand_1', 'brand_2', 'brand_type']
  pd_mi_prices = pd.DataFrame(zip(*[ls_all_prices] + ls_ls_all_brands), index = index, columns = columns)
  pd_pd_prices = pd_mi_prices.to_panel()
  # build pd_df_info (simple info dataframe)
  ls_rows = []
  for indiv_ind, indiv_id in enumerate(master_price['ids']):
    city = master_price['dict_info'][indiv_id]['city']
    if city:
      city = city.replace(',',' ')
    zip_code = '%05d' %int(indiv_id[:-3])
    code_geo = master_price['dict_info'][indiv_id].get('code_geo')
    code_geo_ardts = master_price['dict_info'][indiv_id].get('code_geo_ardts')
    highway = None
    if master_info.get(indiv_id):
      highway = master_info[indiv_id]['highway'][3]
    region = dict_dpts_regions[zip_code[:2]]
    row = [indiv_id, city, zip_code, code_geo, code_geo_ardts, highway, region]
    ls_rows.append(row)
  header = ['id', 'city', 'zip_code', 'code_geo', 'code_geo_ardts', 'highway', 'region']
  pd_df_master_info = pd.DataFrame(zip(*ls_rows), header).T
  # merge info and prices
  pd_df_master_info = pd_df_master_info.set_index('id')
  pd_mi_prices = pd_mi_prices.reset_index()
  pd_mi_final = pd_mi_prices.join(pd_df_master_info, on = 'id')
  pd_mi_final = pd_mi_final.set_index(['id','date'])
  
  # TODO: restrict size to begin with (time/location)
  # pd_mi_final.ix['1500007',:] # based on id
  # pd_mi_final[pd_mi_final['code_geo'].str.startswith('01', na=False)] # based on insee
  # http://stackoverflow.com/questions/17242970/multi-index-sorting-in-pandas
  pd_mi_final_alt = pd_mi_final.swaplevel('id', 'date')
  pd_mi_final_alt = pd_mi_final_alt.sort()
  pd_mi_final_extract = pd_mi_final_alt.ix['20110904':'20111004']
  
  # # EXAMPLE PANEL DATA REGRESSIONS
  # from patsy import dmatrices
  # f = 'price~brand_2'
  # y, X = dmatrices(f, pd_mi_final_extract, return_type='dataframe')
  # sys.path.append(r'W:\Bureau\Etienne_work\Code\code_gasoline\code_gasoline_db_analysis\code_panel_regressions')
  # from panel import *
  # mod1 = PanelLM(y, X, method='pooling').fit()
  # mod2 = PanelLM(y, X, method='between').fit()
  # mod3 = PanelLM(y, X.ix[:,1:], method='within').fit()
  # mod4 = PanelLM(y, X.ix[:,1:], method='within', effects='time').fit()
  # mod5 = PanelLM(y, X.ix[:,1:], method='within', effects='twoways').fit()
  # mod6 = PanelLM(y, X, 'swar').fit()
  # mn = ['OLS', 'Between', 'Within N', 'Within T', 'Within 2w', 'RE-SWAR']
  # results = [mod1, mod2, mod3, mod4, mod5, mod6]
  # # Base group: Agip
  # # Equivalent to Stata FE is Within N (Within T: time effect...)
  # for i, result in enumerate(results):
    # print mn[i]
    # if len(X.columns) == len(result.params):
      # pprint.pprint(zip(X.columns, result.params, result.bse))
    # else:
      # pprint.pprint(zip(X.columns[1:], result.params, result.bse))
  
  # pprint.pprint(zip(map(lambda x: '{:<28}'.format(x[:25]), X.columns),
                    # map(lambda x: '{:8.3f}'.format(x), np.round(mod1.params,3).tolist()),
                    # map(lambda x: '{:8.3f}'.format(x), np.round(mod1.bse,3).tolist())))
  
  # ###########
  # DEPRECATED
  # ###########
  
  # # SMALL REMINDER ON PANDAS COMMANDS
  # pd_multi_index_master['price']
  # pd_multi_index_master.ix['10000001']
  # print X[u'brand[T.TOTAL_ACCESS]'].ix['10000001']
  # # Reorder columns
  # cols = X.columns.tolist()
  # cols = cols[:-2] + cols[-1:] + cols[-2:-1]
  # X = X[cols]
  
  # # Creates a dict: keys = station ids, contents = DataFrame with gas station prices and info etc
  # # e.g. data = {'Item1' : pd.DataFrame(np.random.randn(4,3)), 'Item2' : pd.DataFrame(np.random.randn(4,2))}
  # # e.g. panel_data = pd.Panel(data)
  # # list_formatted_dates = ['%s/%s/%s' %(elt[:4], elt[4:6], elt[6:]) for elt in master_price['dates']]
  # # index_formatted_dates = pd.to_datetime(list_formatted_dates)
  
  # # TODO: try station FE regression within a dpt and with 300 periods
  # # UGLY... PROBLEM SOLVED (TEMP)
  # dict_panel_data_master_temp = {}
  # for i, id in enumerate(master_price['ids']):
    # if 'code_geo' in master_price['dict_info'][id]: # temp: TODO: complete master_info
      # list_station_prices = master_price['diesel_price'][i]
      # list_station_brands = [dict_brands[get_str_no_accent_up(brand)][1] if brand else brand\
                              # for brand in get_field_as_list(id, 'brand', master_price)]
      # zip_code = '%05d' %int(id[:-3])
      # dict_station = {'price' : np.array(list_station_prices, dtype = np.float32),
                      # 'brand' : np.array(list_station_brands),
                      # 'zip_code' : zip_code,
                      # 'department' : zip_code[:2],
                      # 'region' : dict_dpts_regions[zip_code[:2]],
                      # 'insee_code' : master_price['dict_info'][id]['code_geo'],
                      # 'id' : id}
      # pd_df_station_temp = pd.DataFrame(dict_station, index = master_price['dates'])
      # dict_panel_data_master_temp[id] = pd_df_station_temp[0:300]
  # pd_pd_master_temp = pd.Panel(dict_panel_data_master_temp)
  # pd_pd_master_temp = pd_pd_master_temp.transpose('minor', 'items', 'major')
  # pd_mi_master_temp = pd_pd_master_temp.to_frame(filter_observations=False)
  # pd_mi_master_temp['price'] = pd_mi_master_temp['price'].astype(np.float32)
  # pd_dpt_01['date'] = pd_dpt_01.index.get_level_values(1)
  # pd_dpt_01 = pd_mi_master_temp[pd_mi_master_temp['department'] == '01']
  # res01 = smf.ols(formula = 'price ~ C(id) + C(date)', data = pd_dpt_01).fit()
  # # X = pd.DataFrame(pd_dpt_01[['id', 'date']], columns=["id", "date"])
  # # y_prediction = res01.predict(X)