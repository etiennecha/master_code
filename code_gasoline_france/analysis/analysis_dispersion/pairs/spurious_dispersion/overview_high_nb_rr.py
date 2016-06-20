#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from matplotlib.dates import DateFormatter
from matplotlib.dates import MONDAY

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


# ##########
# STATS DES
# ##########

ls_loop_df_ppd_regs = [('All', dict_pair_all['any']),
                       ('Sup', dict_pair_all['sup']),
                       ('Nd All', dict_pair_nd['any']),
                       ('Nd Oil Ind', dict_pair_nd['oil_ind']),
                       ('Nd Sup', dict_pair_nd['sup']),
                       ('Sup Dis', dict_pair_all['sup_dis']),
                       ('Nd Sup Dis', dict_pair_nd['sup_dis']),
                       ('Oil Ind', dict_pair_all['oil_ind'])]

# ##########
# GRAPHS
# ##########

#for df_prices in [df_prices_ttc.ix[:'2011-12'], df_prices_ttc.ix['2014-01':'2014-04']]:
#  ax1 = df_prices['22190001'].plot()
#  for day_date, day_dow in zip(df_prices.index, df_prices.index.dayofweek):
#    # increase on 5, decrease on 1: higher price on week end
#    if (day_dow == 5): # 0: MO, 1: TU, 5: SA, 6: SU
#      ld = ax1.axvline(x=day_date, lw=0.6, ls='-', c='g')
#  plt.show()

#print(len(df_dis[(df_dis['pm_2'] >= nb_lim) & (df_dis['pm_3'] >= nb_lim) &\
#                 (df_dis['pk_2'] >= nb_lim) & (df_dis['pk_3'] >= nb_lim)]))

formatter = DateFormatter('%b-%d')

df_prices_1 = df_prices_ttc.ix['2011-10-03':'2012-04-02'].copy()
df_prices_2 = df_prices_ttc.ix['2013-12-30':'2014-06-30'].copy()
#df_prices_1 = df_prices_ttc.ix['2011-10-03':'2012-01-02'].copy()
#df_prices_2 = df_prices_ttc.ix['2013-12-30':'2014-03-31'].copy()

path_graphs_dpd = os.path.join(path_dir_built_dis_graphs,
                               'dynamic_price_dispersion')

for title, df_temp in ls_loop_df_ppd_regs[3:5]:
  path_graphs_dpd_temp = os.path.join(path_graphs_dpd,
                                      title)
  if not os.path.exists(path_graphs_dpd_temp):
    os.makedirs(path_graphs_dpd_temp)
  df_temp.sort('nb_rr', ascending = False, inplace = True)
  for row_i, row in df_temp[0:50].iterrows():
    #fig = plt.figure()
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1)
    #fig.subplots_adjust(top=0.88)
    # fig.subplots_adjust(vspace=10)
   
    #ax1 = fig.add_subplot(2,1,1)
    #df_prices_1[id_station].plot(ax=ax1, c = 'g')
    ax1.plot(df_prices_1.index,
             df_prices_1[row['id_1']].values,
             c = 'g')
    ax1.plot(df_prices_1.index,
             df_prices_1[row['id_2']].values,
             c = 'b')
    #for day_date, day_dow in zip(df_prices_1.index, df_prices_1.index.dayofweek):
    #  ld = ax1.axvline(x=day_date, lw=1, ls='--', c='g')
    #handles, labels = ax1.get_legend_handles_labels()
    #ax1.legend(handles, labels, loc = 1)
    ax1.yaxis.set_ticks_position('left')
    ax1.xaxis.set_ticks_position('bottom')
    ax1.get_yaxis().set_tick_params(which='both', direction='out')
    ax1.get_xaxis().set_tick_params(which='both', direction='out')
    #plt.ylabel(str_ylabel)
    ax1.set_xlabel('2011')
    ax1.xaxis.set_major_formatter(formatter)
    #ax1.xaxis.grid(True)
    mondays1 = WeekdayLocator(MONDAY)
    ax1.xaxis.set_major_locator(mondays1)
    ax1.grid(True, which = 'major')

    #ax2 = fig.add_subplot(2,1,2)
    #df_prices_2[id_station].plot(ax=ax2, c = 'g')
    ax2.plot(df_prices_2.index,
             df_prices_2[row['id_1']].values,
             c = 'g')
    ax2.plot(df_prices_2.index,
             df_prices_2[row['id_2']].values,
             c = 'b')
    #for day_date, day_dow in zip(df_prices_2.index, df_prices_2.index.dayofweek):
    #  ld = ax2.axvline(x=day_date, lw=1, ls='--', c='g')
    #handles, labels = ax2.get_legend_handles_labels()
    #ax2.legend(handles, labels, loc = 1)
    ax2.yaxis.set_ticks_position('left')
    ax2.xaxis.set_ticks_position('bottom')
    ax2.get_yaxis().set_tick_params(which='both', direction='out')
    ax2.get_xaxis().set_tick_params(which='both', direction='out')
    #plt.ylabel(str_ylabel)
    ax2.set_xlabel('2014')
    ax2.xaxis.set_major_formatter(formatter)
    #ax2.xaxis.grid(True)
    mondays2 = WeekdayLocator(MONDAY)
    ax2.xaxis.set_major_locator(mondays2)
    ax2.grid(True, which = 'major')
    
    fig.suptitle(u'{:s} {:s} - {:s} {:s}'.format(row['id_1'],
                                                 df_info.ix[row['id_1']]['brand_last'],
                                                 row['id_2'],
                                                 df_info.ix[row['id_2']]['brand_last']),
                 x = 0.01,
                 y = 0.04, # y = 0.99
                 horizontalalignment = 'left')
    fig.tight_layout()
    plt.subplots_adjust(bottom=0.10) # top = 0.90
    # plt.show()
    plt.savefig(os.path.join(path_graphs_dpd_temp,
                             u'{:.2f}_{:s}_{:s}.png'.format(row['pct_rr'],
                                                            row['id_1'],
                                                            row['id_2'])),
                dpi = 200)
    plt.close()

## Inspect

df_sup = dict_pair_nd['sup']
df_oi = dict_pair_nd['oil_ind']

lsd_rr = ['id_1', 'id_2', 'pct_rr', 'nb_rr', 'mean_rr_len',
          'mean_spread', 'mean_abs_spread', 'pct_same']

print()
print(df_sup[lsd_rr][0:100].to_string())

print()
print(df_oi[lsd_rr][0:100].to_string())


# ##########
# BACKUP
# ##########

#df_sub_hrr = df_pair_comp[df_pair_comp['nb_rr'] >=\
#                            df_pair_comp['nb_rr'].quantile(0.95)].copy()
#df_sub_hrr.sort('nb_rr', ascending = False, inplace = True)
#print(df_sub_hrr[0:20][['pct_rr', 'nb_rr', 'id_1', 'id_2', 'brand_0_1', 'brand_0_2']].to_string())
#
#id_1, id_2 = '31520003', '31650002'
#
#fig = plt.figure()
#ax1 = fig.add_subplot(111)
## restrict period
#df_prices = df_prices_ttc.ix['2014-01':'2014-03'].copy()
## plot prices
#df_prices[[id_1, id_2]].plot(ax=ax1)
#df_prices.mean(1).plot(c = 'k', ls = '-', label = 'National average')
## plot days
#for day_date, day_dow in zip(df_prices.index, df_prices.index.dayofweek):
#  # increase on 5, decrease on 1: higher price on week end
#  if (day_dow == 5): # 0: MO, 1: TU, 5: SA, 6: SU
#    ld = ax1.axvline(x=day_date, lw=0.6, ls='-', c='g')
#  elif (day_dow == 1):
#    ld = ax1.axvline(x=day_date, lw=0.6, ls='--', c='g')
#handles, labels = ax1.get_legend_handles_labels()
#labels = [df_info.ix[id_1]['brand_0'],
#          df_info.ix[id_2]['brand_0'],
#          'National average']
#ax1.legend(handles, labels, loc = 1)
#ax1.xaxis.grid(True)
#ax1.yaxis.set_ticks_position('left')
#ax1.xaxis.set_ticks_position('bottom')
#ax1.get_yaxis().set_tick_params(which='both', direction='out')
#ax1.get_xaxis().set_tick_params(which='both', direction='out')
#plt.ylabel(str_ylabel)
#plt.show()

# more generally
