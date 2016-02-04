#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time

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
path_dir_built_dis_csv = os.path.join(path_dir_built_dis, u'data_csv')
path_dir_built_dis_json = os.path.join(path_dir_built_dis, u'data_json')

pd.set_option('float_format', '{:,.3f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.3f}'.format(x)

# ################
# LOAD DATA
# ################

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

# FILTER DATA
# exclude stations with insufficient (quality) price data
df_filter = df_station_stats[~((df_station_stats['pct_chge'] < 0.03) |\
                               (df_station_stats['nb_valid'] < 90))]
ls_keep_ids = list(set(df_filter.index).intersection(\
                     set(df_info[(df_info['highway'] != 1) &\
                                 (df_info['reg'] != 'Corse')].index)))
#df_info = df_info.ix[ls_keep_ids]
#df_station_stats = df_station_stats.ix[ls_keep_ids]
#df_prices_ttc = df_prices_ttc[ls_keep_ids]
#df_prices_ht = df_prices_ht[ls_keep_ids]
#df_prices_cl = df_prices_cl[ls_keep_ids]

ls_drop_ids = list(set(df_prices_ttc.columns).difference(set(ls_keep_ids)))
df_prices_ttc[ls_drop_ids] = np.nan
df_prices_ht[ls_drop_ids] = np.nan
# highway stations may not be in df_prices_cl (no pbm here)
ls_drop_ids_nhw =\
  list(set(ls_drop_ids).difference(set(df_info[df_info['highway'] == 1].index)))
df_prices_cl[ls_drop_ids_nhw] = np.nan

# DF PAIRS

ls_dtype_temp = ['id', 'ci_ardt_1']
dict_dtype = dict([('%s_1' %x, str) for x in ls_dtype_temp] +\
                  [('%s_2' %x, str) for x in ls_dtype_temp])
df_pairs = pd.read_csv(os.path.join(path_dir_built_dis_csv,
                                    'df_pair_final.csv'),
              encoding = 'utf-8',
              dtype = dict_dtype)

# Create same corner variables
df_pairs['sc_500'] = 0
df_pairs.loc[df_pairs['distance'] <= 0.5, 'sc_500'] = 1
df_pairs['sc_750'] = 0
df_pairs.loc[df_pairs['distance'] <= 0.75, 'sc_750'] = 1
df_pairs['sc_1000'] = 0
df_pairs.loc[df_pairs['distance'] <= 1, 'sc_1000'] = 1

# RESTRICT CATEGORY

df_pairs_all = df_pairs.copy()
df_pairs = df_pairs[df_pairs['cat'] == 'no_mc'].copy()
#df_pairs = df_pairs[df_pairs['cat'] == 'residuals'].copy()

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

# LISTS FOR DISPLAY

lsd = ['id_1', 'id_2', 'distance', 'group_last_1', 'group_last_2']
lsd_rr = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

# ##################
# REGRESSION
# ##################

# REGRESSION FORMULAS AND PARAMETERS
ls_dist_ols_formulas = ['abs_mean_spread ~ distance',
                        'mean_abs_spread ~ distance',
                        'pct_rr ~ distance',
                        'std_spread ~ distance']

dist_reg = 750

ls_sc_ols_formulas = ['abs_mean_spread ~ sc_{:d}'.format(dist_reg),
                      'mean_abs_spread ~ sc_{:d}'.format(dist_reg),
                      'pct_rr ~ sc_{:d}'.format(dist_reg),
                      'std_spread ~ sc_{:d}'.format(dist_reg)]

# from statsmodels.regression.quantile_regression import QuantReg
ls_quantiles = [0.25, 0.5, 0.75]

def get_df_ols_res(ls_ols_res, ls_index):
  ls_se_ols_res = []
  for reg_res in ls_ols_res:
    ls_reg_res = [reg_res.nobs, reg_res.rsquared, reg_res.rsquared_adj,
                reg_res.params, reg_res.bse, reg_res.tvalues]
    dict_reg_res = dict(zip(['NObs', 'R2', 'R2a'], ls_reg_res[:3]) +\
                        zip(['%s_be' %ind for ind in ls_reg_res[3].index], ls_reg_res[3].values)+\
                        zip(['%s_se' %ind for ind in ls_reg_res[4].index], ls_reg_res[4].values)+\
                        zip(['%s_t' %ind for ind in ls_reg_res[5].index], ls_reg_res[5].values))
    ls_se_ols_res.append(pd.Series(dict_reg_res))
  df_ols_res = pd.DataFrame(ls_se_ols_res, index = ls_index)
  return df_ols_res

#mod = smf.quantreg('pct_rr~distance', df_ppd_reg[~pd.isnull(df_ppd_reg['pct_rr'])])
#res = mod.fit(q=.5)
#print res.summary()
## Following: need to add constant to make it equivalent
#res_alt = QuantReg(df_ppd_reg['pct_rr_nozero'], df_ppd_reg['sc_500']).fit(0.5)
# So far: need to add "resid[resid == 0] = .000001" in quantreg line 171-3 to have it run

ls_df_reg_res = []
for df_ppd_reg in [df_pair_comp_nd, df_pair_comp_d]:
  ls_dist_ols_res = [smf.ols(formula = str_formula, data = df_ppd_reg).fit()\
                       for str_formula in ls_dist_ols_formulas]
  ls_sc_ols_res   = [smf.ols(formula = str_formula, data = df_ppd_reg).fit()\
                       for str_formula in ls_sc_ols_formulas]
  ls_rr_qreg_res  = [smf.quantreg('pct_rr~sc_{:d}'.format(dist_reg),
                                  data = df_ppd_reg).fit(quantile)\
                       for quantile in ls_quantiles]
  ls_std_qreg_res = [smf.quantreg('std_spread~sc_{:d}'.format(dist_reg),
                                  data = df_ppd_reg).fit(quantile)\
                       for quantile in ls_quantiles]
  ls_ls_reg_res = [ls_dist_ols_res, ls_sc_ols_res, ls_rr_qreg_res, ls_std_qreg_res]
  ls_ls_index = [ls_dist_ols_formulas, ls_sc_ols_formulas, ls_quantiles, ls_quantiles]
  ls_df_reg_res.append([get_df_ols_res(ls_ols_res, ls_index)\
                          for ls_ols_res, ls_index in zip(ls_ls_reg_res, ls_ls_index)])

print('Compare raw prices vs. prices not raw:')

lsd_ols_dist = ['distance_be', 'distance_t', 'R2', 'NObs']
lsd_ols_corner = ['sc_{:d}_be'.format(dist_reg), 'sc_{:d}_t'.format(dist_reg), 'R2', 'NObs']
lsd_qr_corner = ['sc_{:d}_be'.format(dist_reg), 'sc_{:d}_t'.format(dist_reg), 'R2', 'NObs']

for i, title in enumerate(['Non differentiated', 'Differentiated']):
  
  print()
  print(u'-'*20)
  print(title)

  print()
  print('OLS: Distance')
  print(ls_df_reg_res[i][0][lsd_ols_dist].to_string())
  
  print()
  print('OLS: Same corner')
  print(ls_df_reg_res[i][1][lsd_ols_corner].to_string())

  print()
  print('QR: Rank reversal (Check vs. R?)')
  print(ls_df_reg_res[i][2][lsd_qr_corner].to_string())
  
  print()
  print('QR: Std spread (Check vs. R?)')
  print(ls_df_reg_res[i][3][lsd_qr_corner].to_string())

# check => https://groups.google.com/forum/?hl=fr#!topic/pystatsmodels/XnXu_k1h-gc

## Output data to csv to run quantile regressions in R
#path_dir_built_csv = os.path.join(path_dir_built_paper, 'data_csv')
#df_ppd.to_csv(os.path.join(path_dir_built_csv, 'data_ppd.csv'))
