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

# ################
# LOAD DATA
# ################

# LOAD COMPETITOR PAIRS
ls_comp_pairs = dec_json(os.path.join(path_dir_built_json,
                                      'ls_comp_pairs.json'))

# LOAD DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
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

# ######################
# GET DF PAIR DISPERSION
# ######################

# can accomodate both ttc prices (raw prices) or cleaned prices
df_prices = df_prices_ttc
km_bound = 3
diff_bound = 0.02

ls_keep_ids = set(df_prices_cl.columns).intersection(set(df_prices_ttc.columns))
ls_comp_pairs = [(indiv_id, competitor_id, distance)\
                   for (indiv_id, competitor_id, distance) in ls_comp_pairs if\
                     (indiv_id in ls_keep_ids) and (competitor_id in ls_keep_ids)]


# LOOP TO GENERATE PRICE DISPERSION STATS

start = time.clock()
ls_rows_ppd = []
ls_pair_index = []
ls_ar_rrs = []
dict_rr_lengths = {}
for (indiv_id, comp_id, distance) in ls_comp_pairs:
  if (distance <= km_bound):
    se_prices_1 = df_prices[indiv_id]
    se_prices_2 = df_prices[comp_id]
    abs_avg_spread_ttc = np.abs((df_prices_ttc[indiv_id] - df_prices_ttc[comp_id]).mean())
    ls_comp_pd = get_pair_price_dispersion(se_prices_1.values,
                                           se_prices_2.values, light = False)
    ls_rows_ppd.append([indiv_id, competitor_id, distance] +\
                       ls_comp_pd[0] +\
                       [abs_avg_spread_ttc] +\
                       get_ls_standardized_frequency(ls_comp_pd[3][0]))
    pair_index = '-'.join([indiv_id, competitor_id])
    ls_pair_index.append(pair_index)
    ls_ar_rrs.append(ls_comp_pd[2][1])
    dict_rr_lengths[pair_index] = ls_comp_pd[3][0]
print 'Loop: rank reversals',  time.clock() - start

# BUILD DF PAIR PRICE DISPERSION (PPD)

ls_scalar_cols  = ['nb_spread', 'nb_same_price', 'nb_a_cheaper', 'nb_b_cheaper', 
                   'nb_rr', 'pct_rr', 'avg_abs_spread_rr', 'med_abs_spread_rr',
                   'avg_abs_spread', 'avg_spread', 'std_spread']

ls_freq_std_cols = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

ls_columns  = ['id_a', 'id_b', 'distance'] +\
              ls_scalar_cols +\
              ['abs_avg_spread_ttc'] +\
              ls_freq_std_cols

df_ppd = pd.DataFrame(ls_rows_ppd, columns = ls_columns)

# CREATE SAME CORNER VARIABLE

for dist in [500, 750, 1000]:
  df_ppd['sc_{:d}'.format(dist)] = 0
  df_ppd.loc[df_ppd['distance'] <= dist/1000.0, 'sc_{:d}'.format(dist)] = 1

# ADD BRANDS AND CODE INSEE (MOVE)

df_info_sub = df_info[['ci_ardt_1', 'brand_0', 'brand_1', 'brand_2']].copy()
df_info_sub['id_a'] = df_info_sub.index
df_ppd = pd.merge(df_info_sub, df_ppd, on='id_a', how = 'right')
df_info_sub.rename(columns={'id_a': 'id_b'}, inplace = True)

df_ppd = pd.merge(df_info_sub,
                  df_ppd,
                  on='id_b',
                  how = 'right',
                  suffixes=('_b', '_a'))

# BUILD DF RANK REVERSALS

ls_index = ['-'.join(ppd[:2]) for ppd in ls_rows_ppd]
df_rr = pd.DataFrame(ls_ar_rrs,
                     index = ls_index,
                     columns = df_prices_ttc.index).T

# ##############
# STATS DES
# ##############

ls_disp_ppd = ['id_a', 'id_b', 'distance'] +\
              ls_scalar_cols +\
              ['abs_avg_spread_ttc']

print df_ppd[ls_disp_ppd][0:10].to_string()

# #########
# OUPUT
# #########

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
