#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *

path_dir_built_json = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_json_gasoline')
path_diesel_price = os.path.join(path_dir_built_json, 'master_diesel', 'master_price_diesel')
path_info = os.path.join(path_dir_built_json, 'master_diesel', 'master_info_diesel')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'master_diesel', 'list_list_competitors')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'master_diesel', 'list_tuple_competitors')

path_dir_source_stations = os.path.join(path_data, 'data_gasoline', 'data_source', 'data_stations')
path_dict_brands = os.path.join(path_dir_source_stations, 'data_brands', 'dict_brands')

path_dict_dpts_regions = os.path.join(path_data, 'data_insee', 'Regions_departements', 'dict_dpts_regions')

path_dir_built_csv = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_csv_gasoline')
path_csv_insee_data = os.path.join(path_dir_built_csv, 'master_insee_output.csv') 

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

# #####################
# IMPORT INSEE DATA
# #####################

pd_df_insee = pd.read_csv(path_csv_insee_data, encoding = 'utf-8', dtype= str)
# excludes dom tom
pd_df_insee = pd_df_insee[~pd_df_insee[u'Département - Commune CODGEO'].str.contains('^97')]
pd_df_insee['Population municipale 2007 POP_MUN_2007'] = \
  pd_df_insee['Population municipale 2007 POP_MUN_2007'].apply(lambda x: float(x))

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
    dict_markets_uu.setdefault(station_uu, []).append(id_station)
    station_au = pd_df_insee.ix[info_station['code_geo']][u'Code AU2010']
    dict_markets_au.setdefault(station_au, []).append(id_station)

# CASE OF ARGENTEUIL:
# TODO: see if switch to code insee or keep both code insee and list of code postal... (e.g. Limoges..)
# for id_sta, address in dict_zip_master['95100']:
  # ind = master_price['ids'].index(id_sta)
  # print id_sta, ind, list_start_end[ind], master_addresses_final[id_sta]
  # print master_price['dict_info'][id_sta]

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

# # #################
# # PRICE OVERVIEW
# # #################

# # TODO: 3 digits or not, how many used (to be done in pandas?)
# # Variations: size of variations, grid of variations used (to be done in pandas?)
# # Promotions (successive inverse moves)
# # Brand changes and impact (pandas)
# # Price graphs (pandas)


# ls_ls_price_durations = get_price_durations_nan(master_price['diesel_price'])
# ls_ls_price_variations = get_price_variations_nan(ls_ls_price_durations)
# ls_start_end, ls_none, ls_ls_dilettante =  get_overview_reporting_nan(master_price['diesel_price'],                                                                      
                                                                      # ls_ls_price_durations,
                                                                      # master_price['dates'],
                                                                      # master_price['missing_dates'])

# # PRICE VARIATION VALUES
# dict_price_variations = Counter()
# for ls_price_variations in ls_ls_price_variations:
  # if ls_price_variations:
    # for variation in [variation for (variation, ls_day_ind) in ls_price_variations if not np.isnan(variation)]:
      # dict_price_variations[variation] += 1 

# # ANALYSIS OF PRICES AT GLOBAL LEVEL: TODO

# # TODO: analysis by region/dpt, brand etc.

# master_np_prices = np.array(master_price['diesel_price'], dtype = np.float32)
# master_np_prices_chges = master_np_prices[:,:-1] - master_np_prices[:,1:]

# # beware when comparing with 0
# ar_non_nan = np.sum((~np.isnan(master_np_prices_chges)), axis = 0)
# ar_nb_chges = np.sum((~np.isnan(master_np_prices_chges)) & (master_np_prices_chges!=0), axis = 0)
# ar_nb_pos_chges = np.sum((master_np_prices_chges > 0), axis = 0)
# ar_nb_neg_chges = np.sum((master_np_prices_chges < 0), axis = 0)

# ar_master_np_pos_prices_chges = np.ma.masked_less_equal(master_np_prices_chges, 0).filled(np.nan)
# ar_avg_pos_chge = scipy.stats.nanmean(pos_master_np_prices_chges, axis = 0)

# ar_master_np_neg_prices_chges = np.ma.masked_greater_equal(master_np_prices_chges, 0).filled(np.nan)
# ar_avg_neg_chge = scipy.stats.nanmean(ar_master_np_neg_prices_chges, axis = 0)

# ar_master_np_nonzero_prices_chges = np.ma.masked_equal(master_np_prices_chges, 0).filled(np.nan)
# ar_avg_nonzero_chge = scipy.stats.nanmean(ar_master_np_nonzero_prices_chges, axis = 0)

# ar_normal_chges = master_np_prices_chges[(np.abs(master_np_prices_chges) <= 0.1) & (master_np_prices_chges != 0)]
# ar_extreme_chges = master_np_prices_chges[(np.abs(master_np_prices_chges) > 0.1)]
# print 'Percentage of abnormal changes', float(len(ar_extreme_chges))/(len(ar_normal_chges) + len(ar_extreme_chges))

# # # TOO BIG => RESTRICT
# # n, bins, patches = plt.hist(ar_normal_chges[0:100000], 50, normed=1, facecolor='g')
# # plt.show()

# # n, bins, patches = plt.hist(ar_extreme_chges, 50, normed=1, facecolor='g')
# # plt.show()
# # CAUTION: still 324 changes among which some very high (-0.6) to be eliminated (except if...)

# # plt.step([i for i in range(300)], ar_avg_nonzero_chge[:300])
# # plt.show()


# # #################
# # ACTIVITY ANALYSIS
# # #################

# # BAD REPORTING

# c_start, c_end = 0, len(master_price['dates'])-1
# ls_late_start = [indiv_ind for indiv_ind, (start, end) in enumerate(ls_start_end) if start != c_start]
# ls_early_end = [indiv_ind for indiv_ind, (start, end) in enumerate(ls_start_end) if end != c_end]
# ls_short_spell = [indiv_ind for indiv_ind, (start, end) in enumerate(ls_start_end)\
                    # if start!= c_start and end !=c_end]
# ls_long_early_end = [indiv_ind for indiv_ind, (start, end) in enumerate(ls_start_end)\
                      # if start == c_start and end != c_end]
# ls_ctd_late_start = [indiv_ind for indiv_ind, (start, end) in enumerate(ls_start_end)\
                      # if start != c_start and end == c_end]

# dict_bad_reporting = {}
# for indiv_ind, ls_day_ind in enumerate(ls_ls_dilettante):
  # for day_ind in ls_day_ind:
	  # dict_bad_reporting.setdefault(day_ind, []).append(indiv_ind)
# # Missing period => nobody reported dilettante (though it could if short given corrections)

# ls_period_bad_reporting = [None for i in master_price['dates']]
# for day_ind, ls_period_indiv_ind in dict_bad_reporting.iteritems():
  # ls_period_bad_reporting[day_ind] = len(ls_period_indiv_ind)
# # pd_df_temp = pd.DataFrame(zip(*[master_price['diesel_price'][51], master_price['diesel_date'][51]]),\
                            # # index=master_price['dates'])
# # print pd_df_temp.to_string()
# # TODO: see why it crashes
# # pd_df_temp = pd.DataFrame(zip(*[list_period_bad_reporting, list_period_old_and_bad_reporting]),\
                            # # index=master_price['dates'], dtype = np.int)
# # pd_df_temp.plot()
# # plt.show()
# # TODO: Explore list of poorly reporting stations + late start / early end => some cheating/agreeing not to report?
# # TODO: Exploit proximity + same date (e.g. Argenteuil => what's happening there!? + Corsica?)
# # TODO: Generically get notion of relations between stations within a list (geographic, brand etc.)

# # CLOSED GAS STATIONS (TODO: use zagaz info)

# # Candidates for closed stations... 
# # Look around if openings? => Check if late_start in vincinity of those
# # TODO: also check on ID (ZIP...)
# # TODO: check by hand (?) with zagaz or other websites (extend dataset length?)
# ls_confirmed_candidates = []
# ls_doubtful_candidates = []
# for indiv_ind in ls_long_early_end:
  # if ls_ls_competitors[indiv_ind]:
    # ls_competitor_ind = [master_price['ids'].index(c_ind) for c_ind, c_dist in ls_ls_competitors[indiv_ind]]
    # ls_suspects = []
    # for competitor_ind in ls_competitor_ind:
      # if ls_start_end[competitor_ind][0]!= 0:
        # ls_suspects.append((competitor_ind, ls_start_end[competitor_ind][0]))
    # if ls_suspects:
      # ls_doubtful_candidates.append([(indiv_ind, ls_start_end[indiv_ind][1])] + ls_suspects)
    # else:
      # ls_confirmed_candidates.append(indiv_ind)
# # Can check brand, location, last prices (?)
# for indiv_ind in ls_confirmed_candidates:
  # if ls_start_end[indiv_ind][1] < 630:
    # indiv_id = master_price['ids'][indiv_ind]
    # print ls_start_end[indiv_ind][1], indiv_ind, indiv_id,\
          # master_price['dict_info'][indiv_id]['name'],\
          # master_price['dict_info'][indiv_id]['brand'],\
          # get_latest_info(indiv_id, 'address', master_info)

# OPENED GAS STATIONS (TODO)

# #############################
# BRAND CHANGES (SEPARATE FILE)
# #############################

# ##############
# PRICE ANALYSIS
# ##############

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

# # TODO: restrict size to begin with (time/location)
# # pd_mi_final.ix['1500007',:] # based on id
# # pd_mi_final[pd_mi_final['code_geo'].str.startswith('01', na=False)] # based on insee
# # http://stackoverflow.com/questions/17242970/multi-index-sorting-in-pandas
# pd_mi_final_alt = pd_mi_final.swaplevel('id', 'date')
# pd_mi_final_alt = pd_mi_final_alt.sort()
# pd_mi_final_extract = pd_mi_final_alt.ix['20110904':'20111004']
# # pd_pd_final_extract = pd_mi_final_extract.to_panel()

# CONVERT MULTI INDEX TO PANEL DATA
pd_pd_final = pd_mi_final.to_panel()

# GET COLUMN OCCURENCES
ar_brand_1 = np.unique(pd_pd_final['brand_1'].values)
se_brand_1_end = pd_pd_final.minor_xs('20130604')['brand_1'].dropna().value_counts()
ls_big_brands_end = list(se_brand_1_end.index)[0:5]

# MEAN PRICE PER GROUP (BRAND, TODO: REGION / DPT etc.)
ls_se_mean_big_brands_end = []
for brand in ls_big_brands_end:
  ls_se_mean_big_brands_end.append(pd_pd_final['price'][pd_pd_final['brand_1'] == brand].mean())
# TODO: inspect ls_se_mean_big_brands_end[1][53:57] # brand: u'INTERMARCHE'

# BRAND PRICES
day, brand = '20111027', 'INTERMARCHE'
for day in pd_pd_final.minor_axis[50:60]:
  pd_df_day = pd_pd_final.minor_xs(day)
  pd_df_day_brand = pd_df_day['price'][pd_df_day['brand_1'] == brand]
  pd_df_day_brand.describe()

# TODO: identify 'INTERMARCHE' which change price between day 52 and day 53
pd_df_brand = pd_pd_final['price'][pd_pd_final['brand_1'] == "INTERMARCHE"]
ls_select_inds = np.where((pd.notnull(pd_df_brand[pd_pd_final.minor_axis[52]])) &\
                   (pd_df_brand[pd_pd_final.minor_axis[52]]!=pd_df_brand[pd_pd_final.minor_axis[53]]))[0]
ls_select_ids = [pd_pd_final.major_axis[ind] for ind in ls_select_inds]
ls_valid_inds = np.where(pd.notnull(pd_df_brand[pd_pd_final.minor_axis[52]]))[0]
ls_valid_ids = [pd_pd_final.major_axis[ind] for ind in ls_valid_inds]
ls_unselected_ids = [indiv_id for indiv_id in ls_valid_ids if indiv_id not in ls_select_ids]
# total valid prices: (pd.notnull(pd_df_brand[pd_pd_final.minor_axis[52]])).sum()
plt.plot(pd_pd_final.major_xs('1000009')['price'])
plt.show()

# check competition
ls_ls_competitors = [sorted(ls_competitors, key=lambda x: x[1])\
                      if ls_competitors else ls_competitors for 
                        ls_competitors in ls_ls_competitors]

# TODO: loop + create functions... (also: might want to check sp95 if similar event?)
# add brands on graph + other info
select_ind = ls_select_inds[0]
plt.plot(master_price['diesel_price'][select_ind])
ls_competitors = ls_ls_competitors[select_ind][0:5]
if ls_competitors:
  for competitor_id, competitor_distance in ls_competitors:
    competitor_ind = master_price['ids'].index(competitor_id)
    plt.plot(master_price['diesel_price'][competitor_ind])
plt.show()


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

# OLD WAY TO BUILD PANDAS PRICE DATA FILE

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
