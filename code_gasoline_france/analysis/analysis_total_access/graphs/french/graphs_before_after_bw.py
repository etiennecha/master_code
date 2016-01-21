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

path_dir_built_ta = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_total_access')
path_dir_built_ta_json = os.path.join(path_dir_built_ta, 'data_json')
path_dir_built_ta_csv = os.path.join(path_dir_built_ta, 'data_csv')
path_dir_built_ta_graphs = os.path.join(path_dir_built_ta, 'data_graphs')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

dir_graphs = 'french_version_bw'
alpha_1 = 0.2
alpha_2 = 0.4
str_xlabel = u'Prix TTC (euro/litre)'
str_ylabel = u'Nombre de stations'

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

# DF TOTAL ACCESS

df_ta = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                 'df_total_access_5km_dist_order.csv'),
                              dtype = {'id_station' : str,
                                       'id_total_ta' : str},
                              encoding = 'utf-8',
                              parse_dates = ['start', 'end',
                                             'ta_date_beg',
                                             'ta_date_end',
                                             'date_min_total_ta',
                                             'date_max_total_ta',
                                             'date_min_elf_ta',
                                             'date_max_elf_ta'])
df_ta.set_index('id_station', inplace = True)

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)


# ###################################
# GRAPHS: PRICE HISTOGRAMS FOR TOTAL
# ###################################

df_total_nta = df_info[(df_info['brand_0'] == 'TOTAL') &\
                       (df_info['brand_last'] == 'TOTAL')]

df_total_ta = df_info[(df_info['brand_0'] == 'TOTAL') &\
                      (df_info['brand_last'] == 'TOTAL_ACCESS')]

ls_total_nta_ids = list(df_total_nta.index)
ls_total_ta_ids = list(df_total_ta.index)

# First day
bins = np.linspace(1.20, 1.60, 41)
fig = plt.figure()
ax = fig.add_subplot(111)
ax.hist(df_prices_ttc[ls_total_nta_ids].iloc[0].values,
        bins, alpha=alpha_1, label=u'"Total" (pas de conversion à venir)', color = 'k')
ax.hist(df_prices_ttc[ls_total_ta_ids].iloc[0].values,
        bins, alpha=alpha_2, label=u'"Total" prochainement "Total Access"', color = 'k')
plt.xticks(np.linspace(1.20, 1.60, 9))
plt.xlim(1.20, 1.60)
plt.ylim(0, 400)
plt.xlabel(str_xlabel)
plt.ylabel(str_ylabel)
# Show ticks only on left and bottom axis
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')
plt.legend()
plt.savefig(os.path.join(path_dir_built_ta_graphs,
                         dir_graphs,
                         'price_dist_total_before.png'),
            bbox_inches='tight')
plt.close()
#plt.show()

# Last day
bins = np.linspace(1.00, 1.50, 51)
fig = plt.figure()
ax = fig.add_subplot(111)
ax.hist(df_prices_ttc[ls_total_nta_ids].iloc[-1].values,
        bins, alpha=alpha_1, label=u'"Total"', color = 'k')
ax.hist(df_prices_ttc[ls_total_ta_ids].iloc[-1].values,
        bins, alpha=alpha_2, label=u'"Total Access" anciennement "Total"', color = 'k')
plt.xticks(np.linspace(1.00, 1.50, 11))
plt.xlim(1.00, 1.50)
plt.xlabel(str_xlabel)
plt.ylabel(str_ylabel)
# Show ticks only on left and bottom axis
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')
plt.legend()
plt.savefig(os.path.join(path_dir_built_ta_graphs,
                         dir_graphs,
                         'price_dist_total_after.png'),
            bbox_inches='tight')
plt.close()
#plt.show()

# forced exclusion of price above 1.50... seems not valid anyway
# df_prices_ttc[ls_total].iloc[-1][df_prices_ttc[ls_total].iloc[-1] > 1.5].index
# df_prices_ttc[['37000002', '6000010']].plot()

## ######################################
## GRAPHS: PRICE HISTOGRAMS FOR TREATED
## ######################################

df_ta_sub = df_ta[(df_ta['filter'] > 4) &\
                  (df_ta['dum_ba'] != 0)]

df_tta_comp = df_ta_sub[(df_ta_sub['treatment_0'] == 1) &\
                        (df_ta_sub['filter'].isin([11, 12]))]

# 3: control, 4: out of market
df_nonaffected = df_ta_sub[(df_ta_sub['treatment_0'].isin([3, 4])) &\
                            (df_ta_sub['filter'] != 5)]

ls_treated_comp_ids = list(df_tta_comp.index)
ls_nonaffected_ids = list(df_nonaffected.index)

# First day
bins = np.linspace(1.20, 1.60, 41)
fig = plt.figure()
ax = fig.add_subplot(111)
ax.hist(df_prices_ttc[ls_nonaffected_ids].iloc[0].values,
        bins, alpha=alpha_1, label=u'Stations qui ne seront pas affectées', color = 'k')
ax.hist(df_prices_ttc[ls_treated_comp_ids].iloc[0].values,
        bins, alpha=alpha_2, label=u'Stations prochainement affectées', color = 'k')
plt.xticks(np.linspace(1.20, 1.60, 9))
plt.xlim(1.20, 1.60)
plt.xlabel(str_xlabel)
plt.ylabel(str_ylabel)
# Show ticks only on left and bottom axis
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')
plt.legend()
plt.savefig(os.path.join(path_dir_built_ta_graphs,
                         dir_graphs,
                         'price_dist_treated_before.png'),
            bbox_inches='tight')
plt.close()
#plt.show()

# Last day
bins = np.linspace(1.00, 1.50, 51)
fig = plt.figure()
ax = fig.add_subplot(111)
ax.hist(df_prices_ttc[ls_nonaffected_ids].iloc[-1].values,
        bins, alpha=alpha_1, label=u'Stations non affectées', color = 'k')
ax.hist(df_prices_ttc[ls_treated_comp_ids].iloc[-1].values,
        bins, alpha=alpha_2, label=u'Stations ayant été affectées', color = 'k')
plt.xticks(np.linspace(1.00, 1.50, 11))
plt.xlim(1.00, 1.50)
plt.xlabel(str_xlabel)
plt.ylabel(str_ylabel)
# Show ticks only on left and bottom axis
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')
plt.legend()
plt.savefig(os.path.join(path_dir_built_ta_graphs,
                         dir_graphs,
                         'price_dist_treated_after.png'),
            bbox_inches='tight')
plt.close()
#plt.show()
