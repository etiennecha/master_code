#!/usr/bin/python
# -*- coding: utf-8 -*-

import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built_paper = os.path.join(path_data,
                                    u'data_gasoline',
                                    u'data_built',
                                    u'data_paper_total_access')

path_dir_built_csv = os.path.join(path_dir_built_paper,
                                  u'data_csv')

path_dir_built_graphs = os.path.join(path_dir_built_paper,
                                     'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_match = os.path.join(path_dir_insee, 'match_insee_codes')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ################
# LOAD DATA
# ################

## LOAD DF PRICES
#df_prices_ttc = pd.read_csv(os.path.join(path_dir_built_csv,
#                                         'df_prices_ttc_final.csv'),
#                        parse_dates = ['date'])
#df_prices_ttc.set_index('date', inplace = True)

# LOAD DF INFO TA
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

# LOAD DF INFO
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

# LOAD DF COMP
df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                  'df_comp.csv'),
                      dtype = {'id_station' : str},
                      encoding = 'utf-8')
df_comp.set_index('id_station', inplace = True)

df_info = pd.merge(df_info,
                   df_comp,
                   how = 'left',
                   left_index = True,
                   right_index = True)

df_info_ta = pd.merge(df_info_ta,
                      df_comp,
                      how = 'left',
                      left_index = True,
                      right_index = True)

ls_title_dfs = [('Total Access',            df_info_ta),
                ('Total - TA',              df_info_ta[df_info_ta['brand_0'] == 'TOTAL']),
                ('Elf - TA',                df_info_ta[df_info_ta['brand_0'] == 'ELF']),
                ('<= 3 km to TA',           df_info[(df_info['group'] != 'TOTAL') &\
                                                    (df_info['dist_ta_0'] <= 3)]),
                ('3 < x <= 5 km to TA',     df_info[(df_info['group'] != 'TOTAL') &\
                                                   (df_info['dist_ta_0'] > 3) &\
                                                   (df_info['dist_ta_0'] <= 5)]),
                ('> 10 km to TA',           df_info[(df_info['group'] != 'TOTAL') &\
                                                    (df_info['dist_ta_0'].isnull())])]

for title, df_temp in ls_title_dfs:
  print u'\n', title
  print df_temp[['nb_c_1km', 'nb_c_2km', 'nb_c_3km', 'dist_c', 'dist_c_sup']].describe()

# One issue: different market conditions a bit further!
# Possible solution: check Elf-TA (no shock) vs. Total-TA (shock)
# But are competitors of Elf-TA similar to Total-TA?

## ###################
## MARKET COMPETITION
## ###################
#
## need to overwrite group to count independent as unique or within brand
## problem brand_0 is not unique either: need to keep original brand (temp fix)
#df_info.loc[(df_info['group'] == 'INDEPENDANT') |\
#            (df_info['group'].isnull()),
#            'group'] = df_info.index.astype(str)
#se_group_vc = df_info['group'].value_counts()
#ls_top10_groups = list(se_group_vc[0:10].index)
#
## INSEE AREAS
#
## should be done before (Also: get rid of DOMTOM & CORSICA)
#df_au_agg = df_au_agg[(df_au_agg.index != '000') &\
#                      (df_au_agg.index != '997') &\
#                      (df_au_agg.index != '998')]
#df_uu_agg = df_uu_agg[~df_uu_agg['LIBUU2010'].str.contains('Communes rurales')]
#
## TODO: loop and store results
## TODO: interact with robust stable markets
## TODO: exploit commuter DATA to link AUs?
## TODO: compare with ZAGAZ (no need for matching)
#
#area_field, area_lib, df_area_agg = 'AU2010', 'LIBAU2010', df_au_agg
##area_field, area_lib, df_area_agg = 'UU2010', 'LIBUU2010', df_uu_agg
##area_field, area_lib, df_area_agg = 'BV', 'LIBBV', df_bv_agg
#
#ls_se_area_ms = []
#for area in df_info[area_field].unique():
#  se_area_groups = df_info[df_info[area_field] == area]['group'].value_counts()
#  se_area_ms = se_area_groups.astype(float) * 100 / se_area_groups.sum()
#  ls_se_area_ms.append(se_area_ms)
#df_area_ms = pd.concat(ls_se_area_ms, keys = df_info[area_field].unique(), axis = 1)
#df_area_ms.fillna(0, inplace = True)
#df_area_ms = df_area_ms.T
#
#df_area = pd.merge(df_area_ms,
#                   df_area_agg,
#                   how = 'right',
#                   left_index = True,
#                   right_index = True)
#
## add HHI and CR1-3 (why groups not kept? check out of AUs?)
#ls_area_groups = list(df_area_ms.columns)
#df_area['HHI'] = df_area[ls_area_groups].apply(lambda x: (x**2).sum(), axis = 1)
#for i in range(1,4):
#  df_area['CR%s' %i] = df_area[ls_area_groups].apply(lambda x: sum(sorted(x)[-i:]), axis = 1)
#
## Display top 10 group (in general) in top 10 AUs
#ls_disp_comp = [area_lib] + ['P10_POP', 'HHI', 'CR1', 'CR2', 'CR3'] + ls_top10_groups
#df_area.sort('P10_POP', inplace = True, ascending = False)
#df_area['P10_POP'] = df_area['P10_POP'] / 1000
#pd.set_option('float_format', '{:,.0f}'.format)
#
#print u'\nTop 20', area_field, 'by pop:'
#print df_area[ls_disp_comp][0:20].to_string()
#
#print u'\nHHI >= 2500: {:d}'.format(len(df_area[df_area['HHI'] >= 2500]))
#print u'\n', df_area[ls_disp_comp][df_area['HHI'] >= 2500][0:20].to_string()
#
#print u'\nCR1 >= 50 {:d}'.format(len(df_area[df_area['CR1'] >= 50]))
#print u'\n', df_area[ls_disp_comp][df_area['CR1'] >= 50][0:20].to_string()
#
#print u'\nCR1 == 100: {:d}'.format(len(df_area[df_area['CR1'] == 100]))
#print u'\n', df_area[ls_disp_comp][df_area['CR1'] == 100][0:20].to_string()
#
#print u'\nCR2 == 100: {:d}'.format(len(df_area[df_area['CR2'] == 100]))
#print u'\n', df_area[ls_disp_comp][df_area['CR2'] == 100][0:20].to_string()
