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

print 'Stations that should almost certainly be excluded:',\
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
ls_all_promo_days, ls_all_promo_dow = [], []
for indiv_id in df_promo['indiv_id'][df_promo['nb_promo'] > 20]:
  ls_indiv_promo = [x for x in dict_promo[indiv_id] if x[0] < 0]
  # check days of week where sales
  ls_promo_days = [day for price_cut, ls_days in ls_indiv_promo for day in ls_days]
  ls_all_promo_days += ls_promo_days
  ls_index_dow = df_prices.index.dayofweek
  # days = ['MON','TUE','WED','THU','FRI','SAT','SUN']
  ls_promo_dow = [ls_index_dow[day] for day in ls_promo_days]
  ls_all_promo_dow += ls_promo_dow
print pd.Series(ls_all_promo_dow).value_counts()
print pd.Series(ls_all_promo_days).value_counts()[0:10]

# Graph: one station: MOVE AND DO IT FOR 20-30
# clearly get just a subset of sales for now... make for flexible (copy error correction?)
indiv_id = '22600004'
ax = df_prices[indiv_id].plot()
ls_indiv_promo = [x for x in dict_promo[indiv_id] if x[0] < 0]
for price_cut, ls_days in ls_indiv_promo:
  ax.axvline(x=df_prices.index[ls_days[0]], linewidth=1, color='r')
plt.show()

# ###########
# DEPRECATED
# ###########

## REMINDER: USE OF PANEL DATA
## select station 10000001 (df object)
#pd_panel_data_master['10000001'] 
## select all station at 1st period (df object)
#pd_panel_data_master.major_xs(pd_panel_data_master.major_axis[0]) 
##tranpose (items: brand, price)
#pd_df_first_period = pd_panel_data_master.major_xs(pd_panel_data_master.major_axis[0]).T 
## selects all TOTAL prices in 1st period
#pd_df_first_period[pd_df_first_period['brand']=='TOTAL']['price']
## average TOTAL price in 1st period
#np.mean(pd_df_first_period[pd_df_first_period['brand']=='TOTAL']['price'])
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
#
#pd_df_price = pd_pd_master.minor_xs('price')
#pd_df_price_total = pd_pd_master.minor_xs('price')[pd_pd_master.minor_xs('brand') == 'TOTAL']
#pd_df_mean_comp = pd.concat([pd_df_price.mean(1),
#                             pd_df_price_total.mean(1)],
#                            keys = ['All', 'Total'] , axis = 1)
#pd_df_mean_comp_2 = pd_df_price_total.mean(1) - pd_df_price.mean(1)

## ANALYSIS OF PRICES AT GLOBAL LEVEL (DEPRECATED)
#master_np_prices = np.array(master_price['diesel_price'], dtype = np.float64)
#master_np_prices_chges = master_np_prices[:,:-1] - master_np_prices[:,1:]
#ar_non_nan = np.sum((~np.isnan(master_np_prices_chges)), axis = 0)
#ar_nb_chges = np.sum((~np.isnan(master_np_prices_chges)) &\
#                     (master_np_prices_chges!=0), axis = 0)
#ar_nb_pos_chges = np.sum((master_np_prices_chges > 0), axis = 0)
#ar_nb_neg_chges = np.sum((master_np_prices_chges < 0), axis = 0)
#ar_pos_chges = np.ma.masked_less_equal(master_np_prices_chges, 0).filled(np.nan)
#ar_avg_pos_chges = scipy.stats.nanmean(pos_master_np_prices_chges, axis = 0)
#ar_neg_chges = np.ma.masked_greater_equal(master_np_prices_chges, 0).filled(np.nan)
#ar_avg_neg_chges = scipy.stats.nanmean(ar_master_np_neg_prices_chges, axis = 0)
#ar_nonzero_chges = np.ma.masked_equal(master_np_prices_chges, 0).filled(np.nan)
#ar_avg_nonzero_chges = scipy.stats.nanmean(ar_master_np_nonzero_prices_chges, axis = 0)
#ar_normal_chges = master_np_prices_chges[(np.abs(master_np_prices_chges) <= 0.1) &\
#                                         (master_np_prices_chges != 0)]
#ar_extreme_chges = master_np_prices_chges[(np.abs(master_np_prices_chges) > 0.1)]
#print 'Percentage of abnormal changes',\
#      float(len(ar_extreme_chges))/(len(ar_normal_chges) + len(ar_extreme_chges))
### TOO BIG => RESTRICT
##n, bins, patches = plt.hist(ar_normal_chges[0:100000], 50, normed=1, facecolor='g')
##plt.show()
##n, bins, patches = plt.hist(ar_extreme_chges, 50, normed=1, facecolor='g')
##plt.show()
### CAUTION: still 324 changes among which some very high (-0.6) 
##plt.step([i for i in range(300)], ar_avg_nonzero_chge[:300])
##plt.show()
