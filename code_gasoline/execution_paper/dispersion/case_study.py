#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import datetime
import time
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')
path_ls_ls_markets = os.path.join(path_dir_built_json, 'ls_ls_markets.json')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_graphs = os.path.join(path_dir_built_paper, 'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
ls_ls_markets = dec_json(path_ls_ls_markets)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

pd.options.display.float_format = '{:6,.4f}'.format
series = 'diesel_price'
km_bound = 3
zero_threshold = np.float64(1e-10)

# DF PRICES
ls_dates = [pd.to_datetime(date) for date in master_price['dates']]
df_price = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_dates).T
se_mean_price = df_price.mean(1)

# DF PRICES CLEANED
df_price_cl = pd.read_csv(os.path.join(path_dir_built_csv, 'df_cleaned_prices.csv'),
                          index_col = 0,
                          parse_dates = True)
# df_price_cl.index = [datetime.datetime.strftime(x, '%Y%m%d') for x in df_price_cl.index]

# ################
# BUILD DATAFRAME
# ################

# DF MARKET PRICE DISPERSION
ls_ls_market_ids = get_ls_ls_distance_market_ids(master_price['ids'],
                                                 ls_ls_competitors, km_bound)
ls_ls_market_ids_st = get_ls_ls_distance_market_ids_restricted(master_price['ids'],
                                                               ls_ls_competitors, km_bound)
ls_ls_market_ids_st_rd = get_ls_ls_distance_market_ids_restricted(master_price['ids'],
                                                                  ls_ls_competitors, km_bound, True)
ls_ls_markets = [ls_market for ls_market in ls_ls_markets if len(ls_market) > 2]

# EXAMPLE: AMBERIEU EN BUGEY

ls_case_studies = ['1500001', # not many rr
                   '3800001', # idem
                   '4100002', # idem
                   '80600001', # rr ?
                   '87500001', # rr ?
                   '9190001', # rr ?
                   '11300001', # rr ?
                   '22100001'] # rr ?
for k, case_id in enumerate(ls_case_studies[0:1]):
  for ls_market in ls_ls_market_ids:
  	if case_id in ls_market:
  		break
  path_temp = os.path.join(path_dir_graphs,
                           'stable_markets',
                           'case_study_%s' %k)
  if not os.path.exists(path_temp):
    os.makedirs(path_temp)
  
  # 1/ Plot market prices: raw, cleaned, cleaned alternative
  
  ## Raw prices
  plt.rcParams['figure.figsize'] = 20, 10 
  df_price[ls_market].plot()
  plt.savefig(os.path.join(path_temp, '%s' %(case_id)))
  plt.close()

  ## Cleaned prices (residuals)
  #df_price_cl[ls_market][:'2012-06'].plot()
  #plt.show()
  #
  ## Cleaned prices: alternative way
  #ls_harmonized_series = [df_price[ls_market[0]]]
  #for comp_id in ls_market[1:]:
  #	ls_harmonized_series.append(df_price[comp_id] +\
  #    (df_price[ls_market[0]] - df_price[comp_id]).median())
  #df_market = pd.DataFrame(dict(zip(ls_market, ls_harmonized_series)))
  ## df_market['range'] = df_market.max(1) - df_market.min(1) + 1 # for graph
  #df_market[:'2012-06'].plot()
  #plt.show()
  
  # 2/ compute spreads, leader follower, matched prices, rank reversals, market dispersion
  
  # Pair: compute stats and display graphs
  #indiv_id = ls_market[0]
  #comp_id = ls_market[1]
 
  # TODO: filter interesting cases only
  # TODO: output text file with stats summary (gen tex report?)
  # TODO: location + market info?

  plt.rcParams['figure.figsize'] = 20, 10 
  for i, indiv_id in enumerate(ls_market):
    for comp_id in ls_market[i+1:]:
      # todo: create clean classes...
      ls_two_cols = ['nb_days_1', 'nb_days_2', 'nb_prices_1', 'nb_prices_2',
                     'nb_ctd_1', 'nb_ctd_2', 'nb_chges_1', 'nb_chges_2', 'nb_sim_chges',
                      'nb_1_fol', 'nb_2_fol']
      ls_two_res = get_stats_two_firm_price_chges(df_price[indiv_id].values,
                                                  df_price[comp_id].values)
      # function does not work with pandas series for now
      se_rows = pd.Series(ls_two_res[:-2], ls_two_cols)
      ls_sim_cols = ['len_spread', 'len_same', 'ls_chge_to_same',
                     'ls_1_lead', 'ls_2_lead', 'ls_ctd_1', 'ls_ctd_2']
      ls_sim_res = get_two_firm_similar_prices(df_price[indiv_id], df_price[comp_id])
      ls_sim_rows = list(ls_sim_res[:3]) + [len(ls_x) for ls_x in ls_sim_res[3:]]
      se_sim = pd.Series(ls_sim_rows, ls_sim_cols)
      ls_disp_cols = ['nb_days_spread', 'nb_days_same_price', 'nb_days_a_cheaper', 'nb_days_b_cheaper',
                      'nb_rr_conservative', 'percent_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr',
                      'avg_abs_spread', 'avg_spread', 'std_spread']
      ls_disp_res = get_pair_price_dispersion(df_price[indiv_id], df_price[comp_id])
      se_disp = pd.Series(ls_disp_res[0], ls_disp_cols)
     
      se_pair_su = pd.concat([se_rows, se_sim, se_disp])

      print '\n', indiv_id, comp_id
      print (df_price[indiv_id] - df_price[comp_id]).mean()
      print se_pair_su

      # Two subplots: followed price changes and matching of competitor's price
      fig = plt.figure()
      
      ax1 = fig.add_subplot(2,1,1)
      #df_price[[indiv_id, comp_id]]['2013-02':].plot(ax=ax1)
      df_price[[indiv_id, comp_id]].plot(ax=ax1)
      for day_ind in ls_two_res[-2]:
        line_0 = ax1.axvline(x=df_price.index[day_ind], lw=1, ls='--', c='b')
        line_0.set_dashes([10,2])
      for day_ind in ls_two_res[-1]:
        line_1 = ax1.axvline(x=df_price.index[day_ind], lw=1, ls='--', c='g')
        line_1.set_dashes([10,2])
      handles, labels = ax1.get_legend_handles_labels()
      ax1.legend(handles, labels, loc = 1)
      ax1.set_title("Followed price changes")
      
      ax2 = fig.add_subplot(2,1,2)
      #df_price[[indiv_id, comp_id]]['2013-02':].plot(ax=ax2)
      df_price[[indiv_id, comp_id]].plot(ax=ax2)
      for day_ind in ls_sim_res[3]:
        line_2 = ax2.axvline(x=df_price.index[day_ind], lw=1, ls='--', c='g')
        line_2.set_dashes([10,2])
      for day_ind in ls_sim_res[4]:
        line_3 = ax2.axvline(x=df_price.index[day_ind], lw=1, ls='--', c='b')
        line_3.set_dashes([10,2])
      
      handles, labels = ax2.get_legend_handles_labels()
      ax2.legend(handles, labels, loc = 1)
      ax2.set_title("Matching of competitor's price")
      
      plt.tight_layout()
      # plt.show()
      plt.savefig(os.path.join(path_temp, '%s-%s' %(indiv_id, comp_id)))
      plt.close()

# BACKUP

## leader, follower
#ax = df_price[[indiv_id, comp_id]][:'2012-06'].plot()
#for day_ind in ls_two_res[-2]:
#  line_0 = ax.axvline(x=df_price.index[day_ind], lw=1, ls='--', c='g')
#  line_0.set_dashes([10,2])
#for day_ind in ls_two_res[-1]:
#  line_1 = ax.axvline(x=df_price.index[day_ind], lw=1, ls='--', c='b')
#  line_1.set_dashes([10,2])
#plt.show()
#
## price matching
#ax = df_price[[indiv_id, comp_id]][:'2012-06'].plot()
#for day_ind in ls_sim_res[3]:
#  line_2 = ax.axvline(x=df_price.index[day_ind], lw=1, ls='--', c='g')
#  line_2.set_dashes([2,4])
#for day_ind in ls_sim_res[4]:
#  line_3 = ax.axvline(x=df_price.index[day_ind], lw=1, ls='--', c='b')
#  line_3.set_dashes([2,4])
#plt.show()
