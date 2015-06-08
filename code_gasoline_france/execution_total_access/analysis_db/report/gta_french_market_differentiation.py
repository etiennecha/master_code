#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_dir_built_graphs = os.path.join(path_dir_built_paper,
                                     'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DF PRICES
# ##############

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# ################
# LOAD DF INFO TA
# ################

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
                                       ['pp_chge_date', 'ta_chge_date'])
df_info_ta.set_index('id_station', inplace = True)

# ##############
# LOAD DF INFO
# ##############

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

# #########################
# DEFINE GROUPS OF STATIONS
# #########################

se_group_vc = df_info['group'].value_counts()
dict_group_ids = {}
ls_rows_groups = []
for group_name in se_group_vc[0:10].index:
  ls_group_ids = list(df_info.index[df_info['group'] == group_name])
  dict_group_ids[group_name] = ls_group_ids
  ls_rows_groups.append(df_prices_ttc[ls_group_ids].iloc[0].describe())
df_groups = pd.concat(ls_rows_groups, axis = 1, keys = se_group_vc[0:10].index)

print df_groups.to_string()

# ############################
# GRAPHS: PRICE HISTOGRAMS
# ############################

print df_prices_ttc.iloc[0].min()
print df_prices_ttc.iloc[0].max()

# First day

for group_name in dict_group_ids.keys()[0:1]:
  bins = np.linspace(1.20, 1.60, 41)
  plt.hist(df_prices_ttc.iloc[10].values,
           bins, alpha=0.5, label='All prices', color = 'g')
  plt.hist(df_prices_ttc[dict_group_ids[group_name]].iloc[10].values,
           bins, alpha=0.5, label='%s prices' %group_name, color = 'b')
  plt.xlim(1.20, 1.60)
  plt.legend()
  plt.show()
