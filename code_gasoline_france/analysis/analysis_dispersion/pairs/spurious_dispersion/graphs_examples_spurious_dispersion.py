#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matplotlib.dates import DateFormatter
from matplotlib.dates import SA

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')

path_dir_built_dis = os.path.join(path_data,
                                  u'data_gasoline',
                                  u'data_built',
                                  u'data_dispersion')
path_dir_built_dis_json = os.path.join(path_dir_built_dis, 'data_json')
path_dir_built_dis_csv = os.path.join(path_dir_built_dis, 'data_csv')
path_dir_built_dis_graphs = os.path.join(path_dir_built_dis, 'data_graphs')

path_dir_built_other = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_other')
path_dir_built_other_csv = os.path.join(path_dir_built_other, 'data_csv')

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

from pylab import *
rcParams['figure.figsize'] = 16, 6

## french date format
#import locale
#locale.setlocale(locale.LC_ALL, 'fra_fra')

dir_graphs = 'bw'

# #########
# LOAD DATA
# #########

# DF STATION INFO

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
                      parse_dates = [u'day_%s' %i for i in range(4)]) # fix
df_info.set_index('id_station', inplace = True)

# DF STATION STATS

df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# DF STATION STATS

df_station_promo = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_promo.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_promo.set_index('id_station', inplace = True)

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

# FILTER DATA
# exclude stations with insufficient (quality) price data
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'corse')].index)))
ls_drop_ids = list(set(df_prices_ttc.columns).difference(set(ls_keep_ids)))
df_prices_ttc[ls_drop_ids] = np.nan
df_prices_ht[ls_drop_ids] = np.nan
# highway stations may not be in df_prices_cl (no pbm here)
ls_drop_ids_nhw =\
  list(set(ls_drop_ids).difference(set(df_info[df_info['highway'] == 1].index)))
df_prices_cl[ls_drop_ids_nhw] = np.nan
# restrict df_info
df_info = df_info.ix[ls_keep_ids]

# DF PAIRS
ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                    'df_pair_final.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)


# DF RANK REVERSALS
df_rr = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                 'df_rank_reversals_all.csv'),
                    parse_dates = ['date'],
                    encoding = 'utf-8')
df_rr.set_index('date', inplace = True)
df_rr = df_rr.T
df_rr.index = [tuple(x.split('-')) for x in df_rr.index]

# DF QUOTATIONS (WHOLESALE GAS PRICES)

df_quotations = pd.read_csv(os.path.join(path_dir_built_other_csv,
                                   'df_quotations.csv'),
                                 encoding = 'utf-8',
                                 parse_dates = ['date'])
df_quotations.set_index('date', inplace = True)

# DF MACRO TRENDS

ls_sup_ids = df_info[df_info['group_type'] == 'SUP'].index
ls_other_ids = df_info[df_info['group_type'] != 'SUP'].index
df_quotations['UFIP Brent R5 EL'] = df_quotations['UFIP Brent R5 EB'] / 158.987
df_macro = pd.DataFrame(df_prices_ht.mean(1).values,
                        columns = [u'Retail avg excl. taxes'],
                        index = df_prices_ht.index)
df_macro['Brent'] = df_quotations['UFIP Brent R5 EL']
df_macro[u'Retail avg excl. taxes - Supermarkets'] = df_prices_ht[ls_sup_ids].mean(1)
df_macro[u'Retail avg excl. taxes - Others'] = df_prices_ht[ls_other_ids].mean(1)
df_macro = df_macro[[u'Brent',
                     u'Retail avg excl. taxes',
                     u'Retail avg excl. taxes - Supermarkets',
                     u'Retail avg excl. taxes - Others']]
df_macro['Brent'] = df_macro['Brent'].fillna(method = 'bfill')

# #######################
# TEMPORAL RANK REVERSALS
# #######################

# RESTRICT CATEGORY (EXCLUDE MC)
df_pairs_bu = df_pairs.copy()
df_pairs = df_pairs[df_pairs['cat'] == 'all']

# REFINE CATEGORIES
# - distinguish discounter among non sup
# - interested in discounter vs discounter and discounter vs. sup

# based on brand_last
ls_discounter = ['ELF', 'ESSO_EXPRESS', 'TOTAL_ACCESS']
for i in (1, 2):
  df_pairs.loc[df_pairs['brand_last_{:d}'.format(i)].isin(ls_discounter),
               'group_type_last_{:d}'.format(i)] = 'DIS'
  df_pairs.loc[df_pairs['brand_last_{:d}'.format(i)].isin(ls_discounter),
               'group_type_{:d}'.format(i)] = 'DIS'
df_info.loc[df_info['brand_last'].isin(ls_discounter),
             'group_type_last'] = 'DIS'
df_info.loc[df_info['brand_last'].isin(ls_discounter),
             'group_type'] = 'DIS'

# COMPETITORS VS. SAME GROUP

df_pair_same =\
  df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
           (df_pairs['group_last_1'] == df_pairs['group_last_2'])].copy()
df_pair_comp =\
  df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
           (df_pairs['group_last_1'] != df_pairs['group_last_2'])].copy()

# DIFFERENTIATED VS. NON DIFFERENTIATED

diff_bound = 0.01
df_pair_same_nd = df_pair_same[df_pair_same['mean_spread'].abs() <= diff_bound]
df_pair_same_d  = df_pair_same[df_pair_same['mean_spread'].abs() > diff_bound]
df_pair_comp_nd = df_pair_comp[df_pair_comp['mean_spread'].abs() <= diff_bound]
df_pair_comp_d  = df_pair_comp[df_pair_comp['mean_spread'].abs() > diff_bound]

# COMP SUP VS. NON SUP

df_pair_sup = df_pair_comp[(df_pair_comp['group_type_1'] == 'SUP') &\
                           (df_pair_comp['group_type_2'] == 'SUP')]
df_pair_nsup = df_pair_comp[(df_pair_comp['group_type_1'] != 'SUP') &\
                            (df_pair_comp['group_type_2'] != 'SUP')]
df_pair_sup_nd = df_pair_sup[(df_pair_sup['mean_spread'].abs() <= diff_bound)]
df_pair_nsup_nd = df_pair_nsup[(df_pair_nsup['mean_spread'].abs() <= diff_bound)]

# ALTERNATIVE

dict_pair_all = {'any' : df_pair_comp}

dict_pair_all['sup'] = df_pair_comp[(df_pair_comp['group_type_1'] == 'SUP') &\
                                   (df_pair_comp['group_type_2'] == 'SUP')]

dict_pair_all['oil_ind'] =\
    df_pair_comp[(df_pair_comp['group_type_1'].isin(['OIL', 'INDEPENDENT'])) &\
                 (df_pair_comp['group_type_2'].isin(['OIL', 'INDEPENDENT']))]

dict_pair_all['dis'] = df_pair_comp[(df_pair_comp['group_type_1'] == 'DIS') &\
                                   (df_pair_comp['group_type_2'] == 'DIS')]

dict_pair_all['sup_dis'] = df_pair_comp[((df_pair_comp['group_type_1'] == 'SUP') &\
                                       (df_pair_comp['group_type_2'] == 'DIS')) |
                                      ((df_pair_comp['group_type_1'] == 'DIS') &\
                                       (df_pair_comp['group_type_2'] == 'SUP'))]

dict_pair_all['oil_sup'] =\
    df_pair_comp[((df_pair_comp['group_type_1'] == 'SUP') &\
                  (df_pair_comp['group_type_2'].isin(['OIL', 'INDEPENDENT']))) |
                 ((df_pair_comp['group_type_1'].isin(['OIL', 'INDEPENDENT'])) &\
                  (df_pair_comp['group_type_2'] == 'SUP'))]

dict_pair_nd = {}
for df_type_title, df_type_pairs in dict_pair_all.items():
  dict_pair_nd[df_type_title] =\
      df_type_pairs[df_type_pairs['abs_mean_spread'] <= diff_bound].copy()

# LISTS FOR DISPLAY

lsd = ['id_1', 'id_2', 'distance', 'group_last_1', 'group_last_2']
lsd_rr = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

dir_graphs = 'bw'
str_ylabel = 'Price (euro/liter)'

# #########################
# TOTAL ACCESS: SPURIOUS RR
# #########################

df_sub_ta = df_pair_comp_nd[(df_pair_comp_nd['brand_last_1'] == 'TOTAL_ACCESS') |\
                            (df_pair_comp_nd['brand_last_2'] == 'TOTAL_ACCESS')]

# print(df_spurious[['pct_rr', 'mean_rr_len']].describe())

df_sub_ta_2 = df_sub_ta[df_sub_ta['mean_rr_len'] >=\
                          df_sub_ta['mean_rr_len'].quantile(0.95)]

id_1, id_2 = df_sub_ta_2[['id_1', 'id_2']].iloc[2]
id_1, id_2 = '83140003', '83190004'
print(df_sub_ta_2[(df_sub_ta_2['id_1'] == id_1) &\
                  (df_sub_ta_2['id_2'] == id_2)][['brand_last_1',
                                                  'brand_last_2',
                                                  'pct_rr',
                                                  'mean_rr_len']].T)

#df_prices_ttc[[id_1, id_2]].plot()

fig = plt.figure()
ax1 = fig.add_subplot(111)
l1 = ax1.plot(df_prices_ttc.index,
              df_prices_ttc[id_1].values,
              c = 'k', ls = '-', alpha = 0.5, # lw = 1, marker = '+', markevery=5,
              label = '{:s}'.format(df_info.ix[id_1]['brand_last']))
l2 = ax1.plot(df_prices_ttc.index, df_prices_ttc[id_2].values,
              c = 'k', ls = '-', alpha = 1,
              label = '{:s}'.format(df_info.ix[id_2]['brand_last']))
l3 = ax1.plot(df_prices_ttc.index, df_prices_ttc.mean(1).values,
              c = 'k', ls = '--', alpha = 1,
              label = 'National average')
lns = l1 + l2 + l3
labs = [l.get_label() for l in lns]
## id_2 is TA
#ax1.axvline(x = df_info_ta.ix[id_2]['pp_chge_date'], color = 'k', ls = '-')
ax1.legend(lns, labs, loc=0)
ax1.grid()
# Show ticks only on left and bottom axis, out of graph
ax1.yaxis.set_ticks_position('left')
ax1.xaxis.set_ticks_position('bottom')
ax1.get_yaxis().set_tick_params(which='both', direction='out')
ax1.get_xaxis().set_tick_params(which='both', direction='out')
plt.ylabel(str_ylabel)
plt.tight_layout()
#plt.show()
plt.savefig(os.path.join(path_dir_built_dis_graphs,
                         dir_graphs,
                         'example_spurious_rr_total_access.png'),
            bbox_inches='tight')
plt.close()

# ################################
# TEMPORAL PRICE DISC: SPURIOUS RR
# ################################

formatter = DateFormatter('%b-%d')

df_sub_hrr = df_pair_comp[df_pair_comp['nb_rr'] >=\
                            df_pair_comp['nb_rr'].quantile(0.95)].copy()
df_sub_hrr.sort('nb_rr', ascending = False, inplace = True)
print(df_sub_hrr[0:20][['pct_rr', 'nb_rr', 'id_1', 'id_2', 'brand_0_1', 'brand_0_2']].to_string())

id_1, id_2 = '31520003', '31650002'
# restrict period
df_prices = df_prices_ttc.ix['2014-01-05':'2014-03-30'].copy()

fig = plt.figure()
ax1 = fig.add_subplot(111)
# plot prices
ax1.plot(df_prices.index,
         df_prices[id_1].values,
         c = 'k', ls = '-', alpha = 0.5, 
         label = '{:s}'.format(df_info.ix[id_1]['brand_last']))
ax1.plot(df_prices.index,
         df_prices[id_2].values,
         c = 'k', ls = '-', alpha = 1,
         label = '{:s}'.format(df_info.ix[id_2]['brand_last']))
#ax1.plot(df_prices.index,
#         df_prices.mean(1),
#         c = 'k', ls = '--', alpha = 1,
#         label = 'National average')

## plot days
#for day_date, day_dow in zip(df_prices.index, df_prices.index.dayofweek):
#  # increase on 5, decrease on 1: higher price on week end
#  if (day_dow == 5): # 0: MO, 1: TU, 5: SA, 6: SU
#    ld = ax1.axvline(x=day_date, lw=0.6, ls='-', c='g')
#  elif (day_dow == 1):
#    ld = ax1.axvline(x=day_date, lw=0.6, ls='--', c='g')

ax1.set_xlabel('2014')
ax1.xaxis.set_major_formatter(formatter)
#ax1.xaxis.grid(True)
sa1 = WeekdayLocator(SA)
ax1.xaxis.set_major_locator(sa1)
ax1.grid(True, which = 'major')
#ax1.xaxis.grid(True)

ax1.yaxis.set_ticks_position('left')
ax1.xaxis.set_ticks_position('bottom')
ax1.get_yaxis().set_tick_params(which='both', direction='out')
ax1.get_xaxis().set_tick_params(which='both', direction='out')

plt.ylabel(str_ylabel)

handles, labels = ax1.get_legend_handles_labels()
ax1.legend(handles, labels, loc = 1)
plt.savefig(os.path.join(path_dir_built_dis_graphs,
                         dir_graphs,
                         'example_spurious_rr_dynamic_price_discrimination.png'),
            bbox_inches='tight')
plt.close()
#plt.show()

# ################################
# NORMAL RR
# ################################

for id_1, id_2 in [['37520001', '37700001'],
                   ['69007002', '69100018'],
                   ['90000009', '90800001'],
                   ['86100005', '86100012'],
                   ['6200021',  '6200022']]:
  # restrict period
  df_prices = df_prices_ttc.ix['2014-01':'2014-06'].copy()
  
  fig = plt.figure()
  ax1 = fig.add_subplot(111)
  # plot prices
  ax1.plot(df_prices.index,
           df_prices[id_1].values,
           c = 'k', ls = '-', alpha = 0.5, 
           label = '{:s}'.format(df_info.ix[id_1]['brand_last']))
  ax1.plot(df_prices.index,
           df_prices[id_2].values,
           c = 'k', ls = '-', alpha = 1,
           label = '{:s}'.format(df_info.ix[id_2]['brand_last']))
  #ax1.plot(df_prices.index,
  #         df_prices.mean(1),
  #         c = 'k', ls = '--', alpha = 1,
  #         label = 'National average')
  
  ax1.grid(True, which = 'both')
  
  ax1.yaxis.set_ticks_position('left')
  ax1.xaxis.set_ticks_position('bottom')
  ax1.get_yaxis().set_tick_params(which='both', direction='out')
  ax1.get_xaxis().set_tick_params(which='both', direction='out')
  
  plt.ylabel(str_ylabel)
  
  handles, labels = ax1.get_legend_handles_labels()
  ax1.legend(handles, labels, loc = 1)
  
  plt.savefig(os.path.join(path_dir_built_dis_graphs,
                           dir_graphs,
                           'example_rr_{:s}_{:s}.png'.format(id_1, id_2)),
              bbox_inches='tight')
  #plt.show()
