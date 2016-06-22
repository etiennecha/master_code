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
path_dir_built_json = os.path.join(path_dir_built, u'data_json')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

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

#dir_graphs = 'bw'
str_ylabel = 'Price (euro/liter)'

# #########
# LOAD DATA
# #########

# DF INFO
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

# DF STATION STATS
df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                            'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# CLOSE STATIONS
dict_ls_close = dec_json(os.path.join(path_dir_built_json,
                                      'dict_ls_close.json'))

# DF PRICES
df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_cl = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_cleaned_prices.csv'),
                          parse_dates = ['date'])
df_prices_cl.set_index('date', inplace = True)

# basic station filter (geo scope or insufficient obs.)
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'corse')].index)))
ls_drop_ids = list(set(df_prices_ttc.columns).difference(set(ls_keep_ids)))
df_prices_ttc[ls_drop_ids] = np.nan
df_prices_ht[ls_drop_ids] = np.nan
# highway stations may not be in df_prices_cl (no pbm here)
ls_drop_ids_cl = list(set(df_prices_cl.columns).difference(set(ls_keep_ids)))
df_prices_cl[ls_drop_ids_cl] = np.nan
#df_info = df_info.ix[ls_keep_ids]
#df_station_stats = df_station_stats.ix[ls_keep_ids]

# DF PAIRS
ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                    'df_pair_final.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# basic pair filter (insufficient obs.)
df_pairs = df_pairs[~((df_pairs['nb_spread'] < 90) &\
                      (df_pairs['nb_ctd_both'] < 90))]

# todo? harmonize pct i.e. * 100

# LISTS FOR DISPLAY
lsd = ['id_1', 'id_2', 'distance', 'group_last_1', 'group_last_2']
lsd_rr = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

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

# #############
# PREPARE DATA
# #############

# RESTRICT CATEGORY: PRICES AND MARGIN CHGE
df_pairs_all = df_pairs.copy()
price_cat = 'no_mc' # 'residuals_no_mc'
print(u'Prices used : {:s}'.format(price_cat))
df_pairs = df_pairs[df_pairs['cat'] == price_cat].copy()

# robustness check with idf: 1 km max
ls_dense_dpts = [75, 92, 93, 94]
df_pairs = df_pairs[~((((df_pairs['dpt_1'].isin(ls_dense_dpts)) |\
                        (df_pairs['dpt_2'].isin(ls_dense_dpts))) &\
                       (df_pairs['distance'] > 1)))]

## robustness check keep closest competitor
#df_pairs.sort(['id_1', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_1', inplace = True, take_last = False)
# could also collect closest for each id_2 and filter further
# - id_1 can have closer competitor as an id_2
# - duplicates in id_2 (that can be solved also but drops too much)
#df_pairs.sort(['id_2', 'distance'], ascending = True, inplace = True)
#df_pairs.drop_duplicates('id_2', inplace = True, take_last = False)
## - too many drops: end ids always listed as id_2 disappear... etc.

### robustness check: rr>20 == 0
#df_pairs = df_pairs[(df_pairs['rr>20'] == 0)]
#df_pairs = df_pairs[(df_pairs['mean_rr_len'] <= 21)]

# COMPETITORS VS. SAME GROUP
df_pair_same =\
  df_pairs[(df_pairs['group_1'] == df_pairs['group_2']) &\
           (df_pairs['group_last_1'] == df_pairs['group_last_2'])].copy()
df_pair_comp =\
  df_pairs[(df_pairs['group_1'] != df_pairs['group_2']) &\
           (df_pairs['group_last_1'] != df_pairs['group_last_2'])].copy()

# DIFFERENTIATED VS. NON DIFFERENTIATED
diff_bound = 0.01
df_pair_same_nd = df_pair_same[df_pair_same['abs_mean_spread'] <= diff_bound]
df_pair_same_d  = df_pair_same[df_pair_same['abs_mean_spread'] > diff_bound]
df_pair_comp_nd = df_pair_comp[df_pair_comp['abs_mean_spread'] <= diff_bound]
df_pair_comp_d  = df_pair_comp[df_pair_comp['abs_mean_spread'] > diff_bound]

# DICT OF DFS
# pairs without spread restriction
# (keep pairs with group change in any)
dict_pair_comp = {'any' : df_pair_comp}
for k in df_pair_comp['pair_type'].unique():
  dict_pair_comp[k] = df_pair_comp[df_pair_comp['pair_type'] == k].copy()
# low spread pairs
dict_pair_comp_nd = {}
for df_temp_title, df_temp in dict_pair_comp.items():
  dict_pair_comp_nd[df_temp_title] =\
      df_temp[df_temp['abs_mean_spread'] <= diff_bound].copy()

# ##########
# STATS DES
# ##########

# Add cost based pricing in df_quotations (for display)
# todo: check TICPE in 2014
cost_ref = 'UFIP RT Diesel R5 EL' # u'ULSD 10 CIF NWE EL' (stops beg 2014) 
df_quotations['Cost based'] = \
  (df_quotations[cost_ref] + 0.4419) *  1.196 + 0.08
for (date_beg, date_end, amount) in [['2012-08-31', '2012-11-30', 0.030],
                                     ['2012-12-01', '2012-12-11', 0.020],
                                     ['2012-12-11', '2012-12-21', 0.015],
                                     ['2012-12-21', '2013-01-11', 0.010]]:
  df_quotations.loc[date_beg:date_end, 'Cost based'] =\
    (df_quotations.loc[date_beg:date_end, cost_ref]  - amount + 0.4419) *  1.196 + 0.08

# Merge station stats (promo info) with info
ls_stats_cols = df_station_stats.columns

df_station_stats = pd.merge(df_info,
                            df_station_stats,
                            left_index = True,
                            right_index = True,
                            how = 'left')

df_high = df_station_stats[df_station_stats['group_type_last'].isin(['OIL', 'IND'])].copy()
df_sup = df_station_stats[df_station_stats['group_type_last'].isin(['SUP'])].copy()
df_dis = df_station_stats[df_station_stats['group_type_last'].isin(['DIS'])].copy()

dict_df_temp = {'high' : df_high,
                'sup'  : df_sup,
                'dis'  : df_dis}

for title_temp, df_temp in dict_df_temp.items():
  df_temp.sort('pct_chge', ascending = False, inplace = True)

# ##########
# GRAPHS
# ##########

formatter = DateFormatter('%b-%d')

df_prices_1 = df_prices_ttc.ix['2011-10-03':'2012-04-02'].copy()
df_prices_2 = df_prices_ttc.ix['2013-12-30':'2014-06-30'].copy()

df_quotations_1 = df_quotations.ix['2011-10-03':'2012-04-02'].copy()
df_quotations_2 = df_quotations.ix['2013-12-30':'2014-06-30'].copy()

path_graphs_pcf = os.path.join(path_dir_built_dis_graphs,
                               'high_price_change_frequency')

for title, df_temp in dict_df_temp.items():
  path_graphs_pcf_temp = os.path.join(path_graphs_pcf,
                                      title)
  if not os.path.exists(path_graphs_pcf_temp):
    os.makedirs(path_graphs_pcf_temp)
  for id_station in df_temp[0:60].index:
    #fig = plt.figure()
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1)
    #fig.subplots_adjust(top=0.88)
    # fig.subplots_adjust(vspace=10)
   
    #ax1 = fig.add_subplot(2,1,1)
    #df_prices_1[id_station].plot(ax=ax1, c = 'g')
    ax1.plot(df_prices_1.index,
             df_prices_1[id_station].values,
             c = 'g')
    ax1.plot(df_quotations_1.index,
             df_quotations_1['Cost based'].values,
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
             df_prices_2[id_station].values,
             c = 'g')
    ax2.plot(df_quotations_2.index,
             df_quotations_2['Cost based'].values,
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
    
    fig.suptitle(u'{:s} - {:s} - {:s}'.format(id_station,
                                              df_info.ix[id_station]['brand_last'],
                                              df_info.ix[id_station]['adr_city']),
                 x = 0.01,
                 y = 0.04, # y = 0.99
                 horizontalalignment = 'left')
    fig.tight_layout()
    plt.subplots_adjust(bottom=0.10) # top = 0.90
    # plt.show()
    plt.savefig(os.path.join(path_graphs_pcf_temp,
                             u'{:.2f}_{:s}_{:s}_{:s}.png'.format(df_station_stats.ix[id_station]['pct_chge'],
                                                                 id_station,
                                                                 df_info.ix[id_station]['brand_last'],
                                                                 df_info.ix[id_station]['adr_city'])),
                dpi = 200)
    plt.close()
#    break

### Inspect
## print(df_sup[['brand_last', 'adr_city', 'nb_promo'] + lsdp][df_sup[lsdp].max(1) >= 8].to_string())
#
## Ex: week end price surges: 22190001 - LECLERC - PLERIN (beg 2014)
## Ex: increase on monday (not well detected): 2110002 - INTERMARCHE - BOHAIN-EN-VERMANDOIS
## Ex: decreases on week end 73600001 - SIMPLY - MOUTIERS (2011), 59118001 CORA WAMBRECHIES (2014)
#
## ##########
## BACKUP
## ##########
#
##df_sub_hrr = df_pair_comp[df_pair_comp['nb_rr'] >=\
##                            df_pair_comp['nb_rr'].quantile(0.95)].copy()
##df_sub_hrr.sort('nb_rr', ascending = False, inplace = True)
##print(df_sub_hrr[0:20][['pct_rr', 'nb_rr', 'id_1', 'id_2', 'brand_0_1', 'brand_0_2']].to_string())
##
##id_1, id_2 = '31520003', '31650002'
##
##fig = plt.figure()
##ax1 = fig.add_subplot(111)
### restrict period
##df_prices = df_prices_ttc.ix['2014-01':'2014-03'].copy()
### plot prices
##df_prices[[id_1, id_2]].plot(ax=ax1)
##df_prices.mean(1).plot(c = 'k', ls = '-', label = 'National average')
### plot days
##for day_date, day_dow in zip(df_prices.index, df_prices.index.dayofweek):
##  # increase on 5, decrease on 1: higher price on week end
##  if (day_dow == 5): # 0: MO, 1: TU, 5: SA, 6: SU
##    ld = ax1.axvline(x=day_date, lw=0.6, ls='-', c='g')
##  elif (day_dow == 1):
##    ld = ax1.axvline(x=day_date, lw=0.6, ls='--', c='g')
##handles, labels = ax1.get_legend_handles_labels()
##labels = [df_info.ix[id_1]['brand_0'],
##          df_info.ix[id_2]['brand_0'],
##          'National average']
##ax1.legend(handles, labels, loc = 1)
##ax1.xaxis.grid(True)
##ax1.yaxis.set_ticks_position('left')
##ax1.xaxis.set_ticks_position('bottom')
##ax1.get_yaxis().set_tick_params(which='both', direction='out')
##ax1.get_xaxis().set_tick_params(which='both', direction='out')
##plt.ylabel(str_ylabel)
##plt.show()
#
## more generally
