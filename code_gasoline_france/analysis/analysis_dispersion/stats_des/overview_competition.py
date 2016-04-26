#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
import add_to_path
from add_to_path import path_data
from generic_master_price import *
from generic_master_info import *

path_dir_built = os.path.join(path_data,
                              u'data_gasoline',
                              u'data_built',
                              u'data_scraped_2011_2014')
path_dir_built_csv = os.path.join(path_dir_built, u'data_csv')
path_dir_built_json = os.path.join(path_dir_built, u'data_json')
path_dir_built_graphs = os.path.join(path_dir_built, u'data_graphs')

path_dir_insee = os.path.join(path_data, 'data_insee')
path_dir_insee_extracts = os.path.join(path_dir_insee, 'data_extracts')

pd.set_option('float_format', '{:,.2f}'.format)
format_float_int = lambda x: '{:10,.0f}'.format(x)
format_float_float = lambda x: '{:10,.2f}'.format(x)

# ##############
# LOAD DATA
# ##############

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
                               'dpt' : str},
                      parse_dates = ['start', 'end', 'day_0', 'day_1', 'day_2'])
df_info.set_index('id_station', inplace = True)

# LOAD COMPETITION

dict_comp_dtype = {'id_ta_{:d}'.format(i) : str for i in range(23)}
dict_comp_dtype['id_station'] = str
df_comp = pd.read_csv(os.path.join(path_dir_built_csv,
                                   'df_comp.csv'),
                      dtype = dict_comp_dtype,
                      encoding = 'utf-8')
df_comp.set_index('id_station', inplace = True)

dict_close = dec_json(os.path.join(path_dir_built_json,
                                   'dict_ls_close.json'))

# LOAD PRICE STATS DES

df_price_stats = pd.read_csv(os.path.join(path_dir_built_csv,
                                          'df_station_stats.csv'),
                               dtype = {'id_station' : str},
                               encoding = 'utf-8')
df_price_stats.set_index('id_station', inplace = True)

# ######################
# CHECK AND FIX DF COMP
# ######################

df_info = df_info[(~(df_info['highway'] == 1)) &\
                  (~df_info['start'].isnull())]
ls_check = [x for x in df_info.index if x not in df_comp.index]
## todo: check
## some should no more be in df_info?
#[u'13680006', u'34500021',
# u'38200017', u'49070007',
# u'91220003', u'99999001', u'99999002']


lsd_comp = ['nb_c_1km', 'nb_c_3km', 'nb_c_5km',
            'nb_s_1km', 'nb_s_3km', 'nb_s_5km',
            'dist_c', 'dist_s', 'dist_c_sup']

ls_pctiles = [0.1, 0.25, 0.5, 0.75, 0.9]
print(u'Overview of competition (including Corsica)')
print(df_comp[lsd_comp].describe(percentiles = ls_pctiles).to_string())


df_info = pd.merge(df_info,
                   df_comp,
                   left_index = True,
                   right_index = True,
                   how = 'left')

# todo: set to nan dist_c_sup for Corsica
df_info.loc[df_info['reg'] == 'Corse',
            'dist_c_sup'] = np.nan

# todo: set to nan dist_s for independent / small groups?
df_info.loc[df_info['group'] == 'INDEPENDANT',
            'dist_s'] = np.nan

# todo: check stations for which dist_s = 0

# #########################
# OVERVIEW COMP BY REGION
# ########################

print()
print(u'Overview of competition (excluding Corsica)')
print(df_info[df_info['reg'] != u'Corse']\
             [lsd_comp].describe(percentiles = ls_pctiles).to_string())

print()
print(u'Overview of competition in Ile de France')
print(df_info[df_info['reg'] == 'Ile-de-France']\
             [lsd_comp].describe(percentiles = ls_pctiles).to_string())

print()
print(u'Overview of competition by region')
df_reg_comp = df_info[lsd_comp + ['reg']].groupby('reg').agg('mean')
df_reg_comp['count'] = df_info['reg'].value_counts()
df_reg_comp = df_reg_comp[['count'] + lsd_comp]
df_reg_comp.sort('count', ascending = False, inplace = True)
df_reg_comp.ix['TOTAL - France'] = df_info[lsd_comp].mean()
df_reg_comp.loc['TOTAL - France', 'count'] = df_reg_comp['count'].sum()
print(df_reg_comp.to_string())

# #########################
# OVERVIEW COMP BY GROUP
# ########################

print()
print(u'Overview of competition for Total (excluding Corsica)')
print(df_info[(df_info['reg'] != u'Corse') &\
              (df_info['group'] == 'TOTAL')]\
             [lsd_comp].describe(percentiles = ls_pctiles).to_string())

print()
print(u'Overview of competition for Total by region')
df_info_sub = df_info[df_info['group'] == 'TOTAL']
df_reg_comp = df_info_sub[lsd_comp + ['reg']].groupby('reg').agg('mean')
df_reg_comp['count'] = df_info_sub['reg'].value_counts()
df_reg_comp = df_reg_comp[['count'] + lsd_comp]
df_reg_comp.sort('count', ascending = False, inplace = True)
df_reg_comp.ix['TOTAL - France'] = df_info_sub[lsd_comp].mean()
df_reg_comp.loc['TOTAL - France', 'count'] = df_reg_comp['count'].sum()
print(df_reg_comp.to_string())

# todo: function + check w/ quartiles to argue on market bounds
# todo: exploit R/B/C/I with INSEE codes for competition
# todo: concentration within INSEE zones

# ########################
# OVERVIEW SAME GROUP
# ########################

print()
print(u'Overview of competition for Mousquetaires (excluding Corsica)')
print(df_info[(df_info['reg'] != u'Corse') &\
              (df_info['group_last'] == 'MOUSQUETAIRES')]\
             [lsd_comp].describe(percentiles = ls_pctiles).to_string())

print()
print(u'Overview of competition for ESSO (excluding Corsica)')
print(df_info[(df_info['reg'] != u'Corse') &\
              (df_info['group_last'] == 'ESSO')]\
             [lsd_comp].describe(percentiles = ls_pctiles).to_string())

print()
print(u'Overview of competition for AVIA (excluding Corsica)')
print(df_info[(df_info['reg'] != u'Corse') &\
              (df_info['group_last'] == 'AVIA')]\
             [lsd_comp].describe(percentiles = ls_pctiles).to_string())
