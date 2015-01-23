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

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv, 'df_prices_ttc_final.csv'),
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

## 1/ Check on TA w/ change in prices
#
#ax = df_prices_ht['63100006'].plot()
#df_prices_ht[ls_control_ids].mean(1).plot(ax = ax, label = 'control', legend = True)
#plt.show()
#
#date_beg = df_info_ta.ix['63100006']['date_beg']
#date_end = df_info_ta.ix['63100006']['date_end']
#
#df_dd_0 = pd.DataFrame(df_prices_ht['63100006'].values, df_prices_ht.index, ['price'])
#df_dd_1 = pd.DataFrame(df_prices_ht[ls_control_ids].mean(1), df_prices_ht.index, ['price'])
#
#for df_dd_temp in [df_dd_0, df_dd_1]:
#  df_dd_temp['time'] = df_dd_temp.index
#  df_dd_temp['treatment'] = 0
#  df_dd_temp['station_fe'] = 0
#df_dd_0.loc[date_beg:date_end, 'price'] = np.nan
#df_dd_0.loc[date_end:, 'treatment'] = 1
#df_dd_0['station_fe'] = 1
#
#df_dd = pd.concat([df_dd_0, df_dd_1], ignore_index = True)
#
## Estimation ok but slow: reduce time span or check use of efficient procedures?
#print smf.ols('price ~ station_fe + treatment + C(time)',
#              data = df_dd,
#              missing = 'drop').fit().summary()

#  2/ Check on all its competitors (one regression with two categorical variable)

# check station: 88300007

print u'\nStarting diff-in-diff regressions:'
ls_df_res = []
for id_station in df_info_ta.index[df_info_ta['pp_chge'] >= 0.05][0:10]:
  try:
    print 'Loop with:', id_station
    #id_station = '88300002'
    date_beg = df_info_ta.ix[id_station]['date_beg']
    date_end = df_info_ta.ix[id_station]['date_end']
    # should filter for group too
    ls_comp = [id_comp for (id_comp, distance) in dict_ls_comp[id_station] if distance <= 5]
    
    df_dd_control = pd.DataFrame(df_prices_ht[ls_control_ids].mean(1), df_prices_ht.index, ['price'])
    df_dd_control['time'] = df_dd_control.index
    ls_df_dd = [df_dd_control]
    for id_comp in ls_comp:
      df_dd_comp = pd.DataFrame(df_prices_ht[id_comp].values, df_prices_ht.index, ['price'])
      df_dd_comp.loc[date_beg:date_end, 'price'] = np.nan
      df_dd_comp['time'] = df_dd_comp.index
      df_dd_comp['fe_%s' %id_comp] = 1
      df_dd_comp['tr_%s' %id_comp] = 0
      df_dd_comp.loc[date_end:, 'tr_%s' %id_comp] = 1
      ls_df_dd.append(df_dd_comp)
    df_dd = pd.concat(ls_df_dd, ignore_index = True)
    
    ls_station_fe_vars = ['fe_%s' %id_comp for id_comp in ls_comp]
    ls_treatment_vars = ['tr_%s' %id_comp for id_comp in ls_comp]
    
    df_dd.fillna(value = {x : 0 for x in ls_station_fe_vars + ls_treatment_vars},
                 inplace = True)
    
    # df_dd.fillna(0, inplace = True)
    ## unsure about that part (index not unique)
    #df_dd.loc[date_beg:date_end,:] = np.nan
    
    str_station_fe = ' + '.join(ls_station_fe_vars)
    str_treatment = ' + '.join(ls_treatment_vars)
    
    df_dd = df_dd[~pd.isnull(df_dd['price'])] # not used anyway, else does not run
    reg_dd_res = smf.ols('price ~ C(time) + %s + %s' %(str_station_fe, str_treatment),
                         data = df_dd,
                         missing = 'drop').fit()
    
    # print reg_dd_res.summary()
    
    ls_tup_coeffs = zip(reg_dd_res.params.index.values.tolist(),
                        reg_dd_res.params.values.tolist(),
                        reg_dd_res.bse.values.tolist(),
                        reg_dd_res.tvalues.values.tolist(),
                        reg_dd_res.pvalues.values.tolist())
    
    ls_tup_treatment = [list(coeff) for coeff in ls_tup_coeffs if 'tr_' in coeff[0]]
    ls_rows_treatment = [[row[0][3:]] + row[1:] for row in ls_tup_treatment]
    df_res = pd.DataFrame(ls_rows_treatment, columns = ['id_station', 'coeff', 'se', 'tval', 'pval'])
    df_res.set_index('id_station', inplace = True)

    df_distance = pd.DataFrame(dict_ls_comp[id_station],
                               columns = ['id_station', 'dist'])
    df_res = pd.merge(df_res,
                      df_distance,
                      how = 'left',
                      left_index = True,
                      right_on = 'id_station')
    df_res['id_TA'] = id_station
    #print df_res.to_string()
    ## add brand and distance (also id_TA + date_TA if going to go big)
    ls_df_res.append(df_res)
  except:
    print u'Pbm with:', id_station

# #################
# STACK AND ANALYSE
# #################

df_dd_su = pd.concat(ls_df_res, ignore_index = True)
df_dd_su = pd.merge(df_dd_su,
                    df_info[['brand_0']],
                    how = 'left',
                    left_on = 'id_station',
                    right_index = True)

# ADD TYPE: SUP OIL or do by brand
ls_gr_total = ['ELF', 'ELAN', 'TOTAL', 'TOTAL_ACCESS']
df_dd_su_cl = df_dd_su[~(df_dd_su['brand_0'].isin(ls_gr_total))].copy()
# todo: inspect problems
df_dd_su_cl = df_dd_su_cl[df_dd_su_cl['se'] < 1]
# can be duplicates... could sort and keep highest drop

df_dd_su_cl['coeff'][df_dd_su_cl['pval'] <= 0.05].describe()
df_dd_su_cl_sf = df_dd_su_cl[df_dd_su_cl['pval'] <= 0.05].copy()
df_dd_su_cl_sf.sort('coeff', ascending = True, inplace = True)

# #######
# GRAPHS
# #######

## Highest coeffs: interesting stories
#  coeff    se    tval  pval id_station  dist     id_TA           brand_0
# -0.061 0.001 -52.103 0.000   91000006 3.310  91130002              AVIA
# -0.056 0.001 -38.847 0.000   91000006 1.180  91000003              AVIA
# -0.052 0.001 -37.759 0.000   95100025 2.610  95100028              ESSO
# -0.051 0.002 -33.315 0.000   95100025 3.120  78800002              ESSO
# -0.049 0.001 -64.158 0.000   74000013 0.240  74000003              AGIP
# -0.048 0.001 -41.728 0.000    5100004 0.000   5100007  CARREFOUR_MARKET
# -0.044 0.002 -27.133 0.000   66000015 2.500  66000009            DYNEFF
# -0.038 0.002 -21.534 0.000   95100025 4.270  95370004              ESSO
# -0.038 0.001 -37.516 0.000   54520004 0.150  54520003              AVIA
# -0.037 0.001 -53.502 0.000   77170007 3.520  77150001       INTERMARCHE


#ls_visu = [id_station] + ['88300004', '88300005', '88300001', '88300006', '88300007', '88307001']
#ls_visu_2 = [id_station] + ['88300004', '88300005', '88300001', '88307001']
#
#df_info.ix[ls_visu]['brand_0']
#
#df_visu = df_prices_ht[ls_visu]
#df_visu = df_visu - df_prices_ht[ls_control_ids].mean(1)
#df_visu.plot()
#plt.show()
