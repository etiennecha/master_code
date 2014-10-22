#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data, u'data_gasoline', u'data_built', u'data_paper')
path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built_paper, 'data_json')

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
df_info = df_info[(df_info['start'] <= '2012-06-01') &\
                  (df_info['end'] >= '2012-06-01')]

# Total Access in brands... but could no more be (check by concatenating)
df_info['TA'] = 0
df_info['TA'][(df_info['brand_0'] == 'TOTAL_ACCESS') |\
              (df_info['brand_1'] == 'TOTAL_ACCESS') |\
              (df_info['brand_2'] == 'TOTAL_ACCESS')] = 1
print u'Nb Total Access (assume no exit of brand nor dupl.):', df_info['TA'].sum()

# Chge to Total Access recorded
df_info['TA_chge'] = 0
df_info['TA_chge'][(df_info['brand_0'] != 'TOTAL_ACCESS') &\
                   (df_info['brand_1'] == 'TOTAL_ACCESS')] = 1
df_info['TA_chge'][(df_info['brand_1'] != 'TOTAL_ACCESS') &\
                   (df_info['brand_2'] == 'TOTAL_ACCESS')] = 1
print u'Chge to Total Access:', df_info['TA_chge'].sum()

# #########################
# TOTAL ACCESS WITHIN AREA
# #########################

area = 'ci_1'
df_dpt_ta = df_info[[area, 'TA']].groupby(area).agg([sum])['TA']
df_dpt_ta.rename(columns = {'sum': 'TA_%s' %area}, inplace = True)

df_ta = pd.merge(df_dpt_ta, df_info,
                 left_index = True, right_on = area,
                 how = 'outer')

# Check % of TA within area
df_dpt_ta['Nb_%s' %area] = df_info[area].value_counts() # keep active only...
df_dpt_ta['Pct_TA'] = df_dpt_ta['TA_%s' %area] / df_dpt_ta['Nb_%s' %area]
df_dpt_ta.sort('Nb_%s' %area, ascending = False, inplace = True)

# Need to adapt if a lot of 0
pd.set_option('float_format', '{:,.2f}'.format)
ls_dpt_ta_col_disp = ['Nb_%s' %area, 'TA_%s' %area, 'Pct_TA']

print '\nNb of areas:', len(df_dpt_ta)
nb_areas_no_TA = len(df_dpt_ta[df_dpt_ta['TA_%s' %area] == 0])
print 'Nb of areas with 0 TA:', nb_areas_no_TA

if nb_areas_no_TA > 10:
  print '\nAreas with TA:'
  print df_dpt_ta[ls_dpt_ta_col_disp][df_dpt_ta['TA_%s' %area] != 0].to_string()
  print '\nTop 50 biggest areas in terms of general count:'
  print df_dpt_ta[ls_dpt_ta_col_disp][0:50].to_string()
else:
  print '\nAll areas:'
  print df_dpt_ta[ls_dpt_ta_col_disp].to_string()

# Need ids of TAs within areas to find dates

# #####################################
# TOTAL ACCESS WITH POLICY PRICE CHANGE
# #####################################

master_price_raw = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel_raw.json'))
master_price = dec_json(os.path.join(path_dir_built_json, 'master_price_diesel.json'))
master_info_raw = dec_json(os.path.join(path_dir_built_json, 'master_info_diesel_raw.json'))
master_info = dec_json(os.path.join(path_dir_built_json, 'master_info_diesel.json'))

# LOAD df_prices
df_prices = pd.DataFrame(master_price['diesel_price'],
                         index = master_price['ids'],
                         columns = [pd.to_datetime(x) for x in master_price['dates']]).T
se_mean_prices = df_prices.mean(1)
df_diff = df_prices.apply(lambda x: x - se_mean_prices, axis = 0)

# FIND BIG DIFFERENCE IN DIFF VS. NATIONAL PRICE
# todo: take tax into account to avoid TICPE effect

window_lim = 20
ls_mean_diffs, ls_index = [], []
for per_ind in range(window_lim, len(df_diff) - window_lim):
  ls_index.append(df_diff.index[per_ind]) # todo better
  mean_diff = df_diff.ix[:per_ind].mean(0) - df_diff[per_ind:].mean(0)
  ls_mean_diffs.append(mean_diff)
df_res = pd.concat(ls_mean_diffs, axis=1, keys =ls_index).T
se_res_max = df_res.max(0)
se_res_argmax = df_res.idxmax(0)
len(se_res_max[se_res_max.abs() > 0.04])

# EXAMPLE
ls_ids_ta_check = [x for x in se_res_max.index[se_res_max.abs() > 0.04]\
                     if x in df_info.index[df_info['TA'] == 1]]

indiv_id = ls_ids_ta_check[0]

plt.rcParams['figure.figsize'] = 16, 6
ax = df_prices[indiv_id].plot()
se_mean_prices.plot(ax=ax)
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, [indiv_id, u'mean price'], loc = 1)
ax.axvline(x = se_res_argmax.ix[indiv_id], color = 'k', ls = 'dashed')
plt.tight_layout()
plt.show()



# ARCHIVE: GRAPH SYNTAX

#ax = df_price[['51520001','51000009', '51000007']].plot()
#handles, labels = ax.get_legend_handles_labels()
#ax.legend(handles, [u'Total Access', u'Intermarché', 'Esso'], loc = 1)
#plt.tight_layout()
#plt.show()

#ax = df_price[['avg_price', indiv_id]].plot(xlim = (df_price.index[0], df_price.index[-1]),
#                                            ylim=(1.2, 1.6))
#ax.axvline(x = se_argmax[indiv_id], color='k', ls='dashed')
#plt.savefig(os.path.join(path_dir_temp, 'chge_id_%s' %indiv_id))
#plt.close()
