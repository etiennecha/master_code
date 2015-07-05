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
# LOAD DATA
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
                                       ['pp_chge_date', 'ta_chge_date',
                                        'date_beg', 'date_end'])
df_info_ta.set_index('id_station', inplace = True)

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

df_prices_ht = pd.read_csv(os.path.join(path_dir_built_csv,
                                        'df_prices_ht_final.csv'),
                        parse_dates = ['date'])
df_prices_ht.set_index('date', inplace = True)

df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
                                         'df_prices_ttc_final.csv'),
                        parse_dates = ['date'])
df_prices_ttc.set_index('date', inplace = True)

df_station_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_station_stats.csv'),
                               encoding = 'utf-8',
                               dtype = {'id_station' : str})
df_station_stats.set_index('id_station', inplace = True)

# LOAD COMPETITION

dict_ls_comp = dec_json(os.path.join(path_dir_built_json,
                                     'dict_ls_comp.json'))

df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_comp.csv'),
                      dtype = {'id_station' : str,
                               'id_ta_0' : str,
                               'id_ta_1' : str,
                               'id_ta_2' : str},
                      encoding = 'utf-8')
df_comp.set_index('id_station', inplace = True)

df_info = pd.merge(df_info,
                   df_comp,
                   how = 'left',
                   left_index = True,
                   right_index = True)

# ###################
# FILTER DATA
# ###################

ls_keep_info = list(df_info[df_info['highway'] != 1].index)
ls_keep_stats = list(df_station_stats[(df_station_stats['nb_chge'] >= 5) &\
                                      (df_station_stats['pct_chge'] >= 0.03)].index)
ls_keep_ids = list(set(ls_keep_info).intersection(set(ls_keep_stats)))

ls_ta_ids = list(df_info_ta.index)

dict_ls_ta_comp = {}
for id_station, ls_comp in dict_ls_comp.items():
  ls_ta_comp = [(comp_id, distance) for comp_id, distance in ls_comp\
                                    if comp_id in ls_ta_ids]
  dict_ls_ta_comp[id_station] = ls_ta_comp

ls_control_ids = []
for id_station, ls_ta_comp in dict_ls_ta_comp.items():
  if (id_station in ls_keep_ids) and\
     ((not ls_ta_comp) or\
      (ls_ta_comp[0][1] > 10)):
    ls_control_ids.append(id_station)

# ##########
# PARAMETERS
# ##########

df_prices = df_prices_ttc

### ##########################################
### LONG PANEL: COMP OF TOTAL => TOTAL ACCESS
### ##########################################
#
#
#dum_dist_max_control = True # False for old setting: only require far enough
#dist_comp, dist_max_control = 5, 10 # dist_comp 10 for old setting else 5, (10)
#
## Keep only non Total stations
#df_comp = df_info[(df_info['group'] != 'TOTAL') &\
#                  (df_info['group_last'] != 'TOTAL')].copy()
#
## TOTAL-TA COMPETITORS
#
## Keep only competitors of TA with chge
#ls_ta_chge_ids = list(df_info_ta.index[(df_info_ta['pp_chge'] >= 0.04) &\
#                                       (~pd.isnull(df_info_ta['date_beg']))])
#
## Keep only if Total => Total Access among competitors
#df_tta_comp =\
#  df_comp[df_comp.apply(\
#    lambda x: any(((y in ls_ta_chge_ids) and (z <= dist_comp))\
#                    for (y, z) in zip(x[['id_ta_{:d}'.format(i) for i in range(10)]].values,
#                                      x[['dist_ta_{:d}'.format(i) for i in range(10)]].values)),
#    axis = 1)]
#
## CONTROL (FAR AND CLOSE ENOUGH TO TA STATIONS)
#
## Want close/far enough to TA
#ls_ta_ids = list(df_info_ta.index)
#
## Exclude if a TA too close
#df_control_comp =\
#  df_comp[~df_comp.apply(\
#    lambda x: any(z <= dist_comp for z in x[['dist_ta_{:d}'.format(i) for i in range(10)]].values),
#    axis = 1)]
#
## Exclude if all TA too far
#if dum_dist_max_control:
#  df_control_comp =\
#    df_control_comp[~df_control_comp.apply(\
#      lambda x: all(((pd.isnull(z)) or (z > dist_max_control))\
#                      for z in x[['dist_ta_{:d}'.format(i) for i in range(10)]].values),
#      axis = 1)]
#
## STATS DES  
#print u'\nTotal-TA: Stats des: Departement, Nb Elf-TA comp, Nb controls'
#c_control_pbm = 0
#for i in range(0,96):
#	nb_tta_comp = len(df_tta_comp[df_tta_comp['dpt'] == '{:2d}'.format(i)])
#	nb_control = len(df_control_comp[df_control_comp['dpt'] == '{:2d}'.format(i)])
#	if nb_tta_comp != 0:
#		print '{:2d}'.format(i), '{:2d}'.format(nb_tta_comp), nb_control
#		if nb_control < 5:
#			c_control_pbm += 1
#
#print u'\nNb Departements with st. less than 5 controls:', c_control_pbm
#
#ls_df_res = []
#ls_rows_tot_comp_details = []
#for dpt in df_tta_comp['dpt'].unique():
#  df_dpt_tta_comp = df_tta_comp[df_tta_comp['dpt'] == dpt]
#  ls_not_treated = list(df_control_comp[df_control_comp['dpt'] == dpt].index)
#  if len(ls_not_treated) >= 5:
#    try:
#      # loop to create station dfs and concatenate
#      # time and id_station as string to generate categorical vars
#      # treatment for each treated
#      ls_df_temp = []
#      for id_station, row_station in df_dpt_tta_comp.iterrows():
#        df_temp = df_prices[[id_station]].copy()
#        df_temp.rename(columns = {id_station : 'price'}, inplace = True)
#        for id_ta in ['id_ta_{:d}'.format(i) for i in range(10)]:
#          # has to be true for some
#          if row_station[id_ta] in ls_ta_chge_ids:
#            date_beg = df_info_ta.ix[row_station[id_ta]]['date_beg']
#            date_end = df_info_ta.ix[row_station[id_ta]]['date_end']
#            ls_rows_tot_comp_details.append((id_station,
#                                             row_station['group_type'],
#                                             row_station[id_ta],
#                                             row_station['dist_ta_{:s}'.format(id_ta[-1])]))
#            break
#        df_temp.loc[date_beg:date_end, 'price'] = np.nan
#        df_temp['time'] = df_temp.index
#        df_temp['time'] = df_temp['time'].apply(lambda x: x.strftime('%Y-%m-%d'))
#        df_temp['id_station'] = id_station
#        df_temp['tr_%s' %id_station] = 0
#        df_temp.loc[date_end:, 'tr_%s' %id_station] = 1
#        ls_df_temp.append(df_temp)
#      for id_station in ls_not_treated:
#        df_temp = df_prices[[id_station]].copy()
#        df_temp.rename(columns = {id_station : 'price'}, inplace = True)
#        df_temp['time'] = df_temp.index
#        df_temp['time'] = df_temp['time'].apply(lambda x: x.strftime('%Y-%m-%d'))
#        df_temp['id_station'] = id_station
#        ls_df_temp.append(df_temp)
#      df_dpt = pd.concat(ls_df_temp, ignore_index = True, axis = 0)
#      ls_tr_vars = [col for col in df_dpt.columns if col[0:3] == u'tr_']
#      for tr_var in ls_tr_vars:
#        df_dpt.loc[df_dpt[tr_var].isnull(), tr_var] = 0
#        # df_dpt[tr_var] = df_dpt[tr_var].astype(int)
#      
#      ## Two way fe regression (todo: exploit sparsity)
#      #df_dpt = df_dpt[~df_dpt['price'].isnull()]
#      #reg = smf.ols('price ~ C(id_station) + C(time) + ' + ' + '.join(ls_tr_vars),
#      #              data = df_dpt,
#      #              missing = 'drop').fit()
#      #ls_tup_coeffs = zip(reg.params.index.values.tolist(),
#      #                    reg.params.values.tolist(),
#      #                    reg.bse.values.tolist(),
#      #                    # reg.HC0_se,
#      #                    reg.tvalues.values.tolist(),
#      #                    reg.pvalues.values.tolist())
#      #df_tc = pd.DataFrame(ls_tup_coeffs, columns = ['name', 'coeff', 'se', 'tval', 'pval'])
#      #print df_tc[df_tc['name'].str.startswith('tr_')].to_string()
#      
#      # Two way fe regression
#      df_dpt.set_index(['time', 'id_station'], inplace = True, verify_integrity = True)
#      reg_pooled  = PanelOLS(y=df_dpt['price'],
#                             x=df_dpt[ls_tr_vars],
#                             time_effects=True,
#                             entity_effects=True)
#      #print reg_pooled
#      ls_tup_coeffs = zip(reg_pooled.beta.index.values.tolist(),
#                          reg_pooled.beta.tolist(),
#                          reg_pooled.std_err.tolist(),
#                          reg_pooled.t_stat.tolist(),
#                          reg_pooled.p_value.tolist())
#      df_res_temp = pd.DataFrame(ls_tup_coeffs, columns = ['name', 'coeff', 'se', 'tval', 'pval'])
#      ls_df_res.append(df_res_temp)
#    except:
#       print u'Pbm with estimation of dpt', dpt
#
#df_res = pd.concat(ls_df_res, axis = 0)
#
## todo: keep only stations for which price data before and after treatment
## for now: multicolinearity between treatment and station_fe hence need...
#df_res = df_res[df_res['coeff'].abs() < 10]
#
#df_res_tr = df_res[df_res['name'].str.startswith('tr_')]
#
#print u'\nNb of estimated treatments {:d}'.format(len(df_res_tr))
## One np.inf in std => dropped for now
#df_res_tr = df_res_tr[df_res_tr['tval'] != np.inf]
#print df_res_tr.describe()
#
## Merge with station details
#df_res_tr['id_station'] = df_res_tr['name'].apply(lambda x: x[3:])
#df_res_tr.set_index('id_station', inplace = True)
#df_tta_comp_details = pd.DataFrame(ls_rows_tot_comp_details,
#                                   columns = ['id_station',
#                                              'group_type',
#                                              'id_ta',
#                                              'distance'])
#df_tta_comp_details.set_index('id_station', inplace = True)
#
#df_tta_comp_final = pd.merge(df_res_tr,
#                             df_tta_comp_details,
#                             left_index = True,
#                             right_index = True,
#                             how = 'left')
#
#
#ls_pctiles = [0.1, 0.25, 0.5, 0.75, 0.9]
#
#dist_display = 5
#print u'\nMax distance for treatment display:', dist_display
#
#print df_tta_comp_final[df_tta_comp_final['distance'] <= dist_display]\
#        .describe(percentiles = ls_pctiles)
#
#print u'\nSupermarkets'
#print df_tta_comp_final[(df_tta_comp_final['group_type'] == 'SUP') &\
#                        (df_tta_comp_final['distance'] <= dist_display)]\
#        .describe(percentiles = ls_pctiles)
#
#print u'\nOthers'
#print df_tta_comp_final[(df_tta_comp_final['group_type'] != 'SUP') &\
#                        (df_tta_comp_final['distance'] <= dist_display)]\
#        .describe(percentiles = ls_pctiles)
#
##df_tta_comp_final.to_csv(os.path.join(path_dir_built_csv,
##                                      'df_tta_by_dpt_final.csv'),
##                         encoding = 'utf-8',
##                         index = False)

# ########################################
# LONG PANEL: COMP OF ELF => TOTAL ACCESS
# ########################################

dum_dist_max_control = True # False for old setting: only require far enough
dist_comp, dist_max_control = 5, 10 # dist_comp 10 for old setting else 5, (10)

# Keep only non Total stations
df_comp = df_info[(df_info['group'] != 'TOTAL') &\
                  (df_info['group_last'] != 'TOTAL')].copy()

# ELF-TA COMPETITORS

# Keep only competitors of Elf => TA
ls_elf_chge_ids = list(df_info_ta.index[(df_info_ta['brand_0'] == 'ELF')])
# Exclude if TA which was not Elf around (conservative)
ls_ta_not_elf_ids = list(df_info_ta.index[(df_info_ta['brand_0'] != 'ELF')])

# Keep only if Elf => Total Access among competitors
df_elf_comp =\
  df_comp[df_comp.apply(\
    lambda x: any(((y in ls_elf_chge_ids) and (z <= dist_comp))\
                    for (y, z) in zip(x[['id_ta_{:d}'.format(i) for i in range(10)]].values,
                                      x[['dist_ta_{:d}'.format(i) for i in range(10)]].values)),
    axis = 1)]

# Exclude if Total => Total Access among competitors
df_elf_comp =\
  df_elf_comp[~df_elf_comp.apply(\
    lambda x: any(((y in ls_ta_not_elf_ids) and (z <= dist_comp))\
                    for (y, z) in zip(x[['id_ta_{:d}'.format(i) for i in range(10)]].values,
                                      x[['dist_ta_{:d}'.format(i) for i in range(10)]].values)),
    axis = 1)]

# CONTROL (FAR AND CLOSE ENOUGH TO TA STATIONS)

# Want close/far enough to TA
ls_ta_ids = list(df_info_ta.index)

# Exclude if a TA too close
df_control_comp =\
  df_comp[~df_comp.apply(\
    lambda x: any(z <= dist_comp for z in x[['dist_ta_{:d}'.format(i) for i in range(10)]].values),
    axis = 1)]

# Exclude if all TA too far
if dum_dist_max_control:
  df_control_comp =\
    df_control_comp[~df_control_comp.apply(\
      lambda x: all(((pd.isnull(z)) or (z > dist_max_control))\
                      for z in x[['dist_ta_{:d}'.format(i) for i in range(10)]].values),
      axis = 1)]

print u'\nNb of Elf-TA competitors kept: {:d}'.format(len(df_elf_comp))

# STATS DES  
print u'\nElf-TA: Stats des: Departement, Nb Elf-TA comp, Nb controls'
c_control_pbm = 0
for i in range(0,96):
	nb_elf_comp = len(df_elf_comp[df_elf_comp['dpt'] == '{:2d}'.format(i)])
	nb_control = len(df_control_comp[df_control_comp['dpt'] == '{:2d}'.format(i)])
	if nb_elf_comp != 0:
		print '{:2d}'.format(i), '{:2d}'.format(nb_elf_comp), nb_control
		if nb_control < 5:
			c_control_pbm += 1

print u'\nNb Departements with st. less than 5 controls:', c_control_pbm

ls_df_elf_res = []
ls_rows_elf_comp_details = []
for dpt in df_elf_comp['dpt'].unique():
  df_dpt_elf_comp = df_elf_comp[df_elf_comp['dpt'] == dpt]
  ls_not_treated = list(df_control_comp[df_control_comp['dpt'] == dpt].index)
  if len(ls_not_treated) >= 5:
    # loop to create station dfs and concatenate
    # time and id_station as string to generate categorical vars
    # treatment for each treated
    ls_df_temp = []
    for id_station, row_station in df_dpt_elf_comp.iterrows():
      df_temp = df_prices[[id_station]].copy()
      df_temp.rename(columns = {id_station : 'price'}, inplace = True)
      for id_ta in ['id_ta_{:d}'.format(i) for i in range(10)]:
        if row_station[id_ta] in ls_elf_chge_ids:
          date_beg = df_info_ta.ix[row_station[id_ta]]['day_1'] - pd.Timedelta(days = 10)
          date_end = df_info_ta.ix[row_station[id_ta]]['day_1'] + pd.Timedelta(days = 10)
          ls_rows_elf_comp_details.append((id_station,
                                           row_station['group_type'],
                                           row_station[id_ta],
                                           row_station['dist_ta_{:s}'.format(id_ta[-1])]))
          break
      df_temp.loc[date_beg:date_end, 'price'] = np.nan
      df_temp['time'] = df_temp.index
      df_temp['time'] = df_temp['time'].apply(lambda x: x.strftime('%Y-%m-%d'))
      df_temp['id_station'] = id_station
      df_temp['tr_%s' %id_station] = 0
      df_temp.loc[date_end:, 'tr_%s' %id_station] = 1
      ls_df_temp.append(df_temp)
    for id_station in ls_not_treated:
      df_temp = df_prices[[id_station]].copy()
      df_temp.rename(columns = {id_station : 'price'}, inplace = True)
      df_temp['time'] = df_temp.index
      df_temp['time'] = df_temp['time'].apply(lambda x: x.strftime('%Y-%m-%d'))
      df_temp['id_station'] = id_station
      ls_df_temp.append(df_temp)
    df_elf_dpt = pd.concat(ls_df_temp, ignore_index = True, axis = 0)
    ls_tr_vars = [col for col in df_elf_dpt.columns if col[0:3] == u'tr_']
    for tr_var in ls_tr_vars:
      df_elf_dpt.loc[df_elf_dpt[tr_var].isnull(), tr_var] = 0
      # df_elf_dpt[tr_var] = df_elf_dpt[tr_var].astype(int)
    
    # Two way fe regression
    df_elf_dpt.set_index(['time', 'id_station'], inplace = True, verify_integrity = True)
    reg_elf_pooled  = PanelOLS(y=df_elf_dpt['price'],
                               x=df_elf_dpt[ls_tr_vars],
                               time_effects=True,
                               entity_effects=True)
    #print reg_pooled
    ls_elf_tup_coeffs = zip(reg_elf_pooled.beta.index.values.tolist(),
                            reg_elf_pooled.beta.tolist(),
                            reg_elf_pooled.std_err.tolist(),
                            reg_elf_pooled.t_stat.tolist(),
                            reg_elf_pooled.p_value.tolist())
    df_res_elf_temp = pd.DataFrame(ls_elf_tup_coeffs,
                                   columns = ['name', 'coeff', 'se', 'tval', 'pval'])
    ls_df_elf_res.append(df_res_elf_temp)

df_elf_res = pd.concat(ls_df_elf_res, axis = 0)

## todo: keep only stations for which price data before and after treatment
## for now: multicolinearity between treatment and station_fe hence need...
df_elf_res = df_elf_res[df_elf_res['coeff'].abs() < 10]

df_elf_res_tr = df_elf_res[df_elf_res['name'].str.startswith('tr_')]

print u'\nNb of estimated treatments {:d}'.format(len(df_elf_res_tr))
# One np.inf in std => dropped for now
df_elf_res_tr = df_elf_res_tr[df_elf_res_tr['tval'] != np.inf]
print df_elf_res_tr.describe()

# Merge with station details
df_elf_res_tr['id_station'] = df_elf_res_tr['name'].apply(lambda x: x[3:])
df_elf_res_tr.set_index('id_station', inplace = True)
df_elf_comp_details = pd.DataFrame(ls_rows_elf_comp_details,
                                   columns = ['id_station',
                                              'group_type',
                                              'id_ta',
                                              'distance'])
df_elf_comp_details.set_index('id_station', inplace = True)

df_elf_comp_final = pd.merge(df_elf_res_tr,
                             df_elf_comp_details,
                             left_index = True,
                             right_index = True,
                             how = 'left')

ls_pctiles = [0.1, 0.25, 0.5, 0.75, 0.9]

dist_display = 5
print u'\nMax distance for treatment display:', dist_display

print df_elf_comp_final[df_elf_comp_final['distance'] <= dist_display]\
        .describe(percentiles = ls_pctiles)

print u'\nSupermarkets'
print df_elf_comp_final[(df_elf_comp_final['group_type'] == 'SUP') &\
                        (df_elf_comp_final['distance'] <= dist_display)]\
        .describe(percentiles = ls_pctiles)

print u'\nOthers'
print df_elf_comp_final[(df_elf_comp_final['group_type'] != 'SUP') &\
                        (df_elf_comp_final['distance'] <= dist_display)]\
        .describe(percentiles = ls_pctiles)

#df_elf_comp_final.to_csv(os.path.join(path_dir_built_csv,
#                                      'df_elfta_by_dpt_final.csv'),
#                         encoding = 'utf-8',
#                         index = False)
