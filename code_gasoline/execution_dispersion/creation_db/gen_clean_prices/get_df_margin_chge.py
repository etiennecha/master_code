#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_dispersion')

path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

# #########################
# LOAD INFO STATIONS
# #########################

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
df_info = df_info[df_info['highway'] != 1]

# #####################################
# DETECT CHANGES IN MARGIN / STATION FE
# #####################################

df_prices = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices.set_index('date', inplace = True)
ls_keep_ids = [id_station for id_station in df_prices.columns if\
                id_station in df_info.index]
df_prices = df_prices[ls_keep_ids]

se_mean_prices = df_prices.mean(1)
df_diff = df_prices.apply(lambda x: x - se_mean_prices, axis = 0)

# find biggest variation of spread vs. national price (improve?)

window_lim = 20
ls_mean_diffs, ls_index = [], []
for per_ind in range(window_lim, len(df_diff) - window_lim):
  ls_index.append(df_diff.index[per_ind]) # todo better
  mean_diff = df_diff.ix[:per_ind].mean(0) - df_diff[per_ind:].mean(0)
  ls_mean_diffs.append(mean_diff)
df_res = pd.concat(ls_mean_diffs, axis=1, keys =ls_index).T
se_res_max = df_res.max(0)
se_res_argmax = df_res.idxmax(0)

df_margin_chge = pd.concat([se_res_max,
                            se_res_argmax],
                           keys = ['value', 'date'],
                           axis = 1)

# ####################
# OVERVIEW OF RESULTS
# ####################

# print df_margin_chge['date'].value_counts()
## 2011-09-24    1027 => pbm w/ window lim: what happens before?
## 2013-05-15     728 => pbm w/ window lim: what happens after?

print u'\nChges detected at beginning:'
print df_margin_chge[df_margin_chge['date'] == '2011-09-24']['value'].describe()

print df_margin_chge[(df_margin_chge['date'] == '2011-09-24') &\
                     (df_margin_chge['value'].abs() > 0.04)].to_string()

print u'\nChges detected at end:'
print df_margin_chge[df_margin_chge['date'] == '2013-05-15']['value'].describe()

print df_margin_chge[(df_margin_chge['date'] == '2013-05-15') &\
                     (df_margin_chge['value'].abs() > 0.04)].to_string()

# ##############################
# IDENTIFICATION OF REAL CHANGES
# ##############################

print u'\nNb of detected chges by size (abs val):'
for x in [0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]:
  print u'Threshold {:.3f}: {:3d}'.format(x,
                                          len(se_res_max[se_res_max.abs() > x]))

criterion = 0.02
print u'\nMost popular dates of change with', criterion, ':'
print df_margin_chge['date']\
        [df_margin_chge['value'].abs() > criterion].value_counts()[0:20]

## todo: graphs to check quality of detection (bad criterion?)
#plt.rcParams['figure.figsize'] = 16, 6
#indiv_id = '62520001'
#ax = df_prices[indiv_id].plot()
#se_mean_prices.plot(ax=ax)
#handles, labels = ax.get_legend_handles_labels()
#ax.legend(handles, [indiv_id, u'mean price'], loc = 1)
## ax.axvline(x = se_res_argmax.ix[indiv_id], color = 'k', ls = 'dashed')
#plt.tight_layout()
#plt.show()

# todo: check when sizable difference (above 0.02?) if also change in brand
# todo: think what to do else... in the end should be two fixed effects

# #############
# OUTPUT
# #############

df_margin_chge.to_csv(os.path.join(path_dir_built_csv,
                                   'df_margin_chge.csv'),
                      index_label = 'id_station',
                      encoding = 'utf-8',
                      float_format='%.4f')
