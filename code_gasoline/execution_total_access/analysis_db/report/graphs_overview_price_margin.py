#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import datetime, time
from BeautifulSoup import BeautifulSoup

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')

path_dir_built_csv = os.path.join(path_dir_built_paper, u'data_csv')

# LOAD DF QUOTATIONS

df_quotations = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_quotations.csv'),
                           parse_dates = ['date'],
                           encoding = 'utf-8')
df_quotations.set_index('date', inplace = True)

# LOAD DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

# LOAD DF INFO

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
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

df_info = df_info[(df_info['highway'] != 1) &\
                  (df_info['reg'] != 'Corse')]

ls_keep_ids = [id_station for id_station in df_info.index\
                 if id_station in df_prices_ht.columns]

# BUILD DF OVERVIEW

df_agg = df_quotations[['ULSD 10 CIF NWE EL', 'UFIP RT Diesel R5 EL']]
df_agg['diesel_ttc'] = df_prices_ttc[ls_keep_ids].mean(1)
df_agg['diesel_ht'] = df_prices_ht[ls_keep_ids].mean(1)
cost_ref = 'ULSD 10 CIF NWE EL' # 'UFIP RT Diesel R5 EL'
df_agg['diesel_brut_margin'] = df_agg['diesel_ht'] - df_agg[cost_ref]

# #################
# GRAPHS
# #################

from pylab import *
rcParams['figure.figsize'] = 16, 6

plt.rc('font', **{'family' : 'Computer Modern Roman',
                  'size'   : 20})

# DRAW PRICES AND COST

fig = plt.figure()
ax1 = fig.add_subplot(111)
line_1 = ax1.plot(df_agg.index, df_agg['diesel_ttc'].values,
                  ls='-', c='b', label='Avg. Fench retail diesel price after tax')
ax2 = ax1.twinx()
line_2 = ax2.plot(df_agg.index, df_agg['ULSD 10 CIF NWE EL'].values,
                  ls='-', c= 'g', label=r'Rotterdam wholesale diesel price')

lns = line_1 + line_2
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, loc=0)

ax1.grid()
#ax1.set_title(r"Add title here")
ax1.set_ylabel(r"French retail diesel (euros/l)")
ax2.set_ylabel(r"Rotterdam wholesale diesel (euros/l)")
plt.tight_layout()
plt.show()

# DRAW PRICES AND MARGIN

fig = plt.figure()
ax1 = fig.add_subplot(111)
# ax1 = plt.subplot(frameon=False)
line_1 = ax1.plot(df_agg.index, df_agg['diesel_ht'].values,
                  ls='--', c='b', label='Avg. French retail diesel price before tax')
line_1[0].set_dashes([4,2])
line_2 = ax1.plot(df_agg.index, df_agg[cost_ref].values,
                  ls='--', c= 'r', label=r'Rotterdam wholesale diesel price')
line_2[0].set_dashes([8,2])
ax2 = ax1.twinx()
line_3 = ax2.plot(df_agg.index, df_agg['diesel_brut_margin'].values,
                  ls='-', c='g', label=r'French retail gross margin (right axis)')

lns = line_1 + line_2 + line_3
labs = [l.get_label() for l in lns]
ax1.legend(lns, labs, loc=0)

ax1.grid()
#ax1.set_title(r"Add title here")
ax1.set_ylabel(r"Price (euros/l)")
ax2.set_ylabel(r"Gross margin (euros/l)")
plt.tight_layout()
plt.show()
