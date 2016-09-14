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

pd.set_option('float_format', '{:,.1f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.1f}'.format(x)

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

# SPREAD IN CENT
for spread_var in ['mean_spread',
                   'mean_abs_spread', 'abs_mean_spread',
                   'std_spread', 'std_abs_spread',
                   'mc_spread', 'smc_spread']:
  df_pairs[spread_var] = df_pairs[spread_var] * 100

for pct_var in ['pct_to_same_maxu', 'pct_to_same_maxl',
                'pct_to_same_min', 'pct_same', 'pct_rr']:
  df_pairs[pct_var] = df_pairs[pct_var] * 100

# RESTRICT CATEGORY

df_pairs_all = df_pairs.copy()
df_pairs = df_pairs[df_pairs['cat'] == 'no_mc'].copy()

## robustness check with idf: 1 km max
#ls_dense_dpts = [75, 92, 93, 94]
#df_pairs = df_pairs[~((((df_pairs['dpt_1'].isin(ls_dense_dpts)) |\
#                        (df_pairs['dpt_2'].isin(ls_dense_dpts))) &\
#                       (df_pairs['distance'] > 1)))]

## robustness check keep closest competitor
#df_pairs.sort(['id_1', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_1', inplace = True, take_last = False)
## could also collect closest for each id_2 and filter further
## - id_1 can have closer competitor as an id_2
## - duplicates in id_2 (that can be solved also but drops too much)
#df_pairs.sort(['id_2', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_2', inplace = True, take_last = False)
## - too many drops: end ids always listed as id_2 disappear... etc.

### robustness check: rr>20 == 0
#df_pairs = df_pairs[(df_pairs['rr>20'] == 0)]
#df_pairs = df_pairs[(df_pairs['mean_rr_len'] <= 21)]

# REFINE TYPES
# - distinguish discounter among non sup
# - interested in discounter vs discounter and discounter vs. sup
# based on brand_last
ls_discounter = ['ELF', 'ESSO_EXPRESS', 'TOTAL_ACCESS']
for i in (1, 2):
  df_pairs.loc[df_pairs['brand_last_{:d}'.format(i)].isin(ls_discounter),
               'group_type_last_{:d}'.format(i)] = 'DIS'
  df_pairs.loc[df_pairs['brand_last_{:d}'.format(i)].isin(ls_discounter),
               'group_type_{:d}'.format(i)] = 'DIS'
df_info.loc[df_info['brand_last'].isin(ls_discounter),
             'group_type_last'] = 'DIS'
df_info.loc[df_info['brand_last'].isin(ls_discounter),
             'group_type'] = 'DIS'

# COMPETITORS VS. SAME GROUP

df_pair_same =\
  df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
           (df_pairs['group_last_1'] == df_pairs['group_last_2'])].copy()
df_pair_comp =\
  df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
           (df_pairs['group_last_1'] != df_pairs['group_last_2'])].copy()

# DIFFERENTIATED VS. NON DIFFERENTIATED

diff_bound = 1.0
df_pair_same_nd = df_pair_same[df_pair_same['mean_spread'].abs() <= diff_bound]
df_pair_same_d  = df_pair_same[df_pair_same['mean_spread'].abs() > diff_bound]
df_pair_comp_nd = df_pair_comp[df_pair_comp['mean_spread'].abs() <= diff_bound]
df_pair_comp_d  = df_pair_comp[df_pair_comp['mean_spread'].abs() > diff_bound]

# CREATE VARS FOR LEADERSHIP ANALYSIS (MOVE?)
df_pair_comp['pct_1_lead'] = df_pair_comp['nb_1_lead'].astype(float) /\
  df_pair_comp[['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same']].sum(1)
df_pair_comp['pct_2_lead'] = df_pair_comp['nb_2_lead'].astype(float) /\
  df_pair_comp[['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same']].sum(1)
df_pair_comp['pct_sim_same'] = df_pair_comp['nb_chge_to_same'].astype(float) /\
  df_pair_comp[['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same']].sum(1)

# COMP SUP VS. NON SUP

df_pair_sup = df_pair_comp[(df_pair_comp['group_type_1'] == 'SUP') &\
                           (df_pair_comp['group_type_2'] == 'SUP')]
df_pair_nsup = df_pair_comp[(df_pair_comp['group_type_1'] != 'SUP') &\
                            (df_pair_comp['group_type_2'] != 'SUP')]
df_pair_sup_nd = df_pair_sup[(df_pair_sup['mean_spread'].abs() <= diff_bound)]
df_pair_nsup_nd = df_pair_nsup[(df_pair_nsup['mean_spread'].abs() <= diff_bound)]

# ALTERNATIVE

dict_pair_all = {'any' : df_pair_comp}

dict_pair_all['sup'] = df_pair_comp[(df_pair_comp['group_type_1'] == 'SUP') &\
                                   (df_pair_comp['group_type_2'] == 'SUP')]

dict_pair_all['oil_ind'] =\
    df_pair_comp[(df_pair_comp['group_type_1'].isin(['OIL', 'INDEPENDENT'])) &\
                 (df_pair_comp['group_type_2'].isin(['OIL', 'INDEPENDENT']))]

dict_pair_all['dis'] = df_pair_comp[(df_pair_comp['group_type_1'] == 'DIS') &\
                                   (df_pair_comp['group_type_2'] == 'DIS')]

dict_pair_all['sup_dis'] = df_pair_comp[((df_pair_comp['group_type_1'] == 'SUP') &\
                                       (df_pair_comp['group_type_2'] == 'DIS')) |
                                      ((df_pair_comp['group_type_1'] == 'DIS') &\
                                       (df_pair_comp['group_type_2'] == 'SUP'))]

dict_pair_nd = {}
for df_type_title, df_type_pairs in dict_pair_all.items():
  dict_pair_nd[df_type_title] =\
      df_type_pairs[df_type_pairs['abs_mean_spread'] <= diff_bound].copy()


# LISTS FOR DISPLAY

lsd = ['id_1', 'id_2', 'distance', 'group_last_1', 'group_last_2']
lsd_rr = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

lsd_spread = ['id_1', 'id_2', 'distance',
              'mc_spread', 'smc_spread',
              'freq_mc_spread', 'freq_smc_spread',
              'abs_mean_spread', 'mean_abs_spread', 'pct_rr', 'pct_same']

zero = 1e-10
ls_pctiles = [0.05, 0.10, 0.25, 0.5, 0.75, 0.90, 0.95]

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

## #############################
## ALIGNED PRICES AND LEADERSHIP
## #############################
#
### HEATMAP: PCT SAME VS PCT RR
##heatmap, xedges, yedges = np.histogram2d(df_pair_comp_nd['pct_same'].values,
##                                         df_pair_comp_nd['pct_rr'].values,
##                                         bins=30)
##extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
##plt.imshow(heatmap.T, extent=extent, origin = 'lower', aspect = 'auto')
##plt.show()
##
### HEATMAP: PCT RR VS MEAN SPREAD (rounding issues)
##heatmap, xedges, yedges = np.histogram2d(df_pair_comp_nd['abs_mean_spread'].values,
##                                         df_pair_comp_nd['pct_rr'].values,
##                                         bins=30)
##extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
##plt.imshow(heatmap.T, extent=extent, origin = 'lower', aspect = 'auto')
##plt.show()
#
## ALIGNED PRICES
#print()
#print(u'Nb aligned prices i.e. pct_same >= 0.33',\
#      len(df_pairs[(df_pairs['pct_same'] >= 0.33)])) # todo: harmonize pct i.e. * 100
## Pct same vs. mean_spread: make MSE appear? (i.e. close prices but no steady gap...)
#
#print()
#print(u'Overview aligned prices i.e. pct_same >= 0.33:')
#print(df_pairs[(df_pairs['pct_same'] >= 0.33)][['pct_rr', 'nb_rr']].describe())
#
## STANDARD SPREAD (ALLOW GENERALIZATION OF LEADERSHIP?)
#print()
#print('Inspect abs mc_spread == 0.010')
#print(df_pairs[(df_pairs['mc_spread'] == 0.010) | (df_pairs['mc_spread'] == -0.010)]
#              [['distance', 'abs_mean_spread',
#                'pct_rr', 'freq_mc_spread', 'pct_same']].describe())
#
##print(df_pair_comp[df_pair_comp['pct_same'] >= 1/3.0]\
##        [lsd + ['nb_1_lead', 'nb_2_lead', 'nb_chge_to_same',
##                'pct_1_lead', 'pct_2_lead', 'pct_sim_same']][0:10].to_string())
#
## NO LEADER
#nl_ps_lim = 33/100.0
#nl_pct_lead_lim = 10/100.0
#df_nl = df_pair_comp[(df_pair_comp['pct_same'] >= nl_ps_lim) &\
#                     (df_pair_comp['pct_1_lead'] <= 10/100.0) &\
#                     (df_pair_comp['pct_2_lead'] <= 10/100.0) ].copy()
#se_nl_chains = pd.concat([df_nl['brand_last_1'], df_nl['brand_last_2']]).value_counts()
#print()
#print(u'Chains: pair with high similar price pct but no leader')
#print(se_nl_chains.to_string())
#
#lsdnl = ['distance', 'id_1', 'id_2', 'brand_last_1', 'brand_last_2',
#        'pct_same', 'pct_1_lead', 'pct_2_lead', 'pct_sim_same']
#
#print()
#print(df_nl[lsdnl][0:20].to_string())
#
## LEADERSHIP?
## Restrictive def:
## - pct_to_same_max: max lead or simulatenously change to same
## - pct_to_same_min: min lead
#
#ps_lim =      33/100.0
#ptsmaxu_lim = 95/100.0
#ptsmaxl_lim = 25/100.0
#ptsmin_lim =  05/100.0
#
#df_leadership =\
#  df_pair_comp[(df_pair_comp['pct_same'] >= ps_lim) &\
#               (df_pair_comp['pct_to_same_maxl'] >= (3 * df_pair_comp['pct_to_same_min'])) &\
#               (df_pair_comp['pct_to_same_maxl'] > 0.10)].copy()
#
#df_leadership['leader_brand'] = df_leadership['brand_last_1']
#df_leadership.loc[df_leadership['nb_2_lead'] > df_leadership['nb_1_lead'],
#                  'leader_brand'] = df_leadership['brand_last_2']
#
#df_leadership['follower_brand'] = df_leadership['brand_last_1']
#df_leadership.loc[df_leadership['nb_2_lead'] < df_leadership['nb_1_lead'],
#                  'leader_brand'] = df_leadership['brand_last_2']
#
#lsdl = ['distance', 'id_1', 'id_2', 'brand_last_1', 'brand_last_2',
#        'pct_same', 'pct_1_lead', 'pct_2_lead', 'pct_sim_same',
#        'leader_brand', 'follower_brand']
#
#print()
#print(u'Overview of leadership')
#print(df_leadership[lsdl][0:20].to_string())
#
#print()
#print('Chain of leaders')
#print(df_leadership['leader_brand'].value_counts()[0:10])
#
#print()
#print('Chain of followers')
#print(df_leadership['follower_brand'].value_counts()[0:10])
#
## Question: how often is a leader a follower (and vice versa?)
#
## UNSURE
#
#df_unsure =\
#  df_pair_comp[(df_pair_comp['pct_same'] >= ps_lim) &\
#               (df_pair_comp['pct_to_same_maxl'] <= (3 * df_pair_comp['pct_to_same_min'])) &\
#               (df_pair_comp['pct_to_same_maxl'] > 0.10)].copy()

# #############################
# OIL / INDEPENDENT PAIRS
# #############################

# Inspect high pct_same among oil / independent pairs

lsdt = ['id_1', 'id_2',
        'brand_0_1', 'brand_last_1',
        'brand_0_2', 'brand_last_2',
        'pct_same', 'pct_rr', 'distance',
        'pct_sim_same', 'pct_1_lead', 'pct_2_lead']

lsdt2 = ['id_1', 'id_2',
         'brand_0_1', 'brand_last_1',
         'brand_0_2', 'brand_last_2',
         'pct_same', 'distance',
         'freq_mc_spread', 'mc_spread', 'freq_smc_spread', 'smc_spread']

dict_pair_nd['oil_ind'].plot(kind = 'scatter', x = 'pct_rr', y  = 'pct_same')
plt.show()

# pct_same >= 0.2 is relatively high: not suspect => 0.3 ... rather leadership story
print(dict_pair_nd['oil_ind'][dict_pair_nd['oil_ind']['pct_same'] >= 30.0][lsdt].to_string())

# can generalize to same spread (todo: create graphs and stress period of same spread)
print(dict_pair_all['oil_ind'][dict_pair_all['oil_ind']['freq_mc_spread'] >= 30][lsdt2].to_string())

# #############################
# SUP PAIRS
# #############################

#dict_pair_nd['sup']['pct_same'].describe()

## Inspect high
#print(dict_pair_nd['sup'][dict_pair_nd['sup']['pct_same'] >= 0.9][lsdt].to_string())

#df_pair_sup = dict_pair_nd['sup'].copy()
#
### add leadership (could do it for all df, not always meaningful of course)
##df_pair_sup['leader_brand'] = df_pair_sup['brand_last_1']
##df_pair_sup.loc[df_pair_sup['nb_2_lead'] > df_pair_sup['nb_1_lead'],
##                  'leader_brand'] = df_pair_sup['brand_last_2']
##df_pair_sup['follower_brand'] = df_pair_sup['brand_last_1']
##df_pair_sup.loc[df_pair_sup['nb_2_lead'] < df_pair_sup['nb_1_lead'],
##                  'leader_brand'] = df_pair_sup['brand_last_2']
#
#df_pair_ss = dict_pair_nd['sup'][dict_pair_nd['sup']['pct_same'] >= 0.33].copy()
#df_pair_ss.sort('pct_sim_same', ascending = True, inplace = True)

df_pair_ss = dict_pair_nd['any'].copy()
df_pair_ss.sort('pct_sim_same', ascending = True, inplace = True)

ls_ss_ids = list(set(df_pair_ss[['id_1', 'id_2']].values.flatten()))
se_ss_brands = df_info.ix[ls_ss_ids]['brand_last'].value_counts()
se_brands = df_info['brand_last'].value_counts()
se_ss_share = se_ss_brands  / se_brands[se_brands > 10]
se_ss_share = se_ss_share[~se_ss_share.isnull()] * 100
se_ss_share.sort(ascending = False)

print()
print(u'Percent stations involved in close price comp (% of stations of same brand)')
print(se_ss_share.to_string())

df_pair_ss_ld = df_pair_ss[(df_pair_ss['pct_sim_same'] <= 60) &\
                           (df_pair_ss['pct_to_same_maxl'] >= (3 * df_pair_ss['pct_to_same_min']))]

# DEFINE LEADER SET
ls_leader_ids = df_pair_ss_ld[df_pair_ss_ld['nb_2_lead'] >\
                                df_pair_ss_ld['nb_1_lead']]['id_2'].values.tolist() +\
                df_pair_ss_ld[df_pair_ss_ld['nb_1_lead'] >\
                                df_pair_ss_ld['nb_2_lead']]['id_1'].values.tolist()
ls_leader_ids = list(set(ls_leader_ids))

# DEFINE FOLLOWER SET
ls_follower_ids = df_pair_ss_ld[df_pair_ss_ld['nb_2_lead'] >\
                                  df_pair_ss_ld['nb_1_lead']]['id_1'].values.tolist() +\
                  df_pair_ss_ld[df_pair_ss_ld['nb_1_lead'] >\
                                  df_pair_ss_ld['nb_2_lead']]['id_2'].values.tolist()
ls_follower_ids = list(set(ls_follower_ids))

# DEFINE BOTH
# stores which are both leader and follower
ls_both_ids = set(ls_follower_ids).intersection(set(ls_leader_ids))

# DEFINE UNSURE
df_pair_ss_uns = df_pair_ss[(df_pair_ss['pct_sim_same'] <= 50) &\
                            (df_pair_ss['pct_to_same_maxl'] < (3 * df_pair_ss['pct_to_same_min']))]
ls_ss_uns_ids = list(set(df_pair_ss_uns[['id_1', 'id_2']].values.flatten()))

for role, ls_role_ids in [['leader', ls_leader_ids],
                          ['follower', ls_follower_ids],
                          ['both', ls_both_ids],
                          ['unsure', ls_ss_uns_ids]]:
  print()
  print(u'Overview {:s} by brand'.format(role))
  se_role_nb = df_info.ix[ls_role_ids]['brand_last'].value_counts()
  se_role_share = se_role_nb  / se_brands * 100
  df_role = pd.concat([se_brands,
                       se_role_nb,
                       se_role_share],
                      axis = 1,
                      keys = ['nb_tot', 'nb_{:s}'.format(role), 'pct'])
  df_role.sort('pct', ascending = False, inplace = True)
  print(df_role[(df_role['nb_{:s}'.format(role)] >= 5) |\
                (df_role['nb_tot'] >= 100)].to_string())
