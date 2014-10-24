#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

# #####################
# LOAD INFO AND PRICES
# #####################

df_info = pd.read_csv(os.path.join(path_dir_built_csv,
                                           'df_station_info.csv'),
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

# Active gas stations? Pick arbitrary day for now
#df_info = df_info[(~pd.isnull(df_info['start'])) &\
#                  (~pd.isnull(df_info['end']))])
#df_info = df_info[(df_info['start'] <= '2012-06-01') &\
#                  (df_info['end'] >= '2012-06-01')]
df_info = df_info[df_info['highway'] != 1]

ls_ids_ctl_fra = df_info.index[(df_info['start'] <= '2011-09-05') &\
                               (df_info['end'] >= '2013-06-03') &\
                               (df_info['dilettante'] <= 10) &\
                               (df_info['dpt'] != 'Corse') &\
                               (pd.isnull(df_info['brand_1']))]

# Work with prices before tax
df_prices = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht.csv'),
                        parse_dates = ['date'])
df_prices.set_index('date', inplace = True)

# ###########################################
# COMPARE ZONE AFFECTED BY CHGE VS. CONTROLS
# ###########################################

# PBM: CHGE TO TA DOES NOT IMPLY CHGE OF PRICE
# LOAD DF_TA or DF_BRAND/PRICE_CHGE (todo: create) to have more info

# Total Access in brands... but could no more be (check by concatenating)
df_info['TA'] = 0
df_info.loc[(df_info['brand_0'] == 'TOTAL_ACCESS') |\
            (df_info['brand_1'] == 'TOTAL_ACCESS') |\
            (df_info['brand_2'] == 'TOTAL_ACCESS'),
            'TA'] = 1
print u'Nb Total Access (assume no exit of brand nor dupl.):', df_info['TA'].sum()

# Chge to Total Access recorded
df_info['TA_chge'] = 0
df_info.loc[(df_info['brand_0'] != 'TOTAL_ACCESS') &\
            (df_info['brand_1'] == 'TOTAL_ACCESS'),
            'TA_chge'] = 1
df_info.loc[(df_info['brand_1'] != 'TOTAL_ACCESS') &\
            (df_info['brand_2'] == 'TOTAL_ACCESS'),
            'TA_chge'] = 1
print u'Chge to Total Access:', df_info['TA_chge'].sum()

# Keep non TA stations active over the whole period in both groups
ls_col_disp = ['name', 'adr_street', 'adr_city', # 'start', 'end',
               'brand_0', 'day_0', 'brand_1', 'day_1', 'brand_2', 'day_2']

# TA station group (just check)
# only one really chges prices (?) => need detection of price policy changes
ls_ids_ta = df_info.index[(df_info['TA'] == 1) &\
                          (df_info['ci_1'] == '13001')]
print df_info.ix[ls_ids_ta][ls_col_disp].to_string()
#df_prices[ls_ids_ta].plot()

# Treated group
ls_ids_treated = df_info.index[(df_info['start' ] <= '2011-09-05') &\
                               (df_info['end'] >= '2013-06-03') &\
                               (df_info['dilettante'] == 0) &\
                               (df_info['TA'] == 0) &\
                               (df_info['ci_1'] == '13001') &\
                               (pd.isnull(df_info['brand_1']))]
print df_info.ix[ls_ids_treated][ls_col_disp].to_string()

# Control group
ls_ids_control = df_info.index[(df_info['start' ] <= '2011-09-05') &\
                               (df_info['end'] >= '2013-06-03') &\
                               (df_info['dilettante'] == 0) &\
                               (df_info['TA'] == 0) &\
                               (df_info['dpt'] == '13') &\
                               (df_info['ci_1'] != '75056') &\
                               (pd.isnull(df_info['brand_1']))]
print df_info.ix[ls_ids_control][ls_col_disp].to_string()

se_diff = df_prices[ls_ids_ctl_fra].mean(1) - df_prices[ls_ids_treated].mean(1)

# Plot ctrl group vs treated
ax = df_prices[ls_ids_treated].mean(1).plot(label = 'treated', legend = True)
df_prices[ls_ids_control].mean(1).plot(ax = ax, label = 'control', legend = True)
df_prices[ls_ids_ta].mean(1).plot(ax = ax, label = 'ta', legend = True)

## Check if corresponds to a change in brand
## todo: exclude highly rigid prices
#
## DD Regression (margin: robustness checks?)
#ls_ids_detected_ta = [indiv_id for indiv_id in dict_chge_brands['TA']\
#                        if indiv_id in ls_candidates]
#indiv_id = ls_ids_detected_ta[0]
#chge_day = se_argmax[indiv_id]
## todo: should check that following is not np.nan... else move to next valid and take this one
#indiv_ind = master_price['ids'].index(indiv_id)
#ls_ls_competitors[indiv_ind].sort(key=lambda x:x[1])
#ls_comp_ids = ls_ls_competitors[indiv_ind]
#
## todo: focus control group, only stations without total access nearby btw
#df_price['avg_price'] = se_mean_price
#
## todo... loop?
#comp_id = ls_comp_ids[0][0]
#df_dd_1 = df_price[['avg_price']]
#df_dd_1= df_dd_1.rename(columns = {'avg_price' : 'price'})
#df_dd_1['d_t'] = 0
#df_dd_1['d_t'][chge_day:] = 1
#df_dd_1['d_x'] = 0
#df_dd_1['d_t_x'] = 0
#df_dd_1['d_tc_1'] = 0
#df_dd_1['d_tc_1']['2012-08-31':'2012-11-30'] = 1
#df_dd_1['d_tc_2'] = 0
#df_dd_1['d_tc_2']['2012-12-01':'2013-01-11'] = 1
#
#df_dd_2 = df_price[[ls_comp_ids[0][0]]]
#df_dd_2= df_dd_2.rename(columns = {ls_comp_ids[0][0] : 'price'})
#df_dd_2['d_t'] = 0
#df_dd_2['d_t'][chge_day:] = 1
#df_dd_2['d_x'] = 1
#df_dd_2['d_t_x'] = 0
#df_dd_2['d_t_x'][chge_day:] = 1
#df_dd_2['d_tc_1'] = 0
#df_dd_2['d_tc_1']['2012-08-31':'2012-11-30'] = 1
#df_dd_2['d_tc_2'] = 0
#df_dd_2['d_tc_2']['2012-12-01':'2013-01-11'] = 1
#
#df_dd = pd.concat([df_dd_1, df_dd_2], ignore_index = True)
#
#print smf.ols('price ~ d_t + d_x + d_t_x',
#              data = df_dd,
#              missing = 'drop').fit().summary()
#
#print smf.ols('price ~ d_t + d_x + d_t_x + d_tc_1 + d_tc_2',
#              data = df_dd,
#              missing = 'drop').fit().summary()
#
## Among pbms: no date fixed effect hence tax cut can bias data
## e.g. if only observation after shock... will appear more expensive than it is after treatment
## More generally: how to specify properly?
## A priori: FD daily basis obviously not good... maybe vs average (margin?)
#
#
## #########################
## BRAND CHANGE DETECTION
## #########################
#
## todo: robustness of price control (no additivity...)
#se_mean_price =  df_price.mean(1)
#df_price_cl = df_price.apply(lambda x: x - se_mean_price)
#window_limit = 20
#beg_ind, end_ind = window_limit, len(df_price_cl) - window_limit
#ls_se_mean_diffs = []
#for day_ind in range(beg_ind, end_ind):
#  ls_se_mean_diffs.append(df_price_cl[:day_ind].mean() - df_price_cl[day_ind:].mean())
#df_mean_diffs = pd.DataFrame(dict(zip(df_price_cl.index[beg_ind:end_ind], ls_se_mean_diffs))).T
#se_argmax = df_mean_diffs.apply(lambda x: x.abs()[~pd.isnull(x)].argmax()\
#                                            if not all(pd.isnull(x)) else None)
#ls_max = [df_mean_diffs[indiv_id][day] if not pd.isnull(day) else np.nan\
#            for indiv_id, day in zip(se_argmax.index, se_argmax.values)]
#se_max = pd.Series(ls_max, index = se_argmax.index)
#ls_candidates = se_max.index[np.abs(se_max) > 0.04] # consistency with numpy only method...
