#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

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
#rcParams['figure.figsize'] = 16, 6
rcParams['figure.figsize'] = 8, 6

## french date format
#import locale
#locale.setlocale(locale.LC_ALL, 'fra_fra')

dir_graphs = 'bw'
str_ylabel = 'Price (euro/litre)'
alpha_1 = 0.2
alpha_2 = 0.4

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
df_info = df_info[df_info['highway'] != 1]

# DF STATION STATS

df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# DF MARGIN CHGE

df_margin_chge = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_margin_chge.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_margin_chge.set_index('id_station', inplace = True)

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
                                 (df_info['reg'] != 'Corse')].index)))

margin_chge_bound = 0.03
ls_ids_margin_chge =\
  df_margin_chge[df_margin_chge['value'].abs() >= margin_chge_bound].index

# Exclude margin chge (equivalent of 'no_mc' in pairs)
ls_keep_ids_2 = list(set(ls_keep_ids).difference(set(ls_ids_margin_chge)))

df_station_stats = df_station_stats.ix[ls_keep_ids]
df_station_stats = pd.merge(df_station_stats,
                            df_info[['brand_last',
                                     'group_last',
                                     'group_type_last']],
                            left_index = True,
                            right_index = True,
                            how = 'left')

df_station_stats_sup =\
  df_station_stats[df_station_stats['group_type_last'] == 'SUP']
df_station_stats_nsup =\
  df_station_stats[df_station_stats['group_type_last'] != 'SUP']

# #############################
# HISTO DAILY PRICE CHGE PROBA
# #############################

myarray = df_station_stats['pct_chge'].values
weights = np.ones_like(myarray)/float(len(myarray)) * 100

fig = plt.figure()
ax = fig.add_subplot(111)
# truncate: exclude those above 0.20
bins = np.linspace(0, 0.7, 15)
ax.hist(myarray,
        weights = weights,
        alpha=0.5,
        color = 'k',
        bins = bins,
        normed = 0)
ax.set_xticks(np.linspace(0, 0.7, 8))  
# Show ticks only on left and bottom axis, out of graph
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')
ax.get_yaxis().set_tick_params(which='both', direction='out')
ax.get_xaxis().set_tick_params(which='both', direction='out')
plt.xlabel(u'Daily price change probability')
plt.ylabel(u'% of obs')
#plt.legend()
plt.savefig(os.path.join(path_dir_built_dis_graphs,
                         dir_graphs,
                         'hist_station_price_chge_proba.png'),
            bbox_inches='tight')
plt.close()

# ##############################################
# HISTO DAILY PRICE CHGE PROBA: SUP VS NON SUPS
# ##############################################

fig = plt.figure()
ax = fig.add_subplot(111)
# truncate: exclude those above 0.20
bins = np.linspace(0, 0.7, 15)
myarray = df_station_stats_sup['pct_chge'].values
weights = np.ones_like(myarray)/float(len(myarray)) * 100
n, bins, rectangles = ax.hist(myarray,
                              weights = weights,
                              bins = bins,
                              alpha = alpha_1,
                              label = u'Supermarkets',
                              color = 'k',
                              normed = 0)
myarray = df_station_stats_nsup['pct_chge'].values
weights = np.ones_like(myarray)/float(len(myarray)) * 100
n, bins, rectangles = ax.hist(myarray,
                              weights = weights,
                              bins = bins,
                              alpha = alpha_2,
                              label = u'Non supermarkets',
                              color = 'k',
                              normed = 0)
ax.set_xticks(np.linspace(0, 0.7, 8))  
# Show ticks only on left and bottom axis, out of graph
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')
ax.get_yaxis().set_tick_params(which='both', direction='out')
ax.get_xaxis().set_tick_params(which='both', direction='out')
plt.xlabel(u'Daily price change probability')
plt.ylabel(u'% of obs')
plt.legend()
plt.savefig(os.path.join(path_dir_built_dis_graphs,
                         dir_graphs,
                         'hist_station_price_chge_proba_sup_nsup.png'),
            bbox_inches='tight')
plt.close()

# ###########################################
# HISTO MEAN PRICE CHGES
# ###########################################

fig = plt.figure()
ax = fig.add_subplot(111)
# truncate: exclude those above 0.20
bins = np.linspace(0, 5, 11)
myarray = df_station_stats['avg_pos_chge'].values * 100
weights = np.ones_like(myarray)/float(len(myarray)) * 100
n, bins, rectangles = ax.hist(myarray,
                              weights = weights,
                              bins = bins,
                              alpha = alpha_1,
                              label = u'Positive chges',
                              color = 'k',
                              normed = 0)
myarray = df_station_stats['avg_neg_chge'].abs().values * 100
weights = np.ones_like(myarray)/float(len(myarray)) * 100
n, bins, rectangles = ax.hist(myarray,
                              weights = weights,
                              bins = bins,
                              alpha = alpha_2,
                              label = u'Negative chges',
                              color = 'k',
                              normed = 0)
ax.set_xticks(np.linspace(0, 5, 6))  
# Show ticks only on left and bottom axis, out of graph
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')
ax.get_yaxis().set_tick_params(which='both', direction='out')
ax.get_xaxis().set_tick_params(which='both', direction='out')
plt.xlabel(u'Station mean price change (euro cents/litre)')
plt.ylabel(u'% of obs')
plt.legend()
plt.savefig(os.path.join(path_dir_built_dis_graphs,
                         dir_graphs,
                         'hist_station_mean_price_chge.png'),
            bbox_inches='tight')
plt.close()
