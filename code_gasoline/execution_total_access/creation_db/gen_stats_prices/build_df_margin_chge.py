#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper_total_access')
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

# Active gas stations? Pick arbitrary day for now
#df_info = df_info[(~pd.isnull(df_info['start'])) &\
#                  (~pd.isnull(df_info['end']))])
#df_info = df_info[(df_info['start'] <= '2012-06-01') &\
#                  (df_info['end'] >= '2012-06-01')]
df_info = df_info[df_info['highway'] != 1]

# #####################################
# POLICY PRICE CHANGE
# #####################################

df_prices = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices.set_index('date', inplace = True)
ls_keep_ids = [id_station for id_station in df_prices.columns if\
                id_station in df_info.index]
df_prices = df_prices[ls_keep_ids]

se_mean_prices = df_prices.mean(1)
df_diff = df_prices.apply(lambda x: x - se_mean_prices, axis = 0)

# FIND BIG DIFFERENCE IN DIFF VS. NATIONAL PRICE (BEFORE TAX)

window_lim = 20
ls_mean_diffs, ls_index = [], []
for per_ind in range(window_lim, len(df_diff) - window_lim):
  ls_index.append(df_diff.index[per_ind]) # todo better
  mean_diff = df_diff.ix[:per_ind].mean(0) - df_diff[per_ind:].mean(0)
  ls_mean_diffs.append(mean_diff)
df_res = pd.concat(ls_mean_diffs, axis=1, keys =ls_index).T
se_res_max = df_res.max(0)
se_res_argmax = df_res.idxmax(0)

print u'\nNb of detected chges:'
for x in [0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]:
  print 'Threshold %s', x, ':', len(se_res_max[se_res_max.abs() > x])

# START WITH STRICT CRITERION

df_margin_chge = pd.concat([se_res_max,
                            se_res_argmax],
                           keys = ['value', 'date'],
                           axis = 1)

print df_margin_chge['date'].value_counts()
# 2011-09-24    1027 => pbm w/ window lim: what happens before?
# 2013-05-15     728 => pbm w/ window lim: what happens after?

print df_margin_chge[df_margin_chge['date'] == '2011-09-24']['value'].describe()
print df_margin_chge[df_margin_chge['date'] == '2013-05-15']['value'].describe()

# todo: display price graphs
print df_margin_chge[(df_margin_chge['date'] == '2011-09-24') &\
                     (df_margin_chge['value'].abs() > 0.04)].to_string()

print df_margin_chge[(df_margin_chge['date'] == '2013-05-15') &\
                     (df_margin_chge['value'].abs() > 0.04)].to_string()

#plt.rcParams['figure.figsize'] = 16, 6
#indiv_id = '62520001'
#ax = df_prices[indiv_id].plot()
#se_mean_prices.plot(ax=ax)
#handles, labels = ax.get_legend_handles_labels()
#ax.legend(handles, [indiv_id, u'mean price'], loc = 1)
## ax.axvline(x = se_res_argmax.ix[indiv_id], color = 'k', ls = 'dashed')
#plt.tight_layout()
#plt.show()

# POLICY PRICE CHGES (todo: merge with brand chges and perform analysis!)
criterion = 0.04
print df_margin_chge['date'][df_margin_chge['value'].abs() > criterion].value_counts()

df_margin_chge.to_csv(os.path.join(path_dir_built_csv,
                                   'df_margin_chge.csv'),
                      index_label = 'id_station',
                      encoding = 'utf-8',
                      float_format='%.4f')
