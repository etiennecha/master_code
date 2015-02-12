#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

path_dir_built_paper = os.path.join(path_data,
                                    'data_gasoline',
                                    'data_built',
                                    'data_paper_dispersion')

path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DATA
# ##############

# LOAD COMPETITOR PAIRS
ls_comp_pairs = dec_json(os.path.join(path_dir_built_json,
                                      'ls_comp_pairs.json'))

# LOAD DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                            parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices = df_prices_ttc.copy()

ls_df_price_ids = df_prices.columns

# ##########################
# GET DF PAIR PRICE CHANGES
# ##########################

# LOOP: FOLLOWED CHANGES AND PRICE MATCHING
start = time.clock()
km_bound = 5
ls_ls_pair_stats = []
for (indiv_id, comp_id, distance) in ls_comp_pairs:
  if (distance < km_bound) and\
     (indiv_id in ls_df_price_ids) and\
     (comp_id in ls_df_price_ids):
    # A changes then B changes (A changes did not follow a change by B?)
    ls_followed_chges = get_stats_two_firm_price_chges(df_prices[indiv_id].values,
                                                       df_prices[comp_id].values)
    # A sets a price which is then matched by B (biased if promotions btw)
    ls_matched_prices = get_two_firm_similar_prices(df_prices[indiv_id].values,
                                                    df_prices[comp_id].values)
    ls_ls_pair_stats.append([[indiv_id, comp_id, distance],
                              ls_followed_chges,
                              list(ls_matched_prices)])
print 'Loop: raw price changes vs. comp analysis',  time.clock() - start

# BUILD DATAFRAME
ls_rows_pairs = [row[0] + row[1][0] + row[2][0] for row in ls_ls_pair_stats]

ls_followed_chges_cols = ['nb_ctd_1', 'nb_ctd_2', 'nb_ctd_both',
                          'nb_chges_1', 'nb_chges_2', 'nb_sim_chges',
                          'nb_1_fol', 'nb_2_fol']

ls_matched_prices_cols = ['nb_spread', 'nb_same', 'nb_chge_to_same',
                          'nb_1_lead', 'nb_2_lead']

df_pairs = pd.DataFrame(ls_rows_pairs, columns = ['id_a', 'id_b', 'distance'] +\
                                                 ls_followed_chges_cols +\
                                                 ls_matched_prices_cols)

df_pairs_bu = df_pairs.copy()

# Add min of chges to filter pairs
df_pairs['nb_chges_min'] = df_pairs[['nb_chges_1', 'nb_chges_2']].min(axis=1)

# Filter out pairs with insufficient data
print u'\nNb observations filtered out for lack of data: {:.0f}'.format(\
      len(df_pairs[~((df_pairs['nb_chges_min'] >= 20) &
                     (df_pairs['nb_spread'] >= 30) &\
                     (df_pairs['nb_ctd_both'] >= 30))]))

df_pairs = df_pairs[(df_pairs['nb_chges_min'] >= 20) &
                     (df_pairs['nb_spread'] >= 30) &\
                     (df_pairs['nb_ctd_both'] >= 30)]

# ENRICH DATAFRAME: FOLLOWED PRICE CHANGES

# Min and max percent of simultaneous changes
df_pairs['pct_sim_max'] = df_pairs.apply(\
   lambda x : max(x['nb_sim_chges']/float(x['nb_chges_1']),
                  x['nb_sim_chges']/float(x['nb_chges_2'])), axis = 1)
df_pairs['pct_sim_min'] = df_pairs.apply(\
   lambda x : min(x['nb_sim_chges']/float(x['nb_chges_1']),
                  x['nb_sim_chges']/float(x['nb_chges_2'])), axis = 1)

# Min and max percent of followed changes (pbm if few obs for other?)
df_pairs['pct_fol_max'] = df_pairs.apply(\
   lambda x : max(x['nb_1_fol']/float(x['nb_chges_1']),
                  x['nb_2_fol']/float(x['nb_chges_2'])), axis = 1)
df_pairs['pct_fol_min'] = df_pairs.apply(\
   lambda x : min(x['nb_1_fol']/float(x['nb_chges_1']),
                  x['nb_2_fol']/float(x['nb_chges_2'])), axis = 1)

# Min and max percent of close changes: simultaneous or followed
df_pairs['pct_close_max'] = df_pairs.apply(\
   lambda x : max((x['nb_1_fol'] + x['nb_sim_chges'])/float(x['nb_chges_1']),
                  (x['nb_2_fol'] + x['nb_sim_chges'])/float(x['nb_chges_2'])),
                  axis = 1)
df_pairs['pct_close_min'] = df_pairs.apply(\
   lambda x : min((x['nb_1_fol'] + x['nb_sim_chges'])/float(x['nb_chges_1']),
                  (x['nb_2_fol'] + x['nb_sim_chges'])/float(x['nb_chges_2'])),
                  axis = 1)

# ENRICH DATAFRAME: SAME PRICE
df_pairs['pct_same'] = df_pairs['nb_same'] / df_pairs['nb_spread'].astype(float)

df_pairs['pct_chge_to_same_max'] = df_pairs.apply(\
   lambda x : max(x['nb_chge_to_same']/float(x['nb_chges_1']),
                  x['nb_chge_to_same']/float(x['nb_chges_2'])), axis = 1)
df_pairs['pct_chge_to_same_min'] = df_pairs.apply(\
   lambda x : min(x['nb_chge_to_same']/float(x['nb_chges_1']),
                  x['nb_chge_to_same']/float(x['nb_chges_2'])), axis = 1)

df_pairs['pct_lead_max'] = df_pairs.apply(\
   lambda x : max(x['nb_1_lead']/float(x['nb_chges_1']),
                  x['nb_2_lead']/float(x['nb_chges_2'])), axis = 1)
df_pairs['pct_lead_min'] = df_pairs.apply(\
   lambda x : min(x['nb_1_lead']/float(x['nb_chges_1']),
                  x['nb_2_lead']/float(x['nb_chges_2'])), axis = 1)

# ################
# OUTPUT
# ################

df_pairs.to_csv(os.path.join(path_dir_built_csv,
                             'df_pair_stats.csv'),
                encoding = 'utf-8',
                index = False)

# ################
# STATS DES
# ################

df_pairs.replace([np.inf, -np.inf], np.nan, inplace = True)

## Drop vars which describe stations individually and are no more needed
#df_pairs.drop(['nb_ctd_1', 'nb_ctd_2', 'nb_chges_1', 'nb_chges_2'],
#              axis = 1, inplace = True)

print u'\Overview: pairs of stations:'
print df_pairs.describe()

## HISTOGRAM OF PCTAGE OF SIM CHANGES
#fig = plt.figure()
#ax = fig.add_subplot(111)
#n, bins, patches = ax.hist(df_pairs['pct_sim_max']\
#                              [~pd.isnull(df_pairs['pct_sim_max'])], 30)
#ax.set_title('Histogram of pctage of simultaneous changes')
#plt.show()

# CLOSE COMPETITION  / COLLUSION ?
# todo: how many same brand / group?
# todo: can be close competition and never have same price: followed + dispersion

print u'\nPairs with same price 50%+ of time: {:.0f}'.format(\
      len(df_pairs[df_pairs['pct_same'] >= 0.5]))

print u'\nPairs with same price 40%+ of time: {:.0f}'.format(\
      len(df_pairs[df_pairs['pct_same'] >= 0.4]))

print u'\nPairs with same price 30%+ of time: {:.0f}'.format(\
      len(df_pairs[df_pairs['pct_same'] >= 0.3]))

print u'\nPairs with same price 20%+ of time: {:.0f}'.format(\
      len(df_pairs[df_pairs['pct_same'] >= 0.2]))

# DETECT LEADERSHIP
ls_disp_cl = ['id_a', 'id_b', 'distance'] +\
             ['nb_ctd_both', 'nb_chges_1', 'nb_chges_2',
              'nb_1_lead', 'nb_2_lead', 'nb_chge_to_same',
              'pct_same', 'pct_lead_max', 'pct_lead_min']

print u'\nCandidates for leadership:'
print df_pairs[df_pairs['pct_lead_max'] >= 0.5][ls_disp_cl][0:10].to_string()

# QUESTIONS

# todo: how many have no competitors based on distance / on this criteria
# todo: how many recursions: too big markets? have to refine? which are excluded?
# todo: draw map with links between stations within market

# GRAPHS: FOLLOWED PRICE CHANGES (very sensitive)

pair_id_1, pair_id_2 = '1500004', '1500006'

def plot_pair_followed_price_chges(pair_id_1, pair_id_2, beg=0, end=1000):
  ls_followed_chges = get_stats_two_firm_price_chges(df_prices[pair_id_1].values,
                                                     df_prices[pair_id_2].values)
  ax = df_prices[[pair_id_1, pair_id_2]][beg:end].plot()
  for day_ind in ls_followed_chges[1][0]:
    line_1 = ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='b')
    line_1.set_dashes([4,2])
  for day_ind in ls_followed_chges[1][1]:
    line_2 = ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='g')
    line_2.set_dashes([8,2])
  plt.show()

plot_pair_followed_price_chges('1500004', '1500006')

# GRAHS: MATCHED PRICES (more robust but works only if no differentiation for now)

pair_id_1, pair_id_2 = '1200003', '1200001'

def plot_pair_matched_prices(pair_id_1, pair_id_2, beg=0, end=1000):
  ls_sim_prices = get_two_firm_similar_prices(df_prices[pair_id_1].values,
                                              df_prices[pair_id_2].values)
  ax = df_prices[[pair_id_1, pair_id_2]][beg:end].plot()
  for day_ind in ls_sim_prices[1][0]:
  	ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='b')
  for day_ind in ls_sim_prices[1][1]:
  	ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='g')
  plt.show()
  
plot_pair_matched_prices('1700004', '1120005')
