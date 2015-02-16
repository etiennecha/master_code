#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_dir_built_json = os.path.join(path_dir_built_paper,
                                  u'data_json')

path_dir_built_graphs = os.path.join(path_dir_built_paper,
                                     'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.3f}'.format)
#format_float_int = lambda x: '{:10,.0f}'.format(x)
#format_float_float = lambda x: '{:10,.2f}'.format(x)

# #############
# LOAD DATA
# #############

df_info_ta = pd.read_csv(os.path.join(path_dir_built_csv,
                                      'df_info_ta_fixed.csv'),
                         encoding = 'utf-8',
                         dtype = {'id_station' : str,
                                  'adr_zip' : str,
                                  'adr_dpt' : str,
                                  'ci_1' : str,
                                  'ci_ardt_1' :str,
                                  'ci_2' : str,
                                  'ci_ardt_2' : str,
                                  'dpt' : str},
                         parse_dates = [u'day_%s' %i for i in range(4)] +\
                                       ['pp_chge_date', 'ta_chge_date',
                                        'date_beg', 'date_end'])
df_info_ta.set_index('id_station', inplace = True)

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
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

df_info = df_info[df_info['highway'] != 1]

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# #############
# LOAD DATA
# #############

df_coeffs = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_coeffs_ttac.csv'),
                        dtype = {'id_station' : str,
                                 'id_elf':  str},
                        encoding = 'utf-8')

ls_pct = [0.1, 0.25, 0.5, 0.75, 0.9]

df_coeffs = df_coeffs[df_coeffs['tval'].abs() >= 1.96]
df_coeffs['treatment'] = df_coeffs['treatment'] * 100

# desc by group_type
ls_rows_group_type = [df_coeffs['treatment'].describe(percentiles = ls_pct)]
for group_type in ['SUP', 'OIL', 'IND']:
  ls_rows_group_type.append(df_coeffs[df_coeffs['group_type'] ==\
                                        group_type]['treatment'].describe(percentiles = ls_pct))
df_group_type = pd.concat(ls_rows_group_type,
                          axis = 1,
                          keys = ['All', 'SUP', 'OIL', 'IND'])

print u'\nDesc of treatment estimates by group type'
print df_group_type.to_latex()

# desc by group
ls_rows_group = []
for group in df_coeffs['group'].unique():
  ls_rows_group.append(df_coeffs[df_coeffs['group'] ==\
                                  group]['treatment'].describe(percentiles = ls_pct))
df_group = pd.concat(ls_rows_group, axis = 1, keys = df_coeffs['group'].unique())

print u'\nDesc of treatment estimates by group:'
print df_group.to_string()

# tails
df_coeffs.sort('treatment', inplace = True)
