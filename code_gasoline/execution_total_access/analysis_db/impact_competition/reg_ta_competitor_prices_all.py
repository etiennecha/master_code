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

ls_ta_chge_ids = list(df_info_ta.index[(df_info_ta['pp_chge'] >= 0.02) &\
                                       (~pd.isnull(df_info_ta['date_beg']))])

df_dd_control = pd.DataFrame(df_prices_ht[ls_control_ids].mean(1), df_prices_ht.index, ['price'])
df_dd_control['time'] = df_dd_control.index
ls_df_dd = []
ls_station_fe_vars = []
ls_treatment_vars = []
ls_rows_close_ta = []
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
      df_dd_comp = pd.DataFrame(df_prices_ht[id_station].values, df_prices_ht.index, ['price'])
      df_dd_comp.loc[date_beg:date_end, 'price'] = np.nan
      df_dd_comp['time'] = df_dd_comp.index
      df_dd_comp['fe_%s' %id_station] = 1
      df_dd_comp['tr_%s' %id_station] = 0
      df_dd_comp.loc[date_end:, 'tr_%s' %id_station] = 1
      ls_df_dd.append(df_dd_comp)
      ls_station_fe_vars.append('fe_%s' %id_station)
      ls_treatment_vars.append('tr_%s' %id_station)
      ls_rows_close_ta.append((id_station, id_ta, distance))

print u'\nLoop finished'

# start, end = 0, 100
ls_df_res = []
for i in range(0, 300, 100):
  start, end = i, i+100
  df_dd = pd.concat([df_dd_control] + ls_df_dd[start:end], ignore_index = True)
  df_dd.fillna(value = {x : 0 for x in ls_station_fe_vars[start:end] +\
                                       ls_treatment_vars[start:end]},
               inplace = True)
  
  str_station_fe = ' + '.join(ls_station_fe_vars[start:end])
  str_treatment = ' + '.join(ls_treatment_vars[start:end])
  
  df_dd = df_dd[~pd.isnull(df_dd['price'])]
  
  print u'\nDataframe built'
  
  reg_dd_res = smf.ols('price ~ C(time) + %s + %s' %(str_station_fe, str_treatment),
                       data = df_dd,
                       missing = 'drop').fit()
  
  print u'\nReg finished'
  
  ls_tup_coeffs = zip(reg_dd_res.params.index.values.tolist(),
                      reg_dd_res.params.values.tolist(),
                      reg_dd_res.bse.values.tolist(),
                      reg_dd_res.tvalues.values.tolist(),
                      reg_dd_res.pvalues.values.tolist())
  
  ls_tup_treatment = [list(coeff) for coeff in ls_tup_coeffs if 'tr_' in coeff[0]]
  ls_rows_treatment = [[row[0][3:]] + row[1:] for row in ls_tup_treatment]
  df_res_temp = pd.DataFrame(ls_rows_treatment,
                             columns = ['id_station', 'coeff', 'se', 'tval', 'pval'])
  df_res_temp.set_index('id_station', inplace = True)
  ls_df_res.append(df_res_temp)

df_res = pd.concat(ls_df_res)

# add nearby TA id and distance
df_close_ta = pd.DataFrame(ls_rows_close_ta, columns = ['id_station', 'id_ta', 'distance'])
df_close_ta.set_index('id_station', inplace = True)
df_res = pd.merge(df_res,
                  df_close_ta,
                  how = 'left',
                  left_index = True,
                  right_index = True)

# add brand
df_res = pd.merge(df_res,
                  df_info[['brand_0']],
                  how = 'left',
                  left_index = True,
                  right_index = True)

df_res_sf = df_res[df_res['pval'] <= 0.05].copy()
df_res_sf.sort('coeff', inplace = True)

# describe by brand
ls_df_desc = []
ls_desc_brands = df_res_sf['brand_0'].value_counts()[0:10].index
for brand in ls_desc_brands:
  df_temp_desc = df_res_sf['coeff'][\
                    df_res_sf['brand_0'] == brand].describe()
  ls_df_desc.append(df_temp_desc)
df_desc = pd.concat(ls_df_desc, axis = 1, keys = ls_desc_brands)
df_desc.rename(columns = {'CARREFOUR_MARKET' : 'CARREFOUR_M'}, inplace = True)
print df_desc.to_string()

### #################
### STACK AND ANALYSE
### #################
##
##df_dd_su = pd.concat(ls_df_res, ignore_index = True)
##df_dd_su = pd.merge(df_dd_su,
##                    df_info[['brand_0']],
##                    how = 'left',
##                    left_on = 'id_station',
##                    right_index = True)
##
### ADD TYPE: SUP OIL or do by brand
##ls_gr_total = ['ELF', 'ELAN', 'TOTAL', 'TOTAL_ACCESS']
##df_dd_su_cl = df_dd_su[~(df_dd_su['brand_0'].isin(ls_gr_total))].copy()
### todo: inspect problems
##df_dd_su_cl = df_dd_su_cl[df_dd_su_cl['se'] < 1]
### can be duplicates... could sort and keep highest drop
##
##df_dd_su_cl['coeff'][df_dd_su_cl['pval'] <= 0.05].describe()
##df_dd_su_cl_sf = df_dd_su_cl[df_dd_su_cl['pval'] <= 0.05].copy()
##df_dd_su_cl_sf.sort('coeff', ascending = True, inplace = True)
##
### #######
### GRAPHS
### #######

# Obfuscate then match TA price (check 2100012)
# 95100025   -0.077 0.001 -107.343 0.000  95100016     0.070
ax = df_prices_ht[['95100025', '95100016']].plot()
df_prices_ht[ls_control_ids].mean(1).plot(ax = ax)
plt.show()

# Match TA price then give up
# 91000006   -0.057 0.001  -68.342 0.000  91000003     1.180
ax = df_prices_ht[['91000006', '91000003']].plot()
df_prices_ht[ls_control_ids].mean(1).plot(ax = ax)
plt.show()

# Match TA price
ax = df_prices_ht[['5100004', '5100007']].plot()
df_prices_ht[ls_control_ids].mean(1).plot(ax = ax)
plt.show()

##
#### Highest coeffs: interesting stories
###  coeff    se    tval  pval id_station  dist     id_TA           brand_0
### -0.061 0.001 -52.103 0.000   91000006 3.310  91130002              AVIA
### -0.056 0.001 -38.847 0.000   91000006 1.180  91000003              AVIA
### -0.052 0.001 -37.759 0.000   95100025 2.610  95100028              ESSO
### -0.051 0.002 -33.315 0.000   95100025 3.120  78800002              ESSO
### -0.049 0.001 -64.158 0.000   74000013 0.240  74000003              AGIP
### -0.048 0.001 -41.728 0.000    5100004 0.000   5100007  CARREFOUR_MARKET
### -0.044 0.002 -27.133 0.000   66000015 2.500  66000009            DYNEFF
### -0.038 0.002 -21.534 0.000   95100025 4.270  95370004              ESSO
### -0.038 0.001 -37.516 0.000   54520004 0.150  54520003              AVIA
### -0.037 0.001 -53.502 0.000   77170007 3.520  77150001       INTERMARCHE
##
##
###ls_visu = [id_station] + ['88300004', '88300005', '88300001', '88300006', '88300007', '88307001']
###ls_visu_2 = [id_station] + ['88300004', '88300005', '88300001', '88307001']
###
###df_info.ix[ls_visu]['brand_0']
###
###df_visu = df_prices_ht[ls_visu]
###df_visu = df_visu - df_prices_ht[ls_control_ids].mean(1)
###df_visu.plot()
###plt.show()
