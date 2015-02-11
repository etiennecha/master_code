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

pd.set_option('float_format', '{:,.4f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ################
# LOAD DATA
# ################

# LOAD DICT LS COMP
dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# LOAD STABLE MARKETS
ls_dict_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                               'ls_dict_stable_markets.json'))
ls_robust_stable_markets = dec_json(os.path.join(path_dir_built_json,
                                                 'ls_robust_stable_markets.json'))

# 0 is 3km, 1 is 4km, 2 is 5km
ls_stable_markets = [stable_market for nb_sellers, stable_markets\
                       in ls_dict_stable_markets[2].items()\
                          for stable_market in stable_markets]

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

# #########################
# GET DF MARKET DISPERSION
# #########################

# PARAMETERS

df_prices = df_prices_cl
km_bound = 5

# GET MARKETS

ls_markets = get_ls_ls_market_ids(dict_ls_comp, km_bound)
ls_markets_st = get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound)
ls_markets_st_rd = get_ls_ls_market_ids_restricted(dict_ls_comp, km_bound, True)
# todo: add stable markets

# GET MARKET DISPERSION

ls_markets_temp = ls_robust_stable_markets # Market definition chosen here (loop?)
ls_df_market_dispersion = [get_market_price_dispersion(market_ids, df_prices)\
                             for market_ids in ls_markets_temp]
se_mean_price = df_prices.mean(1)

# Can loop to add mean price or add date column and then merge df mean price w/ concatd on date
# Pbm: cv is false (pbmatic division?)
ls_stats = ['range', 'gfs', 'std', 'cv', 'nb_comp']
ls_ls_market_stats = []
ls_market_ref_ids = []
for ls_market_id, df_market_dispersion in zip(ls_markets_temp, ls_df_market_dispersion):
  df_md = df_market_dispersion[(df_market_dispersion['nb_comp'] >= 3) &\
                               (df_market_dispersion['nb_comp_t']/\
                                df_market_dispersion['nb_comp'].astype(float)\
                                  >= 2.0/3)].copy()
  if len(df_market_dispersion) > 50:
    df_md['id'] = ls_market_id[0]
    df_md['price'] = se_mean_price
    df_md['date'] = df_md.index
    ls_ls_market_stats.append([df_md[field].mean()\
                                for field in ls_stats] +\
                              [df_md[field].std()\
                                for field in ls_stats])
    ls_market_ref_ids.append(ls_market_id[0])
ls_columns = ['avg_%s' %field for field in ls_stats]+\
             ['std_%s' %field for field in ls_stats]
df_market_stats = pd.DataFrame(ls_ls_market_stats, ls_market_ref_ids, ls_columns)

print u'\nStats desc: all:'
print u'\n', df_market_stats.describe()

print u'\nStats des: restriction on nb of sellers:'
nb_comp_lim = df_market_stats['avg_nb_comp'].quantile(0.75)
print u'\n', df_market_stats[df_market_stats['avg_nb_comp'] <= nb_comp_lim].describe()

# print df_market_stats[['avg_range', 'avg_gfs', 'avg_std', 'avg_nb_comp']].describe().to_latex()

#df_dispersion = pd.concat(ls_df_market_dispersion, ignore_index = True)
#df_dispersion = df_dispersion[(df_dispersion['nb_comp_t'] >= 3) &\
#                              (df_dispersion['nb_comp_t']/\
#                               df_dispersion['nb_comp'].astype(float) >= 2.0/3)]

# ##############
# STATS DES
# ##############


# #########
# OUPUT
# #########

## CSV
#
#df_ppd.to_csv(os.path.join(path_dir_built_csv,
#                           'df_pair_raw_price_dispersion.csv'),
#              encoding = 'utf-8',
#              index = False)
#
#df_rr.to_csv(os.path.join(path_dir_built_csv,
#                           'df_rank_reversals.csv'),
#              float_format= '%.3f',
#              encoding = 'utf-8',
#              index = 'pair_index')
#
## JSON
#
#enc_json(dict_rr_lengths, os.path.join(path_dir_built_json,
#                                       'dict_rr_lengths.json'))
