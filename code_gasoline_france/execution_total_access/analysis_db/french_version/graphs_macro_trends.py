#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import statsmodels.api as sm
import statsmodels.formula.api as smf

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_dir_built_json = os.path.join(path_dir_built_paper,
                                  u'data_json')

path_dir_built_graphs = os.path.join(path_dir_built_paper,
                                     'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.3f}'.format)
#format_float_int = lambda x: '{:10,.0f}'.format(x)
#format_float_float = lambda x: '{:10,.2f}'.format(x)

from pylab import *
rcParams['figure.figsize'] = 16, 6

# french date format
import locale
locale.setlocale(locale.LC_ALL, 'fra_fra')

# #############
# LOAD INFO TA
# #############

df_info_ta = pd.read_csv(os.path.join(path_dir_built_csv,
                                      'df_info_ta_fixed.csv'),
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
                                       ['pp_chge_date', 'ta_chge_date', 'TA_day'])
df_info_ta.set_index('id_station', inplace = True)

# ############
# LOAD INFO
# ############

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

df_info = df_info[df_info['highway'] != 1]

# ############
# LOAD PRICES
# ############

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_quotations = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_quotations.csv'),
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
                        columns = ['Prix moyen HT'],
                        index = df_prices_ht.index)
df_macro['Brent'] = df_quotations['UFIP Brent R5 EL']
df_macro[u'Prix moyen HT Supermarchés'] = df_prices_ht[ls_sup_ids].mean(1)
df_macro[u'Prix moyen HT Autres'] = df_prices_ht[ls_other_ids].mean(1)
# Column order determines legend
df_macro = df_macro[[u'Brent',
                     u'Prix moyen HT',
                     u'Prix moyen HT Supermarchés',
                     u'Prix moyen HT Autres']]
ax = df_macro.plot()
plt.tight_layout()
plt.xlabel('')
plt.savefig(os.path.join(path_dir_built_graphs,
                         'french_version',
                         'macro_trends.png'),
            bbox_inches='tight')
plt.close()

## GRAPHS: COMPETITOR REACTIONS
#
#ls_pair_display = [['95100025', '95100016'],
#                   ['91000006', '91000003'],
#                   ['5100004', '5100007'],
#                   ['22500002', '22500003'],
#                   ['69005002', '69009005'],
#                   ['69110003', '69009005']]
#
#for i, (id_1, id_2) in enumerate(ls_pair_display):
#  fig = plt.figure()
#  ax1 = fig.add_subplot(111)
#  l1 = ax1.plot(df_prices_ttc.index, df_prices_ttc[id_1].values,
#                c = 'b', label = 'Station %s' %(df_info.ix[id_1]['brand_0']))
#  l2 = ax1.plot(df_prices_ttc.index, df_prices_ttc[id_2].values,
#                c = 'g', label = 'Station %s' %(df_info.ix[id_2]['brand_0']))
#  l3 = ax1.plot(df_prices_ttc.index, df_prices_ttc[ls_control_ids].mean(1).values,
#                c = 'r', label = 'Control')
#  lns = l1 + l2 + l3
#  labs = [l.get_label() for l in lns]
#  ax1.legend(lns, labs, loc=0)
#  ax1.grid()
#  plt.tight_layout()
#  #plt.show()
#  plt.savefig(os.path.join(path_dir_built_graphs,
#                           'competitor_reactions',
#                           'ex_%s.png' %i),
#              bbox_inches='tight')
#  plt.close()
#
### Quick Graph
##ax = df_prices_ht[['69005002', '69009005']].plot()
##df_prices_ht[ls_control_ids].mean(1).plot(ax = ax)
##plt.show()
#
## GRAPHS: PRICING POLICY CHANGE
#
#plt.rcParams['figure.figsize'] = 16, 6
#
#se_mean_prices = df_prices_ttc.mean(1)
#
#id_station = '4160001'
#row = df_info_ta.ix[id_station]
#pp_chge = row['pp_chge']
#pp_chge_date = row['pp_chge_date']
#gov_chge_date = row['TA_day']
#ta_chge_date = row['ta_chge_date']
#ax = df_prices_ttc[id_station].plot(label = 'Station Total rebranded Total Access')
#se_mean_prices.plot(ax=ax, label = 'Control')
#handles, labels = ax.get_legend_handles_labels()
#ax.legend(handles, labels, loc = 1)
#ax.axvline(x = pp_chge_date, color = 'b', ls = 'dashed')
#ax.axvline(x = ta_chge_date, color = 'r', ls = 'dashed')
#ax.axvline(x = gov_chge_date, color = 'b', ls = 'dotted')
##plt.ylim(plt.ylim()[0]-0.5, plt.ylim()[1])
##print ax.get_position()
##ax.set_position((0.125, 0.2, 0.8, 0.7))
## plt.text(.02, .02, footnote_text)
## plt.tight_layout()
## plt.show()
#plt.xlabel('')
#plt.savefig(os.path.join(path_dir_built_graphs,
#                         'report_specific',
#                         'price_cut_detection.png'.format(id_station, pp_chge)),
#            bbox_inches='tight')
#plt.close()
