#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built,
                                  u'data_csv')
path_dir_built_json = os.path.join(path_dir_built,
                                   u'data_json')

path_dir_built_ta = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_total_access')
path_dir_built_ta_json = os.path.join(path_dir_built_ta, 
                                      'data_json')
path_dir_built_ta_csv = os.path.join(path_dir_built_ta, 
                                     'data_csv')
path_dir_built_ta_graphs = os.path.join(path_dir_built_ta, 
                                        'data_graphs')

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# #############
# LOAD DATA
# #############

df_info_ta = pd.read_csv(os.path.join(path_dir_built_csv,
                                      'df_info_ta.csv'),
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

# ###################
# FILTER DATA
# ###################

ls_keep_info = list(df_info[df_info['highway'] != 1].index)
ls_keep_stats = list(df_station_stats[(df_station_stats['nb_chge'] >= 5) &\
                                      (df_station_stats['pct_chge'] >= 0.03)].index)
ls_keep_ids = list(set(ls_keep_info).intersection(set(ls_keep_stats)))

ls_ta_ids = list(df_info_ta.index)

dict_ls_ta_comp = {}
for id_station, ls_comp in dict_ls_comp.items():
  ls_ta_comp = [(comp_id, distance) for comp_id, distance in ls_comp\
                                    if comp_id in ls_ta_ids]
  dict_ls_ta_comp[id_station] = ls_ta_comp

ls_control_ids = []
for id_station, ls_ta_comp in dict_ls_ta_comp.items():
  if (id_station in ls_keep_ids) and\
     ((not ls_ta_comp) or\
      (ls_ta_comp[0][1] > 10)):
    ls_control_ids.append(id_station)

# ##########################################
# LONG PANEL: COMP OF TOTAL => TOTAL ACCESS
# ##########################################

df_prices = df_prices_ttc

ls_ta_chge_ids = list(df_info_ta.index[(df_info_ta['pp_chge'] >= 0.05) &\
                                       (~pd.isnull(df_info_ta['date_beg']))])

#df_tta_lg_control = pd.DataFrame(df_prices[ls_control_ids].mean(1),
#                             df_prices.index, ['price'])
#df_tta_lg_control['time'] = df_tta_lg_control.index

ls_df_lg_ttac = []
for id_station, ls_ta_comp in dict_ls_ta_comp.items()[:5000]:
  if (id_station in ls_keep_ids) and\
     (df_info.ix[id_station]['group'] != 'TOTAL'):
    # Need to have pp change and dates of transition
    ls_ta_comp = [(comp_id, distance) for comp_id, distance in ls_ta_comp\
                                      if comp_id in ls_ta_chge_ids]
    # todo: refine if several (first date? or closest?)
    if (ls_ta_comp) and\
       (ls_ta_comp[0][1] <= 3):
      id_ta = ls_ta_comp[0][0]
      distance = ls_ta_comp[0][1]
      date_beg = df_info_ta.ix[id_ta]['date_beg']
      date_end = df_info_ta.ix[id_ta]['date_end']
      df_lg_ttac = pd.DataFrame(df_prices[id_station].values,
                                df_prices.index, ['price'])
      df_lg_ttac.loc[date_beg:date_end, 'price'] = np.nan
      df_lg_ttac['time'] = df_lg_ttac.index
      # df_lg_ttac['time'] = df_lg_ttac['time'].apply(lambda x: x.strftime('%Y-%m-%d'))
      df_lg_ttac['id_station'] = id_station
      df_lg_ttac['treatment'] = 0
      df_lg_ttac.loc[date_end:, 'treatment'] = 1
      df_lg_ttac['group'] = df_info.ix[id_station]['group']
      df_lg_ttac['group_type'] = df_info.ix[id_station]['group_type']
      df_lg_ttac['reg'] = df_info.ix[id_station]['reg']
      df_lg_ttac['distance'] = distance
      ls_df_lg_ttac.append(df_lg_ttac)

df_lg_ttac = pd.concat(ls_df_lg_ttac, ignore_index = True)
df_lg_ttac['time'] = df_lg_ttac['time'].apply(lambda x: x.strftime('%Y-%m-%d'))

#df_lg_ttac.to_csv(os.path.join(path_dir_built_ta_csv,
#                              'df_long_ttac.csv'),
#                 encoding = 'latin-1',
#                 index = False)

# ########################################
# LONG PANEL: COMP OF ELF => TOTAL ACCESS
# ########################################

ls_tta_ids = list(df_info_ta.index[(df_info_ta['brand_0'] == 'TOTAL')])
ls_elf_ids = list(df_info_ta.index[(df_info_ta['brand_0'] == 'ELF')])

ls_df_lg_elfc = []
for id_station, ls_comp in dict_ls_comp.items():
  # station should have no ex Total Total Access competitor
  if any([comp_id in ls_tta_ids for comp_id, distance in ls_comp]):
    pass
  else:
    # need a close elf
    ls_elf_comp = [(comp_id, distance) for comp_id, distance in ls_comp
                    if (comp_id in ls_elf_ids) and (distance <= 3)]
    if ls_elf_comp:
      id_temp = ls_elf_comp[0][0]
      distance = ls_elf_comp[0][1]
      date_chge = df_info_ta.ix[id_ta]['day_1']
      date_beg_nan = df_info_ta.ix[id_temp]['day_1'] - pd.Timedelta(days = 10)
      date_end_nan = df_info_ta.ix[id_temp]['day_1'] + pd.Timedelta(days = 10)
      df_lg_elfc = pd.DataFrame(df_prices[id_station].values,
                                df_prices.index, ['price'])
      df_lg_elfc.loc[date_beg_nan:date_end_nan, 'price'] = np.nan
      df_lg_elfc['time'] = df_lg_elfc.index
      # df_lg_elfc['time'] = df_lg_elfc['time'].apply(lambda x: x.strftime('%Y-%m-%d'))
      df_lg_elfc['id_station'] = id_station
      df_lg_elfc['treatment'] = 0
      df_lg_elfc.loc[date_end_nan:, 'treatment'] = 1
      df_lg_elfc['group'] = df_info.ix[id_station]['group']
      df_lg_elfc['group_type'] = df_info.ix[id_station]['group_type']
      df_lg_elfc['reg'] = df_info.ix[id_station]['reg']
      df_lg_elfc['distance'] = distance
      ls_df_lg_elfc.append(df_lg_elfc)

df_lg_elfc = pd.concat(ls_df_lg_elfc, ignore_index = True)
df_lg_elfc['time'] = df_lg_elfc['time'].apply(lambda x: x.strftime('%Y-%m-%d'))

#df_lg_elfc.to_csv(os.path.join(path_dir_built_ta_csv,
#                              'df_long_elfc.csv'),
#                 encoding = 'latin-1',
#                 index = False)

# todo: need to define dates...
# todo: need to make sure no Total-Total Access around
