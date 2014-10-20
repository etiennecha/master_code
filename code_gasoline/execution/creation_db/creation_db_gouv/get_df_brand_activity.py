#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matching_insee import *
import pprint

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')

# ######################
# LOAD GAS STATION DATA
# ######################

master_price_raw = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel_raw.json'))
master_price = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel.json'))
master_info_raw = dec_json(os.path.join(path_dir_built_json, 'master_info_diesel_raw.json'))
master_info = dec_json(os.path.join(path_dir_built_json, 'master_info_diesel.json'))

dict_brands = dec_json(os.path.join(path_dir_source, 'data_other', 'dict_brands.json'))

# todo: Work with master_price_raw or master_price ?
# todo: probably need intermediate stage (before duplicate reconciliation)

# ##################
# BUILD DF ACTIVITY
# ##################

# todo: refactor / replace?
ls_ls_price_durations = get_price_durations(master_price['diesel_price'])
# ls_ls_price_variations = get_price_variations_nan(ls_ls_price_durations)
ls_start_end, ls_none, dict_dilettante =  get_overview_reporting_bis(master_price['diesel_price'],
                                                                     master_price['dates'],
                                                                     master_price['missing_dates'])

ls_index, ls_rows_activity = [], []
for i, indiv_id in enumerate(master_price['ids']):
  ls_index.append(indiv_id)
  ls_rows_activity.append(list(ls_start_end[i])+\
                          [len(dict_dilettante.get(i, []))])

# todo: change to dates ?
df_activity = pd.DataFrame(ls_rows_activity,
                           index = ls_index,
                           columns = ['start', 'end', 'dilettante'])

# ###############
# BUILD DF BRANDS
# ###############

# Harmonizes brands (softly though so far)
for indiv_id, indiv_info in master_price['dict_info'].items():
  if indiv_info['brand']:
    master_price['dict_info'][indiv_id]['brand'] = [[get_str_no_accent_up(brand), day_ind]\
                                                       for brand, day_ind in indiv_info['brand']]

# Resets brand starting date consistent with price series
ls_to_be_chged = []
for i, (start, end) in enumerate(ls_start_end):
  if start != master_price['dict_info'][master_price['ids'][i]]['brand'][0][1]:
    ls_to_be_chged.append(i)
    if start:
      master_price['dict_info'][master_price['ids'][i]]['brand'][0][1] = start
      
# Adds brand_std to dict_info in master_price and create corresponding dict_std_brands:
dict_std_brands = {v[0]: v for k, v in dict_brands.items()}
for indiv_id, indiv_info in master_price['dict_info'].items():
  ls_brand_std = [[dict_brands[name][0], day_ind] for name, day_ind in indiv_info['brand']]
  i = 1 
  while i < len(ls_brand_std):
    if ls_brand_std[i][0] == ls_brand_std[i-1][0]:
      del(ls_brand_std[i])
    else:
      i += 1
  master_price['dict_info'][indiv_id]['brand_std'] = ls_brand_std

# fix what seems to be mistakes

master_price['dict_info']['78150001']['brand'] =\
    [[u'ELF', 0], [u'TOTAL ACCESS', 30]]
master_price['dict_info']['78150001']['brand_std'] =\
    [[u'ELF', 0], [u'TOTAL ACCESS', 30]]

master_price['dict_info']['86360003']['brand'] =\
   [[u'TOTAL', 0], [u'TOTAL ACCESS', 457]]
master_price['dict_info']['86360003']['brand_std'] =\
   [[u'TOTAL', 0], [u'TOTAL ACCESS', 457]]

# could have been created by me (TA or duplicate merge?)

dict_len_brands = {}
ls_index, ls_rows_brands = [], []
for indiv_id, indiv_info in master_price['dict_info'].items():
  dict_len_brands.setdefault(len(indiv_info['brand_std']), []).append(indiv_id)
  ls_index.append(indiv_id)
  ls_rows_brands.append([x for ls_x in indiv_info['brand_std'] for x in ls_x])

#print dict_len_brands.keys()
ls_ls_columns = [['brand_%s' %i, 'day_%s' %i]\
                   for i in range(np.max(dict_len_brands.keys()))]
ls_columns = [column for ls_columns in ls_ls_columns for column in ls_columns]

df_brands = pd.DataFrame(ls_rows_brands,
                         index = ls_index,
                         columns = ls_columns)

# check '26270001' : 'AUTRE_IND' => 'INDEPENDANT' : why?

# #######################
# BUILD DF BRAND ACTIVITY
# #######################

df_brand_activity = pd.merge(df_activity, df_brands, left_index = True, right_index = True)

for field in ['start', 'end', 'day_0', 'day_1', 'day_2']:
  df_brand_activity[field] = df_brand_activity[field].apply(\
                               lambda x: master_price['dates'][int(x)]\
                                           if not pd.isnull(x) else x)
  df_brand_activity[field] = pd.to_datetime(df_brand_activity[field],
                                            format = '%Y%m%d',
                                            coerce = True)

#for year in ['2011', '2012', '2013']:
#  print u'Nb starting after %s:' %year,\
#        len(df_brand_activity[df_brand_activity['start'] > year])

# todo: group and brand

# OUTPUT TO CSV
df_brand_activity.to_csv(os.path.join(path_dir_built_csv,
                                      'df_brand_activity.csv'),
                         index_label = 'id_station',
                         float_format= '%.3f',
                         encoding = 'utf-8')
