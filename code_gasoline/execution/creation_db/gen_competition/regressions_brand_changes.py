#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path_sub
from add_to_path_sub import path_data
from generic_master_price import *
from generic_master_info import *
from functions_string import *
import itertools
import scipy
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import statsmodels.api as sm
import statsmodels.formula.api as smf
import time

path_dir_built_paper = os.path.join(path_data, 'data_gasoline', 'data_built', 'data_paper')

path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_diesel_price = os.path.join(path_dir_built_json, 'master_price_diesel.json')
path_info = os.path.join(path_dir_built_json, 'master_info_diesel.json')
path_ls_ls_competitors = os.path.join(path_dir_built_json, 'ls_ls_competitors.json')
path_ls_tuple_competitors = os.path.join(path_dir_built_json, 'ls_tuple_competitors.json')

path_dir_built_graphs = os.path.join(path_dir_built_paper, 'data_graphs')
path_dir_brand_chges = os.path.join(path_dir_built_graphs, 'brand_changes')

path_dir_source = os.path.join(path_data, 'data_gasoline', 'data_source')
path_dict_brands = os.path.join(path_dir_source, 'data_other', 'dict_brands.json')
path_csv_insee_data = os.path.join(path_dir_source, 'data_other', 'data_insee_extract.csv')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dict_dpts_regions = os.path.join(path_dir_insee, 'dpts_regions', 'dict_dpts_regions.json')

master_price = dec_json(path_diesel_price)
master_info = dec_json(path_info)
ls_ls_competitors = dec_json(path_ls_ls_competitors)
ls_tuple_competitors = dec_json(path_ls_tuple_competitors)
dict_brands = dec_json(path_dict_brands)
dict_dpts_regions = dec_json(path_dict_dpts_regions)

ls_columns = [pd.to_datetime(date) for date in master_price['dates']]
df_price = pd.DataFrame(master_price['diesel_price'], master_price['ids'], ls_columns).T

# #########################
# BRAND CHANGE DETECTION
# #########################

# todo: robustness of price control (no additivity...)
se_mean_price =  df_price.mean(1)
df_price_cl = df_price.apply(lambda x: x - se_mean_price)
window_limit = 20
beg_ind, end_ind = window_limit, len(df_price_cl) - window_limit
ls_se_mean_diffs = []
for day_ind in range(beg_ind, end_ind):
  ls_se_mean_diffs.append(df_price_cl[:day_ind].mean() - df_price_cl[day_ind:].mean())
df_mean_diffs = pd.DataFrame(dict(zip(df_price_cl.index[beg_ind:end_ind], ls_se_mean_diffs))).T
se_argmax = df_mean_diffs.apply(lambda x: x.abs()[~pd.isnull(x)].argmax()\
                                            if not all(pd.isnull(x)) else None)
ls_max = [df_mean_diffs[indiv_id][day] if not pd.isnull(day) else np.nan\
            for indiv_id, day in zip(se_argmax.index, se_argmax.values)]
se_max = pd.Series(ls_max, index = se_argmax.index)
ls_candidates = se_max.index[np.abs(se_max) > 0.04] # consistency with numpy only method...

# Check if corresponds to a change in brand
# todo: exclude highly rigid prices

#dict_std_brands = {v[0]: v for k, v in dict_brands.items()}
dict_chge_brands = {}
for indiv_id, indiv_info in master_price['dict_info'].items():
  ls_brands = [brand_name for brand_name, brand_day_ind in indiv_info['brand']]
  if (len(ls_brands) > 1) and ('TOTAL ACCESS' in ls_brands):
    dict_chge_brands.setdefault('TA', []).append(indiv_id)
  elif (len(ls_brands) > 1) and ('ESSO EXPRESS' in ls_brands):
    dict_chge_brands.setdefault('EE', []).append(indiv_id)
  elif (len(ls_brands) > 1) and ('AVIA' in ls_brands):
    dict_chge_brands.setdefault('AV', []).append(indiv_id)
  elif len(ls_brands) > 1:
    dict_chge_brands.setdefault('OT', []).append(indiv_id)
  else:
    dict_chge_brands.setdefault('NO', []).append(indiv_id)

for chge in ['TA', 'EE', 'AV', 'OT', 'NO']:
  print chge, len([indiv_id for indiv_id in dict_chge_brands[chge] if indiv_id in ls_candidates])

# DD Regression (margin: robustness checks?)
ls_ids_detected_ta = [indiv_id for indiv_id in dict_chge_brands['TA'] if indiv_id in ls_candidates]
indiv_id = ls_ids_detected_ta[0]
chge_day = se_argmax[indiv_id]
# todo: should check that following is not np.nan... else move to next valid and take this one
indiv_ind = master_price['ids'].index(indiv_id)
ls_ls_competitors[indiv_ind].sort(key=lambda x:x[1])
ls_comp_ids = ls_ls_competitors[indiv_ind]

# todo: focus control group, only stations without total access nearby btw
df_price['avg_price'] = se_mean_price

# todo... loop?
comp_id = ls_comp_ids[0][0]
df_dd_1 = df_price[['avg_price']]
df_dd_1= df_dd_1.rename(columns = {'avg_price' : 'price'})
df_dd_1['d_t'] = 0
df_dd_1['d_t'][chge_day:] = 1
df_dd_1['d_x'] = 0
df_dd_1['d_t_x'] = 0
df_dd_1['d_tc_1'] = 0
df_dd_1['d_tc_1']['2012-08-31':'2012-11-30'] = 1
df_dd_1['d_tc_2'] = 0
df_dd_1['d_tc_2']['2012-12-01':'2013-01-11'] = 1

df_dd_2 = df_price[[ls_comp_ids[0][0]]]
df_dd_2= df_dd_2.rename(columns = {ls_comp_ids[0][0] : 'price'})
df_dd_2['d_t'] = 0
df_dd_2['d_t'][chge_day:] = 1
df_dd_2['d_x'] = 1
df_dd_2['d_t_x'] = 0
df_dd_2['d_t_x'][chge_day:] = 1
df_dd_2['d_tc_1'] = 0
df_dd_2['d_tc_1']['2012-08-31':'2012-11-30'] = 1
df_dd_2['d_tc_2'] = 0
df_dd_2['d_tc_2']['2012-12-01':'2013-01-11'] = 1

df_dd = pd.concat([df_dd_1, df_dd_2], ignore_index = True)

print smf.ols('price ~ d_t + d_x + d_t_x', data = df_dd, missing = 'drop').fit().summary()
print smf.ols('price ~ d_t + d_x + d_t_x + d_tc_1 + d_tc_2', data = df_dd, missing = 'drop').fit().summary()

# Among pbms: no date fixed effect hence tax cut can bias data
# e.g. if only observation after shock... will appear more expensive than it is after treatment
# More generally: how to specify properly?
# A priori: FD daily basis obviously not good... maybe vs average (margin?)
