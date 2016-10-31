#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built, u'data_json')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_built_dis = os.path.join(path_data,
                                  u'data_gasoline',
                                  u'data_built',
                                  u'data_dispersion')
path_dir_built_dis_csv = os.path.join(path_dir_built_dis, u'data_csv')
path_dir_built_dis_json = os.path.join(path_dir_built_dis, u'data_json')
path_dir_built_dis_graphs = os.path.join(path_dir_built_dis, 'data_graphs')

pd.set_option('float_format', '{:,.1f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.1f}'.format(x)

from pylab import *
rcParams['figure.figsize'] = 16, 6

## french date format
#import locale
#locale.setlocale(locale.LC_ALL, 'fra_fra')

dir_graphs = 'bw'

# ################
# LOAD DATA
# ################

# DF INFO
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

# DF STATION STATS
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# DF MARGIN CHGE
df_margin_chge = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_margin_chge.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_margin_chge.set_index('id_station', inplace = True)

# DF COMP
df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_comp.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str})
df_comp.set_index('id_station', inplace = True)

# CLOSE STATIONS
dict_ls_close = dec_json(os.path.join(path_dir_built_json,
                                      'dict_ls_close.json'))

# DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

# FILTER DATA
# exclude stations with insufficient (quality) price data
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'Corse')].index)))
#df_info = df_info.ix[ls_keep_ids]
#df_station_stats = df_station_stats.ix[ls_keep_ids]
#df_prices_ttc = df_prices_ttc[ls_keep_ids]
#df_prices_ht = df_prices_ht[ls_keep_ids]
#df_prices_cl = df_prices_cl[ls_keep_ids]

ls_drop_ids = list(set(df_prices_ttc.columns).difference(set(ls_keep_ids)))
df_prices_ttc[ls_drop_ids] = np.nan
df_prices_ht[ls_drop_ids] = np.nan
# highway stations may not be in df_prices_cl (no pbm here)
ls_drop_ids_nhw =\
  list(set(ls_drop_ids).difference(set(df_info[df_info['highway'] == 1].index)))
df_prices_cl[ls_drop_ids_nhw] = np.nan

# DF PAIRS

ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                    'df_pair_final.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# basic pair filter (insufficient obs, biased rr measure)
df_pairs = df_pairs[(~((df_pairs['nb_spread'] < 90) &\
                       (df_pairs['nb_ctd_both'] < 90))) &
                    (~(df_pairs['nrr_max'] > 60))]

## filter on distance: 5 km
#df_pairs = df_pairs[df_pairs['distance'] <= 5]

# LISTS FOR DISPLAY

lsd = ['id_1', 'id_2', 'distance', 'group_last_1', 'group_last_2']
lsd_rr = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

lsd_spread = ['id_1', 'id_2', 'distance',
              'mc_spread', 'smc_spread',
              'freq_mc_spread', 'freq_smc_spread',
              'abs_mean_spread', 'mean_abs_spread', 'pct_rr', 'pct_same']

zero = 1e-10
ls_pctiles = [0.05, 0.10, 0.25, 0.5, 0.75, 0.90, 0.95]

# SPREAD IN CENT
for spread_var in ['mean_spread',
                   'mean_abs_spread', 'abs_mean_spread',
                   'std_spread', 'std_abs_spread',
                   'mc_spread', 'smc_spread']:
  df_pairs[spread_var] = df_pairs[spread_var] * 100

for pct_var in ['pct_to_same_maxu', 'pct_to_same_maxl',
                'pct_to_same_min', 'pct_same', 'pct_rr']:
  df_pairs[pct_var] = df_pairs[pct_var] * 100

# REFINE GROUP TYPE
# beginning: ELF + need to use future info
# (todo: add TA with no detected margin chge?)
df_info.loc[((df_info['brand_0'] == 'ELF') |\
             (df_info['brand_last'] == 'ESSO_EXPRESS')),
            'group_type'] = 'DIS'
df_info.loc[(df_info['brand_last'].isin(['ELF',
                                         'ESSO_EXPRESS',
                                         'TOTAL_ACCESS'])),
            'group_type_last'] = 'DIS'
# Further GMS refining
ls_hypers = ['AUCHAN', 'CARREFOUR', 'GEANT', 'LECLERC', 'CORA',
             'INTERMARCHE', 'SYSTEMEU']
df_info.loc[(df_info['brand_0'].isin(ls_hypers)),
            'group_type'] = 'HYP'
df_info.loc[(df_info['brand_last'].isin(ls_hypers)),
            'group_type_last'] = 'HYP'

# DEAL WITH OTHER
str_be = 'last' # '_0'
df_info['brand'] = df_info['brand_{:s}'.format(str_be)]
df_info['group_type'] = df_info['group_type_{:s}'.format(str_be)]

df_info['nb_brand'] = df_info[['brand', 'group_type']].groupby('brand')\
                                      .transform(len)

for group_type in df_info['group_type'].unique():
  df_info.loc[(df_info['nb_brand'] <= 50) &\
             (df_info['group_type'] == group_type),
             'brand'] = 'OTHER_{:s}'.format(group_type)

# temp: overwrite ELF for table (fragile but else overwritten due to nb_brand)
df_info.loc[df_info['brand'] == 'OTHER_DIS', 'brand'] = 'TOTAL_ACCESS'

# temp: set small OIL & IND to INDEPENDANT (group_type too => for agg stat on remainder)
df_info.loc[df_info['brand'] == 'OTHER_OIL', 'group_type'] = 'IND'
df_info.loc[df_info['brand'] == 'OTHER_OIL', 'brand'] = 'INDEPENDANT'
df_info.loc[df_info['brand'] == 'OTHER_IND', 'brand'] = 'INDEPENDANT'

# #############
# PREPARE DATA
# #############

# RESTRICT CATEGORY: PRICES AND MARGIN CHGE
df_pairs_all = df_pairs.copy()
price_cat = 'no_mc' # 'residuals_no_mc'
print(u'Prices used : {:s}'.format(price_cat))
df_pairs = df_pairs[df_pairs['cat'] == price_cat].copy()

## robustness check with idf: 1 km max
#ls_dense_dpts = [75, 92, 93, 94]
#df_pairs = df_pairs[~((((df_pairs['dpt_1'].isin(ls_dense_dpts)) |\
#                        (df_pairs['dpt_2'].isin(ls_dense_dpts))) &\
#                       (df_pairs['distance'] > 1)))]

## robustness check keep closest competitor
#df_pairs.sort(['id_1', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_1', inplace = True, take_last = False)
# could also collect closest for each id_2 and filter further
# - id_1 can have closer competitor as an id_2
# - duplicates in id_2 (that can be solved also but drops too much)
#df_pairs.sort(['id_2', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_2', inplace = True, take_last = False)
## - too many drops: end ids always listed as id_2 disappear... etc.

### robustness check: rr>20 == 0
#df_pairs = df_pairs[(df_pairs['rr>20'] == 0)]
#df_pairs = df_pairs[(df_pairs['mean_rr_len'] <= 21)]

# COMPETITORS VS. SAME GROUP
df_pair_same =\
  df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
           (df_pairs['group_last_1'] == df_pairs['group_last_2'])].copy()
df_pair_comp =\
  df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
           (df_pairs['group_last_1'] != df_pairs['group_last_2'])].copy()

# DICT OF DFS
# pairs without spread restriction
# (keep pairs with group change in any)
dict_pair_comp = {'any' : df_pair_comp}
for k in df_pair_comp['pair_type'].unique():
  dict_pair_comp[k] = df_pair_comp[df_pair_comp['pair_type'] == k]
# add sup sup&dis cat
dict_pair_comp['sup&dis'] = pd.concat([dict_pair_comp['sup'],
                                       dict_pair_comp['dis'],
                                       dict_pair_comp['sup_dis']])
# low spread pairs
diff_bound = 1.0
dict_pair_comp_nd = {}
for df_temp_title, df_temp in dict_pair_comp.items():
  dict_pair_comp_nd[df_temp_title] =\
      df_temp[df_temp['abs_mean_spread'] <= diff_bound]

# ########################
# OVERVIEW SPREADS
# ########################

# Based on spread value and frequency:
# Should use "ordered" abs spread values... (desc not very meaningfull this way)

# No differentiation:
# - mc_spread == 0 & freq_mc_spread high (high pct_same) : Betrand or Collusion
# - mc_spread st positive and smc_spread std negative
# - could add tmc_spread to capture cases w/ 3 prices

df_null_mc_spread = df_pair_comp[df_pair_comp['mc_spread'].abs() < zero]

print()
print('Overview most common spread 0 ({:d}):'.format(len(df_null_mc_spread)))
print(df_null_mc_spread[lsd_spread].describe(percentiles=ls_pctiles).to_string())

df_opp_spreads = df_pair_comp[((df_pair_comp['mc_spread'] > zero) &\
                               (df_pair_comp['smc_spread'] < -zero)) |
                              ((df_pair_comp['mc_spread'] <- zero) &\
                               (df_pair_comp['smc_spread'] > zero))]

print()
print('Overview opp sign spreads ({:d}):'.format(len(df_opp_spreads)))
print(df_opp_spreads[lsd_spread].describe(percentiles=ls_pctiles).to_string())

df_opp_spreads_alt =\
  df_pair_comp[(((df_pair_comp['mc_spread']*df_pair_comp['smc_spread']) < -zero) &\
                (df_pair_comp['tmc_spread'].abs() < zero)) |\
               (((df_pair_comp['smc_spread']*df_pair_comp['tmc_spread']) <- zero) &\
                (df_pair_comp['mc_spread'].abs() < zero)) |\
               (((df_pair_comp['mc_spread']*df_pair_comp['tmc_spread']) <- zero) &\
                (df_pair_comp['smc_spread'].abs() < zero))]

print()
print('Overview null and opp sign spreads ({:d}):'.format(len(df_opp_spreads_alt)))
print(df_opp_spreads_alt[lsd_spread].describe(percentiles=ls_pctiles).to_string())

#print(df_null_opp_spreads[lsd_spread][0:20].to_string())

# Low differentiation
# - mc_spread or smc_spread == 0 and both high

df_low_diff_spreads= df_pair_comp[(df_pair_comp['mc_spread'].abs() < zero) |\
                                  (df_pair_comp['smc_spread'].abs() < zero)]

#print(df_low_diff_spreads['abs_mean_spread'].describe(percentiles = ls_pctiles))
#print(df_low_diff_spreads[df_low_diff_spreads['abs_mean_spread'] > 0.057]\
#                         [lsd_spread].to_string())
## Pricing of 93000009: pathological (check dup reconciliations?)

# High(er) differentiation
# - can require mc_spread and smc_spread to be of same sign

df_high_diff_spreads = df_pair_comp[((df_pair_comp['mc_spread'] > zero) &\
                                     (df_pair_comp['smc_spread'] > zero)) |
                                    ((df_pair_comp['mc_spread'] < -zero) &\
                                     (df_pair_comp['smc_spread'] < -zero))]

print()
print('Overview same sign spreads ({:d}):'.format(len(df_high_diff_spreads)))
print(df_high_diff_spreads[lsd_spread].describe(percentiles=ls_pctiles).to_string())

# ##############
# ALIGNED PRICES
# ##############

df_pairs = df_pair_comp[df_pair_comp['distance'] <= 5].copy()

print()
print(u'Nb aligned prices i.e. pct_same >= 33%:',\
      len(df_pairs[(df_pairs['pct_same'] >= 33.0)])) # todo: harmonize pct i.e. * 100

# todo: add distinction supermarkets vs. others
print()
print(u'Overview aligned prices i.e. pct_same >= 33%:')
print(df_pairs[(df_pairs['pct_same'] >= 33.0)][['pct_rr',
                                                'nb_rr',
                                                'pct_same']].describe())

# STANDARD SPREAD (ALLOW GENERALIZATION OF LEADERSHIP?)
print()
print('Inspect abs mc_spread == 1.0:')
print(df_pairs[(df_pairs['mc_spread'] == 1.0) | (df_pairs['mc_spread'] == -1.0)]
              [['distance', 'abs_mean_spread',
                'pct_rr', 'freq_mc_spread', 'pct_same']].describe())

# LEADERSHIP TEST
df_pairs['leader_pval'] = np.nan
df_pairs['leader_pval'] = df_pairs[(~df_pairs['nb_lead_1'].isnull()) &\
                                   (~df_pairs['nb_lead_2'].isnull())].apply(\
                            lambda x: scipy.stats.binom_test(x[['nb_lead_1',
                                                                'nb_lead_2']].values,
                                                             p = 0.5),
                            axis = 1)

## add a measure of whether this is significant (vs total nb of changes?)
## ... requires scipy 0.18 to test proba of success greater (or code it)
#df_pairs['same_pval'] = np.nan
#df_pairs['same_pval'] = df_pairs[(~df_pairs['nb_spread'].isnull())].apply(\
#                            lambda x: scipy.stats.binom_test(x['nb_same'],
#                                                             x['nb_spread'],
#                                                             p = 0.1,
#                                                             alternative = 'greater'),
#                            axis = 1)

lsd_ld = ['pct_same', 'nb_same', 'nb_chge_to_same',
          'nb_lead_1', 'nb_lead_2', 'leader_pval']

print()
print(u'Inspect leaders:')
print(df_pairs[lsd_ld][df_pairs['leader_pval'] <= 0.05][0:20].to_string())

print()
print(u'Types of pairs with leaders:')
print(df_pairs[df_pairs['leader_pval'] <= 0.05]['pair_type'].value_counts())

print()
print(u'Types of pairs with leaders (pct):')
print(df_pairs[df_pairs['leader_pval'] <= 0.05]['pair_type'].value_counts() /\
        df_pairs['pair_type'].value_counts()* 100)


print()
df_pairs['leader_brand'] = np.nan
df_pairs.loc[(df_pairs['leader_pval'] <= 0.05) &\
             (df_pairs['nb_lead_1'] > df_pairs['nb_lead_2']),
             'leader_brand'] = df_pairs['brand_last_1']
                      
df_pairs.loc[(df_pairs['leader_pval'] <= 0.05) &\
             (df_pairs['nb_lead_1'] < df_pairs['nb_lead_2']),
             'leader_brand'] = df_pairs['brand_last_2']

# todo: leader brand only of stations which have:
# - no leader
# - not engaged in tough competition

print()
print(u'Inspect leader brands')
print(df_pairs['leader_brand'].value_counts()[0:10])

## impose close price comp: pct_same 0.33 or 0.50

df_close_comp = df_pairs[(df_pairs['pct_same'] >= 30)].copy()

#df_close_comp = df_pairs[(df_pairs['pct_same'] >= 30) |\
#                         (df_pairs['leader_pval'] <= 0.05)].copy()
#df_close_comp = df_pairs[(df_pairs['abs_mean_spread'] <= 1.0) &\
#                         (df_pairs['pct_same'] >= 30)]

## check what is mutually exclusive

# absolute leader: leading, not led, not uncertain
# leader_led: leading, led
# leader_uncertain: leading, uncertain
# relative leader: leading

ls_close_comp = list(set(\
  df_close_comp['id_1'].values.tolist() +\
  df_close_comp['id_2'].values.tolist()))

ls_rel_leader = list(set(\
  df_close_comp['id_1'][(df_close_comp['leader_pval'] <= 0.05) &\
                        (df_pairs['nb_lead_1'] > df_pairs['nb_lead_2'])].values.tolist() +\
  df_close_comp['id_2'][(df_close_comp['leader_pval'] <= 0.05) &\
                        (df_pairs['nb_lead_1'] < df_pairs['nb_lead_2'])].values.tolist()))

ls_rel_led = list(set(\
  df_close_comp['id_1'][(df_close_comp['leader_pval'] <= 0.05) &\
                        (df_pairs['nb_lead_1'] < df_pairs['nb_lead_2'])].values.tolist() +\
  df_close_comp['id_2'][(df_close_comp['leader_pval'] <= 0.05) &\
                        (df_pairs['nb_lead_1'] > df_pairs['nb_lead_2'])].values.tolist()))

ls_rel_unc = list(set(\
  df_close_comp['id_1'][(df_close_comp['leader_pval'] > 0.05)].values.tolist() +\
  df_close_comp['id_2'][(df_close_comp['leader_pval'] > 0.05)].values.tolist()))

ls_abs_leader = list(set(ls_rel_leader).difference(set(ls_rel_led))\
                                       .difference(set(ls_rel_unc)))

ls_leader_led = list(set(ls_rel_leader).intersection(set(ls_rel_led)))

ls_leader_unc = list(set(ls_rel_leader).intersection(set(ls_rel_unc)))

# absolute led: led, not leading, not uncertain
# relative led: led

ls_abs_led = list(set(ls_rel_led).difference(set(ls_rel_leader))\
                                 .difference(set(ls_rel_unc)))

# absolute uncertain: uncertain, not leading, not led
# relative uncertain: uncertain

ls_abs_unc = list(set(ls_rel_unc).difference(set(ls_rel_leader))\
                                 .difference(set(ls_rel_led)))

# take into account fact that many total access are dropped (margin chge)
ls_drop_ids = df_margin_chge[df_margin_chge['value'].abs() >= 0.03].index
df_info = df_info[~df_info.index.isin(ls_drop_ids)]

ls_close_comp_su = [['close_comp', ls_close_comp],
                    ['rel_leader', ls_rel_leader],
                    ['abs_leader', ls_abs_leader],
                    ['rel_led', ls_rel_led],
                    ['abs_led', ls_abs_led],
                    ['rel_unc', ls_rel_unc],
                    ['abs_unc', ls_abs_unc]]
#                    ['leader_unc', ls_leader_unc]]

ls_station_ind_cols = ['group_type', 'brand']

ls_se_leader = []
for title_temp, ls_ids_temp in ls_close_comp_su:
  ls_se_leader.append(df_info.ix[ls_ids_temp]\
                                [ls_station_ind_cols].groupby(ls_station_ind_cols).agg(len))

df_leader_brands =\
  pd.concat([df_info[ls_station_ind_cols].groupby(ls_station_ind_cols).agg(len)] + ls_se_leader,
            axis = 1,
            keys = ['nb_stations'] + [x[0] for x in ls_close_comp_su])

#ls_se_leader = []
#for title_temp, ls_ids_temp in ls_close_comp_su:
#  ls_se_leader.append(df_info.ix[ls_ids_temp]['brand_last'].value_counts())
#
#df_leader_brands = pd.concat([df_info['brand_last'].value_counts()] + ls_se_leader,
#                             axis = 1,
#                             keys = ['nb_stations'] + [x[0] for x in ls_close_comp_su])

#df_leader_brands = df_leader_brands[df_leader_brands['nb_stations'] >= 30]
df_leader_brands = df_leader_brands.fillna(0)

df_leader_brands_pct =\
  df_leader_brands.apply(lambda x: x / df_leader_brands['nb_stations'] * 100)
df_leader_brands_pct['nb_stations'] = df_leader_brands['nb_stations']

df_leader_brands_pct.sort('nb_stations', ascending = False, inplace = True)

#df_leader_brands_pct = df_leader_brands_pct.sortlevel()
#print()
#print(df_leader_brands_pct.to_string())

# caution: need to be exhaustive...
ls_station_reind = [['OIL', 'TOTAL'],
                    ['OIL', 'ELAN'],
                    ['OIL', 'AGIP'],
                    ['OIL', 'BP'],
                    ['OIL', 'ESSO'],
                    ['IND', 'AVIA'],
                    ['IND', 'DYNEFF'],
                    ['IND', 'INDEPENDANT'],
                    ['DIS', 'TOTAL_ACCESS'],
                    ['DIS', 'ESSO_EXPRESS'],
                    ['HYP', 'CARREFOUR'],
                    ['HYP', 'AUCHAN'],
                    ['HYP', 'CORA'],
                    ['HYP', 'GEANT'],
                    ['HYP', 'INTERMARCHE'],
                    ['HYP', 'SYSTEMEU'],
                    ['HYP', 'LECLERC'],
                    ['SUP', 'CARREFOUR_MARKET'],
                    ['SUP', 'CARREFOUR_CONTACT'],
                    ['SUP', 'SIMPLY'],
                    ['SUP', 'CASINO'],
                    ['SUP', 'INTERMARCHE_CONTACT'],
                    ['SUP', 'OTHER_SUP']]

df_leader_brands_pct = df_leader_brands_pct.reindex([tuple(x) for x in ls_station_reind])
print(df_leader_brands_pct.to_string(float_format = '{:.0f}'.format))

# ##############
# GRAPHS
# ##############

df_prices = df_prices_ttc

## GRAHS: MATCHED PRICES (more robust but works only if no differentiation for now)
#
#pair_id_1, pair_id_2 = '1200003', '1200001'
#
#df_prices = df_prices_ttc.ix['2014-01-01':'2014-06-30'].copy()
#
#def plot_pair_matched_prices(pair_id_1, pair_id_2):
#  ls_sim_prices = get_stats_two_firm_same_prices(df_prices[pair_id_1].values,
#                                                 df_prices[pair_id_2].values)
#  #ax = df_prices[[pair_id_1, pair_id_2]].plot()
#  fig = plt.figure()
#  ax = fig.add_subplot(111)
#  l1 = ax.plot(df_prices.index,
#               df_prices[pair_id_1].values, lw = 1,
#               c = 'k', ls = '-', alpha = 0.4, zorder = 1, # lw = 1, marker = '+', markevery=5, #g
#               label = '{:s}'.format(df_info.ix[pair_id_1]['brand_last']))
#  l2 = ax.plot(df_prices.index,
#               df_prices[pair_id_2].values, lw = 1,
#               c = 'k', ls = '--', alpha = 1, zorder = 2, #b
#               label = '{:s}'.format(df_info.ix[pair_id_2]['brand_last']))
#  for day_ind in ls_sim_prices[1][0]:
#  	ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='k', alpha = 1, zorder = 1)
#  for day_ind in ls_sim_prices[1][1]:
#  	ax.axvline(x=df_prices.index[day_ind], lw=1, ls='-', c='k', alpha = 0.4, zorder = 2)
#  lns = l1 + l2
#  labs = [l.get_label() for l in lns]
#  ## id_2 is TA
#  #ax1.axvline(x = df_info_ta.ix[id_2]['pp_chge_date'], color = 'k', ls = '-')
#  ax.legend(lns, labs, loc=1)
#  ax.grid()
#  # Show ticks only on left and bottom axis, out of graph
#  ax.yaxis.set_ticks_position('left')
#  ax.xaxis.set_ticks_position('bottom')
#  ax.get_yaxis().set_tick_params(which='both', direction='out')
#  ax.get_xaxis().set_tick_params(which='both', direction='out')
#
#  str_ylabel = 'Price (euro/liter)'
#  plt.ylabel(str_ylabel)
#  fig.tight_layout()
#  #plt.show()
#  plt.savefig(os.path.join(path_dir_built_dis_graphs,
#                           dir_graphs,
#                           'example_leadership_{:s}_{:s}.png'.format(pair_id_1, pair_id_2)),
#              dpi = 200)
#  plt.close()
#
#plot_pair_matched_prices('1700004', '1120005')



## GRAPHS: FOLLOWED PRICE CHANGES (very sensitive)
#
#pair_id_1, pair_id_2 = '1500004', '1500006'
#
#def plot_pair_followed_price_chges(pair_id_1, pair_id_2, beg=0, end=1000):
#  ls_followed_chges = get_stats_two_firm_price_chges(df_prices[pair_id_1].values,
#                                                     df_prices[pair_id_2].values)
#  ax = df_prices[[pair_id_1, pair_id_2]][beg:end].plot()
#  for day_ind in ls_followed_chges[1][0]:
#    line_1 = ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='b')
#    line_1.set_dashes([4,2])
#  for day_ind in ls_followed_chges[1][1]:
#    line_2 = ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='g')
#    line_2.set_dashes([8,2])
#  plt.show()
#
#plot_pair_followed_price_chges('1500004', '1500006')

# #################
# EXAMINE LEADERS
# #################

# detect asymmetry in leadership
for i in (1, 2):
  df_pairs['nb_lead_d_{:d}'.format(i)] =\
      df_pairs['nb_lead_{:d}'.format(i)] - df_pairs['nb_lead_u_{:d}'.format(i)]

# Leclerc / Auchan leaders - Carrefour / Geant leg

# BUILD DF WHERE A = LEADER & B = OTHER (ALWAYS FOLLOWER HERE?)
df_leaders = df_pairs[((df_pairs['id_1'].isin(ls_abs_leader)) |
                       (df_pairs['id_2'].isin(ls_abs_leader))) &
                      (df_pairs['leader_pval'] <= 0.05) &\
                      (df_pairs['pct_same'] >= 30)].copy()

for var_name in ['id', 'dpt', 'reg', 'ci_ardt_1',
                 'brand_0', 'brand_last',
                 'group', 'group_last',
                 'group_type', 'group_type_last',
                 'nb_cheaper',
                 'nb_lead', 'nb_lead_u', 'nb_lead_d', 'nb_ctd',
                 'nb_chges', 'nb_fol']:
  df_leaders['{:s}_a'.format(var_name)] = df_leaders['{:s}_1'.format(var_name)]
  df_leaders['{:s}_b'.format(var_name)] = df_leaders['{:s}_2'.format(var_name)]
  df_leaders.loc[df_leaders['id_2'].isin(ls_abs_leader),
                 '{:s}_a'.format(var_name)] = df_leaders['{:s}_2'.format(var_name)]
  df_leaders.loc[df_leaders['id_2'].isin(ls_abs_leader),
                 '{:s}_b'.format(var_name)] = df_leaders['{:s}_1'.format(var_name)]
  if var_name != 'id':
    df_leaders.drop(['{:s}_1'.format(var_name), '{:s}_2'.format(var_name)],
                    axis = 1, inplace = True)
# also chge sign of mean_spread if order chged
df_leaders.loc[~df_leaders['id_1'].isin(ls_abs_leader),
               'mean_spread'] = -df_leaders['mean_spread']

## Check: long term compa by chain pair (do for all pairs)
#df_subc = df_leaders[['brand_last_a', 'brand_last_b', 'mean_spread']]\
#                    .groupby(['brand_last_a', 'brand_last_b'])\
#                    .agg('describe')['mean_spread'].unstack()
#df_subc.reset_index(inplace = True, drop = False)
#
#for br_a in ['LECLERC', 'AUCHAN', 'TOTAL_ACCESS']:
#  print()
#  print(df_subc[df_subc['brand_last_a'] == br_a].to_string())

df_leaders['asym_pval'] = np.nan
df_leaders['asym_pval'] = df_leaders[(~df_leaders['nb_lead_u_a'].isnull()) &\
                                     (~df_leaders['nb_lead_d_b'].isnull())].apply(\
                            lambda x: scipy.stats.binom_test(x[['nb_lead_u_a',
                                                                'nb_lead_d_b']].values,
                                                             p = 0.5),
                            axis = 1)

# For Leclerc
len(df_leaders[(df_leaders['brand_last_a'] == 'LECLERC') &\
               (df_leaders['asym_pval'] <= 0.05) &\
               (df_leaders['nb_lead_u_a'] < df_leaders['nb_lead_d_a'])])

len(df_leaders[(df_leaders['brand_last_a'] == 'LECLERC') &\
               (df_leaders['asym_pval'] <= 0.05) &\
               (df_leaders['nb_lead_u_a'] > df_leaders['nb_lead_d_a'])])

# if work with ld_abs_lead => todo: chge var name
# LECLERC leaders initiate more decreases than increases
# CARREFOUR led follow more decreases than increases

# ##################
# EXAMINE FOLLOWERS
# ##################

# BUILD DF WHERE A = LEADER & B = OTHER (ALWAYS FOLLOWER HERE?)
df_followers = df_pairs[((df_pairs['id_1'].isin(ls_abs_led)) |
                       (df_pairs['id_2'].isin(ls_abs_led))) &
                      (df_pairs['leader_pval'] <= 0.05) &\
                      (df_pairs['pct_same'] >= 30)].copy()

for var_name in ['id', 'dpt', 'reg', 'ci_ardt_1',
                 'brand_0', 'brand_last',
                 'group', 'group_last',
                 'group_type', 'group_type_last',
                 'nb_cheaper',
                 'nb_lead', 'nb_lead_u', 'nb_lead_d', 'nb_ctd',
                 'nb_chges', 'nb_fol']:
  df_followers['{:s}_a'.format(var_name)] = df_followers['{:s}_1'.format(var_name)]
  df_followers['{:s}_b'.format(var_name)] = df_followers['{:s}_2'.format(var_name)]
  df_followers.loc[df_followers['id_2'].isin(ls_abs_led),
                 '{:s}_a'.format(var_name)] = df_followers['{:s}_2'.format(var_name)]
  df_followers.loc[df_followers['id_2'].isin(ls_abs_led),
                 '{:s}_b'.format(var_name)] = df_followers['{:s}_1'.format(var_name)]
  if var_name != 'id':
    df_followers.drop(['{:s}_1'.format(var_name), '{:s}_2'.format(var_name)],
                    axis = 1, inplace = True)
# also chge sign of mean_spread if order chged
df_followers.loc[~df_followers['id_1'].isin(ls_abs_led),
               'mean_spread'] = -df_followers['mean_spread']

lsdl = ['id_a', 'id_b', 'brand_last_a', 'brand_last_b',
        'pct_same', 'leader_pval',
        'nb_lead_a', 'nb_lead_b',
        'nb_lead_u_a', 'nb_lead_d_a',
        'nb_lead_u_b', 'nb_lead_d_b',
        'nb_chge_to_same_u', 'nb_chge_to_same_d']

# caution: one gas station often led by several here...
