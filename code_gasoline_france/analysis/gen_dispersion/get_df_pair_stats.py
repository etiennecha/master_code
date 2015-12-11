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

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

# ##############
# LOAD DATA
# ##############

# CLOSE PAIRS
ls_pairs = dec_json(os.path.join(path_dir_built_json,
                                 'ls_close_pairs.json'))

# DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = True)
df_prices_cl.set_index('date', inplace = True)

# DF MARGIN CHANGE
df_margin_chge = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_margin_chge.csv'),
                             dtype = {'id_station' : str},
                             encoding = 'utf-8')
df_margin_chge.set_index('id_station', inplace = True)

df_margin_chge = df_margin_chge[df_margin_chge['value'].abs() >= 0.03]

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

# ##########################
# GET DF PAIR PRICE CHANGES
# ##########################

# can accomodate both ttc prices (raw prices) or cleaned prices
df_prices = df_prices_ttc
ls_df_price_ids = df_prices.columns
km_bound = 5
diff_bound = 0.02

ls_keep_info = list(df_info[df_info['highway'] != 1].index)
ls_keep_stats = list(df_station_stats[(df_station_stats['nb_chge'] >= 5) &\
                                      (df_station_stats['pct_chge'] >= 0.03)].index)
ls_keep_ids = list(set(ls_keep_info).intersection(set(ls_keep_stats)))
ls_keep_ids = list(set(df_prices.columns).intersection(set(ls_keep_ids)))

ls_keep_pairs = [(indiv_id, other_id, distance)\
                   for (indiv_id, other_id, distance) in ls_pairs if\
                     (indiv_id in ls_keep_ids) and (other_id in ls_keep_ids)]

# LOOP: FOLLOWED CHANGES AND PRICE MATCHING
start = time.clock()
ls_ls_pair_stats = []
for (indiv_id, other_id, distance) in ls_keep_pairs:
  if distance <= km_bound:
    mc_date = None # base case: no limit date
    # change in margin/pricing policy
    ls_mc_dates = [df_margin_chge['date'].ix[id_station]\
                     for id_station in [indiv_id, other_id]\
                       if id_station in df_margin_chge.index]
    if ls_mc_dates:
      ls_mc_dates.sort()
      mc_date = ls_mc_dates[0]
    se_prices_1 = df_prices[indiv_id][:mc_date].values
    se_prices_2 = df_prices[other_id][:mc_date].values
    ls_spread = get_stats_two_firm_price_spread(se_prices_1,
                                                se_prices_2, 3)
    # A changes then B changes (A changes did not follow a change by B?)
    ls_followed_chges = get_stats_two_firm_price_chges(se_prices_1,
                                                       se_prices_2)
    # A sets a price which is then matched by B (biased if promotions btw)
    ls_matched_prices = get_stats_two_firm_same_prices(se_prices_1,
                                                       se_prices_2)
    ls_ls_pair_stats.append([[indiv_id, other_id, distance],
                             ls_spread,
                             ls_followed_chges,
                             list(ls_matched_prices)])
print('Loop: raw price changes vs. comp analysis',  time.clock() - start)

# BUILD DATAFRAME
ls_rows_pairs = [row[0] + row[1] + row[2][0] + row[3][0] for row in ls_ls_pair_stats]

ls_spread_cols = ['nb_spread', 'mean_spread', 'mean_abs_spread',
                  'std_spread', 'std_abs_spread',
                  'mc_spread', 'freq_mc_spread',
                  'smc_spread', 'freq_smc_spread',
                  'med_spread', 'freq_med_spread']

ls_followed_chges_cols = ['nb_ctd_1', 'nb_ctd_2', 'nb_ctd_both',
                          'nb_chges_1', 'nb_chges_2', 'nb_sim_chges',
                          'nb_1_fol', 'nb_2_fol']

ls_matched_prices_cols = ['nb_spread_alt', 'nb_same', 'nb_chge_to_same',
                          'nb_1_lead', 'nb_2_lead']

df_pairs = pd.DataFrame(ls_rows_pairs, columns = ['id_1', 'id_2', 'distance'] +\
                                                 ls_spread_cols +\
                                                 ls_followed_chges_cols +\
                                                 ls_matched_prices_cols)
df_pairs_bu = df_pairs.copy()

# ENRICH DATAFRAME: FOLLOWED PRICE CHANGES

# Min and max percent of simultaneous changes
df_pairs['pct_sim_max'] = df_pairs[['nb_chges_1', 'nb_chges_2']].apply(\
                            lambda x: df_pairs['nb_sim_chges'] / x.astype(float),
                            axis = 0).max(axis = 1)

df_pairs['pct_sim_min'] = df_pairs[['nb_chges_1', 'nb_chges_2']].apply(\
                            lambda x: df_pairs['nb_sim_chges'] / x.astype(float),
                            axis = 0).min(axis = 1)

# Min and max percent of followed changes (pbm if few obs for other?)
df_pairs['pct_fol_max'] = df_pairs.apply(\
   lambda x : max(x['nb_1_fol']/np.float64(x['nb_chges_1']),
                  x['nb_2_fol']/np.float64(x['nb_chges_2'])), axis = 1)
df_pairs['pct_fol_min'] = df_pairs.apply(\
   lambda x : min(x['nb_1_fol']/np.float64(x['nb_chges_1']),
                  x['nb_2_fol']/np.float64(x['nb_chges_2'])), axis = 1)

# Min and max percent of close changes: simultaneous or followed
df_pairs['pct_close_max'] = df_pairs.apply(\
   lambda x : max((x['nb_1_fol'] + x['nb_sim_chges'])/np.float64(x['nb_chges_1']),
                  (x['nb_2_fol'] + x['nb_sim_chges'])/np.float64(x['nb_chges_2'])),
                  axis = 1)
df_pairs['pct_close_min'] = df_pairs.apply(\
   lambda x : min((x['nb_1_fol'] + x['nb_sim_chges'])/np.float64(x['nb_chges_1']),
                  (x['nb_2_fol'] + x['nb_sim_chges'])/np.float64(x['nb_chges_2'])),
                  axis = 1)

# ENRICH DATAFRAME: SAME PRICE
df_pairs['pct_same'] = df_pairs['nb_same'] / df_pairs['nb_spread'].astype(float)

df_pairs['pct_chge_to_same_max'] = df_pairs.apply(\
   lambda x : max(x['nb_chge_to_same']/np.float64(x['nb_chges_1']),
                  x['nb_chge_to_same']/np.float64(x['nb_chges_2'])), axis = 1)
df_pairs['pct_chge_to_same_min'] = df_pairs.apply(\
   lambda x : min(x['nb_chge_to_same']/np.float64(x['nb_chges_1']),
                  x['nb_chge_to_same']/np.float64(x['nb_chges_2'])), axis = 1)

df_pairs['pct_lead_max'] = df_pairs.apply(\
   lambda x : max(x['nb_1_lead']/np.float64(x['nb_chges_1']),
                  x['nb_2_lead']/np.float64(x['nb_chges_2'])), axis = 1)
df_pairs['pct_lead_min'] = df_pairs.apply(\
   lambda x : min(x['nb_1_lead']/np.float64(x['nb_chges_1']),
                  x['nb_2_lead']/np.float64(x['nb_chges_2'])), axis = 1)

# ################
# OUTPUT
# ################

# Add min of chges to filter pairs
df_pairs['nb_chges_min'] = df_pairs[['nb_chges_1', 'nb_chges_2']].min(axis=1)

## Drop vars which describe stations individually and are no more needed
## Cannot just uncomment.. vars used below
#df_pairs.drop(['nb_ctd_1', 'nb_ctd_2', 'nb_chges_1', 'nb_chges_2'],
#              axis = 1, inplace = True)

# Replace inf (div by 0)
df_pairs.replace([np.inf, -np.inf], np.nan, inplace = True)

df_pairs.to_csv(os.path.join(path_dir_built_dis_csv,
                             'df_pair_stats.csv'),
                encoding = 'utf-8',
                index = False)

## ################
## STATS DES
## ################
#
## Filter out pairs with insufficient data
#print u'\nNb observations filtered out for lack of data: {:.0f}'.format(\
#      len(df_pairs[~((df_pairs['nb_chges_min'] >= 20) &
#                     (df_pairs['nb_spread'] >= 30) &\
#                     (df_pairs['nb_ctd_both'] >= 30))]))
#
#df_pairs = df_pairs[(df_pairs['nb_chges_min'] >= 20) &
#                    (df_pairs['nb_spread'] >= 30) &\
#                    (df_pairs['nb_ctd_both'] >= 30)]
#
#
#print u'\Overview: pairs of stations:'
#print df_pairs.describe()
#
### HISTOGRAM OF PCTAGE OF SIM CHANGES
##fig = plt.figure()
##ax = fig.add_subplot(111)
##n, bins, patches = ax.hist(df_pairs['pct_sim_max']\
##                              [~pd.isnull(df_pairs['pct_sim_max'])], 30)
##ax.set_title('Histogram of pctage of simultaneous changes')
##plt.show()
#
## CLOSE COMPETITION  / COLLUSION ?
## todo: how many same brand / group?
## todo: can be close competition and never have same price: followed + dispersion
#
#print u'\nPairs with same price 50%+ of time: {:.0f}'.format(\
#      len(df_pairs[df_pairs['pct_same'] >= 0.5]))
#
#print u'\nPairs with same price 40%+ of time: {:.0f}'.format(\
#      len(df_pairs[df_pairs['pct_same'] >= 0.4]))
#
#print u'\nPairs with same price 30%+ of time: {:.0f}'.format(\
#      len(df_pairs[df_pairs['pct_same'] >= 0.3]))
#
#print u'\nPairs with same price 20%+ of time: {:.0f}'.format(\
#      len(df_pairs[df_pairs['pct_same'] >= 0.2]))
#
## DETECT LEADERSHIP
#ls_disp_cl = ['id_a', 'id_b', 'distance'] +\
#             ['nb_ctd_both', 'nb_chges_1', 'nb_chges_2',
#              'nb_1_lead', 'nb_2_lead', 'nb_chge_to_same',
#              'pct_same', 'pct_lead_max', 'pct_lead_min']
#
#print u'\nCandidates for leadership:'
#print df_pairs[df_pairs['pct_lead_max'] >= 0.5][ls_disp_cl][0:10].to_string()
#
## QUESTIONS
#
## todo: how many have no competitors based on distance / on this criteria
## todo: how many recursions: too big markets? have to refine? which are excluded?
## todo: draw map with links between stations within market
#
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
#
## GRAHS: MATCHED PRICES (more robust but works only if no differentiation for now)
#
#pair_id_1, pair_id_2 = '1200003', '1200001'
#
#def plot_pair_matched_prices(pair_id_1, pair_id_2, beg=0, end=1000):
#  ls_sim_prices = get_two_firm_similar_prices(df_prices[pair_id_1].values,
#                                              df_prices[pair_id_2].values)
#  ax = df_prices[[pair_id_1, pair_id_2]][beg:end].plot()
#  for day_ind in ls_sim_prices[1][0]:
#  	ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='b')
#  for day_ind in ls_sim_prices[1][1]:
#  	ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='g')
#  plt.show()
#  
#plot_pair_matched_prices('1700004', '1120005')
