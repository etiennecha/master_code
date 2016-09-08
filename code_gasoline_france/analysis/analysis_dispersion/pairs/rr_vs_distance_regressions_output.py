#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *
from generic_competition import *
import time
from statsmodels.iolib.summary2 import summary_col

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

# basic pair filter (insufficient obs, biased rr measure)
df_pairs = df_pairs[(~((df_pairs['nb_spread'] < 90) &\
                       (df_pairs['nb_ctd_both'] < 90))) &
                    (~(df_pairs['nrr_max'] > 60))]

# todo? harmonize pct i.e. * 100

# LISTS FOR DISPLAY
lsd = ['id_1', 'id_2', 'distance', 'group_last_1', 'group_last_2']
lsd_rr = ['rr_1', 'rr_2', 'rr_3', 'rr_4', 'rr_5', '5<rr<=20', 'rr>20']

# CREATE SAME CORNER VARIABLES
df_pairs['sc_500'] = 0
df_pairs.loc[df_pairs['distance'] <= 0.5, 'sc_500'] = 1
df_pairs['sc_750'] = 0
df_pairs.loc[df_pairs['distance'] <= 0.75, 'sc_750'] = 1
df_pairs['sc_1000'] = 0
df_pairs.loc[df_pairs['distance'] <= 1, 'sc_1000'] = 1

# SPREAD IN CENT (ONLY IF USED)
for spread_var in ['mean_spread',
                   'mean_abs_spread', 'abs_mean_spread',
                   'std_spread', 'std_abs_spread']:
  df_pairs[spread_var] = df_pairs[spread_var] * 100

for pct_var in ['pct_to_same_maxu', 'pct_to_same_maxl',
                'pct_to_same_min', 'pct_rr']:
  df_pairs[pct_var] = df_pairs[pct_var] * 100

# #############
# PREPARE DATA
# #############

# RESTRICT CATEGORY: PRICES AND MARGIN CHGE
df_pairs_all = df_pairs.copy()
price_cat = 'no_mc' # 'residuals_no_mc'
print(u'Prices used : {:s}'.format(price_cat))
df_pairs = df_pairs[df_pairs['cat'] == price_cat].copy()

## robustness check with idf: 1 km max
#ls_dense_dpts = [75, 92, 93, 94]
#df_pairs = df_pairs[~((((df_pairs['dpt_1'].isin(ls_dense_dpts)) |\
#                        (df_pairs['dpt_2'].isin(ls_dense_dpts))) &\
#                       (df_pairs['distance'] > 1)))]

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

# DICT OF DFS
# pairs without spread restriction
# (keep pairs with group change in any)
dict_pair_comp = {'any' : df_pair_comp}
for k in df_pair_comp['pair_type'].unique():
  dict_pair_comp[k] = df_pair_comp[df_pair_comp['pair_type'] == k]
# add sup sup&dis cat
dict_pair_comp['sup&dis'] = pd.concat([dict_pair_comp['sup'],
                                       dict_pair_comp['dis'],
                                       dict_pair_comp['sup_dis']])
# Low spread pairs (limit on average long term price difference)
diff_bound = 2.0 # euro cents
dict_pair_comp_nd = {}
for df_temp_title, df_temp in dict_pair_comp.items():
  dict_pair_comp_nd[df_temp_title] =\
      df_temp[df_temp['abs_mean_spread'] <= diff_bound]

# ##################
# REGRESSION
# ##################

# REGRESSION FORMULAS AND PARAMETERS
ls_dist_ols_formulas = ['abs_mean_spread ~ distance',
                        'mean_abs_spread ~ distance',
                        'pct_rr ~ distance',
                        'std_spread ~ distance']

dist_reg = 1000
col_sc = 'sc_{:d}'.format(dist_reg)

ls_sc_ols_formulas = ['abs_mean_spread ~ sc_{:d}'.format(dist_reg),
                      'mean_abs_spread ~ sc_{:d}'.format(dist_reg),
                      'pct_rr ~ sc_{:d}'.format(dist_reg),
                      'std_spread ~ sc_{:d}'.format(dist_reg)]

# from statsmodels.regression.quantile_regression import QuantReg
ls_quantiles = [0.2501, 0.501, 0.7501, 0.9001]

#mod = smf.quantreg('pct_rr~distance', df_ppd_reg[~pd.isnull(df_ppd_reg['pct_rr'])])
#res = mod.fit(q=.5)
#print res.summary()
## Following: need to add constant to make it equivalent
#res_alt = QuantReg(df_ppd_reg['pct_rr_nozero'], df_ppd_reg['sc_500']).fit(0.5)
# So far: need to add "resid[resid == 0] = .000001" in quantreg line 171-3 to have it run

# check => https://groups.google.com/forum/?hl=fr#!topic/pystatsmodels/XnXu_k1h-gc

# Output data to csv to run quantile regressions in R
df_pair_comp.to_csv(os.path.join(path_dir_built_dis_csv,
                                 'df_pair_comp_{:s}.csv'.format(price_cat)),
                    float_format= '%.4f',
                    encoding = 'utf-8',
                    index = False)

# REWRITE OUTPUT REGS

# FOR OLS AND QR
# - provide var names
# - provide stats to output for these vars
# - provide general reg stats to output
# - create dataframe with one row per reg: index is specification or part of it?

#ls_loop_df_ppd_regs = [('All', dict_pair_comp['any']),
#                       ('Sup', dict_pair_comp['sup']),
#                       ('Nd All', dict_pair_comp_nd['any']),
#                       ('Nd Oil&Ind', dict_pair_comp_nd['oil&ind']),
#                       ('Nd Sup', dict_pair_comp_nd['sup']),
#                       ('Sup Dis', dict_pair_comp['sup_dis']),
#                       ('Nd Sup Dis', dict_pair_comp_nd['sup_dis']),
#                       ('Oil&Ind', dict_pair_comp['oil&ind'])]

ls_loop_df_ppd_regs = [('Nd All', dict_pair_comp_nd['any']),
                       ('Nd Oil&Ind', dict_pair_comp_nd['oil&ind']),
                       ('Nd Sup', dict_pair_comp_nd['sup']),
                       ('Nd Sup&Dis', dict_pair_comp_nd['sup&dis'])]

# Some issues with current implementation of quantreg => R
# Work with dist 1000 until Oil Ind...

for df_ppd_title, df_ppd_reg in ls_loop_df_ppd_regs:
  df_ppd_reg = df_ppd_reg[(df_ppd_reg['distance'] <= 3)].copy()
  #df_ppd_reg.loc[df_ppd_reg['pct_rr'] == 0, 'pct_rr'] = 0.0001
  #df_ppd_reg.loc[df_ppd_reg['distance'] == 0, 'distance'] = 0.0001
  print()
  print(u'-'*30)
  print()
  print(u'{:s} ({:d} pairs)'.format(df_ppd_title, len(df_ppd_reg)))
  print(u'Pct same corner: {:3.1f}%'.format(len(df_ppd_reg[df_ppd_reg[col_sc] == 1]) /\
                                       float(len(df_ppd_reg)) * 100))
  # Simple ols
  ls_dis_ols_fits = [(str_formula,
                     smf.ols(formula = str_formula, data = df_ppd_reg).fit())\
                       for str_formula in ls_sc_ols_formulas]
  #df_dis_ols_res = format_ls_reg_fits_to_df(ls_dis_ols_fits, [col_sc])
  #print()
  #print(df_dis_ols_res.to_string())
  # QRs rank reversals
  ls_rr_qr_fits  = [('rr_sc_Q{:.2f}'.format(quantile),
                     smf.quantreg('pct_rr~{:s}'.format(col_sc),
                                  data = df_ppd_reg).fit(quantile))\
                       for quantile in ls_quantiles]
  #df_rr_qr_fits = format_ls_reg_fits_to_df(ls_rr_qr_fits, [col_sc])
  #print()
  #print(df_rr_qr_fits.to_string())
  # QRs standard deviation
  ls_std_qr_fits  = [('std_sc_Q{:.2f}'.format(quantile),
                      smf.quantreg('std_spread~{:s}'.format(col_sc),
                                    data = df_ppd_reg).fit(quantile))\
                         for quantile in ls_quantiles]
  #df_std_qr_fits = format_ls_reg_fits_to_df(ls_std_qr_fits, [col_sc])
  #print()
  #print(df_std_qr_fits.to_string())

  su_rr = summary_col([x[1] for x in ls_rr_qr_fits],
                       stars=True,
                       float_format='%0.2f',
                       model_names=[u'Q{:2.0f}'.format(quantile*100) for quantile in ls_quantiles],
                       info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                                  'R2':lambda x: "{:.2f}".format(x.rsquared)})
  
  su_std = summary_col([x[1] for x in ls_std_qr_fits],
                       stars=True,
                       float_format='%0.2f',
                       model_names=[u'Q{:2.0f}'.format(quantile*100) for quantile in ls_quantiles],
                       info_dict={'N':lambda x: "{0:d}".format(int(x.nobs)),
                                  'R2':lambda x: "{:.2f}".format(x.rsquared)})

  print(su_rr)
  print(su_std)
