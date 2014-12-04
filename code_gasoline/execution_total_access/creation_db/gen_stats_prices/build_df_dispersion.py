#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

ls_comp_pairs = dec_json(os.path.join(path_dir_built_json, 'ls_comp_pairs.json'))

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

# GET DF PAIR DISPERSION

# can accomodate both ttc prices (raw prices) or cleaned prices
df_prices = df_prices_ttc
km_bound = 3
diff_bound = 0.02

ls_keep_ids = set(df_prices_cl.columns).intersection(set(df_prices_ttc.columns))
ls_comp_pairs = [(indiv_id, competitor_id, distance)\
                   for (indiv_id, competitor_id, distance) in ls_comp_pairs if\
                     (indiv_id in ls_keep_ids) and (competitor_id in ls_keep_ids)]

start = time.clock()
ls_ppd = []
ls_pair_index = []
ls_ar_rrs = []
dict_rr_lengths = {}
for (indiv_id, competitor_id, distance) in ls_comp_pairs:
  if (distance <= km_bound):
    se_prices_1 = df_prices[indiv_id]
    se_prices_2 = df_prices[competitor_id]
    avg_spread = (df_prices_ttc[competitor_id] - df_prices_ttc[indiv_id]).mean()
    ls_comp_pd = get_pair_price_dispersion(se_prices_1.as_matrix(),
                                           se_prices_2.as_matrix(), light = False)
    ls_comp_chges = get_stats_two_firm_price_chges(se_prices_1.as_matrix(),
                                                   se_prices_2.as_matrix())
    ls_ppd.append([indiv_id, competitor_id, distance] +\
                  ls_comp_pd[0] +\
                  [avg_spread] +\
                  get_ls_standardized_frequency(ls_comp_pd[3][0]) +\
                  ls_comp_chges[:-2])
    pair_index = '-'.join([indiv_id, competitor_id])
    ls_pair_index.append(pair_index)
    ls_ar_rrs.append(ls_comp_pd[2][1])
    dict_rr_lengths[pair_index] = ls_comp_pd[3][0]
print 'Loop: rank reversals',  time.clock() - start

ls_scalars  = ['nb_spread', 'nb_same_price', 'nb_a_cheaper', 'nb_b_cheaper', 
               'nb_rr', 'pct_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr',
               'avg_abs_spread', 'avg_spread', 'std_spread', 'avg_ttc_spread']

ls_freq_std = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

ls_chges    = ['nb_days_a', 'nb_days_b', 'nb_prices_a', 'nb_prices_b',
               'nb_ctd_a', 'nb_ctd_b', 'nb_chges_a', 'nb_chges_b', 'nb_sim_chges',
               'nb_a_fol', 'nb_b_fol']

ls_columns  = ['id_a', 'id_b', 'distance'] + ls_scalars + ls_freq_std + ls_chges

# BUILD DF PPD

df_ppd = pd.DataFrame(ls_ppd, columns = ls_columns)
df_ppd['pct_same_price'] = df_ppd['nb_same_price'] / df_ppd['nb_spread']
# Create same corner variables
for dist in [500, 750, 1000]:
  df_ppd['sc_{:d}'.format(dist)] = 0
  df_ppd.loc[df_ppd['distance'] <= dist/1000.0, 'sc_{:d}'.format(dist)] = 1
# Add brands and code insee (keep here?)
df_info_sub = df_info[['ci_ardt_1', 'brand_0', 'brand_1', 'brand_2']].copy()
df_info_sub['id_a'] = df_info_sub.index
df_ppd = pd.merge(df_info_sub, df_ppd, on='id_a', how = 'right')
df_info_sub.rename(columns={'id_a': 'id_b'}, inplace = True)
df_ppd = pd.merge(df_info_sub, df_ppd, on='id_b', how = 'right', suffixes=('_b', '_a'))

# BUILD DF RR
ls_index = ['-'.join(ppd[:2]) for ppd in ls_ppd]
df_rr = pd.DataFrame(ls_ar_rrs, index = ls_index, columns = df_prices_ttc.index).T

# OUPUT

# CSV

df_ppd.to_csv(os.path.join(path_dir_built_csv,
                           'df_pair_raw_price_dispersion.csv'),
              encoding = 'utf-8',
              index = False)

df_rr.to_csv(os.path.join(path_dir_built_csv,
                           'df_rank_reversals.csv'),
              float_format= '%.3f',
              encoding = 'utf-8',
              index = 'pair_index')

# JSON

enc_json(dict_rr_lengths, os.path.join(path_dir_built_json,
                                       'dict_rr_lengths.json'))
