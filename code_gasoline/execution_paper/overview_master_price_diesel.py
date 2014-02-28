#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *

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

# #########
# TURNOVER
# #########

ls_start_end, ls_nan, dict_dilettante = get_overview_reporting_bis(master_price['diesel_price'],
                                                                   master_price['dates'],
                                                                   master_price['missing_dates'])
# TODO: correct missing dates...

#dict_turnover = get_overview_turnover(ls_start_end, master_price['dates'], 3)

# BAD REPORTING OVER TIME
ls_nb_missing_prices = [0 if date not in master_price['missing_dates'] else np.nan\
                          for date in master_price['dates']]
for indiv_ind, ls_missing_day_ind in dict_dilettante.items():
  for day_ind in ls_missing_day_ind:
    ls_nb_missing_prices[day_ind] += 1
ar_nb_missing_prices = np.array(ls_nb_missing_prices)
#plt.plot(ar_nb_missing_prices)
#plt.show()

# BAD REPORTING OVER INDIVIDUALS
print 'Nb of nan only:', len(ls_nan)
ls_reporting = []
for indiv_ind, indiv_start_end in enumerate(ls_start_end):
  ls_reporting.append(list(indiv_start_end) + [len(dict_dilettante.get(indiv_ind, []))])
ls_columns = ['start', 'end', 'nb_missing']
df_reporting = pd.DataFrame(ls_reporting, columns = ls_columns, index = master_price['ids'])
start_full, end_full = 0, 639
df_full  = df_reporting[(df_reporting['start'] <= start_full) & (df_reporting['end'] >= end_full)]
df_short = df_reporting[(df_reporting['start'] >  start_full) & (df_reporting['end'] <  end_full)]
df_late  = df_reporting[(df_reporting['start'] >  start_full) & (df_reporting['end'] >= end_full)]
df_early = df_reporting[(df_reporting['start'] <= start_full) & (df_reporting['end'] < end_full)]

# EARLY END (Candidates for duplicates / closed stations / bad reporting)
# Check with zagaz or other websites (extend dataset length?)
## Add station info in df: name, brand, city (last original price...)
## Compare with found nearyby stations (duplicate check)

ls_confirmed_candidates = []
ls_doubtful_candidates = []
for indiv_id in df_early.index:
  indiv_ind = master_price['ids'].index(indiv_id)
  if ls_ls_competitors[indiv_ind]:
    ls_competitor_ids = [competitor_id for competitor_id, distance in ls_ls_competitors[indiv_ind]]
    ls_suspects = []
    for competitor_id in ls_competitor_ids:
      if (competitor_id in df_short.index) or (competitor_id in df_late.index):
        ls_suspects.append((competitor_id, df_reporting['start'].ix[competitor_id]))
    if ls_suspects:
      ls_doubtful_candidates.append([(indiv_id, df_reporting['start'].ix[indiv_id])] + ls_suspects)
    else:
      ls_confirmed_candidates.append(indiv_id)

# LATE START
# Same location? based on zip (map?)

# ##############################
# BRAND CHANGES (QUICK OVERVIEW)
# ##############################

## Count

# #################
# PRICE OVERVIEW
# #################

# TODO: 3 digits or not, how many used (to be done in pandas?)
# Variations: size of variations, grid of variations used (to be done in pandas?)
# Promotions (successive inverse moves)
# Brand changes and impact (pandas)
# Price graphs (pandas)

ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
ls_ls_price_variations = get_price_variations(ls_ls_price_durations)

# PRICE VARIATION VALUES (DEPRECATED?)
dict_price_variations = Counter()
for ls_price_variations in ls_ls_price_variations:
  if ls_price_variations:
    for variation in [variation for (variation, ls_day_ind) in ls_price_variations if not np.isnan(variation)]:
      dict_price_variations[variation] += 1 

zero_threshold = np.float64(1e-10)
master_np_prices = np.array(master_price['diesel_price'], np.float64)
df_prices = pd.DataFrame(master_np_prices.T, columns = master_price['ids'], index = master_price['dates'])
df_chges = df_prices.shift(1) - df_prices

# TODO: apply also at region / dpt / city / brand level => apply to subsets of df_chges

# Period price change frequency
ls_freq_price_chges = []
for day in df_chges.index:
  nb_valid_prices = df_chges.ix[day].count()
  nb_no_price_chge = df_chges.ix[day][np.abs(df_chges.ix[day]) < zero_threshold].count()
  nb_pos_price_chge = df_chges.ix[day][df_chges.ix[day] >  zero_threshold].count()
  nb_neg_price_chge = df_chges.ix[day][df_chges.ix[day] < -zero_threshold].count()
  ls_freq_price_chges.append([nb_valid_prices, nb_no_price_chge, nb_pos_price_chge, nb_neg_price_chge])
ls_columns = ['nb_valid', 'nb_no_chge', 'nb_pos_chge', 'nb_neg_chge']
df_freq_price_chges = pd.DataFrame(ls_freq_price_chges, columns = ls_columns, index = df_chges.index)
df_freq_price_chges['pct_chge'] = (df_freq_price_chges['nb_pos_chge'] + df_freq_price_chges['nb_neg_chge'])/\
                                     df_freq_price_chges['nb_valid']
#df_freq_price_chges[['nb_pos_chge', 'nb_neg_chge']][0:100].plot(kind = 'bar')
#plt.plot()
#df_freq_price_chges['pct_chge'][355:450].plot(kind = 'bar')
#plt.show()

# Period price change values (TODO: MERGE WITH PREVIOUS!)
# TODO: see use of describe (standard metrics) and merging all in one df (flex: quantiles etc)
ls_val_price_chges = []
for day in df_chges.index:
  se_pos_price_chge = df_chges.ix[day][df_chges.ix[day] >  zero_threshold]
  se_neg_price_chge = df_chges.ix[day][df_chges.ix[day] < -zero_threshold]
  med_pos_chge = np.median(se_pos_price_chge)
  avg_pos_chge = np.mean(se_pos_price_chge)
  med_neg_chge = np.median(se_neg_price_chge)
  avg_neg_chge = np.mean(se_neg_price_chge)
  ls_val_price_chges.append([med_pos_chge, avg_pos_chge, med_neg_chge, avg_neg_chge])
ls_columns = ['med_pos_chge', 'avg_pos_chge', 'med_neg_chge', 'avg_neg_chge']
df_val_price_chges = pd.DataFrame(ls_val_price_chges, columns = ls_columns, index = df_chges.index)
#df_val_price_chges.plot()
#plt.show()

# FIRM LEVEL DESCRIPTIVE STATICS

ls_ls_indiv_chges = []
for indiv_id in df_chges.columns:
  # TODO: Check what to do with missing values(exclude first not to miss any change?)
  # TODO: Exclusion of stations from dispersion stats: count all chges...
  nb_valid_prices = df_chges[indiv_id].count()
  nb_no_price_chge = df_chges[indiv_id][np.abs(df_chges[indiv_id]) < zero_threshold].count()
  se_pos_price_chge = df_chges[indiv_id][df_chges[indiv_id] >  zero_threshold]
  se_neg_price_chge = df_chges[indiv_id][df_chges[indiv_id] < -zero_threshold]
  nb_pos_price_chge = se_pos_price_chge.count()
  nb_neg_price_chge = se_neg_price_chge.count()
  med_pos_chge = np.median(se_pos_price_chge)
  avg_pos_chge = np.mean(se_pos_price_chge)
  med_neg_chge = np.median(se_neg_price_chge)
  avg_neg_chge = np.mean(se_neg_price_chge)
  ls_ls_indiv_chges.append([nb_valid_prices, nb_no_price_chge, nb_pos_price_chge, nb_neg_price_chge,
                            med_pos_chge, avg_pos_chge, med_neg_chge, avg_neg_chge])
ls_columns = ['nb_valid', 'nb_no_chge', 'nb_pos_chge', 'nb_neg_chge',
              'med_pos_chge', 'avg_pos_chge', 'med_neg_chge', 'avg_neg_chge']
df_indiv_price_chges = pd.DataFrame(ls_ls_indiv_chges, columns = ls_columns, index = df_chges.columns)
df_indiv_price_chges['nb_chge'] = df_indiv_price_chges['nb_pos_chge'] + df_indiv_price_chges['nb_neg_chge']
df_indiv_price_chges['pct_chge'] = df_indiv_price_chges['nb_chge'] / df_indiv_price_chges['nb_valid']
# TODO: check if should not rather divide by nb of days?
# TODO: stats by brand / dpt etc / nb competitors etc.

print 'Stations that should almost certainly be excluded:',\
  len(df_indiv_price_chges[df_indiv_price_chges['pct_chge'] < 0.03])

#pd.options.display.float_format = '{:10,.2f}'.format
#pd.set_option('max_columns',10)
#print df_indiv_price_chges.ix[0:100].to_string()

# ###########
# DEPRECATED
# ###########

## REMINDER: USE OF PANEL DATA

#pd_panel_data_master['10000001'] # select station 10000001 (df object)
#pd_panel_data_master.major_xs(pd_panel_data_master.major_axis[0]) # select all station at 1st period (df object)
#pd_df_first_period = pd_panel_data_master.major_xs(pd_panel_data_master.major_axis[0]).T 
##tranpose (items: brand, price)
#pd_df_first_period[pd_df_first_period['brand']=='TOTAL']['price'] # selects all TOTAL prices in 1st period
#np.mean(pd_df_first_period[pd_df_first_period['brand']=='TOTAL']['price']) # average TOTAL price in 1st period
## average price in 1st period at TOTAL stations in Paris
#np.mean(pd_df_first_period[(pd_df_first_period['brand']=='TOTAL') & \
#                           (pd_df_first_period['zip_code'].str.startswith('75')) & \
#                           (pd_df_first_period['zip_code'].str.len()==5)]['price'])
## display prices of TOTAL stations in Paris for periods 1 to 10 ?

## OLD WAY TO BUILD PANDAS PRICE DATA FILE

#dict_panel_data_master = {}
#ls_formatted_dates = ['%s/%s/%s' %(elt[:4], elt[4:6], elt[6:]) for elt in master_price['dates']]
#index_formatted_dates = pd.to_datetime(ls_formatted_dates)
#for i, id in enumerate(master_price['ids']):
#  if 'code_geo' in master_price['dict_info'][id]:
#    ls_station_prices = master_price['diesel_price'][i]
#    ls_station_brands = [dict_brands[get_str_no_accent_up(brand)][1] if brand else brand\
#                            for brand in get_field_as_list(id, 'brand', master_price)]
#    zip_code = '%05d' %int(id[:-3])
#    dict_station = {'price' : np.array(ls_station_prices, dtype = np.float32),
#                    'brand' : np.array(ls_station_brands),
#                    'zip_code' : zip_code,
#                    'department' : zip_code[:2],
#                    'region' : dict_dpts_regions[zip_code[:2]],
#                    'insee_code' : master_price['dict_info'][id]['code_geo']}
#    dict_panel_data_master[id] = pd.DataFrame(dict_station, index = index_formatted_dates)
#pd_pd_master = pd.Panel(dict_panel_data_master)


# pd_df_price = pd_pd_master.minor_xs('price')
# pd_df_price_total = pd_pd_master.minor_xs('price')[pd_pd_master.minor_xs('brand') == 'TOTAL']
# pd_df_mean_comp = pd.concat([pd_df_price.mean(1),pd_df_price_total.mean(1)], keys = ['All', 'Total'] , axis = 1)
# pd_df_mean_comp_2 = pd_df_price_total.mean(1) - pd_df_price.mean(1)

# # ANALYSIS OF PRICES AT GLOBAL LEVEL (DEPRECATED)
# TODO: check comparison with 0
# master_np_prices = np.array(master_price['diesel_price'], dtype = np.float64)
# master_np_prices_chges = master_np_prices[:,:-1] - master_np_prices[:,1:]
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
