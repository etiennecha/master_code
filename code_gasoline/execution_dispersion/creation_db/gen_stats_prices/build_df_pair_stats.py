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

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

ls_comp_pairs = dec_json(os.path.join(path_dir_built_json, 'ls_comp_pairs.json'))

# LOAD DF PRICES
df_prices = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices.set_index('date', inplace = True)

# GET DF PAIR STATS

# Basic loop: followed price changes and prices matched by competitor
start = time.clock()
ls_df_price_ids = df_prices.columns
km_bound = 5
ls_ls_results = []
for (indiv_id, competitor_id, distance) in ls_comp_pairs:
  if (distance < km_bound) and\
     (indiv_id in ls_df_price_ids) and\
     (competitor_id in ls_df_price_ids):
    ls_followed_chges = get_stats_two_firm_price_chges(df_prices[indiv_id].values,
                                                       df_prices[competitor_id].values)
    ls_matched_prices = get_two_firm_similar_prices(df_prices[indiv_id].values,
                                                    df_prices[competitor_id].values)
    ls_ls_results.append([[indiv_id, competitor_id, distance],
                          ls_followed_chges,
                          list(ls_matched_prices)])
print 'Loop: raw price changes vs. comp analysis',  time.clock() - start

# Build dataframe
ls_rows = [ls_results[0] + ls_results[1][:-2] + ls_results[2][:3] +\
             [len(ls_results[2][3]), len(ls_results[2][4])] for ls_results in ls_ls_results]
ls_followed_chges_titles = ['nb_days_1', 'nb_days_2', 'nb_prices_1', 'nb_prices_2',
                            'nb_ctd_1', 'nb_ctd_2', 'nb_chges_1', 'nb_chges_2', 'nb_sim_chges',
                            'nb_1_fol', 'nb_2_fol']
ls_matched_prices_titles = ['nb_spread', 'nb_same', 'chge_to_same','lead_1', 'lead_2']
ls_columns = ['id_1', 'id_2', 'distance'] + ls_followed_chges_titles + ls_matched_prices_titles
df_comp_chges = pd.DataFrame(ls_rows, columns = ls_columns)

# Followed price changes
df_comp_chges['nb_chges_min'] = df_comp_chges[['nb_chges_1', 'nb_chges_2']].min(axis=1)

df_comp_chges['pct_sim_1'] = df_comp_chges['nb_sim_chges'] / df_comp_chges['nb_chges_1']
df_comp_chges['pct_sim_2'] = df_comp_chges['nb_sim_chges'] / df_comp_chges['nb_chges_2']
df_comp_chges['pct_sim'] = df_comp_chges[['pct_sim_1', 'pct_sim_2']].max(axis=1)
df_comp_chges['pct_sim'] = df_comp_chges['pct_sim'][df_comp_chges['nb_chges_min'] > 30]

fig = plt.figure()
ax = fig.add_subplot(111)
n, bins, patches = ax.hist(df_comp_chges['pct_sim']\
                              [~pd.isnull(df_comp_chges['pct_sim'])], 30)
ax.set_title('Histogram of pctage of simultaneous changes')
plt.show()

df_comp_chges['pct_close_1'] = df_comp_chges[['nb_sim_chges', 'nb_1_fol', 'nb_2_fol']].\
                                 sum(axis = 1) / df_comp_chges['nb_chges_1']
df_comp_chges['pct_close_2'] = df_comp_chges[['nb_sim_chges', 'nb_1_fol', 'nb_2_fol']].\
                                 sum(axis = 1) / df_comp_chges['nb_chges_2']
df_comp_chges['pct_close'] = df_comp_chges[['pct_close_1', 'pct_close_2']].max(axis=1)
df_comp_chges['pct_close'] = df_comp_chges['pct_close'][df_comp_chges['nb_chges_min'] > 30]

# matched prices
ls_match_disp = ['id_1', 'id_2', 'distance'] + ls_matched_prices_titles
# include simultaneous changes?
df_comp_chges['lead_both'] = df_comp_chges['lead_1'] + df_comp_chges['lead_2']
df_comp_chges['pct_lead_1'] = df_comp_chges['lead_1'] / df_comp_chges['lead_both']
df_comp_chges['pct_lead_2'] = df_comp_chges['lead_2'] / df_comp_chges['lead_both']

df_leader = df_comp_chges[(df_comp_chges['lead_both'] > 30) &\
                          ((df_comp_chges['pct_lead_1'] >= 0.7) |\
                           (df_comp_chges['pct_lead_1'] <= 0.3))]

print u'\nOverview: chges followed by competitor:'
print df_comp_chges[ls_match_disp][0:100].to_string()

print u'\nCandidates for close price competition:'
print df_leader[ls_match_disp][0:10].to_string()

# todo: how many have no competitors based on distance / on this criteria
# todo: how many recursions: too big markets? have to refine? which are excluded?
# todo: draw map with links between stations within market

# Check followed prices changes (very sensitive)
pair_id_1, pair_id_2 = '1500004', '1500006'
def plot_pair_followed_price_chges(pair_id_1, pair_id_2, beg=0, end=1000):
  ls_pair_chges = get_stats_two_firm_price_chges(df_prices[pair_id_1].values,
                                                 df_prices[pair_id_2].values)
  ax = df_prices[[pair_id_1, pair_id_2]][beg:end].plot()
  for day_ind in ls_pair_chges[-1]:
    line_1 = ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='b')
    line_1.set_dashes([4,2])
  for day_ind in ls_pair_chges[-2]:
    line_2 = ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='g')
    line_2.set_dashes([8,2])
  plt.show()

# Check matched prices (more robust but works only if no differentiation for now)
#pair_id_1, pair_id_2 = '1200003', '1200001'

def plot_pair_matched_prices(pair_id_1, pair_id_2, beg=0, end=1000):
  ls_sim_prices = get_two_firm_similar_prices(df_prices[pair_id_1].values,
                                              df_prices[pair_id_2].values)
  ax = df_prices[[pair_id_1, pair_id_2]][beg:end].plot()
  for day_ind in ls_sim_prices[3]:
  	ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='b')
  for day_ind in ls_sim_prices[4]:
  	ax.axvline(x=df_prices.index[day_ind], lw=1, ls='--', c='g')
  plt.show()
  
plot_pair_matched_prices('1700004', '1120005')
