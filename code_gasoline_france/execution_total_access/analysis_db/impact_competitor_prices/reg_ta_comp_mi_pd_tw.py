#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pandas.stats.plm import PanelOLS

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
# POOLED OLS
# ###################

# Pooled OLS regression to estimate aggrefate treatment effect 
# Includes day and station FE
# Unsure if should expect different result vs. FE estimation (std errors?)
# Run with PanelOLS first... not necessarily very trustworthy?

df_prices = df_prices_ttc

ls_ta_chge_ids = list(df_info_ta.index[(df_info_ta['pp_chge'] >= 0.05) &\
                                       (~pd.isnull(df_info_ta['date_beg']))])

df_dd_control = pd.DataFrame(df_prices[ls_control_ids].mean(1),
                             df_prices.index, ['price'])
df_dd_control['time'] = df_dd_control.index
ls_df_dd = []
for id_station, ls_ta_comp in dict_ls_ta_comp.items()[0:4000]:
  if df_info.ix[id_station]['brand_0'] not in ['ELF', 'TOTAL', 'TOTAL_ACCESS', 'ELAN']:
    # Need to have pp change and dates of transition
    ls_ta_comp = [(comp_id, distance) for comp_id, distance in ls_ta_comp\
                                      if comp_id in ls_ta_chge_ids]
    # todo: refine if several (first date? or closest?)
    if (ls_ta_comp) and\
       (ls_ta_comp[0][1] <= 3):
      id_ta = ls_ta_comp[0][0]
      distance = ls_ta_comp[0][1]
      date_beg = df_info_ta.ix[id_ta]['date_beg']
      date_end = df_info_ta.ix[id_ta]['date_end']
      df_dd_comp = pd.DataFrame(df_prices[id_station].values,
                                df_prices.index, ['price'])
      df_dd_comp.loc[date_beg:date_end, 'price'] = np.nan
      df_dd_comp['time'] = df_dd_comp.index
      # df_dd_comp['time'] = df_dd_comp['time'].apply(lambda x: x.strftime('%Y-%m-%d'))
      df_dd_comp['id_station'] = id_station
      df_dd_comp['treatment'] = 0
      df_dd_comp.loc[date_end:, 'treatment'] = 1
      df_dd_comp['treatment_sup'] = 0
      if df_info.ix[id_station]['group_type'] == 'SUP':
        df_dd_comp.loc[date_end:, 'treatment_sup'] = 1
      df_dd_comp['treatment_ind'] = 0
      if df_info.ix[id_station]['group_type'] == 'IND':
        df_dd_comp.loc[date_end:, 'treatment_ind'] = 1
      ls_df_dd.append(df_dd_comp) # restriction on days considered

ls_ls_start_end = [[0,1200], # all?
                   [0, 600],
                   [600, 1200],
                   [300, 900]]

for start, end in ls_ls_start_end:
  ls_df_dd_temp = [df_dd_comp[start:end] for df_dd_comp in ls_df_dd]
  df_dd = pd.concat(ls_df_dd_temp, ignore_index = True)
  print u'Data contains: {:d} days and {:d} stations'.format(\
         len(df_dd['time'].unique()),
         len(df_dd['id_station'].unique()))
  print u'First date: {:s}'.format(df_dd['time'].min().strftime('%d/%m/%Y'))
  print u'Last date: {:s}'.format(df_dd['time'].max().strftime('%d/%m/%Y'))
  
  df_dd.set_index(['time', 'id_station'], inplace = True, verify_integrity = True)
  
  print u'\nPooled OLS with single streatment (day & station FE)'
  reg_one  = PanelOLS(y=df_dd['price'],
                      x=df_dd[['treatment']],
                      time_effects=True,
                      entity_effects=True)
  print reg_one
  
  #print u'\nPooled OLS reg with treatment for Oil/Sup/Ind (day & station FE)'
  #reg_two  = PanelOLS(y=df_dd['price'],
  #                    x=df_dd[['treatment', 'treatment_sup', 'treatment_ind']],
  #                    time_effects=True,
  #                    entity_effects=True)
  #print reg_two

## (VERIFICATION) MANUAL POOLED OLS (UNSURE ABOUT DIFF... STD ERRORS?)
#
## Same as above but using simple ols and adding day and station FE
## Too heavy with all days (seems around 150 days supported at CREST...)
## => either reduce nb of days
## => or use sparse matrices
## Consistent with results from Pooled OLS
#
#print u'\nPooled OLS reg with treatment for Oil/Sup/Ind (day & station FE)'
#df_dd = df_dd[~pd.isnull(df_dd['price'])]
#
#df_dd.reset_index(inplace = True, drop = False)
#reg_three = smf.ols('price ~ C(time) + C(id_station) + treatment - 1',
#                     data = df_dd,
#                     missing = 'drop').fit()
#
#ls_tup_coeffs = zip(reg_three.params.index.values.tolist(),
#                    reg_three.params.values.tolist(),
#                    reg_three.bse.values.tolist(),
#                    reg_three.tvalues.values.tolist(),
#                    reg_three.pvalues.values.tolist())
#
#df_reg_three = pd.DataFrame(ls_tup_coeffs,
#                           columns = ['name', 'coeff', 'se', 'tval', 'pval'])
#print df_reg_three

## (VERIFICATION) MANUAL POOLED OLS WITH SPARSE MATRICES (todo)
