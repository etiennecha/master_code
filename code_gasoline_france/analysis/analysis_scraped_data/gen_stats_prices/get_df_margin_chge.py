#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_scraped = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_scraped_2011_2014')

path_dir_built_csv = os.path.join(path_dir_built_scraped, u'data_csv')
path_dir_built_graphs = os.path.join(path_dir_built_scraped, 'data_graphs')

pd.set_option('float_format', '{:.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

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
                               'dpt' : str},
                      parse_dates = ['day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)
df_info = df_info[df_info['highway'] != 1]

# #####################################
# POLICY PRICE CHANGE
# #####################################

df_prices = pd.read_csv(os.path.join(path_dir_built_csv,
                                     'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices.set_index('date', inplace = True)
ls_keep_ids = [id_station for id_station in df_prices.columns if\
                 id_station in df_info.index]
df_prices = df_prices[ls_keep_ids]

se_mean_prices = df_prices.mean(1)
df_diff = df_prices.apply(lambda x: x - se_mean_prices, axis = 0)

# find biggest variation of spread vs. national price
# todo: check if would change with regional/dptal avg?
# todo: take into account activity period

lim = 20 # nb observations required before and after
ls_mean_diffs, ls_index = [], []
for per_ind in range(lim, len(df_diff) - lim):
  ls_index.append(df_diff.index[per_ind])
  # bu: without requiring nb of obs before and after
  # mean_diff = df_diff.ix[:per_ind].mean(0) - df_diff[per_ind:].mean(0)
  df_before = df_diff.ix[:per_ind]
  df_after = df_diff.ix[per_ind:]
  mean_diff = df_before[df_before.count(0)[df_before.count(0) >= lim].index].mean(0) -\
                df_after[df_after.count(0)[df_after.count(0) >= lim].index].mean(0)
  ls_mean_diffs.append(mean_diff)
df_res = pd.concat(ls_mean_diffs, axis=1, keys=ls_index).T
se_res_max = df_res.max(0)
se_res_argmax = df_res.idxmax(0)

df_margin_chge = pd.concat([se_res_max,
                            se_res_argmax],
                           keys = ['value', 'date'],
                           axis = 1)

# ##################################
# OVERVIEW OF CHGE VALUES AND DATES
# ##################################

print u'\nMost popular dates of change (top 10):'
print df_margin_chge['date'].value_counts()[0:10]

print u'\nNb of detected chges by size in abs val (interior in parenthesis):'
for x in [0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]:
  nb_chges_all_dates = len(df_margin_chge[df_margin_chge['value'].abs() > x])
  nb_chges_interior = len(df_margin_chge[(df_margin_chge['value'].abs() > x) &\
                                         (df_margin_chge['date'] != '2011-09-24') &\
                                         (df_margin_chge['date'] != '2013-05-15')])
  print u'Threshold {:.3f}: {:4d} ({:4d})'.format(x,
                                                  nb_chges_all_dates,
                                                  nb_chges_interior)

criterion = 0.02
print u'\nMost popular dates of change (top 20) with', criterion, ':'
print df_margin_chge['date']\
        [df_margin_chge['value'].abs() > criterion].value_counts()[0:20]

# #############
# OUTPUT
# #############

df_margin_chge.to_csv(os.path.join(path_dir_built_csv,
                                   'df_margin_chge.csv'),
                      index_label = 'id_station',
                      encoding = 'utf-8',
                      float_format='%.4f')

## ###############
## GRAPHS
## ###############
#
## Load TTC prices for graphs
#df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
#                                     'df_prices_ttc_final.csv'),
#                            parse_dates = ['date'])
#df_prices_ttc.set_index('date', inplace = True)
#
#df_prices_ttc = df_prices_ttc[ls_keep_ids]
#se_mean_prices_ttc = df_prices_ttc.mean(1)
#
#plt.rcParams['figure.figsize'] = 16, 6
#
#for row_ind, row in df_margin_chge[df_margin_chge['value'].abs() > 0.02].iterrows():
#  brand_str, value_str = 'same_brand', '02'
#  ax = df_prices_ttc[row_ind].plot()
#  se_mean_prices_ttc.plot(ax=ax)
#  handles, labels = ax.get_legend_handles_labels()
#  ax.legend(handles, [row_ind, u'mean price'], loc = 1)
#  ax.axvline(x = row['date'], color = 'b', ls = '--')
#  if not pd.isnull(df_info.ix[row_ind]['brand_1']):
#    brand_str = 'brand_change'
#    ax.axvline(x = df_info.ix[row_ind]['day_1'], color = 'r', ls = ':')
#    # error if null? (if yes add if?)
#    ax.axvline(x = df_info.ix[row_ind]['day_2'], color = 'r', ls = ':')
#  foot_str_0 = u'-'.join([x for x in df_info.ix[row_ind][['brand_0',
#                                                          'brand_1',
#                                                          'brand_2']].values.tolist()\
#                            if not pd.isnull(x)])
#  foot_str_1 = u'\n'.join([x if not pd.isnull(x) else ''\
#                             for x in df_info.ix[row_ind][['name',
#                                                           'adr_street',
#                                                           'adr_city',
#                                                           'ci_ardt_1']].values.tolist()])
#  plt.figtext(0.1, -0.15, u'\n'.join([foot_str_0, foot_str_1]))
#  if np.abs(row['value']) >= 0.04:
#    value_str = '04'
#  plt.savefig(os.path.join(path_dir_built_graphs,
#                           u'pricing_change',
#                           u'{:s}_{:s}'.format(brand_str, value_str),
#                           u'{:.3f}_{:s}.png'.format(np.abs(row['value']), row_ind)),
#              dpi = 200, bbox_inches='tight')
#  plt.close()
#
## todo: check when sizable difference (above 0.02?) if also change in brand
## todo: think what to do else... in the end should be two fixed effects
#
## Inspection of same_brand_04
#
### Chges to discard (outdated prices.. rigidity)
##81400003, 63940001, 50130002 (end), 42100010 (end),
##84000015 (end), 13120006, 77130004 (end), 95180001 (beginning),
##35760003, 56170001 (end), 44600003 (end), 61110001 (end),
##78590002, 35520002 (end... caution nan in general missing period before),
##44130002 (same), 47180001 (same), 20290007 (unsure), 83310010 (end),
##31000003, 63000021, 64800006 (rigid + date?), 6650003, 75008004 (end),
##56150003, 24320003 (rigid + end), 66000015, 52160002 (end)
##
### Check why margin chge detected (pbm... missing prices & window limits)
##20150003, 22460002, 20137004, 86360004, 6250001, 64800006 (position)
##
### Real chge at beginning (seems to be Carrefour Market only!)
##34200002, 13880001, 62520001, 5100004, 74230005, 13300007
##
### Promotion before closing?
##77940001, 25400002, 34340001, 
