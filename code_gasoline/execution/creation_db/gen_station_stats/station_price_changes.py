#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *
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

# ###################
# BUILD DF INFO
# ###################

dict_std_brands = {v[0]: v for k, v in dict_brands.items()}

ls_services = [service for indiv_id, indiv_info in master_info.items()\
                 if indiv_info['services'][-1] for service in indiv_info['services'][-1]]
ls_services = list(set(ls_services))
for indiv_id, indiv_info in master_info.items():
  # Caution [] and None are false but different here
  if indiv_info['services'][-1] is not None:
    ls_station_services = [0 for i in ls_services]
    for service in indiv_info['services'][-1]:
      service_ind = ls_services.index(service)
      ls_station_services[service_ind] = 1
  else:
    ls_station_services = [None for i in ls_services]
  master_info[indiv_id]['list_service_dummies'] = ls_station_services

ls_ls_info = []
for indiv_ind, indiv_id in enumerate(master_price['ids']):
  # from master_price
  indiv_dict_info = master_price['dict_info'][indiv_id]
  city = indiv_dict_info['city']
  zip_code = '%05d' %int(indiv_id[:-3]) # todo: improve if must be used alone
  region = dict_dpts_regions[zip_code[:2]]
  code_geo = indiv_dict_info.get('code_geo')
  code_geo_ardts = indiv_dict_info.get('code_geo_ardts')
  brand_1_b = indiv_dict_info['brand_std'][0][0]
  brand_2_b = dict_std_brands[indiv_dict_info['brand_std'][0][0]][1]
  brand_type_b = dict_std_brands[indiv_dict_info['brand_std'][0][0]][2]
  brand_1_e = indiv_dict_info['brand_std'][-1][0]
  brand_2_e = dict_std_brands[indiv_dict_info['brand_std'][-1][0]][1]
  brand_type_e = dict_std_brands[indiv_dict_info['brand_std'][-1][0]][2]
  # from master_info
  highway, hours = None, None
  ls_service_dummies = [None for i in ls_services]
  if master_info.get(indiv_id):
    highway = master_info[indiv_id]['highway'][3]
    hours = master_info[indiv_id]['hours'][-1]
    ls_service_dummies = master_info[indiv_id]['list_service_dummies']
  ls_ls_info.append([city, zip_code, code_geo, code_geo_ardts, region,
                     brand_1_b, brand_2_b, brand_type_b,
                     brand_1_e, brand_2_e, brand_type_e,
                     highway, hours] + ls_service_dummies)
ls_columns = ['city', 'zip_code', 'code_geo', 'code_geo_ardts', 'region',
              'brand_1_b', 'brand_2_b', 'brand_type_b',
              'brand_1_e', 'brand_2_e', 'brand_type_e',
              'highway', 'hours'] + ls_services
df_info = pd.DataFrame(ls_ls_info, master_price['ids'], ls_columns)

df_info['dpt'] = df_info['code_geo'].map(lambda x: x[:2] if x else None)


# #########
# TURNOVER
# #########

ls_start_end, ls_nan, dict_dilettante = get_overview_reporting_bis(master_price['diesel_price'],
                                                                   master_price['dates'],
                                                                   master_price['missing_dates'])

#dict_turnover = get_overview_turnover(ls_start_end, master_price['dates'], 3)

# Bad reporting over time
ls_nb_missing_prices = [0 if date not in master_price['missing_dates'] else np.nan\
                          for date in master_price['dates']]
for indiv_ind, ls_missing_day_ind in dict_dilettante.items():
  for day_ind in ls_missing_day_ind:
    ls_nb_missing_prices[day_ind] += 1
ar_nb_missing_prices = np.array(ls_nb_missing_prices)
#plt.plot(ar_nb_missing_prices)
#plt.show()

# Bad reporting over individuals
print '\nNb of stations with no price (nan): {:,.0f}'.format(len(ls_nan))
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

# ######################
# BUILD DF PRICE CHANGES
# ######################

# Variations: size of variations, grid of variations used
# Promotions
# Brand changes and impact (here?)
# Price graphs (here?)

ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
ls_ls_price_variations = get_price_variations(ls_ls_price_durations)

# Create prices and price changes pandas dataframes
zero_threshold = np.float64(1e-10)
ls_dates = [pd.to_datetime(date) for date in master_price['dates']]
df_prices = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_dates).T
df_chges = df_prices - df_prices.shift(1)

# Stations using 3 digit prices
ls_two_digit_ids, ls_three_digit_ids = [], []
for col in df_prices.columns:
  ar_prices_cent = df_prices[col].values*100
  if any(ar_prices_cent[~np.isnan(ar_prices_cent)] !=\
          ar_prices_cent[~np.isnan(ar_prices_cent)].astype(int).astype(float)):
    ls_three_digit_ids.append(col)
  elif len(ar_prices_cent[~np.isnan(ar_prices_cent)]) > 0:
    ls_two_digit_ids.append(col)
print '\nNb of stations with 2 digit prices: {:,.0f}'.format(len(ls_two_digit_ids))
print '\nNb of stations with 3 digit prices: {:,.0f}'.format(len(ls_three_digit_ids))

# Nb of prices in data (todo: apply restrictions before: highway etc?)
ar_all_prices = df_prices.values
ar_all_prices = ar_all_prices[~np.isnan(ar_all_prices)]
print '\nNb of prices: {:,.0f}'.format(len(ar_all_prices))

# Last figure of 3 digit prices
ar_3d_prices = (df_prices[ls_three_digit_ids]*1000).values
# todo: improve (int then str avoids 1299.0 but not robust)
ar_3d_prices = ar_3d_prices[~np.isnan(ar_3d_prices)].astype(int).astype(str)  
print '\nNb of 3 digit prices: {:,.0f}'.format(len(ar_3d_prices))
dict_last_digit = {}
for i in range(10):
  ar_3dld_prices = ar_3d_prices[np.core.defchararray.startswith(ar_3d_prices, '%s'%i, start = -1)]
  dict_last_digit[i] = len(ar_3dld_prices)
print '\nNb of 3 digit prices ending with (nb and %)'
for k,v in dict_last_digit.items():
	print "{:>d}{:>12,.0f}{:>8.2f}".format(k, v, float(v)/len(ar_3d_prices))

# Price changes: Value of price changes
ls_rows = []
for indiv_id in df_chges.columns:
  # todo: check what to do with missing values(exclude first not to miss any change?)
  se_pos_price_chge = df_chges[indiv_id][df_chges[indiv_id] >  zero_threshold]
  se_neg_price_chge = df_chges[indiv_id][df_chges[indiv_id] < -zero_threshold]
  ls_rows.append([df_chges[indiv_id].count(), # nb valid (no nan) price chges
                  df_chges[indiv_id][df_chges[indiv_id].abs() < zero_threshold].count(), # nb no chge
                  se_pos_price_chge.count(),
                  se_neg_price_chge.count(),
                  se_pos_price_chge.median(),
                  se_pos_price_chge.mean(),
                  se_neg_price_chge.median(),
                  se_neg_price_chge.mean()])
ls_columns = ['nb_valid', 'nb_no_chge', 'nb_pos_chge', 'nb_neg_chge',
              'med_pos_chge', 'avg_pos_chge', 'med_neg_chge', 'avg_neg_chge']
df_chges_indiv_su = pd.DataFrame(ls_rows, columns = ls_columns, index = df_chges.columns)
df_chges_indiv_su['nb_chge'] = df_chges_indiv_su['nb_pos_chge'] + df_chges_indiv_su['nb_neg_chge']
df_chges_indiv_su['pct_chge'] = df_chges_indiv_su['nb_chge'] / df_chges_indiv_su['nb_valid']
# todo: check if should not rather divide by nb of days?

# Price rigidity: Frequency of prices changes
ls_rigidity_rows = []
for indiv_id, ls_price_durations in zip(master_price['ids'], ls_ls_price_durations):
  ls_indiv_durations = []
  for i, price_duration in enumerate(ls_price_durations[2:-1], 2):
    # discard first and last price
    # consider only prices which are not followed by missing periods
    if not np.isnan(price_duration[0]):
      # ls_indiv_durations.append(len(ls_price_durations[i-1][1]))
      ls_indiv_durations.append(len(price_duration[1]))
  if ls_indiv_durations:
    ls_rigidity_rows.append([len(ls_indiv_durations),
                             np.mean(ls_indiv_durations),
                             np.std(ls_indiv_durations),
                             np.min(ls_indiv_durations),
                             np.max(ls_indiv_durations)])
  else:
    ls_rigidity_rows.append([np.nan for i in range(5)])
ls_columns = ['nb_prices_used', 'mean_length', 'std_length', 'min_length', 'max_length']
df_rigidity = pd.DataFrame(ls_rigidity_rows, master_price['ids'], ls_columns)
# Solve pbm... one length > 60: probably two stations reconciled?
df_rigidity = df_rigidity[df_rigidity.index != '35660003']
print "\nNb w/ less than 10 prices (dropped): {:>6.2f}".\
         format(len(df_rigidity[(pd.isnull(df_rigidity['nb_prices_used'])) |\
                   (df_rigidity['nb_prices_used'] < 10)]))
ls_ids_nb_prices_drop = df_rigidity.index[df_rigidity['nb_prices_used'] < 10]
df_rigidity = df_rigidity[df_rigidity['nb_prices_used'] >= 10]
print df_rigidity.describe()
print "\nNb of stations with censored prices: {:>8.2f}".\
        format(len(df_rigidity[df_rigidity['max_length'] == 60]))
print "\nAvg max length of a price validity w/o censored: {:>8.2f}".\
        format(df_rigidity['max_length'][df_rigidity['max_length'] < 60].mean())

# Price changes: day of week (todo: normalize by available days!)
ar_ind_dow = df_prices.index.dayofweek # seems faster to store it first
ls_chge_dow_rows = []
ls_se_chge_dows = []
for ls_price_durations in ls_ls_price_durations:
  ls_chge_days = []
  for price, ls_price_days in ls_price_durations:
    if price:
      ls_chge_days.append(ls_price_days[0])
  ls_chge_dows = [ar_ind_dow[i] for i in ls_chge_days]
  se_chge_dows = pd.Series(ls_chge_dows).value_counts()
  ls_se_chge_dows.append(se_chge_dows)
  dow_argmax = se_chge_dows.argmax()
  dow_max_pct = se_chge_dows.max() / float(se_chge_dows.sum())
  ls_chge_dow_rows.append((dow_argmax, dow_max_pct))
df_chge_dow = pd.DataFrame(ls_chge_dow_rows, master_price['ids'], ['dow_max', 'pct_dow_max'])

df_chges_indiv = pd.merge(df_chges_indiv_su, df_rigidity, left_index = True, right_index = True)
df_chges_indiv = pd.merge(df_chges_indiv, df_chge_dow, left_index = True, right_index = True)

ls_ids_frequency_drop =  df_chges_indiv.index[df_chges_indiv['pct_chge'] < 0.03]
print '\nStations w/ less than 1 price/month: {:>6.0f}'.format(len(ls_ids_frequency_drop))

# Get final id list
# TODO: may want to check location of dropped stations (based on price rigidity)
ls_ids_highway_drop = df_info.index[df_info['highway'] == 1]
ls_ids_corsica_drop = df_info.index[df_info['region'] == 'Corse'] # could keep!
print '\nStations on highway: {:>6.0f}'.format(len(ls_ids_highway_drop))
print '\nStations in Corsica: {:>6.0f}'.format(len(ls_ids_corsica_drop))

ls_ids_drop = ls_ids_nb_prices_drop + ls_ids_frequency_drop +\
              ls_ids_highway_drop + ls_ids_corsica_drop

ls_ids_final = [indiv_id for indiv_id in df_chges_indiv.index\
                  if indiv_id not in ls_ids_drop]

# List of ids per type
df_info_st = df_info.ix[[x for x in df_info.index if x in ls_ids_final]]
ls_ids_sup = df_info_st.index[df_info_st['brand_type_e'] == 'SUP']
ls_ids_ind = df_info_st.index[df_info_st['brand_type_e'] == 'IND']
ls_ids_oil = df_info_st.index[df_info_st['brand_type_e'] == 'OIL']
ls_ids_oil_noelan = df_info_st.index[(df_info_st['brand_type_e'] == 'OIL') &\
                                     (df_info_st['brand_1_e'] != 'ELAN')]

pd.options.display.float_format = '{:10,.2f}'.format

print '\nAll stations'
print df_chges_indiv.ix[ls_ids_final].describe()
print '\nOil'
print df_chges_indiv.ix[ls_ids_sup].describe()
print '\nSup'
print df_chges_indiv.ix[ls_ids_oil].describe()
print '\nInd'
print df_chges_indiv.ix[ls_ids_ind].describe()

df_prices_st = df_prices[ls_ids_final]
ls_nb_prices = [df_prices_st.ix[ind].count() for ind in df_prices_st.index]
print "Min nb of prices observed in one day: {:>6,.0f}".\
        format(np.min([x for x in ls_nb_prices if x != 0]))
print "Max nb of prices observed in one day: {:>6,.0f}".\
        format(np.max([x for x in ls_nb_prices if x != 0]))

# Total changes per period
ls_ids_total = df_info_st.index[df_info_st['brand_2_e'] == 'TOTAL']
ls_ids_total_92 = df_info_st.index[(df_info_st['brand_2_e'] == 'TOTAL') &\
                                   (df_info_st['dpt'] == '92')]

ls_total_nb_chges = []
for ind in df_chges.index:
  ls_total_nb_chges.append((df_chges.ix[ind][ls_ids_total].count(),
                            len(df_chges.ix[ind][ls_ids_total]\
                              [df_chges.ix[ind][ls_ids_total].abs() > zero_threshold])))
df_total_chges = pd.DataFrame(ls_total_nb_chges, df_chges.index)

# Store list of ids to be kept for analysis
enc_json(ls_ids_final, os.path.join(path_dir_built_json, 'ls_ids_final.json'))

# Final description of price changes (temporal)
df_chges = df_chges[ls_ids_final]
ls_rows = []
for day in df_chges.index:
  se_pos_price_chge = df_chges.ix[day][df_chges.ix[day] >  zero_threshold]
  se_neg_price_chge = df_chges.ix[day][df_chges.ix[day] < -zero_threshold]
  ls_rows.append([df_chges.ix[day].count(), # valid (no nan) chges
                  df_chges.ix[day][df_chges.ix[day].abs() < zero_threshold].count(), # no chge
                  se_pos_price_chge.count(),
                  se_neg_price_chge.count(),
                  se_pos_price_chge.median(),
                  se_pos_price_chge.mean(),
                  se_neg_price_chge.median(),
                  se_neg_price_chge.mean()])
ls_columns = ['nb_valid', 'nb_no_chge', 'nb_pos_chge', 'nb_neg_chge',
              'med_pos_chge', 'avg_pos_chge', 'med_neg_chge', 'avg_neg_chge']
df_chges_su = pd.DataFrame(ls_rows, df_chges.index, ls_columns)
df_chges_su['nb_valid'][df_chges_su['nb_valid'] == 0] = np.nan
df_chges_su['pct_chge'] = df_chges_su[['nb_pos_chge','nb_neg_chge']].sum(1)/df_chges_su['nb_valid']
df_chges_su['nb_chge'] = df_chges_su[['nb_pos_chge', 'nb_neg_chge']].sum(1)
