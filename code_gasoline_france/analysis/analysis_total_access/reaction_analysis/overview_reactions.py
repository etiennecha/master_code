#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')

path_dir_built_csv = os.path.join(path_dir_built,
                                  u'data_csv')

path_dir_built_ta = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_total_access')

path_dir_built_ta_json = os.path.join(path_dir_built_ta, 
                                      'data_json')

path_dir_built_ta_csv = os.path.join(path_dir_built_ta, 
                                     'data_csv')

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

# #########
# LOAD DATA
# #########

# DF STATION INFO

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
                               'dpt' : str},
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
df_info.set_index('id_station', inplace = True)
df_info = df_info[df_info['highway'] != 1]

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices = df_prices_ttc

# DF TOTAL ACCESS

str_ta_ext = '_5km_dist_order'

df_ta = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                 'df_total_access{:s}.csv'.format(str_ta_ext)),
                              dtype = {'id_station' : str,
                                       'id_total_ta' : str,
                                       'id_elf_ta' : str,
                                       'ci_1' : str,
                                       'ci_ardt_1' : str},
                              encoding = 'utf-8',
                              parse_dates = ['start', 'end',
                                             'ta_date_beg',
                                             'ta_date_end',
                                             'date_min_total_ta',
                                             'date_max_total_ta',
                                             'date_min_elf_ta',
                                             'date_max_elf_ta'])
df_ta.set_index('id_station', inplace = True)

# DF REG RES

str_ta_ext = '_5km_dist_order'
df_res = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                 'df_res_indiv{:s}.csv'.format(str_ta_ext)),
                     encoding = 'utf-8',
                     dtype = {'id_station' : str})
df_res.set_index('id_station', inplace = True)

# ##########
# OVERVIEW
# ##########

df_res = pd.merge(df_res,
                  df_ta[['name',
                         'adr_street',
                         'adr_city',
                         'ci_1',
                         'ci_ardt_1',
                         'reg',
                         'dpt',
                         'group',
                         'brand_last',
                         'group_last',
                         'group_type_last',
                         'id_total_ta',
                         'dist_total_ta',
                         'id_elf_ta',
                         'dist_elf_ta']],
                  left_index = True,
                  right_index = True,
                  how = 'left')

# todo: graphs of reactions above 0.03 or 0.04 cents
# todo: check share supermarkets vs. oil/indep
# todo: check reaction vs. station fe (todo elsewhere)
# todo: check closest competitor(s) of total access systematically? (based on pair price stats)
