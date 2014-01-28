import os, sys
import json
import itertools
import timeit
import copy
import math
import random
import numpy as np
import scipy
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import patsy
from generic_master_price import *

# DATA DISPLAY

def print_dict_stat_des(dict_stat_des):
  for key, content in dict_stat_des.iteritems():
    print key, len(content)

def get_plot_prices(list_of_ids, master_price, series, path_save=None):
  list_list_prices = []
  for some_id in list_of_ids:
    list_list_prices.append(master_price[series][master_price['ids'].index(some_id)])
  pd_df_temp = pd.DataFrame(zip(*list_list_prices), index=master_price['dates'], columns=list_of_ids, dtype=np.float32)
  plt.figure()
  pd_df_temp.plot()
  fig = plt.gcf()
  fig.set_size_inches(18.5,10.5)
  if path_save: 
    plt.savefig(path_save)
  else:
    plt.show()
  return

def get_plot_list_arrays(list_price_arrays, list_labels = None):
  plt.figure()
  for price_index, price_array in enumerate(list_price_arrays):
    axis = np.array([i for i in range(len(price_array))])
    if list_labels:
      plt.plot(axis, price_array, label=list_labels[price_index])
    else:
      plt.plot(axis, price_array, label='')
    plt.legend(loc = 4)
  plt.show()
  return 

# PAIR PRICE DISPERSION

def get_pair_price_dispersion(id_1, id_2, master_price, series):
  price_array_1 = np.array(master_price[series][master_price['ids'].index(id_1)], dtype = np.float32)
  price_array_2 = np.array(master_price[series][master_price['ids'].index(id_2)], dtype = np.float32)
  spread = price_array_1 - price_array_2
  duration = (~np.isnan(spread)).sum()
  avg_abs_spread = scipy.stats.nanmean(np.abs(spread))
  avg_spread = scipy.stats.nanmean(spread)
  std_spread = scipy.stats.nanstd(spread)
  b_cheaper = (spread < 0).sum()
  a_cheaper = (spread > 0).sum()
  rank_reversal = np.min([np.float32(b_cheaper)/duration, np.float32(a_cheaper)/duration])
  if b_cheaper > a_cheaper:
    ar_rank_reversal = np.where(spread <= 0, 0, spread)
  else:
    ar_rank_reversal = np.where(spread >= 0, 0, spread)
  list_tuples_rr = []
  for group in itertools.groupby(iter(range(len(ar_rank_reversal))),\
                                  lambda x: ar_rank_reversal[x] if ~np.isnan(ar_rank_reversal[x]) else None):
    list_tuples_rr.append((group[0], list(group[1])))
  list_rr_durations = [len(tuple_rr[1]) for tuple_rr in list_tuples_rr if tuple_rr[0] and tuple_rr[0] != 0]
  return (duration, avg_abs_spread, avg_spread, std_spread, rank_reversal, ar_rank_reversal, spread, list_rr_durations)

def get_station_price_dispersion(indiv_id, list_list_competitors, master_price, series, km_bound):
  """ for an id: price dispersion stats with each competitor within a given nb of km """
  dict_results = {}
  for (competitor_id, competitor_distance) in list_list_competitors[master_price['ids'].index(indiv_id)]:
    if competitor_distance < km_bound:
      pair_pd_stats = get_pair_price_dispersion(indiv_id, competitor_id, master_price, series)
      dict_results.setdefault('ids', []).append(competitor_id)
      dict_results.setdefault('duration', []).append(pair_pd_stats[0])
      dict_results.setdefault('avg_abs_spread', []).append(pair_pd_stats[1])
      dict_results.setdefault('avg_spread', []).append(pair_pd_stats[2])
      dict_results.setdefault('std_spread', []).append(pair_pd_stats[3])
      dict_results.setdefault('rank_reversal', []).append(pair_pd_stats[4])
      dict_results.setdefault('ar_rank_reversal', []).append(pair_pd_stats[5])
      dict_results.setdefault('spread', []).append(pair_pd_stats[6])
      dict_results.setdefault('list_rr_durations', []).append(pair_pd_stats[7])
  return dict_results

def get_list_pair_price_dispersion(list_tuple_competitors, master_price, series, km_bound):
  """ 
  Price dispersion stats for each pair with distance smaller than a given bound
  TODO: add the average spread conditional on rank being reversed
  """
  list_pair_price_dispersion = []
  list_pbms = []
  for ((id_1, id_2), distance) in list_tuple_competitors:
    if distance < km_bound:
      pair_pd_stats = get_pair_price_dispersion(id_1, id_2, master_price, series)
      pair_price_dispersion = ((id_1,id_2), # 0 id pair
                               distance, # 1 distance
                               pair_pd_stats[0], # 2 duration
                               pair_pd_stats[1], # 3 avg_abs_spread
                               pair_pd_stats[2], # 4 avg_spread
                               pair_pd_stats[3], # 5 std_spread
                               pair_pd_stats[4], # 6 rank_reversal
                               pair_pd_stats[5], # 7 ar_rank_reversal
                               pair_pd_stats[6], # 8 spread
                               pair_pd_stats[7]) # 9 rr_durations
      list_pair_price_dispersion.append(pair_price_dispersion)
  return list_pair_price_dispersion

# MARKET PRICE DISPERSION

def get_list_list_distance_market_ids(master_price, list_list_competitors, km_bound):
  """
  Distance used to define markets
  list_list_competitors has same order as master price (necessary condition)
  list_list_competitors: list of (id, distance) for each competitor (within 10km)
  """
  list_list_distance_market_ids = []
  for ind_individual, list_competitors in enumerate(list_list_competitors):
    id_individual = master_price['ids'][ind_individual]
    if list_competitors: # and id_individual not in list_rejected_ids:
      list_distance_market_ids = [id_individual]
      for id_competitor, distance_competitor in list_competitors:
        if id_competitor in master_price['ids']: # and id_competitor not in list_rejected_ids:
          if distance_competitor < km_bound:
            list_distance_market_ids.append(id_competitor)
        else:
          print id_competitor, 'not in master_price => check'
      if len(list_distance_market_ids) > 1:
        list_list_distance_market_ids.append(list_distance_market_ids)
  return list_list_distance_market_ids

def get_list_list_distance_market_ids_restricted(master_price, list_list_competitors, km_bound):
  """
  Distance used to define markets
  list_list_competitors: list of (id, distance) for each competitor (within 10km)
  list_list_competitors has same order as master price
  If id in previous market: drop market 
  TODO: design better algorithm (max nb of stations such that keep) OR:
  TODO: add possibility to randomize (beware: list_list_competitors' order matters)
  list_id_and_list_competitors_random = copy.deepcopy()
  random.shuffle(list_id_and_list_competitors_random)
  """
  list_list_distance_market_ids = []
  list_ids_covered = []
  for ind_individual, list_competitors in enumerate(list_list_competitors):
    id_individual = master_price['ids'][ind_individual]
    if list_competitors:
      list_distance_market_ids = [id_individual]
      for id_competitor, distance_competitor in list_competitors:
        if id_competitor in master_price['ids']:
          if distance_competitor < km_bound:
            list_distance_market_ids.append(id_competitor)
        else:
          print id_competitor, 'not in master_price => check'
      if len(list_distance_market_ids) > 1 and all(id not in list_ids_covered for id in list_distance_market_ids):
        list_list_distance_market_ids.append(list_distance_market_ids)
        list_ids_covered += list_distance_market_ids
  return list_list_distance_market_ids

def get_fe_predicted_prices(list_ids, series):
  dict_panel_data_master_temp = {}
  for id in list_ids:
    ind = master_price['ids'].index(id)
    list_station_prices = master_price[series][ind]
    list_station_brands = [dict_brands[get_str_no_accent_up(brand)][1] if brand else brand\
                            for brand in get_field_as_list(id, 'brand', master_price)]
    dict_station = {'price' : np.array(list_station_prices, dtype = np.float32),
                    'brand' : np.array(list_station_brands),
                    'id' : id}
    dict_panel_data_master_temp[id] = pd.DataFrame(dict_station, index = master_price['dates'])
  pd_pd_master_temp = pd.Panel(dict_panel_data_master_temp)
  pd_pd_master_temp = pd_pd_master_temp.transpose('minor', 'items', 'major')
  pd_mi_master_temp = pd_pd_master_temp.to_frame(filter_observations=False)
  pd_mi_master_temp['price'] = pd_mi_master_temp['price'].astype(np.float32)
  pd_mi_master_temp['date'] = pd_mi_master_temp.index.get_level_values(1)
  res = smf.ols(formula = 'price ~ C(id) + C(date)', data = pd_mi_master_temp).fit()
  #pd_df_X = pd.DataFrame(pd_mi_master_temp[['id', 'date']], columns=["id", "date"])
  pd_df_X = pd_mi_master_temp[['id']]
  pd_df_X['dates'] = 0
  ar_y_prediction = res.predict(pd_df_X)
  # Need to cut ar_y_prediction in price arrays
  # Here: Assumes all have same lengths
  return np.reshape(ar_y_prediction, (len(list_ids), -1))
  
def get_list_list_market_price_dispersion(list_list_market_ids, master_price, series, clean=False):
  # if numpy.version.version = '1.8' or above => switch from scipy to numpy
  # checks nb of prices (non nan) per period (must be 2 prices at least)
  list_list_market_price_dispersion = []
  for list_market_ids in list_list_market_ids:
    list_market_prices = [master_price[series][master_price['ids'].index(id)] for id in list_market_ids]
    arr_market_prices = np.array(list_market_prices, dtype = np.float32)
    if clean is True:
      ar_predicted_market_prices = get_fe_predicted_prices(list_market_ids, series)
      arr_market_prices = arr_market_prices - ar_predicted_market_prices
    arr_nb_market_prices = (~np.isnan(arr_market_prices)).sum(0)
    arr_bool_enough_market_prices = np.where(arr_nb_market_prices > 1, 1, np.nan)
    arr_market_prices = arr_bool_enough_market_prices * arr_market_prices
    range_price_array = scipy.nanmax(arr_market_prices, 0) - scipy.nanmin(arr_market_prices, axis = 0)
    std_price_array = scipy.stats.nanstd(arr_market_prices, 0)
    coeff_var_price_array = scipy.stats.nanstd(arr_market_prices, 0) / scipy.stats.nanmean(arr_market_prices, 0)
    gain_from_search_array = scipy.stats.nanmean(arr_market_prices, 0) - scipy.nanmin(arr_market_prices, axis = 0)
    list_list_market_price_dispersion.append(( list_market_ids,
                                               len(list_market_ids),
                                               range_price_array,
                                               std_price_array,
                                               coeff_var_price_array,
                                               gain_from_search_array ))
  return list_list_market_price_dispersion




if __name__=="__main__":
  if os.path.exists(r'W:\Bureau\Etienne_work\Data'):
    path_data = r'W:\Bureau\Etienne_work\Data'
  else:
    path_data = r'C:\Users\etna\Desktop\Etienne_work\Data'
  folder_built_master_json = r'\data_gasoline\data_built\data_json_gasoline'
  folder_source_brand = r'\data_gasoline\data_source\data_stations\data_brands'
  folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'
  
  master_price = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_price_diesel')
  master_info = dec_json(path_data + folder_built_master_json + r'\master_diesel\master_info_diesel')
  
  dict_brands = dec_json(path_data + folder_source_brand + r'\dict_brands')
  
  # cross_distances_dict = dec_json(path_data + folder_built_master_json + r'\dict_ids_gps_cross_distances')
  list_list_competitors = dec_json(path_data + folder_built_master_json + r'\master_diesel\list_list_competitors')
  list_tuple_competitors = dec_json(path_data + folder_built_master_json + r'\master_diesel\list_tuple_competitors')
  
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
                                                          list_list_competitors, 
                                                          master_price, 
                                                          series,
                                                          km_bound)
  
  list_pair_price_dispersion = get_list_pair_price_dispersion(list_tuple_competitors,
                                                              master_price,
                                                              series,
                                                              km_bound)
  
  list_list_market_ids = get_list_list_distance_market_ids(master_price, list_list_competitors, km_bound)
  list_list_market_price_dispersion = get_list_list_market_price_dispersion(list_list_market_ids, master_price, series)
  
  list_list_m_ids_res = get_list_list_distance_market_ids_restricted(master_price, list_list_competitors, km_bound)
  list_list_mpd_res = get_list_list_market_price_dispersion(list_list_m_ids_res, master_price, series)
    
  # print 'Starting sample market price dispersion with cleaned prices'
  # list_list_mpd_res_clean = get_list_list_market_price_dispersion(list_list_m_ids_res[0:10],
                                                                  # master_price,
                                                                  # series,
                                                                  # clean = True)
  
  # TODO: other definitions of market based on insee criteria
  # TODO: robustess to price corrections
  
  
  # REGRESSIONS WITH PANDAS / SM FORMULAS
  
  # REGRESSION OF PAIR PRICE DISPERSION ON DISTANCE
  
  matrix_pair_pd = np.array([pd_tuple for pd_tuple in list_pair_price_dispersion if pd_tuple[1] < km_bound])
  # col 1: distance, (col 2: duration, col 4: avg_spread), col 5: std_spread, col 6: rank reversals
  matrix_pair_pd = np.array(np.vstack([matrix_pair_pd[:,1],
                                       matrix_pair_pd[:,5], 
                                       matrix_pair_pd[:,6]]), dtype = np.float32).T
  pd_pair_pd = pd.DataFrame(matrix_pair_pd, columns = ['distance','rank_reversals','spread_std'])
  pd_pair_pd = pd_pair_pd.dropna()
  print smf.ols(formula = 'rank_reversals ~ distance', data = pd_pair_pd).fit().summary()
  print smf.ols(formula = 'spread_std ~ distance', data = pd_pair_pd).fit().summary()
  
  # REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE
  
  matrix_master_pd = []
  for market in list_list_market_price_dispersion:
    # create variable containing number of competitors for each period
    array_nb_competitors = np.ones(len(market[2])) * market[1]
    # TODO: reminder on columns
    matrix_master_pd.append(np.vstack([array_nb_competitors, period_mean_prices, market[2:]]).T)
  matrix_master_pd = np.vstack(matrix_master_pd)
  # matrix_master_pd = np.array(matrix_master_pd, dtype = np.float64)
  
  list_column_labels = ['nb_competitors', 'price', 'std_prices', 'coeff_var_prices', 'range_prices', 'gain_search']
  pd_master_pd = pd.DataFrame(matrix_master_pd, columns = list_column_labels)
  pd_master_pd = pd_master_pd.dropna()
  print smf.ols(formula = 'std_prices ~  nb_competitors', data = pd_master_pd).fit().summary()
  print smf.ols(formula = 'std_prices ~ nb_competitors + price', data = pd_master_pd).fit().summary()
  print smf.ols(formula = 'coeff_var_prices ~  nb_competitors', data = pd_master_pd).fit().summary()
  print smf.ols(formula = 'coeff_var_prices ~ nb_competitors + price', data = pd_master_pd).fit().summary()
  print smf.ols(formula = 'range_prices ~  nb_competitors', data = pd_master_pd).fit().summary()
  print smf.ols(formula = 'range_prices ~ nb_competitors + price', data = pd_master_pd).fit().summary()
  print smf.ols(formula = 'gain_search ~  nb_competitors', data = pd_master_pd).fit().summary()
  print smf.ols(formula = 'gain_search ~ nb_competitors + price', data = pd_master_pd).fit().summary()
  
  
  # # REGRESSIONS W/O PANDAS / SM FORMULAS
  
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
  
  
  # # PRICE CLEANING...VERY PRELIMINARY AND TEMPORARY
  
  # price_effect = {'AGIP' : 0,
                  # 'AUCHAN': -.0639177,
                  # 'AUTRE_DIS': .0543546,
                  # 'AUTRE_GMS': -.0557188,
                  # 'AUTRE_IND': -.0051177,
                  # 'AVIA': .003345,
                  # 'BP': .0056645,
                  # 'BRETECHE': -.0031029,
                  # 'CARREFOUR': -.0677206,
                  # 'CASINO': -.0699135,
                  # 'COLRUYT': -.0640661,
                  # 'CORA': -.0621978,
                  # 'DYNEFF': .0013379,
                  # 'ELAN': .0492857,
                  # 'ELF': -.0797696,
                  # 'ESSO': -.0340026,
                  # 'INDEPENDANT':  -.0163602,
                  # 'LECLERC': -.0801179,
                  # 'MOUSQUETAIRES':  -.0711393,
                  # 'SHELL': .0346202,
                  # 'SYSTEMEU': -.0763088,
                  # 'TOTAL': .0208815,
                  # 'TOTAL_ACCESS': -.0556952}
  
  # list_brands = []
  # list_coeffs = []
  # master_coeffs = []
  # for id in master_price['ids']:
    # list_brands.append(dict_brands[get_str_no_accent_up(master_price['dict_info'][id]['brand'][0][0])][1])
  # for brand in list_brands:
    # list_coeffs.append(price_effect[brand])
  # for coeff in list_coeffs:
    # master_coeffs.append([coeff for i in range(len(master_price['diesel_price'][0]))])
  # matrix_coeffs = np.array(master_coeffs, dtype = np.float64)
  # matrix_price_cont = master_np_prices - matrix_coeffs
  # master_price['diesel_price_corrected'] = matrix_price_cont.tolist()
  
  
  
  
  # # REGRESSION OF PAIR PRICE DISPERSION ON DISTANCE WITH CLEANED PRICES
  
  # series = 'diesel_price_corrected'
  
  # list_pair_price_dispersion_cont = get_list_pair_price_dispersion(list_tuple_competitors,
                                                              # master_price,
                                                              # series,
                                                              # km_bound)
  
  # list_pair_pd_print = np.array([elt[1:7] for elt in list_pair_price_dispersion_cont])
  
  # # head_list_pair_pd_cont = 'distance, duration, avg_abs_spread ,avg_spread, std_spread, rank_reversal'
  # # path_ppd = path_data + folder_built_csv + r'\list_pair_pd_cont.txt'
  # # np.savetxt(path_ppd, list_pair_pd_print, fmt = '%.5f', delimiter = ',', header = head_list_pair_pd_cont)
  
  
  
  
  # # REGRESSION OF MARKET PRICE DISPERSION ON NB COMPETITORS AND PRICE WITH CLEANED PRICES
  
  # list_list_market_price_dispersion_cont = get_list_list_market_price_dispersion(list_list_market_ids,
                                                                                 # master_price, 
                                                                                 # series)
  
  # matrix_master_pd_cont = []
  # for market in list_list_market_price_dispersion_cont:
    # array_nb_competitors = np.ones(len(market[2])) * market[1]
    # matrix_master_pd_cont.append(np.vstack([array_nb_competitors, period_mean_prices, market[2:]]).T)
  # matrix_master_pd_cont = np.vstack(matrix_master_pd_cont)
  
  # # head_list_market_pd = 'nb_competitors, mean_period_price, std_price, coeff_var_price, range_price, gain_from_search'
  # # path_mpd = path_data + folder_built_csv + r'\list_market_pd_cont_5.txt'
  # # np.savetxt(path_mpd,  matrix_master_pd_cont, fmt = '%.5f', delimiter = ',', header = head_list_market_pd)
  
  # nb_competitors = np.vstack([matrix_master_pd_cont[:,0]]).T
  # nb_competitors_and_price = np.vstack([matrix_master_pd_cont[:,0], matrix_master_pd_cont[:,1]]).T
  # range_prices = matrix_master_pd_cont[:,2]
  # std_prices = matrix_master_pd_cont[:,3]
  # coeff_var_prices = matrix_master_pd_cont[:,4]
  # gain_search = matrix_master_pd_cont[:,5]
  # print '\n REGRESSIONS OF PAIR PRICE DISPERSION ON DISTANCE (CLEANED PRICES) \n'
  # print sm.OLS(std_prices, sm.add_constant(nb_competitors), missing = "drop").fit()\
                # .summary(yname='std_prices', xname = ['constant', 'nb_competitors'])
  # print sm.OLS(std_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()\
                # .summary(yname='std_prices', xname = ['constant', 'nb_competitors', 'price'])
  # print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors), missing = "drop").fit()\
                # .summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors'])
  # print sm.OLS(coeff_var_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()\
                # .summary(yname='coeff_var_prices', xname = ['constant', 'nb_competitors', 'price'])
  # print sm.OLS(range_prices, sm.add_constant(nb_competitors), missing = "drop").fit()\
                # .summary(yname='range_prices', xname = ['constant', 'nb_competitors'])
  # print sm.OLS(range_prices, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()\
                # .summary(yname='range_prices', xname = ['constant', 'nb_competitors', 'price'])
  # print sm.OLS(gain_search, sm.add_constant(nb_competitors), missing = "drop").fit()\
                # .summary(yname='gain_search', xname = ['constant', 'nb_competitors'])
  # print sm.OLS(gain_search, sm.add_constant(nb_competitors_and_price), missing = "drop").fit()\
                # .summary(yname='gain_search', xname = ['constant', 'nb_competitors', 'price'])
  
  # # head_master_long = 'id, period, price, brand'
  # # path_ml = path_data + folder_built_csv +r'\master_long.txt'
  # # np.savetxt(path_ml, master_long, fmt = '%s', delimiter = ',', header = head_master_long)