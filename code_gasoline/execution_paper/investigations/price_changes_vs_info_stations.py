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
  zip_code = '%05d' %int(indiv_id[:-3]) # TODO: improve if must be used alone
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

# Exclude highway and Corse
df_info = df_info[(df_info['highway'] != 1) &\
                  (df_info['region'] != 'Corse')]

ls_ids_sup = df_info.index[df_info['brand_type_e'] == 'SUP']
ls_ids_oil = df_info.index[df_info['brand_type_e'] == 'OIL']
ls_ids_oil_noelan = df_info.index[(df_info['brand_type_e'] == 'OIL') &\
                                  (df_info['brand_1_e'] != 'ELAN')]
ls_ids_ind = df_info.index[df_info['brand_type_e'] == 'IND']

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

# #################
# PRICE OVERVIEW
# #################

# Variations: size of variations, grid of variations used
# Promotions
# Brand changes and impact (here?)
# Price graphs (here?)

ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
ls_ls_price_variations = get_price_variations(ls_ls_price_durations)

# Price variation values (todo: deprecate)
dict_price_variations = Counter()
for ls_price_variations in ls_ls_price_variations:
  if ls_price_variations:
    for variation in [variation for (variation, ls_day_ind)\
                        in ls_price_variations if not np.isnan(variation)]:
      dict_price_variations[variation] += 1 

# Price ridigity
ls_rigidity_rows = []
for indiv_id, ls_price_durations in zip(master_price['ids'], ls_ls_price_durations):
  ls_indiv_durations = []
  for i, price_duration in enumerate(ls_price_durations[2:-1], 2):
    # discard first and last price
    # consider only prices which are not followed by missing periods
    if not np.isnan(price_duration[0]):
      ls_indiv_durations.append(len(ls_price_durations[i-1][1]))
  ls_rigidity_rows.append([len(ls_indiv_durations),
                           np.mean(ls_indiv_durations),
                           np.std(ls_indiv_durations)])
ls_columns = ['nb_prices_used', 'mean_length', 'std_length']
df_rigidity = pd.DataFrame(ls_rigidity_rows, master_price['ids'], ls_columns)
print "\nMean length of a price validity: {:>4.2f}".format(df_rigidity['mean_length'].mean())
print "\nMean length of a price validity(10 prices at least): {:>4.2f}".\
        format(df_rigidity[df_rigidity['nb_prices_used'] > 10]['mean_length'].mean())

print "\nMean length of a price validity OIL: {:>4.2f}".\
        format(df_rigidity.ix[ls_ids_oil]['mean_length'].mean())
print "\nMean length of a price validity OIL (no ELAN): {:>4.2f}".\
        format(df_rigidity.ix[ls_ids_oil_noelan]['mean_length'].mean())
print "\nMean length of a price validity SUP: {:>4.2f}".\
        format(df_rigidity.ix[ls_ids_sup]['mean_length'].mean())
print "\nMean length of a price validity IND: {:>4.2f}".\
        format(df_rigidity.ix[ls_ids_ind]['mean_length'].mean())

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

# Daily price changes: number and value
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

# Changes per day of week
df_chges_su['nb_chge'] = df_chges_su[['nb_pos_chge', 'nb_neg_chge']].sum(1)
df_chges_su['dow'] = df_chges_su.index.dayofweek
# assumes that 0 chge is equiv to missing... (essentially true)
df_chges_su_notnan = df_chges_su[df_chges_su['nb_chge'] != 0]
min_cut = df_chges_su_notnan['dow'].value_counts().min()
ls_dow_chge_desc = [df_chges_su_notnan['nb_chge'][df_chges_su_notnan['dow'] == i]\
                      [:min_cut].describe() for i in range(7)]
ls_dow_chge_sum = [df_chges_su_notnan['nb_chge'][df_chges_su_notnan['dow'] == i]\
                      [:min_cut].sum() for i in range(7)]
print '\nChanges per day of week'
for i, x in enumerate(ls_dow_chge_sum):
  print '% of total chges on dow {:,.0f}: {:>4.2f}'.format(i, x/float(np.sum(ls_dow_chge_sum)))

# http://matplotlib.org/examples/pylab_examples/bar_stacked.html
# http://stackoverflow.com/questions/14920691/using-negative-values-in-a-matplotlibs-bar-plot
# todo: add average price or price change with secondary axis?
ar_pos_chges = df_chges_su['nb_pos_chge'][:'2012-06'].values
ar_neg_chges = df_chges_su['nb_neg_chge'][:'2012-06'].values

# Summary graphs of daily price changes
plt.rcParams['figure.figsize'] = 16, 6
fig = plt.figure()
ax1 = fig.add_subplot(111)
width = 0.8
p1 = ax1.bar(range(len(ar_pos_chges)), ar_pos_chges, width=width, color = 'r', label='positive')
p2 = ax1.bar(range(len(ar_neg_chges)), -ar_neg_chges, width=width, color = 'y', label='negative')
ls_x_axis = []
for i, date in enumerate(df_chges_su['nb_neg_chge'][:'2012-06'].index[1:], 1):
  if date.month != df_chges_su['nb_neg_chge'][:'2012-06'].index[i-1].month:
		ls_x_axis.append((i, date.strftime('%b-%Y')))
ind = np.array([x[0] for x in ls_x_axis])
handles, labels = ax1.get_legend_handles_labels()
ax1.legend(handles, labels, loc = 4)
ax1.grid()
plt.xlim((0, len(ar_neg_chges)))
plt.xticks(ind+0.8/2., [x[1] for x in ls_x_axis])
y_l, y_t = plt.yticks() # can be done with ax1
plt.yticks(label = np.abs(y_l).astype(int))
plt.tight_layout()
plt.show()

#p1 = plt.bar(range(len(ar_pos_chges)), ar_pos_chges, color = 'r')
#p2 = plt.bar(range(len(ar_neg_chges)), ar_neg_chges, color = 'y', bottom = ar_pos_chges)
#plt.show()
#fig, ax = plt.subplots()
#df_chges_su['nb_pos_chge'][0:200].plot(style = 'bs-', ax=ax)
#df_chges_su['nb_neg_chge'][0:200].plot(style = 'ro-', ax=ax)
#plt.show()
#df_chges_su[['nb_pos_chge', 'nb_neg_chge']][0:100].plot(kind = 'bar')
#plt.plot()
#df_chges_su['pct_chge'][355:450].plot(kind = 'bar')
#plt.show()

# Firm level descriptive stats

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
# todo: stats by brand / dpt etc / nb competitors etc.

print '\nStations that should almost certainly be excluded:',\
  len(df_chges_indiv_su[df_chges_indiv_su['pct_chge'] < 0.03])

#pd.options.display.float_format = '{:10,.2f}'.format
#pd.set_option('max_columns',10)
#print df_chges_indiv_su.ix[0:100].to_string()

# Big price cuts & promotions (tentative)

# Big price cuts (nb per day)
ls_cuts = [[], [], []]
for day in df_chges.index:
	ls_cuts[0].append(len(df_chges.ix[day][df_chges.ix[day] < -0.04]))
	ls_cuts[1].append(len(df_chges.ix[day][df_chges.ix[day] < -0.05]))
	ls_cuts[2].append(len(df_chges.ix[day][df_chges.ix[day] < -0.10]))
# or add to df_chges_su ?
ls_columns = ['nb_promo_04', 'nb_promo_05', 'nb_promo_10']
df_cuts_su = pd.DataFrame(zip(*ls_cuts), index = df_chges.index, columns = ls_columns)

# Promotions: look for successive inverse price cuts at station level
dict_promo = get_sales(ls_ls_price_variations, 3)
# update function to get ids and drop loop
for k,v in dict_promo.items():
  dict_promo[master_price['ids'][k]] = v
  del(dict_promo[k])
ls_promo = [(k, len(v)) for k,v in dict_promo.items()]
df_promo = pd.DataFrame(ls_promo, columns = ['indiv_id', 'nb_promo'])
df_promo.sort('nb_promo', ascending = False ,inplace = True)
print len(df_promo[df_promo['nb_promo'] >= 10])
print df_promo[0:10]

# Aggregate and look at nb of promotions per day and day of week
ls_index_dow = df_prices.index.dayofweek
# days = ['MON','TUE','WED','THU','FRI','SAT','SUN']
ls_ls_promo_days, ls_ls_promo_dow = [], []
ls_ls_peak_days, ls_ls_peak_dow = [], []
ls_promo_ids = df_promo['indiv_id'][df_promo['nb_promo'] >= 10]
for indiv_id in ls_promo_ids:
  ls_indiv_promo = [x for x in dict_promo[indiv_id] if x[0] < 0]
  ls_indiv_peaks = [x for x in dict_promo[indiv_id] if x[0] > 0]
  ls_promo_days = [day for price_cut, ls_days in ls_indiv_promo for day in ls_days]
  ls_promo_dow = [ls_index_dow[day] for day in ls_promo_days]
  ls_peak_days = [day for price_cut, ls_days in ls_indiv_peaks for day in ls_days]
  ls_peak_dow = [ls_index_dow[day] for day in ls_peak_days]
  ls_ls_promo_days.append(ls_promo_days)
  ls_ls_promo_dow.append(ls_promo_dow)
  ls_ls_peak_days.append(ls_peak_days)
  ls_ls_peak_dow.append(ls_peak_dow)

ls_all_promo_days = [x for ls_x in ls_ls_promo_days for x in ls_x]
ls_all_promo_dow = [x for ls_x in ls_ls_promo_dow for x in ls_x]
ls_all_peak_days = [x for ls_x in ls_ls_peak_days for x in ls_x]
ls_all_peak_dow = [x for ls_x in ls_ls_peak_dow for x in ls_x]

print '\nPromo price per day of week'
print pd.Series(ls_all_promo_dow).value_counts()
print '\nPeak price per day of week'
print pd.Series(ls_all_peak_dow).value_counts()

print '\nPromo price per date'
print pd.Series(ls_all_promo_days).value_counts()[0:10]
print '\nPeak price per date'
print pd.Series(ls_all_peak_days).value_counts()[0:10]

# Dataframes dow
ls_se_peak_dow = [pd.Series(ls_peak_dow).value_counts() for ls_peak_dow in ls_ls_peak_dow]
df_peak_dow = pd.DataFrame(ls_se_peak_dow, index = ls_promo_ids)
df_peak_dow.fillna(0, inplace = True)

ls_se_promo_dow = [pd.Series(ls_promo_dow).value_counts() for ls_promo_dow in ls_ls_promo_dow]
df_promo_dow = pd.DataFrame(ls_se_promo_dow, index = ls_promo_ids)
df_promo_dow.fillna(0, inplace = True)

# Graph: one station: MOVE AND DO IT FOR 20-30
# clearly get just a subset of sales for now... make for flexible (copy error correction?)
indiv_id = '22600004'
ax = df_prices[indiv_id].plot()
ls_indiv_promo = [x for x in dict_promo[indiv_id] if x[0] < 0]
ls_indiv_peaks = [x for x in dict_promo[indiv_id] if x[0] > 0]
for price_cut, ls_days in ls_indiv_promo:
  ax.axvline(x=df_prices.index[ls_days[0]], linewidth=1, color='g')
for price_cut, ls_days in ls_indiv_peaks:
  ax.axvline(x=df_prices.index[ls_days[0]], linewidth=1, color='r')
plt.show()
