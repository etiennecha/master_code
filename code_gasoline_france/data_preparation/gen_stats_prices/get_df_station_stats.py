#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built,
                                  u'data_csv')
path_dir_built_json = os.path.join(path_dir_built,
                                   u'data_json')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ###############
# LOAD DF PRICES
# ###############

df_prices = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices.set_index('date', inplace = True)
df_chges = df_prices - df_prices.shift(1)

# todo: refactoring?
ls_ls_prices = [list(df_prices[col].values) for col in df_prices.columns]
ls_ls_price_durations = get_price_durations(ls_ls_prices)
ls_ls_price_variations = get_price_variations(ls_ls_price_durations)

# ################
# BUILD DF DIGITS
# ################

# Stations using 2 or 3 digits after decimal point and frequency of last digit
ls_rows_last_digit = []
for col in df_prices.columns:
  ar_prices_cent = df_prices[col][~pd.isnull(df_prices[col])].values * 100
  if len(ar_prices_cent) > 0:
    dummy_two_digits = 1
    if any(ar_prices_cent != ar_prices_cent.astype(int).astype(float)):
      dummy_two_digits = 0
      # need to avoid digits after decimal point
      ar_prices_cent = ar_prices_cent * 10 # no more cents actually
    ar_prices_temp = ar_prices_cent.astype(int).astype(str)
    ls_last_digit = []
    for i in range(10):
      ar_temp = ar_prices_temp[np.core.defchararray.startswith(ar_prices_temp,
                                                               '{:d}'.format(i),
                                                               start = -1)]
      ls_last_digit.append(len(ar_temp))
    row_last_digit = [dummy_two_digits] + ls_last_digit
  else:
    row_last_digit = [None for i in range(11)]
  ls_rows_last_digit.append(row_last_digit)

df_digits = pd.DataFrame(ls_rows_last_digit,
                         columns = ['2d'] + ['ld_%s' %i for i in range(10)],
                         index = df_prices.columns)

# STATS DES

print u'Nb stations w/ 2 digits: {:,.0f}'.format(len(df_digits[df_digits['2d'] == 1]))
print u'Nb stations w/ 3 digits: {:,.0f}'.format(len(df_digits[df_digits['2d'] == 0]))

print u'\nFrequency of last digit (3 digit prices):'
df_digits_3d = df_digits[df_digits['2d'] == 0]
se_su_3d_ld = df_digits_3d[['ld_%s' %i for i in range(10)]].sum()
se_su_3d_ld_freq = se_su_3d_ld / se_su_3d_ld.sum()
print se_su_3d_ld_freq.to_string()

print u'\nFrequency of last digit (2 digit prices):'
df_digits_2d = df_digits[df_digits['2d'] == 1]
se_su_2d_ld = df_digits_2d[['ld_%s' %i for i in range(10)]].sum()
se_su_2d_ld_freq = se_su_2d_ld / se_su_2d_ld.sum()
print se_su_2d_ld_freq.to_string()

# ################
# BUILD DF CHANGES
# ################

# Price changes: Value of price changes
zero = np.float64(1e-10)
ls_rows_chges = []
for col in df_chges.columns:
  # todo: check what to do with missing values(exclude first not to miss any change?)
  se_pos_price_chge = df_chges[col][df_chges[col] >  zero]
  se_neg_price_chge = df_chges[col][df_chges[col] < -zero]
  ls_rows_chges.append([df_chges[col].count(), # nb valid (no nan) price chges
                        df_chges[col][df_chges[col].abs() < zero].count(), # nb no chge
                        se_pos_price_chge.count(),
                        se_neg_price_chge.count(),
                        se_pos_price_chge.median(),
                        se_pos_price_chge.mean(),
                        se_neg_price_chge.median(),
                        se_neg_price_chge.mean()])
ls_columns = ['nb_valid', 'nb_no_chge',
              'nb_pos_chge', 'nb_neg_chge',
              'med_pos_chge', 'avg_pos_chge', 'med_neg_chge', 'avg_neg_chge']
df_chges_indiv_su = pd.DataFrame(ls_rows_chges,
                                 index = df_chges.columns,
                                 columns = ls_columns)

df_chges_indiv_su['nb_chge'] = df_chges_indiv_su['nb_pos_chge'] +\
                                 df_chges_indiv_su['nb_neg_chge']
df_chges_indiv_su['pct_chge'] = df_chges_indiv_su['nb_chge'] /\
                                  df_chges_indiv_su['nb_valid']

# #################
# BUILD DF RIGIDITY
# #################

# Price rigidity: Frequency of prices changes
ls_rigidity_rows = []
for indiv_id, ls_price_durations in zip(list(df_prices.columns),
                                        ls_ls_price_durations):
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
df_rigidity = pd.DataFrame(ls_rigidity_rows, df_prices.columns, ls_columns)

# STATS DES

# One length > 60: probably two stations reconciled?

print "\nNb w/ less than 10 prices (drop?): {:,.0f}".\
         format(len(df_rigidity[(pd.isnull(df_rigidity['nb_prices_used'])) |\
                   (df_rigidity['nb_prices_used'] <= 10)]))

ls_ids_nb_prices_drop = df_rigidity.index[(pd.isnull(df_rigidity['nb_prices_used'])) |\
                                          (df_rigidity['nb_prices_used'] <= 10)]

df_rigidity = df_rigidity[(~pd.isnull(df_rigidity['nb_prices_used'])) &\
                          (df_rigidity['nb_prices_used'] > 10)]

print u'\nOverview of price rigidity (nb days, incl. censored):'
print u'\n', df_rigidity.describe()

print u'\nOverview of price rigidity (nb days, no censored):'
print u'\n', df_rigidity[df_rigidity['max_length'] < 60].describe()

print u'\nNb of stations with censored prices (nb days): {:,.0f}'.\
        format(len(df_rigidity[df_rigidity['max_length'] >= 60]))

# #################
# BUILD DF DAY CHGE
# #################

# Price change: day of week (normalization by days observed)
ar_ind_dow = df_prices.index.dayofweek # seems faster to store it first
ls_chge_dow_rows = []
for ls_price_durations in ls_ls_price_durations:
  ls_indiv_chge_days = []
  ls_indiv_days = []
  for price, ls_price_days in ls_price_durations:
    if not np.isnan(price):
      ls_indiv_chge_days.append(ls_price_days[0])
      ls_indiv_days += ls_price_days
  ls_indiv_chge_dows = [ar_ind_dow[i] for i in ls_indiv_chge_days]
  ls_indiv_dows = [ar_ind_dow[i] for i in ls_indiv_days]
  se_indiv_chge_dows = pd.Series(ls_indiv_chge_dows).value_counts()
  se_indiv_days = pd.Series(ls_indiv_dows).value_counts()
  se_indiv_chge_dows_norm = se_indiv_chge_dows / se_indiv_days.astype(float)
  dow_argmax = se_indiv_chge_dows_norm.argmax()
  dow_max_pct = se_indiv_chge_dows_norm.max() / float(se_indiv_chge_dows_norm.sum())
  ls_chge_dow_rows.append((dow_argmax, dow_max_pct))
df_chge_dow = pd.DataFrame(ls_chge_dow_rows,
                           index = list(df_prices.columns),
                           columns = ['dow_max', 'pct_dow_max'])

dict_replace_dow = dict(zip(range(7), ['MO','TU','WE','TH','FR','SA','SU']))
df_chge_dow['dow_max'] =\
   df_chge_dow['dow_max'].apply(lambda x: dict_replace_dow.get(x, None))

# Inspect results (check process, rename days?)
print u'\nOverview of days of week where changes most frequent:'
print df_chge_dow['dow_max'].value_counts()

# ########################
# BUILD DF PEAKS AND DROPS
# ########################

# Promotions: look for successive inverse price cuts at station level
ls_ls_promo = get_sales(ls_ls_price_variations, 4)

# Add to rows: nb of promotions per day of week
ls_index_dow = df_prices.index.dayofweek
# days = ['MON','TUE','WED','THU','FRI','SAT','SUN']
ls_ls_promo_days, ls_ls_promo_dow = [], []
ls_ls_peak_days, ls_ls_peak_dow = [], []
ls_rows_promo = []
for ls_promo in ls_ls_promo:
  # promo (negative chge)
  ls_indiv_promo = [x for x in ls_promo if x[0] < 0]
  ls_promo_days = [day for price_cut, ls_days in ls_indiv_promo for day in ls_days]
  ls_ls_promo_days.append(ls_promo_days)
  ls_promo_dow = [ls_index_dow[day] for day in ls_promo_days]
  ls_ls_promo_dow.append(ls_promo_dow)
  # peak (positive chge)
  ls_indiv_peaks = [x for x in ls_promo if x[0] > 0]
  ls_peak_days = [day for price_cut, ls_days in ls_indiv_peaks for day in ls_days]
  ls_ls_peak_days.append(ls_peak_days)
  ls_peak_dow = [ls_index_dow[day] for day in ls_peak_days]
  ls_ls_peak_dow.append(ls_peak_dow)
  ls_rows_promo.append([len(ls_promo)]+\
                       [ls_promo_dow.count(i) for i in range(7)]+\
                       [ls_peak_dow.count(i) for i in range(7)])

df_promo = pd.DataFrame(ls_rows_promo,
                        index = list(df_prices.columns),
                        columns = ['nb_promo'] +\
                                  ['pm_{:d}'.format(i) for i in range(7)]+\
                                  ['pk_{:d}'.format(i) for i in range(7)])

df_promo.sort('nb_promo', ascending = False ,inplace = True)
print '\nNb stations with over 10 promo', len(df_promo[df_promo['nb_promo'] >= 10])
print '\n', df_promo[0:10].to_string()

# STATS DES

ls_all_promo_days = [x for ls_x in ls_ls_promo_days for x in ls_x]
ls_all_promo_dow = [x for ls_x in ls_ls_promo_dow for x in ls_x]
ls_all_peak_days = [x for ls_x in ls_ls_peak_days for x in ls_x]
ls_all_peak_dow = [x for ls_x in ls_ls_peak_dow for x in ls_x]

print '\nPromo price per day of week:'
print pd.Series(ls_all_promo_dow).value_counts()

print '\nPeak price per day of week:'
print pd.Series(ls_all_peak_dow).value_counts()

# todo: get real dates... not day in

print '\nPromo price per date:'
print pd.Series(ls_all_promo_days).value_counts()[0:10]

print '\nPeak price per date:'
print pd.Series(ls_all_peak_days).value_counts()[0:10]

# Dataframes dow
ls_se_peak_dow = [pd.Series(ls_peak_dow).value_counts() for ls_peak_dow in ls_ls_peak_dow]
df_peak_dow = pd.DataFrame(ls_se_peak_dow, index = list(df_prices.columns))
df_peak_dow.fillna(0, inplace = True)

ls_se_promo_dow = [pd.Series(ls_promo_dow).value_counts() for ls_promo_dow in ls_ls_promo_dow]
df_promo_dow = pd.DataFrame(ls_se_promo_dow, index = list(df_prices.columns))
df_promo_dow.fillna(0, inplace = True)

# Big price cuts (nb per day)
ls_rows_cuts = []
for day in df_chges.index:
	ls_rows_cuts.append([len(df_chges.ix[day][df_chges.ix[day] < -0.04]),
	                     len(df_chges.ix[day][df_chges.ix[day] < -0.05]),
	                     len(df_chges.ix[day][df_chges.ix[day] < -0.10])])

ls_columns = ['nb_promo_04', 'nb_promo_05', 'nb_promo_10']
df_cuts_su = pd.DataFrame(ls_rows_cuts,
                          index = list(df_chges.index),
                          columns = ls_columns)

# inspect cuts

print u'\nOverview cuts of 0.04 at least:'
print df_cuts_su['nb_promo_04'].describe()

print u'\nDay with max nb of price cuts:'
print df_cuts_su[df_cuts_su['nb_promo_04'] == df_cuts_su['nb_promo_04'].max()]
# impact of government intervention

print u'\nExamples of cut on this day:'
print df_chges.ix['2012-08-31'][df_chges.ix['2012-08-31'] < - 0.04][0:10]

# df_prices[['1500007', '1500001', '1500004']]['2012-08-21':'2012-09-11'].plot()
# plt.show()
## todo: check stations with df_info

# #########################
# MERGE AND OUTPUT TO CSV
# #########################

df_station_stats = pd.merge(df_chges_indiv_su,
                            df_rigidity,
                            how = 'left',
                            right_index = True,
                            left_index = True)

df_station_stats = pd.merge(df_chges_indiv_su,
                            df_chge_dow,
                            how = 'left',
                            right_index = True,
                            left_index = True)

# quasi no info (nb_chge: min five) or doubtful info (pct_chge: min once a month)

print u'\nNb stations with too little changes: {:,.0f}'.\
         format(len(df_station_stats[~((df_station_stats['nb_chge'] >= 5) &\
                                       (df_station_stats['pct_chge'] >= 0.03))]))

print u'\nOverview of valid price series:'
print df_station_stats[(df_station_stats['nb_chge'] >= 5) &\
                       (df_station_stats['pct_chge'] >= 0.03)].describe()

# add dummy 2 digit after decimal point prices
df_station_stats['2d'] = df_digits['2d']
# temp
df_station_stats['nb_promo'] = df_promo['nb_promo']

df_station_stats.to_csv(os.path.join(path_dir_built_csv,
                                     'df_station_stats.csv'),
                         index_label = 'id_station',
                         float_format= '%.4f',
                         encoding = 'utf-8')

df_promo.to_csv(os.path.join(path_dir_built_csv,
                             'df_station_promo.csv'),
                index_label = 'id_station',
                encoding = 'utf-8')

# ###############
# MOVE / DISPOSE?
# ###############

## Graph: one station: MOVE AND DO IT FOR 20-30
## clearly get just a subset of sales for now... make for flexible (copy error correction?)
#indiv_id = '22600004'
#ax = df_prices[indiv_id].plot()
#ls_indiv_promo = [x for x in dict_promo[indiv_id] if x[0] < 0]
#ls_indiv_peaks = [x for x in dict_promo[indiv_id] if x[0] > 0]
#for price_cut, ls_days in ls_indiv_promo:
#  ax.axvline(x=df_prices.index[ls_days[0]], linewidth=1, color='g')
#for price_cut, ls_days in ls_indiv_peaks:
#  ax.axvline(x=df_prices.index[ls_days[0]], linewidth=1, color='r')
#plt.show()

### Graphs: competitors (subset)
##print ls_ls_competitors[master_price['ids'].index('22600004')]
##ax = df_prices[['22600006', '22600001', '22600004']][0:100].plot()
##for i, dow in enumerate(ar_ind_dow[0:100]):
##  if dow == 5:
##    ax.axvline(x=df_prices.index[i], lw=0.8, ls='--' ,color='k')
##
##pd.options.display.float_format = '{:,.3f}'.format
##print df_prices[['22600006', '22600001', '22600004']][0:30].to_string()
### Looks like Leclerc only has 2 digit prices vs. 3 for others?
### Super U uses 5 and 9 to be cheaper / more expensive but not noticed?
##
### Leclerc (*4) relatively far from Carrefour Market (*1) and Super U (*6)
### Yet Leclerc has a pattern of prices closer to Carrefour Market: seems prices higher on week ends
### Close to N164: people going to Brest or whatever: not local consumers so higher price?
### Check prices of ESSO on N164 a bit further vs. other ESSO
### Check prices of Leclerc vs. Leclerc around etc
