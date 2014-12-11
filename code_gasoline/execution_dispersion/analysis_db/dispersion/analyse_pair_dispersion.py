#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
from statsmodels.distributions.empirical_distribution import ECDF
from scipy.stats import ks_2samp

# ###################
# LOAD DATA
# ###################

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')

# LOAD DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv, 'df_cleaned_prices.csv'),
                          parse_dates = True)
df_prices_cl.set_index('date', inplace = True)

# LOAD DF INFO
df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_info_final.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str})
df_info.set_index('id_station', inplace = True)

# LOAD DF DISPERSION
print '\nLoad df_ppd'
ls_dtype_temp = ['id', 'ci_ardt_1', 'brand_0', 'brand_1', 'brand_2']
dict_dtype = dict([('%s_b' %x, str) for x in ls_dtype_temp] +\
                  [('%s_a' %x, str) for x in ls_dtype_temp])
df_ppd = pd.read_csv(os.path.join(path_dir_built_csv,
                     'df_pair_raw_price_dispersion.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# LOAD DF STATION STATS
print '\nLoad df_station_stats'
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# LOAD dict_std_brands (to exclude same group stations)
dict_brands = dec_json(os.path.join(path_dir_source,
                                    'data_other',
                                    'dict_brands.json'))
dict_std_brands = {v[0]: v for k, v in dict_brands.items()}

# ##################
# FILTER DATA
# ##################

# DROP PAIRS WITH INSUFFICIENT PRICE DATA (temp?)

print "Dropped pairs (insuff spread obs):",\
        len(df_ppd[(pd.isnull(df_ppd['avg_spread'])) | (df_ppd['nb_spread'] < 100)])
df_ppd = df_ppd[(~pd.isnull(df_ppd['avg_spread'])) & (df_ppd['nb_spread'] >= 100)]

ls_exclude_ids = df_station_stats.index[(df_station_stats['nb_chge'] < 10) |\
                                        (df_station_stats['pct_chge'] < 0.03)]
print "Dropped pairs (insuff price data):",\
        len(df_ppd[(df_ppd['id_a'].isin(ls_exclude_ids)) | (df_ppd['id_b'].isin(ls_exclude_ids))])
df_ppd = df_ppd[(~df_ppd['id_a'].isin(ls_exclude_ids)) & (~df_ppd['id_b'].isin(ls_exclude_ids))]

# EXCLUDE TOTAL ACCESS (temp)

ls_brand_fields = ['brand_0_a', 'brand_1_a', 'brand_2_a',
                   'brand_0_b', 'brand_1_b', 'brand_2_b']
for field in ls_brand_fields:
  df_ppd[field].fillna(u'', inplace = True)
df_ppd['all_brands'] = df_ppd.apply(\
                         lambda x: ','.join([x[brand_field] for brand_field\
                                               in ls_brand_fields if x[brand_field]]), axis = 1)
# group is in fact only normalized brand for now
df_ppd['groups_a'] = df_ppd.apply(\
                         lambda x: ','.join([dict_std_brands[x[brand_field]][1] for brand_field\
                                               in ls_brand_fields[:3] if x[brand_field]]), axis = 1)

df_ppd['groups_b'] = df_ppd.apply(\
                         lambda x: ','.join([dict_std_brands[x[brand_field]][1] for brand_field\
                                               in ls_brand_fields[3:] if x[brand_field]]), axis = 1)
# not equivalent for now because can be 'TOTAL' and 'TOTAL_ACCESS' => deprecate
df_ppd['sg_a'] = df_ppd.apply(lambda x: any([y in x['groups_a']\
                                               for y in x['groups_b'].split(',')]), axis = 1)
df_ppd['sg_b'] = df_ppd.apply(lambda x: any([y in x['groups_b']\
                                               for y in x['groups_a'].split(',')]), axis = 1)

print 'Nb pairs before dropping same group:', len(df_ppd)
df_ppd = df_ppd[(~df_ppd['sg_a']) & (~df_ppd['sg_b'])]
print 'Nb pairs after dropping same group:', len(df_ppd)

# STILL SUSPECT (Small number of rank reversals but long...)
ls_disp = ['id_a', 'id_b', 'groups_a', 'groups_b', 'nb_chges_a','nb_chges_b', 'pct_rr']
# df_ppd['rr<=5'] = df_ppd[['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5']].sum(axis = 1)
#print len(df_ppd[(df_ppd['rr>20'] > 0) & (df_ppd['nb_rr'] < 5)])
#print df_ppd[ls_disp][(df_ppd['rr>20'] > 0) & (df_ppd['nb_rr'] < 5)][0:10].to_string()
#df_ppd = df_ppd[~((df_ppd['rr>20'] > 0) & (df_ppd['nb_rr'] < 5))]
df_ppd['avg_rr_len'] = (df_ppd['nb_spread'] * df_ppd['pct_rr']) / df_ppd['nb_rr']
df_ppd['avg_rr_len'] = df_ppd['avg_rr_len'].replace(np.inf, np.nan)
df_ppd = df_ppd[(pd.isnull(df_ppd['avg_rr_len'])) | (df_ppd['avg_rr_len'] <= 15)]

# SEPARATE PAIRS WITH A TOTAL ACCESS

df_ppd_ta = df_ppd[df_ppd['all_brands'].str.contains('TOTAL_ACCESS')]
df_ppd_nota = df_ppd[~(df_ppd['all_brands'].str.contains('TOTAL_ACCESS'))]

# need to separate since change in brand tends to inflate pct_rr artificially
# todo: generalize to rule out significant chges in margin

# ##########
# STATS DESC
# ##########

pd.set_option('float_format', '{:,.2f}'.format)
diff_bound = 0.01

# Histogram of average spreads (abs value required)
hist_test = plt.hist(df_ppd['avg_spread'].abs().values,
                     bins = 100,
                     range = (0, 0.3))
plt.show()

print '\nRank reversal: All'
print df_ppd['pct_rr'].describe()

print '\nRank reversal: Total Access (TA)'
print df_ppd_ta['pct_rr'].describe()

print '\nRank reversal: All except TA'
print df_ppd_nota['pct_rr'].describe()

print '\nRank reversal: No differentiation, no TA'
print df_ppd_nota['pct_rr'][df_ppd_nota['avg_spread'].abs() <= diff_bound].describe()

print '\nRank reversal: Differentiation, no TA'
print df_ppd_nota['pct_rr'][df_ppd_nota['avg_spread'].abs() > diff_bound].describe()

# CAUTION: RESTRICTION TO NON TOTAL ACCESS
# df_ppd = df_ppd_nota

df_ppd_nodiff = df_ppd[np.abs(df_ppd['avg_spread']) <= diff_bound]
df_ppd_diff = df_ppd[np.abs(df_ppd['avg_spread']) > diff_bound]
ls_ppd_names = ['All', 'No differentation', 'Differentiation']

zero = np.float64(1e-10)

for ppd_name, df_ppd_temp in zip(ls_ppd_names, [df_ppd, df_ppd_nodiff, df_ppd_diff]):
  print '\n', ppd_name
  print "\nNb pairs", len(df_ppd_temp)
  
  print "Of which no rank rank reversals",\
           len(df_ppd_temp['pct_rr'][df_ppd_temp['pct_rr'] <= zero])
  
  # RR & SPREAD VS DISTANCE + PER TYPE OF BRAND
  #hist_test = plt.hist(df_ppd_nodiff['pct_rr'][~pd.isnull(df_ppd_nodiff['pct_rr'])], bins = 50)
  df_all = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] <= 3)]
  df_close = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] <= 1)]
  df_far = df_ppd_temp[(~pd.isnull(df_ppd_temp['pct_rr'])) & (df_ppd_temp['distance'] > 1)]
  
  # Plot ECDF of rank reversals: close vs. far
  ecdf = ECDF(df_all['pct_rr'])
  ecdf_close = ECDF(df_close['pct_rr'])
  ecdf_far = ECDF(df_far['pct_rr'])
  x = np.linspace(min(df_all['pct_rr']), max(df_all['pct_rr']), num=100)
  y = ecdf(x)
  y_close = ecdf_close(x)
  y_far = ecdf_far(x)
  plt.rcParams['figure.figsize'] = 8, 6
  ax = plt.subplot()
  ax.step(x, y_close, label = r'$d_{ij} \leq 1km$')
  ax.step(x, y_far, label = r'$1km < d_{ij} \leq 3km$')
  plt.title(ppd_name)
  plt.legend()
  plt.tight_layout()
  plt.show()
  
  print '\nK-S test of equality of rank reversal distributions'
  print ks_2samp(df_close['pct_rr'], df_far['pct_rr'])
  # one side test not implemented in python ? (not in scipy at least)
  
  print '\nNb of pairs', len(df_all['pct_rr'])
  print 'Nb of pairs w/ short distance', len(df_close['pct_rr'])
  print 'Nb of pairs w/ longer distance', len(df_far['pct_rr'])
  
  #print '\nPair types representation among all pairs, close pairs, far pairs'
  #for df_temp, name_df in zip([df_all, df_close, df_far], ['All', 'Close', 'Far']):
  #  print '\n%s' %name_df, len(df_temp), 'pairs'
  #  for pair_type in np.unique(df_temp['pair_type']):
  #    print "{:20} {:>4.2f}".\
  #            format(pair_type, len(df_temp[df_temp['pair_type'] == pair_type]) /\
  #                     float(len(df_temp)))
  
# RR VS. TOTAL ACCESS / RR DURATION
## Find suspect rank reversal
#print 'Station with max length rank reversal:', np.argmax(df_ppd['max_len_rr'])

# INSPECT OUTLIERS
len(df_ppd[(df_ppd['avg_spread'].abs() > 0.01) & (df_ppd['pct_rr']> 0.4)])
ls_disp = ['id_a', 'id_b', 'groups_a', 'groups_b', 'nb_chges_a','nb_chges_b', 'pct_rr', 'nb_rr']
print df_ppd[ls_disp][(df_ppd['avg_spread'].abs() > 0.01) &\
                      (df_ppd['pct_rr']> 0.4)].to_string()

# todo: filter pairs on frequency of changes (todo everywhere incl. price cleaning)
# todo: filter chge of price policy: df_prices_ttc[['63000013','63000019']].plot()

## ####################
## DF PAIR PD TEMPORAL
## ####################
#
#km_bound = 3
#diff_bound = 0.02
#
## todo: iterate with various  (high value: no cleaning of prices)
#
## DF PAIR PRICE DISPERSION
#ls_ppd = []
#ls_ar_rrs = []
#ls_rr_lengths = []
#for (indiv_id, comp_id), distance in ls_tuple_competitors:
#  if distance <= km_bound: 
#    se_prices_1 = df_prices[indiv_id]
#    se_prices_2 = df_prices[comp_id]
#    avg_spread = (se_prices_2 - se_prices_1).mean()
#    if np.abs(avg_spread) > diff_bound:
#      #se_prices_1 = df_price_cl[indiv_id]
#      #se_prices_2 = df_price_cl[comp_id]
#      se_prices_1 = df_prices[indiv_id]
#      se_prices_2 = df_prices[comp_id]
#    ls_comp_pd = get_pair_price_dispersion(se_prices_1.as_matrix(),
#                                           se_prices_2.as_matrix(), light = False)
#    ls_comp_chges = get_stats_two_firm_price_chges(se_prices_1.as_matrix(),
#                                                   se_prices_2.as_matrix())
#    ls_ppd.append([indiv_id, comp_id, distance] +\
#                  ls_comp_pd[0][:9] + [avg_spread] + ls_comp_pd[0][10:]+\
#                  get_ls_standardized_frequency(ls_comp_pd[3][0]) +\
#                  ls_comp_chges[:-2])
#    ls_ar_rrs.append(ls_comp_pd[2][1])
#    ls_rr_lengths += ls_comp_pd[3][0]

## All, Total Access, No Total Access
#ls_ar_rrs_ta, ls_ar_rrs_nota = [], []
#for ar_rrs, ls_pair_ppd in zip(ls_ar_rrs, ls_ppd): 
#  if (df_brands['brand_1_e'][ls_pair_ppd[0]] == 'TOTAL_ACCESS') or\
#     (df_brands['brand_1_e'][ls_pair_ppd[1]] == 'TOTAL_ACCESS'):
#    ls_ar_rrs_ta.append(ar_rrs)
#  else:
#    ls_ar_rrs_nota.append(ar_rrs)
#
## Stations with low differentiation and not Total Access
#ls_ar_rrs_nodiff = [] 
#for ar_rrs, ls_pair_ppd in zip(ls_ar_rrs, ls_ppd):
#  if (not df_brands['brand_1_e'][ls_pair_ppd[0]] == 'TOTAL_ACCESS') &\
#     (not df_brands['brand_1_e'][ls_pair_ppd[1]] == 'TOTAL_ACCESS') &\
#     (np.abs(ls_pair_ppd[12]) <= diff_bound): # CHANGE !?!
#    ls_ar_rrs_nodiff.append(ar_rrs)
# 
#ls_df_rrs_su = []
#for ls_ar_rrs_temp in [ls_ar_rrs, ls_ar_rrs_ta, ls_ar_rrs_nota, ls_ar_rrs_nodiff]:
#  ls_dates = [pd.to_datetime(date) for date in master_price['dates']]
#  df_rrs_temp = pd.DataFrame(ls_ar_rrs_temp, columns = ls_dates)
#  se_nb_valid = df_rrs_temp.apply(lambda x: (~pd.isnull(x)).sum())
#  se_nb_rr    = df_rrs_temp.apply(lambda x: (np.abs(x) > zero_threshold).sum())
#  se_avg_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero_threshold]).mean())
#  se_std_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero_threshold]).std())
#  se_med_rr   = df_rrs_temp.apply(lambda x: np.abs(x[np.abs(x) > zero_threshold]).median())
#  df_rrs_su_temp = pd.DataFrame({'se_nb_valid' : se_nb_valid,
#                                 'se_nb_rr'    : se_nb_rr,
#                                 'se_avg_rr'   : se_avg_rr,
#                                 'se_std_rr'   : se_std_rr,
#                                 'se_med_rr'   : se_med_rr})
#  df_rrs_su_temp['pct_rr'] = df_rrs_su_temp['se_nb_rr'] / df_rrs_su_temp['se_nb_valid']
#  ls_df_rrs_su.append(df_rrs_su_temp) 
#
## Merge: to be improved? (more dataframes potentially?)
#df_rrs_su_all = pd.merge(ls_df_rrs_su[0], ls_df_rrs_su[1],\
#                         right_index = True, left_index = True, suffixes=('', '_ta'))
#df_rrs_su_all = pd.merge(df_rrs_su_all, ls_df_rrs_su[2],\
#                         right_index = True, left_index = True, suffixes=('', '_nota'))
#df_rrs_su_all = pd.merge(df_rrs_su_all, ls_df_rrs_su[3],\
#                         right_index = True, left_index = True, suffixes=('', '_nodiff'))
#
#df_rrs_su_all[df_rrs_su_all['pct_rr_nota'] == np.inf] = np.nan
#print '\n', df_rrs_su_all['pct_rr_nota'].describe()
#print 'argmax', df_rrs_su_all['pct_rr_nota'].argmax()
#
#df_rrs_su_all[df_rrs_su_all['pct_rr_nodiff'] == np.inf] = np.nan
#print '\n', df_rrs_su_all['pct_rr_nodiff'].describe()
#
#plt.rcParams['figure.figsize'] = 16, 6
#ax = df_rrs_su_all[['pct_rr', 'pct_rr_ta', 'pct_rr_nota', 'pct_rr_nodiff']].plot()
#handles, labels = ax.get_legend_handles_labels()
#labels = ['All', 'Total Access', 'All but Total Access', 'No differentiation']
#ax.legend(handles, labels)
#plt.tight_layout()
#plt.show()
#
## Price obs: stats descs + graph observations (investigate price cleaning too)
#
## Check very close prices (Output to folder: graph + map (Google?))
## todo: check if same result with average spread small
#df_ppd['pair_type'][(df_ppd['pct_same_price'] > 0.5) &\
#                    (df_ppd['brand_2_e_1'] != df_ppd['brand_2_e_2'])].value_counts()
#df_ppd[['id_1', 'id_2', 'pair_type']][(df_ppd['pct_same_price'] > 0.5) &\
#                                      (df_ppd['brand_2_e_1'] != df_ppd['brand_2_e_2'])][0:10]
## Set size of plot
#ax = df_prices[['1500007', '1500001']].plot()
#handles, labels = ax.get_legend_handles_labels()
#ax.legend(handles, [df_brands.ix[indiv_id]['brand_2_e'] for indiv_id in labels])
#plt.title(master_price['dict_info']['1500007']['city'])
#plt.show()
#
## pd.set_option('display.max_columns', 500)
#
## Check leader follower
## todo: check if can add follow 1 follow 2 and sim (?)
## todo: make more systematic and output graphs with relevant info + maps
## todo: static dispersion but sim changes... more or less same trend (work on variations?)
#df_ppd[(df_ppd['brand_2_e_1'] != df_ppd['brand_2_e_2']) &\
#       (df_ppd['nb_1_fol'] / df_ppd[['nb_chges_1', 'nb_chges_2']].min(axis=1) > 0.5)]
#
## todo: add same brand pair var to make lighter + get rid of/signal abnormal obs (rigid prices)
#
## Examine support through spread
#
## todo: add order (always do more expensive less cheaper...)
## todo: need to round diff before value count
#ls_rows_spread = []
#for count, row in df_ppd.iterrows():
#  id_1, id_2 = row['id_1'], row['id_2']
#  se_spread = df_prices[id_1] - df_prices[id_2]
#  se_spread = se_spread.round(3) # no price has more than 3 digits
#  ls_rows_spread.append([id_1, id_2, se_spread.value_counts()])
#
##for id_1, id_2, se_vc in ls_rows_spread:
##  if se_vc.max() / float(se_vc.sum()) > 0.5:
##    print '\n', id_1, id_2
##    print se_vc.iloc[0:min(len(se_vc, 5)]
#
## DEPRECATED
#
## #######################################
## PAIR PRICE DISPERSION: NORMALIZED PRICES
## ########################################
#
### COMPUTE PAIR PRICE DISPERSION
##start = time.clock()
##ls_pair_price_dispersion = []
##ls_pair_competitors = []
##for ((indiv_id_1, indiv_id_2), distance) in ls_tuple_competitors:
##  # could check presence btw...
##  indiv_ind_1 = master_price['ids'].index(indiv_id_1)
##  indiv_ind_2 = master_price['ids'].index(indiv_id_2)
##  if distance < km_bound:
##    ls_pair_competitors.append(((indiv_id_1, indiv_id_2), distance))
##    ar_price_1 = master_np_prices[indiv_ind_1]
##    ar_price_2 = master_np_prices[indiv_ind_2]
##    ar_diff = ar_price_1 - ar_price_2
##    ar_price_1_norm = ar_price_1 - ar_diff[~np.isnan(ar_diff)].mean()
##    ls_pair_price_dispersion.append(get_pair_price_dispersion(ar_price_1_norm,
##                                                              ar_price_2,
##                                                              light = False))
##print 'Pair price dispersion:', time.clock() - start
##
##def get_plot_normalized(ar_price_1, ar_price2):
##  # TODO: see if orient towards pandas or not
##  ar_diff = ar_price_1 - ar_price_2
##  ar_price_1_norm = ar_price_1 - ar_diff[~np.isnan(ar_diff)].mean()
##  plt.plot(ar_price_1_norm)
##  plt.plot(ar_price_2)
##  plt.plot(ar_price_1)
##  plt.show()
##  return
##
### DF PAIR PD STATS
##ls_ppd_for_df = [elt[0] for elt in ls_pair_price_dispersion]
##ls_columns = ['avg_abs_spread', 'avg_spread', 'std_spread', 'nb_days_spread',
##              'percent_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr', 'nb_rr_conservative']
##df_ppd = pd.DataFrame(ls_ppd_for_df, columns = ls_columns)
##ls_max_len_rr = [np.max(elt[3][0]) if elt[3][0] else 0 for elt in ls_pair_price_dispersion]
##df_ppd['max_len_rr'] = ls_max_len_rr
##df_ppd['id_1'] = [comp[0][0] for comp in ls_pair_competitors]
##df_ppd['id_2'] = [comp[0][1] for comp in ls_pair_competitors]
##
##df_brands = df_brands.rename(columns={'id_2': 'id_1'})
##df_ppd_brands = pd.merge(df_ppd, df_brands, on='id_1')
##df_brands = df_brands.rename(columns={'id_1': 'id_2'})
##df_ppd_brands = pd.merge(df_ppd_brands, df_brands, on='id_2', suffixes=('_1', '_2'))
##
##df_ppd_brands = df_ppd_brands.rename(columns={'nb_rr_conservative': 'nb_rr'})
##
##plt.hist(np.array(df_ppd_brands['avg_abs_spread'][~pd.isnull(df_ppd_brands['avg_abs_spread'])]), bins = 100)
##plt.hist(np.array(df_ppd_brands['max_len_rr'][~pd.isnull(df_ppd_brands['max_len_rr'])]), bins = 100)
##plt.hist(np.array(df_ppd_brands['nb_rr'][~pd.isnull(df_ppd_brands['nb_rr'])]), bins = 100)
##
#### Change in price policy => high avg_abs_spread with low nb_rr => clear cut: exlude!
###print df_ppd_brands[ls_view_1][df_ppd_brands['avg_abs_spread'] > 0.03].to_string()
##print df_ppd_brands[ls_view_1][(df_ppd_brands['avg_abs_spread'] < 0.02) & \
##                               (df_ppd_brands['nb_rr'] > 30)].to_string()
##get_plot_normalized(np.array(df_price['95190001']), np.array(df_price['95500005']))
