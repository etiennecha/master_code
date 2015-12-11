#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

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
format_float_float = lambda x: '{:10,.3f}'.format(x)

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

# DF COMP

dict_comp_dtype = {'id_ta_{:d}'.format(i) : str for i in range(23)}
dict_comp_dtype['id_station'] = str
df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_comp.csv'),
                      dtype = dict_comp_dtype,
                      encoding = 'utf-8')
df_comp.set_index('id_station', inplace = True)

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices = df_prices_ttc

# CHOOSE DISTANCE

str_ta_ext = '_5km_dist_order'

# DF TOTAL ACCESS

df_ta = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                 'df_total_access{:s}.csv'.format(str_ta_ext)),
                              dtype = {'id_station' : str,
                                       'id_total_ta' : str,
                                       'id_elf_ta' : str,
                                       'ci_1' : str,
                                       'ci_ardt_1' : str},
                              encoding = 'utf-8',
                              parse_dates = ['start', 'end',
                                             'ta_date_beg',
                                             'ta_date_end',
                                             'date_min_total_ta',
                                             'date_max_total_ta',
                                             'date_min_elf_ta',
                                             'date_max_elf_ta'])
df_ta.set_index('id_station', inplace = True)

# DF REG RES

df_res = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                 'df_res_indiv{:s}.csv'.format(str_ta_ext)),
                     encoding = 'utf-8',
                     dtype = {'id_station' : str})
df_res.set_index('id_station', inplace = True)

# CHECK FOR DUPLICATES IN DF RES (AND DROP)

# one case: Total => Avia hence tta_comp and tta_tot (drop)
#import collections
#dict_cnt = dict(Counter(list(df_res.index)))
#print([k for k,v in cnt.items() if v != 1])
df_res = df_res[df_res.index != '4600001']

# ENRICH DF REG
df_res = pd.merge(df_res,
                  df_ta[['name',
                         'adr_street',
                         'adr_city',
                         'ci_1',
                         'ci_ardt_1',
                         'reg',
                         'dpt',
                         'group',
                         'brand_last',
                         'group_last',
                         'group_type_last',
                         'id_total_ta',
                         'dist_total_ta',
                         'date_min_total_ta',
                         'date_max_total_ta',
                         'id_elf_ta',
                         'dist_elf_ta',
                         'date_min_elf_ta',
                         'date_max_elf_ta',
                         'ta_date_beg',
                         'ta_date_end']],
                  left_index = True,
                  right_index = True,
                  how = 'left')

df_res['tr_id'] = None
df_res['tr_dist'] = None
#df_res['tr_date_min'] = pd.NaT
#df_res['tr_date_max'] = pd.NaT
df_res.rename(columns = {'ta_date_beg' : 'tr_date_min',
                        'ta_date_end' : 'tr_date_max'},
             inplace = True)

for str_treated in ['tta_comp', 'tta_tot']:
  df_res.loc[df_res['treated'] == str_treated,
             'tr_id'] = df_res['id_total_ta']
  df_res.loc[df_res['treated'] == str_treated,
             'tr_dist'] = df_res['dist_total_ta']
  df_res.loc[df_res['treated'] == str_treated,
             'tr_date_min'] = df_res['date_min_total_ta']
  df_res.loc[df_res['treated'] == str_treated,
             'tr_date_max'] = df_res['date_max_total_ta']
for str_treated in ['eta_comp']:
  df_res.loc[df_res['treated'] == str_treated,
             'tr_id'] = df_res['id_elf_ta']
  df_res.loc[df_res['treated'] == str_treated,
             'tr_dist'] = df_res['dist_elf_ta']
  df_res.loc[df_res['treated'] == str_treated,
             'tr_date_min'] = df_res['date_min_elf_ta']
  df_res.loc[df_res['treated'] == str_treated,
             'tr_date_max'] = df_res['date_max_elf_ta']

df_res.drop(['id_total_ta', 'dist_total_ta',
             'date_min_total_ta', 'date_max_total_ta',
             'id_elf_ta', 'dist_elf_ta',
             'date_min_elf_ta', 'date_max_elf_ta'],
            axis = 1,
            inplace = True)

# DF RES RONAN
df_res_ronan = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                        'df_res_indiv_ronan.csv'),
                            encoding = 'utf-8',
                            dtype = {'id_station' : str})
df_res_ronan.set_index('id_station', inplace = True)

df_res = pd.merge(df_res,
                  df_res_ronan[['Price5', 'Price5reg', 'Price5Ind']],
                  left_index = True,
                  right_index = True,
                  how = 'left')

df_res['c_treatment'] = df_res['c_treatment'] * 100

print(u"Inspect Ronan's estimates:")
print(df_res[(df_res['treated'] == 'tta_comp')]\
            [['Price5', 'Price5reg', 'c_treatment', 'p_treatment']][0:10].to_string())

df_res['diff'] = df_res['c_treatment'] - df_res['Price5reg']
df_res.sort('diff', ascending = False, inplace = True)

print()
print(u"Inspect extreme diffs:")
print(df_res[(df_res['treated'] == 'tta_comp')]\
             [['Price5', 'Price5reg', 'c_treatment', 'p_treatment', 'diff']][0:10].to_string())
print(df_res[(df_res['treated'] == 'tta_comp')]\
             [['Price5', 'Price5reg', 'c_treatment', 'p_treatment', 'diff']][-10:].to_string())

# diff by region
print()
print(u"Inspect avg diff by region:")
for reg in df_res['reg'].unique():
  #df_res_reg = df_res[df_res['reg'] == reg]
  df_res_reg = df_res[(df_res['reg'] == reg) &\
                      (df_res['treated'] == 'tta_comp') & 
                      (df_res['p_treatment'] <= 0.05)]
  print(u"{:s} {:.2f}".format(reg, (df_res_reg['Price5Ind'] - df_res_reg['Price5reg']).mean()))

## ##########
## OVERVIEW
## ##########
#
## todo: graphs of reactions above 0.03 or 0.04 cents
## todo: check share supermarkets vs. oil/indep
## todo: check reaction vs. station fe (todo elsewhere)
## todo: check closest competitor(s) of total access systematically? (based on pair price stats)
#
## treatment value thresholds for display
#ls_val = [i/100.0 for i in range(1, 10)]
#
## cent display
#pd.set_option('float_format', '{:,.2f}'.format)
#df_res['c_treatment'] = df_res['c_treatment'] * 100
#ls_val = [i for i in range(1, 10)]
#
#ls_pctiles = [0.1, 0.25, 0.5, 0.75, 0.9]
#
#for str_treated in ['tta', 'tta_tot', 'tta_comp', 'eta', 'eta_comp']:
#  str_treated = 'tta_comp'
#  df_res_sub = df_res[df_res['treated'] == str_treated]
#  
#  print()
#  print(u'Overview of regression results for {:s}'.format(str_treated))
#  print(df_res_sub.describe(percentiles = ls_pctiles).to_string())
#  
#  # Inspect significant treatments
#  df_res_sub_sig = df_res_sub[df_res_sub['p_treatment'] <= 0.05]
#  print()
#  print(u'Nb sig treatments:', len(df_res_sub_sig))
#  print(u'Nb positive/negative reactions above threshold:')
#  
#  ls_nb_inc = [len(df_res_sub_sig[df_res_sub_sig['c_treatment'] >= val])\
#                 for val in ls_val]
#  ls_nb_dec = [len(df_res_sub_sig[df_res_sub_sig['c_treatment'] <= -val])\
#                 for val in ls_val]
#  df_su_sig_reacs = pd.DataFrame([ls_nb_inc, ls_nb_dec],
#                                  columns = ls_val,
#                                  index = ['Nb pos', 'Nb neg'])
#  print(df_su_sig_reacs.to_string())
#
## treatment distributions by station type for tta_comp
#print()
#print(u'Overview of indiv effects by group type for tta_comp:')
#df_res_sub = df_res[df_res['treated'] == 'tta_comp']
#ls_se_gp_ies = []
#ls_temp_loop = [('Sup', df_res_sub[df_res_sub['group_type_last'] == 'SUP']),
#                ('Esso Exp.', df_res_sub[df_res_sub['brand_last'] == 'ESSO_EXPRESS']),
#                ('Esso', df_res_sub[df_res_sub['brand_last'] == 'ESSO']),
#                ('NSup', df_res_sub[df_res_sub['group_type_last'] != 'SUP']),
#                ('NSup NEExp',
#                    df_res_sub[(df_res_sub['group_type_last'] != 'SUP') &\
#                               (df_res_sub['brand_last'] != 'ESSO_EXPRESS')])]
#for str_temp, df_temp in ls_temp_loop:
#  ls_se_gp_ies.append(df_temp['c_treatment'].describe())
#df_su_gp_ies = pd.concat(ls_se_gp_ies,
#                         axis = 1,
#                         keys = [x[0] for x in ls_temp_loop])
#print(df_su_gp_ies.to_string())
#
### ########
### GRAPHS
### ########
##
### Move?
##
### Graphs of competitors or group Total stations affected
##df_res_check = df_res[(df_res['treated'].isin(['tta_tot',
##                                               'tta_comp',
##                                               'eta_comp'])) &\
##                      (df_res['p_treatment'] <= 0.05) &\
##                      (df_res['c_treatment'].abs() >= 3)] # 0.04 if not using cent
##
##for id_station, row in df_res_check.iterrows():
##  fig = plt.figure(figsize=(16,6))
##  ax1 = fig.add_subplot(111)
##  l2 = ax1.plot(df_prices_ttc.index, df_prices_ttc[row['tr_id']].values,
##                c = 'b', label = 'Station {:s}'.format(df_info.ix[row['tr_id']]['brand_0']))
##  l3 = ax1.plot(df_prices_ttc.index, df_prices_ttc.mean(1).values,
##                c = 'r', label = 'Moyenne nationale')
##  l1 = ax1.plot(df_prices_ttc.index, df_prices_ttc[id_station].values,
##                c = 'g', label = 'Station {:s}'.format(df_info.ix[id_station]['brand_0']))
##  lns = l1 + l2 + l3
##  labs = [l.get_label() for l in lns]
##  ax1.legend(lns, labs, loc=0)
##  ax1.axvline(x = row['tr_date_min'], color = 'b', ls = '--', alpha = 1.0, lw = 1.5)
##  ax1.axvline(x = row['tr_date_max'], color = 'b', ls = '--', alpha = 1.0, lw = 1.5)
##  ax1.grid()
##  plt.tight_layout()
##  #plt.show()
##  reac_sign = 'pos'
##  if row['c_treatment'] < 0:
##    reac_sign = 'neg'
##  plt.savefig(os.path.join(path_dir_built_ta_graphs,
##                           'price_series_treated',
##                           '{:s}_{:s}_{:.2f}_{:s}.png'.format(row['treated'],
##                                                              reac_sign,
##                                                              np.abs(row['c_treatment']),
##                                                              id_station)),
##              dpi = 200,
##              bbox_inches='tight')
##  plt.close()
