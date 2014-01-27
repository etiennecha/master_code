#!/usr/bin/python
# -*- coding: utf-8 -*-

import scipy
from generic_master_price import *

# Temp functions (to drop)

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
  ls_tuple_competitors = dec_json(path_data + folder_built_master_json + r'\master_diesel\list_tuple_competitors')
  
  folder_dpts_regions = r'\data_insee\Regions_departements'
  dict_dpts_regions = dec_json(path_data + folder_dpts_regions + r'\dict_dpts_regions')

  folder_built_csv = r'\data_gasoline\data_built\data_csv_gasoline'
  
  # #####################
  # IMPORT INSEE DATA
  # #####################
  
  pd_df_insee = pd.read_csv(path_data + folder_built_csv + r'/master_insee_output.csv',\
                              encoding = 'utf-8', dtype= str)
  ls_no_match = []
  pd_df_insee[u'Département - Commune CODGEO'] = pd_df_insee[u'Département - Commune CODGEO'].astype(str)
  ls_insee_data_codes_geo = list(pd_df_insee[u'Département - Commune CODGEO'])
  for station_id, station_info in master_price['dict_info'].iteritems():
    if 'code_geo' in station_info.keys():
      if (station_info['code_geo'] not in ls_insee_data_codes_geo) and\
         (station_info['code_geo_ardts'] not in ls_insee_data_codes_geo):
			  ls_no_match.append((station_id, station_info['code_geo']))
  # exclude dom tom
  pd_df_insee = pd_df_insee[~pd_df_insee[u'Département - Commune CODGEO'].str.contains('^97')]
  pd_df_insee['Population municipale 2007 POP_MUN_2007'] =\
    pd_df_insee['Population municipale 2007 POP_MUN_2007'].astype(float)
  
  # #####################
  # MARKET DEFINITIONS
  # #####################
  
  pd_df_insee['id_code_geo'] = pd_df_insee[u'Département - Commune CODGEO']
  pd_df_insee = pd_df_insee.set_index('id_code_geo')
  dict_markets_insee = {}
  dict_markets_au = {}
  dict_markets_uu = {}
  # some stations don't have code_geo (short spells which are not in master_info)
  for id_station, info_station in master_price['dict_info'].iteritems():
    if 'code_geo' in info_station:
      dict_markets_insee.setdefault(info_station['code_geo'], []).append(id_station)
      station_uu = pd_df_insee.ix[info_station['code_geo']][u"Code géographique de l'unité urbaine UU2010"]
      dict_markets_uu.setdefault(station_uu, []).append(station_id)
      station_au = pd_df_insee.ix[info_station['code_geo']][u'Code AU2010']
      dict_markets_au.setdefault(station_au, []).append(station_id)
  
  # CASE OF ARGENTEUIL:
  # TODO: see if switch to code insee or keep both code insee and list of code postal... (e.g. Limoges..)
  # for id_sta, address in dict_zip_master['95100']:
	  # ind = master_price['ids'].index(id_sta)
	  # print id_sta, ind, list_start_end[ind], master_addresses_final[id_sta]
	  # print master_price['dict_info'][id_sta]
  
  # ##############
  # PRICE ANALYSIS
  # ##############
  
  # Price corrections already done at this stage (normally)
  # TODO list:
  # Aggregate... mean, variance etc. (pandas dataframe)
  # Bad reporting... closed / newly opened gas stations (or newly reported...)
  # Price values: 3 digits or not, how many used (to be done in pandas?)
  # Variations: size of variations, grid of variations used (to be done in pandas?)
  # Promotions (successive inverse moves)
  # Brand changes and impact (pandas)
  # Price graphs (pandas)
  
  ls_ls_price_durations = get_price_durations_nan(master_price['diesel_price'])
  ls_ls_price_variations = get_price_variations_nan(ls_ls_price_durations)
  ls_start_end, ls_none, ls_ls_dilettante =  get_overview_reporting_nan(master_price['diesel_price'],                                                                      
                                                                        ls_ls_price_durations,
                                                                        master_price['dates'],
                                                                        master_price['missing_dates'])
  
  # BAD REPORTING (COULD DO IT BEFORE CENSORSHIP TO COMPARE...)
  
  c_start, c_end = 0, len(master_price['dates'])-1
  ls_late_start = [indiv_ind for indiv_ind, (start, end) in enumerate(ls_start_end) if start != c_start]
  ls_early_end = [indiv_ind for indiv_ind, (start, end) in enumerate(ls_start_end) if end != c_end]
  ls_short_spell = [indiv_ind for indiv_ind, (start, end) in enumerate(ls_start_end)\
                      if start!= c_start and end !=c_end]
  ls_long_early_end = [indiv_ind for indiv_ind, (start, end) in enumerate(ls_start_end)\
                        if start == c_start and end != c_end]
  ls_ctd_late_start = [indiv_ind for indiv_ind, (start, end) in enumerate(ls_start_end)\
                        if start != c_start and end == c_end]
  
  dict_bad_reporting = {}
  for indiv_ind, ls_day_ind in enumerate(ls_ls_dilettante):
	  for day_ind in ls_day_ind:
		  dict_bad_reporting.setdefault(day_ind, []).append(indiv_ind)
  # Missing period => nobody reported dilettante (though it could if short given corrections)
  
  ls_period_bad_reporting = [None for i in master_price['dates']]
  for day_ind, ls_period_indiv_ind in dict_bad_reporting.iteritems():
    ls_period_bad_reporting[day_ind] = len(ls_period_indiv_ind)
  # pd_df_temp = pd.DataFrame(zip(*[master_price['diesel_price'][51], master_price['diesel_date'][51]]),\
                              # index=master_price['dates'])
  # print pd_df_temp.to_string()
  # TODO: see why it crashes
  # pd_df_temp = pd.DataFrame(zip(*[list_period_bad_reporting, list_period_old_and_bad_reporting]),\
                              # index=master_price['dates'], dtype = np.int)
  # pd_df_temp.plot()
  # plt.show()
  # TODO: Explore list of poorly reporting stations + late start / early end => some cheating/agreeing not to report?
  # TODO: Exploit proximity + same date (e.g. Argenteuil => what's happening there!? + Corsica?)
  # TODO: Generically get notion of relations between stations within a list (geographic, brand etc.)
  
  # PRICE VARIATION VALUES
  dict_price_variations = Counter()
  for ls_price_variations in ls_ls_price_variations:
    if ls_price_variations:
      for variation in [variation for (variation, ls_day_ind) in ls_price_variations if not np.isnan(variation)]:
        dict_price_variations[variation] += 1 
  
  # ANALYSIS OF PRICES AT GLOBAL LEVEL: TODO
  
  # TODO: analysis by region/dpt, brand etc.
  
  master_np_prices = np.array(master_price['diesel_price'], dtype = np.float32)
  master_np_prices_chges = master_np_prices[:,:-1] - master_np_prices[:,1:]
  
  # beware when comparing with 0
  ar_non_nan = np.sum((~np.isnan(master_np_prices_chges)), axis = 0)
  ar_nb_chges = np.sum((~np.isnan(master_np_prices_chges)) & (master_np_prices_chges!=0), axis = 0)
  ar_nb_pos_chges = np.sum((master_np_prices_chges > 0), axis = 0)
  ar_nb_neg_chges = np.sum((master_np_prices_chges < 0), axis = 0)
  
  ar_master_np_pos_prices_chges = np.ma.masked_less_equal(master_np_prices_chges, 0).filled(np.nan)
  ar_avg_pos_chge = scipy.stats.nanmean(pos_master_np_prices_chges, axis = 0)
  
  ar_master_np_neg_prices_chges = np.ma.masked_greater_equal(master_np_prices_chges, 0).filled(np.nan)
  ar_avg_neg_chge = scipy.stats.nanmean(ar_master_np_neg_prices_chges, axis = 0)
  
  ar_master_np_nonzero_prices_chges = np.ma.masked_equal(master_np_prices_chges, 0).filled(np.nan)
  ar_avg_nonzero_chge = scipy.stats.nanmean(ar_master_np_nonzero_prices_chges, axis = 0)
  
  ar_normal_chges = master_np_prices_chges[(np.abs(master_np_prices_chges) <= 0.1) & (master_np_prices_chges != 0)]
  ar_extreme_chges = master_np_prices_chges[(np.abs(master_np_prices_chges) > 0.1)]
  print 'Percentage of abnormal changes', float(len(ar_extreme_chges))/(len(ar_normal_chges) + len(ar_extreme_chges))
  
  # # TOO BIG => RESTRICT
  # n, bins, patches = plt.hist(ar_normal_chges[0:100000], 50, normed=1, facecolor='g')
  # plt.show()
  
  # n, bins, patches = plt.hist(ar_extreme_chges, 50, normed=1, facecolor='g')
  # plt.show()
  # CAUTION: still 324 changes among which some very high (-0.6) to be eliminated (except if...)
  
  # plt.step([i for i in range(300)], ar_avg_nonzero_chge[:300])
  # plt.show()
  
  # ANALYSIS OF PRICES AT STATION LEVEL: TODO (frequency etc)
  
  # ##########################
  # BRAND CHANGES: TODO HERE?
  # ##########################
  
  # #####################
  # CLOSED GAS STATIONS
  # #####################
  
  # Candidates for closed stations... 
  # Look around if openings? => Check if late_start in vincinity of those
  # TODO: also check on ID (ZIP...)
  # TODO: check by hand (?) with zagaz or other websites (extend dataset length?)
  ls_confirmed_candidates = []
  ls_doubtful_candidates = []
  for indiv_ind in ls_long_early_end:
    if ls_ls_competitors[indiv_ind]:
      ls_competitor_ind = [master_price['ids'].index(c_ind) for c_ind, c_dist in ls_ls_competitors[indiv_ind]]
      ls_suspects = []
      for competitor_ind in ls_competitor_ind:
        if ls_start_end[competitor_ind][0]!= 0:
          ls_suspects.append((competitor_ind, ls_start_end[competitor_ind][0]))
      if ls_suspects:
        ls_doubtful_candidates.append([(indiv_ind, ls_start_end[indiv_ind][1])] + ls_suspects)
      else:
        ls_confirmed_candidates.append(indiv_ind)
  # Can check brand, location, last prices (?)
  for indiv_ind in ls_confirmed_candidates:
    if ls_start_end[indiv_ind][1] < 630:
      indiv_id = master_price['ids'][indiv_ind]
      print ls_start_end[indiv_ind][1], indiv_ind, indiv_id,\
            master_price['dict_info'][indiv_id]['name'],\
            master_price['dict_info'][indiv_id]['brand'],\
            get_latest_info(indiv_id, 'address', master_info)
  
  # #####################
  # OPENED GAS STATIONS
  # #####################
  
  # TODO
  
  # ##############
  # PRICE GRAPHS
  # ##############
  
  # dict_panel_data_master = {}
  # ls_formatted_dates = ['%s/%s/%s' %(elt[:4], elt[4:6], elt[6:]) for elt in master_price['dates']]
  # index_formatted_dates = pd.to_datetime(ls_formatted_dates)
  # for i, id in enumerate(master_price['ids']):
    # if 'code_geo' in master_price['dict_info'][id]: # temp: TODO: complete master_info
      # ls_station_prices = master_price['diesel_price'][i]
      # ls_station_brands = [dict_brands[get_str_no_accent_up(brand)][1] if brand else brand\
                              # for brand in get_field_as_list(id, 'brand', master_price)]
      # zip_code = '%05d' %int(id[:-3])
      # dict_station = {'price' : np.array(ls_station_prices, dtype = np.float32),
                      # 'brand' : np.array(ls_station_brands),
                      # 'zip_code' : zip_code,
                      # 'department' : zip_code[:2],
                      # 'region' : dict_dpts_regions[zip_code[:2]],
                      # 'insee_code' : master_price['dict_info'][id]['code_geo']}
      # # TODO: declare type when moving to pd, add highway id, and geo data!
      # dict_panel_data_master[id] = pd.DataFrame(dict_station, index = index_formatted_dates)
  # pd_pd_master = pd.Panel(dict_panel_data_master)
  
  
  # pd_df_price = pd_pd_master.minor_xs('price')
  # pd_df_price_total = pd_pd_master.minor_xs('price')[pd_pd_master.minor_xs('brand') == 'TOTAL']
  # pd_df_mean_comp = pd.concat([pd_df_price.mean(1),pd_df_price_total.mean(1)], keys = ['All', 'Total'] , axis = 1)
  # pd_df_mean_comp_2 = pd_df_price_total.mean(1) - pd_df_price.mean(1)
  
  # # PRICE TOTAL
  
  # # Brand Total: missing periods should be set to NAN: strong bias
  # # Stations Total in missing periods are those with low prices (visible from margin)
  # plt.plot(pd_df_price_total.count(1)/float(max(pd_df_price_total.count(1))))
  # plt.plot(pd_df_mean_comp_2)
  # # pd_df_mean_comp_2[pdf_df_mean_comp_2<0.04] Total premium is esp. low on 2012-08-30, due to Total strong decrease !
  # # pd_df_temp = pd.DataFrame(pd_df_price_total.ix['2012-08-30'], dtype = np.float32)
  # # pd_df_temp.sort('2012-08-30').head()
  # # print pdf_df_mean_comp.to_string()

  # # # GET COUNT STATS DES ON CATEGORICAL VARIABLE
  
  # # Categorical variable stat des (static)
  # pd_pd_master.minor_xs('region').ix['2013-06-04'].value_counts()
  # # Categorical variable stat des not taking NAN into account (otherwise same in any period)
  # pd_df_temp = pd_pd_master.major_xs('2011-09-04').T
  # pd_df_temp = pd_df_temp.dropna(how = 'any')
  # pd_df_temp['region'].value_counts()
  
  # # # GET STATS DES ON CONTINUOUS VARIABLE
  
  # # # Can get a dataframe by selecting column
  # # pd_df_temp = pd_pd_master.minor_xs('brand')[pd_pd_master.minor_xs('department') == '34']
  # # pd_df_temp.ix['2013-06-04'].describe()
  # # pd_df_temp.ix['2013-06-04'].dropna().value_counts()
  # # pd_df_temp.ix['2013-06-04'].describe()
  # # pd_df_temp.ix['2013-06-04'].value_counts()
  # # pd_df_temp = pd_pd_master.minor_xs('price')[pd_pd_master.minor_xs('department') == '34']
  
  # # # Harder to keep a panel data object
  # # # list_ids_to_keep = ['10000001']
  
  # # TOTAL - TOTAL ACCESS : Seems to be real change in prices (COMPARE ELF => TOTAL ACCESS ?)
  # list_ids_total_total_access = dict_stats_brand_changes['TOTAL - TOTAL ACCESS']
  # pd_pd_total_access = pd_pd_master.filter(list_ids_total_total_access)
  # pd_df_mean_comp_total_access = pd.concat([pd_pd_master.minor_xs('price').mean(1),\
                                            # pd_pd_total_access.minor_xs('price').mean(1)],\
                                            # keys = ['All', 'Total Access'] , axis = 1)
  # # pd_df_mean_comp_total_access.plot()
    
  # # CARREFOUR MARKET - COOP - SYSTEME U
  # list_ids_interest = dict_stats_brand_changes['CARREFOUR MARKET - COOP - SYSTEME U']
  # pd_pd_interest = pd_pd_master.filter(list_ids_interest)
  # # pd_pd_interest.minor_xs('price').astype('float').plot()
  # pd_df_mean_comp_interest = pd.concat([pd_pd_master.minor_xs('price').mean(1),\
                                        # pd_pd_interest.minor_xs('price').mean(1)],\
                                        # keys = ['All', 'Carrefour - Systeme U'] , axis = 1)
  # pd_series_comp = pd_pd_master.minor_xs('price').mean(1) - pd_pd_interest.minor_xs('price').mean(1)
  # pd_series_comp_2 = pd_pd_master.minor_xs('price')[pd_pd_master.minor_xs('brand') == 'CARREFOUR'].mean(1) - \
                      # pd_pd_interest.minor_xs('price').mean(1)
  # # Decreasing trend in diff (price increase) + sales in October ?
  # # Quite a few appear to be in Dpt 17 => Leave Carrefour at same time: shock on competition?
  
  # # TODO: CHECK SHELL => AVIA & AVIA => SHELL ? SAME LOCATION ?
  # # TODO: CHECK TOTAL => ESSO & TOTAL => ELAN
  # # TODO: CHECK SHELL => ESSO & ESSO => AVIA
    
  
  # ###########
  # DEPRECATED
  # ###########
  
  # # REMINDER: USE OF PANEL DATA
  
  # pd_panel_data_master['10000001'] # select station 10000001 (df object)
  # pd_panel_data_master.major_xs(pd_panel_data_master.major_axis[0]) # select all station at 1st period (df object)
  # pd_df_first_period = pd_panel_data_master.major_xs(pd_panel_data_master.major_axis[0]).T 
  # #tranpose (items: brand, price)
  # pd_df_first_period[pd_df_first_period['brand']=='TOTAL']['price'] # selects all TOTAL prices in 1st period
  # np.mean(pd_df_first_period[pd_df_first_period['brand']=='TOTAL']['price']) # average TOTAL price in 1st period
  # # average price in 1st period at TOTAL stations in Paris
  # np.mean(pd_df_first_period[(pd_df_first_period['brand']=='TOTAL') & \
                             # (pd_df_first_period['zip_code'].str.startswith('75')) & \
                             # (pd_df_first_period['zip_code'].str.len()==5)]['price'])
  # # display prices of TOTAL stations in Paris for periods 1 to 10 ?