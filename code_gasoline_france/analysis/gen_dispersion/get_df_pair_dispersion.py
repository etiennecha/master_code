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

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

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

# CLOSE PAIRS
ls_close_pairs = dec_json(os.path.join(path_dir_built_json,
                                       'ls_close_pairs.json'))

# COMPETITORS
dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# STABLE MARKETS
ls_dict_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                               'ls_dict_stable_markets.json'))
ls_robust_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                                 'ls_robust_stable_markets.json'))
# 0 is 3km, 1 is 4km, 2 is 5km
ls_stable_markets = [stable_market for nb_sellers, stable_markets\
                       in ls_dict_stable_markets[2].items()\
                          for stable_market in stable_markets]

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
                          parse_dates = True)
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

# ######################
# GET DF PAIR DISPERSION
# ######################

# Need to consider both raw prices and residuals
km_bound = 5 # extend to 10 for robustness checks?
margin_chge_bound = 0.03
ls_pairs = ls_close_pairs

# Scenarios:
# Residuals
# Raw prices no mc
# Raw prices before mc
# Raw prices after mc
# Raw prices all

# Post processing: competitor vs same brand and pair distance

df_prices = df_prices_ttc
ls_pairs = ls_close_pairs
km_bound = 5
margin_chge_bound = 0.03

ls_keep_pairs = [(indiv_id, other_id, distance)\
                   for (indiv_id, other_id, distance) in ls_pairs if\
                     (distance <= km_bound) and\
                     (indiv_id in ls_keep_ids) and\
                     (other_id in ls_keep_ids)]

ls_ids_margin_chge =\
  df_margin_chge[df_margin_chge['value'].abs() >= margin_chge_bound].index

ls_loop_pairs = []
for (indiv_id, other_id, distance) in ls_keep_pairs:
  ls_mc_dates = [df_margin_chge['date'].ix[id_station]\
                   for id_station in [indiv_id, other_id]\
                     if id_station in ls_ids_margin_chge]
  ls_mc_dates.sort()
  ls_loop_pairs.append((indiv_id, other_id, distance, ls_mc_dates))

def get_ls_dispersion_res(res):
  return res[0] + get_ls_standardized_frequency(res[3][0])

start = time.clock()
ls_categories = ['residuals', 'before_mc', 'after_mc', 'no_mc', 'all']
dict_pairs_rr = {k : [] for k in ls_categories}
dict_ls_ar_rrs = {k : [] for k in ls_categories}
dict_dict_rr_lengths = {k : {} for k in ls_categories}
for (indiv_id, other_id, distance, ls_mc_dates) in ls_loop_pairs:
  base_res = [indiv_id, other_id, distance]
  # Residuals
  se_prices_1_cl = df_prices_cl[indiv_id]
  se_prices_2_cl = df_prices_cl[other_id]
  res_cl = get_pair_price_dispersion(se_prices_1_cl, se_prices_2_cl, light = False)
  dict_pairs_rr['residuals'].append(base_res + res_cl)
  dict_ls_ar_rrs['residuals'].append(res_cl[2][1])
  dict_dict_rr_lengths['residuals']['{:s}-{:s}'.format(indiv_id, other_id)] =\
      res_cl[3][0]
  # Raw prices
  se_prices_1 = df_prices_ttc[indiv_id]
  se_prices_2 = df_prices_ttc[other_id]
  if ls_mc_dates:
    # before changes
    se_prices_1_b = se_prices_1.copy()
    se_prices_1_b.ix[ls_mc_dates[0]:] = np.nan
    se_prices_2_b = se_prices_2.copy()
    se_prices_2_b.ix[ls_mc_dates[0]:] = np.nan
    res_b = get_pair_price_dispersion(se_prices_1_b, se_prices_2_b, light = False)
    dict_pairs_rr['before_mc'].append(base_res + get_ls_dispersion_res(res_b))
    dict_ls_ar_rrs['before_mc'].append(res_b[2][1])
    dict_dict_rr_lengths['before_mc']['{:s}-{:s}'.format(indiv_id, other_id)] =\
        res_b[3][0]
    # after changes
    se_prices_1_a = se_prices_1.copy()
    se_prices_1_a.ix[:ls_mc_dates[-1]] = np.nan
    se_prices_2_a = se_prices_2.copy()
    se_prices_2_a.ix[:ls_mc_dates[-1]] = np.nan
    res_a = get_pair_price_dispersion(se_prices_1_a, se_prices_2_a, light = False)
    dict_pairs_rr['after_mc'].append(base_res + get_ls_dispersion_res(res_a))
    dict_ls_ar_rrs['after_mc'].append(res_a[2][1])
    dict_dict_rr_lengths['after_mc']['{:s}-{:s}'.format(indiv_id, other_id)] =\
        res_a[3][0]
    # disregarding changes
    res = get_pair_price_dispersion(se_prices_1, se_prices_2, light = False)
    dict_pairs_rr['all'].append(base_res + get_ls_dispersion_res(res))
    dict_ls_ar_rrs['all'].append(res[2][1])
    dict_dict_rr_lengths['all']['{:s}-{:s}'.format(indiv_id, other_id)] =\
        res[3][0]
  else:
    res = get_pair_price_dispersion(se_prices_1, se_prices_2, light = False)
    dict_pairs_rr['no_mc'].append(base_res + get_ls_dispersion_res(res))
    dict_ls_ar_rrs['no_mc'].append(res[2][1])
    dict_dict_rr_lengths['no_mc']['{:s}-{:s}'.format(indiv_id, other_id)] =\
        res[3][0]
    dict_pairs_rr['all'].append(base_res + get_ls_dispersion_res(res))
    dict_ls_ar_rrs['all'].append(res[2][1])
    dict_dict_rr_lengths['all']['{:s}-{:s}'.format(indiv_id, other_id)] =\
        res[3][0]
print('Loop: rank reversals',  time.clock() - start)

# BUILD DF PAIR RANK REVERSALS

ls_rows_pairs_rr = []
for title_temp, ls_ls_pairs_rr_temp in dict_pairs_rr.items():
  ls_rows_temp = [[title_temp] + row for row in ls_ls_pairs_rr_temp]
  ls_rows_pairs_rr += ls_rows_temp

ls_scalar_cols  = ['nb_spread', 'nb_same_price', 'nb_1_cheaper', 'nb_2_cheaper', 
                   'nb_rr', 'pct_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr',
                   'avg_abs_spread', 'avg_spread', 'std_spread', 'std_abs_spread']

ls_freq_std_cols = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

ls_columns  = ['cat', 'id_1', 'id_2', 'distance'] +\
              ls_scalar_cols + ls_freq_std_cols

df_pairs_rr = pd.DataFrame(ls_rows_pairs_rr, columns = ls_columns)

# BUILD DF RANK REVERSALS

dict_df_rr = {}
for cat, ls_ar_rrs in dict_ls_ar_rrs.items():
  ls_index = ['-'.join(ppd[:2]) for ppd in dict_pairs_rr[cat]]
  df_rr = pd.DataFrame(dict_ls_ar_rrs[cat],
                       index = ls_index,
                       columns = df_prices_ttc.index).T
  dict_df_rr[cat] = df_rr

# could use tuple index but not very convenient to read csv
# store dates in column to make csv convenient to read

# #########
# OUPUT
# #########

# CSV

df_pairs_rr.to_csv(os.path.join(path_dir_built_dis_csv,
                                'df_pairs_dispersion.csv'),
                   encoding = 'utf-8',
                   index = False)

for cat, df_rr_cat in dict_df_rr.items():
  df_rr.to_csv(os.path.join(path_dir_built_dis_csv,
                            'df_rank_reversals_{:s}.csv'.format(cat)),
                                        float_format= '%.3f',
                                        encoding = 'utf-8')

# JSON

enc_json(dict_dict_rr_lengths, os.path.join(path_dir_built_dis_json,
                                            'dict_dict_rr_lengths.json'))

## ###############
## STATS DES: PPD
## ###############
#
## CREATE SAME CORNER VARIABLE
#
#for dist in [500, 750, 1000]:
#  df_pairs_rr['sc_{:d}'.format(dist)] = 0
#  df_pairs_rr.loc[df_pairs_rr['distance'] <= dist/1000.0, 'sc_{:d}'.format(dist)] = 1
#
## ADD BRANDS AND CODE INSEE (MOVE)
#
#df_info_sub = df_info[['ci_ardt_1', 'brand_0', 'brand_1', 'brand_2']].copy()
#df_info_sub['id_a'] = df_info_sub.index
#df_pairs_rr = pd.merge(df_info_sub, df_pairs_rr, on='id_a', how = 'right')
#df_info_sub.rename(columns={'id_a': 'id_b'}, inplace = True)
#
#df_pairs_rr = pd.merge(df_info_sub,
#                  df_pairs_rr,
#                  on='id_b',
#                  how = 'right',
#                  suffixes=('_b', '_a'))
#
## Drop if insufficient observations
#df_pairs_rr = df_pairs_rr[df_pairs_rr['nb_spread'] >= 30]
#
#ls_disp_ppd = ['id_a', 'id_b', 'distance'] +\
#              ls_scalar_cols +\
#              ['abs_avg_spread_ttc']
#
#print u'\nOverview df_pairs_rr:'
#print df_pairs_rr[ls_disp_ppd][0:10].to_string()
#
#ls_disp_rr = ['pct_rr', 'nb_rr', 'rr_1', 'rr_2', '5<rr<=20', 'rr>20']
#
#print u'\nOverview rank reversals (all):'
#print df_pairs_rr[ls_disp_rr].describe()
#
#print u'\nOverview high differentiation but high rank reversals'
#print df_pairs_rr[['id_a', 'id_b', 'distance', 'nb_spread', 'abs_avg_spread_ttc', 'pct_rr']]\
#        [(df_pairs_rr['abs_avg_spread_ttc'] >= 0.05) & (df_pairs_rr['pct_rr'] >= 0.3)]
#
#print u'\nOverview low differentiation and low rank reversals:'
#print len(df_pairs_rr[(df_pairs_rr['abs_avg_spread_ttc'] == 0) & (df_pairs_rr['pct_rr'] == 0)])
##print df_pairs_rr[['id_a', 'id_b', 'distance', 'nb_spread']]\
##        [(df_pairs_rr['abs_avg_spread_ttc'] == 0) & (df_pairs_rr['pct_rr'] == 0)]
### actually not competitors: same name "SA CHIRAULT" so drop it
##print len(df_pairs_rr[(df_pairs_rr['abs_avg_spread_ttc'] <= 0.01) & (df_pairs_rr['pct_rr'] < 0.01)])
##print df_pairs_rr[['id_a', 'id_b', 'distance', 'nb_spread', 'abs_avg_spread_ttc', 'pct_rr']]\
##        [(df_pairs_rr['abs_avg_spread_ttc'] <= 0.01) & (df_pairs_rr['pct_rr'] < 0.01)]
#
#print u'\nOverview rank reversals (low differentiation):'
#print df_pairs_rr[ls_disp_rr][df_pairs_rr['abs_avg_spread_ttc'] <= 0.02].describe()
#
#print u'\nPairs with a least one rank reversal per month: {:.0f}'.format(\
#      len(df_pairs_rr[(df_pairs_rr['nb_rr'] >= df_pairs_rr['nb_spread'] / 30.0 )]))
#
#df_pairs_rr_hrr = df_pairs_rr[(df_pairs_rr['nb_rr'] >= df_pairs_rr['nb_spread'] / 30.0 )].copy()
#
#print u'\n', df_pairs_rr_hrr[ls_disp_rr].describe()
#
## Inspect those with rr of high length
#df_pairs_rr_hrr.sort('rr>20', ascending = False, inplace = True)
#print df_pairs_rr_hrr[['id_a', 'id_b', 'distance'] + ls_disp_rr][0:10].to_string()
