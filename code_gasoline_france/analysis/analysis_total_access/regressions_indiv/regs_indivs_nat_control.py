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

path_dir_built_csv = os.path.join(path_dir_built,
                                  u'data_csv')

path_dir_built_ta = os.path.join(path_data,
                                 u'data_gasoline',
                                 u'data_built',
                                 u'data_total_access')

path_dir_built_ta_json = os.path.join(path_dir_built_ta, 
                                      'data_json')

path_dir_built_ta_csv = os.path.join(path_dir_built_ta, 
                                     'data_csv')

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

# DF PRICES

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                           parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ttc_final.csv'),
                           parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_prices = df_prices_ht

# DF TOTAL ACCESS

df_ta = pd.read_csv(os.path.join(path_dir_built_ta_csv,
                                           'df_total_access_3km.csv'),
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

# ##########################
# DEFINE CONTROL AND TREATED
# ##########################

# filter stations with insufficient data
df_ta_sub = df_ta[(df_ta['filter'] > 4) &\
                  (df_ta['dum_ba'] != 0)]

dict_df_treated = {}
dict_df_treated['tta'] = df_ta_sub[(df_ta_sub['treatment_0'] == 5)]
dict_df_treated['eta'] = df_ta_sub[(df_ta_sub['treatment_0'] == 6)]
dict_df_treated['tta_comp'] = df_ta_sub[(df_ta_sub['treatment_0'] == 1) &\
                                        (df_ta_sub['filter'].isin([11, 12]))]
dict_df_treated['eta_comp'] = df_ta_sub[(df_ta_sub['treatment_0'] == 2) &\
                                        (df_ta_sub['filter'].isin([11,12]))]
dict_df_treated['tta_tot'] = df_ta_sub[(df_ta_sub['treatment_0'] == 1) &\
                                       (df_ta_sub['filter'] > 5) &\
                                       (df_ta_sub['group'] == 'TOTAL')]

df_control = df_ta_sub[(df_ta_sub['treatment_0'] == 3) &\
                       (df_ta_sub['filter'] != 5)]

str_treated = 'tta_comp'
df_treated = dict_df_treated[str_treated]

# ################
# LOOP ON STATIONS
# ################

ls_ids_nores = []
ls_ids_nodata = []
ls_rows_res = []
for id_station, row in df_treated.iterrows():
  try:
    if str_treated in ['tta', 'eta']:
      date_beg, date_end = row[['ta_date_beg', 'ta_date_end']].values
    elif str_treated in ['tta_comp', 'tta_tot']:
      date_beg, date_end = row[['date_min_total_ta', 'date_max_total_ta']].values
    elif str_treated in ['eta_comp']:
      date_beg, date_end = row[['date_min_elf_ta', 'date_max_elf_ta']].values
    else:
      date_beg, date_end = None, None
    df_station = df_prices[[id_station]].copy()
    df_station.rename(columns = {id_station : 'price'},
                   inplace = True)
    if (df_station['price'][df_station.index <= date_beg].count() >= 30) &\
       (df_station['price'][df_station.index >= date_end].count() >= 30):
      df_station['ref_price'] = df_prices[df_control.index].mean(1)
      df_station['resid'] = df_station['ref_price'] - df_station['price']
      df_station['l1_resid'] = df_station['resid'].shift(1)
      df_station['treatment'] = 0
      df_station.loc[(df_station.index >= date_beg) &\
                  (df_station.index <= date_end),
                  'treatment'] = np.nan
      df_station.loc[(df_station.index >= date_end),
                  'treatment'] = 1
      df_station['resid_2'] = df_station['resid'] * df_station['treatment']
      df_station['ref_price_2'] = df_station['ref_price'] * df_station['treatment']
      ## keep only one price per week
      #df_station['dow'] = df_station.index.weekday
      #df_station = df_station[df_station['dow'] == 3]
      res0 = smf.ols('price ~ ref_price + treatment',
                     data = df_station).fit(cov_type='HAC',
                                            cov_kwds={'maxlags':14})
      #rob_cov_hact0 = sm.stats.sandwich_covariance.cov_hac(rest0, nlags = 7)
      #rob_bse0 = np.sqrt(np.diag(rob_cov_hact0))
      #print res0.summary()
      res1 = smf.ols('price ~ ref_price + ref_price_2 + treatment',
                    data = df_station).fit(cov_type='HAC',
                                            cov_kwds={'maxlags':14})
      #print res1.summary()
      # pbm: how to run with robust standard errors?
      hyp = '(ref_price_2 = 0), (treatment =0)'
      f_test = res1.f_test(hyp)
      #print f_test
      ls_rows_res.append([id_station,
                          res0.params.ix['ref_price'],
                          res0.bse.ix['ref_price'],
                          res0.params.ix['treatment'],
                          res0.bse.ix['treatment'],
                          res0.tvalues.ix['treatment'],
                          res0.pvalues.ix['treatment'],
                          res0.rsquared,
                          res0.rsquared_adj,
                          res0.resid.autocorr(),
                          res0.nobs,
                          float(f_test.pvalue)])
    else:
      ls_ids_nodata.append(id_station)
  except:
    ls_ids_nores.append(id_station)

df_res = pd.DataFrame(ls_rows_res,
                      columns = ['id_station',
                                 'c_ref_price',
                                 'b_ref_price',
                                 'c_treatment',
                                 'b_treatment',
                                 't_treatment',
                                 'p_treatment',
                                 'r2',
                                 'r2a',
                                 'r_ac',
                                 'nobs',
                                 'p_chow'])
df_res.set_index('id_station', inplace = True)

# #########
# OVERVIEW
# #########

#print(u'Nb w/ problematic R2 (excluded):',
#      len(df_res[(~np.isfinite(df_res['r2'])) |
#                  (df_res['r2'] < 0)]))
#df_res = df_res[(np.isfinite(df_res['r2'])) &\
#                (df_res['r2'] >= 0)]

print()
print(u'Overview of regression results:')
print(df_res.describe().to_string())

# Inspect significant treatments
df_res_sig = df_res[df_res['p_treatment'] <= 0.05]
print()
print(u'Nb sig treatments:', len(df_res_sig))
print(u'Nb sig above 1c:', len(df_res_sig[df_res_sig['c_treatment'] >= 0.01]))
print(u'Nb sig below -1c:', len(df_res_sig[df_res_sig['c_treatment'] <= -0.01]))

# Check: one not always capture due to date (need closest competitor)
print()
print(df_res[df_res.index.isin(['95100025',  '91000006', '5100004'])].to_string())


# Inspect increases and decreases by station group
ls_ids_inc = df_res_sig[df_res_sig['c_treatment'] >= 0.01].index
ls_ids_dec = df_res_sig[df_res_sig['c_treatment'] <= -0.01].index
print()
print(u'Inspect increases in price:')
print(df_info.ix[ls_ids_inc]['group_last'].value_counts())
print()
print(u'Inspect decreases in price:')
print(df_info.ix[ls_ids_dec]['group_last'].value_counts())

# Enrich
df_res = pd.merge(df_res,
                  df_info[['brand_last']],
                  left_index = True,
                  right_index = True,
                  how = 'left')
df_res = pd.merge(df_res,
                  df_ta[['id_total_ta',
                         'dist_total_ta',
                         'date_min_total_ta',
                         'date_max_total_ta']],
                  left_index = True,
                  right_index = True,
                  how = 'left')

## temp: get rid of high treatment (pbm with data)
#df_res = df_res[df_res['c_treatment'].abs() <= 0.1]
#
#print(df_res[(df_res['brand_last'] == 'BP') &\
#             (df_res['p_treatment'] <= 0.05) &\
#             (df_res['c_treatment'] <= -0.1)].to_string())
#
#print(df_res[(df_res['brand_last'] == 'LECLERC') &\
#             (df_res['p_treatment'] <= 0.05)]['c_treatment'].describe())
#
#print(df_res[(df_res['brand_last'] == 'LECLERC')]['c_treatment'].describe())
#
## TOTAL STATIONS
#print(df_res[(df_res['p_treatment'] <= 0.05) &\
#             (df_res['c_treatment'] >= 0.01)].to_string())
