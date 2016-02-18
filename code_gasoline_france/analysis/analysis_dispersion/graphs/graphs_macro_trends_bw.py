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
rcParams['figure.figsize'] = 16, 6

## french date format
#import locale
#locale.setlocale(locale.LC_ALL, 'fra_fra')

dir_graphs = 'bw'
str_ylabel = 'Price (euro/litre)'

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

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# DF QUOTATIONS (WHOLESALE GAS PRICES)
df_quotations = pd.read_csv(os.path.join(path_dir_built_other_csv,
                                   'df_quotations.csv'),
                                 encoding = 'utf-8',
                                 parse_dates = ['date'])
df_quotations.set_index('date', inplace = True)

# ###############################
# GRAPHS: MACRO TRENDS
# ###############################

# ls_oil_ids = df_info[df_info['group_type'] == 'OIL'].index
ls_sup_ids = df_info[df_info['group_type'] == 'SUP'].index
ls_other_ids = df_info[df_info['group_type'] != 'SUP'].index

df_quotations['UFIP Brent R5 EL'] = df_quotations['UFIP Brent R5 EB'] / 158.987

#df_quotations[['UFIP Brent R5 EL', 'Europe Brent FOB EL']].plot()
#plt.show()

df_macro = pd.DataFrame(df_prices_ht.mean(1).values,
                        columns = [u'Retail avg excl. taxes'],
                        index = df_prices_ht.index)
df_macro['Brent'] = df_quotations['UFIP Brent R5 EL']
df_macro[u'Retail avg excl. taxes - Supermarkets'] = df_prices_ht[ls_sup_ids].mean(1)
df_macro[u'Retail avg excl. taxes - Others'] = df_prices_ht[ls_other_ids].mean(1)
# Column order determines legend
df_macro = df_macro[[u'Brent',
                     u'Retail avg excl. taxes',
                     u'Retail avg excl. taxes - Supermarkets',
                     u'Retail avg excl. taxes - Others']]

df_macro['Brent'] = df_macro['Brent'].fillna(method = 'bfill')

fig = plt.figure()
ax1 = fig.add_subplot(111)
ls_l = []
for col, ls, alpha in zip(df_macro.columns,
                          ['-', '-', ':', '-.'],
                          [0.4, 1, 1, 1]):
  ls_l.append(ax1.plot(df_macro.index,
                       df_macro[col].values,
                       c = 'k', ls = ls, alpha = alpha,
                       label = col))
lns = ls_l[0] + ls_l[1] + ls_l[2] + ls_l[3]
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, loc=0)
ax1.grid()
# Show ticks only on left and bottom axis, out of graph
ax1.yaxis.set_ticks_position('left')
ax1.xaxis.set_ticks_position('bottom')
ax1.get_yaxis().set_tick_params(which='both', direction='out')
ax1.get_xaxis().set_tick_params(which='both', direction='out')
plt.xlabel('')
plt.ylabel(str_ylabel)
plt.tight_layout()
plt.savefig(os.path.join(path_dir_built_dis_graphs,
                         dir_graphs,
                         'macro_trends.png'),
            bbox_inches='tight')
plt.close()

# #################
# GRAPH PRICE CHGES
# #################

zero = 1e-10

df_chges = df_prices_ttc - df_prices_ttc.shift(1)
#df_chges = df_chges.ix['2012-01-01':'2012-12-31']

se_neg_chges = df_chges[df_chges < - zero].count(1)
se_pos_chges = df_chges[df_chges >  zero].count(1)

fig = plt.figure()
ax = plt.subplot(111)
b0 = ax.bar(se_neg_chges.index,
            (-se_neg_chges).values,
            lw=0,
            color='k',
            alpha = 0.2)
b1 = ax.bar(se_pos_chges.index,
            se_pos_chges.values,
            lw=0,
            color='k',
            alpha=0.5)
ax.legend((b1[0], b0[0]), ('Price increases', 'Price decreases'))
# make it symmetric
ax.set_ylim(-7000, 7000)
ax.set_yticks((-7000, -5000, -3000, -1000, 0, 1000, 3000, 5000, 7000))  
# abs value: number of price changes
ax.set_yticklabels([u'{:.0f}'.format(x) for x in np.abs(ax.get_yticks())])
ax.grid()
# Show ticks only on left and bottom axis, out of graph
ax.yaxis.set_ticks_position('left')
ax.xaxis.set_ticks_position('bottom')
ax.get_yaxis().set_tick_params(which='both', direction='out')
ax.get_xaxis().set_tick_params(which='both', direction='out')
plt.ylabel(u'Nb price changes')
plt.tight_layout()
plt.savefig(os.path.join(path_dir_built_dis_graphs,
                         dir_graphs,
                         'macro_vol_price_chges.png'),
            bbox_inches='tight')
plt.close()