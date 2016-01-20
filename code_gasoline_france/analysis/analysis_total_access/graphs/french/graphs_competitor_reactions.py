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

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

from pylab import *
rcParams['figure.figsize'] = 16, 6

# french date format
import locale
locale.setlocale(locale.LC_ALL, 'fra_fra')

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

# DF STATION INFO TOTAL ACCESS

df_info_ta = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                      'df_info_ta.csv'),
                      encoding = 'utf-8',
                      dtype = {'id_station' : str,
                               'adr_zip' : str,
                               'adr_dpt' : str,
                               'ci_1' : str,
                               'ci_ardt_1' :str,
                               'ci_2' : str,
                               'ci_ardt_2' : str,
                               'dpt' : str},
                      parse_dates = [u'day_%s' %i for i in range(4)] +\
                                    ['pp_chge_date',
                                     'ta_tot_date',
                                     'ta_gov_date']) # fix
df_info_ta.set_index('id_station', inplace = True)

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

# ###############################
# GRAPHS: COMPETITOR REACTIONS
# ###############################

df_ta_sub = df_ta[(df_ta['filter'] > 4) &\
                  (df_ta['dum_ba'] != 0)]

df_tta_comp = df_ta_sub[(df_ta_sub['treatment_0'] == 1) &\
                        (df_ta_sub['filter'].isin([11, 12]))]

df_control = df_ta_sub[(df_ta_sub['treatment_0'] == 3) &\
                       (df_ta_sub['filter'] != 5)]

ls_treated_comp_ids = list(df_tta_comp.index)
ls_nontreated_comp_ids = list(df_control.index)

ls_control_ids = ls_nontreated_comp_ids

#plt.rc('font', **{'family' : 'Computer Modern Roman',
#                  'size'   : 15})

# Obfuscate then match TA price (check 2100012)
# 95100025   -0.077 0.001 -107.343 0.000  95100016     0.070
# Match TA price then give up
# 91000006   -0.057 0.001  -68.342 0.000  91000003     1.180
# Match TA price
# 5100004 ... lost the line

ls_pair_display = [['95100025', '95100016'],
                   ['91000006', '91000003'],
                   ['5100004', '5100007'],
                   ['22500002', '22500003'],
                   ['69005002', '69009005'],
                   ['69110003', '69009005']]

for i, (id_1, id_2) in enumerate(ls_pair_display):
  fig = plt.figure()
  ax1 = fig.add_subplot(111)
  l1 = ax1.plot(df_prices_ttc.index, df_prices_ttc[id_1].values,
                c = 'b', label = 'Station %s' %(df_info.ix[id_1]['brand_0']))
  l2 = ax1.plot(df_prices_ttc.index, df_prices_ttc[id_2].values,
                c = 'g', label = 'Station %s' %(df_info.ix[id_2]['brand_0']))
  l3 = ax1.plot(df_prices_ttc.index, df_prices_ttc[ls_control_ids].mean(1).values,
                c = 'r', label = 'Moyenne nationale')
  lns = l1 + l2 + l3
  labs = [l.get_label() for l in lns]
  ax1.legend(lns, labs, loc=0)
  ax1.grid()
  plt.tight_layout()
  #plt.show()
  plt.savefig(os.path.join(path_dir_built_ta_graphs,
                           'french_version',
                           'ex_%s.png' %i),
              bbox_inches='tight')
  plt.close()

## Quick Graph
#ax = df_prices_ht[['69005002', '69009005']].plot()
#df_prices_ht[ls_control_ids].mean(1).plot(ax = ax)
#plt.show()

# ###############################
# GRAPHS: PRICING POLICY CHANGE
# ###############################

plt.rcParams['figure.figsize'] = 16, 6

se_mean_prices = df_prices_ttc.mean(1)

id_station = '4160001'
row = df_info_ta.ix[id_station]
pp_chge = row['pp_chge']
pp_chge_date = row['pp_chge_date']
gov_chge_date = row['ta_gov_date']
ta_chge_date = row['ta_tot_date']
ax = df_prices_ttc[id_station].plot(label = 'Station Total convertie')
se_mean_prices.plot(ax=ax, label = 'Moyenne Nationale')
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc = 1)
ax.axvline(x = pp_chge_date, color = 'b', ls = 'dashed')
#ax.axvline(x = ta_chge_date, color = 'r', ls = 'dashed')
#ax.axvline(x = gov_chge_date, color = 'b', ls = 'dotted')
#plt.ylim(plt.ylim()[0]-0.5, plt.ylim()[1])
#print ax.get_position()
#ax.set_position((0.125, 0.2, 0.8, 0.7))
# plt.text(.02, .02, footnote_text)
# plt.tight_layout()
# plt.show()
plt.xlabel('')
plt.savefig(os.path.join(path_dir_built_ta_graphs,
                         'french_version',
                         'fr_price_cut_detection.png'.format(id_station, pp_chge)),
            bbox_inches='tight')
plt.close()
