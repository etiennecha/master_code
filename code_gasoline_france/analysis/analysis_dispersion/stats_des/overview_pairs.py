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

## CLOSE STATIONS
#dict_ls_close = dec_json(os.path.join(path_dir_built_json,
#                                      'dict_ls_close.json'))

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

df_pbms = df_station_stats[(df_station_stats['pct_chge'] < 0.03) |\
                           (df_station_stats['nb_valid'] < 90)]
print(u'Nb with insufficient/pbmatic price data: {:d}'.format(len(df_pbms)))

df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'Corse')].index)))
df_prices_ht = df_prices_ht[ls_keep_ids]
df_prices_ttc = df_prices_ttc[ls_keep_ids]
df_info = df_info.ix[ls_keep_ids]
df_station_stats = df_station_stats.ix[ls_keep_ids]
df_comp = df_comp.ix[ls_keep_ids]

print(u'Nb of stations after all filters: {:d}'.format(len(df_info)))

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
dict_pair_comp_nd = {'any_s' : dict_pair_comp.copy()}
for diff_bound in [2.0, 1.0]:
  dict_pair_comp_nd['s<={:.0f}'.format(diff_bound)] = {}
  for df_temp_title, df_temp in dict_pair_comp.items():
    dict_pair_comp_nd['s<={:.0f}'.format(diff_bound)][df_temp_title] =\
        df_temp[df_temp['abs_mean_spread'] <= diff_bound].copy()

# #######################
# STATS DES BY TYPE
# #######################

print()
print(u'Overview of pair stats by gas station types:')

# Need to play on two criteria to produce tables of paper
# - diff_bound set to 0.01 and 0.02 (differentiation)
# - df_pairs['cat'] : 'no_mc' (raw _prices) and 'residuals_no_mc' (price residuals)

ls_var_desc = ['distance',
               'pct_rr', 'pct_same',
               'abs_mean_spread', 'std_spread',
               'freq_mc_spread', 'mean_rr_len']

ls_categories = ['any', 'oil&ind', 'sup&dis', 'sup', 'dis', 'sup_dis']

ls_loop_pair_disp = []
for str_diff_bound in ['any_s', 's<=2', 's<=1']:
  for str_category in ls_categories:
    ls_loop_pair_disp.append((u'{:s} - {:s}'.format(str_diff_bound, str_category),
                              dict_pair_comp_nd[str_diff_bound][str_category]))

#ls_loop_pair_disp = [('All', dict_pair_comp['any']),
#                     ('Oil&Ind', dict_pair_comp['oil&ind']),
#                     ('Sup&Dis', dict_pair_comp['sup&dis']),
#                     ('Sup', dict_pair_comp['sup']),
#                     ('Dis', dict_pair_comp['dis']),
#                     ('Sup_Dis', dict_pair_comp['sup_dis']),
#                     ('Nd All', dict_pair_comp_nd['any']),
#                     ('Nd Oil&Ind', dict_pair_comp_nd['oil&ind']),
#                     ('Nd Sup&Dis', dict_pair_comp_nd['sup&dis']),
#                     ('Nd Sup', dict_pair_comp_nd['sup']),
#                     ('Nd Dis', dict_pair_comp_nd['dis']),
#                     ('Nd Sup_Dis', dict_pair_comp_nd['sup_dis'])]

pd.set_option('float_format', '{:,.1f}'.format)
for dist_lim in [5, 3, 1]:
  print()
  print('Overview of pair dispersion w/ max distance {:.1f}'.format(dist_lim))
  for stat in ['mean', 'std']:
    print()
    print(stat)
    ls_se_desc, ls_nb_obs = [], []
    for title, df_pair_disp in ls_loop_pair_disp:
      df_pair_disp_sub = df_pair_disp[df_pair_disp['distance'] <= dist_lim]
      ls_se_desc.append(df_pair_disp_sub[ls_var_desc].describe().ix[stat])
      ls_nb_obs.append(len(df_pair_disp_sub))
    df_desc_pair_disp = pd.concat(ls_se_desc,
                                  axis = 1,
                                  keys = [x[0] for x in ls_loop_pair_disp])
    df_desc_pair_disp.ix['nb_obs'] = ls_nb_obs
    print(df_desc_pair_disp.ix[['nb_obs'] + ls_var_desc[1:]].T.to_string())

## Nb ids covered for each distance
#print()
#print('Nb ids covered depending on distance:')
#for dist_lim in [0.5, 1, 3, 5, 10]:
#  df_temp = df_pair_comp[df_pair_comp['distance'] <= dist_lim]
#  ls_ids = set(df_temp['id_1'].values.tolist() +\
#                 df_temp['id_2'].values.tolist())
#  print('Nb ids for dist {:.1f} km: {:d}'.format(dist_lim, len(ls_ids)))
#
## ##################################
## PCT SAME PRICE VS. RANK REVERSALS
## ##################################
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
## ##############
## ALIGNED PRICES
## ##############
#
#df_pairs = df_pair_comp[df_pair_comp['distance'] <= 5].copy()
#
#print()
#print(u'Nb aligned prices i.e. pct_same >= 33%:',\
#      len(df_pairs[(df_pairs['pct_same'] >= 33.0)])) # todo: harmonize pct i.e. * 100
#
## todo: add distinction supermarkets vs. others
#print()
#print(u'Overview aligned prices i.e. pct_same >= 33%:')
#print(df_pairs[(df_pairs['pct_same'] >= 33.0)][['pct_rr',
#                                                'nb_rr',
#                                                'pct_same']].describe())
#
## STANDARD SPREAD (ALLOW GENERALIZATION OF LEADERSHIP?)
#print()
#print('Inspect abs mc_spread == 1.0:')
#print(df_pairs[(df_pairs['mc_spread'] == 1.0) | (df_pairs['mc_spread'] == -1.0)]
#              [['distance', 'abs_mean_spread',
#                'pct_rr', 'freq_mc_spread', 'pct_same']].describe())
#
## LEADERSHIP TEST
#df_pairs['leader_pval'] = np.nan
#df_pairs['leader_pval'] = df_pairs[(~df_pairs['nb_1_lead'].isnull()) &\
#                                   (~df_pairs['nb_2_lead'].isnull())].apply(\
#                            lambda x: scipy.stats.binom_test(x[['nb_1_lead',
#                                                                'nb_2_lead']].values,
#                                                             p = 0.5),
#                            axis = 1)
#
### add a measure of whether this is significant (vs total nb of changes?)
### ... requires scipy 0.18 to test proba of success greater (or code it)
##df_pairs['same_pval'] = np.nan
##df_pairs['same_pval'] = df_pairs[(~df_pairs['nb_spread'].isnull())].apply(\
##                            lambda x: scipy.stats.binom_test(x['nb_same'],
##                                                             x['nb_spread'],
##                                                             p = 0.1,
##                                                             alternative = 'greater'),
##                            axis = 1)
#
#lsd_ld = ['pct_same', 'nb_same', 'nb_chge_to_same',
#          'nb_1_lead', 'nb_2_lead', 'leader_pval']
#
#print()
#print(u'Inspect leaders:')
#print(df_pairs[lsd_ld][df_pairs['leader_pval'] <= 0.05][0:20].to_string())
#
#print()
#print(u'Types of pairs with leaders:')
#print(df_pairs[df_pairs['leader_pval'] <= 0.05]['pair_type'].value_counts())
#
#print()
#print(u'Types of pairs with leaders (pct):')
#print(df_pairs[df_pairs['leader_pval'] <= 0.05]['pair_type'].value_counts() /\
#        df_pairs['pair_type'].value_counts()* 100)
#
#
#print()
#df_pairs['leader_brand'] = np.nan
#df_pairs.loc[(df_pairs['leader_pval'] <= 0.05) &\
#             (df_pairs['nb_1_lead'] > df_pairs['nb_2_lead']),
#             'leader_brand'] = df_pairs['brand_last_1']
#                      
#df_pairs.loc[(df_pairs['leader_pval'] <= 0.05) &\
#             (df_pairs['nb_1_lead'] < df_pairs['nb_2_lead']),
#             'leader_brand'] = df_pairs['brand_last_2']
#
## todo: leader brand only of stations which have:
## - no leader
## - not engaged in tough competition
#
#print()
#print(u'Inspect leader brands')
#print(df_pairs['leader_brand'].value_counts()[0:10])
#
### impose close price comp: pct_same 0.33 or 0.50
#
#df_close_comp = df_pairs[(df_pairs['pct_same'] >= 30)].copy()
#
##df_close_comp = df_pairs[(df_pairs['pct_same'] >= 30) |\
##                         (df_pairs['leader_pval'] <= 0.05)].copy()
##df_close_comp = df_pairs[(df_pairs['abs_mean_spread'] <= 1.0) &\
##                         (df_pairs['pct_same'] >= 30)]
#
### check what is mutually exclusive
#
## absolute leader: leading, not led, not uncertain
## leader_led: leading, led
## leader_uncertain: leading, uncertain
## relative leader: leading
#
#ls_close_comp = list(set(\
#  df_close_comp['id_1'].values.tolist() +\
#  df_close_comp['id_2'].values.tolist()))
#
#ls_rel_leader = list(set(\
#  df_close_comp['id_1'][(df_close_comp['leader_pval'] <= 0.05) &\
#                        (df_pairs['nb_1_lead'] > df_pairs['nb_2_lead'])].values.tolist() +\
#  df_close_comp['id_2'][(df_close_comp['leader_pval'] <= 0.05) &\
#                        (df_pairs['nb_1_lead'] < df_pairs['nb_2_lead'])].values.tolist()))
#
#ls_rel_led = list(set(\
#  df_close_comp['id_1'][(df_close_comp['leader_pval'] <= 0.05) &\
#                        (df_pairs['nb_1_lead'] < df_pairs['nb_2_lead'])].values.tolist() +\
#  df_close_comp['id_2'][(df_close_comp['leader_pval'] <= 0.05) &\
#                        (df_pairs['nb_1_lead'] > df_pairs['nb_2_lead'])].values.tolist()))
#
#ls_rel_unc = list(set(\
#  df_close_comp['id_1'][(df_close_comp['leader_pval'] > 0.05)].values.tolist() +\
#  df_close_comp['id_2'][(df_close_comp['leader_pval'] > 0.05)].values.tolist()))
#
#ls_abs_leader = list(set(ls_rel_leader).difference(set(ls_rel_led))\
#                                       .difference(set(ls_rel_unc)))
#
#ls_leader_led = list(set(ls_rel_leader).intersection(set(ls_rel_led)))
#
#ls_leader_unc = list(set(ls_rel_leader).intersection(set(ls_rel_unc)))
#
## absolute led: led, not leading, not uncertain
## relative led: led
#
#ls_abs_led = list(set(ls_rel_led).difference(set(ls_rel_leader))\
#                                 .difference(set(ls_rel_unc)))
#
## absolute uncertain: uncertain, not leading, not led
## relative uncertain: uncertain
#
#ls_abs_unc = list(set(ls_rel_unc).difference(set(ls_rel_leader))\
#                                 .difference(set(ls_rel_led)))
#
## take into account fact that many total access are dropped (margin chge)
#ls_drop_ids = df_margin_chge[df_margin_chge['value'].abs() >= 0.03].index
#df_info = df_info[~df_info.index.isin(ls_drop_ids)]
#
#ls_close_comp_su = [['close_comp', ls_close_comp],
#                    ['rel_leader', ls_rel_leader],
#                    ['abs_leader', ls_abs_leader],
#                    ['rel_led', ls_rel_led],
#                    ['abs_led', ls_abs_led],
#                    ['rel_unc', ls_rel_unc],
#                    ['abs_unc', ls_abs_unc]]
##                    ['leader_unc', ls_leader_unc]]
#
#ls_station_ind_cols = ['group_type', 'brand']
#
#ls_se_leader = []
#for title_temp, ls_ids_temp in ls_close_comp_su:
#  ls_se_leader.append(df_info.ix[ls_ids_temp]\
#                                [ls_station_ind_cols].groupby(ls_station_ind_cols).agg(len))
#
#df_leader_brands =\
#  pd.concat([df_info[ls_station_ind_cols].groupby(ls_station_ind_cols).agg(len)] + ls_se_leader,
#            axis = 1,
#            keys = ['nb_stations'] + [x[0] for x in ls_close_comp_su])
#
##ls_se_leader = []
##for title_temp, ls_ids_temp in ls_close_comp_su:
##  ls_se_leader.append(df_info.ix[ls_ids_temp]['brand_last'].value_counts())
##
##df_leader_brands = pd.concat([df_info['brand_last'].value_counts()] + ls_se_leader,
##                             axis = 1,
##                             keys = ['nb_stations'] + [x[0] for x in ls_close_comp_su])
#
##df_leader_brands = df_leader_brands[df_leader_brands['nb_stations'] >= 30]
#df_leader_brands = df_leader_brands.fillna(0)
#
#df_leader_brands_pct =\
#  df_leader_brands.apply(lambda x: x / df_leader_brands['nb_stations'] * 100)
#df_leader_brands_pct['nb_stations'] = df_leader_brands['nb_stations']
#
#df_leader_brands_pct.sort('nb_stations', ascending = False, inplace = True)
#
##df_leader_brands_pct = df_leader_brands_pct.sortlevel()
##print()
##print(df_leader_brands_pct.to_string())
#
## caution: need to be exhaustive...
#ls_station_reind = [['OIL', 'TOTAL'],
#                    ['OIL', 'ELAN'],
#                    ['OIL', 'AGIP'],
#                    ['OIL', 'BP'],
#                    ['OIL', 'ESSO'],
#                    ['IND', 'AVIA'],
#                    ['IND', 'DYNEFF'],
#                    ['IND', 'INDEPENDANT'],
#                    ['DIS', 'TOTAL_ACCESS'],
#                    ['DIS', 'ESSO_EXPRESS'],
#                    ['HYP', 'CARREFOUR'],
#                    ['HYP', 'AUCHAN'],
#                    ['HYP', 'CORA'],
#                    ['HYP', 'GEANT'],
#                    ['HYP', 'INTERMARCHE'],
#                    ['HYP', 'SYSTEMEU'],
#                    ['HYP', 'LECLERC'],
#                    ['SUP', 'CARREFOUR_MARKET'],
#                    ['SUP', 'CARREFOUR_CONTACT'],
#                    ['SUP', 'SIMPLY'],
#                    ['SUP', 'CASINO'],
#                    ['SUP', 'INTERMARCHE_CONTACT'],
#                    ['SUP', 'OTHER_SUP']]
#
#df_leader_brands_pct = df_leader_brands_pct.reindex([tuple(x) for x in ls_station_reind])
#print(df_leader_brands_pct.to_string(float_format = '{:.0f}'.format))
#
#df_leader_brands_pct.to_csv(os.path.join(path_dir_built_dis_csv,
#                                         'df_temp.csv'),
#                               index = True,
#                               encoding = 'latin-1',
#                               sep = ';',
#                               escapechar = '\\',
#                               quoting = 1) 
