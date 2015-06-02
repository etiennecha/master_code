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
                                       ['pp_chge_date', 'ta_chge_date'])
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

# #################
# LOAD COMPETITION
# #################

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

# ###################
# BUILD CONTROL GROUP
# ###################

# Can refine by brand and region
# Can take date into account

ls_ta_ids = list(df_info_ta.index)

dict_ls_ta_comp = {}
for id_station, ls_comp in dict_ls_comp.items():
  ls_ta_comp = [(comp_id, distance) for comp_id, distance in ls_comp\
                                    if comp_id in ls_ta_ids]
  dict_ls_ta_comp[id_station] = ls_ta_comp

ls_control_ids = []
for id_station, ls_ta_comp in dict_ls_ta_comp.items():
  if (not ls_ta_comp) or (ls_ta_comp[0][1] > 5):
    ls_control_ids.append(id_station)

#ax = df_prices_ht.mean(1).plot(label = 'all', legend = True)
#df_prices_ht[ls_control_ids].mean(1).plot(ax = ax, label = 'control', legend = True)
#plt.show()
#
#se_diff = df_prices_ht.mean(1) - df_prices_ht[ls_control_ids].mean(1)
#se_diff.plot()
#plt.show()

# ###################
# DIFF IN DIFF
# ###################

df_prices = df_prices_ttc

ls_ta_chge_ids = list(df_info_ta.index[(df_info_ta['pp_chge'] >= 0.05) &\
                                       (~pd.isnull(df_info_ta['date_beg']))])

df_dd_control = pd.DataFrame(df_prices[ls_control_ids].mean(1),
                             df_prices.index, ['price'])
df_dd_control['time'] = df_dd_control.index
ls_df_dd = []
ls_station_fe_vars = []
for id_station, ls_ta_comp in dict_ls_ta_comp.items():
  if df_info.ix[id_station]['brand_0'] not in ['ELF', 'TOTAL', 'TOTAL_ACCESS', 'ELAN']:
    # Need to have pp change and dates of transition
    ls_ta_comp = [(comp_id, distance) for comp_id, distance in ls_ta_comp\
                                      if comp_id in ls_ta_chge_ids]
    # todo: refine if several (first date?)
    if (ls_ta_comp) and (ls_ta_comp[0][1] <= 3):
      id_ta = ls_ta_comp[0][0]
      distance = ls_ta_comp[0][1]
      date_beg = df_info_ta.ix[id_ta]['date_beg']
      date_end = df_info_ta.ix[id_ta]['date_end']
      df_dd_comp = pd.DataFrame(df_prices[id_station].values,
                                df_prices.index, ['price'])
      df_dd_comp.loc[date_beg:date_end, 'price'] = np.nan
      df_dd_comp['time'] = df_dd_comp.index
      df_dd_comp['time'] = df_dd_comp['time'].apply(lambda x: x.strftime('%Y-%m-%d'))
      df_dd_comp['fe_%s' %id_station] = 1
      df_dd_comp['treatment'] = 0
      df_dd_comp.loc[date_end:, 'treatment'] = 1
      ls_df_dd.append(df_dd_comp)
      ls_station_fe_vars.append('fe_%s' %id_station)

# start, end = 0, 100
ls_df_res = []
# for i in range(0, 200, 00):
start, end = 100, 150 #i, i+100
# df_dd = pd.concat([df_dd_control] + ls_df_dd[start:end], ignore_index = True)
df_dd = pd.concat(ls_df_dd[start:end], ignore_index = True)
df_dd.fillna(value = {x : 0 for x in ls_station_fe_vars[start:end] + ['treatment']},
             inplace = True)

str_station_fe = ' + '.join(ls_station_fe_vars[start:end])

df_dd = df_dd[~pd.isnull(df_dd['price'])]

reg_dd_res = smf.ols('price ~ C(time) + %s + treatment - 1' %str_station_fe,
                     data = df_dd,
                     missing = 'drop').fit()

ls_tup_coeffs = zip(reg_dd_res.params.index.values.tolist(),
                    reg_dd_res.params.values.tolist(),
                    reg_dd_res.bse.values.tolist(),
                    reg_dd_res.tvalues.values.tolist(),
                    reg_dd_res.pvalues.values.tolist())

df_res_temp = pd.DataFrame(ls_tup_coeffs,
                           columns = ['name', 'coeff', 'se', 'tval', 'pval'])
#df_res_temp.set_index('id_station', inplace = True)
#ls_df_res.append(df_res_temp)
#
#df_res = pd.concat(ls_df_res)


## Table: TA chge vs. TA comp
#ls_pcts = [0.1, 0.25, 0.5, 0.75, 0.9]
#df_ta_chge_vs_ta_comp =\
#  pd.concat([(-df_info_ta.ix[ls_ta_chge_ids]['pp_chge']).describe(percentiles=ls_pcts),
#             df_res_sf['coeff'].describe(percentiles=ls_pcts),
#             df_res_sf['coeff'][df_res_sf['distance'] <= 2].describe(percentiles=ls_pcts),
#             df_res_sf['coeff'][df_res_sf['distance'] <= 1].describe(percentiles=ls_pcts)],
#             keys = ['TA', 'TA_comp_3km', 'TA_comp_2km' ,'TA_comp_1km'], axis = 1)
#print df_ta_chge_vs_ta_comp.to_string()
#
## describe by brand
#ls_df_desc = []
#ls_desc_brands = df_res_sf['brand_0'].value_counts()[0:10].index
#for brand in ls_desc_brands:
#  df_temp_desc = df_res_sf['coeff'][\
#                    df_res_sf['brand_0'] == brand].describe()
#  ls_df_desc.append(df_temp_desc)
#df_desc = pd.concat(ls_df_desc, axis = 1, keys = ls_desc_brands)
#df_desc.rename(columns = {'CARREFOUR_MARKET' : 'CARREFOUR_M'}, inplace = True)
#print df_desc.to_string()
#
## small reg to explain coeff
#print smf.ols('coeff ~ C(brand_0) + distance + pp_chge',
#              data = df_res_sf).fit().summary()


## #######
## GRAPHS
## #######
#
#from pylab import *
#rcParams['figure.figsize'] = 16, 6
#
#plt.rc('font', **{'family' : 'Computer Modern Roman',
#                  'size'   : 20})
#
## Obfuscate then match TA price (check 2100012)
## 95100025   -0.077 0.001 -107.343 0.000  95100016     0.070
## Match TA price then give up
## 91000006   -0.057 0.001  -68.342 0.000  91000003     1.180
## Match TA price
## 5100004 ... lost the line
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
#  l1 = ax1.plot(df_prices_ht.index, df_prices_ht[id_1].values,
#                c = 'b', label = '%s_%s' %(id_1, df_info.ix[id_1]['brand_0']))
#  l2 = ax1.plot(df_prices_ht.index, df_prices_ht[id_2].values,
#                c = 'g', label = '%s_%s' %(id_2, df_info.ix[id_2]['brand_0']))
#  l3 = ax1.plot(df_prices_ht.index, df_prices_ht[ls_control_ids].mean(1).values,
#                c = 'r', label = 'Control')
#  lns = l1 + l2 + l3
#  labs = [l.get_label() for l in lns]
#  ax1.legend(lns, labs, loc=0)
#  ax1.grid()
#  plt.tight_layout()
#  #plt.show()
#  plt.savefig(os.path.join(path_dir_built_graphs,
#                           'competitor_reactions',
#                           'ex_%s.png' %i))

## Quick Graph
# ax = df_prices_ht[['69005002', '69009005']].plot()
# df_prices_ht[ls_control_ids].mean(1).plot(ax = ax)
# plt.show()
